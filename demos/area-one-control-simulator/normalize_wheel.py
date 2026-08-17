#!/usr/bin/env python3
"""Canonicalize a pure-Python wheel for cross-platform reproducibility."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import os
import stat
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath


TEXT_NAMES = {"METADATA", "WHEEL", "entry_points.txt", "top_level.txt"}
DEFAULT_EPOCH = 1767225600


class WheelNormalizationError(ValueError):
    """Raised when a wheel cannot be safely canonicalized."""


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and not path.is_absolute()
        and all(part not in ("", ".", "..") for part in path.parts)
        and path.as_posix() == name
    )


def _normalize_text(data: bytes) -> bytes:
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _record_bytes(files: dict[str, bytes], record_name: str) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    for name in sorted(files):
        digest = base64.urlsafe_b64encode(
            hashlib.sha256(files[name]).digest()
        ).rstrip(b"=").decode("ascii")
        writer.writerow((name, f"sha256={digest}", str(len(files[name]))))
    writer.writerow((record_name, "", ""))
    return output.getvalue().encode("utf-8")

def normalize_wheel(path: Path, epoch: int = DEFAULT_EPOCH) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise WheelNormalizationError("wheel contains duplicate paths")
            if any(info.is_dir() or not _safe_name(info.filename) for info in infos):
                raise WheelNormalizationError("wheel contains an unsafe path")
            files = {info.filename: archive.read(info) for info in infos}
    except (OSError, zipfile.BadZipFile) as exc:
        raise WheelNormalizationError(f"cannot read wheel: {exc}") from exc

    records = [name for name in files if name.endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise WheelNormalizationError("wheel must contain exactly one RECORD")
    record_name = records[0]
    files.pop(record_name)
    for name, data in tuple(files.items()):
        if name.endswith(".py") or PurePosixPath(name).name in TEXT_NAMES:
            try:
                files[name] = _normalize_text(data)
            except UnicodeDecodeError as exc:
                raise WheelNormalizationError(f"non-UTF-8 text member: {name}") from exc
    files[record_name] = _record_bytes(files, record_name)

    date_time = time.gmtime(epoch)[:6]
    if date_time[0] < 1980:
        raise WheelNormalizationError("ZIP timestamps cannot predate 1980")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=path.name + ".", suffix=".tmp", dir=path.parent, delete=False
        ) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, date_time=date_time)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, files[name])
        os.replace(temporary_name, path)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot write canonical wheel: {exc}") from exc
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--source-date-epoch", type=int, default=DEFAULT_EPOCH)
    args = parser.parse_args()
    normalize_wheel(args.wheel, args.source_date_epoch)
    digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
    print(f"wheel={args.wheel}")
    print(f"size={args.wheel.stat().st_size}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
