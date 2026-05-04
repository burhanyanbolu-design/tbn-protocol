"""
TBN Protocol — Email Notification System
Sends alerts for violations, certifications, and network events.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone


# Email configuration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("TBN_EMAIL_USER", "burhanyanbolu@gmail.com")
SMTP_PASS = os.environ.get("TBN_EMAIL_PASS", "")
NOTIFY_TO = os.environ.get("TBN_NOTIFY_EMAIL", "burhan@hardinai.co.uk")


def send_email(subject: str, html_body: str, text_body: str = None) -> bool:
    """Send an email notification."""
    try:
        if not SMTP_PASS:
            print(f"[Notify] ⚠️ No email password configured, skipping: {subject}")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TBN Protocol <{SMTP_USER}>"
        msg["To"] = NOTIFY_TO

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, NOTIFY_TO, msg.as_string())

        print(f"[Notify] ✅ Email sent: {subject}")
        return True

    except Exception as e:
        print(f"[Notify] ❌ Email failed: {e}")
        return False


def notify_violation(bot_id: str, bot_name: str, violation: str,
                     reporter: str, violation_count: int, revoked: bool) -> bool:
    """Send violation notification email."""

    status_color = "#f85149" if revoked else "#d29922"
    status_text = "🚨 BOT REVOKED" if revoked else f"⚠️ Violation #{violation_count}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Courier New',monospace;background:#0a0e1a;color:#c9d1d9;padding:20px;margin:0">
  <div style="max-width:600px;margin:0 auto">

    <div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:24px;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <div style="width:40px;height:40px;background:linear-gradient(135deg,#00d9ff,#0099cc);
                    clip-path:polygon(30% 0%,70% 0%,100% 50%,70% 100%,30% 100%,0% 50%);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:bold;font-size:20px;color:#0d1117">H</div>
        <div>
          <div style="font-size:14px;font-weight:bold;color:#fff;letter-spacing:1px">HARDIN AI SOLUTIONS</div>
          <div style="font-size:10px;color:#8b949e">TBN Protocol Alerts</div>
        </div>
      </div>

      <div style="background:{status_color}22;border:1px solid {status_color};
                  border-radius:6px;padding:16px;margin-bottom:20px;text-align:center">
        <div style="font-size:20px;font-weight:bold;color:{status_color}">{status_text}</div>
        <div style="font-size:12px;color:#8b949e;margin-top:4px">{timestamp}</div>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681;width:140px">Bot ID</td>
          <td style="padding:10px 0;color:#58a6ff">{bot_id}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Bot Name</td>
          <td style="padding:10px 0;color:#c9d1d9">{bot_name}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Violation</td>
          <td style="padding:10px 0;color:#f85149">{violation}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Reporter</td>
          <td style="padding:10px 0;color:#c9d1d9">{reporter}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Total Violations</td>
          <td style="padding:10px 0;color:{status_color}">{violation_count}</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:#6e7681">Status</td>
          <td style="padding:10px 0;color:{'#f85149' if revoked else '#3fb950'}">
            {'❌ REVOKED' if revoked else '✅ Still Active'}
          </td>
        </tr>
      </table>
    </div>

    <div style="text-align:center;margin-top:16px">
      <a href="https://tbn.hardinai.co.uk/admin/violations"
         style="background:#238636;color:#fff;padding:10px 20px;border-radius:6px;
                text-decoration:none;font-size:12px;font-weight:bold">
        View Violations Dashboard
      </a>
    </div>

    <div style="text-align:center;margin-top:20px;font-size:10px;color:#6e7681">
      TBN Protocol — Trusted Bot Network<br>
      © 2026 Hardin Enterprises Ltd
    </div>
  </div>
</body>
</html>
"""

    text = f"""
TBN PROTOCOL — VIOLATION ALERT
{status_text}
Time: {timestamp}

Bot ID: {bot_id}
Bot Name: {bot_name}
Violation: {violation}
Reporter: {reporter}
Total Violations: {violation_count}
Status: {'REVOKED' if revoked else 'Still Active'}

View dashboard: https://tbn.hardinai.co.uk/admin/violations
"""

    return send_email(
        subject=f"[TBN] {status_text} — {bot_name}",
        html_body=html,
        text_body=text
    )


def notify_certification(bot_id: str, bot_name: str, cert_level: str, purpose: str = "") -> bool:
    """Send certification notification email."""

    badges = {"COMMUNITY": "🟢", "STANDARD": "🔵", "RESTRICTED": "🟡"}
    colors = {"COMMUNITY": "#3fb950", "STANDARD": "#58a6ff", "RESTRICTED": "#d29922"}
    badge = badges.get(cert_level, "⚪")
    color = colors.get(cert_level, "#8b949e")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Courier New',monospace;background:#0a0e1a;color:#c9d1d9;padding:20px;margin:0">
  <div style="max-width:600px;margin:0 auto">
    <div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:24px">

      <div style="background:{color}22;border:1px solid {color};
                  border-radius:6px;padding:16px;margin-bottom:20px;text-align:center">
        <div style="font-size:24px">{badge}</div>
        <div style="font-size:18px;font-weight:bold;color:{color}">Bot Certified: {cert_level}</div>
        <div style="font-size:12px;color:#8b949e;margin-top:4px">{timestamp}</div>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681;width:140px">Bot ID</td>
          <td style="padding:10px 0;color:#58a6ff">{bot_id}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Bot Name</td>
          <td style="padding:10px 0;color:#c9d1d9">{bot_name}</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:#6e7681">Level</td>
          <td style="padding:10px 0;color:{color}">{badge} {cert_level}</td>
        </tr>
        {f'<tr><td style="padding:10px 0;color:#6e7681">Purpose</td><td style="padding:10px 0;color:#c9d1d9">{purpose}</td></tr>' if purpose else ''}
      </table>
    </div>

    <div style="text-align:center;margin-top:20px;font-size:10px;color:#6e7681">
      TBN Protocol — Trusted Bot Network<br>
      © 2026 Hardin Enterprises Ltd
    </div>
  </div>
</body>
</html>
"""

    return send_email(
        subject=f"[TBN] {badge} Bot Certified: {bot_name} — {cert_level}",
        html_body=html
    )


def notify_registration(bot_id: str, bot_name: str, bot_type: str) -> bool:
    """Send new bot registration notification."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Courier New',monospace;background:#0a0e1a;color:#c9d1d9;padding:20px;margin:0">
  <div style="max-width:600px;margin:0 auto">
    <div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:24px">
      <div style="background:#1a3a2a;border:1px solid #3fb950;border-radius:6px;
                  padding:16px;margin-bottom:20px;text-align:center">
        <div style="font-size:24px">🤖</div>
        <div style="font-size:18px;font-weight:bold;color:#3fb950">New Bot Registered</div>
        <div style="font-size:12px;color:#8b949e;margin-top:4px">{timestamp}</div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681;width:140px">Bot ID</td>
          <td style="padding:10px 0;color:#58a6ff">{bot_id}</td>
        </tr>
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:10px 0;color:#6e7681">Bot Name</td>
          <td style="padding:10px 0;color:#c9d1d9">{bot_name}</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:#6e7681">Type</td>
          <td style="padding:10px 0;color:#c9d1d9">{bot_type}</td>
        </tr>
      </table>
    </div>
    <div style="text-align:center;margin-top:20px;font-size:10px;color:#6e7681">
      TBN Protocol — © 2026 Hardin Enterprises Ltd
    </div>
  </div>
</body>
</html>
"""

    return send_email(
        subject=f"[TBN] 🤖 New Bot Registered: {bot_name}",
        html_body=html
    )
