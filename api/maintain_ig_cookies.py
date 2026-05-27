#!/usr/bin/env python3
"""
Auto-maintain Instagram cookies for TBN Video Agent.

Strategy: Visit Instagram with current cookies — Instagram returns refreshed
cookies which extend the session. This keeps the session alive as long as
we run at least every 30 days.

If cookies fail (expired/logged out), write to alert file.

Run daily via systemd timer or cron.
"""

import os
import json
import sys
import time
import shutil
import requests
from datetime import datetime, timezone
from http.cookiejar import MozillaCookieJar

LOG_FILE = "/var/log/tbn/ig_maintenance.log"
ALERT_FILE = "/opt/tbn-protocol/IG_COOKIES_BROKEN.flag"
COOKIES_TXT = "/opt/tbn-protocol/instagram_cookies.txt"
COOKIES_JSON = "/opt/tbn-protocol/instagram_browser_cookies.json"
HEALTH_FILE = "/opt/tbn-protocol/ig_cookies_health.json"


def log(msg):
    """Log to file and stdout."""
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
    """Write health status to a file the API can read."""
    health = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "details": details,
    }
    try:
        with open(HEALTH_FILE, "w") as f:
            json.dump(health, f, indent=2)
    except Exception as e:
        log(f"Failed to write health file: {e}")


def set_alert(reason):
    """Create alert flag file when cookies are broken."""
    try:
        with open(ALERT_FILE, "w") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}\n{reason}\n")
        log(f"⚠️  ALERT FLAG SET: {reason}")
    except Exception as e:
        log(f"Failed to set alert: {e}")


def clear_alert():
    """Remove alert flag when cookies are healthy."""
    if os.path.exists(ALERT_FILE):
        try:
            os.remove(ALERT_FILE)
            log("Alert flag cleared")
        except Exception:
            pass


def refresh_cookies_via_playwright():
    """
    Visit Instagram with current cookies. Instagram returns refreshed cookies
    (longer expiry) which we save back. This keeps the session alive.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed"

    if not os.path.exists(COOKIES_JSON):
        return False, "No cookies file found"

    with open(COOKIES_JSON) as f:
        cookies = json.load(f)

    if not cookies:
        return False, "Empty cookies file"

    log(f"Refreshing {len(cookies)} cookies via Playwright...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            context.add_cookies(cookies)
            page = context.new_page()

            # Visit Instagram homepage — this triggers cookie refresh
            try:
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                log(f"  Homepage goto warning (non-fatal): {e}")

            page.wait_for_timeout(5000)

            # Check if we're logged in by looking for login redirect
            current_url = page.url
            if "/accounts/login" in current_url:
                browser.close()
                return False, f"Redirected to login — cookies expired. URL: {current_url}"

            # Visit a profile to keep session active
            try:
                page.goto("https://www.instagram.com/instagram/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)
            except Exception:
                pass

            # Extract refreshed cookies
            refreshed = context.cookies()
            browser.close()

        # Find sessionid in refreshed cookies
        session_cookie = next((c for c in refreshed if c["name"] == "sessionid"), None)
        if not session_cookie:
            return False, "No sessionid in refreshed cookies — likely logged out"

        # Backup old cookies
        if os.path.exists(COOKIES_JSON):
            shutil.copy(COOKIES_JSON, COOKIES_JSON + ".bak")

        # Save refreshed cookies (Playwright JSON format)
        with open(COOKIES_JSON, "w") as f:
            json.dump(refreshed, f, indent=2)

        # Also update Netscape format for yt-dlp
        with open(COOKIES_TXT, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# Auto-refreshed by maintain_ig_cookies.py\n\n")
            for c in refreshed:
                domain = c["domain"]
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure") else "FALSE"
                expires = str(int(c.get("expires", 0))) if c.get("expires", -1) > 0 else "0"
                name = c["name"]
                value = c["value"]
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        log(f"✅ Saved {len(refreshed)} refreshed cookies")

        # Calculate session expiry
        if session_cookie.get("expires", -1) > 0:
            expiry_dt = datetime.fromtimestamp(session_cookie["expires"], tz=timezone.utc)
            days_left = (expiry_dt - datetime.now(timezone.utc)).days
            return True, f"Session refreshed, expires in {days_left} days"
        return True, "Session refreshed (no expiry timestamp)"

    except Exception as e:
        return False, f"Playwright error: {type(e).__name__}: {e}"


def test_with_real_reel():
    """Test by attempting to download a public Instagram reel."""
    sys.path.insert(0, "/opt/tbn-protocol")
    try:
        from instagram_download import download_instagram_video
    except ImportError:
        return False, "instagram_download module not found"

    # Use Instagram's own official reel as a stable test target
    test_url = "https://www.instagram.com/reel/DYrikxAlwxC/"
    test_path = "/tmp/ig_health_test.mp4"

    if os.path.exists(test_path):
        os.remove(test_path)

    log(f"Testing download: {test_url}")
    result = download_instagram_video(test_url, test_path)

    if result and os.path.exists(test_path):
        size = os.path.getsize(test_path)
        os.remove(test_path)
        if size > 100000:
            return True, f"Test reel downloaded ({size:,} bytes)"
        return False, f"Test reel too small ({size} bytes)"
    return False, "Test reel download failed"


def main():
    log("=" * 60)
    log("Instagram cookie maintenance starting")

    # Step 1: Refresh cookies
    refresh_ok, refresh_msg = refresh_cookies_via_playwright()
    log(f"Refresh: {refresh_msg}")

    if not refresh_ok:
        set_alert(f"Cookie refresh failed: {refresh_msg}")
        write_health("BROKEN", {"refresh": refresh_msg, "test": "skipped"})
        log("=" * 60)
        sys.exit(1)

    # Step 2: Test with real reel
    test_ok, test_msg = test_with_real_reel()
    log(f"Test: {test_msg}")

    if test_ok:
        clear_alert()
        write_health("HEALTHY", {"refresh": refresh_msg, "test": test_msg})
        log("✅ All checks passed")
    else:
        set_alert(f"Test download failed: {test_msg}")
        write_health("BROKEN", {"refresh": refresh_msg, "test": test_msg})

    log("=" * 60)


if __name__ == "__main__":
    main()
