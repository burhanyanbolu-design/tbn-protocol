"""
TBN Memory — 3-Tier Trust Split (the anti-social-engineering safeguard)
=======================================================================

The integrity guarantee "you cannot lie to the agent" only holds if the memory
that *decisions trust* is NOT the same surface that *adaptivity writes to*.
Otherwise an attacker teaches/poisons the agent through the personalization or
feedback channel — re-opening the exact trick we engineered out.

This module enforces that separation as ARCHITECTURE, not convention, by giving
each tier its own physically separate store and its own write path:

  Tier 1 — FACTS OF RECORD   (immutable, signed, append-only)
      Refunds issued, orders placed, entitlements granted by a verified system
      event. Written ONLY via record_fact(..., privileged=True) — never from
      user assertion or model inference. Entitlement decisions read ONLY here.
      Backed by the signed+chained engine (tbn_memory) in facts.sqlite.

  Tier 2 — PREFERENCES        (mutable, low-trust)
      Tone, language, UI prefs. Adapts freely (overwrite allowed). Structurally
      incapable of granting an entitlement: the entitlement check never reads it.
      Backed by a plain JSON KV (prefs.json) — deliberately NOT in the signed store.

  Tier 3 — LEARNED POLICY     (curated, GATED)
      Outcome-based tuning. Learning may only PROPOSE; a proposal is inert until
      a human/governance step approves it, at which point it becomes a signed
      shard in policy.sqlite. No silent self-modification.

Invariant: adaptivity lives in Tier 2/3; integrity decisions read only Tier 1.

PROPRIETARY AND CONFIDENTIAL — (c) 2026 Hardin Enterprises Ltd. All rights reserved.
Hardin Memory engine. NOT open source. Do not distribute or publish.
"""

import os
import json
import uuid
import hashlib
import datetime

try:
    from . import tbn_memory as mem
except Exception:
    from api import tbn_memory as mem

# Same signer the engine uses — lets a decision be independently verifiable.
try:
    from .tbn_signing import sign_response, verify_signature
except Exception:
    try:
        from api.tbn_signing import sign_response, verify_signature
    except Exception:
        sign_response = None
        verify_signature = None

TIERS_ROOT = "data/memory_tiers"

# Tier identifiers
TIER1_FACTS = "facts"
TIER2_PREFS = "prefs"
TIER3_POLICY = "policy"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _tenant_dir(tenant_id: str) -> str:
    safe = "".join(c for c in (tenant_id or "default") if c.isalnum() or c in "_-")
    d = os.path.join(TIERS_ROOT, safe or "default")
    os.makedirs(d, exist_ok=True)
    return d


def _facts_db(tenant_id: str) -> str:
    return os.path.join(_tenant_dir(tenant_id), "facts.sqlite")


def _policy_db(tenant_id: str) -> str:
    return os.path.join(_tenant_dir(tenant_id), "policy.sqlite")


def _prefs_path(tenant_id: str) -> str:
    return os.path.join(_tenant_dir(tenant_id), "prefs.json")


def _pending_path(tenant_id: str) -> str:
    return os.path.join(_tenant_dir(tenant_id), "policy_pending.json")


def _refusals_db(tenant_id: str) -> str:
    return os.path.join(_tenant_dir(tenant_id), "refusals.sqlite")


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256(obj) -> str:
    return "sha256:" + hashlib.sha256(_canon(obj).encode()).hexdigest()


def _load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


# ══ TIER 1 — FACTS OF RECORD (immutable, signed, append-only) ════════════
def record_fact(tenant_id: str, fact_type: str, subject: str, data: dict,
                source: str, privileged: bool = False) -> dict:
    """Append a signed fact of record. THIS IS THE ONLY WRITE PATH TO TIER 1.

    `privileged` MUST be True and `source` must name a verified system event
    (e.g. 'stripe:checkout.session.completed', 'orders:fulfilled'). A fact can
    never originate from user-asserted text or model inference — that is what
    makes the store impossible to socially-engineer.
    """
    if not privileged:
        return {"ok": False, "rejected": True,
                "error": "Tier-1 facts require privileged=True from a verified system event. "
                         "User assertions and inference cannot write facts of record."}
    if not fact_type or not subject:
        return {"ok": False, "error": "fact_type and subject are required"}

    body = {
        "fact_type": fact_type,        # e.g. "refund_issued", "entitlement", "order"
        "subject": subject,            # e.g. user/customer id
        "data": data or {},            # structured payload (amount, order_id, entitlement key…)
        "recorded": _now(),
    }
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    out = mem.remember(text, kind="fact:" + fact_type, source=source,
                       db_path=_facts_db(tenant_id), allow_conflict=True)
    if not out.get("shard_id"):
        return {"ok": False, "error": "fact write failed", "detail": out}
    return {"ok": True, "tier": TIER1_FACTS, "shard_id": out["shard_id"],
            "signed": out["signed"], "chain_index": out["chain_index"],
            "fact_type": fact_type, "subject": subject}


def get_facts(tenant_id: str, fact_type: str = None, subject: str = None) -> list:
    """Read facts BY REFERENCE from the signed store (never semantic guessing).
    Only signature-valid shards are returned; tampered/unsigned facts are dropped.
    Returned oldest -> newest (by recorded time) so callers can take the latest state."""
    verified = mem.all_verified(db_path=_facts_db(tenant_id))
    out = []
    for v in verified:
        try:
            body = json.loads(v["text"])
        except Exception:
            continue
        if fact_type and body.get("fact_type") != fact_type:
            continue
        if subject and body.get("subject") != subject:
            continue
        out.append({"shard_id": v["shard_id"], "source": v["source"], **body})
    out.sort(key=lambda f: f.get("recorded") or "")
    return out


def check_entitlement(tenant_id: str, subject: str, entitlement: str) -> dict:
    """Decision-grade check. Reads ONLY Tier-1 signed facts and honours the LATEST
    state (a later signed fact can revoke an earlier grant). Fails CLOSED: if no
    valid signed fact currently grants it, the answer is False — regardless of any
    preference or learned policy."""
    facts = get_facts(tenant_id, fact_type="entitlement", subject=subject)
    matching = [f for f in facts if f.get("data", {}).get("entitlement") == entitlement]
    if not matching:
        return {"granted": False, "source": "tier1_signed_fact",
                "entitlement": entitlement, "evidence_shard_id": None, "as_of": None}
    latest = matching[-1]                       # newest wins
    granted = latest.get("data", {}).get("granted") is True
    ever_granted = any(m.get("data", {}).get("granted") is True for m in matching)
    return {"granted": granted, "source": "tier1_signed_fact", "entitlement": entitlement,
            "evidence_shard_id": latest["shard_id"], "as_of": latest.get("recorded"),
            "revoked": (not granted) and ever_granted}


def revoke_entitlement(tenant_id: str, subject: str, entitlement: str, source: str,
                       reason: str = "", privileged: bool = False) -> dict:
    """Officially cancel an entitlement by appending a SIGNED superseding fact
    (granted=false) that links to the grant it replaces. Tier 1 stays append-only
    and sealed; check_entitlement now returns False because the latest state says so."""
    if not privileged:
        return {"ok": False, "rejected": True,
                "error": "Revocation is a Tier-1 write — requires privileged=True from a verified system event."}
    cur = check_entitlement(tenant_id, subject, entitlement)
    return record_fact(tenant_id, "entitlement", subject,
                       {"entitlement": entitlement, "granted": False, "reason": reason,
                        "supersedes": cur.get("evidence_shard_id")},
                       source, privileged=True)


# ── Signed decision receipts (S1) — a provable answer, not just an answer ────
def decision_receipt(tenant_id: str, subject: str, entitlement: str) -> dict:
    """Make an entitlement decision (Tier-1 only) and return a SIGNED receipt that
    cites the exact fact it relied on. Independently verifiable with the public key."""
    ent = check_entitlement(tenant_id, subject, entitlement)
    body = {
        "type": "TBN-MEMORY-DECISION",
        "subject": subject,
        "entitlement": entitlement,
        "granted": ent["granted"],
        "decision_source": ent["source"],
        "evidence_shard_id": ent.get("evidence_shard_id"),
        "as_of": ent.get("as_of"),
        "decided_at": _now(),
        "algorithm": "RSA-PSS-SHA256",
    }
    sig = sign_response(body) if sign_response else None
    body["signature"] = sig
    body["signed"] = bool(sig)
    return body


def verify_decision(receipt: dict) -> dict:
    """Standalone verify a decision receipt against the public key. No server trust."""
    if not verify_signature:
        return {"valid": False, "error": "verifier unavailable"}
    sig = receipt.get("signature")
    if not sig:
        return {"valid": False, "error": "no signature on receipt"}
    body = {k: v for k, v in receipt.items() if k not in ("signature", "signed")}
    try:
        ok = verify_signature(body, sig)
    except Exception as e:
        return {"valid": False, "error": str(e)}
    return {"valid": bool(ok), "subject": receipt.get("subject"),
            "entitlement": receipt.get("entitlement"), "granted": receipt.get("granted"),
            "evidence_shard_id": receipt.get("evidence_shard_id")}


def audit_facts(tenant_id: str) -> dict:
    """Whole-store integrity proof over the Tier-1 facts (signatures + chain + Merkle root)."""
    return mem.audit(db_path=_facts_db(tenant_id))


# ══ TIER 2 — PREFERENCES (mutable, low-trust) ════════════════════════════
# Keys that would smuggle an entitlement through the soft channel are refused
# at the door, so a pref can never even *look* like a fact of record.
_FORBIDDEN_PREF_TOKENS = ("entitle", "refund", "grant", "credit", "balance",
                          "order", "paid", "license", "licence", "access_granted")


def set_preference(tenant_id: str, key: str, value, source: str = "user") -> dict:
    """Write/overwrite a soft preference. Cannot grant entitlements (refused if it
    tries) and is never consulted by check_entitlement."""
    k = (key or "").strip().lower()
    if not k:
        return {"ok": False, "error": "preference key required"}
    if any(tok in k for tok in _FORBIDDEN_PREF_TOKENS):
        return {"ok": False, "rejected": True,
                "error": f"'{key}' resembles an entitlement; Tier-2 cannot grant rights. "
                         "Use record_fact (Tier-1, privileged) for facts of record."}
    prefs = _load_json(_prefs_path(tenant_id), {})
    prefs[k] = {"value": value, "source": source, "updated": _now()}
    _save_json(_prefs_path(tenant_id), prefs)
    return {"ok": True, "tier": TIER2_PREFS, "key": k, "value": value}


def get_preferences(tenant_id: str) -> dict:
    return _load_json(_prefs_path(tenant_id), {})


# ══ TIER 3 — LEARNED POLICY (curated, gated) ═════════════════════════════
def propose_policy(tenant_id: str, name: str, rule: dict, rationale: str = "",
                   proposed_by: str = "learning") -> dict:
    """Learning/feedback may ONLY propose. The proposal is inert until approved."""
    if not name or not isinstance(rule, dict):
        return {"ok": False, "error": "name and rule(dict) required"}
    pending = _load_json(_pending_path(tenant_id), [])
    pid = "pol_" + uuid.uuid4().hex[:12]
    pending.append({"proposal_id": pid, "name": name, "rule": rule,
                    "rationale": rationale, "proposed_by": proposed_by,
                    "status": "pending", "proposed_at": _now()})
    _save_json(_pending_path(tenant_id), pending)
    return {"ok": True, "tier": TIER3_POLICY, "proposal_id": pid, "status": "pending",
            "note": "Inert until approve_policy() by a human/governance step."}


def list_pending_policies(tenant_id: str) -> list:
    return [p for p in _load_json(_pending_path(tenant_id), []) if p.get("status") == "pending"]


def approve_policy(tenant_id: str, proposal_id: str, approver: str,
                   rendered_context: dict = None) -> dict:
    """Gate: promote a pending proposal into the SIGNED active policy store.
    This is the only way a learned policy becomes active — no silent self-edit.

    `rendered_context` (optional but strongly recommended) is the exact state
    the approver had in front of them at the moment of approval — e.g. the
    session/turn history, other participants' prior actions, the proposal
    text itself. It is hashed into `approval_context_hash` and stored on the
    approval, so a later dispute can ask not only "who approved this" but
    "what did they actually see" — an approver cannot be bound to context
    they never had a chance to review, and the record proves what was shown.
    Omitting it still approves (backward compatible) but the receipt then
    states informed_context_captured=False.
    """
    if not approver:
        return {"ok": False, "error": "approver required (human/governance identity)"}
    pending = _load_json(_pending_path(tenant_id), [])
    target = next((p for p in pending if p.get("proposal_id") == proposal_id
                   and p.get("status") == "pending"), None)
    if not target:
        return {"ok": False, "error": "no pending proposal with that id"}
    approval_context_hash = _sha256(rendered_context) if rendered_context is not None else None
    body = {"name": target["name"], "rule": target["rule"],
            "rationale": target.get("rationale", ""),
            "proposed_by": target.get("proposed_by"), "approved_by": approver,
            "approved_at": _now(), "proposal_id": proposal_id,
            "approval_context_hash": approval_context_hash,
            "informed_context_captured": approval_context_hash is not None}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    out = mem.remember(text, kind="policy", source="approved:" + approver,
                       db_path=_policy_db(tenant_id))
    target["status"] = "approved"
    target["approved_by"] = approver
    target["approved_at"] = body["approved_at"]
    target["approval_context_hash"] = approval_context_hash
    _save_json(_pending_path(tenant_id), pending)
    return {"ok": True, "tier": TIER3_POLICY, "active": True,
            "shard_id": out["shard_id"], "signed": out["signed"], "proposal_id": proposal_id,
            "approval_context_hash": approval_context_hash,
            "informed_context_captured": approval_context_hash is not None}


def reject_policy(tenant_id: str, proposal_id: str, approver: str, reason: str = "",
                  rendered_context: dict = None) -> dict:
    pending = _load_json(_pending_path(tenant_id), [])
    target = next((p for p in pending if p.get("proposal_id") == proposal_id
                   and p.get("status") == "pending"), None)
    if not target:
        return {"ok": False, "error": "no pending proposal with that id"}
    approval_context_hash = _sha256(rendered_context) if rendered_context is not None else None
    target["status"] = "rejected"
    target["rejected_by"] = approver
    target["reason"] = reason
    target["rejected_at"] = _now()
    target["approval_context_hash"] = approval_context_hash
    _save_json(_pending_path(tenant_id), pending)
    return {"ok": True, "status": "rejected", "proposal_id": proposal_id,
            "approval_context_hash": approval_context_hash,
            "informed_context_captured": approval_context_hash is not None}


# ══ REFUSAL LOG (the pressure-valve problem) ═════════════════════════════
# A hard refusal mid-flow that just dead-ends gets routed around off-session,
# and if refusals aren't durably logged, the audit trail is clean exactly
# where it doesn't matter (safe actions) and silent exactly where it does
# (the consequential ones). Every refusal gets a durable, signed record with
# an open follow_up slot that gets filled in by whatever happens next —
# manual override, escalation, retry, or nothing.
def log_refusal(tenant_id: str, subject: str, action: str, reason: str,
                rendered_context: dict = None, source: str = "governance") -> dict:
    """Record a refusal as a SIGNED fact (append-only, same integrity guarantee
    as Tier-1). Returns {refusal_id, ...} — pass refusal_id to record_followup()
    once you know what happened next."""
    if not action or not reason:
        return {"ok": False, "error": "action and reason are required"}
    refusal_id = "ref_" + uuid.uuid4().hex[:12]
    context_hash = _sha256(rendered_context) if rendered_context is not None else None
    body = {
        "refusal_id": refusal_id,
        "subject": subject,
        "action": action,
        "reason": reason,
        "refusal_context_hash": context_hash,
        "refused_at": _now(),
        "followup": None,          # filled in later via record_followup()
        "followup_recorded_at": None,
    }
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    out = mem.remember(text, kind="refusal", source=source,
                       db_path=_refusals_db(tenant_id), allow_conflict=True)
    if not out.get("shard_id"):
        return {"ok": False, "error": "refusal log write failed", "detail": out}
    return {"ok": True, "refusal_id": refusal_id, "shard_id": out["shard_id"],
            "signed": out["signed"], "refusal_context_hash": context_hash}


def record_followup(tenant_id: str, refusal_id: str, followup: str,
                    followup_source: str = "system") -> dict:
    """Append what actually happened after a refusal (manual override, escalated,
    retried and blocked again, dropped, resolved another way). Written as a NEW
    signed shard that references the refusal_id — the log stays append-only, so
    a followup can be added but a refusal can never be quietly erased."""
    if not followup:
        return {"ok": False, "error": "followup is required"}
    body = {
        "refusal_id": refusal_id,
        "followup": followup,
        "followup_source": followup_source,
        "followup_recorded_at": _now(),
    }
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    out = mem.remember(text, kind="refusal_followup", source=followup_source,
                       db_path=_refusals_db(tenant_id), allow_conflict=True)
    if not out.get("shard_id"):
        return {"ok": False, "error": "followup write failed", "detail": out}
    return {"ok": True, "refusal_id": refusal_id, "shard_id": out["shard_id"],
            "signed": out["signed"]}


def get_refusals(tenant_id: str, subject: str = None) -> list:
    """Read all signed refusals, each joined with its followup (if any) by
    refusal_id — so 'refused with no followup logged yet' is visible, not hidden."""
    verified = mem.all_verified(db_path=_refusals_db(tenant_id))
    refusals, followups = {}, {}
    for v in verified:
        try:
            body = json.loads(v["text"])
        except Exception:
            continue
        rid = body.get("refusal_id")
        if not rid:
            continue
        if "action" in body and "reason" in body:
            refusals[rid] = {**body, "shard_id": v["shard_id"]}
        elif "followup" in body:
            followups.setdefault(rid, []).append(body)
    out = []
    for rid, r in refusals.items():
        if subject and r.get("subject") != subject:
            continue
        fu = sorted(followups.get(rid, []), key=lambda f: f.get("followup_recorded_at") or "")
        r["followup"] = fu[-1]["followup"] if fu else None
        r["followup_recorded_at"] = fu[-1]["followup_recorded_at"] if fu else None
        r["followup_pending"] = fu == []
        out.append(r)
    out.sort(key=lambda r: r.get("refused_at") or "")
    return out


def get_active_policies(tenant_id: str) -> list:
    """Active policies = signature-valid shards in the policy store (by reference)."""
    out = []
    for v in mem.all_verified(kind="policy", db_path=_policy_db(tenant_id)):
        try:
            out.append(json.loads(v["text"]))
        except Exception:
            continue
    return out


# ══ DECISION SURFACE — demonstrates the rule end-to-end ══════════════════
def decide(tenant_id: str, subject: str, entitlement: str) -> dict:
    """Make an entitlement decision the safe way:
      * the YES/NO comes ONLY from Tier-1 signed facts (cannot be lied to),
      * a SIGNED decision receipt cites the exact fact it relied on (provable),
      * Tier-2 prefs personalise the *response* (never the decision),
      * Tier-3 active policy may shape *handling* (never grant the right).
    """
    receipt = decision_receipt(tenant_id, subject, entitlement)
    prefs = get_preferences(tenant_id)
    tone = prefs.get("tone", {}).get("value", "neutral")
    lang = prefs.get("language", {}).get("value", "en")
    policies = get_active_policies(tenant_id)
    return {
        "subject": subject,
        "entitlement": entitlement,
        "granted": receipt["granted"],            # Tier-1 only
        "decision_source": receipt["decision_source"],
        "evidence_shard_id": receipt.get("evidence_shard_id"),
        "personalisation": {"tone": tone, "language": lang},   # Tier-2 only
        "active_policies": [p.get("name") for p in policies],  # Tier-3 (handling)
        "receipt": receipt,                       # signed, independently verifiable
    }
