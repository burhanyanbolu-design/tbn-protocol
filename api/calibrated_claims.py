"""
TBN G6 — Calibrated Claims
==========================
Extends G5's "prove what you DID" to "prove how well-grounded what you SAID
is." `api/answer_verification.py` already breaks an answer into claims and
scores how well each is supported by the sources used — but today that score
is consumed once (used to decide whether to rewrite/abstain) and then
discarded. Nothing about the grounding check survives past that one request.

G6 makes the grounding check itself a signed, persistent, auditable record —
the same signed-claim structure G5 uses for action receipts, but for FACTUAL
claims instead of ACTION claims. Anyone auditing a reply later sees not just
"the agent said X" but "the agent said X, with this much grounding, against
these sources, verified at this time" — a flat statement becomes an
audit-ready claim.

This module does not change what gets shown to the user (that's still
answer_verification.py's job — rewriting/abstaining). It only persists the
scoring that already happened, as a signed record.

This is the G6 layer described in .kiro/steering/tbn-g5-g7-framework.md.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0
"""
import os
import json
import hashlib
import secrets
import datetime

RECORDS_DIR = "data/calibrated_claims"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256(obj):
    return "sha256:" + hashlib.sha256(_canon(obj).encode()).hexdigest()


def _session_path(session_id: str) -> str:
    safe = "".join(c for c in (session_id or "unknown") if c.isalnum() or c in "-_")[:80] or "unknown"
    os.makedirs(RECORDS_DIR, exist_ok=True)
    return os.path.join(RECORDS_DIR, f"{safe}.json")


def _load_session_records(session_id: str) -> list:
    p = _session_path(session_id)
    try:
        with open(p) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_session_records(session_id: str, records: list):
    p = _session_path(session_id)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(records, f, indent=2)
    os.replace(tmp, p)


def record_calibrated_claims(session_id: str, question: str, verification: dict,
                              sources: list = None, agent_id: str = None) -> dict:
    """Persist an answer_verification.verify_answer() result as a signed,
    auditable record. Call this right after verify_answer() returns (whether
    or not the caller ends up rewriting/abstaining the reply) — it captures
    the grounding decision itself, not the user-facing text.

    Args:
      session_id:   groups records the same way G5 groups execution receipts
      question:     what was asked (truncated for storage)
      verification: the dict returned by answer_verification.verify_answer()
      sources:      the sources list that was available (may differ slightly
                     from what verification['claims'] cites, kept for context)
      agent_id:      optional, which agent produced this

    Returns the signed record. Never raises — a failure to persist a
    calibrated-claims record must not block the reply from reaching the user.
    """
    try:
        # CHANGED 12 Aug 2026 — this used to `return` here and write NOTHING
        # when the verifier hadn't run, which meant an unchecked reply left no
        # trace at all. That is the defect: not that unchecked replies exist,
        # but that silence converted them into apparently-checked ones with
        # nothing recording the conversion. A "not_checked" record is now
        # persisted and signed, so the ABSENCE of a check is itself evidence.
        if not verification or not verification.get("verified"):
            return _record_not_checked(session_id, question, verification, sources, agent_id)

        claims = verification.get("claims") or []
        if not isinstance(claims, list):
            claims = []

        record_id = "tbn_claim_" + secrets.token_hex(12)
        core = {
            "claim_record_id": record_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "question": (question or "")[:300],
            "claims": [
                {"claim": (c.get("claim") or "")[:300], "status": c.get("status")}
                for c in claims if isinstance(c, dict)
            ],
            "grounding_score": verification.get("grounding_score"),
            "verdict": verification.get("verdict"),
            # Carried from verify_answer so every record states its own state
            # explicitly instead of it having to be inferred from the score.
            "state": verification.get("state") or (
                "failed_grounding" if verification.get("abstain") else "grounded"),
            "supported_count": verification.get("supported_count"),
            "unsupported_count": verification.get("unsupported_count"),
            "total_claims": verification.get("total_claims"),
            "abstained": bool(verification.get("abstain")),
            "sources": [
                {"title": (s.get("title") or "")[:200], "uri": (s.get("uri") or "")[:300]}
                for s in (sources or []) if isinstance(s, dict)
            ][:10],
            "timestamp": _now(),
        }
        record_hash = _sha256(core)
        core["record_hash"] = record_hash
        try:
            from api.tbn_signing import sign_response
            core["signature"] = sign_response({"record_hash": record_hash})
            core["signature_algorithm"] = "RSA-PSS-SHA256"
        except Exception:
            core["signature"] = None

        records = _load_session_records(session_id)
        records.append(core)
        _save_session_records(session_id, records)
        return core
    except Exception as e:
        return {"claim_record_id": None, "error": str(e)[:120]}


def _record_not_checked(session_id: str, question: str, verification: dict,
                         sources: list = None, agent_id: str = None) -> dict:
    """Persist a signed record stating that grounding was NOT checked, and why.

    Deliberately the same shape and store as a real calibrated-claims record,
    so an auditor reading a session sees "no check ran here" as an explicit
    entry rather than having to notice a gap between entries. Absence of
    evidence becomes evidence of absence, which is the only honest version.
    """
    try:
        record_id = "tbn_claim_unchecked_" + secrets.token_hex(10)
        core = {
            "claim_record_id": record_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "question": (question or "")[:300],
            "claims": [],
            "grounding_score": None,
            "verdict": "UNVERIFIED",
            "state": "not_checked",
            "supported_count": None,
            "unsupported_count": None,
            "total_claims": None,
            "abstained": False,
            # WHY it didn't run — no key, transport error, malformed verifier
            # output. Without this the record says nothing useful.
            "not_checked_reason": ((verification or {}).get("note") or "verifier did not run")[:300],
            "sources": [
                {"title": (s.get("title") or "")[:200], "uri": (s.get("uri") or "")[:300]}
                for s in (sources or []) if isinstance(s, dict)
            ][:10],
            "timestamp": _now(),
        }
        record_hash = _sha256(core)
        core["record_hash"] = record_hash
        try:
            from api.tbn_signing import sign_response
            core["signature"] = sign_response({"record_hash": record_hash})
            core["signature_algorithm"] = "RSA-PSS-SHA256"
        except Exception:
            core["signature"] = None

        records = _load_session_records(session_id)
        records.append(core)
        _save_session_records(session_id, records)
        return core
    except Exception as e:
        return {"claim_record_id": None, "state": "not_checked", "error": str(e)[:120]}


def get_session_calibrated_claims(session_id: str) -> list:
    """All G6 calibrated-claim records recorded so far for this session —
    the audit trail of what was claimed, how grounded it was, and against
    which sources, across every verified reply in the session."""
    return _load_session_records(session_id)


def claim_record_summary(record: dict) -> dict:
    """Small, response-safe summary of a calibrated-claim record (for
    attaching to an API response / Governed Action Record without dumping
    the full claim list)."""
    if not record or not record.get("claim_record_id"):
        return None
    return {
        "claim_record_id": record.get("claim_record_id"),
        # Three states: grounded / failed_grounding / not_checked. Included in
        # the response-safe summary so a caller cannot show a grounding block
        # that looks clean when in fact nothing was checked.
        "state": record.get("state") or ("grounded" if record.get("grounding_score") is not None
                                         else "not_checked"),
        "grounding_score": record.get("grounding_score"),
        "verdict": record.get("verdict"),
        "supported_count": record.get("supported_count"),
        "unsupported_count": record.get("unsupported_count"),
        "not_checked_reason": record.get("not_checked_reason"),
        "record_hash": record.get("record_hash"),
        "signed": bool(record.get("signature")),
    }
