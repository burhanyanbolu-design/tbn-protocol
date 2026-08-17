#!/usr/bin/env python3
"""Request and independently verify RFC 3161 timestamps for log checkpoints."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rfc3161ng
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, ed448, padding, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, ExtensionOID
from pyasn1.codec.der import decoder, encoder
from pyasn1.type import univ

from report_file_verifier import canonical_json, load_report
from report_signature import parse_utc_timestamp
from transparency_log import HASH_PATTERN, verify_log


SCHEMA_VERSION = "area-one-rfc3161-evidence/1.0"
SHA256_OID = "2.16.840.1.101.3.4.2.1"
MESSAGE_DIGEST_OID = "1.2.840.113549.1.9.4"
CONTENT_TYPE_OID = "1.2.840.113549.1.9.3"
RSA_PSS_OID = "1.2.840.113549.1.1.10"
EVIDENCE_FIELDS = {
    "schema_version", "tsa_url", "log_id", "tree_size", "checkpoint_hash",
    "hash_algorithm", "nonce", "request_der", "response_der", "granted_at",
    "policy_oid", "serial_number", "tsa_subject", "tsa_certificate_sha256",
    "evidence_hash",
}
HASH_ALGORITHMS = {
    "1.3.14.3.2.26": hashes.SHA1,
    SHA256_OID: hashes.SHA256,
    "2.16.840.1.101.3.4.2.2": hashes.SHA384,
    "2.16.840.1.101.3.4.2.3": hashes.SHA512,
}


class TimestampError(ValueError):
    """Raised when RFC 3161 evidence cannot be safely created or verified."""


@dataclass(frozen=True)
class TokenVerification:
    signer: x509.Certificate
    granted_at: datetime
    policy_oid: str
    serial_number: str


@dataclass(frozen=True)
class EvidenceVerification:
    valid: bool
    checkpoint_hash: str | None
    granted_at: str | None
    tsa_subject: str | None
    errors: tuple[str, ...]

def load_certificates(path: Path) -> list[x509.Certificate]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise TimestampError(f"cannot read certificate file: {exc}") from exc
    try:
        if b"-----BEGIN CERTIFICATE-----" in data:
            certificates = x509.load_pem_x509_certificates(data)
        else:
            certificates = [x509.load_der_x509_certificate(data)]
    except ValueError as exc:
        raise TimestampError(f"invalid certificate file: {exc}") from exc
    if not certificates:
        raise TimestampError("certificate file contains no certificates")
    return certificates


def _fingerprint(certificate: x509.Certificate) -> bytes:
    return certificate.fingerprint(hashes.SHA256())


def _verify_certificate_signature(
    certificate: x509.Certificate, issuer: x509.Certificate
) -> None:
    public_key = issuer.public_key()
    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            parameters = certificate.signature_algorithm_parameters
            if not isinstance(parameters, (padding.PKCS1v15, padding.PSS)):
                raise TimestampError("unsupported RSA certificate signature parameters")
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                parameters,
                certificate.signature_hash_algorithm,
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                ec.ECDSA(certificate.signature_hash_algorithm),
            )
        elif isinstance(public_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
            public_key.verify(certificate.signature, certificate.tbs_certificate_bytes)
        else:
            raise TimestampError("unsupported certificate public-key type")
    except InvalidSignature as exc:
        raise TimestampError("certificate signature verification failed") from exc


def _require_valid_at(certificate: x509.Certificate, moment: datetime) -> None:
    if not certificate.not_valid_before_utc <= moment <= certificate.not_valid_after_utc:
        raise TimestampError("certificate was not valid at timestamp generation time")


def _require_ca(certificate: x509.Certificate, ca_below: int) -> None:
    try:
        constraints = certificate.extensions.get_extension_for_oid(
            ExtensionOID.BASIC_CONSTRAINTS
        ).value
    except x509.ExtensionNotFound as exc:
        raise TimestampError("issuer certificate lacks Basic Constraints") from exc
    if not constraints.ca:
        raise TimestampError("issuer certificate is not a CA")
    if constraints.path_length is not None and ca_below > constraints.path_length:
        raise TimestampError("certificate path-length constraint exceeded")
    try:
        usage = certificate.extensions.get_extension_for_oid(
            ExtensionOID.KEY_USAGE
        ).value
        if not usage.key_cert_sign:
            raise TimestampError("issuer certificate cannot sign certificates")
    except x509.ExtensionNotFound:
        pass

def _require_tsa_certificate(certificate: x509.Certificate, moment: datetime) -> None:
    _require_valid_at(certificate, moment)
    try:
        constraints = certificate.extensions.get_extension_for_oid(
            ExtensionOID.BASIC_CONSTRAINTS
        ).value
        if constraints.ca:
            raise TimestampError("TSA signer certificate cannot be a CA")
    except x509.ExtensionNotFound:
        pass
    try:
        extension = certificate.extensions.get_extension_for_oid(
            ExtensionOID.EXTENDED_KEY_USAGE
        )
    except x509.ExtensionNotFound as exc:
        raise TimestampError("TSA signer certificate lacks Extended Key Usage") from exc
    if not extension.critical or set(extension.value) != {ExtendedKeyUsageOID.TIME_STAMPING}:
        raise TimestampError("TSA Extended Key Usage must be critical and timestamping-only")
    try:
        usage = certificate.extensions.get_extension_for_oid(ExtensionOID.KEY_USAGE).value
        if not (usage.digital_signature or usage.content_commitment):
            raise TimestampError("TSA certificate cannot create signatures")
    except x509.ExtensionNotFound:
        pass


def verify_certificate_chain(
    signer: x509.Certificate,
    included: list[x509.Certificate],
    trust_roots: list[x509.Certificate],
    moment: datetime,
) -> None:
    if not trust_roots:
        raise TimestampError("at least one explicit trust root is required")
    root_fingerprints = {_fingerprint(root) for root in trust_roots}
    candidates = included + trust_roots

    def walk(
        current: x509.Certificate,
        visited: set[bytes],
        ca_below: int,
    ) -> bool:
        current_fingerprint = _fingerprint(current)
        if current_fingerprint in root_fingerprints:
            _require_valid_at(current, moment)
            _require_ca(current, ca_below)
            return True
        for issuer in candidates:
            issuer_fingerprint = _fingerprint(issuer)
            if issuer_fingerprint in visited or issuer.subject != current.issuer:
                continue
            try:
                _require_valid_at(issuer, moment)
                _require_ca(issuer, ca_below)
                _verify_certificate_signature(current, issuer)
                if walk(issuer, visited | {issuer_fingerprint}, ca_below + 1):
                    return True
            except TimestampError:
                continue
        return False

    _require_tsa_certificate(signer, moment)
    if not walk(signer, {_fingerprint(signer)}, 0):
        raise TimestampError("TSA certificate does not chain to an explicit trust root")

def _hash_algorithm(oid: str) -> hashes.HashAlgorithm:
    factory = HASH_ALGORITHMS.get(oid)
    if factory is None:
        raise TimestampError(f"unsupported digest algorithm OID: {oid}")
    return factory()


def _included_certificates(signed_data: Any) -> list[x509.Certificate]:
    certificates: list[x509.Certificate] = []
    for choice in signed_data["certificates"]:
        try:
            encoded = encoder.encode(choice[0])
            certificates.append(x509.load_der_x509_certificate(encoded))
        except (ValueError, TypeError, IndexError) as exc:
            raise TimestampError(f"invalid embedded TSA certificate: {exc}") from exc
    if not certificates:
        raise TimestampError("timestamp response did not include a TSA certificate")
    return certificates


def _signed_content_and_digest(signer_info: Any, content: bytes) -> tuple[bytes, hashes.HashAlgorithm]:
    digest_oid = str(signer_info["digestAlgorithm"]["algorithm"])
    algorithm = _hash_algorithm(digest_oid)
    attributes = signer_info["authenticatedAttributes"]
    if not len(attributes):
        raise TimestampError("RFC 3161 signer must include authenticated attributes")
    expected_digest = hashlib.new(algorithm.name, content).digest()
    found_digest = False
    found_content_type = False
    for attribute in attributes:
        oid = str(attribute[0])
        if oid == MESSAGE_DIGEST_OID:
            value, remainder = decoder.decode(
                bytes(attribute[1][0]), asn1Spec=univ.OctetString()
            )
            if remainder or bytes(value) != expected_digest:
                raise TimestampError("CMS signed message digest does not match TSTInfo")
            found_digest = True
        elif oid == CONTENT_TYPE_OID:
            value, remainder = decoder.decode(
                bytes(attribute[1][0]), asn1Spec=univ.ObjectIdentifier()
            )
            if remainder or str(value) != str(rfc3161ng.id_ct_TSTInfo):
                raise TimestampError("CMS signed content type is not TSTInfo")
            found_content_type = True
    if not found_digest or not found_content_type:
        raise TimestampError("CMS signed attributes omit digest or content type")
    signed_set = univ.SetOf()
    for index, attribute in enumerate(attributes):
        signed_set.setComponentByPosition(index, attribute)
    return encoder.encode(signed_set), algorithm


def _verify_cms_signature(
    signer_info: Any,
    signed_bytes: bytes,
    algorithm: hashes.HashAlgorithm,
    certificate: x509.Certificate,
) -> None:
    signature = bytes(signer_info["encryptedDigest"])
    signature_oid = str(signer_info["digestEncryptionAlgorithm"]["algorithm"])
    public_key = certificate.public_key()
    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            if signature_oid == RSA_PSS_OID:
                raise TimestampError("RSA-PSS CMS parameters are not supported by this profile")
            public_key.verify(signature, signed_bytes, padding.PKCS1v15(), algorithm)
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(signature, signed_bytes, ec.ECDSA(algorithm))
        elif isinstance(public_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
            public_key.verify(signature, signed_bytes)
        else:
            raise TimestampError("unsupported TSA signer public-key type")
    except InvalidSignature as exc:
        raise TimestampError("CMS timestamp signature is invalid") from exc

def verify_token(
    request_der: bytes,
    response_der: bytes,
    checkpoint_hash: str,
    trust_roots: list[x509.Certificate],
    extra_certificates: list[x509.Certificate] | None = None,
) -> TokenVerification:
    if not HASH_PATTERN.fullmatch(checkpoint_hash):
        raise TimestampError("checkpoint_hash has invalid format")
    try:
        request = rfc3161ng.decode_timestamp_request(request_der)
        response = rfc3161ng.decode_timestamp_response(response_der)
    except Exception as exc:
        raise TimestampError(f"invalid RFC 3161 DER: {exc}") from exc
    status = int(response["status"]["status"])
    if status not in (0, 1):
        raise TimestampError(f"TSA did not grant timestamp request; status={status}")
    token = response.time_stamp_token
    tst_info = token.tst_info
    request_imprint = request["messageImprint"]
    response_imprint = tst_info["messageImprint"]
    expected_digest = bytes.fromhex(checkpoint_hash[7:])
    if str(request_imprint["hashAlgorithm"]["algorithm"]) != SHA256_OID:
        raise TimestampError("timestamp request does not use SHA-256")
    if bytes(request_imprint["hashedMessage"]) != expected_digest:
        raise TimestampError("timestamp request imprint does not match checkpoint")
    if str(response_imprint["hashAlgorithm"]["algorithm"]) != SHA256_OID:
        raise TimestampError("timestamp response imprint does not use SHA-256")
    if bytes(response_imprint["hashedMessage"]) != expected_digest:
        raise TimestampError("timestamp response imprint does not match checkpoint")
    if not request["nonce"].hasValue() or not tst_info["nonce"].hasValue():
        raise TimestampError("RFC 3161 request and response must contain a nonce")
    if int(request["nonce"]) != int(tst_info["nonce"]):
        raise TimestampError("RFC 3161 response nonce does not match request")
    if not bool(request["certReq"]):
        raise TimestampError("timestamp request must ask TSA to include its certificate")

    try:
        granted_at = rfc3161ng.get_timestamp(token, naive=False).astimezone(timezone.utc)
    except Exception as exc:
        raise TimestampError(f"invalid TSA generation time: {exc}") from exc
    signed_data = token.content
    if str(signed_data["contentInfo"]["contentType"]) != str(rfc3161ng.id_ct_TSTInfo):
        raise TimestampError("CMS encapsulated content is not TSTInfo")
    content_value, remainder = decoder.decode(
        bytes(signed_data["contentInfo"]["content"]), asn1Spec=univ.OctetString()
    )
    if remainder:
        raise TimestampError("extra bytes follow encapsulated TSTInfo")
    content = bytes(content_value)
    if not len(signed_data["signerInfos"]):
        raise TimestampError("timestamp response has no CMS signer")
    if len(signed_data["signerInfos"]) != 1:
        raise TimestampError("timestamp profile requires exactly one CMS signer")
    signer_info = signed_data["signerInfos"][0]
    signed_bytes, digest_algorithm = _signed_content_and_digest(signer_info, content)
    signer_serial = int(signer_info["issuerAndSerialNumber"]["serialNumber"])
    included = _included_certificates(signed_data)
    matching = [certificate for certificate in included if certificate.serial_number == signer_serial]
    if not matching:
        raise TimestampError("embedded certificates do not match CMS signer identifier")
    signer = matching[0]
    _verify_cms_signature(signer_info, signed_bytes, digest_algorithm, signer)
    verify_certificate_chain(
        signer,
        [certificate for certificate in included if certificate != signer]
        + list(extra_certificates or []),
        trust_roots,
        granted_at,
    )
    return TokenVerification(
        signer=signer,
        granted_at=granted_at,
        policy_oid=str(tst_info["policy"]),
        serial_number=str(int(tst_info["serialNumber"])),
    )

def calculate_evidence_hash(evidence: dict[str, Any]) -> str:
    body = dict(evidence)
    body.pop("evidence_hash", None)
    payload = b"AREA-ONE-RFC3161\x00" + canonical_json(body).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def request_timestamp(
    log: dict[str, Any],
    expected_checkpoint_hash: str,
    tsa_url: str,
    trust_roots: list[x509.Certificate],
    extra_certificates: list[x509.Certificate] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    log_result = verify_log(log, expected_checkpoint_hash)
    if not log_result.valid or log_result.tree_size == 0:
        detail = "; ".join(log_result.errors) or "empty logs cannot be timestamped"
        raise TimestampError("checkpoint verification failed: " + detail)
    if not tsa_url.startswith("https://"):
        raise TimestampError("TSA URL must use HTTPS")
    nonce = secrets.randbits(128) or 1
    digest = bytes.fromhex(expected_checkpoint_hash[7:])
    request_object = rfc3161ng.make_timestamp_request(
        digest=digest,
        hashname="sha256",
        include_tsa_certificate=True,
        nonce=nonce,
    )
    request_der = rfc3161ng.encode_timestamp_request(request_object)
    http_request = urllib.request.Request(
        tsa_url,
        data=request_der,
        headers={
            "Content-Type": "application/timestamp-query",
            "Accept": "application/timestamp-reply",
            "User-Agent": "Area-One-RFC3161/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if content_type != "application/timestamp-reply":
                raise TimestampError(
                    f"TSA returned unexpected content type: {content_type}"
                )
            response_der = response.read(1_048_577)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TimestampError(f"TSA request failed: {exc}") from exc
    if len(response_der) > 1_048_576:
        raise TimestampError("TSA response exceeds 1 MiB safety limit")
    token = verify_token(
        request_der,
        response_der,
        expected_checkpoint_hash,
        trust_roots,
        extra_certificates,
    )
    checkpoint = log["checkpoints"][-1]
    checkpoint_generated = parse_utc_timestamp(
        checkpoint["generated_at"], "checkpoint.generated_at"
    )
    if token.granted_at < checkpoint_generated:
        raise TimestampError("RFC 3161 grant predates checkpoint generation")
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tsa_url": tsa_url,
        "log_id": log["log_id"],
        "tree_size": checkpoint["tree_size"],
        "checkpoint_hash": expected_checkpoint_hash,
        "hash_algorithm": "sha256",
        "nonce": str(nonce),
        "request_der": base64.b64encode(request_der).decode("ascii"),
        "response_der": base64.b64encode(response_der).decode("ascii"),
        "granted_at": _format_time(token.granted_at),
        "policy_oid": token.policy_oid,
        "serial_number": token.serial_number,
        "tsa_subject": token.signer.subject.rfc4514_string(),
        "tsa_certificate_sha256": "sha256:" + _fingerprint(token.signer).hex(),
    }
    evidence["evidence_hash"] = calculate_evidence_hash(evidence)
    return evidence

def verify_evidence(
    log: dict[str, Any],
    evidence: dict[str, Any],
    trust_roots: list[x509.Certificate],
    extra_certificates: list[x509.Certificate] | None = None,
) -> EvidenceVerification:
    errors: list[str] = []
    checkpoint_hash = evidence.get("checkpoint_hash")
    if set(evidence) != EVIDENCE_FIELDS:
        errors.append("RFC 3161 evidence fields differ from schema")
    if evidence.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported RFC 3161 evidence schema_version")
    if not isinstance(evidence.get("tsa_url"), str) or not evidence["tsa_url"].startswith("https://"):
        errors.append("tsa_url must use HTTPS")
    if evidence.get("hash_algorithm") != "sha256":
        errors.append("only SHA-256 checkpoint imprints are supported")
    claimed_evidence_hash = evidence.get("evidence_hash")
    if not isinstance(claimed_evidence_hash, str) or not HASH_PATTERN.fullmatch(
        claimed_evidence_hash
    ):
        errors.append("evidence_hash has invalid format")
    elif not hmac_compare(claimed_evidence_hash, calculate_evidence_hash(evidence)):
        errors.append("evidence_hash does not match evidence content")
    if not isinstance(checkpoint_hash, str) or not HASH_PATTERN.fullmatch(checkpoint_hash):
        errors.append("checkpoint_hash has invalid format")
    else:
        log_result = verify_log(log, checkpoint_hash)
        errors.extend(log_result.errors)
        if evidence.get("log_id") != log.get("log_id"):
            errors.append("evidence log_id does not match log")
        if evidence.get("tree_size") != log_result.tree_size:
            errors.append("evidence tree_size does not match log")

    try:
        request_der = base64.b64decode(evidence.get("request_der", ""), validate=True)
        response_der = base64.b64decode(evidence.get("response_der", ""), validate=True)
        request = rfc3161ng.decode_timestamp_request(request_der)
        if str(int(request["nonce"])) != evidence.get("nonce"):
            errors.append("evidence nonce does not match timestamp request")
        if isinstance(checkpoint_hash, str) and HASH_PATTERN.fullmatch(checkpoint_hash):
            token = verify_token(
                request_der,
                response_der,
                checkpoint_hash,
                trust_roots,
                extra_certificates,
            )
            checkpoints = log.get("checkpoints")
            if isinstance(checkpoints, list) and checkpoints:
                generated_at = parse_utc_timestamp(
                    checkpoints[-1].get("generated_at"),
                    "checkpoint.generated_at",
                )
                if token.granted_at < generated_at:
                    errors.append("RFC 3161 grant predates checkpoint generation")
            comparisons = {
                "granted_at": _format_time(token.granted_at),
                "policy_oid": token.policy_oid,
                "serial_number": token.serial_number,
                "tsa_subject": token.signer.subject.rfc4514_string(),
                "tsa_certificate_sha256": "sha256:" + _fingerprint(token.signer).hex(),
            }
            for field, expected in comparisons.items():
                if evidence.get(field) != expected:
                    errors.append(f"evidence {field} does not match timestamp token")
    except (ValueError, TypeError, binascii.Error, TimestampError) as exc:
        errors.append(f"RFC 3161 verification failed: {exc}")

    return EvidenceVerification(
        valid=not errors,
        checkpoint_hash=checkpoint_hash if isinstance(checkpoint_hash, str) else None,
        granted_at=(
            evidence.get("granted_at")
            if isinstance(evidence.get("granted_at"), str)
            else None
        ),
        tsa_subject=(
            evidence.get("tsa_subject")
            if isinstance(evidence.get("tsa_subject"), str)
            else None
        ),
        errors=tuple(errors),
    )


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)

def _load_many(paths: list[Path] | None) -> list[x509.Certificate]:
    return [certificate for path in (paths or []) for certificate in load_certificates(path)]


def _write_json(value: dict[str, Any], output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise TimestampError("output exists; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    request = commands.add_parser("request")
    request.add_argument("log", type=Path)
    request.add_argument("--expected-checkpoint-hash", required=True)
    request.add_argument("--tsa-url", required=True)
    request.add_argument("--ca-file", type=Path, action="append", required=True)
    request.add_argument("--untrusted-file", type=Path, action="append")
    request.add_argument("--timeout", type=float, default=15.0)
    request.add_argument("--output", type=Path, required=True)
    request.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("log", type=Path)
    verify.add_argument("evidence", type=Path)
    verify.add_argument("--ca-file", type=Path, action="append", required=True)
    verify.add_argument("--untrusted-file", type=Path, action="append")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        roots = _load_many(args.ca_file)
        intermediates = _load_many(args.untrusted_file)
        log = load_report(args.log)
        if args.command == "request":
            if args.timeout <= 0:
                raise TimestampError("timeout must be positive")
            evidence = request_timestamp(
                log,
                args.expected_checkpoint_hash,
                args.tsa_url,
                roots,
                intermediates,
                args.timeout,
            )
            _write_json(evidence, args.output, args.force)
            print(f"evidence_written={args.output}")
            print(f"checkpoint_hash={evidence['checkpoint_hash']}")
            print(f"granted_at={evidence['granted_at']}")
            print(f"tsa_subject={evidence['tsa_subject']}")
            return 0
        result = verify_evidence(
            log,
            load_report(args.evidence),
            roots,
            intermediates,
        )
    except (TimestampError, ValueError) as exc:
        print("rfc3161_valid=false")
        print(f"error={exc}")
        return 2

    print(f"rfc3161_valid={str(result.valid).lower()}")
    print(f"checkpoint_hash={result.checkpoint_hash or 'missing'}")
    print(f"granted_at={result.granted_at or 'missing'}")
    print(f"tsa_subject={result.tsa_subject or 'missing'}")
    for error in result.errors:
        print(f"error={error}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
