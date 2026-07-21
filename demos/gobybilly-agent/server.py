"""
GoByBilly Agent — Server
=========================
Real customer-facing chat agent for Go By Billy (VIP Chauffeur & Transfer,
Essex & London). Powered directly by OpenAI's API (not Azure), governed by
TBN Protocol — every turn produces a signed receipt.

Endpoints:
  GET  /                    — standalone demo page (widget embedded)
  POST /chat                — customer message -> agent reply + receipt
  GET  /health               — status
  GET  /receipts/<session>   — list receipts for a session (for spot-checks)

Sessions are in-memory, keyed by session id. No personal data persisted
beyond the receipt log (hashes only — no raw message content is stored
in the receipt itself, only in-memory for the session's own history).

Run: python server.py   (default port 5010)

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import os

from flask import Flask, request, jsonify, render_template

import config
import conversation
import compliance

# Explicit template_folder anchored to this file's own directory — the
# process's working directory is set to /opt/tbn-protocol in production
# (so compliance.py's relative signing-key paths resolve), which would
# otherwise break Flask's default "templates next to cwd" lookup.
_HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_HERE, "templates"))

_sessions = {}


def _get_session(sid):
    if sid not in _sessions:
        _sessions[sid] = {"history": []}
    return _sessions[sid]


@app.route("/")
def index():
    return render_template("widget_demo.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    sid = (data.get("session_id") or "default").strip()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"success": False, "error": "No message"}), 400

    sess = _get_session(sid)
    result = conversation.reply(message, sess)
    reply_text = result["reply"]
    model_meta = result["model_meta"]

    if not reply_text:
        # Model call failed — never fabricate a reply, return the real error.
        return jsonify({
            "success": False,
            "error": model_meta.get("error", "model_unavailable"),
        }), 502

    receipt = compliance.issue_turn_receipt(
        session_id=sid,
        system_prompt=conversation.build_system_prompt(),
        user_message=message,
        reply_text=reply_text,
        model_meta=model_meta,
    )

    # Fail-closed: if the scope check flagged the model's reply, the customer
    # sees the safe fallback (delivered_reply), never the flagged original —
    # the original is still hashed/recorded in the receipt for audit.
    return jsonify({
        "success": True,
        "reply": receipt["delivered_reply"],
        "receipt_id": receipt["receipt_id"],
        "scope_check": receipt["scope_check"],
        "blocked": receipt["blocked"],
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "service": "gobybilly-customer-agent",
        "model_provider": "openai",
        "model": config.OPENAI_MODEL,
        "openai_configured": bool(config.OPENAI_API_KEY),
        "governed_by": "TBN Protocol",
    })


@app.route("/receipts/<session_id>", methods=["GET"])
def list_receipts(session_id):
    """Read back this session's receipts from the append-only log — lets
    anyone spot-check that governance actually ran, not just trust the /chat
    response."""
    import os
    import json
    out = []
    if os.path.exists(compliance.RECEIPTS_LOG):
        with open(compliance.RECEIPTS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("session_id") == session_id:
                    out.append(r)
    return jsonify({"success": True, "session_id": session_id, "receipts": out})


if __name__ == "__main__":
    print(f"\nGo By Billy Agent running on http://localhost:{config.GOBYBILLY_PORT}")
    print(f"  OpenAI configured: {bool(config.OPENAI_API_KEY)} | model: {config.OPENAI_MODEL}")
    print(f"  Governed by: TBN Protocol (signed receipt per turn)\n")
    app.run(host="0.0.0.0", port=config.GOBYBILLY_PORT, debug=False, use_reloader=False)
