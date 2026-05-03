"""
TBN Protocol — API Server
Runs the Flask API + live dashboard.

Usage:
    python server.py

Then open: http://localhost:5000
API docs:  http://localhost:5000/api/bots
"""

from flask import Flask, render_template, send_from_directory
from api.routes import api
import os

app = Flask(__name__, template_folder="api/templates")
app.register_blueprint(api, url_prefix="/api")


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — API Server")
    print("  Dashboard : http://localhost:5000")
    print("  API       : http://localhost:5000/api/bots")
    print("=" * 60 + "\n")
    app.run(debug=False, port=5000)
