#!/usr/bin/env python3
"""Build and verify portable Area One evidence bundles."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes

from issuer_trust import verify_trusted_report
from report_file_verifier import canonical_json, verify_report
from rfc3161_timestamp import verify_evidence
from transparency_log import signature_hash, verify_log
from witness_quorum import verify_quorum


VERSION = "0.1.0"
SCHEMA_VERSION = "area-one-evidence-bundle/1.0"
MANIFEST_NAME = "manifest.json"
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MANIFEST_FIELDS = {
    "schema_version", "artifacts", "bindings", "files", "bundle_hash",
}
ARTIFACT_FIELDS = {
    "report", "issuer_signature", "issuer_trust", "transparency_log",
    "witness_policy", "witness_attestations", "rfc3161", "tsa_roots",
    "tsa_intermediates",
}
BINDING_FIELDS = {"log_entry_index"}


class BundleError(ValueError):
    """Raised when a bundle is unsafe, malformed, or unverifiable."""


@dataclass(frozen=True)
class BundleVerification:
    valid: bool
    report_hash: str | None
    checkpoint_hash: str | None
    accepted_witnesses: tuple[str, ...]
    granted_at: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BundleError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def _reject_constant(value: str) -> None:
    raise BundleError(f"non-standard JSON constant: {value}")


def _strict_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BundleError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BundleError(f"{label} root must be an object")
    return value


def calculate_bundle_hash(manifest: dict[str, Any]) -> str:
    body = dict(manifest)
    body.pop("bundle_hash", None)
    payload = b"AREA-ONE-EVIDENCE-BUNDLE\x00" + canonical_json(body).encode("utf-8")
    return _sha256(payload)


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and not name.startswith("/")
        and not path.is_absolute()
        and all(part not in ("", ".", "..") for part in path.parts)
        and path.as_posix() == name
    )


def _artifact_paths(artifacts: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for field in (
        "report", "issuer_signature", "issuer_trust", "transparency_log",
        "witness_policy", "rfc3161",
    ):
        value = artifacts.get(field)
        if not isinstance(value, str):
            raise BundleError(f"artifacts.{field} must be a path")
        paths.append(value)
    for field in ("witness_attestations", "tsa_roots", "tsa_intermediates"):
        values = artifacts.get(field)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise BundleError(f"artifacts.{field} must be an array of paths")
        paths.extend(values)
    if not artifacts.get("witness_attestations"):
        raise BundleError("bundle requires at least one witness attestation")
    if not artifacts.get("tsa_roots"):
        raise BundleError("bundle requires at least one TSA root")
    if len(paths) != len(set(paths)):
        raise BundleError("artifact paths must be unique")
    if any(not _safe_name(path) for path in paths):
        raise BundleError("artifact path is unsafe")
    return paths

def read_bundle(source: Path | bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    try:
        archive_source = io.BytesIO(source) if isinstance(source, bytes) else source
        archive = zipfile.ZipFile(archive_source, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise BundleError(f"cannot open bundle ZIP: {exc}") from exc
    with archive:
        if archive.comment:
            raise BundleError("bundle ZIP comments are not permitted")
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise BundleError("bundle ZIP contains duplicate file names")
        if MANIFEST_NAME not in names:
            raise BundleError("bundle ZIP lacks manifest.json")
        total = 0
        files: dict[str, bytes] = {}
        for info in infos:
            if not _safe_name(info.filename) or info.is_dir():
                raise BundleError(f"unsafe ZIP entry: {info.filename!r}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise BundleError("ZIP symbolic links are not permitted")
            if info.flag_bits & 1:
                raise BundleError("encrypted ZIP entries are not permitted")
            if info.file_size > MAX_FILE_BYTES:
                raise BundleError(f"ZIP entry exceeds size limit: {info.filename}")
            if info.file_size > 1_048_576 and info.compress_size * 100 < info.file_size:
                raise BundleError(f"suspicious ZIP compression ratio: {info.filename}")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise BundleError("bundle exceeds total uncompressed size limit")
            files[info.filename] = archive.read(info)

    manifest = _strict_json(files[MANIFEST_NAME], MANIFEST_NAME)
    if set(manifest) != MANIFEST_FIELDS:
        raise BundleError("manifest fields differ from schema")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise BundleError("unsupported bundle schema_version")
    artifacts = manifest.get("artifacts")
    bindings = manifest.get("bindings")
    listed_files = manifest.get("files")
    if not isinstance(artifacts, dict) or set(artifacts) != ARTIFACT_FIELDS:
        raise BundleError("manifest artifacts differ from schema")
    if not isinstance(bindings, dict) or set(bindings) != BINDING_FIELDS:
        raise BundleError("manifest bindings differ from schema")
    if type(bindings.get("log_entry_index")) is not int or bindings["log_entry_index"] < 0:
        raise BundleError("log_entry_index must be a non-negative integer")
    artifact_paths = _artifact_paths(artifacts)
    if not isinstance(listed_files, dict) or set(listed_files) != set(artifact_paths):
        raise BundleError("manifest files do not exactly match artifact paths")
    if set(files) != {MANIFEST_NAME, *artifact_paths}:
        raise BundleError("ZIP entries do not exactly match the manifest")
    for name, claimed_hash in listed_files.items():
        if not isinstance(claimed_hash, str) or not HASH_PATTERN.fullmatch(claimed_hash):
            raise BundleError(f"invalid manifest hash for {name}")
        if _sha256(files[name]) != claimed_hash:
            raise BundleError(f"artifact hash mismatch: {name}")
    claimed_bundle_hash = manifest.get("bundle_hash")
    if not isinstance(claimed_bundle_hash, str) or not HASH_PATTERN.fullmatch(claimed_bundle_hash):
        raise BundleError("bundle_hash has invalid format")
    if claimed_bundle_hash != calculate_bundle_hash(manifest):
        raise BundleError("bundle_hash does not match manifest")
    return manifest, files

def _certificates(data: bytes, label: str) -> list[x509.Certificate]:
    try:
        if b"-----BEGIN CERTIFICATE-----" in data:
            certificates = x509.load_pem_x509_certificates(data)
        else:
            certificates = [x509.load_der_x509_certificate(data)]
    except ValueError as exc:
        raise BundleError(f"{label} contains invalid certificates: {exc}") from exc
    if not certificates:
        raise BundleError(f"{label} contains no certificates")
    return certificates


def _normalize_fingerprint(value: str) -> str:
    normalized = value.lower()
    if not normalized.startswith("sha256:"):
        normalized = "sha256:" + normalized
    if not HASH_PATTERN.fullmatch(normalized):
        raise BundleError(f"invalid expected TSA root fingerprint: {value}")
    return normalized


def verify_bundle(
    path: Path | bytes,
    expected_issuer_trust_hash: str,
    expected_witness_policy_hash: str,
    expected_checkpoint_hash: str,
    expected_tsa_root_fingerprints: list[str],
    expected_report_hash: str | None = None,
) -> BundleVerification:
    manifest, files = read_bundle(path)
    artifacts = manifest["artifacts"]
    errors: list[str] = []
    warnings: list[str] = []
    report = _strict_json(files[artifacts["report"]], "report")
    signature = _strict_json(
        files[artifacts["issuer_signature"]], "issuer signature"
    )
    trust = _strict_json(files[artifacts["issuer_trust"]], "issuer trust")
    log = _strict_json(files[artifacts["transparency_log"]], "transparency log")
    policy = _strict_json(files[artifacts["witness_policy"]], "witness policy")
    attestations = [
        _strict_json(files[name], f"witness attestation {index}")
        for index, name in enumerate(artifacts["witness_attestations"])
    ]
    timestamp = _strict_json(files[artifacts["rfc3161"]], "RFC 3161 evidence")

    report_result = verify_report(report, expected_report_hash, require_passed=True)
    errors.extend(report_result.errors)
    trusted_result = verify_trusted_report(
        report,
        signature,
        trust,
        expected_issuer_trust_hash,
        require_passed=True,
    )
    errors.extend(trusted_result.errors)
    log_result = verify_log(log, expected_checkpoint_hash)
    errors.extend(log_result.errors)
    entry_index = manifest["bindings"]["log_entry_index"]
    entries = log.get("entries")
    if not isinstance(entries, list) or entry_index >= len(entries):
        errors.append("bound log_entry_index is outside transparency log")
    else:
        entry = entries[entry_index]
        if entry.get("report_hash") != report.get("report_hash"):
            errors.append("bound log entry does not reference bundled report")
        if entry.get("signature_hash") != signature_hash(signature):
            errors.append("bound log entry does not reference bundled issuer signature")

    quorum_result = verify_quorum(
        log, attestations, policy, expected_witness_policy_hash
    )
    if not quorum_result.valid:
        errors.append(
            f"witness quorum not met: accepted={len(quorum_result.accepted_witnesses)} "
            f"threshold={quorum_result.threshold}"
        )
    warnings.extend(quorum_result.rejected_evidence)

    roots = [
        certificate
        for name in artifacts["tsa_roots"]
        for certificate in _certificates(files[name], name)
    ]
    intermediates = [
        certificate
        for name in artifacts["tsa_intermediates"]
        for certificate in _certificates(files[name], name)
    ]
    actual_root_fingerprints = {
        "sha256:" + certificate.fingerprint(hashes.SHA256()).hex()
        for certificate in roots
    }
    expected_root_fingerprints = {
        _normalize_fingerprint(value) for value in expected_tsa_root_fingerprints
    }
    if not expected_root_fingerprints:
        errors.append("at least one independently expected TSA root is required")
    elif actual_root_fingerprints != expected_root_fingerprints:
        errors.append("bundled TSA roots do not exactly match expected fingerprints")
    timestamp_result = verify_evidence(log, timestamp, roots, intermediates)
    errors.extend(timestamp_result.errors)
    if timestamp.get("checkpoint_hash") != expected_checkpoint_hash:
        errors.append("RFC 3161 token does not bind expected checkpoint")

    return BundleVerification(
        valid=not errors,
        report_hash=(
            report.get("report_hash")
            if isinstance(report.get("report_hash"), str)
            else None
        ),
        checkpoint_hash=log_result.checkpoint_hash,
        accepted_witnesses=quorum_result.accepted_witnesses,
        granted_at=timestamp_result.granted_at,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )

def _read_input(path: Path, label: str, json_required: bool = True) -> bytes:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BundleError(f"cannot read {label}: {exc}") from exc
    if len(data) > MAX_FILE_BYTES:
        raise BundleError(f"{label} exceeds size limit")
    if json_required:
        _strict_json(data, label)
    return data


def build_bundle_bytes(
    report_path: Path,
    signature_path: Path,
    trust_path: Path,
    log_path: Path,
    witness_policy_path: Path,
    witness_attestation_paths: list[Path],
    timestamp_path: Path,
    tsa_root_paths: list[Path],
    tsa_intermediate_paths: list[Path] | None = None,
    log_entry_index: int = 0,
) -> bytes:
    if type(log_entry_index) is not int or log_entry_index < 0:
        raise BundleError("log_entry_index must be a non-negative integer")
    if not witness_attestation_paths:
        raise BundleError("at least one witness attestation is required")
    if not tsa_root_paths:
        raise BundleError("at least one TSA root is required")
    artifacts: dict[str, Any] = {
        "report": "report.json",
        "issuer_signature": "issuer-signature.json",
        "issuer_trust": "issuer-trust.json",
        "transparency_log": "transparency-log.json",
        "witness_policy": "witness-policy.json",
        "witness_attestations": [
            f"witnesses/{index}.json"
            for index in range(len(witness_attestation_paths))
        ],
        "rfc3161": "rfc3161.json",
        "tsa_roots": [f"tsa-roots/{index}.pem" for index in range(len(tsa_root_paths))],
        "tsa_intermediates": [
            f"tsa-intermediates/{index}.pem"
            for index in range(len(tsa_intermediate_paths or []))
        ],
    }
    source_pairs: list[tuple[str, Path, bool]] = [
        (artifacts["report"], report_path, True),
        (artifacts["issuer_signature"], signature_path, True),
        (artifacts["issuer_trust"], trust_path, True),
        (artifacts["transparency_log"], log_path, True),
        (artifacts["witness_policy"], witness_policy_path, True),
        (artifacts["rfc3161"], timestamp_path, True),
    ]
    source_pairs.extend(
        (name, path, True)
        for name, path in zip(
            artifacts["witness_attestations"], witness_attestation_paths
        )
    )
    source_pairs.extend(
        (name, path, False)
        for name, path in zip(artifacts["tsa_roots"], tsa_root_paths)
    )
    source_pairs.extend(
        (name, path, False)
        for name, path in zip(
            artifacts["tsa_intermediates"], tsa_intermediate_paths or []
        )
    )
    files = {
        name: _read_input(path, name, json_required)
        for name, path, json_required in source_pairs
    }
    for name in artifacts["tsa_roots"] + artifacts["tsa_intermediates"]:
        _certificates(files[name], name)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifacts": artifacts,
        "bindings": {"log_entry_index": log_entry_index},
        "files": {name: _sha256(data) for name, data in sorted(files.items())},
    }
    manifest["bundle_hash"] = calculate_bundle_hash(manifest)
    manifest_bytes = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    output = io.BytesIO()
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in [(MANIFEST_NAME, manifest_bytes), *sorted(files.items())]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def write_bundle(data: bytes, output: Path, force: bool = False) -> None:
    if output.exists() and not force:
        raise BundleError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)

def _add_anchor_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-report-hash")
    parser.add_argument("--expected-issuer-trust-hash", required=True)
    parser.add_argument("--expected-witness-policy-hash", required=True)
    parser.add_argument("--expected-checkpoint-hash", required=True)
    parser.add_argument(
        "--expected-tsa-root-sha256", action="append", required=True
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", action="version", version=f"area-one-verify {VERSION}"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--report", type=Path, required=True)
    create.add_argument("--issuer-signature", type=Path, required=True)
    create.add_argument("--issuer-trust", type=Path, required=True)
    create.add_argument("--transparency-log", type=Path, required=True)
    create.add_argument("--log-entry-index", type=int, default=0)
    create.add_argument("--witness-policy", type=Path, required=True)
    create.add_argument(
        "--witness-attestation", type=Path, action="append", required=True
    )
    create.add_argument("--rfc3161", type=Path, required=True)
    create.add_argument("--tsa-root", type=Path, action="append", required=True)
    create.add_argument("--tsa-intermediate", type=Path, action="append")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--force", action="store_true")
    _add_anchor_arguments(create)
    verify = commands.add_parser("verify")
    verify.add_argument("bundle", type=Path)
    _add_anchor_arguments(verify)
    return parser


def _verify_with_args(source: Path | bytes, args: argparse.Namespace) -> BundleVerification:
    return verify_bundle(
        source,
        args.expected_issuer_trust_hash,
        args.expected_witness_policy_hash,
        args.expected_checkpoint_hash,
        args.expected_tsa_root_sha256,
        args.expected_report_hash,
    )


def _print_result(result: BundleVerification) -> None:
    print(f"bundle_valid={str(result.valid).lower()}")
    print(f"report_hash={result.report_hash or 'missing'}")
    print(f"checkpoint_hash={result.checkpoint_hash or 'missing'}")
    print(f"accepted_witnesses={len(result.accepted_witnesses)}")
    print(f"rfc3161_granted_at={result.granted_at or 'missing'}")
    for witness in result.accepted_witnesses:
        print(f"accepted_witness={witness}")
    for warning in result.warnings:
        print(f"warning={warning}")
    for error in result.errors:
        print(f"error={error}")

def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            data = build_bundle_bytes(
                args.report,
                args.issuer_signature,
                args.issuer_trust,
                args.transparency_log,
                args.witness_policy,
                args.witness_attestation,
                args.rfc3161,
                args.tsa_root,
                args.tsa_intermediate,
                args.log_entry_index,
            )
            result = _verify_with_args(data, args)
            _print_result(result)
            if not result.valid:
                print("bundle_written=false")
                return 1
            write_bundle(data, args.output, args.force)
            manifest, _ = read_bundle(data)
            print(f"bundle_written={args.output}")
            print(f"bundle_hash={manifest['bundle_hash']}")
            return 0
        result = _verify_with_args(args.bundle, args)
    except BundleError as exc:
        print("bundle_valid=false")
        print(f"error={exc}")
        return 2

    _print_result(result)
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
