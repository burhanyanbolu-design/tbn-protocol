"""
TBN Verifiable Intelligence — Receipt System
=============================================
Every AI observation gets a cryptographic receipt that proves:
  1. WHAT was processed (video hash, source URL)
  2. WHEN it was processed (timestamp)
  3. HOW it was processed (model, mode, parameters)
  4. WHAT was observed (entities, claims with confidence)
  5. WHO governed it (TBN Protocol, decision hash)

This is PROOF OF PROCESSING — not Proof of Truth.
The receipt certifies the observation occurred and was governed.
It does NOT guarantee the AI output is factually correct.

Any third party can verify a receipt at /api/verify/receipt/<id>

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-VR-2f8a4c1e
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timezone


RECEIPTS_FILE = "data/verifiable_receipts.json"


def _load_receipts():
    if os.path.exists(RECEIPTS_FILE):
        with open(RECEIPTS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_receipts(data):
    os.makedirs(os.path.dirname(RECEIPTS_FILE) or ".", exist_ok=True)
    with open(RECEIPTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_verifiable_receipt(
    agent_id,
    mode,
    source,
    video_hash,
    understanding,
    duration=None,
    file_size=None,
    model_used="gemini-2.5-flash",
):
    """
    Generate a full verifiable receipt for a video observation.
    Stored permanently for third-party verification.
    """
    now = datetime.now(timezone.utc)
    receipt_id = f"tbn_vr_{uuid.uuid4().hex[:16]}"

    # ── Confidence scoring ────────────────────────────────────────────
    base_confidence = understanding.get("confidence", 0.5)
    risks = understanding.get("risks", [])
    has_risks = bool(risks) and not (len(risks) == 1 and "no" in str(risks[0]).lower())

    # Risk assessment
    risk_score = 15  # Base
    if has_risks:
        risk_score = min(30 + len(risks) * 15, 95)
    if mode == "monitor":
        risk_score = max(risk_score, 25)

    decision = "ALLOWED" if risk_score < 80 else "FLAGGED"

    # ── Source provenance ─────────────────────────────────────────────
    provenance = {
        "source_url": source if source != "demo" else "local:demo_video",
        "video_hash": video_hash,
        "duration_seconds": duration,
        "file_size_mb": file_size,
        "frames_analysed": 10,
        "audio_transcribed": bool(understanding.get("transcript_summary")),
    }

    # ── Processing parameters ─────────────────────────────────────────
    processing = {
        "model": model_used,
        "mode": mode,
        "agent_id": agent_id,
        "protocol_version": "TBN v1.0",
        "extraction_method": "multimodal_frames_plus_audio",
    }

    # ── Claims with individual confidence ─────────────────────────────
    claims = []
    # Summary claim
    if understanding.get("summary"):
        claims.append({
            "type": "summary",
            "content": understanding["summary"],
            "confidence": base_confidence,
            "source_type": "visual+audio",
        })
    # Transcript claim
    if understanding.get("transcript_summary"):
        claims.append({
            "type": "transcript",
            "content": understanding["transcript_summary"],
            "confidence": min(base_confidence + 0.1, 1.0),
            "source_type": "audio",
        })
    # Entity claims
    entities = understanding.get("entities", {})
    for etype, elist in entities.items():
        if not isinstance(elist, list):
            continue
        for item in elist:
            name = item.get("name", item) if isinstance(item, dict) else item
            desc = item.get("description", "") if isinstance(item, dict) else ""
            claims.append({
                "type": "entity",
                "entity_type": etype,
                "name": name,
                "description": desc,
                "confidence": base_confidence * 0.9,
                "source_type": "visual+audio",
            })

    # ── Authenticity assessment ───────────────────────────────────────
    authenticity = understanding.get("authenticity", {})

    # ── Build the full receipt ────────────────────────────────────────
    receipt = {
        "receipt_id": receipt_id,
        "version": "2.0",
        "proof_type": "PROCESSING",
        "disclaimer": (
            "This receipt certifies that the described processing occurred "
            "under TBN Protocol governance. It is Proof of Processing, not "
            "Proof of Truth. The accuracy of AI-generated observations is "
            "probabilistic and indicated by confidence scores."
        ),
        "timestamp": now.isoformat(),
        "agent_id": agent_id,
        "decision": decision,
        "risk_score": risk_score,
        "governed_by": "TBN Protocol v1.0 — Hardin Enterprises Ltd",
        "provenance": provenance,
        "processing": processing,
        "claims_count": len(claims),
        "claims": claims,
        "authenticity": authenticity,
        "frameworks": [
            "EU AI Act Art. 52 (Transparency)",
            "EU AI Act Art. 13 (Record-keeping)",
            "UK GDPR Art. 22 (Automated decisions)",
        ],
    }

    # ── Decision hash (integrity proof) ───────────────────────────────
    # Hash everything except the hash itself and signature
    hash_payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    receipt["decision_hash"] = f"sha256:{hashlib.sha256(hash_payload.encode()).hexdigest()}"

    # ── Sign with TBN key ─────────────────────────────────────────────
    try:
        from api.tbn_signing import sign_response
        receipt["signature"] = sign_response(receipt)
        receipt["signature_algorithm"] = "RSA-PSS-SHA256"
        receipt["verification_url"] = f"https://tbn.hardinai.co.uk/api/verify/receipt/{receipt_id}"
    except Exception:
        receipt["signature"] = "unsigned-dev-mode"

    # ── Store for verification ────────────────────────────────────────
    receipts = _load_receipts()
    receipts[receipt_id] = receipt
    _save_receipts(receipts)

    return receipt


def verify_receipt(receipt_id):
    """
    Verify a receipt exists and its integrity is intact.
    Returns the receipt + verification status.
    Any third party can call this.
    """
    receipts = _load_receipts()
    receipt = receipts.get(receipt_id)

    if not receipt:
        return {"verified": False, "error": "Receipt not found", "receipt_id": receipt_id}

    # Verify integrity — recompute hash
    stored_hash = receipt.get("decision_hash", "")
    stored_sig = receipt.get("signature", "")
    sig_algo = receipt.get("signature_algorithm", "")
    verification_url = receipt.get("verification_url", "")

    # Remove hash/sig fields, recompute
    check_receipt = {k: v for k, v in receipt.items()
                     if k not in ("decision_hash", "signature", "signature_algorithm", "verification_url")}
    recomputed = f"sha256:{hashlib.sha256(json.dumps(check_receipt, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}"

    hash_valid = (stored_hash == recomputed)

    # Verify signature
    sig_valid = False
    try:
        from api.tbn_signing import verify_signature
        sig_receipt = {k: v for k, v in receipt.items() if k not in ("signature", "signature_algorithm", "verification_url")}
        sig_valid = verify_signature(sig_receipt, stored_sig)
    except Exception:
        sig_valid = False

    return {
        "verified": hash_valid and sig_valid,
        "receipt_id": receipt_id,
        "hash_integrity": "VALID" if hash_valid else "TAMPERED",
        "signature_integrity": "VALID" if sig_valid else "UNVERIFIED",
        "proof_type": receipt.get("proof_type", "PROCESSING"),
        "disclaimer": receipt.get("disclaimer", ""),
        "timestamp": receipt.get("timestamp"),
        "agent_id": receipt.get("agent_id"),
        "decision": receipt.get("decision"),
        "risk_score": receipt.get("risk_score"),
        "claims_count": receipt.get("claims_count", 0),
        "provenance": receipt.get("provenance"),
        "processing": receipt.get("processing"),
        "governed_by": receipt.get("governed_by"),
        "frameworks": receipt.get("frameworks", []),
        "full_receipt": receipt,
    }


def get_all_receipts_summary():
    """Return a summary of all stored receipts."""
    receipts = _load_receipts()
    return {
        "total_receipts": len(receipts),
        "receipts": [
            {
                "receipt_id": r["receipt_id"],
                "timestamp": r.get("timestamp"),
                "agent_id": r.get("agent_id"),
                "decision": r.get("decision"),
                "risk_score": r.get("risk_score"),
                "proof_type": r.get("proof_type"),
                "claims_count": r.get("claims_count", 0),
                "source": r.get("provenance", {}).get("source_url", ""),
            }
            for r in sorted(receipts.values(), key=lambda x: x.get("timestamp", ""), reverse=True)
        ][:50]
    }
