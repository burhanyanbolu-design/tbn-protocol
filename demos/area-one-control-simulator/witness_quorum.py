#!/usr/bin/env python3
"""Verify threshold quorums of independent Area One checkpoint witnesses."""

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

from checkpoint_witness import (
    ALGORITHM,
    verify_attestation,
    witness_key_id_for,
)
from report_file_verifier import canonical_json, load_report


POLICY_SCHEMA_VERSION = "area-one-witness-quorum-policy/1.0"
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
KEY_ID_PATTERN = re.compile(r"a1wkey_[0-9a-f]{16}\Z")
POLICY_FIELDS = {
    "schema_version", "policy_id", "threshold", "witnesses", "policy_hash",
}
MEMBER_FIELDS = {
    "witness", "witness_key_id", "algorithm", "public_key_pem",
    "public_key_sha256", "status",
}
MEMBER_STATUSES = {"active", "revoked"}


class QuorumError(ValueError):
    """Raised when quorum policy inputs are invalid."""


@dataclass(frozen=True)
class PolicyVerification:
    valid: bool
    policy_hash: str | None
    threshold: int | None
    active_witnesses: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class QuorumVerification:
    valid: bool
    checkpoint_hash: str | None
    policy_hash: str | None
    threshold: int
    accepted_witnesses: tuple[str, ...]
    rejected_evidence: tuple[str, ...]

def _canonical_public_pem(public_key: rsa.RSAPublicKey) -> str:
    return public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def _public_key_from_member(member: dict[str, Any]) -> rsa.RSAPublicKey:
    pem = member.get("public_key_pem")
    if not isinstance(pem, str):
        raise QuorumError("public_key_pem must be text")
    try:
        key = serialization.load_pem_public_key(pem.encode("ascii"))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise QuorumError(f"invalid public_key_pem: {exc}") from exc
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
        raise QuorumError("witness public key must be RSA with at least 2048 bits")
    if _canonical_public_pem(key) != pem:
        raise QuorumError("public_key_pem must use canonical SubjectPublicKeyInfo PEM")
    return key


def _member(witness: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
    witness = witness.strip()
    if not witness:
        raise QuorumError("witness name must not be empty")
    if public_key.key_size < 2048:
        raise QuorumError("witness RSA key must be at least 2048 bits")
    pem = _canonical_public_pem(public_key)
    return {
        "witness": witness,
        "witness_key_id": witness_key_id_for(public_key),
        "algorithm": ALGORITHM,
        "public_key_pem": pem,
        "public_key_sha256": "sha256:" + hashlib.sha256(pem.encode("ascii")).hexdigest(),
        "status": "active",
    }


def calculate_policy_hash(policy: dict[str, Any]) -> str:
    body = copy.deepcopy(policy)
    body.pop("policy_hash", None)
    payload = b"AREA-ONE-WITNESS-QUORUM\x00" + canonical_json(body).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def create_policy(
    policy_id: str,
    threshold: int,
    members: list[tuple[str, rsa.RSAPublicKey]],
) -> dict[str, Any]:
    policy_id = policy_id.strip()
    if not policy_id:
        raise QuorumError("policy_id must not be empty")
    if type(threshold) is not int or threshold < 1:
        raise QuorumError("threshold must be a positive integer")
    records = [_member(name, key) for name, key in members]
    if threshold > len(records):
        raise QuorumError("threshold cannot exceed witness count")
    policy: dict[str, Any] = {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_id": policy_id,
        "threshold": threshold,
        "witnesses": records,
    }
    result = verify_policy({**policy, "policy_hash": calculate_policy_hash(policy)})
    if not result.valid:
        raise QuorumError("invalid policy: " + "; ".join(result.errors))
    policy["policy_hash"] = calculate_policy_hash(policy)
    return policy

def verify_policy(
    policy: dict[str, Any], expected_hash: str | None = None
) -> PolicyVerification:
    errors: list[str] = []
    claimed_hash = policy.get("policy_hash")
    threshold = policy.get("threshold")
    if set(policy) != POLICY_FIELDS:
        errors.append("policy fields differ from schema")
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        errors.append("unsupported policy schema_version")
    if not isinstance(policy.get("policy_id"), str) or not policy["policy_id"].strip():
        errors.append("policy_id must be non-empty text")
    if type(threshold) is not int or threshold < 1:
        errors.append("threshold must be a positive integer")
        threshold_value = None
    else:
        threshold_value = threshold
    if not isinstance(claimed_hash, str) or not HASH_PATTERN.fullmatch(claimed_hash):
        errors.append("policy_hash has invalid format")
    elif not hmac.compare_digest(claimed_hash, calculate_policy_hash(policy)):
        errors.append("policy_hash does not match policy content")
    if expected_hash is not None:
        if not HASH_PATTERN.fullmatch(expected_hash):
            errors.append("expected policy hash has invalid format")
        elif not isinstance(claimed_hash, str) or not hmac.compare_digest(
            claimed_hash, expected_hash
        ):
            errors.append("policy_hash does not match independently expected hash")

    members = policy.get("witnesses")
    if not isinstance(members, list) or not members:
        errors.append("witnesses must be a non-empty array")
        members = []
    names: set[str] = set()
    key_ids: set[str] = set()
    active_count = 0
    for index, member in enumerate(members):
        prefix = f"witnesses[{index}]"
        if not isinstance(member, dict) or set(member) != MEMBER_FIELDS:
            errors.append(f"{prefix} fields differ from schema")
            continue
        name = member.get("witness")
        key_id = member.get("witness_key_id")
        status = member.get("status")
        if not isinstance(name, str) or not name.strip() or name in names:
            errors.append(f"{prefix}.witness is empty or duplicated")
        else:
            names.add(name)
        if not isinstance(key_id, str) or not KEY_ID_PATTERN.fullmatch(key_id) or key_id in key_ids:
            errors.append(f"{prefix}.witness_key_id is invalid or duplicated")
        else:
            key_ids.add(key_id)
        if status not in MEMBER_STATUSES:
            errors.append(f"{prefix}.status is invalid")
        elif status == "active":
            active_count += 1
        if member.get("algorithm") != ALGORITHM:
            errors.append(f"{prefix}.algorithm is unsupported")

        try:
            public_key = _public_key_from_member(member)
            pem = member["public_key_pem"].encode("ascii")
            fingerprint = "sha256:" + hashlib.sha256(pem).hexdigest()
            if key_id != witness_key_id_for(public_key):
                errors.append(f"{prefix}.witness_key_id does not match public key")
            if member.get("public_key_sha256") != fingerprint:
                errors.append(f"{prefix}.public_key_sha256 does not match public key")
        except QuorumError as exc:
            errors.append(f"{prefix}: {exc}")
    if threshold_value is not None and threshold_value > active_count:
        errors.append("threshold exceeds active witness count")
    return PolicyVerification(
        valid=not errors,
        policy_hash=claimed_hash if isinstance(claimed_hash, str) else None,
        threshold=threshold_value,
        active_witnesses=active_count,
        errors=tuple(errors),
    )


def verify_quorum(
    log: dict[str, Any],
    attestations: list[dict[str, Any]],
    policy: dict[str, Any],
    expected_policy_hash: str,
) -> QuorumVerification:
    policy_result = verify_policy(policy, expected_policy_hash)
    if not policy_result.valid or policy_result.threshold is None:
        return QuorumVerification(
            False,
            None,
            policy_result.policy_hash,
            policy_result.threshold or 0,
            (),
            policy_result.errors,
        )
    by_key = {
        member["witness_key_id"]: member
        for member in policy["witnesses"]
    }
    accepted_keys: set[str] = set()
    accepted_names: list[str] = []
    rejected: list[str] = []
    checkpoints = log.get("checkpoints")
    checkpoint_hash = (
        checkpoints[-1].get("checkpoint_hash")
        if isinstance(checkpoints, list)
        and checkpoints
        and isinstance(checkpoints[-1], dict)
        else None
    )
    for index, attestation in enumerate(attestations):
        if not isinstance(attestation, dict):
            rejected.append(f"attestation[{index}]: evidence must be an object")
            continue
        key_id = attestation.get("witness_key_id")
        if not isinstance(key_id, str) or key_id not in by_key:
            rejected.append(f"attestation[{index}]: unknown witness key")
            continue
        if key_id in accepted_keys:
            rejected.append(f"attestation[{index}]: duplicate witness key does not count")
            continue
        member = by_key[key_id]
        if member["status"] != "active":
            rejected.append(f"attestation[{index}]: witness key is {member['status']}")
            continue
        result = verify_attestation(
            log,
            attestation,
            _public_key_from_member(member),
            member["witness"],
        )
        if result.valid:
            accepted_keys.add(key_id)
            accepted_names.append(member["witness"])
        else:
            rejected.append(
                f"attestation[{index}]: " + "; ".join(result.errors)
            )
    return QuorumVerification(
        valid=len(accepted_keys) >= policy_result.threshold,
        checkpoint_hash=checkpoint_hash if isinstance(checkpoint_hash, str) else None,
        policy_hash=policy_result.policy_hash,
        threshold=policy_result.threshold,
        accepted_witnesses=tuple(accepted_names),
        rejected_evidence=tuple(rejected),
    )

def _load_public_key(path: Path) -> rsa.RSAPublicKey:
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise QuorumError(f"cannot load witness public key: {exc}") from exc
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
        raise QuorumError("witness public key must be RSA with at least 2048 bits")
    return key


def _parse_member(value: str) -> tuple[str, rsa.RSAPublicKey]:
    if "=" not in value:
        raise QuorumError("member must use WITNESS=PUBLIC_KEY_PATH")
    name, path = value.split("=", 1)
    if not name.strip() or not path.strip():
        raise QuorumError("member name and public-key path must not be empty")
    return name.strip(), _load_public_key(Path(path))


def _write_json(value: dict[str, Any], output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise QuorumError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-policy")
    create.add_argument("--policy-id", required=True)
    create.add_argument("--threshold", type=int, required=True)
    create.add_argument(
        "--member",
        action="append",
        required=True,
        help="repeat WITNESS=PUBLIC_KEY_PATH",
    )
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify-policy")
    verify.add_argument("policy", type=Path)
    verify.add_argument("--expected-policy-hash", required=True)
    quorum = commands.add_parser("verify")
    quorum.add_argument("log", type=Path)
    quorum.add_argument("policy", type=Path)
    quorum.add_argument("attestations", type=Path, nargs="+")
    quorum.add_argument("--expected-policy-hash", required=True)
    return parser

def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create-policy":
            policy = create_policy(
                args.policy_id,
                args.threshold,
                [_parse_member(value) for value in args.member],
            )
            _write_json(policy, args.output, args.force)
            print(f"policy_written={args.output}")
            print(f"policy_hash={policy['policy_hash']}")
            print(f"threshold={policy['threshold']}")
            return 0
        if args.command == "verify-policy":
            result = verify_policy(
                load_report(args.policy), args.expected_policy_hash
            )
            print(f"policy_valid={str(result.valid).lower()}")
            print(f"policy_hash={result.policy_hash or 'missing'}")
            print(f"threshold={result.threshold or 0}")
            print(f"active_witnesses={result.active_witnesses}")
            for error in result.errors:
                print(f"error={error}")
            return 0 if result.valid else 1
        result = verify_quorum(
            load_report(args.log),
            [load_report(path) for path in args.attestations],
            load_report(args.policy),
            args.expected_policy_hash,
        )
    except (QuorumError, ValueError) as exc:
        print("quorum_valid=false")
        print(f"error={exc}")
        return 2

    print(f"quorum_valid={str(result.valid).lower()}")
    print(f"checkpoint_hash={result.checkpoint_hash or 'missing'}")
    print(f"policy_hash={result.policy_hash or 'missing'}")
    print(f"threshold={result.threshold}")
    print(f"accepted_count={len(result.accepted_witnesses)}")
    for witness in result.accepted_witnesses:
        print(f"accepted_witness={witness}")
    for rejection in result.rejected_evidence:
        print(f"rejected={rejection}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
