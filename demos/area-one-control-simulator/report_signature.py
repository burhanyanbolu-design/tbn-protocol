#!/usr/bin/env python3
"""Create and verify detached issuer signatures for Area One reports."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from report_file_verifier import canonical_json, load_report, verify_report


SIGNATURE_SCHEMA_VERSION = "area-one-report-signature/1.1"
ALGORITHM = "RSA-PSS-SHA256"
KEY_ID_PATTERN = re.compile(r"a1key_[0-9a-f]{16}\Z")
PASSWORD_ENV = "AREA_ONE_SIGNING_KEY_PASSWORD"
SIGNATURE_FIELDS = {
    "schema_version",
    "report_schema_version",
    "report_hash",
    "issued_at",
    "issuer",
    "key_id",
    "algorithm",
    "signature",
}


class SignatureError(ValueError):
    """Raised when signing inputs or signature evidence are invalid."""


@dataclass(frozen=True)
class SignatureVerification:
    valid: bool
    issuer: str | None
    key_id: str | None
    errors: tuple[str, ...]


def _public_pem(public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def key_id_for(public_key: rsa.RSAPublicKey) -> str:
    return "a1key_" + hashlib.sha256(_public_pem(public_key)).hexdigest()[:16]


def utc_timestamp(value: datetime | None = None) -> str:
    moment = value or datetime.now(timezone.utc)
    if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
        raise SignatureError("timestamp must use UTC")
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: Any, field: str = "timestamp") -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SignatureError(f"{field} must be an RFC 3339 UTC timestamp ending in Z")
    try:
        moment = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SignatureError(f"{field} is not a valid timestamp") from exc
    if utc_timestamp(moment) != value:
        raise SignatureError(f"{field} must use canonical whole-second UTC format")
    return moment

def _require_rsa(key: Any, role: str) -> rsa.RSAPrivateKey | rsa.RSAPublicKey:
    if not isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
        raise SignatureError(f"{role} key must be RSA")
    if key.key_size < 2048:
        raise SignatureError(f"{role} RSA key must be at least 2048 bits")
    return key


def load_private_key(path: Path) -> rsa.RSAPrivateKey:
    password_text = os.environ.get(PASSWORD_ENV)
    password = password_text.encode("utf-8") if password_text is not None else None
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=password)
    except (OSError, ValueError, TypeError) as exc:
        raise SignatureError(f"cannot load private key: {exc}") from exc
    return _require_rsa(key, "private")  # type: ignore[return-value]


def load_public_key(path: Path) -> rsa.RSAPublicKey:
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise SignatureError(f"cannot load public key: {exc}") from exc
    return _require_rsa(key, "public")  # type: ignore[return-value]


def signature_payload(evidence: dict[str, Any]) -> bytes:
    body = {key: value for key, value in evidence.items() if key != "signature"}
    return canonical_json(body).encode("utf-8")


def create_signature(
    report: dict[str, Any],
    private_key: rsa.RSAPrivateKey,
    issuer: str,
    issued_at: str | None = None,
) -> dict[str, Any]:
    report_result = verify_report(report)
    if not report_result.valid:
        raise SignatureError("report verification failed: " + "; ".join(report_result.errors))
    issuer = issuer.strip()
    if not issuer:
        raise SignatureError("issuer must not be empty")
    issued_at = issued_at or utc_timestamp()
    parse_utc_timestamp(issued_at, "issued_at")
    _require_rsa(private_key, "private")
    public_key = private_key.public_key()
    evidence: dict[str, Any] = {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "report_schema_version": report["schema_version"],
        "report_hash": report["report_hash"],
        "issued_at": issued_at,
        "issuer": issuer,
        "key_id": key_id_for(public_key),
        "algorithm": ALGORITHM,
    }
    signature = private_key.sign(
        signature_payload(evidence),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    evidence["signature"] = base64.b64encode(signature).decode("ascii")
    return evidence

def verify_signature(
    report: dict[str, Any],
    evidence: dict[str, Any],
    public_key: rsa.RSAPublicKey,
    expected_issuer: str | None = None,
    require_passed: bool = False,
) -> SignatureVerification:
    errors = list(verify_report(report, require_passed=require_passed).errors)
    issuer = evidence.get("issuer")
    claimed_key_id = evidence.get("key_id")
    if set(evidence) != SIGNATURE_FIELDS:
        missing = sorted(SIGNATURE_FIELDS - set(evidence))
        extra = sorted(set(evidence) - SIGNATURE_FIELDS)
        errors.append(f"signature fields differ; missing={missing}, extra={extra}")
    if evidence.get("schema_version") != SIGNATURE_SCHEMA_VERSION:
        errors.append("unsupported signature schema_version")
    if evidence.get("report_schema_version") != report.get("schema_version"):
        errors.append("signature report_schema_version does not match report")
    if evidence.get("report_hash") != report.get("report_hash"):
        errors.append("signature report_hash does not match report")
    if evidence.get("algorithm") != ALGORITHM:
        errors.append("unsupported signature algorithm")
    try:
        parse_utc_timestamp(evidence.get("issued_at"), "issued_at")
    except SignatureError as exc:
        errors.append(str(exc))
    if not isinstance(issuer, str) or not issuer.strip():
        errors.append("signature issuer must be a non-empty string")
    elif expected_issuer is not None and issuer != expected_issuer:
        errors.append("signature issuer does not match expected issuer")

    try:
        _require_rsa(public_key, "public")
        derived_key_id = key_id_for(public_key)
        if not isinstance(claimed_key_id, str) or not KEY_ID_PATTERN.fullmatch(
            claimed_key_id
        ):
            errors.append("signature key_id has an invalid format")
        elif claimed_key_id != derived_key_id:
            errors.append("signature key_id does not match public key")
        encoded = evidence.get("signature")
        if not isinstance(encoded, str):
            raise SignatureError("signature must be base64 text")
        signature = base64.b64decode(encoded, validate=True)
        public_key.verify(
            signature,
            signature_payload(evidence),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except (InvalidSignature, SignatureError, ValueError, TypeError, binascii.Error) as exc:
        errors.append(f"cryptographic signature verification failed: {exc}")

    return SignatureVerification(
        valid=not errors,
        issuer=issuer if isinstance(issuer, str) else None,
        key_id=claimed_key_id if isinstance(claimed_key_id, str) else None,
        errors=tuple(errors),
    )

def write_json(value: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sign = commands.add_parser("sign", help="create detached signature evidence")
    sign.add_argument("report", type=Path)
    sign.add_argument("--private-key", type=Path, required=True)
    sign.add_argument("--issuer", required=True)
    sign.add_argument("--output", type=Path, required=True)
    sign.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify", help="verify detached signature evidence")
    verify.add_argument("report", type=Path)
    verify.add_argument("signature", type=Path)
    verify.add_argument("--public-key", type=Path, required=True)
    verify.add_argument("--expected-issuer")
    verify.add_argument("--require-passed", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = load_report(args.report)
        if args.command == "sign":
            if args.output.exists() and not args.force:
                raise SignatureError("output exists; use --force to replace it")
            evidence = create_signature(report, load_private_key(args.private_key), args.issuer)
            write_json(evidence, args.output)
            print(f"signature_written={args.output}")
            print(f"report_hash={evidence['report_hash']}")
            print(f"issuer={evidence['issuer']}")
            print(f"key_id={evidence['key_id']}")
            return 0
        evidence = load_report(args.signature)
        result = verify_signature(
            report,
            evidence,
            load_public_key(args.public_key),
            args.expected_issuer,
            args.require_passed,
        )
    except (SignatureError, ValueError) as exc:
        print("signature_valid=false")
        print(f"error={exc}")
        return 2

    print(f"signature_valid={str(result.valid).lower()}")
    print(f"issuer={result.issuer or 'missing'}")
    print(f"key_id={result.key_id or 'missing'}")
    for error in result.errors:
        print(f"error={error}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
