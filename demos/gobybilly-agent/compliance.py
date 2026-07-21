"""
GoByBilly Agent — TBN Governance Layer
========================================
Every chat turn produces a signed TBN receipt: what the customer asked,
what the model was told (system prompt hash, not full text — no need to
re-publish the prompt on every receipt), what it replied, and whether the
reply stayed within the agent's declared scope (Go By Billy only).

Uses TBN's real production signing key (data/tbn_signing_key.pem, the
same key api/tbn_signing.py already loads) — this is a real signed
receipt, not a mock. Receipts are appended to a local append-only log
for this agent (data/gobybilly_receipts.jsonl) so the trail is
independently inspectable.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import os
import sys
import json
import uuid
import hashlib
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

# Make TBN's api/ (and its data/ keys) importable/reachable. Defaults assume
# this demo lives at <repo>/demos/gobybilly-agent (local dev layout); override
# TBN_API_DIR / TBN_DATA_DIR when deployed elsewhere (e.g. /opt/tbn-protocol
# on the server — see deploy/gobybilly.env).
_DEFAULT_API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "api"))
_DEFAULT_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
_API_DIR = os.environ.get("TBN_API_DIR", _DEFAULT_API_DIR)
_DATA_DIR = os.environ.get("TBN_DATA_DIR", _DEFAULT_DATA_DIR)
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

RECEIPTS_LOG = os.path.join(_DATA_DIR, "gobybilly_receipts.jsonl")

AGENT_ID = "gobybilly-customer-agent-v1"
AGENT_SCOPE = ["chauffeur_service_info", "coverage_area_info", "booking_redirect"]

# Phrases that would indicate the model claimed to have DONE something
# real (booked, charged, confirmed) rather than just informing/redirecting.
# The agent has no real booking/payment tool — any such claim is a scope
# violation and gets flagged in the receipt, same principle as
# api/verified_execution.py's claim-vs-real-tool-result check elsewhere
# in this repo.
_OVERCLAIM_MARKERS = [
    "i have booked", "i've booked", "your booking is confirmed",
    "i have charged", "i've charged", "payment has been taken",
    "i have scheduled", "i've scheduled your",
]


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _check_scope(reply_text: str) -> dict:
    """Fail-closed style scope check: did the reply claim a real action this
    agent cannot actually perform?"""
    low = (reply_text or "").lower()
    hit = next((m for m in _OVERCLAIM_MARKERS if m in low), None)
    if hit:
        return {"in_scope": False, "reason": f"reply claimed a real action ('{hit}') this agent cannot perform"}
    return {"in_scope": True, "reason": None}


# Safe fallback shown to the customer when a reply is blocked for overstepping
# scope. Never fabricates an outcome — always redirects to a human.
SAFE_FALLBACK_REPLY = (
    "I can help with pricing, coverage, and how to book, but I'm not able to "
    "confirm or process an actual booking myself. Please call or WhatsApp "
    "+44 790 1756 001 to complete your booking with our team."
)

# ── Alerting on blocked turns ────────────────────────────────────────────
# The receipt log used to be passive: a scope violation was recorded but
# nothing told anyone it happened. This closes that gap with the same
# real IONOS SMTP path api/webhooks.py already uses (same credential,
# no new secret needed) — if a turn gets blocked, someone finds out the
# same day, not only if they happen to go read the .jsonl log.
ALERT_EMAIL_TO = os.environ.get("GOBYBILLY_ALERT_EMAIL", "burhan@hardinai.co.uk")
ALERT_EMAIL_FROM = os.environ.get("GOBYBILLY_ALERT_EMAIL_FROM", "burhan@hardinai.co.uk")


def _send_block_alert(receipt: dict) -> bool:
    """Best-effort email alert when a turn is blocked (scope violation).
    Never raises — an alerting failure must not affect the chat response
    or the receipt that's already been signed and persisted. Returns True
    if the email was actually sent, False otherwise (including when SMTP
    isn't configured — that gap is logged honestly, not hidden)."""
    ionos_pass = os.environ.get("IONOS_PASS", "")
    subject = f"[GoByBilly] Blocked reply — session {receipt.get('session_id')}"
    body = (
        f"A GoByBilly agent reply was blocked by the TBN scope check "
        f"(fail-closed — the customer was shown the safe fallback, not the "
        f"model's original text).\n\n"
        f"Receipt ID:   {receipt.get('receipt_id')}\n"
        f"Session:      {receipt.get('session_id')}\n"
        f"Timestamp:    {receipt.get('timestamp')}\n"
        f"Model:        {receipt.get('model')}\n"
        f"Reason:       {receipt.get('scope_check', {}).get('reason')}\n\n"
        f"Read back the full receipt (input/output hashes, signature) at:\n"
        f"  https://gobybilly.co.uk/ai-chat/receipts/{receipt.get('session_id')}\n"
    )
    if not ionos_pass:
        print(f"[gobybilly-alert] IONOS_PASS not set; would have emailed "
              f"{ALERT_EMAIL_TO}: {subject}")
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = ALERT_EMAIL_FROM
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP_SSL("smtp.ionos.co.uk", 465, timeout=10) as server:
            server.login(ALERT_EMAIL_FROM, ionos_pass)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_string())
        print(f"[gobybilly-alert] sent to {ALERT_EMAIL_TO}: {subject}")
        return True
    except Exception as e:
        # Never let an alerting failure surface to the customer or caller —
        # the receipt is already signed and persisted regardless.
        print(f"[gobybilly-alert] FAILED to {ALERT_EMAIL_TO}: {e}")
        return False


def issue_turn_receipt(session_id: str, system_prompt: str, user_message: str,
                        reply_text: str, model_meta: dict) -> dict:
    """
    Build, sign, and persist a receipt for one chat turn.

    Fail-closed enforcement: if the scope check flags the model's reply as
    claiming a real action it cannot perform, the receipt's "delivered_reply"
    is the safe fallback, NOT the model's original text — the caller
    (server.py) sends delivered_reply to the customer, never the flagged
    original. The model's actual original reply is still hashed and recorded
    (output_hash) for audit, so nothing is hidden, but nothing false reaches
    the customer either.

    Returns the full signed receipt dict, plus "delivered_reply" (what the
    customer should actually be shown).
    """
    from tbn_signing import sign_response

    scope_check = _check_scope(reply_text)
    blocked = not scope_check["in_scope"]
    delivered_reply = SAFE_FALLBACK_REPLY if blocked else reply_text

    body = {
        "receipt_id": "gbb_" + uuid.uuid4().hex,
        "agent_id": AGENT_ID,
        "product": "gobybilly-customer-agent",
        "governed_by": "TBN Protocol",
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model_meta.get("model", ""),
        "system_prompt_hash": _sha256_hex(system_prompt.encode("utf-8")),
        "input_hash": _sha256_hex(user_message.encode("utf-8")),
        "output_hash": _sha256_hex((reply_text or "").encode("utf-8")),
        "scope_declared": AGENT_SCOPE,
        "scope_check": scope_check,
        "blocked": blocked,
        "delivered_hash": _sha256_hex(delivered_reply.encode("utf-8")),
        "model_error": model_meta.get("error"),
        "token_usage": model_meta.get("usage"),
        "signature_algorithm": "RSA-PSS-SHA256",
        "public_key_endpoint": "https://tbn.hardinai.co.uk/api/signing/public-key",
    }
    # Sign over every field above EXCEPT the signature itself (which doesn't
    # exist yet). Any field added after this point would not be covered by
    # the signature, so nothing else may be added to the receipt below.
    body["signature"] = sign_response(body)

    _append_receipt(body)
    if blocked:
        # Fires only after the receipt is signed and persisted — an alert
        # failure must never affect the record itself, only whether
        # someone finds out about it sooner.
        _send_block_alert(body)
    body["delivered_reply"] = delivered_reply
    return body


def _append_receipt(receipt: dict):
    try:
        os.makedirs(os.path.dirname(RECEIPTS_LOG), exist_ok=True)
        with open(RECEIPTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt) + "\n")
    except Exception:
        pass  # governance logging must never break the chat response itself


def verify_turn_receipt(receipt: dict) -> dict:
    """Standalone verification — recompute signature validity for a receipt.
    "delivered_reply" is added to the dict AFTER signing (see
    issue_turn_receipt) purely for the caller's convenience, so it must be
    excluded here along with "signature" itself when recomputing."""
    from tbn_signing import verify_signature
    body = {k: v for k, v in receipt.items() if k not in ("signature", "delivered_reply")}
    sig = receipt.get("signature", "")
    return {"signature_valid": verify_signature(body, sig)}
