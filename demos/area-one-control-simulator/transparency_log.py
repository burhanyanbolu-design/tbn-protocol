#!/usr/bin/env python3
"""Append-only transparency evidence for trusted Area One report signatures."""

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

from issuer_trust import verify_trusted_report
from report_file_verifier import canonical_json, load_report
from report_signature import parse_utc_timestamp, utc_timestamp


LOG_SCHEMA_VERSION = "area-one-transparency-log/1.0"
ENTRY_SCHEMA_VERSION = "area-one-transparency-entry/1.0"
CHECKPOINT_SCHEMA_VERSION = "area-one-transparency-checkpoint/1.0"
PROOF_SCHEMA_VERSION = "area-one-transparency-inclusion/1.0"
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
LOG_FIELDS = {"schema_version", "log_id", "entries", "checkpoints"}
ENTRY_FIELDS = {
    "schema_version", "sequence", "report_hash", "signature_hash", "issuer",
    "key_id", "issued_at", "logged_at", "previous_entry_hash", "entry_hash",
}
CHECKPOINT_FIELDS = {
    "schema_version", "log_id", "tree_size", "root_hash", "generated_at",
    "previous_checkpoint_hash", "checkpoint_hash",
}


class TransparencyError(ValueError):
    """Raised when transparency evidence or an append request is invalid."""


@dataclass(frozen=True)
class LogVerification:
    valid: bool
    tree_size: int
    checkpoint_hash: str | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ExtensionVerification:
    valid: bool
    old_size: int
    new_size: int
    errors: tuple[str, ...]

def _digest(prefix: bytes, value: Any) -> str:
    payload = prefix + canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _leaf_hash(entry_hash: str) -> bytes:
    return hashlib.sha256(b"\x00" + bytes.fromhex(entry_hash[7:])).digest()


def merkle_root(entry_hashes: list[str]) -> str:
    if not entry_hashes:
        return "sha256:" + hashlib.sha256(b"").hexdigest()
    level = [_leaf_hash(value) for value in entry_hashes]
    while len(level) > 1:
        next_level: list[bytes] = []
        for index in range(0, len(level), 2):
            if index + 1 < len(level):
                next_level.append(_node_hash(level[index], level[index + 1]))
            else:
                next_level.append(level[index])
        level = next_level
    return "sha256:" + level[0].hex()


def calculate_entry_hash(entry: dict[str, Any]) -> str:
    body = copy.deepcopy(entry)
    body.pop("entry_hash", None)
    return _digest(b"AREA-ONE-LOG-ENTRY\x00", body)


def calculate_checkpoint_hash(checkpoint: dict[str, Any]) -> str:
    body = copy.deepcopy(checkpoint)
    body.pop("checkpoint_hash", None)
    return _digest(b"AREA-ONE-LOG-CHECKPOINT\x00", body)


def signature_hash(evidence: dict[str, Any]) -> str:
    return _digest(b"AREA-ONE-SIGNATURE-EVIDENCE\x00", evidence)


def create_log(log_id: str) -> dict[str, Any]:
    log_id = log_id.strip()
    if not log_id:
        raise TransparencyError("log_id must not be empty")
    return {
        "schema_version": LOG_SCHEMA_VERSION,
        "log_id": log_id,
        "entries": [],
        "checkpoints": [],
    }

def verify_log(
    log: dict[str, Any], expected_checkpoint_hash: str | None = None
) -> LogVerification:
    errors: list[str] = []
    if set(log) != LOG_FIELDS:
        errors.append("log top-level fields differ from schema")
    if log.get("schema_version") != LOG_SCHEMA_VERSION:
        errors.append("unsupported log schema_version")
    log_id = log.get("log_id")
    if not isinstance(log_id, str) or not log_id.strip():
        errors.append("log_id must be a non-empty string")
    entries = log.get("entries")
    checkpoints = log.get("checkpoints")
    if not isinstance(entries, list):
        errors.append("entries must be an array")
        entries = []
    if not isinstance(checkpoints, list):
        errors.append("checkpoints must be an array")
        checkpoints = []
    if len(checkpoints) != len(entries):
        errors.append("there must be exactly one checkpoint per entry")

    previous_entry: str | None = None
    valid_entry_hashes: list[str] = []
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            errors.append(f"{prefix} fields differ from schema")
            continue
        if entry.get("schema_version") != ENTRY_SCHEMA_VERSION:
            errors.append(f"{prefix} has unsupported schema_version")
        if type(entry.get("sequence")) is not int or entry["sequence"] != index:
            errors.append(f"{prefix}.sequence is not contiguous")
        for field in ("report_hash", "signature_hash", "entry_hash"):
            value = entry.get(field)
            if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
                errors.append(f"{prefix}.{field} has invalid hash format")
        if entry.get("previous_entry_hash") != previous_entry:
            errors.append(f"{prefix}.previous_entry_hash breaks the chain")
        for field in ("issuer", "key_id"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                errors.append(f"{prefix}.{field} must be non-empty text")
        try:
            issued = parse_utc_timestamp(entry.get("issued_at"), f"{prefix}.issued_at")
            logged = parse_utc_timestamp(entry.get("logged_at"), f"{prefix}.logged_at")
            if logged < issued:
                errors.append(f"{prefix}.logged_at precedes issued_at")
        except ValueError as exc:
            errors.append(str(exc))
        calculated = calculate_entry_hash(entry)
        if entry.get("entry_hash") != calculated:
            errors.append(f"{prefix}.entry_hash does not match content")
        claimed_entry_hash = entry.get("entry_hash")
        if isinstance(claimed_entry_hash, str) and HASH_PATTERN.fullmatch(claimed_entry_hash):
            valid_entry_hashes.append(claimed_entry_hash)
            previous_entry = claimed_entry_hash

    previous_checkpoint: str | None = None
    for index, checkpoint in enumerate(checkpoints):
        prefix = f"checkpoints[{index}]"
        if not isinstance(checkpoint, dict) or set(checkpoint) != CHECKPOINT_FIELDS:
            errors.append(f"{prefix} fields differ from schema")
            continue
        if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
            errors.append(f"{prefix} has unsupported schema_version")
        if checkpoint.get("log_id") != log_id:
            errors.append(f"{prefix}.log_id does not match log")
        if type(checkpoint.get("tree_size")) is not int or checkpoint["tree_size"] != index + 1:
            errors.append(f"{prefix}.tree_size is not contiguous")
        if checkpoint.get("previous_checkpoint_hash") != previous_checkpoint:
            errors.append(f"{prefix}.previous_checkpoint_hash breaks the chain")
        try:
            parse_utc_timestamp(checkpoint.get("generated_at"), f"{prefix}.generated_at")
        except ValueError as exc:
            errors.append(str(exc))
        if index < len(entries) and checkpoint.get("generated_at") != entries[index].get("logged_at"):
            errors.append(f"{prefix}.generated_at does not match appended entry")
        if len(valid_entry_hashes) >= index + 1:
            expected_root = merkle_root(valid_entry_hashes[: index + 1])
            if checkpoint.get("root_hash") != expected_root:
                errors.append(f"{prefix}.root_hash does not match entry prefix")
        calculated = calculate_checkpoint_hash(checkpoint)
        if checkpoint.get("checkpoint_hash") != calculated:
            errors.append(f"{prefix}.checkpoint_hash does not match content")
        claimed_checkpoint = checkpoint.get("checkpoint_hash")
        if isinstance(claimed_checkpoint, str) and HASH_PATTERN.fullmatch(claimed_checkpoint):
            previous_checkpoint = claimed_checkpoint

    final_hash = previous_checkpoint if checkpoints else None
    if expected_checkpoint_hash is not None:
        if not HASH_PATTERN.fullmatch(expected_checkpoint_hash):
            errors.append("expected checkpoint hash has an invalid format")
        elif final_hash is None or not hmac.compare_digest(final_hash, expected_checkpoint_hash):
            errors.append("final checkpoint does not match independently expected hash")
    return LogVerification(not errors, len(entries), final_hash, tuple(errors))

def append_trusted_entry(
    log: dict[str, Any],
    report: dict[str, Any],
    evidence: dict[str, Any],
    registry: dict[str, Any],
    expected_trust_hash: str,
    expected_checkpoint_hash: str | None = None,
    logged_at: str | None = None,
) -> dict[str, Any]:
    current = verify_log(log, expected_checkpoint_hash)
    if not current.valid:
        raise TransparencyError("current log verification failed: " + "; ".join(current.errors))
    if current.tree_size and expected_checkpoint_hash is None:
        raise TransparencyError("non-empty log append requires expected checkpoint hash")
    trusted = verify_trusted_report(
        report, evidence, registry, expected_trust_hash, require_passed=True
    )
    if not trusted.valid:
        raise TransparencyError("trusted report verification failed: " + "; ".join(trusted.errors))
    logged_at = logged_at or utc_timestamp()
    logged = parse_utc_timestamp(logged_at, "logged_at")
    issued = parse_utc_timestamp(evidence.get("issued_at"), "issued_at")
    if logged < issued:
        raise TransparencyError("logged_at cannot precede issued_at")

    updated = copy.deepcopy(log)
    previous_entry = updated["entries"][-1]["entry_hash"] if updated["entries"] else None
    entry: dict[str, Any] = {
        "schema_version": ENTRY_SCHEMA_VERSION,
        "sequence": len(updated["entries"]),
        "report_hash": report["report_hash"],
        "signature_hash": signature_hash(evidence),
        "issuer": evidence["issuer"],
        "key_id": evidence["key_id"],
        "issued_at": evidence["issued_at"],
        "logged_at": logged_at,
        "previous_entry_hash": previous_entry,
    }
    entry["entry_hash"] = calculate_entry_hash(entry)
    updated["entries"].append(entry)

    previous_checkpoint = (
        updated["checkpoints"][-1]["checkpoint_hash"] if updated["checkpoints"] else None
    )
    checkpoint: dict[str, Any] = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "log_id": updated["log_id"],
        "tree_size": len(updated["entries"]),
        "root_hash": merkle_root([item["entry_hash"] for item in updated["entries"]]),
        "generated_at": logged_at,
        "previous_checkpoint_hash": previous_checkpoint,
    }
    checkpoint["checkpoint_hash"] = calculate_checkpoint_hash(checkpoint)
    updated["checkpoints"].append(checkpoint)
    result = verify_log(updated, checkpoint["checkpoint_hash"])
    if not result.valid:
        raise TransparencyError("generated log failed verification: " + "; ".join(result.errors))
    return updated

@dataclass(frozen=True)
class ProofVerification:
    valid: bool
    entry_hash: str | None
    root_hash: str | None
    errors: tuple[str, ...]


def verify_extension(
    old: dict[str, Any],
    new: dict[str, Any],
    expected_old_checkpoint: str,
    expected_new_checkpoint: str | None = None,
) -> ExtensionVerification:
    old_result = verify_log(old, expected_old_checkpoint)
    new_result = verify_log(new, expected_new_checkpoint)
    errors = list(old_result.errors) + list(new_result.errors)
    if old.get("log_id") != new.get("log_id"):
        errors.append("log_id changed")
    old_entries = old.get("entries", [])
    new_entries = new.get("entries", [])
    old_checkpoints = old.get("checkpoints", [])
    new_checkpoints = new.get("checkpoints", [])
    if len(new_entries) < len(old_entries):
        errors.append("new log is shorter than old log")
    elif new_entries[: len(old_entries)] != old_entries:
        errors.append("old entries are not an exact prefix of new log")
    if len(new_checkpoints) < len(old_checkpoints):
        errors.append("new checkpoint history is shorter")
    elif new_checkpoints[: len(old_checkpoints)] != old_checkpoints:
        errors.append("old checkpoints are not an exact prefix of new log")
    return ExtensionVerification(
        not errors, len(old_entries), len(new_entries), tuple(errors)
    )


def create_inclusion_proof(log: dict[str, Any], leaf_index: int) -> dict[str, Any]:
    result = verify_log(log)
    if not result.valid:
        raise TransparencyError("log verification failed: " + "; ".join(result.errors))
    if leaf_index < 0 or leaf_index >= result.tree_size:
        raise TransparencyError("leaf_index is outside the log")
    entry_hashes = [entry["entry_hash"] for entry in log["entries"]]
    level = [_leaf_hash(value) for value in entry_hashes]
    index = leaf_index
    path: list[dict[str, str]] = []
    while len(level) > 1:
        if index % 2 == 1:
            path.append({"side": "left", "hash": "sha256:" + level[index - 1].hex()})
        elif index + 1 < len(level):
            path.append({"side": "right", "hash": "sha256:" + level[index + 1].hex()})
        next_level = [
            _node_hash(level[position], level[position + 1])
            if position + 1 < len(level) else level[position]
            for position in range(0, len(level), 2)
        ]
        level = next_level
        index //= 2
    return {
        "schema_version": PROOF_SCHEMA_VERSION,
        "log_id": log["log_id"],
        "tree_size": result.tree_size,
        "leaf_index": leaf_index,
        "entry_hash": entry_hashes[leaf_index],
        "root_hash": log["checkpoints"][-1]["root_hash"],
        "path": path,
    }

def verify_inclusion_proof(
    proof: dict[str, Any], expected_root_hash: str
) -> ProofVerification:
    errors: list[str] = []
    required = {
        "schema_version", "log_id", "tree_size", "leaf_index", "entry_hash",
        "root_hash", "path",
    }
    if set(proof) != required:
        errors.append("proof fields differ from schema")
    if proof.get("schema_version") != PROOF_SCHEMA_VERSION:
        errors.append("unsupported proof schema_version")
    tree_size = proof.get("tree_size")
    leaf_index = proof.get("leaf_index")
    entry_hash = proof.get("entry_hash")
    root_hash = proof.get("root_hash")
    path = proof.get("path")
    if type(tree_size) is not int or tree_size < 1:
        errors.append("tree_size must be a positive integer")
    if type(leaf_index) is not int or type(tree_size) is not int or not 0 <= leaf_index < tree_size:
        errors.append("leaf_index is outside tree_size")
    for name, value in (("entry_hash", entry_hash), ("root_hash", root_hash), ("expected_root_hash", expected_root_hash)):
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            errors.append(f"{name} has invalid hash format")
    if not isinstance(path, list):
        errors.append("path must be an array")
        path = []
    if errors:
        return ProofVerification(False, entry_hash if isinstance(entry_hash, str) else None, root_hash if isinstance(root_hash, str) else None, tuple(errors))

    current = _leaf_hash(entry_hash)
    index = leaf_index
    width = tree_size
    path_index = 0
    while width > 1:
        expected_side = None
        if index % 2 == 1:
            expected_side = "left"
        elif index + 1 < width:
            expected_side = "right"
        if expected_side is not None:
            if path_index >= len(path) or not isinstance(path[path_index], dict):
                errors.append("proof path is too short")
                break
            step = path[path_index]
            sibling_hash = step.get("hash")
            if step.get("side") != expected_side or not isinstance(sibling_hash, str) or not HASH_PATTERN.fullmatch(sibling_hash):
                errors.append("proof path step is invalid")
                break
            sibling = bytes.fromhex(sibling_hash[7:])
            current = _node_hash(sibling, current) if expected_side == "left" else _node_hash(current, sibling)
            path_index += 1
        index //= 2
        width = (width + 1) // 2
    if path_index != len(path):
        errors.append("proof path contains unused steps")
    calculated_root = "sha256:" + current.hex()
    if calculated_root != root_hash or not hmac.compare_digest(root_hash, expected_root_hash):
        errors.append("proof root does not match expected root")
    return ProofVerification(not errors, entry_hash, root_hash, tuple(errors))

def _write_json(value: dict[str, Any], output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise TransparencyError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--log-id", required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--force", action="store_true")
    append = commands.add_parser("append")
    append.add_argument("log", type=Path)
    append.add_argument("report", type=Path)
    append.add_argument("signature", type=Path)
    append.add_argument("registry", type=Path)
    append.add_argument("--expected-trust-hash", required=True)
    append.add_argument("--expected-checkpoint-hash")
    append.add_argument("--logged-at")
    append.add_argument("--output", type=Path, required=True)
    append.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("log", type=Path)
    verify.add_argument("--expected-checkpoint-hash")
    extension = commands.add_parser("verify-extension")
    extension.add_argument("old", type=Path)
    extension.add_argument("new", type=Path)
    extension.add_argument("--expected-old-checkpoint", required=True)
    extension.add_argument("--expected-new-checkpoint")
    proof = commands.add_parser("proof")
    proof.add_argument("log", type=Path)
    proof.add_argument("--index", type=int, required=True)
    proof.add_argument("--output", type=Path, required=True)
    proof.add_argument("--force", action="store_true")
    verify_proof = commands.add_parser("verify-proof")
    verify_proof.add_argument("proof", type=Path)
    verify_proof.add_argument("--expected-root", required=True)
    return parser

def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            value = create_log(args.log_id)
            _write_json(value, args.output, args.force)
            print(f"log_written={args.output}")
            print("tree_size=0")
            return 0
        if args.command == "append":
            value = append_trusted_entry(
                load_report(args.log),
                load_report(args.report),
                load_report(args.signature),
                load_report(args.registry),
                args.expected_trust_hash,
                args.expected_checkpoint_hash,
                args.logged_at,
            )
            _write_json(value, args.output, args.force)
            checkpoint = value["checkpoints"][-1]
            print(f"log_written={args.output}")
            print(f"tree_size={checkpoint['tree_size']}")
            print(f"root_hash={checkpoint['root_hash']}")
            print(f"checkpoint_hash={checkpoint['checkpoint_hash']}")
            return 0
        if args.command == "verify":
            result = verify_log(load_report(args.log), args.expected_checkpoint_hash)
            print(f"log_valid={str(result.valid).lower()}")
            print(f"tree_size={result.tree_size}")
            print(f"checkpoint_hash={result.checkpoint_hash or 'missing'}")
        elif args.command == "verify-extension":
            result = verify_extension(
                load_report(args.old),
                load_report(args.new),
                args.expected_old_checkpoint,
                args.expected_new_checkpoint,
            )
            print(f"extension_valid={str(result.valid).lower()}")
            print(f"old_size={result.old_size}")
            print(f"new_size={result.new_size}")
        elif args.command == "proof":
            proof = create_inclusion_proof(load_report(args.log), args.index)
            _write_json(proof, args.output, args.force)
            print(f"proof_written={args.output}")
            print(f"entry_hash={proof['entry_hash']}")
            print(f"root_hash={proof['root_hash']}")
            return 0
        else:
            result = verify_inclusion_proof(
                load_report(args.proof), args.expected_root
            )
            print(f"proof_valid={str(result.valid).lower()}")
            print(f"entry_hash={result.entry_hash or 'missing'}")
            print(f"root_hash={result.root_hash or 'missing'}")
        for error in result.errors:
            print(f"error={error}")
        return 0 if result.valid else 1
    except (TransparencyError, ValueError) as exc:
        print("transparency_operation_valid=false")
        print(f"error={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
