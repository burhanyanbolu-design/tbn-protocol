# TBN Protocol — Trusted Bot Network
# Copyright (C) 2026 Burhan Yanbolu / Hardin Enterprises Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# For commercial licensing inquiries, contact: burhan@hardinai.co.uk

"""
TBN Protocol — API Server
Runs the Flask API + live dashboard.

Development:
    python server.py
    Open: http://localhost:5000

Production (via gunicorn — started by systemd):
    gunicorn --workers 4 --bind 127.0.0.1:5000 "server:app"
"""

import os
import logging
import hashlib
import secrets
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from api.routes import api
from api.certification import certification
from api.governance import governance
from api.billing import billing
from api.governance_engine import governance_engine
from api.security_challenge import security_challenge
from api.budget_enforcement import budget_enforcement
from api.webhooks import webhooks
from api.compliance_drift import compliance_drift
from api.prospects import prospects_bp
from api.digiemu_interop import digiemu_bp
from api.hardin_aso import hardin_aso
# HASO (Hardin Agent Security Operations) — enquiry-only landing page for the
# agent governance/security product built on TBN Protocol, for companies
# running their own AI agents. No self-serve pricing: every company's agent
# estate is different, so it's scoped per engagement after a conversation,
# not sold as a fixed-price tier (same reasoning as pqc_scanner).

# ── App setup ────────────────────────────────────────
app = Flask(__name__, template_folder="api/templates", static_folder="api/static")
app.secret_key = os.environ.get("TBN_SECRET_KEY", secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max upload

# ── Customer auth ────────────────────────────────────
CUSTOMER_PASSWORD = os.environ.get("TBN_CUSTOMER_PASSWORD", "tbn-customer-2026")


def customer_login_required(f):
    """Decorator to require customer login for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("customer_authenticated"):
            return redirect(url_for("customer_login", next=request.path))
        return f(*args, **kwargs)
    return decorated
app.register_blueprint(api,                url_prefix="/api")
app.register_blueprint(certification,      url_prefix="/certification")
app.register_blueprint(governance,         url_prefix="/governance")
app.register_blueprint(billing,            url_prefix="/api/billing")
app.register_blueprint(governance_engine,  url_prefix="/api/govern")
app.register_blueprint(security_challenge, url_prefix="/api/security-challenge")
app.register_blueprint(budget_enforcement, url_prefix="/api/budget")
app.register_blueprint(webhooks, url_prefix="/api/webhooks")
app.register_blueprint(compliance_drift, url_prefix="/api/compliance")
app.register_blueprint(prospects_bp)
app.register_blueprint(digiemu_bp, url_prefix="/api/digiemu")
app.register_blueprint(hardin_aso)

# ── Logging ──────────────────────────────────────────
is_production = os.environ.get("TBN_ENV") == "production"

if is_production:
    logging.basicConfig(level=logging.INFO)
    # Create log directory if needed
    os.makedirs("/var/log/tbn", exist_ok=True)
else:
    logging.basicConfig(level=logging.DEBUG)


# ── Routes ───────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template("dashboard_new.html")


@app.route("/assess")
def assess_page():
    """AI Governance Readiness Assessment — public lead-gen tool."""
    return render_template("assess.html")


@app.route("/video-agent")
def video_agent_page():
    """Video Agent Dashboard — governed video intelligence."""
    return render_template("video_agent.html")


@app.route("/api/video-agent/process", methods=["POST"])
def video_agent_process():
    """Process a video through the TBN Video Agent."""
    import tempfile, subprocess, base64, uuid, hashlib
    import json as json_mod
    import google.generativeai as genai
    
    GEMINI_KEY = "AIzaSyAmM_DYDI1riSrHuOaQJNu-6ZKDze40of8"
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    if 'video' not in request.files:
        # Check for URL or demo mode
        url = request.form.get('url', '')
        if url == 'DEMO':
            video_path = '/opt/video-agent/demo.MOV'
            if not os.path.exists(video_path):
                return jsonify({"success": False, "error": "Demo video not found on server"})
            tmp_dir = tempfile.mkdtemp()
        elif url:
            # Download from URL
            tmp_dir = tempfile.mkdtemp()
            video_path = os.path.join(tmp_dir, "download.mp4")
            try:
                import urllib.request
                urllib.request.urlretrieve(url, video_path)
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to download: {str(e)}"})
        else:
            return jsonify({"success": False, "error": "No video file or URL provided"})
    else:
        video = request.files['video']
        tmp_dir = tempfile.mkdtemp()
        video_path = os.path.join(tmp_dir, "upload.mp4")
        video.save(video_path)
    
    mode = request.form.get('mode', 'observe')
    task = request.form.get('task', 'Describe what is happening in this video')
    
    # Extract frames
    frames = []
    transcript = ""
    try:
        import json as json_mod
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", video_path],
            capture_output=True, text=True, timeout=10
        )
        duration = float(json_mod.loads(probe.stdout)["format"]["duration"])
        interval = max(1, duration / 10)
        
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vf", f"fps=1/{interval:.1f}",
            "-frames:v", "10", "-q:v", "2",
            os.path.join(tmp_dir, "frame_%03d.jpg"), "-y"
        ], capture_output=True, timeout=30)
        
        # Extract audio for transcription
        audio_path = os.path.join(tmp_dir, "audio.mp3")
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame",
            "-q:a", "5", audio_path, "-y"
        ], capture_output=True, timeout=30)
        
        # Transcribe audio using Gemini
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            try:
                with open(audio_path, "rb") as af:
                    audio_data = base64.b64encode(af.read()).decode()
                audio_response = model.generate_content([
                    "Transcribe this audio. Return ONLY the spoken words, nothing else.",
                    {"mime_type": "audio/mp3", "data": audio_data}
                ])
                transcript = audio_response.text.strip()
            except Exception as e:
                transcript = f"(Audio transcription failed: {str(e)[:50]})"
        
        for f in sorted(os.listdir(tmp_dir)):
            if f.endswith(".jpg"):
                with open(os.path.join(tmp_dir, f), "rb") as img:
                    frames.append(base64.b64encode(img.read()).decode())
    except Exception as e:
        return jsonify({"success": False, "error": f"Frame extraction failed: {str(e)}"})
    
    # Send to Gemini
    try:
        prompt = f"""You are a video analysis agent operating in {mode.upper()} mode.
Task: {task}

AUDIO TRANSCRIPT OF THE VIDEO:
{transcript if transcript else "(No audio detected or transcription unavailable)"}

Analyse both the visual frames AND the audio transcript above to provide a complete understanding.

Also assess AUTHENTICITY:
- Do the lip movements appear to match the audio? (lip-sync check)
- Does the audio sound natural or AI-generated?
- Are there signs of video manipulation, deepfake, or dubbing?
- Confidence that this is an authentic, unmanipulated video?

Respond in JSON format:
{{"summary": "...", "events": ["..."], "objects": ["..."], "context": "...", "risks": ["..."], "recommended_action": "...", "confidence": 0.0-1.0, "transcript_summary": "...", "authenticity": {{"lip_sync_match": true/false, "audio_natural": true/false, "deepfake_indicators": "none/low/medium/high", "authenticity_confidence": 0.0-1.0, "notes": "..."}}}}"""
        
        parts = [prompt]
        for frame_data in frames[:8]:
            parts.append({"mime_type": "image/jpeg", "data": frame_data})
        
        response = model.generate_content(parts)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        understanding = json_mod.loads(text)
    except Exception as e:
        understanding = {"summary": f"Analysis error: {str(e)}", "events": [], "objects": [], "context": "", "risks": [], "recommended_action": "retry", "confidence": 0.5}
    
    # TBN Governance
    receipt_id = f"tbn_vr_{uuid.uuid4().hex[:12]}"
    confidence = understanding.get("confidence", 0.5)
    risks = understanding.get("risks", [])
    risk_score = 30 if not risks or risks == ["No visible safety, compliance, or governance concerns are present in these frames. The scene appears to be benign and private."] else 60 if len(risks) <= 2 else 85
    
    decision = "ALLOWED" if risk_score < 90 else "BLOCKED"
    decision_data = json_mod.dumps({"agent": "video-agent-001", "action": mode, "risk": risk_score}, sort_keys=True)
    decision_hash = f"sha256:{hashlib.sha256(decision_data.encode()).hexdigest()}"
    
    receipt = {
        "receipt_id": receipt_id,
        "agent_id": "video-agent-001",
        "decision": decision,
        "risk_score": risk_score,
        "confidence": confidence,
        "decision_hash": decision_hash,
        "governed_by": "TBN Protocol v0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return jsonify({
        "success": True,
        "understanding": understanding,
        "receipt": receipt,
        "frames_extracted": len(frames),
        "mode": mode
    })


@app.route("/api/assess/save", methods=["POST"])
def assess_save():
    """Save assessment results."""
    data = request.get_json() or {}
    # Store in a simple JSON file
    import json
    results_file = "data/assessments.json"
    os.makedirs("data", exist_ok=True)
    try:
        with open(results_file, "r") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = []
    results.append(data)
    with open(results_file, "w") as f:
        json.dump(results[-500:], f)  # Keep last 500
    return jsonify({"saved": True})


@app.route("/api/assess/lead", methods=["POST"])
def assess_lead():
    """Capture lead from assessment and email to Burhan."""
    data = request.get_json() or {}
    name = data.get("name", "")
    email = data.get("email", "")
    company = data.get("company", "")
    role = data.get("role", "")
    score = data.get("score", 0)
    level = data.get("level", "")
    gaps = data.get("gaps", 0)
    ref_id = data.get("ref_id", "")
    
    import json, smtplib
    from email.mime.text import MIMEText
    
    # Save lead locally
    leads_file = "data/assess_leads.json"
    os.makedirs("data", exist_ok=True)
    try:
        with open(leads_file, "r") as f:
            leads = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leads = []
    leads.append({
        "ref_id": ref_id,
        "name": name,
        "email": email,
        "company": company,
        "role": role,
        "score": score,
        "level": level,
        "gaps": gaps,
        "timestamp": data.get("timestamp", "")
    })
    with open(leads_file, "w") as f:
        json.dump(leads, f, indent=2)
    
    # Send email notification to Burhan
    try:
        subject = f"[TBN LEAD] {company} - {name} ({role}) - Score: {score}/100"
        body = f"""New AI Governance Assessment Lead

Reference: {ref_id}
Name: {name}
Email: {email}
Company: {company}
Role: {role}

Assessment Results:
- Score: {score}/100
- Level: {level}
- Gaps Identified: {gaps}

Timestamp: {data.get('timestamp', '')}

---
Follow up at: {email}
Assessment tool: https://tbn.hardinai.co.uk/assess
"""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "noreply@hardinai.co.uk"
        msg["To"] = "burhan@hardinai.co.uk"
        
        smtp = smtplib.SMTP("localhost", 25)
        smtp.send_message(msg)
        smtp.quit()
    except Exception as e:
        print(f"[Assess] Email send failed: {e}")
    
    return jsonify({"saved": True, "ref_id": ref_id})


@app.route("/demo")
def demo_page():
    return render_template("demo.html")


@app.route("/demo/hero")
def demo_hero():
    return render_template("tbn-hero-demo.html")


@app.route("/early-access")
def early_access_page():
    return render_template("early_access.html")


@app.route("/api/early-access", methods=["POST"])
def early_access_submit():
    """Store early access signups and notify Burhan."""
    import json
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    
    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400
    
    company = data.get("company", "")
    agents = data.get("agents", "")
    concern = data.get("concern", "")
    notes = data.get("notes", "")
    
    signup = {
        "name": name,
        "email": email,
        "company": company,
        "agents": agents,
        "concern": concern,
        "notes": notes,
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to file
    signups_file = "data/early_access_signups.json"
    signups = []
    if os.path.exists(signups_file):
        with open(signups_file, "r") as f:
            signups = json.load(f)
    signups.append(signup)
    os.makedirs("data", exist_ok=True)
    with open(signups_file, "w") as f:
        json.dump(signups, f, indent=2)
    
    # Send email notification to Burhan
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = os.environ.get("TBN_SMTP_HOST", "")
        smtp_user = os.environ.get("TBN_SMTP_USER", "")
        smtp_pass = os.environ.get("TBN_SMTP_PASS", "")
        
        if smtp_host and smtp_user and smtp_pass:
            html_body = f"""
            <h2 style="color:#7c3aed">🚀 New Early Access Signup!</h2>
            <table style="font-family:monospace; font-size:14px; border-collapse:collapse;">
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Name:</td><td>{name}</td></tr>
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Email:</td><td>{email}</td></tr>
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Company:</td><td>{company or '—'}</td></tr>
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Agents:</td><td>{agents or '—'}</td></tr>
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Concern:</td><td>{concern or '—'}</td></tr>
                <tr><td style="padding:4px 12px 4px 0; font-weight:bold;">Notes:</td><td>{notes or '—'}</td></tr>
            </table>
            <p style="margin-top:16px; color:#71717a; font-size:12px;">
                Total signups: {len(signups)} | Reply to {email} within 48 hours.
            </p>
            """
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[TBN] 🚀 Early Access Signup: {name} ({company or 'No company'})"
            msg["From"] = f"TBN Protocol <{smtp_user}>"
            msg["To"] = "burhan@hardinai.co.uk"
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP_SSL(smtp_host, 465, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, "burhan@hardinai.co.uk", msg.as_string())
            print(f"[Early Access] ✅ Email sent for: {name} ({email})")
        else:
            print(f"[Early Access] ⚠️ SMTP not configured, skipping email for: {name}")
    except Exception as e:
        print(f"[Early Access] Email notification failed: {e}")
    
    return jsonify({"success": True, "message": f"Welcome {name}! You're on the early access list."})


@app.route("/admin")
def admin_dashboard():
    return render_template("dashboard.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/register")
def register_page():
    return render_template("register_bot.html")


@app.route("/admin/violations")
def violations_dashboard():
    return render_template("violations_dashboard.html")


@app.route("/demo/live")
def demo_live():
    return render_template("demo_live.html")


@app.route("/demo/nhs")
def demo_nhs():
    return render_template("demo_nhs.html")


@app.route("/demo/langchain")
def demo_langchain():
    return render_template("demo_langchain.html")


@app.route("/philosophy")
def philosophy():
    return render_template("philosophy_chat.html")


@app.route("/partners")
def partners_page():
    return render_template("partner_register.html")


@app.route("/verify")
def verify_page():
    return render_template("verify_public.html")


@app.route("/customer")
@customer_login_required
def customer_dashboard():
    return render_template("customer_dashboard.html")


@app.route("/customer/login", methods=["GET", "POST"])
def customer_login():
    """Login page for customer dashboard."""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == CUSTOMER_PASSWORD:
            session["customer_authenticated"] = True
            next_page = request.args.get("next", "/customer")
            return redirect(next_page)
        return render_template("customer_login.html", error="Invalid password")
    return render_template("customer_login.html", error=None)


@app.route("/customer/logout")
def customer_logout():
    """Logout from customer dashboard."""
    session.pop("customer_authenticated", None)
    return redirect(url_for("customer_login"))


@app.route("/chat")
def hardin_chatbot():
    return render_template("hardin_chatbot.html")


@app.route("/admin/partners")
def partner_monitor_page():
    # Require admin secret via query param: /admin/partners?key=hardin-admin-2026-secret
    admin_key = request.args.get("key", "")
    expected = os.environ.get("TBN_ADMIN_SECRET", "")
    if not expected or admin_key != expected:
        return "Not Found", 404
    return render_template("partner_monitor.html")


@app.route("/health")
def health():
    return {"status": "ok", "service": "tbn-protocol"}


# ── Dev server ───────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — API Server")
    print("  Dashboard : http://localhost:5000")
    print("  API       : http://localhost:5000/api/bots")
    print("  Guided Tour → click ▶ in the dashboard header")
    print("=" * 60 + "\n")
    app.run(debug=not is_production, port=5000, host="0.0.0.0")
