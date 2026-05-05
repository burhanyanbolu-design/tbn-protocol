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
from flask import Flask, render_template
from api.routes import api
from api.certification import certification
from api.governance import governance

# ── App setup ────────────────────────────────────────
app = Flask(__name__, template_folder="api/templates")
app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(certification, url_prefix="/certification")
app.register_blueprint(governance, url_prefix="/governance")

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
    return render_template("dashboard.html")


@app.route("/register")
def register_page():
    return render_template("register_bot.html")


@app.route("/admin/violations")
def violations_dashboard():
    return render_template("violations_dashboard.html")


@app.route("/demo")
def demo():
    return render_template("demo.html")


@app.route("/demo/nhs")
def demo_nhs():
    return render_template("demo_nhs.html")


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
