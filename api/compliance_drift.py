"""
TBN Compliance Drift System
Tracks the gap between stated policy and actual bot behavior.
The "Aha!" metric for executives — shows where bots are drifting from their certified state.

Drift Types:
- Identity Drift: Bot endpoint or system prompt changed
- Config Drift: Bot settings changed (model, temperature, etc.)
- Budget Drift: Bot spending pattern deviates from budget
- Behavior Drift: Bot responses changing over time
- Certification Drift: Bot overdue for re-test
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
import json
import os
import hashlib

compliance_drift = Blueprint('compliance_drift', __name__)

DRIFT_FILE = "data/compliance_drift.json"
POLICY_FILE = "data/bot_policies.json"


def _load_drift():
    if os.path.exists(DRIFT_FILE):
        with open(DRIFT_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_drift(data):
    os.makedirs(os.path.dirname(DRIFT_FILE) or ".", exist_ok=True)
    with open(DRIFT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _load_policies():
    if os.path.exists(POLICY_FILE):
        with open(POLICY_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_policies(data):
    os.makedirs(os.path.dirname(POLICY_FILE) or ".", exist_ok=True)
    with open(POLICY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_drift(bot_id, drift_type, severity, description, policy_value=None, actual_value=None):
    """
    Record a compliance drift event.
    Called internally when drift is detected.
    """
    drift_data = _load_drift()
    if bot_id not in drift_data:
        drift_data[bot_id] = {"events": [], "score": 100}
    
    event = {
        "type": drift_type,
        "severity": severity,  # "low", "medium", "high", "critical"
        "description": description,
        "policy_value": policy_value,
        "actual_value": actual_value,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False
    }
    
    drift_data[bot_id]["events"].append(event)
    
    # Calculate drift score (100 = perfect compliance, 0 = fully drifted)
    severity_weights = {"low": 5, "medium": 10, "high": 20, "critical": 40}
    unresolved = [e for e in drift_data[bot_id]["events"] if not e["resolved"]]
    penalty = sum(severity_weights.get(e["severity"], 10) for e in unresolved)
    drift_data[bot_id]["score"] = max(0, 100 - penalty)
    drift_data[bot_id]["last_checked"] = datetime.now(timezone.utc).isoformat()
    
    _save_drift(drift_data)
    return event


# ── Set Policy ────────────────────────────────────────────────────────

@compliance_drift.route("/policy/set", methods=["POST"])
def set_policy():
    """
    Set the compliance policy for a bot.
    This defines what the bot SHOULD be doing.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "policy": {
            "max_daily_spend": 50.0,
            "max_response_time_ms": 5000,
            "allowed_models": ["gpt-4", "gpt-3.5-turbo"],
            "max_tokens_per_request": 4000,
            "allowed_endpoints": ["https://mybot.com/api"],
            "required_system_prompt_hash": "abc123...",
            "max_hallucination_rate": 0.02,
            "must_refuse_injection": true,
            "retest_interval_hours": 24
        }
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    policy = data.get("policy", {})
    
    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    if not policy:
        return jsonify({"error": "policy is required"}), 400
    
    policies = _load_policies()
    policies[bot_id] = {
        "policy": policy,
        "set_at": datetime.now(timezone.utc).isoformat(),
        "version": policies.get(bot_id, {}).get("version", 0) + 1
    }
    _save_policies(policies)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "policy_version": policies[bot_id]["version"],
        "rules_count": len(policy),
        "message": f"Policy set with {len(policy)} rules for {bot_id}"
    })


# ── Check Drift ──────────────────────────────────────────────────────

@compliance_drift.route("/check", methods=["POST"])
def check_drift():
    """
    Check a bot's current state against its policy.
    Returns all drift events (where actual != policy).
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "current_state": {
            "daily_spend": 45.00,
            "response_time_ms": 3200,
            "model_used": "gpt-4",
            "tokens_used": 3500,
            "endpoint": "https://mybot.com/api",
            "system_prompt_hash": "abc123..."
        }
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    current_state = data.get("current_state", {})
    
    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    
    policies = _load_policies()
    bot_policy = policies.get(bot_id, {}).get("policy", {})
    
    if not bot_policy:
        return jsonify({
            "success": True,
            "bot_id": bot_id,
            "drift_detected": False,
            "message": "No policy set for this bot. Set one via /policy/set"
        })
    
    # Check each policy rule against current state
    drifts = []
    
    # Budget drift
    if "max_daily_spend" in bot_policy and "daily_spend" in current_state:
        if current_state["daily_spend"] > bot_policy["max_daily_spend"]:
            drifts.append(record_drift(bot_id, "budget_drift", "high",
                f"Daily spend £{current_state['daily_spend']} exceeds policy limit £{bot_policy['max_daily_spend']}",
                str(bot_policy["max_daily_spend"]), str(current_state["daily_spend"])))
        elif current_state["daily_spend"] > bot_policy["max_daily_spend"] * 0.8:
            drifts.append(record_drift(bot_id, "budget_drift", "medium",
                f"Daily spend £{current_state['daily_spend']} approaching limit £{bot_policy['max_daily_spend']}",
                str(bot_policy["max_daily_spend"]), str(current_state["daily_spend"])))
    
    # Response time drift
    if "max_response_time_ms" in bot_policy and "response_time_ms" in current_state:
        if current_state["response_time_ms"] > bot_policy["max_response_time_ms"]:
            drifts.append(record_drift(bot_id, "performance_drift", "medium",
                f"Response time {current_state['response_time_ms']}ms exceeds {bot_policy['max_response_time_ms']}ms",
                str(bot_policy["max_response_time_ms"]), str(current_state["response_time_ms"])))
    
    # Model drift
    if "allowed_models" in bot_policy and "model_used" in current_state:
        if current_state["model_used"] not in bot_policy["allowed_models"]:
            drifts.append(record_drift(bot_id, "config_drift", "high",
                f"Model '{current_state['model_used']}' not in allowed list: {bot_policy['allowed_models']}",
                str(bot_policy["allowed_models"]), current_state["model_used"]))
    
    # Token drift
    if "max_tokens_per_request" in bot_policy and "tokens_used" in current_state:
        if current_state["tokens_used"] > bot_policy["max_tokens_per_request"]:
            drifts.append(record_drift(bot_id, "budget_drift", "medium",
                f"Tokens {current_state['tokens_used']} exceeds limit {bot_policy['max_tokens_per_request']}",
                str(bot_policy["max_tokens_per_request"]), str(current_state["tokens_used"])))
    
    # Endpoint drift
    if "allowed_endpoints" in bot_policy and "endpoint" in current_state:
        if current_state["endpoint"] not in bot_policy["allowed_endpoints"]:
            drifts.append(record_drift(bot_id, "identity_drift", "critical",
                f"Endpoint '{current_state['endpoint']}' not in allowed list",
                str(bot_policy["allowed_endpoints"]), current_state["endpoint"]))
    
    # System prompt drift
    if "required_system_prompt_hash" in bot_policy and "system_prompt_hash" in current_state:
        if current_state["system_prompt_hash"] != bot_policy["required_system_prompt_hash"]:
            drifts.append(record_drift(bot_id, "identity_drift", "critical",
                "System prompt has changed from certified version",
                bot_policy["required_system_prompt_hash"][:16] + "...",
                current_state["system_prompt_hash"][:16] + "..."))
    
    # Load current drift score
    drift_data = _load_drift()
    bot_drift = drift_data.get(bot_id, {"score": 100, "events": []})
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "drift_detected": len(drifts) > 0,
        "compliance_score": bot_drift["score"],
        "new_drifts": len(drifts),
        "total_unresolved": len([e for e in bot_drift.get("events", []) if not e.get("resolved")]),
        "drifts": drifts,
        "message": f"{'⚠️ ' + str(len(drifts)) + ' drift(s) detected' if drifts else '✅ No drift — fully compliant'}"
    })


# ── Dashboard ─────────────────────────────────────────────────────────

@compliance_drift.route("/dashboard", methods=["GET"])
def drift_dashboard():
    """
    Compliance drift dashboard — overview of all bots.
    The "Single Pane of Glass" for executives.
    Shows the delta between stated policy and actual behavior.
    """
    drift_data = _load_drift()
    policies = _load_policies()
    
    bots_summary = []
    total_score = 0
    critical_count = 0
    
    for bot_id, data in drift_data.items():
        score = data.get("score", 100)
        total_score += score
        unresolved = [e for e in data.get("events", []) if not e.get("resolved")]
        critical = [e for e in unresolved if e.get("severity") == "critical"]
        critical_count += len(critical)
        
        bots_summary.append({
            "bot_id": bot_id,
            "compliance_score": score,
            "status": "compliant" if score >= 80 else "drifting" if score >= 50 else "non-compliant",
            "unresolved_drifts": len(unresolved),
            "critical_drifts": len(critical),
            "has_policy": bot_id in policies,
            "last_checked": data.get("last_checked")
        })
    
    avg_score = round(total_score / len(drift_data), 1) if drift_data else 100
    
    return jsonify({
        "success": True,
        "summary": {
            "total_bots_monitored": len(drift_data),
            "average_compliance_score": avg_score,
            "compliant": sum(1 for b in bots_summary if b["status"] == "compliant"),
            "drifting": sum(1 for b in bots_summary if b["status"] == "drifting"),
            "non_compliant": sum(1 for b in bots_summary if b["status"] == "non-compliant"),
            "total_critical_drifts": critical_count,
            "policies_set": len(policies)
        },
        "bots": sorted(bots_summary, key=lambda x: x["compliance_score"]),
        "message": f"Average compliance: {avg_score}% | {critical_count} critical drift(s)"
    })


# ── Resolve Drift ─────────────────────────────────────────────────────

@compliance_drift.route("/resolve", methods=["POST"])
def resolve_drift():
    """
    Mark a drift event as resolved.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "resolve_all": true  // or "drift_index": 0
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    resolve_all = data.get("resolve_all", False)
    drift_index = data.get("drift_index")
    
    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    
    drift_data = _load_drift()
    if bot_id not in drift_data:
        return jsonify({"error": "No drift data for this bot"}), 404
    
    if resolve_all:
        for event in drift_data[bot_id]["events"]:
            event["resolved"] = True
            event["resolved_at"] = datetime.now(timezone.utc).isoformat()
        drift_data[bot_id]["score"] = 100
    elif drift_index is not None and drift_index < len(drift_data[bot_id]["events"]):
        drift_data[bot_id]["events"][drift_index]["resolved"] = True
        drift_data[bot_id]["events"][drift_index]["resolved_at"] = datetime.now(timezone.utc).isoformat()
        # Recalculate score
        severity_weights = {"low": 5, "medium": 10, "high": 20, "critical": 40}
        unresolved = [e for e in drift_data[bot_id]["events"] if not e["resolved"]]
        penalty = sum(severity_weights.get(e["severity"], 10) for e in unresolved)
        drift_data[bot_id]["score"] = max(0, 100 - penalty)
    
    _save_drift(drift_data)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "new_score": drift_data[bot_id]["score"],
        "message": "All drifts resolved" if resolve_all else "Drift resolved"
    })


# ── History ───────────────────────────────────────────────────────────

@compliance_drift.route("/history/<bot_id>", methods=["GET"])
def drift_history(bot_id):
    """Get full drift history for a bot."""
    drift_data = _load_drift()
    bot_drift = drift_data.get(bot_id)
    
    if not bot_drift:
        return jsonify({
            "success": True,
            "bot_id": bot_id,
            "score": 100,
            "events": [],
            "message": "No drift events recorded"
        })
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "compliance_score": bot_drift["score"],
        "total_events": len(bot_drift["events"]),
        "unresolved": len([e for e in bot_drift["events"] if not e.get("resolved")]),
        "events": bot_drift["events"][-20:],  # Last 20
        "last_checked": bot_drift.get("last_checked")
    })
