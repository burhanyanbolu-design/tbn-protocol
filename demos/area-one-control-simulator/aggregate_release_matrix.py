#!/usr/bin/env python3
"""Validate environment reports and produce one Area One release matrix report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
INPUT_SCHEMA = "area-one-release-verification/1.0"
OUTPUT_SCHEMA = "area-one-release-matrix/1.0"
DOMAIN = b"AREA-ONE-RELEASE-VERIFICATION\x00"
MATRIX_DOMAIN = b"AREA-ONE-RELEASE-MATRIX\x00"
DEFAULT_REPORTS = [
    ROOT / "release-verification-windows-python313.json",
    ROOT / "release-verification-linux-python311.json",
    ROOT / "release-verification-linux-python312.json",
    ROOT / "release-verification-linux-python313.json",
]


class MatrixError(ValueError):
    """Raised when environment evidence is inconsistent or incomplete."""


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _verify_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != INPUT_SCHEMA:
        raise MatrixError(f"unsupported schema in {path.name}")
    claimed = report.get("report_hash")
    body = dict(report)
    body.pop("report_hash", None)
    actual = "sha256:" + hashlib.sha256(DOMAIN + _canonical(body)).hexdigest()
    if claimed != actual:
        raise MatrixError(f"invalid report hash in {path.name}")
    checks = report.get("checks")
    if report.get("verdict") != "passed" or not isinstance(checks, list):
        raise MatrixError(f"environment report did not pass: {path.name}")
    if not checks or any(check.get("passed") is not True for check in checks):
        raise MatrixError(f"environment report has failed checks: {path.name}")
    return report

def aggregate(paths: list[Path], output: Path) -> dict[str, Any]:
    reports = [(path, _verify_report(path)) for path in paths]
    targets: list[dict[str, Any]] = []
    wheel_hashes: set[str] = set()
    target_ids: set[str] = set()
    for path, report in reports:
        environment = report["environment"]
        distribution = report["distribution"]
        target_id = (
            f"{environment['system'].lower()}-"
            f"python{environment['python_version'].replace('.', '')}"
        )
        if target_id in target_ids:
            raise MatrixError(f"duplicate environment target: {target_id}")
        target_ids.add(target_id)
        wheel_hashes.add(distribution["wheel_sha256"])
        targets.append(
            {
                "target": target_id,
                "system": environment["system"],
                "system_release": environment["release"],
                "machine": environment["machine"],
                "python_implementation": environment["implementation"],
                "python_version": environment["python_version"],
                "environment_report": path.name,
                "environment_report_hash": report["report_hash"],
            }
        )
    if len(wheel_hashes) != 1:
        raise MatrixError(f"matrix reports disagree on wheel hash: {wheel_hashes}")
    linux_minors = {
        ".".join(target["python_version"].split(".")[:2])
        for target in targets
        if target["system"] == "Linux"
    }
    if linux_minors != {"3.11", "3.12", "3.13"}:
        raise MatrixError(f"Linux Python coverage is incomplete: {linux_minors}")
    if not any(target["system"] == "Windows" for target in targets):
        raise MatrixError("matrix lacks a Windows environment")

    matrix = {
        "schema_version": OUTPUT_SCHEMA,
        "verdict": "passed",
        "wheel_sha256": next(iter(wheel_hashes)),
        "targets": sorted(targets, key=lambda target: target["target"]),
        "coverage": {
            "linux_python_minors": sorted(linux_minors),
            "windows_python_minors": sorted(
                {
                    ".".join(target["python_version"].split(".")[:2])
                    for target in targets
                    if target["system"] == "Windows"
                }
            ),
        },
        "limitations": [
            "Windows Python 3.11 and 3.12 were unavailable and were not tested.",
            "Linux checks ran in Docker Desktop on its WSL2 Linux engine.",
            "No macOS environment was tested.",
            "The wheel has no production release signature and is not on PyPI.",
        ],
    }
    matrix["matrix_hash"] = "sha256:" + hashlib.sha256(
        MATRIX_DOMAIN + _canonical(matrix)
    ).hexdigest()
    output.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return matrix

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="*")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "release-matrix-report.json"
    )
    args = parser.parse_args()
    matrix = aggregate(args.reports or DEFAULT_REPORTS, args.output)
    print(f"matrix_verdict={matrix['verdict']}")
    print(f"targets={len(matrix['targets'])}")
    print(f"wheel_sha256={matrix['wheel_sha256']}")
    print(f"matrix_hash={matrix['matrix_hash']}")
    print(f"report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
