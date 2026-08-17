#!/usr/bin/env python3
"""Sign and verify independent witness attestations for transparency checkpoints."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from report_file_verifier import canonical_json, load_report
from report_signature import parse_utc_timestamp, utc_timestamp
from transparency_log import HASH_PATTERN, verify_log


WITNESS_SCHEMA_VERSION = "area-one-checkpoint-witness/1.0"
ALGORITHM = "RSA-PSS-SHA256"
PASSWORD_ENV = "AREA_ONE_WITNESS_KEY_PASSWORD"
KEY_ID_PATTERN = re.compile(r"a1wkey_[0-9a-f]{16}\Z")
WITNESS_FIELDS = {
    "schema_version", "log_id", "tree_size", "root_hash", "checkpoint_hash",
    "checkpoint_generated_at", "witnessed_at", "witness", "witness_key_id",
    "algorithm", "signature",
}


class WitnessError(ValueError):
    """Raised when witness inputs or evidence are invalid."""


@dataclass(frozen=True)
class WitnessVerification:
    valid: bool
    witness: str | None
    witness_key_id: str | None
    checkpoint_hash: str | None
    errors: tuple[str, ...]


def _public_pem(public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def witness_key_id_for(public_key: rsa.RSAPublicKey) -> str:
    return "a1wkey_" + hashlib.sha256(_public_pem(public_key)).hexdigest()[:16]


def _require_rsa(key: Any, role: str) -> rsa.RSAPrivateKey | rsa.RSAPublicKey:
    if not isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
        raise WitnessError(f"{role} key must be RSA")
    if key.key_size < 2048:
        raise WitnessError(f"{role} RSA key must be at least 2048 bits")
    return key


def load_witness_private_key(path: Path) -> rsa.RSAPrivateKey:
    password_text = os.environ.get(PASSWORD_ENV)
    password = password_text.encode("utf-8") if password_text is not None else None
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=password)
    except (OSError, ValueError, TypeError) as exc:
        raise WitnessError(f"cannot load witness private key: {exc}") from exc
    return _require_rsa(key, "witness private")  # type: ignore[return-value]


def load_witness_public_key(path: Path) -> rsa.RSAPublicKey:
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise WitnessError(f"cannot load witness public key: {exc}") from exc
    return _require_rsa(key, "witness public")  # type: ignore[return-value]


def witness_payload(attestation: dict[str, Any]) -> bytes:
    body = {key: value for key, value in attestation.items() if key != "signature"}
    return canonical_json(body).encode("utf-8")


def create_attestation(
    log: dict[str, Any],
    expected_checkpoint_hash: str,
    private_key: rsa.RSAPrivateKey,
    witness: str,
    witnessed_at: str | None = None,
) -> dict[str, Any]:
    log_result = verify_log(log, expected_checkpoint_hash)
    if log_result.tree_size == 0:
        raise WitnessError("checkpoint verification failed: empty logs cannot be witnessed")
    if not log_result.valid:
        raise WitnessError(
            "checkpoint verification failed: " + "; ".join(log_result.errors)
        )
    witness = witness.strip()
    if not witness:
        raise WitnessError("witness must not be empty")
    _require_rsa(private_key, "witness private")
    witnessed_at = witnessed_at or utc_timestamp()
    witnessed = parse_utc_timestamp(witnessed_at, "witnessed_at")
    checkpoint = log["checkpoints"][-1]
    generated = parse_utc_timestamp(
        checkpoint["generated_at"], "checkpoint_generated_at"
    )
    if witnessed < generated:
        raise WitnessError("witnessed_at cannot precede checkpoint generation")

    public_key = private_key.public_key()
    attestation: dict[str, Any] = {
        "schema_version": WITNESS_SCHEMA_VERSION,
        "log_id": log["log_id"],
        "tree_size": checkpoint["tree_size"],
        "root_hash": checkpoint["root_hash"],
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "checkpoint_generated_at": checkpoint["generated_at"],
        "witnessed_at": witnessed_at,
        "witness": witness,
        "witness_key_id": witness_key_id_for(public_key),
        "algorithm": ALGORITHM,
    }
    signature = private_key.sign(
        witness_payload(attestation),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    attestation["signature"] = base64.b64encode(signature).decode("ascii")
    return attestation


def verify_attestation(
    log: dict[str, Any],
    attestation: dict[str, Any],
    public_key: rsa.RSAPublicKey,
    expected_witness: str | None = None,
) -> WitnessVerification:
    errors: list[str] = []
    witness = attestation.get("witness")
    key_id = attestation.get("witness_key_id")
    checkpoint_hash = attestation.get("checkpoint_hash")
    if set(attestation) != WITNESS_FIELDS:
        errors.append("witness fields differ from schema")
    if attestation.get("schema_version") != WITNESS_SCHEMA_VERSION:
        errors.append("unsupported witness schema_version")
    if attestation.get("algorithm") != ALGORITHM:
        errors.append("unsupported witness algorithm")
    if not isinstance(checkpoint_hash, str) or not HASH_PATTERN.fullmatch(checkpoint_hash):
        errors.append("checkpoint_hash has invalid format")
        log_result = verify_log(log)
    else:
        log_result = verify_log(log, checkpoint_hash)
    errors.extend(log_result.errors)
    if log_result.tree_size == 0:
        errors.append("empty logs cannot have witness attestations")

    if not isinstance(witness, str) or not witness.strip():
        errors.append("witness must be non-empty text")
    elif expected_witness is not None and witness != expected_witness:
        errors.append("witness does not match expected witness")

    if log_result.tree_size:
        checkpoint = log["checkpoints"][-1]
        comparisons = {
            "log_id": log.get("log_id"),
            "tree_size": checkpoint.get("tree_size"),
            "root_hash": checkpoint.get("root_hash"),
            "checkpoint_hash": checkpoint.get("checkpoint_hash"),
            "checkpoint_generated_at": checkpoint.get("generated_at"),
        }
        for field, expected in comparisons.items():
            if attestation.get(field) != expected:
                errors.append(f"witness {field} does not match checkpoint")
    try:
        witnessed = parse_utc_timestamp(
            attestation.get("witnessed_at"), "witnessed_at"
        )
        generated = parse_utc_timestamp(
            attestation.get("checkpoint_generated_at"),
            "checkpoint_generated_at",
        )
        if witnessed < generated:
            errors.append("witnessed_at precedes checkpoint generation")
    except ValueError as exc:
        errors.append(str(exc))

    try:
        _require_rsa(public_key, "witness public")
        derived_id = witness_key_id_for(public_key)
        if not isinstance(key_id, str) or not KEY_ID_PATTERN.fullmatch(key_id):
            errors.append("witness_key_id has invalid format")
        elif key_id != derived_id:
            errors.append("witness_key_id does not match public key")
        encoded = attestation.get("signature")
        if not isinstance(encoded, str):
            raise WitnessError("signature must be base64 text")
        signature = base64.b64decode(encoded, validate=True)
        public_key.verify(
            signature,
            witness_payload(attestation),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except (
        InvalidSignature,
        WitnessError,
        ValueError,
        TypeError,
        binascii.Error,
    ) as exc:
        errors.append(f"witness signature verification failed: {exc}")

    return WitnessVerification(
        valid=not errors,
        witness=witness if isinstance(witness, str) else None,
        witness_key_id=key_id if isinstance(key_id, str) else None,
        checkpoint_hash=(
            checkpoint_hash if isinstance(checkpoint_hash, str) else None
        ),
        errors=tuple(errors),
    )

def _write_json(value: dict[str, Any], output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise WitnessError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sign = commands.add_parser("sign")
    sign.add_argument("log", type=Path)
    sign.add_argument("--expected-checkpoint-hash", required=True)
    sign.add_argument("--private-key", type=Path, required=True)
    sign.add_argument("--witness", required=True)
    sign.add_argument("--witnessed-at")
    sign.add_argument("--output", type=Path, required=True)
    sign.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("log", type=Path)
    verify.add_argument("attestation", type=Path)
    verify.add_argument("--public-key", type=Path, required=True)
    verify.add_argument("--expected-witness")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        log = load_report(args.log)
        if args.command == "sign":
            attestation = create_attestation(
                log,
                args.expected_checkpoint_hash,
                load_witness_private_key(args.private_key),
                args.witness,
                args.witnessed_at,
            )
            _write_json(attestation, args.output, args.force)
            print(f"witness_written={args.output}")
            print(f"checkpoint_hash={attestation['checkpoint_hash']}")
            print(f"witness={attestation['witness']}")
            print(f"witness_key_id={attestation['witness_key_id']}")
            return 0
        result = verify_attestation(
            log,
            load_report(args.attestation),
            load_witness_public_key(args.public_key),
            args.expected_witness,
        )
    except (WitnessError, ValueError) as exc:
        print("witness_valid=false")
        print(f"error={exc}")
        return 2

    print(f"witness_valid={str(result.valid).lower()}")
    print(f"checkpoint_hash={result.checkpoint_hash or 'missing'}")
    print(f"witness={result.witness or 'missing'}")
    print(f"witness_key_id={result.witness_key_id or 'missing'}")
    for error in result.errors:
        print(f"error={error}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
