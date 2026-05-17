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
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from api.routes import api
from api.certification import certification
from api.governance import governance
from api.billing import billing
from api.governance_engine import governance_engine
from api.security_challenge import security_challenge
from api.budget_enforcement import budget_enforcement
from api.webhooks import webhooks
from api.compliance_drift import compliance_drift

# ── App setup ────────────────────────────────────────
app = Flask(__name__, template_folder="api/templates", static_folder="api/static")
app.register_blueprint(api,                url_prefix="/api")
app.register_blueprint(certification,      url_prefix="/certification")
app.register_blueprint(governance,         url_prefix="/governance")
app.register_blueprint(billing,            url_prefix="/api/billing")
app.register_blueprint(governance_engine,  url_prefix="/api/govern")
app.register_blueprint(security_challenge, url_prefix="/api/security-challenge")
app.register_blueprint(budget_enforcement, url_prefix="/api/budget")
app.register_blueprint(webhooks, url_prefix="/api/webhooks")
app.register_blueprint(compliance_drift, url_prefix="/api/compliance")

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


@app.route("/demo")
def demo_page():
    return render_template("demo.html")


@app.route("/early-access")
def early_access_page():
    return render_template("early_access.html")


@app.route("/api/early-access", methods=["POST"])
def early_access_submit():
    """Store early access signups."""
    import json
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    
    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400
    
    signup = {
        "name": name,
        "email": email,
        "company": data.get("company", ""),
        "agents": data.get("agents", ""),
        "concern": data.get("concern", ""),
        "notes": data.get("notes", ""),
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
    return render_template("demo.html")


@app.route("/demo/nhs")
def demo_nhs():
    return render_template("demo_nhs.html")


@app.route("/philosophy")
def philosophy():
    return render_template("philosophy_chat.html")


@app.route("/partners")
def partners_page():
    return render_template("partner_register.html")


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
