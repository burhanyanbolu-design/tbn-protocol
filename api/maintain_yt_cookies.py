#!/usr/bin/env python3
"""
Auto-maintain YouTube cookies for TBN Video Agent.

Strategy:
  - MASTER cookies file (read-only) — never modified
  - WORKING copy created on-demand before each yt-dlp run
  - Daily Playwright refresh extends the master session

Run daily via systemd timer.
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime, timezone

LOG_FILE = "/var/log/tbn/yt_maintenance.log"
ALERT_FILE = "/opt/tbn-protocol/YT_COOKIES_BROKEN.flag"
HEALTH_FILE = "/opt/tbn-protocol/yt_cookies_health.json"

# Master file — read-only, only modified by maintenance refresh
MASTER_COOKIES = "/opt/tbn-protocol/youtube_cookies_master.txt"
MASTER_BROWSER = "/opt/tbn-protocol/youtube_browser_cookies.json"
# Working file — created fresh from master before each yt-dlp run
WORKING_COOKIES = "/opt/tbn-protocol/youtube_cookies.txt"


def log(msg):
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def write_health(status, details):
    try:
        with open(HEALTH_FILE, "w") as f:
            json.dump({
                "last_check": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "details": details,
            }, f, indent=2)
    except Exception:
        pass


def set_alert(reason):
    try:
        with open(ALERT_FILE, "w") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}\n{reason}\n")
        log(f"⚠️  ALERT: {reason}")
    except Exception:
        pass


def clear_alert():
    if os.path.exists(ALERT_FILE):
        try:
            os.remove(ALERT_FILE)
        except Exception:
            pass


def refresh_via_playwright():
    """Visit YouTube with master cookies — extends session expiry."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed"

    if not os.path.exists(MASTER_BROWSER):
        return False, f"Master browser cookies missing: {MASTER_BROWSER}"

    with open(MASTER_BROWSER) as f:
        cookies = json.load(f)

    if not cookies:
        return False, "Empty cookies file"

    log(f"Refreshing {len(cookies)} YouTube cookies via Playwright...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            context.add_cookies(cookies)
            page = context.new_page()

            try:
                page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                log(f"  Goto warning (non-fatal): {e}")

            page.wait_for_timeout(5000)

            current_url = page.url
            if "/accounts/login" in current_url or "consent" in current_url.lower():
                browser.close()
                return False, f"Redirected to login/consent: {current_url}"

            refreshed = context.cookies()
            browser.close()

        if not refreshed:
            return False, "No cookies returned"

        # Write refreshed cookies to BOTH master files
        # JSON format for Playwright
        with open(MASTER_BROWSER + ".tmp", "w") as f:
            json.dump(refreshed, f, indent=2)
        os.replace(MASTER_BROWSER + ".tmp", MASTER_BROWSER)

        # Netscape format for yt-dlp (master)
        with open(MASTER_COOKIES + ".tmp", "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# Auto-refreshed by maintain_yt_cookies.py — DO NOT EDIT\n\n")
            for c in refreshed:
                domain = c["domain"]
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure") else "FALSE"
                expires = str(int(c.get("expires", 0))) if c.get("expires", -1) > 0 else "0"
                name = c["name"]
                value = c["value"]
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        os.replace(MASTER_COOKIES + ".tmp", MASTER_COOKIES)

        # Make master files read-only (444 = r--r--r--)
        os.chmod(MASTER_COOKIES, 0o444)
        os.chmod(MASTER_BROWSER, 0o444)

        log(f"✅ Saved {len(refreshed)} refreshed cookies (master files locked read-only)")
        return True, f"Session refreshed ({len(refreshed)} cookies)"

    except Exception as e:
        return False, f"Playwright error: {type(e).__name__}: {e}"


def test_youtube_download():
    """Try downloading a tiny public video to verify cookies work."""
    if not os.path.exists(MASTER_COOKIES):
        return False, f"Master cookies missing: {MASTER_COOKIES}"

    # Always create fresh working copy from master before yt-dlp
    shutil.copy(MASTER_COOKIES, WORKING_COOKIES)
    os.chmod(WORKING_COOKIES, 0o666)  # yt-dlp needs write access

    test_path = "/tmp/yt_health_test.mp4"
    if os.path.exists(test_path):
        os.remove(test_path)

    cmd = [
        "yt-dlp",
        "--cookies", WORKING_COOKIES,
        "--js-runtimes", "node:/usr/bin/node",
        "--remote-components", "ejs:github",
        "--extractor-args", "youtube:player_client=tv,web_safari,android",
        "-f", "worst[ext=mp4]/worst",
        "--no-playlist",
        "--max-filesize", "5M",
        "-o", test_path,
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(test_path):
            size = os.path.getsize(test_path)
            os.remove(test_path)
            if size > 50000:
                return True, f"Test video downloaded ({size:,} bytes)"
            return False, f"Test video too small ({size} bytes)"
        return False, f"yt-dlp failed: {(result.stderr or result.stdout)[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "yt-dlp timeout"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def main():
    log("=" * 60)
    log("YouTube cookie maintenance starting")

    # Step 1: refresh cookies (extends session expiry)
    refresh_ok, refresh_msg = refresh_via_playwright()
    log(f"Refresh: {refresh_msg}")

    # Step 2: test download (uses fresh working copy)
    test_ok, test_msg = test_youtube_download()
    log(f"Test: {test_msg}")

    if test_ok:
        clear_alert()
        write_health("HEALTHY", {"refresh": refresh_msg, "test": test_msg})
        log("✅ YouTube cookies healthy")
    else:
        set_alert(f"YouTube test failed: {test_msg}")
        write_health("BROKEN", {"refresh": refresh_msg, "test": test_msg})

    log("=" * 60)


if __name__ == "__main__":
    main()
