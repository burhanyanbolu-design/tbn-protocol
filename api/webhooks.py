"""
TBN Webhook Notification System
Alerts when bots fail re-tests, hit budget limits, or fingerprint mismatches.
Supports Slack, email, and custom webhook URLs.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import json
import os
import requests as http_requests
import threading

webhooks = Blueprint('webhooks', __name__)

WEBHOOKS_FILE = "data/webhooks.json"


def _load_webhooks():
    if os.path.exists(WEBHOOKS_FILE):
        with open(WEBHOOKS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_webhooks(data):
    os.makedirs(os.path.dirname(WEBHOOKS_FILE) or ".", exist_ok=True)
    with open(WEBHOOKS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_webhook(bot_id, event_type, message, details=None):
    """
    Send a webhook notification for a bot event.
    Called internally by other modules when events occur.
    
    event_type: "budget_exceeded", "retest_failed", "fingerprint_mismatch", 
                "certification_expired", "bot_suspended", "bot_certified"
    """
    hooks = _load_webhooks()
    bot_hooks = hooks.get(bot_id, {}).get("endpoints", [])
    global_hooks = hooks.get("_global", {}).get("endpoints", [])
    
    all_hooks = bot_hooks + global_hooks
    if not all_hooks:
        return
    
    payload = {
        "event": event_type,
        "bot_id": bot_id,
        "message": message,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "TBN Protocol"
    }
    
    # Send async to not block the main request
    def _send():
        for hook in all_hooks:
            url = hook.get("url", "")
            hook_type = hook.get("type", "custom")
            try:
                if hook_type == "slack":
                    # Slack webhook format
                    slack_payload = {
                        "text": f"🛡️ *TBN Alert* — {event_type}",
                        "blocks": [
                            {"type": "header", "text": {"type": "plain_text", "text": f"🛡️ TBN Alert: {event_type}"}},
                            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Bot:* `{bot_id}`\n*Message:* {message}"}},
                        ]
                    }
                    http_requests.post(url, json=slack_payload, timeout=5)
                else:
                    # Generic webhook
                    http_requests.post(url, json=payload, timeout=5)
                
                # Log successful delivery
                _log_delivery(bot_id, event_type, url, "delivered")
            except Exception as e:
                _log_delivery(bot_id, event_type, url, f"failed: {str(e)}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


DELIVERY_LOG_FILE = "data/webhook_deliveries.json"


def _log_delivery(bot_id, event_type, url, status):
    """Log webhook delivery attempt."""
    try:
        logs = []
        if os.path.exists(DELIVERY_LOG_FILE):
            with open(DELIVERY_LOG_FILE, "r") as f:
                logs = json.load(f)
        logs.append({
            "bot_id": bot_id,
            "event": event_type,
            "url": url[:50] + "...",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        # Keep last 100 entries
        logs = logs[-100:]
        os.makedirs(os.path.dirname(DELIVERY_LOG_FILE) or ".", exist_ok=True)
        with open(DELIVERY_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except:
        pass


# ── API Endpoints ─────────────────────────────────────────────────────

@webhooks.route("/register", methods=["POST"])
def register_webhook():
    """
    Register a webhook endpoint for bot notifications.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx" or "_global" for all bots,
        "url": "https://hooks.slack.com/services/xxx" or any URL,
        "type": "slack" or "custom",
        "events": ["budget_exceeded", "retest_failed", "fingerprint_mismatch"]
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "_global").strip()
    url = data.get("url", "").strip()
    hook_type = data.get("type", "custom")
    events = data.get("events", ["all"])
    
    if not url:
        return jsonify({"error": "url is required"}), 400
    
    hooks = _load_webhooks()
    if bot_id not in hooks:
        hooks[bot_id] = {"endpoints": []}
    
    hooks[bot_id]["endpoints"].append({
        "url": url,
        "type": hook_type,
        "events": events,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    _save_webhooks(hooks)
    
    return jsonify({
        "success": True,
        "bot_id": bot_id,
        "webhook_url": url[:30] + "...",
        "type": hook_type,
        "events": events,
        "message": f"Webhook registered for {'all bots' if bot_id == '_global' else bot_id}"
    })


@webhooks.route("/list", methods=["GET"])
def list_webhooks():
    """List all registered webhooks."""
    hooks = _load_webhooks()
    total = sum(len(v.get("endpoints", [])) for v in hooks.values())
    return jsonify({
        "success": True,
        "total_webhooks": total,
        "webhooks": hooks
    })


@webhooks.route("/test", methods=["POST"])
def test_webhook():
    """
    Send a test notification to verify webhook is working.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "url": "https://hooks.slack.com/services/xxx"
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "test-bot")
    url = data.get("url", "").strip()
    
    if not url:
        return jsonify({"error": "url is required"}), 400
    
    # Send test payload
    payload = {
        "event": "test",
        "bot_id": bot_id,
        "message": "🧪 This is a test notification from TBN Protocol",
        "details": {"test": True},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "TBN Protocol"
    }
    
    try:
        r = http_requests.post(url, json=payload, timeout=5)
        return jsonify({
            "success": True,
            "status_code": r.status_code,
            "message": "Test webhook sent successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to send test webhook"
        }), 500


@webhooks.route("/deliveries", methods=["GET"])
def delivery_log():
    """Get recent webhook delivery log."""
    logs = []
    if os.path.exists(DELIVERY_LOG_FILE):
        with open(DELIVERY_LOG_FILE, "r") as f:
            logs = json.load(f)
    
    return jsonify({
        "success": True,
        "total": len(logs),
        "deliveries": logs[-20:]  # Last 20
    })


@webhooks.route("/remove", methods=["POST"])
def remove_webhook():
    """
    Remove a webhook endpoint.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx" or "_global",
        "url": "https://hooks.slack.com/services/xxx"
    }
    """
    data = request.get_json()
    bot_id = data.get("bot_id", "").strip()
    url = data.get("url", "").strip()
    
    if not bot_id or not url:
        return jsonify({"error": "bot_id and url are required"}), 400
    
    hooks = _load_webhooks()
    if bot_id in hooks:
        hooks[bot_id]["endpoints"] = [
            h for h in hooks[bot_id].get("endpoints", [])
            if h.get("url") != url
        ]
        _save_webhooks(hooks)
    
    return jsonify({
        "success": True,
        "message": f"Webhook removed for {bot_id}"
    })
