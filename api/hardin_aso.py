"""
Hardin Agent Security Operations (HASO) — Landing Page + Enquiry Capture
=========================================================================
Public landing page for Hardin Agent Security Operations — the agent
governance & security platform for companies running their own AI agents,
built on TBN Protocol. Enterprise / mid-size buyers, so no self-serve
pricing: they submit an enquiry and Burhan follows up directly.

Routes:
  GET  /agent-security                      public landing page
  POST /api/agent-security/enquiry          public: submit an enquiry
  GET  /agent-security/enquiries?key=...    admin: view captured enquiries

Storage: data/haso_enquiries.json (same pattern as prospects.py)
Notification: emails burhan@hardinai.co.uk via IONOS SMTP on each enquiry
(same pattern as article50_checkout.py).

NOTE ON ACCESS CONTROL: the enquiry POST is intentionally unauthenticated —
it's a public contact form, which is expected for a sales landing page. It is
therefore abuse-exposed by design, so it carries: a honeypot field, field
length caps, and a per-IP daily submission cap (file-backed, so it holds
across gunicorn workers). The admin view IS gated by TBN_ADMIN_SECRET.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import os
import json
import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, render_template

hardin_aso = Blueprint("hardin_aso", __name__)

ENQUIRIES_FILE = "data/haso_enquiries.json"

# Abuse limits for the public, unauthenticated enquiry form
MAX_FIELD_LEN = 500
MAX_MESSAGE_LEN = 2000
MAX_PER_IP_PER_DAY = 5


def _load() -> dict:
    if os.path.exists(ENQUIRIES_FILE):
        try:
            with open(ENQUIRIES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"enquiries": []}


def _save(data: dict):
    os.makedirs(os.path.dirname(ENQUIRIES_FILE) or "data", exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(ENQUIRIES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _client_ip() -> str:
    """Best-effort client IP. Behind nginx, X-Forwarded-For holds the real one."""
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _recent_count_for_ip(data: dict, ip: str) -> int:
    """How many enquiries this IP submitted in the last 24h."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    count = 0
    for e in data.get("enquiries", []):
        if e.get("ip") != ip:
            continue
        try:
            ts = datetime.fromisoformat(e.get("submitted_at", ""))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            count += 1
    return count


def _notify(enquiry: dict) -> bool:
    """Email the enquiry to Burhan so it isn't only sitting in a JSON file."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        def esc(s):
            return (str(s or "")
                    .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e1a;color:#e0e6ed;padding:32px;border-radius:14px">
          <h2 style="color:#4fd1c5;margin:0 0 4px;font-size:20px">New HASO enquiry</h2>
          <p style="color:#8da3bd;margin:0 0 22px;font-size:13px">{esc(enquiry.get('submitted_at'))}</p>
          <div style="background:#111722;border:1px solid #2d3748;border-radius:12px;padding:20px">
            <p style="margin:0 0 8px"><b>Name:</b> {esc(enquiry.get('name'))}</p>
            <p style="margin:0 0 8px"><b>Company:</b> {esc(enquiry.get('company'))}</p>
            <p style="margin:0 0 8px"><b>Email:</b> {esc(enquiry.get('email'))}</p>
            <p style="margin:0 0 8px"><b>Company size:</b> {esc(enquiry.get('company_size'))}</p>
            <p style="margin:0 0 8px"><b>Agents in use:</b> {esc(enquiry.get('agents_context'))}</p>
            <p style="margin:16px 0 4px"><b>Message:</b></p>
            <p style="margin:0;color:#cbd5e0;white-space:pre-wrap">{esc(enquiry.get('message'))}</p>
          </div>
          <p style="color:#5f7488;font-size:11px;margin-top:18px">Ref {esc(enquiry.get('id'))} &middot; Hardin Agent Security Operations</p>
        </div>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"HASO enquiry — {enquiry.get('company') or enquiry.get('email')}"
        msg["From"] = "burhan@hardinai.co.uk"
        msg["To"] = "burhan@hardinai.co.uk"
        if enquiry.get("email"):
            msg["Reply-To"] = enquiry["email"]
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.ionos.co.uk", 465, timeout=12) as s:
            s.login("burhan@hardinai.co.uk", os.environ.get("IONOS_PASS", ""))
            s.sendmail("burhan@hardinai.co.uk", "burhan@hardinai.co.uk", msg.as_string())
        return True
    except Exception as e:
        # Never fail the user's submission because email broke — it's already saved.
        print(f"[hardin_aso] enquiry notification email failed: {e}")
        return False


@hardin_aso.route("/agent-security", methods=["GET"])
def landing():
    """Public HASO (Hardin Agent Security Operations) landing page."""
    return render_template("hardin_aso.html")


@hardin_aso.route("/api/agent-security/enquiry", methods=["POST"])
def submit_enquiry():
    """
    Public enquiry submission. Saves the lead and emails Burhan.
    Returns a generic success message (no enumeration, no internal detail).
    """
    body = request.get_json(silent=True) or request.form or {}

    # Honeypot: a hidden field real users never fill in. Bots usually do.
    if (body.get("website_url") or "").strip():
        # Pretend success so the bot doesn't retry with a different shape.
        return jsonify({"ok": True, "message": "Thanks — we'll be in touch shortly."})

    name = (body.get("name") or "").strip()[:MAX_FIELD_LEN]
    company = (body.get("company") or "").strip()[:MAX_FIELD_LEN]
    email = (body.get("email") or "").strip().lower()[:MAX_FIELD_LEN]
    company_size = (body.get("company_size") or "").strip()[:MAX_FIELD_LEN]
    agents_context = (body.get("agents_context") or "").strip()[:MAX_FIELD_LEN]
    message = (body.get("message") or "").strip()[:MAX_MESSAGE_LEN]

    if not name or not company or not email or "@" not in email:
        return jsonify({
            "ok": False,
            "error": "Please provide your name, company, and a valid work email."
        }), 400

    data = _load()

    ip = _client_ip()
    if _recent_count_for_ip(data, ip) >= MAX_PER_IP_PER_DAY:
        return jsonify({
            "ok": False,
            "error": "You've submitted several enquiries already. Email burhan@hardinai.co.uk directly and we'll pick it up."
        }), 429

    enquiry = {
        "id": f"haso_{secrets.token_hex(8)}",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "company": company,
        "email": email,
        "company_size": company_size,
        "agents_context": agents_context,
        "message": message,
        "ip": ip,
        "status": "new",
    }

    data.setdefault("enquiries", []).insert(0, enquiry)
    _save(data)

    _notify(enquiry)

    return jsonify({
        "ok": True,
        "message": "Thanks — we'll be in touch shortly.",
        "reference": enquiry["id"],
    })


@hardin_aso.route("/agent-security/enquiries", methods=["GET"])
def list_enquiries():
    """Admin-only: view captured enquiries. Gated by TBN_ADMIN_SECRET."""
    admin_key = request.args.get("key", "")
    expected = os.environ.get("TBN_ADMIN_SECRET", "")
    if not expected or admin_key != expected:
        return "Not Found", 404

    data = _load()
    enquiries = data.get("enquiries", [])

    rows = "".join(
        f"<tr>"
        f"<td>{e.get('submitted_at','')[:19].replace('T',' ')}</td>"
        f"<td><b>{e.get('company','')}</b></td>"
        f"<td>{e.get('name','')}</td>"
        f"<td><a href=\"mailto:{e.get('email','')}\">{e.get('email','')}</a></td>"
        f"<td>{e.get('company_size','')}</td>"
        f"<td>{e.get('agents_context','')}</td>"
        f"<td style=\"max-width:320px\">{e.get('message','')}</td>"
        f"</tr>"
        for e in enquiries
    )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>HASO enquiries ({len(enquiries)})</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0a0e1a;color:#e0e6ed;padding:32px}}
h1{{font-size:20px;color:#4fd1c5}}
table{{border-collapse:collapse;width:100%;margin-top:20px;font-size:13px}}
th,td{{border:1px solid #2d3748;padding:9px 11px;text-align:left;vertical-align:top}}
th{{background:#111722;color:#8da3bd;font-size:11px;text-transform:uppercase;letter-spacing:1px}}
a{{color:#4fd1c5}}
</style></head><body>
<h1>Hardin Agent Security Operations — enquiries ({len(enquiries)})</h1>
<table><tr><th>When</th><th>Company</th><th>Name</th><th>Email</th><th>Size</th><th>Agents</th><th>Message</th></tr>{rows}</table>
</body></html>"""
