"""
TBN Protocol — Fork & Code Theft Monitor
Checks GitHub for forks and searches for code that may have been copied.

Run periodically: python monitor_forks.py
(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import requests
import json
from datetime import datetime

REPO = "burhanyanbolu-design/tbn-protocol"
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = "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"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

# Unique strings that only exist in TBN Protocol
# If found in other repos, it's likely a copy
WATERMARK_STRINGS = [
    "HRD-SC-9f2e7b4a",
    "HRD-GE-3c8d1f5a",
    "HRD-RS-6a4e2d9c",
    "HRD-CD-1b7f4e8a",
    "HRD-BE-5d2c8f3a",
    "HRD-CP-8e1a6b4d",
    "HRD-RT-2a5f9c7e",
    "HRD-AC-4b9e7f2c",
    "HRD-EGG-0x4f7a2b9e1c3d",
    "7f3a9b2e-4d1c-4e8f-b6a2-9c0d5e8f1a3b",
    "hardin-tbn-2026-burhan-yanbolu-agpl3",
    "_HARDIN_ORIGIN",
    "_tbn_provenance_check",
]

# Unique code patterns (function names, variable names)
CODE_PATTERNS = [
    "TBN Security Challenge System",
    "TBN Compliance Drift System",
    "TBN Budget & Cost Enforcement",
    "TBN Governance Engine",
    "BICA trust registry",
    "Bot Language Compiler",
    "tbn_provenance_check",
    "verify_origin",
]


def check_forks():
    """List all forks of the TBN Protocol repo."""
    print("=" * 60)
    print("TBN PROTOCOL — FORK MONITOR")
    print(f"Repo: {REPO}")
    print(f"Checked: {datetime.now().isoformat()}")
    print("=" * 60)
    
    url = f"{GITHUB_API}/repos/{REPO}/forks"
    resp = requests.get(url, headers=HEADERS)
    
    if resp.status_code == 200:
        forks = resp.json()
        if not forks:
            print("\n✅ No forks found. Your code has not been forked.")
        else:
            print(f"\n⚠️  {len(forks)} FORK(S) DETECTED:\n")
            for fork in forks:
                print(f"  👤 {fork['owner']['login']}")
                print(f"     Repo: {fork['html_url']}")
                print(f"     Created: {fork['created_at']}")
                print(f"     Last push: {fork['pushed_at']}")
                print(f"     Private: {fork['private']}")
                print()
    else:
        print(f"❌ Error checking forks: {resp.status_code}")
    
    return forks if resp.status_code == 200 else []


def search_github_for_copies():
    """Search GitHub for code that contains our watermarks."""
    print("\n" + "=" * 60)
    print("SEARCHING FOR CODE COPIES...")
    print("=" * 60)
    
    found_violations = []
    
    for pattern in WATERMARK_STRINGS[:5]:  # GitHub rate limits, check top 5
        url = f"{GITHUB_API}/search/code"
        params = {"q": f'"{pattern}" -repo:{REPO}'}
        resp = requests.get(url, params=params, headers=HEADERS)
        
        if resp.status_code == 200:
            results = resp.json()
            if results.get("total_count", 0) > 0:
                print(f"\n🚨 WATERMARK FOUND ELSEWHERE: {pattern}")
                print(f"   Found in {results['total_count']} file(s):")
                for item in results.get("items", [])[:3]:
                    print(f"   → {item['repository']['full_name']}: {item['path']}")
                    found_violations.append({
                        "watermark": pattern,
                        "repo": item['repository']['full_name'],
                        "file": item['path'],
                        "url": item['html_url'],
                    })
            else:
                print(f"  ✅ {pattern[:20]}... — not found elsewhere")
        elif resp.status_code == 403:
            print("  ⏳ Rate limited — try again in 60 seconds")
            break
        else:
            print(f"  ❌ Error: {resp.status_code}")
    
    if found_violations:
        print("\n" + "=" * 60)
        print("🚨 POTENTIAL AGPL VIOLATIONS DETECTED")
        print("=" * 60)
        for v in found_violations:
            print(f"\n  Watermark: {v['watermark']}")
            print(f"  Repo: {v['repo']}")
            print(f"  File: {v['file']}")
            print(f"  URL: {v['url']}")
        print("\n  ACTION: Check if these repos comply with AGPL-3.0")
        print("  If not, send cease & desist to: burhan@hardinai.co.uk")
    else:
        print("\n✅ No copies of your watermarked code found on GitHub.")
    
    return found_violations


def check_repo_stats():
    """Check repo stats — stars, watchers, etc."""
    url = f"{GITHUB_API}/repos/{REPO}"
    resp = requests.get(url, headers=HEADERS)
    
    if resp.status_code == 200:
        repo = resp.json()
        print("\n" + "=" * 60)
        print("REPO STATS")
        print("=" * 60)
        print(f"  Stars: {repo['stargazers_count']}")
        print(f"  Watchers: {repo['watchers_count']}")
        print(f"  Forks: {repo['forks_count']}")
        print(f"  Open issues: {repo['open_issues_count']}")
        print(f"  License: {repo.get('license', {}).get('spdx_id', 'Unknown')}")
        print(f"  Last push: {repo['pushed_at']}")


if __name__ == "__main__":
    check_repo_stats()
    forks = check_forks()
    search_github_for_copies()
    
    print("\n" + "=" * 60)
    print("MONITOR COMPLETE")
    print("=" * 60)
    print("\nTip: Run this weekly or set up a cron job on your server:")
    print("  crontab -e")
    print("  0 9 * * 1 cd /opt/tbn-protocol && python3 monitor_forks.py >> /var/log/tbn/fork_monitor.log")
    print()
