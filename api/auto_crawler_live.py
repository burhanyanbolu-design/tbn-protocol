"""Run real crawl with better page loading."""
import os
import json
import hashlib
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

os.chdir("/opt/tbn-protocol")

FEED_FILE = "data/live_feed.json"
STATS_FILE = "data/monitor_stats.json"

def load_feed():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE) as f:
            return json.load(f)
    return []

def save_feed(feed):
    os.makedirs("data", exist_ok=True)
    with open(FEED_FILE, "w") as f:
        json.dump(feed[-200:], f, indent=2)

print("[TBN] Starting crawl with extended wait...")

feed = load_feed()
total_checked = 0

terms = ["beauty", "fashion"]

for term in terms:
    print(f"  Crawling: {term}")
    feed.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "crawl_start",
        "url": f"meta_ads/{term}",
        "result": "scanning",
        "details": f"Scanning Meta Ad Library: {term}"
    })

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q={term}&media_type=image"
            print(f"    Loading: {url}")
            page.goto(url, timeout=45000, wait_until="networkidle")
            page.wait_for_timeout(6000)

            # Scroll down to load more
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

            # Get ALL images
            images = page.query_selector_all("img")
            print(f"    Total img tags: {len(images)}")

            img_urls = []
            for img in images:
                src = img.get_attribute("src")
                if src and "scontent" in src:
                    img_urls.append(src)

            print(f"    scontent images: {len(img_urls)}")
            browser.close()

    except Exception as e:
        print(f"    Error: {e}")
        img_urls = []

    # Download and scan
    for img_url in img_urls[:10]:
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code != 200 or len(resp.content) < 500:
                continue
        except:
            continue

        h = hashlib.sha256(resp.content).hexdigest()[:16]
        has_ai = any(m in resp.content for m in [
            b"c2pa", b"jumb", b"trainedAlgorithmicMedia",
            b"Stable Diffusion", b"DALL-E", b"AI Generated"
        ])

        feed.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "metadata_scan",
            "url": img_url[:150],
            "result": "ai_detected" if has_ai else "clean",
            "details": f"Hash:{h} | AI:{has_ai} | {len(resp.content)}B"
        })
        total_checked += 1

    feed.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "crawl_complete",
        "url": f"meta_ads/{term}",
        "result": "done",
        "details": f"Checked {min(len(img_urls),10)} ads"
    })

feed.append({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "action": "system",
    "url": "auto_crawler",
    "result": "complete",
    "details": f"Total: {total_checked} ads scanned from Meta Ad Library"
})
save_feed(feed)

# Stats
stats = {}
if os.path.exists(STATS_FILE):
    with open(STATS_FILE) as f:
        stats = json.load(f)
stats["last_crawl"] = datetime.now(timezone.utc).isoformat()
stats["total_crawls"] = stats.get("total_crawls", 0) + 1
stats["total_images_checked"] = stats.get("total_images_checked", 0) + total_checked
with open(STATS_FILE, "w") as f:
    json.dump(stats, f, indent=2)

print(f"\n[TBN] Done: {total_checked} ads scanned")
