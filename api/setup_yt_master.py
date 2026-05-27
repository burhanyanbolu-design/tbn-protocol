#!/usr/bin/env python3
"""
One-time setup: take a freshly-exported YouTube cookies.txt and create
both master files (Netscape + Playwright JSON), locked read-only.

Run after uploading new cookies to /tmp/yt_cookies_master.txt
"""

import os
import json
import sys

INPUT = "/tmp/yt_cookies_master.txt"
MASTER_COOKIES = "/opt/tbn-protocol/youtube_cookies_master.txt"
MASTER_BROWSER = "/opt/tbn-protocol/youtube_browser_cookies.json"
WORKING = "/opt/tbn-protocol/youtube_cookies.txt"

if not os.path.exists(INPUT):
    print(f"ERROR: {INPUT} not found")
    sys.exit(1)

# Make existing files writable so we can replace them
for f in [MASTER_COOKIES, MASTER_BROWSER, WORKING]:
    if os.path.exists(f):
        try:
            os.chmod(f, 0o666)
        except Exception:
            pass

# Copy Netscape master
import shutil
shutil.copy(INPUT, MASTER_COOKIES)
os.chmod(MASTER_COOKIES, 0o444)
print(f"[1/3] Master Netscape cookies → {MASTER_COOKIES} (read-only)")

# Convert to Playwright JSON
cookies = []
with open(INPUT, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, flag, path, secure, expires, name, value = parts[:7]
        cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path,
            "secure": secure.upper() == "TRUE",
            "httpOnly": False,
            "sameSite": "Lax",
        }
        try:
            exp = int(expires)
            if exp > 0:
                cookie["expires"] = exp
        except ValueError:
            pass
        cookies.append(cookie)

with open(MASTER_BROWSER, "w") as f:
    json.dump(cookies, f, indent=2)
os.chmod(MASTER_BROWSER, 0o444)
print(f"[2/3] Master Playwright cookies → {MASTER_BROWSER} (read-only) [{len(cookies)} cookies]")

# Create initial working copy
shutil.copy(MASTER_COOKIES, WORKING)
os.chmod(WORKING, 0o666)
print(f"[3/3] Working copy → {WORKING}")

print("\nDone. Cookies installed.")
print("Cookie names:", [c["name"] for c in cookies])
