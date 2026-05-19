"""
TBN Protocol — LinkedIn Prospect Finder API
Searches for LinkedIn posts/people in the AI governance space.
Dashboard at /prospects (admin only).

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-PF-7a3b9e2d
"""

import os
import re
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

prospects_bp = Blueprint('prospects', __name__)

PROSPECTS_FILE = "data/linkedin_prospects.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _load_prospects():
    if os.path.exists(PROSPECTS_FILE):
        with open(PROSPECTS_FILE, "r") as f:
            return json.load(f)
    return {"prospects": []}


def _save_prospects(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PROSPECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _categorize(url):
    if "/in/" in url:
        return "PERSON"
    elif "/posts/" in url:
        return "POST"
    elif "/pulse/" in url:
        return "ARTICLE"
    elif "/company/" in url:
        return "COMPANY"
    return "OTHER"


def _search_linkedin(keyword):
    """Search DuckDuckGo for LinkedIn posts matching keyword."""
    try:
        query = f'site:linkedin.com "{keyword}"'
        url = "https://lite.duckduckgo.com/lite/"
        data = {"q": query, "kl": ""}
        resp = requests.post(url, data=data, headers=HEADERS, timeout=15)

        if resp.status_code != 200:
            url2 = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            resp = requests.get(url2, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []

        urls = re.findall(
            r'https?://(?:www\.)?linkedin\.com/(?:posts|pulse|in|company)/[^\s"<>&\)]+',
            resp.text
        )

        results = []
        seen = set()
        for found_url in urls[:15]:
            found_url = found_url.split("&amp;")[0].split("?")[0].rstrip("/").rstrip(".")
            if found_url in seen or len(found_url) < 30:
                continue
            seen.add(found_url)
            results.append({
                "url": found_url,
                "title": "",
                "keyword": keyword,
                "found_at": datetime.now().isoformat(),
                "category": _categorize(found_url),
                "engaged": False,
                "notes": "",
            })

        return results
    except Exception as e:
        print(f"[Prospects] Search error: {e}")
        return []


# ── Routes ─────────────────────────────────────────────────────────────

@prospects_bp.route("/prospects")
def prospect_dashboard():
    """Render the prospect finder dashboard (admin only)."""
    admin_key = request.args.get("key", "")
    expected = os.environ.get("TBN_ADMIN_SECRET", "")
    if not expected or admin_key != expected:
        return "Not Found", 404
    return render_template("prospect_dashboard.html")


@prospects_bp.route("/api/prospects", methods=["GET"])
def get_prospects():
    """Return all saved prospects."""
    data = _load_prospects()
    return jsonify(data)


@prospects_bp.route("/api/prospects/search", methods=["POST"])
def search_prospects():
    """Search LinkedIn for a keyword and return results."""
    body = request.get_json() or {}
    keyword = body.get("keyword", "").strip()

    if not keyword:
        return jsonify({"error": "keyword is required"}), 400

    results = _search_linkedin(keyword)

    # Save new results
    data = _load_prospects()
    existing_urls = {p["url"] for p in data["prospects"]}
    new_results = []

    for r in results:
        if r["url"] not in existing_urls:
            data["prospects"].insert(0, r)
            existing_urls.add(r["url"])
            new_results.append(r)

    _save_prospects(data)

    return jsonify({
        "keyword": keyword,
        "results": new_results,
        "total_new": len(new_results),
        "total_saved": len(data["prospects"]),
    })


@prospects_bp.route("/api/prospects/save", methods=["POST"])
def save_prospects():
    """Save updated prospects (e.g. marking as engaged)."""
    body = request.get_json() or {}
    prospects = body.get("prospects", [])

    data = {"prospects": prospects}
    _save_prospects(data)

    return jsonify({"saved": len(prospects)})
