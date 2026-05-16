"""
TBN Budget & Cost Enforcement System
Prevents AI agents from exceeding operational boundaries.

This is the "Trojan Horse" — solves the immediate pain point of
runaway LLM costs and infinite-loop API billing, while establishing
TBN as the enforcement layer for all agent operations.

Features:
- Per-bot budget limits (daily/monthly)
- API call tracking and rate limiting
- Real-time spend monitoring
- Automatic bot suspension when limits hit
- Cost alerts and notifications
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
import json
import os
import uuid

budget_enforcement = Blueprint('budget_enforcement', __name__)

# Budget data storage
BUDGETS_FILE = "data/bot_budgets.json"
USAGE_FILE = "data/bot_usage.json"


def _load_budgets():
    if os.path.exists(BUDGETS_FILE):
        with open(BUDGETS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_budgets(data):
    os.makedirs(os.path.dirname(BUDGETS_FILE) or ".", exist_ok=True)
    with open(BUDGETS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _load_usage():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_usage(data):
    os.makedirs(os.path.dirname(USAGE_FILE) or ".", exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Set Budget ────────────────────────────────────────────────────────

@budget_enforcement.route("/set", methods=["POST"])
def set_budget():
    """
    Set budget limits for a bot.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "daily_limit": 50.00,
        "monthly_limit": 1000.00,
        "max_api_calls_per_hour": 100,
        "max_api_calls_per_day": 2000,
        "currency": "GBP",
        "alert_threshold": 0.8
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    
    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    
    budgets = _load_budgets()
    budgets[bot_id] = {
        "bot_id": bot_id,
        "daily_limit": data.get("daily_limit", 50.00),
        "monthly_limit": data.get("monthly_limit", 1000.00),
        "max_api_calls_per_hour": data.get("max_api_calls_per_hour", 100),
        "max_api_calls_per_day": data.get("max_api_calls_per_day", 2000),
        "currency": data.get("currency", "GBP"),
        "alert_threshold": data.get("alert_threshold", 0.8),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    _save_budgets(budgets)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "budget": budgets[bot_id],
        "message": f"Budget set: £{budgets[bot_id]['daily_limit']}/day, £{budgets[bot_id]['monthly_limit']}/month, {budgets[bot_id]['max_api_calls_per_day']} calls/day"
    })


# ── Track Usage ───────────────────────────────────────────────────────

@budget_enforcement.route("/track", methods=["POST"])
def track_usage():
    """
    Track an API call or cost event for a bot.
    Called every time a bot makes an API call or incurs a cost.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "cost": 0.03,
        "operation": "llm_call",
        "model": "gpt-4",
        "tokens": 1500
    }
    
    Returns whether the bot is still within budget or has been suspended.
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    cost = data.get("cost", 0.0)
    operation = data.get("operation", "api_call")
    
    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    
    # Load budget and usage
    budgets = _load_budgets()
    usage = _load_usage()
    
    # Check if bot has a budget set
    budget = budgets.get(bot_id)
    if not budget:
        return jsonify({
            "success": True,
            "bot_id": bot_id,
            "allowed": True,
            "message": "No budget set — operation allowed (unlimited)"
        })
    
    # Check if bot is suspended
    if budget.get("status") == "suspended":
        return jsonify({
            "success": False,
            "bot_id": bot_id,
            "allowed": False,
            "reason": "BUDGET_EXCEEDED",
            "message": "❌ Bot SUSPENDED — budget limit reached. Reset or increase budget."
        }), 403
    
    # Initialize usage tracking for this bot
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    if bot_id not in usage:
        usage[bot_id] = {"daily": {}, "hourly": {}, "monthly": {}, "total_cost": 0, "total_calls": 0}
    
    bot_usage = usage[bot_id]
    
    # Track this call
    bot_usage["daily"][today] = bot_usage["daily"].get(today, {"cost": 0, "calls": 0})
    bot_usage["daily"][today]["cost"] += cost
    bot_usage["daily"][today]["calls"] += 1
    
    bot_usage["hourly"][this_hour] = bot_usage["hourly"].get(this_hour, {"cost": 0, "calls": 0})
    bot_usage["hourly"][this_hour]["cost"] += cost
    bot_usage["hourly"][this_hour]["calls"] += 1
    
    bot_usage["monthly"][this_month] = bot_usage["monthly"].get(this_month, {"cost": 0, "calls": 0})
    bot_usage["monthly"][this_month]["cost"] += cost
    bot_usage["monthly"][this_month]["calls"] += 1
    
    bot_usage["total_cost"] += cost
    bot_usage["total_calls"] += 1
    
    # Check limits
    daily_cost = bot_usage["daily"][today]["cost"]
    daily_calls = bot_usage["daily"][today]["calls"]
    hourly_calls = bot_usage["hourly"][this_hour]["calls"]
    monthly_cost = bot_usage["monthly"][this_month]["cost"]
    
    alerts = []
    suspended = False
    
    # Daily cost limit
    if daily_cost >= budget["daily_limit"]:
        suspended = True
        alerts.append(f"Daily cost limit exceeded: £{daily_cost:.2f}/£{budget['daily_limit']:.2f}")
    elif daily_cost >= budget["daily_limit"] * budget["alert_threshold"]:
        alerts.append(f"⚠️ Approaching daily limit: £{daily_cost:.2f}/£{budget['daily_limit']:.2f}")
    
    # Monthly cost limit
    if monthly_cost >= budget["monthly_limit"]:
        suspended = True
        alerts.append(f"Monthly cost limit exceeded: £{monthly_cost:.2f}/£{budget['monthly_limit']:.2f}")
    
    # Hourly API call limit
    if hourly_calls >= budget["max_api_calls_per_hour"]:
        suspended = True
        alerts.append(f"Hourly call limit exceeded: {hourly_calls}/{budget['max_api_calls_per_hour']}")
    
    # Daily API call limit
    if daily_calls >= budget["max_api_calls_per_day"]:
        suspended = True
        alerts.append(f"Daily call limit exceeded: {daily_calls}/{budget['max_api_calls_per_day']}")
    
    # Suspend bot if limits exceeded
    if suspended:
        budgets[bot_id]["status"] = "suspended"
        budgets[bot_id]["suspended_at"] = datetime.now(timezone.utc).isoformat()
        budgets[bot_id]["suspension_reason"] = alerts[0]
        _save_budgets(budgets)
    
    _save_usage(usage)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "allowed": not suspended,
        "operation": operation,
        "cost_tracked": cost,
        "daily_spend": round(daily_cost, 4),
        "daily_limit": budget["daily_limit"],
        "daily_calls": daily_calls,
        "monthly_spend": round(monthly_cost, 4),
        "alerts": alerts,
        "status": "suspended" if suspended else "active",
        "message": "❌ SUSPENDED — limit exceeded" if suspended else "✅ Within budget"
    })


# ── Check Budget ──────────────────────────────────────────────────────

@budget_enforcement.route("/check/<bot_id>", methods=["GET"])
def check_budget(bot_id):
    """Check a bot's current budget status and usage."""
    budgets = _load_budgets()
    usage = _load_usage()
    
    budget = budgets.get(bot_id)
    if not budget:
        return jsonify({
            "success": False,
            "bot_id": bot_id,
            "message": "No budget set for this bot"
        }), 404
    
    bot_usage = usage.get(bot_id, {"daily": {}, "monthly": {}, "total_cost": 0, "total_calls": 0})
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    daily_cost = bot_usage["daily"].get(today, {}).get("cost", 0)
    daily_calls = bot_usage["daily"].get(today, {}).get("calls", 0)
    monthly_cost = bot_usage["monthly"].get(this_month, {}).get("cost", 0)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "status": budget["status"],
        "budget": {
            "daily_limit": budget["daily_limit"],
            "monthly_limit": budget["monthly_limit"],
            "max_api_calls_per_hour": budget["max_api_calls_per_hour"],
            "max_api_calls_per_day": budget["max_api_calls_per_day"],
            "currency": budget["currency"]
        },
        "usage_today": {
            "cost": round(daily_cost, 4),
            "calls": daily_calls,
            "cost_remaining": round(budget["daily_limit"] - daily_cost, 4),
            "calls_remaining": budget["max_api_calls_per_day"] - daily_calls,
            "percent_used": round((daily_cost / budget["daily_limit"]) * 100, 1) if budget["daily_limit"] > 0 else 0
        },
        "usage_month": {
            "cost": round(monthly_cost, 4),
            "percent_used": round((monthly_cost / budget["monthly_limit"]) * 100, 1) if budget["monthly_limit"] > 0 else 0
        },
        "lifetime": {
            "total_cost": round(bot_usage["total_cost"], 4),
            "total_calls": bot_usage["total_calls"]
        }
    })


# ── Reset / Resume ────────────────────────────────────────────────────

@budget_enforcement.route("/reset/<bot_id>", methods=["POST"])
def reset_budget(bot_id):
    """Reset a suspended bot's budget (re-activate it)."""
    budgets = _load_budgets()
    
    if bot_id not in budgets:
        return jsonify({"error": "No budget found for this bot"}), 404
    
    budgets[bot_id]["status"] = "active"
    budgets[bot_id]["suspended_at"] = None
    budgets[bot_id]["suspension_reason"] = None
    budgets[bot_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_budgets(budgets)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "status": "active",
        "message": "✅ Bot reactivated. Budget limits still apply."
    })


# ── Dashboard ─────────────────────────────────────────────────────────

@budget_enforcement.route("/dashboard", methods=["GET"])
def budget_dashboard():
    """Get budget overview for all bots."""
    budgets = _load_budgets()
    usage = _load_usage()
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    bots_summary = []
    total_daily_spend = 0
    total_monthly_spend = 0
    suspended_count = 0
    
    for bot_id, budget in budgets.items():
        bot_usage = usage.get(bot_id, {"daily": {}, "monthly": {}, "total_cost": 0})
        daily_cost = bot_usage["daily"].get(today, {}).get("cost", 0)
        monthly_cost = bot_usage["monthly"].get(this_month, {}).get("cost", 0)
        
        total_daily_spend += daily_cost
        total_monthly_spend += monthly_cost
        if budget["status"] == "suspended":
            suspended_count += 1
        
        bots_summary.append({
            "bot_id": bot_id,
            "status": budget["status"],
            "daily_spend": round(daily_cost, 4),
            "daily_limit": budget["daily_limit"],
            "monthly_spend": round(monthly_cost, 4),
            "monthly_limit": budget["monthly_limit"],
            "percent_daily": round((daily_cost / budget["daily_limit"]) * 100, 1) if budget["daily_limit"] > 0 else 0
        })
    
    return jsonify({
        "success": True,
        "summary": {
            "total_bots_with_budgets": len(budgets),
            "active": len(budgets) - suspended_count,
            "suspended": suspended_count,
            "total_daily_spend": round(total_daily_spend, 4),
            "total_monthly_spend": round(total_monthly_spend, 4),
            "currency": "GBP"
        },
        "bots": bots_summary
    })
