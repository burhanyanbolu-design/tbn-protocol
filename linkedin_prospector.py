"""
TBN Protocol — LinkedIn Prospect Finder
Searches Google for LinkedIn posts matching AI governance keywords.
Finds potential customers, partners, and people to engage with.

Usage:
    python linkedin_prospector.py              # Run all searches
    python linkedin_prospector.py --keyword "EU AI Act"  # Search specific keyword

(c) 2026 Hardin Enterprises Ltd. Part of TBN Protocol tooling.
"""

import requests
import json
import os
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────────────

RESULTS_DIR = "data/linkedin_prospects"
RESULTS_FILE = os.path.join(RESULTS_DIR, "prospects.json")
HISTORY_FILE = os.path.join(RESULTS_DIR, "search_history.json")

# Keywords to search — these find your target audience
KEYWORDS = [
    # Core market
    "AI agent governance",
    "AI agent certification",
    "EU AI Act compliance",
    "AI agent attestation",
    "AI runtime governance",
    "autonomous AI agent security",
    
    # Enterprise buyers
    "AI agents Salesforce",
    "AI agent CRM governance",
    "AI write governance",
    "AI agent compliance enterprise",
    
    # German/EU market
    "KI Agent Governance",
    "AI Act Article 9",
    "AI Act Article 14",
    "sovereign AI governance",
    "T-Systems AI",
    
    # Technical decision makers
    "AI agent trust verification",
    "AI agent identity",
    "cryptographic attestation AI",
    "AI compliance infrastructure",
    
    # Competitors/adjacent
    "AI governance startup",
    "AI agent monitoring",
    "AI agent enforcement",
    "LLM governance",
    "AI agent boundary",
]

# Google Custom Search API (free tier: 100 searches/day)
# Get your own key at: https://developers.google.com/custom-search/v1/introduction
# For now, we use a simple scraping approach via requests
SEARCH_URL = "https://www.google.com/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def ensure_dirs():
    """Create output directories."""
    os.makedirs(RESULTS_DIR, exist_ok=True)


def load_prospects():
    """Load existing prospects."""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return {"prospects": [], "last_updated": None}


def save_prospects(data):
    """Save prospects to file."""
    data["last_updated"] = datetime.now().isoformat()
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def search_google(keyword, num_results=10):
    """
    Search Google for LinkedIn posts matching a keyword.
    Returns list of results with title, url, snippet.
    """
    query = f'site:linkedin.com/posts OR site:linkedin.com/pulse "{keyword}"'
    
    try:
        params = {
            "q": query,
            "num": num_results,
            "hl": "en",
        }
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        
        if resp.status_code != 200:
            print(f"  ⚠️  Google returned {resp.status_code} — may be rate limited")
            return []
        
        # Parse results from HTML (basic extraction)
        results = []
        html = resp.text
        
        # Extract URLs that contain linkedin.com
        import re
        # Find all LinkedIn URLs in the response
        urls = re.findall(r'https?://(?:www\.)?linkedin\.com/(?:posts|pulse)/[^\s"<>&]+', html)
        
        for url in urls[:num_results]:
            # Clean URL
            url = url.split("&")[0].split("?")[0]
            results.append({
                "url": url,
                "keyword": keyword,
                "found_at": datetime.now().isoformat(),
            })
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error searching for '{keyword}': {e}")
        return []


def search_with_web_tool(keyword):
    """
    Search using DuckDuckGo Lite (more reliable, less blocking).
    """
    try:
        query = f'site:linkedin.com "{keyword}"'
        url = "https://lite.duckduckgo.com/lite/"
        data = {"q": query, "kl": ""}
        resp = requests.post(url, data=data, headers=HEADERS, timeout=15)
        
        if resp.status_code != 200:
            # Fallback: try regular DuckDuckGo HTML
            url2 = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            resp = requests.get(url2, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
        
        import re
        # Extract all LinkedIn URLs from the response
        urls = re.findall(r'https?://(?:www\.)?linkedin\.com/(?:posts|pulse|in|company)/[^\s"<>&\)]+', resp.text)
        
        # Extract snippets/titles near the URLs
        snippets = re.findall(r'class="result-snippet"[^>]*>([^<]+)', resp.text)
        
        results = []
        seen_urls = set()
        
        for i, found_url in enumerate(urls[:15]):
            # Clean URL
            found_url = found_url.split("&amp;")[0].split("?")[0].rstrip("/").rstrip(".")
            if found_url in seen_urls:
                continue
            if len(found_url) < 30:
                continue
            seen_urls.add(found_url)
            
            snippet = snippets[i] if i < len(snippets) else ""
            results.append({
                "url": found_url,
                "title": snippet[:120] if snippet else "",
                "keyword": keyword,
                "found_at": datetime.now().isoformat(),
            })
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def categorize_prospect(url, title=""):
    """Categorize a prospect based on URL pattern."""
    if "/in/" in url:
        return "PERSON"
    elif "/posts/" in url:
        return "POST"
    elif "/pulse/" in url:
        return "ARTICLE"
    elif "/company/" in url:
        return "COMPANY"
    return "OTHER"


def run_search(keywords=None):
    """Run the full prospect search."""
    ensure_dirs()
    
    if keywords is None:
        keywords = KEYWORDS
    
    print("=" * 70)
    print("TBN PROTOCOL — LINKEDIN PROSPECT FINDER")
    print(f"Searching {len(keywords)} keywords...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    data = load_prospects()
    existing_urls = {p["url"] for p in data["prospects"]}
    new_prospects = []
    
    for i, keyword in enumerate(keywords):
        print(f"\n[{i+1}/{len(keywords)}] Searching: \"{keyword}\"")
        
        results = search_with_web_tool(keyword)
        
        for result in results:
            if result["url"] not in existing_urls:
                result["category"] = categorize_prospect(result["url"], result.get("title", ""))
                result["engaged"] = False
                result["notes"] = ""
                new_prospects.append(result)
                existing_urls.add(result["url"])
                print(f"  ✅ NEW: [{result['category']}] {result['url'][:80]}")
        
        if not results:
            print(f"  — No results")
    
    # Add new prospects
    data["prospects"].extend(new_prospects)
    save_prospects(data)
    
    # Summary
    print("\n" + "=" * 70)
    print("SEARCH COMPLETE")
    print("=" * 70)
    print(f"  New prospects found: {len(new_prospects)}")
    print(f"  Total prospects: {len(data['prospects'])}")
    
    # Breakdown by category
    categories = {}
    for p in data["prospects"]:
        cat = p.get("category", "OTHER")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n  Breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")
    
    print(f"\n  Results saved to: {RESULTS_FILE}")
    print(f"\n  Next steps:")
    print(f"    1. Open {RESULTS_FILE}")
    print(f"    2. Visit the LinkedIn URLs")
    print(f"    3. Engage with relevant posts/people")
    print(f"    4. Mark 'engaged: true' after connecting")
    
    return new_prospects


def show_prospects(category=None):
    """Display saved prospects."""
    ensure_dirs()
    data = load_prospects()
    
    prospects = data["prospects"]
    if category:
        prospects = [p for p in prospects if p.get("category") == category]
    
    print(f"\n{'=' * 70}")
    print(f"SAVED PROSPECTS ({len(prospects)} total)")
    print(f"{'=' * 70}")
    
    for p in prospects:
        engaged = "✅" if p.get("engaged") else "⬜"
        print(f"\n  {engaged} [{p.get('category', '?')}] {p.get('keyword', '')}")
        print(f"     {p['url'][:90]}")
        if p.get("title"):
            print(f"     Title: {p['title'][:80]}")
        if p.get("notes"):
            print(f"     Notes: {p['notes']}")


if __name__ == "__main__":
    import sys
    
    if "--show" in sys.argv:
        show_prospects()
    elif "--keyword" in sys.argv:
        idx = sys.argv.index("--keyword")
        if idx + 1 < len(sys.argv):
            run_search([sys.argv[idx + 1]])
    elif "--people" in sys.argv:
        show_prospects("PERSON")
    elif "--posts" in sys.argv:
        show_prospects("POST")
    else:
        run_search()
