#!/usr/bin/env python3
"""Create and verify the candidate SHA-256 anchor for the Area One protocol.

This tool can normalize bytes and prepare an anchor, but it cannot approve or
freeze the protocol. Freeze always requires a separate explicit human decision.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import tempfile
import unicodedata
from collections.abc import Callable
from pathlib import Path

PROTOCOL_BASENAME = "area-one-overlap-pair-scatterer-research-design-2026-08-15.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL_PATH = PROJECT_ROOT / "data" / PROTOCOL_BASENAME
DEFAULT_ANCHOR_PATH = DEFAULT_PROTOCOL_PATH.with_name(PROTOCOL_BASENAME + ".sha256")
MAX_PROTOCOL_BYTES = 1_000_000
MAX_ANCHOR_BYTES = 1024
_ANCHOR_RE = re.compile(rb"([0-9a-f]{64})  ([!-~]+)\n\Z")


class ProtocolAnchorError(ValueError):
    """Raised when protocol or anchor bytes violate the T8 contract."""


def normalize_protocol_bytes(data: bytes) -> bytes:
    """Apply the protocol's frozen transport-normalization contract."""
    if not data or len(data) > MAX_PROTOCOL_BYTES:
        raise ProtocolAnchorError("protocol must be nonempty and within the size limit")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    if not data or data.startswith(b"\xef\xbb\xbf"):
        raise ProtocolAnchorError("protocol is empty after BOM removal or has multiple BOMs")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ProtocolAnchorError("protocol is not strict UTF-8") from exc
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if any((ord(char) < 32 and char not in "\n\t") or ord(char) == 127 for char in text):
        raise ProtocolAnchorError("protocol contains a forbidden control character")
    text = text.rstrip("\n") + "\n"
    normalized = text.encode("utf-8")
    if len(normalized) > MAX_PROTOCOL_BYTES:
        raise ProtocolAnchorError("normalized protocol exceeds the size limit")
    return normalized


def protocol_hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_anchor_bytes(protocol_bytes: bytes, basename: str = PROTOCOL_BASENAME) -> bytes:
    if not basename or Path(basename).name != basename or not basename.isascii():
        raise ProtocolAnchorError("anchor basename must be nonempty safe ASCII")
    return f"{protocol_hexdigest(protocol_bytes)}  {basename}\n".encode("ascii")


def parse_anchor_bytes(data: bytes) -> tuple[str, str]:
    match = _ANCHOR_RE.fullmatch(data)
    if match is None:
        raise ProtocolAnchorError("anchor is not lowercase SHA-256, two spaces, basename, LF")
    digest = match.group(1).decode("ascii")
    basename = match.group(2).decode("ascii")
    if Path(basename).name != basename:
        raise ProtocolAnchorError("anchor filename is not a basename")
    return digest, basename


def _identity(metadata: os.stat_result) -> tuple[int, int, int, int]:
    return (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns)


def _read_stable_regular(path: Path, limit: int) -> tuple[bytes, tuple[int, int, int, int]]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise ProtocolAnchorError(f"{path.name} is not a regular non-symlink file")
    if before.st_size > limit:
        raise ProtocolAnchorError(f"{path.name} exceeds its size limit")
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        data = handle.read(limit + 1)
        after_read = os.fstat(handle.fileno())
    after = path.lstat()
    identities = {_identity(before), _identity(opened), _identity(after_read), _identity(after)}
    if len(identities) != 1 or len(data) > limit:
        raise ProtocolAnchorError(f"{path.name} changed while it was read")
    return data, _identity(after)


def _require_sibling_paths(protocol: Path, anchor: Path) -> None:
    expected = protocol.with_name(protocol.name + ".sha256")
    actual_name = os.path.normcase(os.path.abspath(anchor))
    expected_name = os.path.normcase(os.path.abspath(expected))
    protocol_name = os.path.normcase(os.path.abspath(protocol))
    if actual_name == protocol_name or actual_name != expected_name:
        raise ProtocolAnchorError("anchor must be the distinct exact sibling <protocol>.sha256")


def verify_candidate(protocol_path: Path | str, anchor_path: Path | str) -> str:
    protocol, anchor = Path(protocol_path), Path(anchor_path)
    _require_sibling_paths(protocol, anchor)
    raw, protocol_identity = _read_stable_regular(protocol, MAX_PROTOCOL_BYTES)
    normalized = normalize_protocol_bytes(raw)
    if raw != normalized:
        raise ProtocolAnchorError("protocol file is not in canonical normalized form")
    anchor_raw, anchor_identity = _read_stable_regular(anchor, MAX_ANCHOR_BYTES)
    digest, basename = parse_anchor_bytes(anchor_raw)
    if _identity(protocol.lstat()) != protocol_identity or _identity(anchor.lstat()) != anchor_identity:
        raise ProtocolAnchorError("protocol or anchor changed during pair verification")
    if basename != protocol.name:
        raise ProtocolAnchorError("anchor filename does not match protocol filename")
    expected = protocol_hexdigest(raw)
    if digest != expected:
        raise ProtocolAnchorError("anchor digest does not match exact protocol bytes")
    return "sha256:" + expected


def _sync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise ProtocolAnchorError(f"refusing to replace non-regular {path.name}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_candidate(
    protocol_path: Path | str,
    anchor_path: Path | str,
    fault_hook: Callable[[str], None] | None = None,
) -> str:
    """Normalize and durably prepare a fail-closed, explicitly unapproved pair."""
    protocol, anchor = Path(protocol_path), Path(anchor_path)
    _require_sibling_paths(protocol, anchor)
    raw, _identity_before = _read_stable_regular(protocol, MAX_PROTOCOL_BYTES)
    normalized = normalize_protocol_bytes(raw)
    event = fault_hook or (lambda _name: None)
    event("before_protocol_replace")
    if raw != normalized:
        _atomic_write(protocol, normalized)
    event("after_protocol_replace")
    event("before_anchor_replace")
    _atomic_write(anchor, canonical_anchor_bytes(normalized, protocol.name))
    event("after_anchor_replace")
    return verify_candidate(protocol, anchor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL_PATH)
    parser.add_argument("--anchor", type=Path, default=DEFAULT_ANCHOR_PATH)
    parser.add_argument("--write-candidate", action="store_true")
    args = parser.parse_args(argv)
    digest = (
        write_candidate(args.protocol, args.anchor)
        if args.write_candidate
        else verify_candidate(args.protocol, args.anchor)
    )
    print(f"protocol_sha256={digest}")
    print(f"protocol_bytes={args.protocol.stat().st_size}")
    print("independent_verification=REQUIRED")
    print("freeze_status=AWAITING_EXPLICIT_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())