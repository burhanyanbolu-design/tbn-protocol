"""
Instagram Reel/Post Download — Working approach (May 2026)
============================================================
Uses Playwright with saved browser cookies to render the reel page,
captures the CDN video URL from network responses, then downloads
via the same cookie-authenticated session.

Setup:
  1. Log into Instagram in Chrome with a burner account
  2. Watch the target reel to load cookies
  3. Export cookies (Netscape format) with a browser extension
  4. Run convert_cookies.py to install on server

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import os
import re
import json
import requests
import subprocess


COOKIES_FILE = "/opt/tbn-protocol/instagram_cookies.txt"
BROWSER_COOKIES_FILE = "/opt/tbn-protocol/instagram_browser_cookies.json"
SESSION_FILE = "/opt/tbn-protocol/instaloader_session"


def _extract_shortcode(url):
    """Extract Instagram shortcode from a reel/post URL."""
    match = re.search(r'instagram\.com/(?:reel|p|reels)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None


def _strategy_playwright_cdn(url, filepath):
    """
    PRIMARY STRATEGY (working as of May 2026):
    Use Playwright with cookies to render the page, capture CDN video URL,
    then download via the same session.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    if not os.path.exists(BROWSER_COOKIES_FILE):
        return None

    try:
        with open(BROWSER_COOKIES_FILE) as f:
            cookies = json.load(f)
    except Exception:
        return None

    if not cookies:
        return None

    captured_urls = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            context.add_cookies(cookies)
            page = context.new_page()

            def on_response(response):
                resp_url = response.url
                ct = response.headers.get("content-type", "")
                if (".mp4" in resp_url or "video" in ct) and "scontent" in resp_url:
                    captured_urls.append(resp_url)

            page.on("response", on_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(8000)

            final_cookies = {c["name"]: c["value"] for c in context.cookies()}
            browser.close()

        if not captured_urls:
            return None

        # Get unique base URLs (deduplicate by stripping query strings)
        unique_bases = {}
        for u in captured_urls:
            base = u.split("?")[0]
            if base not in unique_bases:
                unique_bases[base] = u

        # Try each unique URL — download with cookies
        for base, full_url in unique_bases.items():
            # Strip byte range params to request whole file
            clean_url = re.sub(r'&?bytestart=\d+', '', full_url)
            clean_url = re.sub(r'&?byteend=\d+', '', clean_url)

            try:
                r = requests.get(
                    clean_url,
                    timeout=60,
                    cookies=final_cookies,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.instagram.com/",
                        "Accept": "*/*",
                    },
                )
                if r.status_code == 200 and len(r.content) > 100000:
                    with open(filepath, "wb") as f:
                        f.write(r.content)
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 100000:
                        return filepath
            except Exception:
                continue
    except Exception:
        pass

    return None


def _strategy_instaloader(url, filepath):
    """Fallback: instaloader with session (rarely works without checkpoint approval)."""
    try:
        import instaloader
    except ImportError:
        return None

    shortcode = _extract_shortcode(url)
    if not shortcode:
        return None

    ig_user = os.environ.get("INSTAGRAM_USER", "")
    if not ig_user or not os.path.exists(SESSION_FILE):
        return None

    try:
        L = instaloader.Instaloader(quiet=True)
        L.load_session_from_file(ig_user, SESSION_FILE)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.is_video and post.video_url:
            resp = requests.get(post.video_url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(filepath) > 100000:
                return filepath
    except Exception:
        pass
    return None


def _strategy_ytdlp(url, filepath):
    """Last-resort: yt-dlp with cookies (Instagram API often blocks this)."""
    try:
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "-f", "best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", filepath,
            "--no-playlist",
            "--socket-timeout", "30",
        ]
        if os.path.exists(COOKIES_FILE):
            cmd.extend(["--cookies", COOKIES_FILE])
        cmd.append(url)
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100000:
            return filepath
    except Exception:
        pass
    return None


def download_instagram_video(url, filepath):
    """
    Download an Instagram reel/post video.
    
    Primary: Playwright + browser cookies (works as of May 2026)
    Fallbacks: instaloader, yt-dlp
    
    Returns the filepath on success, None on failure.
    
    REQUIRES: /opt/tbn-protocol/instagram_browser_cookies.json
    Set up by exporting Instagram cookies from a logged-in browser session.
    """
    strategies = [
        ("playwright-cdn", _strategy_playwright_cdn),
        ("instaloader", _strategy_instaloader),
        ("yt-dlp", _strategy_ytdlp),
    ]

    for name, strategy in strategies:
        result = strategy(url, filepath)
        if result:
            return result

    return None
