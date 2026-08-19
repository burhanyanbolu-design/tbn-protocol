"""
TBN Trusted Memory — multi-tenant SaaS layer over the governed memory engine
============================================================================

Turns api/tbn_memory.py (a single shared store) into a product OTHER companies
can use:
  * each customer = a TENANT with their OWN private store (data never mixes),
  * each tenant authenticates with an API KEY (we store only its hash),
  * the four governed actions (remember / recall / verify / audit) are exposed
    per-tenant,
  * a per-tenant USAGE meter counts operations so pricing is a later switch.

The trust properties are inherited from the engine: every memory is TBN-signed
and hash-chained, recall rejects unsigned/tampered shards, and audit returns a
Merkle root proving the whole store is intact — that is the sellable feature.

PROPRIETARY AND CONFIDENTIAL — © 2026 Hardin Enterprises Ltd. All rights reserved.
Hardin Memory multi-tenant service. NOT open source. Do not distribute or publish.
"""

import os
import json
import uuid
import re
import time
import secrets
import hashlib
import datetime

try:
    from . import tbn_memory as mem
except Exception:
    from api import tbn_memory as mem

try:
    from . import area_five_shadow
except Exception:
    try:
        from api import area_five_shadow
    except Exception:
        area_five_shadow = None

TENANTS_FILE = "data/memory_tenants.json"
USAGE_FILE = "data/memory_usage.json"
SIGNUPS_FILE = "data/memory_signups.json"
TENANT_DB_DIR = "data/memory_tenants"

# Free-tier-style soft limits (enforced; pricing flips these later).
PLAN_LIMITS = {
    "free": {"writes_per_month": 10000, "reads_per_month": 10000},
    "payg": {"writes_per_month": 100000000, "reads_per_month": 100000000},
    "pro": {"writes_per_month": 1000000, "reads_per_month": 5000000},
}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _month():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def _key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _tenant_db(tenant_id: str) -> str:
    os.makedirs(TENANT_DB_DIR, exist_ok=True)
    # tenant_id is server-generated (no path traversal risk), but keep it tight.
    safe = "".join(c for c in tenant_id if c.isalnum() or c in "_-")
    return os.path.join(TENANT_DB_DIR, safe + ".sqlite")


def _memory_agent_id(value: str = None) -> str:
    agent_id = (value or mem.MEM_AGENT_ID).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", agent_id):
        raise ValueError("agent_id must contain only letters, numbers, '_' or '-'")
    return agent_id


def _principal(tenant: dict) -> dict:
    """Derive engine identity only from the authenticated server-side record."""
    tenant_id = str(tenant.get("tenant_id") or "").strip()
    if not re.fullmatch(r"ten_[A-Za-z0-9_-]{4,64}", tenant_id):
        raise ValueError("invalid tenant identity")
    return {
        "tenant_id": tenant_id,
        "agent_id": _memory_agent_id(tenant.get("agent_id")),
        "store_scope": "tenant:" + tenant_id,
        "private": True,
    }


def _shadow_sync(authority_db: str, principal: dict) -> dict:
    if area_five_shadow is None or not area_five_shadow.enabled():
        return {"status": "disabled"}
    try:
        return area_five_shadow.sync(authority_db, principal)
    except Exception as exc:
        return {"status": "degraded", "reason": type(exc).__name__}


# ── Tenants ──────────────────────────────────────────────────────────────
def create_tenant(name: str, plan: str = "free", agent_id: str = None) -> dict:
    """Create a tenant and bind its API-key identity to a TBN agent."""
    key = "tbnmem_" + secrets.token_hex(24)
    tenant_id = "ten_" + uuid.uuid4().hex[:12]
    bound_agent_id = _memory_agent_id(agent_id)
    tenants = _load(TENANTS_FILE, {})
    tenants[_key_hash(key)] = {
        "tenant_id": tenant_id,
        "agent_id": bound_agent_id,
        "name": name or "unnamed",
        "plan": plan if plan in PLAN_LIMITS else "free",
        "active": True,
        "expires_at": None,
        "created": _now(),
    }
    _save(TENANTS_FILE, tenants)
    return {"tenant_id": tenant_id, "agent_id": bound_agent_id,
            "name": name, "plan": plan, "api_key": key,
            "note": "Store this API key now — it is not shown again."}


def authenticate(key: str):
    """Return an active, unexpired server-side tenant principal, else None."""
    if not key or not key.startswith("tbnmem_"):
        return None
    record = _load(TENANTS_FILE, {}).get(_key_hash(key))
    if not record or record.get("active", True) is not True:
        return None
    expires_at = record.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.datetime.fromisoformat(
                str(expires_at).replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)
            if expiry <= datetime.datetime.now(datetime.timezone.utc):
                return None
        except Exception:
            return None
    # Legacy tenant records are mapped deterministically to the registered
    # service agent without trusting request-controlled data.
    resolved = dict(record)
    resolved["agent_id"] = _memory_agent_id(record.get("agent_id"))
    resolved.setdefault("active", True)
    resolved.setdefault("expires_at", None)
    return resolved


def list_tenants() -> list:
    """Admin view: tenants WITHOUT keys (keys are never recoverable)."""
    return [{"tenant_id": t["tenant_id"], "agent_id": t.get("agent_id", mem.MEM_AGENT_ID),
             "name": t["name"], "plan": t["plan"],
             "active": t.get("active", True), "expires_at": t.get("expires_at"),
             "created": t["created"]} for t in _load(TENANTS_FILE, {}).values()]


# ── Self-serve signup (email + terms → instant free key) ─────────────────
_SIGNUP_IP = {}   # process-local IP -> [timestamps] for basic rate limiting


def _valid_email(e: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (e or "").strip()))


def find_signup_by_email(email: str):
    return _load(SIGNUPS_FILE, {}).get((email or "").lower().strip())


def _ip_rate_ok(ip: str, limit: int = 5, window: int = 3600) -> bool:
    now = time.time()
    arr = [t for t in _SIGNUP_IP.get(ip or "", []) if now - t < window]
    if len(arr) >= limit:
        _SIGNUP_IP[ip or ""] = arr
        return False
    arr.append(now)
    _SIGNUP_IP[ip or ""] = arr
    return True


def signup(email: str, url: str = "", ip: str = "", plan: str = "free") -> dict:
    """Create a tenant tied to an email + website, EMAIL the key to that address
    (so only a real, owned inbox receives it), and record the signup so the owner
    can contact them. Dedupes by email; rate-limits per IP."""
    email = (email or "").lower().strip()
    url = (url or "").strip()
    if not _valid_email(email):
        return {"ok": False, "error": "Please enter a valid email address."}
    if len(url) < 4 or "." not in url:
        return {"ok": False, "error": "Please enter your website or project URL."}
    if not _ip_rate_ok(ip):
        return {"ok": False, "error": "Too many requests from your network. Try again later."}
    if find_signup_by_email(email):
        return {"ok": False, "already": True,
                "error": "This email already has a key. Check your inbox, or email info@hardinai.co.uk."}
    t = create_tenant(email, plan=plan)
    signups = _load(SIGNUPS_FILE, {})
    signups[email] = {"tenant_id": t["tenant_id"], "created": _now(),
                      "ip": ip, "url": url, "terms_accepted": True}
    _save(SIGNUPS_FILE, signups)

    # Deliver the key by email (verifies the address is real and theirs).
    body = (
        "Welcome to Hardin Memory.\n\n"
        "Here is your API key (keep it secret):\n\n"
        f"    {t['api_key']}\n\n"
        "Quickstart:\n"
        "  curl -X POST https://memory.hardinai.co.uk/v1/memory/remember \\\n"
        f"    -H \"Authorization: Bearer {t['api_key']}\" \\\n"
        "    -H \"Content-Type: application/json\" \\\n"
        "    -d '{\"text\": \"hello\", \"kind\": \"fact\", \"source\": \"test\"}'\n\n"
        "Free tier: 10,000 writes + 10,000 reads / month.\n"
        "Docs: https://memory.hardinai.co.uk\n\n"
        "— Hardin AI · info@hardinai.co.uk")
    sent = False
    try:
        from . import company_mail as cm
    except Exception:
        try:
            from api import company_mail as cm
        except Exception:
            cm = None
    if cm:
        try:
            sent = cm.send_transactional(email, "Your Hardin Memory API key", body).get("ok", False)
        except Exception:
            sent = False

    if sent:
        return {"ok": True, "emailed": True, "email": email}
    # Fallback: if email could not be sent, show the key on the page so the user
    # still gets it (their tenant exists either way).
    return {"ok": True, "emailed": False, "email": email, "api_key": t["api_key"]}


# ── Usage meter ──────────────────────────────────────────────────────────
def _bump(tenant_id: str, op: str) -> dict:
    u = _load(USAGE_FILE, {})
    rec = u.get(tenant_id) or {}
    if rec.get("month") != _month():
        rec = {"month": _month()}
    rec[op] = rec.get(op, 0) + 1
    rec["total"] = rec.get("total", 0) + 1
    u[tenant_id] = rec
    _save(USAGE_FILE, u)
    return rec


def usage(tenant_id: str) -> dict:
    return _load(USAGE_FILE, {}).get(tenant_id, {"month": _month(), "total": 0})


# ── Billing helpers (link tenant ↔ Stripe; track what's been reported) ───
def find_by_tenant_id(tenant_id: str):
    """Return (key_hash, record) for a tenant_id, else (None, None)."""
    for kh, rec in _load(TENANTS_FILE, {}).items():
        if rec.get("tenant_id") == tenant_id:
            return kh, rec
    return None, None


def update_tenant(tenant_id: str, **fields) -> bool:
    """Patch a tenant record (e.g. plan, stripe_customer_id). Returns success."""
    tenants = _load(TENANTS_FILE, {})
    kh, rec = None, None
    for k, r in tenants.items():
        if r.get("tenant_id") == tenant_id:
            kh, rec = k, r
            break
    if not rec:
        return False
    rec.update(fields)
    tenants[kh] = rec
    _save(TENANTS_FILE, tenants)
    return True


def unreported_ops(tenant_id: str) -> int:
    """How many metered ops this month have NOT yet been pushed to Stripe."""
    u = usage(tenant_id)
    if u.get("month") != _month():
        return 0
    return max(0, int(u.get("total", 0)) - int(u.get("reported", 0)))


def mark_reported(tenant_id: str, n: int):
    u = _load(USAGE_FILE, {})
    rec = u.get(tenant_id) or {"month": _month()}
    rec["reported"] = int(rec.get("reported", 0)) + int(n)
    u[tenant_id] = rec
    _save(USAGE_FILE, u)


def _within_limit(tenant: dict, kind: str) -> bool:
    limits = PLAN_LIMITS.get(tenant.get("plan", "free"), PLAN_LIMITS["free"])
    u = usage(tenant["tenant_id"])
    if u.get("month") != _month():
        return True
    if kind == "write":
        return u.get("remember", 0) < limits["writes_per_month"]
    return u.get("recall", 0) < limits["reads_per_month"]


# ── Governed actions (per-tenant) ────────────────────────────────────────
def remember(tenant: dict, text: str, kind: str = "fact", source: str = "api",
             image_path: str = None, auto_version: bool = False,
             supersedes: str = None) -> dict:
    """auto_version=True: if this write contradicts an existing verified memory,
    it is written as a SIGNED correction that supersedes the old one (a
    temporal edge) instead of being rejected outright. supersedes=<shard_id>:
    explicitly version a named fact (caller already knows which one it replaces)."""
    if not _within_limit(tenant, "write"):
        return {"error": "monthly write limit reached for plan", "limited": True}
    try:
        principal = _principal(tenant)
    except ValueError as exc:
        return {"error": str(exc), "error_code": "invalid_principal"}
    authority_db = _tenant_db(tenant["tenant_id"])
    out = mem.remember(text, image_path=image_path, kind=kind, source=source,
                       db_path=authority_db,
                       auto_version=auto_version, supersedes=supersedes,
                       principal=principal, private=True,
                       require_governance=True)
    if out.get("error"):
        _bump(tenant["tenant_id"], "remember")
        return out
    # If the poison gate rejected the write, return the rejection directly
    if out.get("rejected"):
        _bump(tenant["tenant_id"], "remember")  # still count the attempt
        return out
    # Near-duplicate of an existing fact: no new shard was written, existing
    # shard_id is returned as-is so the caller can still reference it.
    if out.get("deduplicated"):
        _bump(tenant["tenant_id"], "remember")  # still count the attempt
        return out
    _bump(tenant["tenant_id"], "remember")
    shadow_status = _shadow_sync(authority_db, principal)
    return {"shard_id": out["shard_id"], "signed": out["signed"],
            "chain_index": out["chain_index"], "created": out["created"],
            "supersedes": out.get("supersedes") or [],
            "versioned": out.get("versioned", False),
            "area_five_shadow": shadow_status}


def recall(tenant: dict, query: str, k: int = 5) -> dict:
    if not _within_limit(tenant, "read"):
        return {"error": "monthly read limit reached for plan", "limited": True}
    try:
        principal = _principal(tenant)
    except ValueError as exc:
        return {"error": str(exc), "error_code": "invalid_principal"}
    authority_db = _tenant_db(tenant["tenant_id"])
    shadow_status = _shadow_sync(authority_db, principal)
    if shadow_status.get("status") == "governance_error":
        code = shadow_status.get("error_code", "governance_unavailable")
        return {"error": "memory operation denied by governance"
                         if code == "governance_denied"
                         else "memory governance unavailable",
                "error_code": code, "authorized": False}

    routed = None
    if area_five_shadow is not None and area_five_shadow.enabled() \
            and shadow_status.get("status") in ("current", "rebuilt"):
        try:
            routed = area_five_shadow.route(query, k, principal)
        except Exception as exc:
            routed = {"candidate_shard_ids": [], "routing_trace": {
                "router": "area-five-shadow/1", "stop_reason": "route_error",
                "reason": type(exc).__name__, "routing_work": 0}}

    if routed and routed.get("candidate_shard_ids"):
        out = mem.recall(
            query, k=k, db_path=authority_db, principal=principal, private=True,
            require_governance=True,
            candidate_shard_ids=routed["candidate_shard_ids"])
        if out.get("error"):
            _bump(tenant["tenant_id"], "recall")
            return out
        if out.get("results"):
            _bump(tenant["tenant_id"], "recall")
            trace = dict(routed["routing_trace"], authority_fallback=False)
            return {"query": out["query"], "results": out["results"],
                    "total_shards": out["total_shards"],
                    "area_five_shadow": trace}

    out = mem.recall(query, k=k, db_path=authority_db,
                     principal=principal, private=True,
                     require_governance=True)
    _bump(tenant["tenant_id"], "recall")
    if out.get("error"):
        return out
    trace = dict((routed or {}).get("routing_trace") or {},
                 authority_fallback=True,
                 stop_reason="authority_fallback")
    trace.setdefault("router", "area-five-shadow/1")
    trace["sync_status"] = shadow_status.get("status")
    return {"query": out["query"], "results": out["results"],
            "total_shards": out["total_shards"],
            "area_five_shadow": trace}


def verify(tenant: dict, shard_id: str) -> dict:
    out = mem.verify_shard(shard_id, db_path=_tenant_db(tenant["tenant_id"]))
    _bump(tenant["tenant_id"], "verify")
    return out


def audit(tenant: dict) -> dict:
    out = mem.audit(db_path=_tenant_db(tenant["tenant_id"]))
    _bump(tenant["tenant_id"], "audit")
    return out


def history(tenant: dict, shard_id: str) -> dict:
    """Full signed version timeline for a fact — every prior belief, when it
    changed, and proof none of it was tampered with."""
    out = mem.history(shard_id, db_path=_tenant_db(tenant["tenant_id"]))
    _bump(tenant["tenant_id"], "recall")
    return out


def entities(tenant: dict, type_filter: str = None) -> dict:
    """Summary of every named entity (email/company/custom) this store has
    linked, ranked by mentions."""
    out = mem.list_entities(type_filter=type_filter, db_path=_tenant_db(tenant["tenant_id"]))
    _bump(tenant["tenant_id"], "recall")
    return {"entities": out, "count": len(out)}


def entity_history(tenant: dict, name: str) -> dict:
    """Eligible signed entity history scoped to the authenticated tenant."""
    try:
        principal = _principal(tenant)
    except ValueError as exc:
        return {"error": str(exc), "error_code": "invalid_principal"}
    out = mem.entity_shards(name, db_path=_tenant_db(tenant["tenant_id"]),
                            principal=principal)
    _bump(tenant["tenant_id"], "recall")
    return {"name": name, "shards": out, "count": len(out)}


# -- Tiered memory: 3-tier trust split (facts / prefs / learned policy) ----
# Adaptivity (Tier 2/3) can never grant an entitlement; decisions read only the
# signed Tier-1 facts store. See api/tbn_memory_tiers.py.
def _tiers():
    try:
        from . import tbn_memory_tiers as tiers
    except Exception:
        from api import tbn_memory_tiers as tiers
    return tiers


def facts_record(tenant: dict, fact_type: str, subject: str, data: dict, source: str) -> dict:
    out = _tiers().record_fact(tenant["tenant_id"], fact_type, subject, data, source, privileged=True)
    if out.get("ok"):
        _bump(tenant["tenant_id"], "remember")
    return out


def facts_get(tenant: dict, fact_type=None, subject=None) -> dict:
    _bump(tenant["tenant_id"], "recall")
    return {"facts": _tiers().get_facts(tenant["tenant_id"], fact_type=fact_type, subject=subject)}


def entitlement_check(tenant: dict, subject: str, entitlement: str) -> dict:
    _bump(tenant["tenant_id"], "recall")
    return _tiers().check_entitlement(tenant["tenant_id"], subject, entitlement)


def facts_audit(tenant: dict) -> dict:
    return _tiers().audit_facts(tenant["tenant_id"])


def prefs_set(tenant: dict, key: str, value, source: str = "user") -> dict:
    return _tiers().set_preference(tenant["tenant_id"], key, value, source=source)


def prefs_get(tenant: dict) -> dict:
    return {"preferences": _tiers().get_preferences(tenant["tenant_id"])}


def policy_propose(tenant: dict, name: str, rule: dict, rationale: str = "", proposed_by: str = "learning") -> dict:
    return _tiers().propose_policy(tenant["tenant_id"], name, rule, rationale=rationale, proposed_by=proposed_by)


def policy_pending(tenant: dict) -> dict:
    return {"pending": _tiers().list_pending_policies(tenant["tenant_id"])}


def policy_approve(tenant: dict, proposal_id: str, approver: str, rendered_context: dict = None) -> dict:
    return _tiers().approve_policy(tenant["tenant_id"], proposal_id, approver,
                                   rendered_context=rendered_context)


def policy_reject(tenant: dict, proposal_id: str, approver: str, reason: str = "",
                  rendered_context: dict = None) -> dict:
    return _tiers().reject_policy(tenant["tenant_id"], proposal_id, approver, reason=reason,
                                  rendered_context=rendered_context)


def refusal_log(tenant: dict, subject: str, action: str, reason: str,
                rendered_context: dict = None, source: str = "governance") -> dict:
    out = _tiers().log_refusal(tenant["tenant_id"], subject, action, reason,
                               rendered_context=rendered_context, source=source)
    if out.get("ok"):
        _bump(tenant["tenant_id"], "remember")
    return out


def refusal_followup(tenant: dict, refusal_id: str, followup: str, followup_source: str = "system") -> dict:
    out = _tiers().record_followup(tenant["tenant_id"], refusal_id, followup,
                                   followup_source=followup_source)
    if out.get("ok"):
        _bump(tenant["tenant_id"], "remember")
    return out


def refusals_get(tenant: dict, subject: str = None) -> dict:
    _bump(tenant["tenant_id"], "recall")
    return {"refusals": _tiers().get_refusals(tenant["tenant_id"], subject=subject)}


def policy_active(tenant: dict) -> dict:
    return {"active": _tiers().get_active_policies(tenant["tenant_id"])}


def decide(tenant: dict, subject: str, entitlement: str) -> dict:
    _bump(tenant["tenant_id"], "recall")
    return _tiers().decide(tenant["tenant_id"], subject, entitlement)


# -- Feedback & learning loop (Tier 2/3 only) ------------------------------
def _learn():
    try:
        from . import tbn_memory_learning as L
    except Exception:
        from api import tbn_memory_learning as L
    return L


def record_outcome(tenant: dict, subject: str, decision: str, outcome: str,
                   sentiment=None, signal=None, weight=1.0, context=None) -> dict:
    out = _learn().record_outcome(tenant["tenant_id"], subject, decision, outcome,
                                  sentiment=sentiment, signal=signal, weight=weight, context=context)
    if out.get("ok"):
        _bump(tenant["tenant_id"], "remember")
    return out


def outcome_stats(tenant: dict) -> dict:
    return _learn().outcome_stats(tenant["tenant_id"])


def learn_tune(tenant: dict, min_support: int = 3, consistency: float = 0.6) -> dict:
    return _learn().tune(tenant["tenant_id"], min_support=min_support, consistency=consistency)


def get_profile(tenant: dict, subject: str) -> dict:
    return _learn().get_profile(tenant["tenant_id"], subject)


def revoke_entitlement(tenant: dict, subject: str, entitlement: str, source: str, reason: str = "") -> dict:
    out = _tiers().revoke_entitlement(tenant["tenant_id"], subject, entitlement, source, reason=reason, privileged=True)
    if out.get("ok"):
        _bump(tenant["tenant_id"], "remember")
    return out
