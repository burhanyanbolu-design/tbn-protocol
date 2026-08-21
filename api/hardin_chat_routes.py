"""
Hardin Chat — Flask routes
===========================
Page: GET  /chat                       -- the chat UI
API:  POST /v1/chat/message            -- one governed turn
      GET  /v1/chat/receipt/<id>       -- verify a receipt (public, no key)

Auth follows the same pattern as the rest of Hardin Memory's tenant API:
Authorization: Bearer <api_key>  or  X-API-Key: <api_key>. Get a trial key
the same way as TBN/Memory: POST /api/access/request (TBN) or the existing
memory signup flow -- Hardin Chat is a new surface on the same account
system, not a separate signup.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
from flask import Blueprint, jsonify, request, render_template

hardin_chat_bp = Blueprint("hardin_chat", __name__)


def _chat_tenant():
    """Resolve the calling tenant from the request's API key, or None.
    Mirrors health_agent.py's _mem_tenant() -- same account system."""
    try:
        from . import memory_service as ms
    except Exception:
        from api import memory_service as ms
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        key = auth[7:].strip()
    else:
        key = request.headers.get("X-API-Key", "").strip()
    return ms.authenticate(key)


@hardin_chat_bp.route("/chat")
def chat_page():
    """The Hardin Chat UI."""
    return render_template("hardin_chat.html")


@hardin_chat_bp.route("/v1/chat/message", methods=["POST"])
def chat_message():
    """One governed chat turn. Requires a tenant API key."""
    tenant = _chat_tenant()
    if not tenant:
        return jsonify({"error": "invalid or missing API key",
                        "signup": "https://tbn.hardinai.co.uk/pricing"}), 401

    body = request.get_json(silent=True) or {}
    question = (body.get("message") or "").strip()
    conversation_id = (body.get("conversation_id") or "default").strip()
    if not question:
        return jsonify({"error": "field 'message' is required"}), 400
    if len(question) > 4000:
        return jsonify({"error": "message too long (max 4000 characters)"}), 400

    try:
        from .hardin_chat_engine import hardin_chat_turn
    except Exception:
        from api.hardin_chat_engine import hardin_chat_turn

    try:
        result = hardin_chat_turn(tenant["tenant_id"], conversation_id, question)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": "chat turn failed", "detail": str(exc)[:200]}), 500

    return jsonify(result)


@hardin_chat_bp.route("/v1/chat/verify", methods=["POST"])
def chat_verify_receipt():
    """Zero-trust receipt verification. No API key required -- recomputes
    the hash and checks the signature, same guarantee as the GAR verify
    endpoint. POST the full receipt object (returned inline by
    /v1/chat/message) as {"receipt": {...}}."""
    try:
        from . import hardin_filter_receipt as hfr
    except Exception:
        from api import hardin_filter_receipt as hfr

    body = request.get_json(silent=True) or {}
    receipt = body.get("receipt")
    if not receipt:
        return jsonify({"error": "POST the receipt object as {'receipt': {...}}"}), 400
    result = hfr.verify_filter_receipt(receipt)
    return jsonify(result)
