#!/usr/bin/env python3
"""Manage and enforce pinned issuer trust for Area One report signatures."""

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

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from report_file_verifier import canonical_json, load_report
from report_signature import (
    ALGORITHM,
    SignatureError,
    key_id_for,
    load_public_key,
    parse_utc_timestamp,
    verify_signature,
)


TRUST_SCHEMA_VERSION = "area-one-issuer-trust/1.0"
TRUST_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
KEY_STATUSES = {"active", "retired", "revoked"}
TOP_LEVEL_FIELDS = {"schema_version", "issuer", "keys", "trust_hash"}
KEY_FIELDS = {
    "key_id",
    "algorithm",
    "public_key_pem",
    "public_key_sha256",
    "status",
    "valid_from",
    "valid_until",
    "revoked_at",
    "revocation_reason",
}


class TrustError(ValueError):
    """Raised when a trust registry or transition is invalid."""


@dataclass(frozen=True)
class TrustVerification:
    valid: bool
    issuer: str | None
    trust_hash: str | None
    errors: tuple[str, ...]

@dataclass(frozen=True)
class TrustedReportVerification:
    valid: bool
    issuer: str | None
    key_id: str | None
    trust_hash: str | None
    key_status: str | None
    errors: tuple[str, ...]


def calculate_trust_hash(registry: dict[str, Any]) -> str:
    body = copy.deepcopy(registry)
    body.pop("trust_hash", None)
    digest = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    return "sha256:" + digest


def _canonical_public_pem(public_key: rsa.RSAPublicKey) -> str:
    return public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def _public_key_from_record(record: dict[str, Any]) -> rsa.RSAPublicKey:
    pem = record.get("public_key_pem")
    if not isinstance(pem, str):
        raise TrustError("public_key_pem must be text")
    try:
        key = serialization.load_pem_public_key(pem.encode("ascii"))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise TrustError(f"invalid public_key_pem: {exc}") from exc
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
        raise TrustError("trusted public key must be RSA with at least 2048 bits")
    if _canonical_public_pem(key) != pem:
        raise TrustError("public_key_pem must use canonical SubjectPublicKeyInfo PEM")
    return key


def _key_record(
    public_key: rsa.RSAPublicKey,
    valid_from: str,
    status: str = "active",
) -> dict[str, Any]:
    parse_utc_timestamp(valid_from, "valid_from")
    pem = _canonical_public_pem(public_key)
    return {
        "key_id": key_id_for(public_key),
        "algorithm": ALGORITHM,
        "public_key_pem": pem,
        "public_key_sha256": "sha256:" + hashlib.sha256(pem.encode("ascii")).hexdigest(),
        "status": status,
        "valid_from": valid_from,
        "valid_until": None,
        "revoked_at": None,
        "revocation_reason": None,
    }

def create_registry(
    issuer: str, public_key: rsa.RSAPublicKey, valid_from: str
) -> dict[str, Any]:
    issuer = issuer.strip()
    if not issuer:
        raise TrustError("issuer must not be empty")
    registry: dict[str, Any] = {
        "schema_version": TRUST_SCHEMA_VERSION,
        "issuer": issuer,
        "keys": [_key_record(public_key, valid_from)],
    }
    registry["trust_hash"] = calculate_trust_hash(registry)
    return registry


def verify_registry(
    registry: dict[str, Any], expected_hash: str | None = None
) -> TrustVerification:
    errors: list[str] = []
    issuer = registry.get("issuer")
    claimed_hash = registry.get("trust_hash")
    if set(registry) != TOP_LEVEL_FIELDS:
        errors.append("trust registry top-level fields differ from schema")
    if registry.get("schema_version") != TRUST_SCHEMA_VERSION:
        errors.append("unsupported trust schema_version")
    if not isinstance(issuer, str) or not issuer.strip():
        errors.append("trust issuer must be a non-empty string")
    if not isinstance(claimed_hash, str) or not TRUST_HASH_PATTERN.fullmatch(claimed_hash):
        errors.append("trust_hash has an invalid format")
    elif not hmac.compare_digest(claimed_hash, calculate_trust_hash(registry)):
        errors.append("trust_hash does not match registry content")
    if expected_hash is not None:
        if not TRUST_HASH_PATTERN.fullmatch(expected_hash):
            errors.append("expected trust hash has an invalid format")
        elif not isinstance(claimed_hash, str) or not hmac.compare_digest(
            claimed_hash, expected_hash
        ):
            errors.append("trust_hash does not match independently expected hash")

    keys = registry.get("keys")
    if not isinstance(keys, list) or not keys:
        errors.append("keys must be a non-empty array")
        keys = []
    seen: set[str] = set()
    active_count = 0
    for index, record in enumerate(keys):
        prefix = f"keys[{index}]"
        if not isinstance(record, dict) or set(record) != KEY_FIELDS:
            errors.append(f"{prefix} fields differ from schema")
            continue
        status = record.get("status")
        if status not in KEY_STATUSES:
            errors.append(f"{prefix}.status is invalid")
        if status == "active":
            active_count += 1
        try:
            public_key = _public_key_from_record(record)
            derived_id = key_id_for(public_key)
            pem = record["public_key_pem"].encode("ascii")
            fingerprint = "sha256:" + hashlib.sha256(pem).hexdigest()
            if record.get("key_id") != derived_id:
                errors.append(f"{prefix}.key_id does not match public key")
            if record.get("public_key_sha256") != fingerprint:
                errors.append(f"{prefix}.public_key_sha256 does not match public key")
        except TrustError as exc:
            errors.append(f"{prefix}: {exc}")

        key_id = record.get("key_id")
        if not isinstance(key_id, str) or key_id in seen:
            errors.append(f"{prefix}.key_id is missing or duplicated")
        else:
            seen.add(key_id)
        if record.get("algorithm") != ALGORITHM:
            errors.append(f"{prefix}.algorithm is unsupported")
        try:
            valid_from = parse_utc_timestamp(record.get("valid_from"), f"{prefix}.valid_from")
            valid_until_value = record.get("valid_until")
            valid_until = (
                parse_utc_timestamp(valid_until_value, f"{prefix}.valid_until")
                if valid_until_value is not None
                else None
            )
            revoked_value = record.get("revoked_at")
            revoked_at = (
                parse_utc_timestamp(revoked_value, f"{prefix}.revoked_at")
                if revoked_value is not None
                else None
            )
            if valid_until is not None and valid_until <= valid_from:
                errors.append(f"{prefix}.valid_until must follow valid_from")
            if revoked_at is not None and revoked_at < valid_from:
                errors.append(f"{prefix}.revoked_at precedes valid_from")
        except SignatureError as exc:
            errors.append(str(exc))
            valid_until = None
            revoked_at = None

        reason = record.get("revocation_reason")
        if status == "active" and any(
            value is not None for value in (valid_until, revoked_at, reason)
        ):
            errors.append(f"{prefix} active key cannot have end or revocation fields")
        elif status == "retired" and (
            valid_until is None or revoked_at is not None or reason is not None
        ):
            errors.append(f"{prefix} retired key requires only valid_until")
        elif status == "revoked" and (
            revoked_at is None or valid_until != revoked_at or not isinstance(reason, str) or not reason.strip()
        ):
            errors.append(f"{prefix} revoked key requires matching end/revocation time and reason")

    if active_count > 1:
        errors.append("trust registry cannot contain more than one active key")
    return TrustVerification(
        valid=not errors,
        issuer=issuer if isinstance(issuer, str) else None,
        trust_hash=claimed_hash if isinstance(claimed_hash, str) else None,
        errors=tuple(errors),
    )

def _validated_copy(
    registry: dict[str, Any], expected_hash: str
) -> dict[str, Any]:
    result = verify_registry(registry, expected_hash)
    if not result.valid:
        raise TrustError("registry verification failed: " + "; ".join(result.errors))
    return copy.deepcopy(registry)


def rotate_registry(
    registry: dict[str, Any],
    expected_hash: str,
    new_public_key: rsa.RSAPublicKey,
    effective_at: str,
) -> dict[str, Any]:
    updated = _validated_copy(registry, expected_hash)
    effective = parse_utc_timestamp(effective_at, "effective_at")
    new_id = key_id_for(new_public_key)
    if any(record["key_id"] == new_id for record in updated["keys"]):
        raise TrustError("new public key already exists in registry")
    active = [record for record in updated["keys"] if record["status"] == "active"]
    if len(active) != 1:
        raise TrustError("rotation requires exactly one active key")
    if effective <= parse_utc_timestamp(active[0]["valid_from"], "valid_from"):
        raise TrustError("rotation effective_at must follow active key valid_from")
    active[0]["status"] = "retired"
    active[0]["valid_until"] = effective_at
    updated["keys"].append(_key_record(new_public_key, effective_at))
    updated["trust_hash"] = calculate_trust_hash(updated)
    return updated


def revoke_key(
    registry: dict[str, Any],
    expected_hash: str,
    key_id: str,
    revoked_at: str,
    reason: str,
) -> dict[str, Any]:
    updated = _validated_copy(registry, expected_hash)
    moment = parse_utc_timestamp(revoked_at, "revoked_at")
    reason = reason.strip()
    if not reason:
        raise TrustError("revocation reason must not be empty")
    matches = [record for record in updated["keys"] if record["key_id"] == key_id]
    if len(matches) != 1:
        raise TrustError("key_id was not found exactly once")
    record = matches[0]
    if record["status"] == "revoked":
        raise TrustError("key is already revoked")
    if moment <= parse_utc_timestamp(record["valid_from"], "valid_from"):
        raise TrustError("revoked_at must follow key valid_from")
    record["status"] = "revoked"
    record["valid_until"] = revoked_at
    record["revoked_at"] = revoked_at
    record["revocation_reason"] = reason
    updated["trust_hash"] = calculate_trust_hash(updated)
    return updated

def verify_trusted_report(
    report: dict[str, Any],
    evidence: dict[str, Any],
    registry: dict[str, Any],
    expected_trust_hash: str,
    require_passed: bool = False,
) -> TrustedReportVerification:
    trust = verify_registry(registry, expected_trust_hash)
    errors = list(trust.errors)
    issuer = evidence.get("issuer")
    key_id = evidence.get("key_id")
    if not trust.valid:
        return TrustedReportVerification(
            False,
            issuer if isinstance(issuer, str) else None,
            key_id if isinstance(key_id, str) else None,
            trust.trust_hash,
            None,
            tuple(errors),
        )
    if issuer != registry["issuer"]:
        errors.append("signature issuer does not match trusted issuer")
    matches = [record for record in registry["keys"] if record["key_id"] == key_id]
    if len(matches) != 1:
        errors.append("signature key_id is not present exactly once in trust registry")
        return TrustedReportVerification(
            False,
            issuer if isinstance(issuer, str) else None,
            key_id if isinstance(key_id, str) else None,
            trust.trust_hash,
            None,
            tuple(errors),
        )

    record = matches[0]
    public_key = _public_key_from_record(record)
    signature_result = verify_signature(
        report,
        evidence,
        public_key,
        registry["issuer"],
        require_passed,
    )
    errors.extend(signature_result.errors)
    try:
        issued_at = parse_utc_timestamp(evidence.get("issued_at"), "issued_at")
        valid_from = parse_utc_timestamp(record["valid_from"], "valid_from")
        valid_until = (
            parse_utc_timestamp(record["valid_until"], "valid_until")
            if record["valid_until"] is not None
            else None
        )
        if issued_at < valid_from:
            errors.append("signature predates key validity")
        if valid_until is not None and issued_at >= valid_until:
            errors.append("signature falls outside key validity window")
    except SignatureError as exc:
        errors.append(str(exc))
    if record["status"] == "revoked":
        errors.append("signing key is revoked; all signatures fail closed")

    return TrustedReportVerification(
        valid=not errors,
        issuer=issuer if isinstance(issuer, str) else None,
        key_id=key_id if isinstance(key_id, str) else None,
        trust_hash=trust.trust_hash,
        key_status=record["status"],
        errors=tuple(errors),
    )

def _write_registry(registry: dict[str, Any], output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise TrustError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--issuer", required=True)
    create.add_argument("--public-key", type=Path, required=True)
    create.add_argument("--valid-from", required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--force", action="store_true")
    rotate = commands.add_parser("rotate")
    rotate.add_argument("registry", type=Path)
    rotate.add_argument("--expected-current-hash", required=True)
    rotate.add_argument("--new-public-key", type=Path, required=True)
    rotate.add_argument("--effective-at", required=True)
    rotate.add_argument("--output", type=Path, required=True)
    rotate.add_argument("--force", action="store_true")
    revoke = commands.add_parser("revoke")
    revoke.add_argument("registry", type=Path)
    revoke.add_argument("--expected-current-hash", required=True)
    revoke.add_argument("--key-id", required=True)
    revoke.add_argument("--revoked-at", required=True)
    revoke.add_argument("--reason", required=True)
    revoke.add_argument("--output", type=Path, required=True)
    revoke.add_argument("--force", action="store_true")
    check = commands.add_parser("verify")
    check.add_argument("registry", type=Path)
    check.add_argument("--expected-hash", required=True)
    report = commands.add_parser("verify-report")
    report.add_argument("report", type=Path)
    report.add_argument("signature", type=Path)
    report.add_argument("registry", type=Path)
    report.add_argument("--expected-trust-hash", required=True)
    report.add_argument("--require-passed", action="store_true")
    return parser

def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            registry = create_registry(
                args.issuer, load_public_key(args.public_key), args.valid_from
            )
            _write_registry(registry, args.output, args.force)
            print(f"registry_written={args.output}")
            print(f"trust_hash={registry['trust_hash']}")
            return 0
        if args.command == "rotate":
            registry = rotate_registry(
                load_report(args.registry),
                args.expected_current_hash,
                load_public_key(args.new_public_key),
                args.effective_at,
            )
            _write_registry(registry, args.output, args.force)
            print(f"registry_written={args.output}")
            print(f"trust_hash={registry['trust_hash']}")
            return 0
        if args.command == "revoke":
            registry = revoke_key(
                load_report(args.registry),
                args.expected_current_hash,
                args.key_id,
                args.revoked_at,
                args.reason,
            )
            _write_registry(registry, args.output, args.force)
            print(f"registry_written={args.output}")
            print(f"trust_hash={registry['trust_hash']}")
            return 0
        if args.command == "verify":
            result = verify_registry(load_report(args.registry), args.expected_hash)
            print(f"trust_valid={str(result.valid).lower()}")
            print(f"issuer={result.issuer or 'missing'}")
            print(f"trust_hash={result.trust_hash or 'missing'}")
        else:
            result = verify_trusted_report(
                load_report(args.report),
                load_report(args.signature),
                load_report(args.registry),
                args.expected_trust_hash,
                args.require_passed,
            )
            print(f"trusted_report_valid={str(result.valid).lower()}")
            print(f"issuer={result.issuer or 'missing'}")
            print(f"key_id={result.key_id or 'missing'}")
            print(f"key_status={result.key_status or 'missing'}")
            print(f"trust_hash={result.trust_hash or 'missing'}")
        for error in result.errors:
            print(f"error={error}")
        return 0 if result.valid else 1
    except (TrustError, SignatureError, ValueError) as exc:
        print("trust_operation_valid=false")
        print(f"error={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
