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

# Google Custom Search API — set via env vars on the server
GOOGLE_API_KEY = os.environ.get("GOOGLE_CSE_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")


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
    """Search for LinkedIn profiles/posts matching keyword using Google Custom Search API."""
    # Primary: Google Custom Search API (reliable, 100 free/day)
    results = _search_google_cse(keyword)
    if results:
        return results
    
    # Fallback: DuckDuckGo
    results = _search_duckduckgo(keyword)
    if results:
        return results
    
    return []


def _search_google_cse(keyword):
    """Search using Google Custom Search API — reliable and fast."""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": keyword,
            "num": 10,
        }
        resp = requests.get(url, params=params, timeout=15)
        
        if resp.status_code != 200:
            print(f"[Prospects] Google CSE error: HTTP {resp.status_code} - {resp.text[:200]}")
            return []
        
        data = resp.json()
        items = data.get("items", [])
        
        results = []
        seen = set()
        for item in items:
            link = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            
            # Only keep LinkedIn URLs
            if "linkedin.com" not in link:
                continue
            
            # Clean URL
            link = link.split("?")[0].rstrip("/")
            if link in seen or len(link) < 30:
                continue
            seen.add(link)
            
            results.append({
                "url": link,
                "title": title,
                "snippet": snippet[:150],
                "keyword": keyword,
                "found_at": datetime.now().isoformat(),
                "category": _categorize(link),
                "engaged": False,
                "notes": "",
            })
        
        return results
    except Exception as e:
        print(f"[Prospects] Google CSE error: {e}")
        return []


def _search_duckduckgo(keyword):
    """Fallback: Search DuckDuckGo HTML version."""
    try:
        query = f'site:linkedin.com "{keyword}"'
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return _extract_linkedin_urls(resp.text, keyword)
    except Exception as e:
        print(f"[Prospects] DDG error: {e}")
    return []


def _extract_linkedin_urls(html_text, keyword):
    """Extract LinkedIn URLs from search result HTML."""
    urls = re.findall(
        r'https?://(?:www\.)?linkedin\.com/(?:posts|pulse|in|company)/[^\s"<>&\)\']+',
        html_text
    )

    results = []
    seen = set()
    for found_url in urls[:20]:
        found_url = found_url.split("&amp;")[0].split("?")[0].rstrip("/").rstrip(".")
        found_url = found_url.split("%")[0] if "%25" in found_url else found_url
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
