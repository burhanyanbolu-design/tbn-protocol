#!/usr/bin/env python3
"""Independent verifier for the Area One candidate protocol anchor.

This module intentionally imports no producer anchor or protocol code.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import unicodedata
from pathlib import Path

_BASENAME = "area-one-overlap-pair-scatterer-research-design-2026-08-15.md"
_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = _ROOT / "data" / _BASENAME
_ANCHOR = _PROTOCOL.with_name(_BASENAME + ".sha256")
_LIMIT = 1_000_000
_ANCHOR_LIMIT = 1024
_LINE = re.compile(rb"([0-9a-f]{64})  ([!-~]+)\n\Z")


class IndependentAnchorError(ValueError):
    pass


def _independent_normalize(data: bytes) -> bytes:
    if not data or len(data) > _LIMIT:
        raise IndependentAnchorError("invalid protocol size")
    if data[:3] == b"\xef\xbb\xbf":
        data = data[3:]
    if not data or data[:3] == b"\xef\xbb\xbf":
        raise IndependentAnchorError("empty protocol or multiple BOMs")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise IndependentAnchorError("protocol is not UTF-8") from exc
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for character in text:
        number = ord(character)
        if (number < 32 and character not in ("\n", "\t")) or number == 127:
            raise IndependentAnchorError("forbidden protocol control character")
    normalized = (text.rstrip("\n") + "\n").encode("utf-8")
    if len(normalized) > _LIMIT:
        raise IndependentAnchorError("normalized protocol is oversized")
    return normalized


def _fingerprint(value: os.stat_result) -> tuple[int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def _read_regular_unchanged(path: Path, limit: int) -> tuple[bytes, tuple[int, int, int, int]]:
    first = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(first.st_mode) or first.st_size > limit:
        raise IndependentAnchorError(f"unsafe or oversized file: {path.name}")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        payload = stream.read(limit + 1)
        finished = os.fstat(stream.fileno())
    last = path.lstat()
    if len({_fingerprint(first), _fingerprint(opened), _fingerprint(finished), _fingerprint(last)}) != 1:
        raise IndependentAnchorError(f"file changed during read: {path.name}")
    if len(payload) > limit:
        raise IndependentAnchorError(f"oversized file: {path.name}")
    return payload, _fingerprint(last)


def verify(protocol_path: Path | str = _PROTOCOL, anchor_path: Path | str = _ANCHOR) -> str:
    protocol, anchor = Path(protocol_path), Path(anchor_path)
    expected_anchor = protocol.with_name(protocol.name + ".sha256")
    actual = os.path.normcase(os.path.abspath(anchor))
    if (actual != os.path.normcase(os.path.abspath(expected_anchor))
            or actual == os.path.normcase(os.path.abspath(protocol))):
        raise IndependentAnchorError("anchor is not the exact distinct sibling")
    raw, protocol_fingerprint = _read_regular_unchanged(protocol, _LIMIT)
    if raw != _independent_normalize(raw):
        raise IndependentAnchorError("protocol bytes are not canonical")
    anchor_raw, anchor_fingerprint = _read_regular_unchanged(anchor, _ANCHOR_LIMIT)
    match = _LINE.fullmatch(anchor_raw)
    if match is None:
        raise IndependentAnchorError("anchor format is not canonical")
    digest = match.group(1).decode("ascii")
    filename = match.group(2).decode("ascii")
    if (_fingerprint(protocol.lstat()) != protocol_fingerprint
            or _fingerprint(anchor.lstat()) != anchor_fingerprint):
        raise IndependentAnchorError("protocol or anchor changed during verification")
    if filename != protocol.name or Path(filename).name != filename:
        raise IndependentAnchorError("anchor filename mismatch")
    expected = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise IndependentAnchorError("anchor digest mismatch")
    return "sha256:" + expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=_PROTOCOL)
    parser.add_argument("--anchor", type=Path, default=_ANCHOR)
    args = parser.parse_args(argv)
    digest = verify(args.protocol, args.anchor)
    print(f"protocol_sha256={digest}")
    print("independent_verification=PASS")
    print("freeze_status=AWAITING_EXPLICIT_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())