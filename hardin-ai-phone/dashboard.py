"""
Hardin-AI Phone — Admin Dashboard
Simple Flask web app to view bookings and call logs.
Accessible at https://phone.hardinai.co.uk/dashboard
"""

from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Bookings file (shared with AGI server)
BOOKINGS_FILE = "/opt/hardin-ai-phone/bookings.json"


def load_bookings():
    """Load bookings from JSON file."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r") as f:
            return json.load(f)
    return []


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardin-AI Phone — Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1117;
            color: #e4e4e7;
            min-height: 100vh;
        }
        .header {
            background: #1a1b23;
            border-bottom: 1px solid #2a2b35;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { 
            font-size: 1.5rem;
            color: #c8ff00;
        }
        .header .status {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #4ade80;
            font-size: 0.9rem;
        }
        .header .status::before {
            content: '';
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
        }
        .stat-card {
            background: #1a1b23;
            border: 1px solid #2a2b35;
            border-radius: 12px;
            padding: 24px;
        }
        .stat-card .label {
            font-size: 0.85rem;
            color: #71717a;
            margin-bottom: 8px;
        }
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: #c8ff00;
        }
        .content { padding: 0 40px 40px; }
        .section-title {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: #e4e4e7;
        }
        .bookings-table {
            width: 100%;
            border-collapse: collapse;
            background: #1a1b23;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #2a2b35;
        }
        .bookings-table th {
            background: #22232d;
            padding: 14px 16px;
            text-align: left;
            font-size: 0.8rem;
            text-transform: uppercase;
            color: #71717a;
            letter-spacing: 0.5px;
        }
        .bookings-table td {
            padding: 14px 16px;
            border-top: 1px solid #2a2b35;
            font-size: 0.9rem;
        }
        .bookings-table tr:hover td {
            background: #22232d;
        }
        .ref {
            font-family: monospace;
            color: #c8ff00;
            font-weight: 600;
        }
        .empty {
            text-align: center;
            padding: 60px;
            color: #71717a;
        }
        .phone-number {
            background: #22232d;
            padding: 4px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
        }
        .refresh-btn {
            background: #c8ff00;
            color: #0f1117;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.85rem;
        }
        .refresh-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Hardin-AI Phone</h1>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div class="status">System Live</div>
            <span class="phone-number">+44 20 4577 2353</span>
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
        </div>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="label">Total Bookings</div>
            <div class="value">{{ bookings|length }}</div>
        </div>
        <div class="stat-card">
            <div class="label">Today</div>
            <div class="value">{{ today_count }}</div>
        </div>
        <div class="stat-card">
            <div class="label">This Week</div>
            <div class="value">{{ week_count }}</div>
        </div>
        <div class="stat-card">
            <div class="label">Active Number</div>
            <div class="value" style="font-size: 1rem;">+442045772353</div>
        </div>
    </div>

    <div class="content">
        <h2 class="section-title">Recent Bookings</h2>
        {% if bookings %}
        <table class="bookings-table">
            <thead>
                <tr>
                    <th>Reference</th>
                    <th>Name</th>
                    <th>Pickup</th>
                    <th>Destination</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Passengers</th>
                    <th>Flight</th>
                    <th>Caller</th>
                    <th>Booked At</th>
                </tr>
            </thead>
            <tbody>
                {% for b in bookings|reverse %}
                <tr>
                    <td><span class="ref">{{ b.reference }}</span></td>
                    <td>{{ b.name or '-' }}</td>
                    <td>{{ b.pickup or '-' }}</td>
                    <td>{{ b.destination or '-' }}</td>
                    <td>{{ b.date or '-' }}</td>
                    <td>{{ b.time or '-' }}</td>
                    <td>{{ b.passengers or '-' }}</td>
                    <td>{{ b.flight or '-' }}</td>
                    <td><span class="phone-number">{{ b.caller or '-' }}</span></td>
                    <td>{{ b.timestamp[:16] if b.timestamp else '-' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">
            <p>No bookings yet. Call +44 20 4577 2353 to create one.</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/")
@app.route("/dashboard")
def dashboard():
    """Main dashboard view."""
    bookings = load_bookings()
    
    # Count today's bookings
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for b in bookings if b.get("timestamp", "").startswith(today))
    
    # Count this week's bookings (simple: last 7 days)
    week_count = len(bookings)  # TODO: proper week calculation
    
    return render_template_string(
        DASHBOARD_HTML,
        bookings=bookings,
        today_count=today_count,
        week_count=week_count
    )


@app.route("/api/bookings")
def api_bookings():
    """API endpoint to get bookings as JSON."""
    bookings = load_bookings()
    return jsonify(bookings)


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "healthy", "service": "hardin-ai-phone-dashboard"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=False)
