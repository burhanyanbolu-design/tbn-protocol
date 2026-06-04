"""
TBN Access Control — API Key & Subscription Management
-------------------------------------------------------
No more free bot creation. Companies pay to ACCESS our bots.

Tiers:
  TRIAL    — 7 days free, 100 calls/day,  read-only, 3 bots
  STARTER  — £99/mo,      1,000 calls/day, 10 bots
  PRO      — £299/mo,     10,000 calls/day, all bots
  ENTERPRISE — custom,   unlimited,        all bots + dedicated support

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-AC-4b9e7f2c
"""

import os
import json
import hashlib
import secrets
import string
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify

# ── Tier definitions ─────────────────────────────────────────────────

TIERS = {
    "TRIAL": {
        "name":        "Trial",
        "price_gbp":   0,
        "calls_per_day": 100,
        "bot_access":  3,          # max number of bots they can query
        "duration_days": 7,        # trial expires after 7 days
        "features":    ["read_only", "basic_search"],
    },
    "STARTER": {
        "name":        "Starter",
        "price_gbp":   99,
        "calls_per_day": 1_000,
        "bot_access":  10,
        "duration_days": None,     # no expiry (monthly subscription)
        "features":    ["read_only", "basic_search", "sports_data", "financial_data"],
    },
    "PRO": {
        "name":        "Pro",
        "price_gbp":   299,
        "calls_per_day": 10_000,
        "bot_access":  None,       # all bots
        "duration_days": None,
        "features":    ["read_write", "all_data", "real_time", "analytics", "webhooks"],
    },
    "ENTERPRISE": {
        "name":        "Enterprise",
        "price_gbp":   None,       # custom pricing
        "calls_per_day": None,     # unlimited
        "bot_access":  None,       # all bots
        "duration_days": None,
        "features":    ["read_write", "all_data", "real_time", "analytics",
                        "webhooks", "dedicated_support", "sla", "custom_bots"],
    },
    "PRODUCTION": {
        "name":        "Production Partner",
        "price_gbp":   None,       # partnership agreement
        "calls_per_day": None,     # unlimited
        "bot_access":  None,       # all bots
        "duration_days": None,
        "features":    ["read_write", "all_data", "real_time", "analytics",
                        "webhooks", "dedicated_support", "sla", "production_attestation"],
    },
}

# ── API Key storage (JSON file — upgrade to DB when scaling) ─────────

KEYS_FILE = "data/api_keys.json"

def _load_keys() -> dict:
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            return json.load(f)
    return {}

def _save_keys(keys: dict):
    os.makedirs("data", exist_ok=True)
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

# ── Key generation ────────────────────────────────────────────────────

def generate_api_key(company_name: str, email: str, tier: str = "TRIAL") -> dict:
    """
    Create a new API key for a company.
    Returns the key record (save the raw key — it's shown only once).
    """
    if tier not in TIERS:
        raise ValueError(f"Invalid tier. Choose from: {list(TIERS)}")

    # Generate key: tbn_live_<32 random chars>
    alphabet = string.ascii_letters + string.digits
    raw_key  = "tbn_live_" + "".join(secrets.choice(alphabet) for _ in range(32))
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    tier_cfg = TIERS[tier]
    now      = datetime.now(timezone.utc)
    expires  = (now + timedelta(days=tier_cfg["duration_days"])).isoformat() \
               if tier_cfg["duration_days"] else None

    record = {
        "key_hash":     key_hash,
        "company":      company_name,
        "email":        email,
        "tier":         tier,
        "active":       True,
        "created_at":   now.isoformat(),
        "expires_at":   expires,
        "calls_today":  0,
        "calls_total":  0,
        "last_call_date": None,
        "bots_accessed": [],
    }

    keys = _load_keys()
    keys[key_hash] = record
    _save_keys(keys)

    # Return record WITH raw key (shown once only)
    return {**record, "api_key": raw_key}


def revoke_api_key(key_hash: str) -> bool:
    """Revoke an API key."""
    keys = _load_keys()
    if key_hash in keys:
        keys[key_hash]["active"] = False
        _save_keys(keys)
        return True
    return False


# ── Key validation ────────────────────────────────────────────────────

def validate_api_key(raw_key: str) -> tuple[bool, dict | None, str]:
    """
    Validate an API key.
    Returns (valid, record, reason).
    """
    if not raw_key or not raw_key.startswith("tbn_live_"):
        return False, None, "Invalid key format"

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    keys     = _load_keys()
    record   = keys.get(key_hash)

    if not record:
        return False, None, "API key not found"

    if not record["active"]:
        return False, None, "API key has been revoked"

    # Check expiry
    if record["expires_at"]:
        expires = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > expires:
            return False, None, "API key has expired — please upgrade your plan"

    # Check daily rate limit
    tier_cfg   = TIERS[record["tier"]]
    limit      = tier_cfg["calls_per_day"]
    today      = datetime.now(timezone.utc).date().isoformat()

    if record["last_call_date"] != today:
        # Reset daily counter
        record["calls_today"]    = 0
        record["last_call_date"] = today

    if limit and record["calls_today"] >= limit:
        return False, record, f"Daily limit reached ({limit} calls/day). Upgrade to get more."

    return True, record, "OK"


def record_api_call(record: dict, bot_id: str = None):
    """Increment call counters after a successful API call."""
    key_hash = record["key_hash"]
    keys     = _load_keys()
    if key_hash not in keys:
        return

    today = datetime.now(timezone.utc).date().isoformat()
    if keys[key_hash]["last_call_date"] != today:
        keys[key_hash]["calls_today"]    = 0
        keys[key_hash]["last_call_date"] = today

    keys[key_hash]["calls_today"]  += 1
    keys[key_hash]["calls_total"]  += 1

    if bot_id and bot_id not in keys[key_hash]["bots_accessed"]:
        keys[key_hash]["bots_accessed"].append(bot_id)

    _save_keys(keys)


def check_bot_access(record: dict, bot_id: str) -> tuple[bool, str]:
    """Check if this API key's tier allows access to a specific bot."""
    tier_cfg   = TIERS[record["tier"]]
    bot_limit  = tier_cfg["bot_access"]

    if bot_limit is None:
        return True, "OK"  # unlimited

    accessed = record.get("bots_accessed", [])
    if bot_id in accessed:
        return True, "OK"  # already accessed this bot

    if len(accessed) >= bot_limit:
        return False, (
            f"Your {record['tier']} plan allows access to {bot_limit} bots. "
            f"Upgrade to Pro for unlimited bot access."
        )

    return True, "OK"


# ── Flask decorator ───────────────────────────────────────────────────

def require_api_key(f):
    """
    Decorator — protect any route with API key authentication.

    Clients pass key in header:
        Authorization: Bearer tbn_live_xxxx
    or query param:
        ?api_key=tbn_live_xxxx
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract key from header or query param
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_key = auth_header[7:]
        else:
            raw_key = request.args.get("api_key", "")

        valid, record, reason = validate_api_key(raw_key)

        if not valid:
            return jsonify({
                "error":   "Unauthorized",
                "reason":  reason,
                "upgrade": "https://tbn.hardinai.co.uk/pricing",
            }), 401

        # Attach record to request context for use in route
        request.tbn_key_record = record
        return f(*args, **kwargs)

    return decorated


# ── Admin helpers ─────────────────────────────────────────────────────

def list_all_keys() -> list:
    """List all API keys (admin use only — never expose raw keys)."""
    keys = _load_keys()
    return [
        {k: v for k, v in rec.items() if k != "key_hash"}
        for rec in keys.values()
    ]


def get_key_stats() -> dict:
    """Summary stats for the admin dashboard."""
    keys   = _load_keys()
    active = [r for r in keys.values() if r["active"]]
    tiers  = {}
    for r in active:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1

    return {
        "total_keys":  len(keys),
        "active_keys": len(active),
        "by_tier":     tiers,
        "total_calls": sum(r["calls_total"] for r in keys.values()),
    }
