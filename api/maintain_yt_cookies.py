#!/usr/bin/env python3
"""
Auto-maintain YouTube cookies for TBN Video Agent.
Tests yt-dlp can still download a known public video; alerts if broken.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone

LOG_FILE = "/var/log/tbn/yt_maintenance.log"
ALERT_FILE = "/opt/tbn-protocol/YT_COOKIES_BROKEN.flag"
COOKIES_FILE = "/opt/tbn-protocol/youtube_cookies.txt"
HEALTH_FILE = "/opt/tbn-protocol/yt_cookies_health.json"


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


def test_youtube_download():
    """Try downloading a tiny public video — first YouTube video ever (stable target)."""
    if not os.path.exists(COOKIES_FILE):
        return False, f"Cookies file missing: {COOKIES_FILE}"

    test_path = "/tmp/yt_health_test.mp4"
    if os.path.exists(test_path):
        os.remove(test_path)

    cmd = [
        "yt-dlp",
        "--cookies", COOKIES_FILE,
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
        return False, f"yt-dlp failed: {result.stderr[-200:] if result.stderr else 'no output'}"
    except subprocess.TimeoutExpired:
        return False, "yt-dlp timeout"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def main():
    log("=" * 60)
    log("YouTube cookie maintenance starting")

    ok, msg = test_youtube_download()
    log(f"Test: {msg}")

    if ok:
        clear_alert()
        write_health("HEALTHY", {"test": msg})
        log("✅ YouTube cookies healthy")
    else:
        set_alert(f"YouTube test failed: {msg}")
        write_health("BROKEN", {"test": msg})

    log("=" * 60)


if __name__ == "__main__":
    main()
