#!/usr/bin/env python3
"""Independently verify an Area One JSON report using only the standard library."""

from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "area-one-verification-report/1.0"
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")


class ReportLoadError(ValueError):
    """Raised when a report file is not unambiguous strict JSON."""


def _reject_constant(value: str) -> None:
    raise ReportLoadError(f"non-standard JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportLoadError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReportLoadError(str(exc)) from exc
    if not isinstance(value, dict):
        raise ReportLoadError("report root must be a JSON object")
    return value

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def calculate_report_hash(report: dict[str, Any]) -> str:
    body = copy.deepcopy(report)
    body.pop("report_hash", None)
    payload = canonical_json(body).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    report_hash: str | None
    verdict_passed: bool | None
    errors: tuple[str, ...]


def verify_report(
    report: dict[str, Any],
    expected_hash: str | None = None,
    require_passed: bool = False,
) -> VerificationResult:
    errors: list[str] = []
    claimed_hash = report.get("report_hash")
    schema = report.get("schema_version")
    checks = report.get("checks")
    verdict = report.get("verdict")

    if schema != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {schema!r}")
    if not isinstance(claimed_hash, str) or not HASH_PATTERN.fullmatch(claimed_hash):
        errors.append("report_hash must be lowercase sha256:<64 hex characters>")
    elif not hmac.compare_digest(claimed_hash, calculate_report_hash(report)):
        errors.append("report hash does not match the report content")
    if expected_hash is not None:
        if not HASH_PATTERN.fullmatch(expected_hash):
            errors.append("expected hash has an invalid format")
        elif not isinstance(claimed_hash, str) or not hmac.compare_digest(
            claimed_hash, expected_hash
        ):
            errors.append("report hash does not match the expected hash")

    checks_valid = isinstance(checks, dict) and bool(checks)
    if not checks_valid or any(
        not isinstance(name, str) or not isinstance(value, bool)
        for name, value in checks.items() if isinstance(checks, dict)
    ):
        errors.append("checks must be a non-empty object of boolean values")
        checks_valid = False

    verdict_passed = verdict.get("passed") if isinstance(verdict, dict) else None
    if not isinstance(verdict_passed, bool):
        errors.append("verdict.passed must be boolean")
        verdict_passed = None
    elif checks_valid and verdict_passed != all(checks.values()):
        errors.append("verdict.passed is inconsistent with checks")
    if require_passed and verdict_passed is not True:
        errors.append("a passing verdict is required")

    if not isinstance(report.get("configuration"), dict):
        errors.append("configuration must be an object")
    if not isinstance(report.get("results"), dict):
        errors.append("results must be an object")
    if isinstance(verdict, dict):
        for field in ("supported", "not_supported"):
            statements = verdict.get(field)
            if not isinstance(statements, list) or any(
                not isinstance(statement, str) for statement in statements
            ):
                errors.append(f"verdict.{field} must be an array of strings")
    else:
        errors.append("verdict must be an object")

    return VerificationResult(
        valid=not errors,
        report_hash=claimed_hash if isinstance(claimed_hash, str) else None,
        verdict_passed=verdict_passed,
        errors=tuple(errors),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify an Area One report file without rerunning its simulation."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--expected-hash")
    parser.add_argument("--require-passed", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = load_report(args.report)
    except ReportLoadError as exc:
        print("report_valid=false")
        print(f"error={exc}")
        return 2

    result = verify_report(report, args.expected_hash, args.require_passed)
    print(f"report_valid={str(result.valid).lower()}")
    print(f"report_hash={result.report_hash or 'missing'}")
    print(f"verdict_passed={str(result.verdict_passed).lower()}")
    for error in result.errors:
        print(f"error={error}")
    if result.valid:
        print("assurance=integrity-only; not an issuer signature")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
