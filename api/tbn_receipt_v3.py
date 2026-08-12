"""
TBN Receipt v2.1 — Gate 2 hardened build
=========================================
Builds on v2.0 with the following Gate 2 remediation changes:

  RB-01: Full RFC 3161 .tsr token retention (not just token hash)
         Machine-readable timestamp status enumeration
  RB-04: Formal canonical rules documented in code
  RB-05: Hardened fail-closed verifier behaviour

Changes from v2.0:
  - rfc3161.token_b64: full binary .tsr response, base64-encoded
  - rfc3161.imprint: the exact SHA-256 hex of the canonical body used as message imprint
  - rfc3161.imprint_algorithm: always "sha256"
  - rfc3161.status enum: anchored | not_requested | tsa_unavailable | tsa_rejected | tsa_timeout
  - rfc3161.tsa_cert_chain_b64: base64 of the TSA cert chain (DER)
  - Token also saved as binary .tsr file in TSR_STORE_DIR

Original receipts 3329-3333 are PRESERVED UNCHANGED. This module generates
new receipts with new identifiers, chain indices, and timestamps.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
import os
import json
import uuid
import hashlib
import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

# ── Construction identity (added 7 Aug 2026 — Register item 8) ────────
# WHY: `schema_version` names a FIELD SET, not the rules by which a receipt is
# canonicalised, hashed, chained and signed. That gap caused a real failure —
# two different field sets shared the label "tbn-receipt/2.1", so a cutover
# defined as "the first receipt carrying tbn-receipt/2.1" also matched an
# earlier receipt and a verifier re-deriving it from the stated rule got the
# wrong answer.
#
# A name alone is not enough either: a name can be reinterpreted and a pointer
# can be repointed. So the receipt carries BOTH the name and the DIGEST of the
# frozen specification. The name is for humans; the digest is what makes the
# rules unreinterpretable. If the rules change the digest changes, and every
# receipt signed under the old digest stays bound to the old rules.
#
# The digest is over data/spec-tbn-receipt-1.md with LF line endings — see
# section 0 of that document. LF because that is what git stores; a Windows
# checkout materialises CRLF and would hash to a different, wrong value.
#
# THESE VALUES ARE NOT DEFINED HERE. They are imported from tbn_construction,
# which is the single source of truth. Register item 17 happened because two
# modules each owned their own copy of a value that had to agree across both.
# Re-declaring any of them locally would reintroduce that defect.
# The MODULE is imported, not just names from it, so that anything which can
# change at runtime (the spec digest) is always read live via _tc.<name> rather
# than through a binding frozen at import time.
try:
    from . import tbn_construction as _tc
except ImportError:
    from api import tbn_construction as _tc

CONSTRUCTION_SPEC_PATH = _tc.CONSTRUCTION_SPEC_PATH
MERKLE_CONSTRUCTION = _tc.MERKLE_CONSTRUCTION
CURRENT_SCHEMA = _tc.CURRENT_SCHEMA
SUPPORTED_SCHEMAS = _tc.SUPPORTED_SCHEMAS
CONSTRUCTION_FIELDS = _tc.CONSTRUCTION_FIELDS
construction_fields = _tc.construction_fields
spec_digest_from_disk = _tc.spec_digest_from_disk
verify_spec_digest = _tc.verify_spec_digest


def __getattr__(name):
    """Read CONSTRUCTION and CONSTRUCTION_SPEC live from tbn_construction.

    Deliberately NOT module-level constants. A test proved why: bound at import
    time, they silently diverge from the source the moment anything changes the
    value there, and the spec-drift guard stops firing. Module __getattr__ makes
    the indirection unavoidable while keeping `r3.CONSTRUCTION` readable for
    callers."""
    if name in ("CONSTRUCTION", "CONSTRUCTION_SPEC"):
        return getattr(_tc, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

SCHEMA_VERSION = CURRENT_SCHEMA  # tbn-receipt/2.3 — see tbn_construction for the
                                 # label-to-field-set mapping. 2.2 and earlier
                                 # remain valid and are NOT retroactively relabelled.
_SCHEMA_HISTORY_NOTE = "tbn-receipt/2.2"  # 2.2: full RFC 3161 token retention (rfc3161 object with
                                     # token_b64/imprint kept), distinct from 2.1 (tsa_anchored
                                     # bool only, no token retained). 2.1 and 2.2 previously
                                     # shared the "tbn-receipt/2.1" label despite different field
                                     # sets — this collided with the SB 942 cutover, pinned at
                                     # chain_index 3952 and defined as "the first receipt carrying
                                     # schema tbn-receipt/2.1" — a definition that incorrectly also
                                     # matched chain_index 3335 (the gate2 sample, issued 16 July,
                                     # 8 days before the cutover). Found by Shango's independent
                                     # verification of the gate2 receipts, 27 July 2026 (Disagreement
                                     # Register item 17). 2.1 receipts already on disk/published are
                                     # NOT retroactively renamed — this only affects new receipts
                                     # issued via this module going forward.
SIGNING_KEY_PATH = "data/tbn_signing_key.pem"
PUBLIC_KEY_PATH = "data/tbn_signing_public.pem"
CHAIN_FILE = "data/v2_receipt_chain.json"
TSR_STORE_DIR = "data/tsr_tokens"

# --- RFC 3161 status enumeration (RB-01) ---
TSA_STATUS_ANCHORED = "anchored"
TSA_STATUS_NOT_REQUESTED = "not_requested"
TSA_STATUS_UNAVAILABLE = "tsa_unavailable"
TSA_STATUS_REJECTED = "tsa_rejected"
TSA_STATUS_TIMEOUT = "tsa_timeout"

VALID_TSA_STATUSES = {
    TSA_STATUS_ANCHORED,
    TSA_STATUS_NOT_REQUESTED,
    TSA_STATUS_UNAVAILABLE,
    TSA_STATUS_REJECTED,
    TSA_STATUS_TIMEOUT,
}


# NOTE — spec_digest_from_disk() and verify_spec_digest() are IMPORTED from
# tbn_construction above and deliberately NOT redefined here.
#
# They were briefly defined locally in this module, and a test caught the
# consequence immediately: the local copies closed over this module's own
# import-time binding of CONSTRUCTION_SPEC, so editing the value in
# tbn_construction no longer reached them and the spec-drift guard stopped
# firing. That is the item 17 defect in miniature, inside the very code written
# to prevent it. Left as a comment because the temptation to "just add a small
# local helper" is what causes it.


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_bytes(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def _load_keys():
    with open(SIGNING_KEY_PATH, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    with open(PUBLIC_KEY_PATH, "rb") as f:
        pub_pem = f.read()
    return priv, pub_pem


def key_id(pub_pem: bytes) -> str:
    """Stable identifier for the public key = first 16 hex of its SHA-256."""
    return "tbnkey_" + _sha256_hex(pub_pem)[:16]


def _load_chain():
    if os.path.exists(CHAIN_FILE):
        with open(CHAIN_FILE) as f:
            return json.load(f)
    return {"head": None, "count": 0}


def _save_chain(chain):
    os.makedirs(os.path.dirname(CHAIN_FILE) or ".", exist_ok=True)
    with open(CHAIN_FILE, "w") as f:
        json.dump(chain, f, indent=2)


def canonical(obj) -> bytes:
    """
    Deterministic serialization (canonicalisation rules):
    1. Remove the 'signature' key if present
    2. Sort all keys alphabetically at every nesting level
    3. Use compact separators: (",", ":") — no whitespace
    4. Encode as UTF-8 bytes

    This is the ONLY canonical form. Any other serialization is non-canonical
    and MUST NOT be used for signing or hash computation.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _save_tsr_token(receipt_id: str, token_bytes: bytes):
    """Persist the full binary .tsr token to disk."""
    os.makedirs(TSR_STORE_DIR, exist_ok=True)
    path = os.path.join(TSR_STORE_DIR, f"{receipt_id}.tsr")
    with open(path, "wb") as f:
        f.write(token_bytes)
    return path


def _try_timestamp(data: bytes, receipt_id: str):
    """
    Attempt RFC 3161 trusted timestamp. Returns structured status dict.
    On success: retains the full binary .tsr token (base64 in receipt + file on disk).
    On failure: records the specific failure reason. Never raises. Never blocks issuance.
    """
    imprint_hex = _sha256_hex(data)

    try:
        import rfc3161ng
    except ImportError:
        return {
            "status": TSA_STATUS_UNAVAILABLE,
            "reason": "rfc3161ng library not installed",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "imprint": imprint_hex,
            "imprint_algorithm": "sha256",
        }

    try:
        import socket
        socket.setdefaulttimeout(10)  # 10 second timeout for TSA

        tsa_url = "http://freetsa.org/tsr"
        ts = rfc3161ng.RemoteTimestamper(tsa_url, hashname="sha256")
        token = ts.timestamp(data=data)

        if token is None:
            return {
                "status": TSA_STATUS_REJECTED,
                "reason": "TSA returned empty response",
                "tsa": "freetsa.org",
                "event_time": datetime.now(timezone.utc).isoformat(),
                "imprint": imprint_hex,
                "imprint_algorithm": "sha256",
            }

        # Success — retain full token
        token_b64 = base64.b64encode(token).decode("ascii")
        token_sha256 = _sha256_hex(token)

        # Save binary .tsr file
        tsr_path = _save_tsr_token(receipt_id, token)

        # Attempt to extract TSA cert chain
        tsa_cert_chain_b64 = _extract_tsa_cert_chain(token)

        return {
            "status": TSA_STATUS_ANCHORED,
            "tsa": "freetsa.org",
            "tsa_policy": "1.2.3.4.1",  # FreeTSA default policy OID
            "token_b64": token_b64,
            "token_sha256": token_sha256,
            "token_file": os.path.basename(tsr_path),
            "imprint": imprint_hex,
            "imprint_algorithm": "sha256",
            "tsa_cert_chain_b64": tsa_cert_chain_b64,
            "event_time": datetime.now(timezone.utc).isoformat(),
        }

    except socket.timeout:
        return {
            "status": TSA_STATUS_TIMEOUT,
            "reason": "TSA request timed out (10s)",
            "tsa": "freetsa.org",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "imprint": imprint_hex,
            "imprint_algorithm": "sha256",
        }
    except Exception as e:
        return {
            "status": TSA_STATUS_UNAVAILABLE,
            "reason": str(e)[:200],
            "tsa": "freetsa.org",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "imprint": imprint_hex,
            "imprint_algorithm": "sha256",
        }


def _extract_tsa_cert_chain(token_bytes: bytes):
    """
    Best-effort extraction of TSA certificate chain from the timestamp token.
    Returns base64-encoded DER certs, or None if extraction fails.
    """
    try:
        from cryptography.hazmat.primitives.serialization import pkcs7
        from cryptography import x509

        # Try to parse as PKCS#7 / CMS
        certs = pkcs7.load_der_pkcs7_certificates(token_bytes)
        if certs:
            chain = []
            for cert in certs:
                cert_der = cert.public_bytes(serialization.Encoding.DER)
                chain.append(base64.b64encode(cert_der).decode("ascii"))
            return chain
    except Exception:
        pass
    return None


def issue_receipt(agent_id, action, input_data="", output_data="",
                  controls=None, timestamp_authority=True, run_id=None,
                  require_spec_match=True,
                  input_hash=None, output_hash=None):
    """Issue a receipt.

    VERBATIM HASH COMMITMENTS (input_hash / output_hash)
    ---------------------------------------------------
    When supplied, these are signed EXACTLY as given and the server does not
    re-hash anything. That matters because a counterparty's binding — for
    example SHA-256(canonical(authorisation_envelope)) — must be what appears in
    the signed body. A server re-hash would silently substitute our commitment
    for theirs, and the receipt would then attest to something the counterparty
    never computed.

    This behaviour exists in tbn_receipt_v2 and /api/v2/attest depends on it.
    It was absent from this module, so pointing /attest here without it would
    have broken that contract without any error surfacing. Added 7 Aug 2026.
    """
    """
    Create a v2.1 receipt with full RFC 3161 token retention.

    Args:
        agent_id: Identifier of the AI agent
        action: The action performed
        input_data: Raw input (hashed, not stored)
        output_data: Raw output (hashed, not stored)
        controls: List of {name, result, version} governance control results
        timestamp_authority: True=request timestamp, False=skip (status: not_requested)

    Returns:
        Complete receipt dict, signed and chained.
    """
    # Fail closed if the frozen spec no longer matches what we sign. Issuing a
    # receipt that names a construction whose rules have quietly changed is worse
    # than issuing none: the receipt would carry a digest nobody can resolve.
    if require_spec_match:
        # Called through the module, not through an imported name, so the check
        # always reads the CURRENT value in tbn_construction rather than a binding
        # captured at import time.
        chk = _tc.verify_spec_digest()
        if not chk["ok"]:
            raise RuntimeError(
                f"refusing to issue: {chk['reason']} — {chk.get('note', '')}")

    priv, pub_pem = _load_keys()
    kid = key_id(pub_pem)
    chain = _load_chain()

    # Normalize controls
    norm_controls = []
    for c in (controls or []):
        ver = c.get("version", "")
        norm_controls.append({
            "name": c.get("name"),
            "result": c.get("result"),
            "version": ver,
            "version_hash": _sha256_hex(str(ver).encode())[:16] if ver else None,
        })

    # Generate receipt_id early (needed for .tsr filename)
    receipt_id = "tbn2_" + uuid.uuid4().hex

    body = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "key_id": kid,
        "agent_id": agent_id,
        "action": action,
        # Client commitment honoured verbatim when given; only hashed here when
        # it is not. See the docstring — substituting our hash for theirs would
        # make the receipt attest to something they never computed.
        "input_hash": input_hash if input_hash else _sha256_hex(
            input_data.encode() if isinstance(input_data, str) else input_data),
        "output_hash": output_hash if output_hash else _sha256_hex(
            output_data.encode() if isinstance(output_data, str) else output_data),
        "controls": norm_controls,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": chain["head"],
        "chain_index": chain["count"],
    }
    # Construction identity + run_id from the single source of truth, so no
    # issuer can drift from another (Register items 8 and 7).
    body.update(construction_fields(run_id))

    # RFC 3161 timestamp (RB-01: full token retention)
    if timestamp_authority:
        body["rfc3161"] = _try_timestamp(canonical(body), receipt_id)
    else:
        body["rfc3161"] = {
            "status": TSA_STATUS_NOT_REQUESTED,
            "event_time": datetime.now(timezone.utc).isoformat(),
        }

    # Receipt hash (computed BEFORE receipt_hash, algorithm, signature are added)
    receipt_hash = _sha256_hex(canonical(body))
    body["receipt_hash"] = receipt_hash
    body["algorithm"] = "RSA-PSS-SHA256"

    # Sign over canonical body (everything except signature)
    signature = priv.sign(
        canonical({k: body[k] for k in body if k != "signature"}),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    body["signature"] = signature.hex()

    # Advance the chain
    chain["head"] = receipt_hash
    chain["count"] += 1
    _save_chain(chain)
    return body


def verify_receipt(receipt: dict, pub_key_pem: bytes = None) -> dict:
    """
    Standalone verification — hardened, fail-closed (RB-05).

    Checks:
    1. Required fields present
    2. Schema version recognised
    3. Key ID matches supplied public key
    4. RSA-PSS-SHA256 signature valid
    5. receipt_hash is consistent with body
    6. rfc3161.status is a valid enumeration value

    Returns dict with 'valid' (bool) and diagnostic details.
    Fails closed: any missing, malformed, or unexpected input = invalid.
    """
    # Required fields are PER SCHEMA and come from tbn_construction — see
    # _tc.required_fields_for(). They are NOT a flat set here.
    #
    # BUG FIXED 12 Aug 2026, live regression: this function held ONE required set
    # that included `rfc3161`, and applied it to every schema. `rfc3161` does not
    # exist before 2.2, so the moment /api/v2/verify was pointed at this module
    # ALL 4,165 historical receipts (3,932 at 2.0, 233 at 2.1) began returning
    # "Missing fields: ['rfc3161']". Rejecting valid historical evidence is the
    # same defect as failing to verify your own issuer's output, reversed — and a
    # verifier that reports good receipts as invalid is worse than none, because
    # the failure looks like proof of tampering.

    # CONSTRUCTION_FIELDS and SUPPORTED_SCHEMAS come from tbn_construction — the
    # single source of truth. They are NOT redefined here.
    #
    # BUG FIXED 7 Aug 2026: this function previously hardcoded a schema list of
    # only 2.0 and 2.1 while the module itself issued 2.2, so verify_receipt()
    # REJECTED receipts issue_receipt() had just produced, with "Unsupported
    # schema". A verifier that cannot verify its own issuer's output is worse than
    # no verifier: it reports valid evidence as invalid. That the list was a local
    # copy is exactly why it drifted.

    # Fail-closed: input must be a dict
    if not isinstance(receipt, dict):
        return {"valid": False, "error": "Receipt is not a dict", "check": "type"}

    # SCHEMA IS CHECKED BEFORE FIELDS, deliberately: which fields are required
    # depends on which schema this is, so the old order could not have been
    # correct for more than one schema at a time.
    if "schema_version" not in receipt:
        return {"valid": False, "error": "Missing fields: ['schema_version']",
                "check": "fields"}
    if receipt["schema_version"] not in SUPPORTED_SCHEMAS:
        return {"valid": False, "error": f"Unsupported schema: {receipt['schema_version']}", "check": "schema"}

    # Fail-closed: all fields required FOR THIS SCHEMA present
    missing = _tc.required_fields_for(receipt["schema_version"]) - set(receipt.keys())
    if missing:
        return {"valid": False, "error": f"Missing fields: {sorted(missing)}",
                "check": "fields", "schema_version": receipt["schema_version"]}

    # ── Construction check — FIRST substantive check, per spec section 9 ──
    # If the rules in force are not the rules being applied, nothing further is
    # worth checking. Ordered ahead of the signature deliberately: a valid
    # signature over rules you cannot resolve is not a useful result.
    if receipt["schema_version"] == CURRENT_SCHEMA:
        c_missing = set(CONSTRUCTION_FIELDS) - set(receipt.keys())
        if c_missing:
            return {"valid": False, "check": "construction",
                    "error": f"schema 2.3 requires {sorted(c_missing)}; a construction "
                             f"identifier cannot be optional"}
        # Read via _tc so the check always uses the CURRENT value, never a
        # binding captured when this module was imported.
        if receipt["construction"] != _tc.CONSTRUCTION:
            return {"valid": False, "check": "construction",
                    "error": f"unknown construction {receipt['construction']!r}",
                    "note": "This verifier only knows how to apply "
                            f"{_tc.CONSTRUCTION!r}. Refusing rather than guessing."}
        if receipt["construction_spec"] != _tc.CONSTRUCTION_SPEC:
            return {"valid": False, "check": "construction_spec",
                    "error": "construction_spec does not match the frozen spec "
                             "this verifier holds",
                    "expected": _tc.CONSTRUCTION_SPEC,
                    "found": receipt["construction_spec"],
                    "note": "Either the receipt follows different rules, or the "
                            "spec on this machine has been edited. Both are "
                            "reasons to stop."}

    # Fail-closed: algorithm must be supported
    if receipt["algorithm"] != "RSA-PSS-SHA256":
        return {"valid": False, "error": f"Unsupported algorithm: {receipt['algorithm']}", "check": "algorithm"}

    # Fail-closed: chain_index must be a non-negative integer
    if not isinstance(receipt["chain_index"], int) or receipt["chain_index"] < 0:
        return {"valid": False, "error": "chain_index must be non-negative integer", "check": "chain_index"}

    # Fail-closed: signature must be valid hex
    try:
        sig = bytes.fromhex(receipt["signature"])
    except (ValueError, TypeError):
        return {"valid": False, "error": "Signature is not valid hex", "check": "signature_format"}

    # Fail-closed: rfc3161.status must be valid enum (if rfc3161 present)
    rfc3161 = receipt.get("rfc3161")
    if isinstance(rfc3161, dict):
        status = rfc3161.get("status")
        if status not in VALID_TSA_STATUSES:
            return {"valid": False, "error": f"Invalid rfc3161.status: {status}", "check": "rfc3161_status"}

    # Load public key
    if pub_key_pem is None:
        try:
            with open(PUBLIC_KEY_PATH, "rb") as f:
                pub_key_pem = f.read()
        except FileNotFoundError:
            return {"valid": False, "error": "Public key file not found", "check": "key_file"}

    # Fail-closed: key_id must match
    expected_kid = key_id(pub_key_pem)
    if receipt["key_id"] != expected_kid:
        return {"valid": False, "error": f"key_id mismatch: got {receipt['key_id']}, expected {expected_kid}", "check": "key_id"}

    # Verify signature
    try:
        pub = serialization.load_pem_public_key(pub_key_pem)
        body = {k: receipt[k] for k in receipt if k != "signature"}
        pub.verify(
            sig,
            canonical(body),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
    except Exception as e:
        return {"valid": False, "error": f"Signature verification failed: {e}", "check": "signature"}

    # Verify receipt_hash consistency
    hash_body = {k: receipt[k] for k in receipt if k not in ("receipt_hash", "algorithm", "signature")}
    expected_hash = _sha256_hex(canonical(hash_body))
    if receipt["receipt_hash"] != expected_hash:
        return {"valid": False, "error": "receipt_hash does not match body", "check": "receipt_hash"}

    return {
        "valid": True,
        "key_id": receipt["key_id"],
        "schema_version": receipt["schema_version"],
        "chain_index": receipt["chain_index"],
        "rfc3161_status": rfc3161.get("status") if isinstance(rfc3161, dict) else None,
        "checks_passed": ["type", "fields", "schema", "algorithm", "chain_index",
                          "signature_format", "rfc3161_status", "key_id", "signature", "receipt_hash"],
    }


def verify_chain(receipts: list, pub_key_pem: bytes = None) -> dict:
    """
    Verify a contiguous sequence of receipts: signatures + chain linkage.
    Fail-closed: any break = failure with specific diagnostic.
    """
    if not isinstance(receipts, list) or len(receipts) == 0:
        return {"valid": False, "error": "Empty or non-list input", "check": "input"}

    results = []
    all_valid = True

    for i, receipt in enumerate(receipts):
        # Verify each receipt individually
        v = verify_receipt(receipt, pub_key_pem)
        results.append({"index": i, "chain_index": receipt.get("chain_index"), **v})
        if not v["valid"]:
            all_valid = False

    # Verify chain linkage
    chain_links = []
    for i in range(1, len(receipts)):
        # receipt_hash is computed from body WITHOUT receipt_hash, algorithm, signature
        prev_body = {k: v for k, v in receipts[i - 1].items()
                     if k not in ("receipt_hash", "algorithm", "signature")}
        expected_prev = _sha256_hex(canonical(prev_body))
        actual_prev = receipts[i].get("prev_hash")
        linked = expected_prev == actual_prev
        chain_links.append({
            "from_index": receipts[i - 1].get("chain_index"),
            "to_index": receipts[i].get("chain_index"),
            "valid": linked,
        })
        if not linked:
            all_valid = False

    # Verify sequential chain_index
    for i in range(1, len(receipts)):
        if receipts[i].get("chain_index") != receipts[i - 1].get("chain_index", -1) + 1:
            all_valid = False
            chain_links.append({
                "error": f"Non-sequential chain_index at position {i}",
                "expected": receipts[i - 1].get("chain_index", -1) + 1,
                "got": receipts[i].get("chain_index"),
            })

    return {
        "valid": all_valid,
        "receipt_count": len(receipts),
        "receipt_results": results,
        "chain_links": chain_links,
    }


if __name__ == "__main__":
    # Demo: issue a receipt with full .tsr retention
    r = issue_receipt(
        "demo-agent", "evaluate_sensor_fusion",
        input_data="smoke: triggered, heat: nominal, camera: 0.45",
        output_data="verdict: hold, confidence: 0.45",
        controls=[
            {"name": "risk_score", "result": "medium", "version": "2.1.0"},
            {"name": "adaptive_friction", "result": "human_review", "version": "1.4.2"},
        ],
        timestamp_authority=True,
    )
    print(json.dumps(r, indent=2))
    print("\nVERIFY:", json.dumps(verify_receipt(r), indent=2))

    # Tamper test (fail-closed)
    r2 = dict(r)
    r2["output_hash"] = "0" * 64
    print("\nTAMPER:", json.dumps(verify_receipt(r2), indent=2))

    # Missing field test (fail-closed)
    r3 = {k: v for k, v in r.items() if k != "algorithm"}
    print("\nMISSING FIELD:", json.dumps(verify_receipt(r3), indent=2))

    # Bad type test (fail-closed)
    print("\nBAD TYPE:", json.dumps(verify_receipt("not a dict"), indent=2))
