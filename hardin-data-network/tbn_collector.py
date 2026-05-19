"""
TBN Ethical Data Collector
===========================
Transparent, compliant web data collection for TBN Protocol.

Rules:
  1. Always identifies itself honestly (TBN-Bot user-agent)
  2. Respects robots.txt — if they say no, we don't go
  3. Rate-limited — never hammers a server
  4. Logs everything — full audit trail of what was collected and from where
  5. No logins, no paywalls, no bypassing access controls
  6. Credits sources in all data records

Usage:
    from tbn_collector import TBNCollector

    collector = TBNCollector()
    
    # Check if we're allowed first
    if collector.is_allowed("https://example.com/data"):
        data = collector.fetch("https://example.com/data")
    
    # Or use the safe_fetch which checks automatically
    data = collector.safe_fetch("https://example.com/data")

(c) Hardin AI Solutions — tbn.hardinai.co.uk
License: AGPL-3.0
"""

import os
import json
import time
import hashlib
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_NAME = "TBN-Bot"
BOT_VERSION = "1.0"
BOT_URL = "https://tbn.hardinai.co.uk/bot-info"
BOT_CONTACT = "burhan@hardinai.co.uk"

USER_AGENT = f"{BOT_NAME}/{BOT_VERSION} (+{BOT_URL}; contact: {BOT_CONTACT})"

# Rate limiting
MIN_DELAY_SECONDS = 1.5   # Minimum wait between requests to same domain
MAX_DELAY_SECONDS = 3.0   # Maximum wait (randomized for politeness)
MAX_REQUESTS_PER_MINUTE = 20  # Hard cap per domain

# Logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collection_logs")
os.makedirs(LOG_DIR, exist_ok=True)


# ============================================================================
# ROBOTS.TXT CHECKER
# ============================================================================

class RobotsTxtChecker:
    """Checks and caches robots.txt for each domain"""

    def __init__(self):
        self._cache = {}  # domain -> RobotFileParser
        self._cache_time = {}  # domain -> timestamp

    def is_allowed(self, url: str) -> bool:
        """Check if our bot is allowed to access this URL"""
        parsed = urlparse(url)
        domain = parsed.netloc

        # Refresh cache every hour
        if domain in self._cache_time:
            age = time.time() - self._cache_time[domain]
            if age > 3600:
                del self._cache[domain]
                del self._cache_time[domain]

        # Fetch and parse robots.txt if not cached
        if domain not in self._cache:
            self._fetch_robots(parsed.scheme, domain)

        parser = self._cache.get(domain)
        if parser is None:
            # If we couldn't fetch robots.txt, assume allowed
            return True

        return parser.can_fetch(USER_AGENT, url)

    def _fetch_robots(self, scheme: str, domain: str):
        """Fetch and parse robots.txt for a domain"""
        import requests

        robots_url = f"{scheme}://{domain}/robots.txt"
        try:
            response = requests.get(
                robots_url,
                headers={"User-Agent": USER_AGENT},
                timeout=10
            )
            if response.status_code == 200:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                self._cache[domain] = parser
            else:
                # No robots.txt = everything allowed
                self._cache[domain] = None
        except Exception:
            # Can't reach robots.txt = assume allowed
            self._cache[domain] = None

        self._cache_time[domain] = time.time()

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """Get the crawl-delay specified in robots.txt"""
        parsed = urlparse(url)
        domain = parsed.netloc
        parser = self._cache.get(domain)
        if parser:
            delay = parser.crawl_delay(USER_AGENT)
            return delay
        return None


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Ensures we don't overwhelm any single domain"""

    def __init__(self):
        self._last_request = {}  # domain -> timestamp
        self._request_count = {}  # domain -> count in current minute
        self._minute_start = {}  # domain -> minute start time

    def wait(self, domain: str, crawl_delay: float = None):
        """Wait appropriate time before next request to this domain"""
        now = time.time()

        # Check per-minute cap
        if domain in self._minute_start:
            elapsed = now - self._minute_start[domain]
            if elapsed < 60:
                if self._request_count.get(domain, 0) >= MAX_REQUESTS_PER_MINUTE:
                    wait_time = 60 - elapsed
                    print(f"  [Rate limit] Waiting {wait_time:.1f}s (hit {MAX_REQUESTS_PER_MINUTE}/min cap for {domain})")
                    time.sleep(wait_time)
                    self._request_count[domain] = 0
                    self._minute_start[domain] = time.time()
            else:
                self._request_count[domain] = 0
                self._minute_start[domain] = now
        else:
            self._minute_start[domain] = now
            self._request_count[domain] = 0

        # Respect crawl-delay from robots.txt
        delay = crawl_delay or random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)

        if domain in self._last_request:
            elapsed = now - self._last_request[domain]
            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)

        self._last_request[domain] = time.time()
        self._request_count[domain] = self._request_count.get(domain, 0) + 1


# ============================================================================
# COLLECTION LOGGER
# ============================================================================

class CollectionLogger:
    """Full audit trail of all data collection"""

    def __init__(self):
        self.log_file = os.path.join(LOG_DIR, f"collection_{datetime.now().strftime('%Y-%m-%d')}.json")
        self.entries = []

    def log(self, url: str, status: str, response_code: int = None,
            data_collected: bool = False, notes: str = ""):
        """Log a collection attempt"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "domain": urlparse(url).netloc,
            "status": status,  # "success", "blocked_robots", "rate_limited", "error"
            "response_code": response_code,
            "data_collected": data_collected,
            "user_agent": USER_AGENT,
            "notes": notes,
        }
        self.entries.append(entry)
        self._save()
        return entry

    def _save(self):
        """Append to daily log file"""
        existing = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                existing = json.load(f)
        existing.extend(self.entries)
        with open(self.log_file, 'w') as f:
            json.dump(existing, f, indent=2)
        self.entries = []

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        if not os.path.exists(self.log_file):
            return {"total": 0, "success": 0, "blocked": 0, "errors": 0}
        with open(self.log_file, 'r') as f:
            logs = json.load(f)
        return {
            "total": len(logs),
            "success": sum(1 for l in logs if l["status"] == "success"),
            "blocked": sum(1 for l in logs if l["status"] == "blocked_robots"),
            "errors": sum(1 for l in logs if l["status"] == "error"),
            "domains": list(set(l["domain"] for l in logs)),
        }


# ============================================================================
# MAIN COLLECTOR
# ============================================================================

class TBNCollector:
    """
    Ethical, transparent data collector for TBN Protocol.
    
    - Identifies itself honestly
    - Respects robots.txt
    - Rate-limited
    - Full audit trail
    - Never bypasses access controls
    """

    def __init__(self):
        self.robots = RobotsTxtChecker()
        self.rate_limiter = RateLimiter()
        self.logger = CollectionLogger()
        self.session = self._create_session()

    def _create_session(self):
        """Create a requests session with honest headers"""
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "From": BOT_CONTACT,
        })
        return session

    def is_allowed(self, url: str) -> bool:
        """Check if we're allowed to access this URL (robots.txt)"""
        return self.robots.is_allowed(url)

    def safe_fetch(self, url: str, as_json: bool = False) -> Optional[Dict]:
        """
        Fetch a URL safely and ethically.
        
        - Checks robots.txt first
        - Respects rate limits
        - Logs everything
        - Returns None if blocked or error
        """
        domain = urlparse(url).netloc

        # Step 1: Check robots.txt
        if not self.is_allowed(url):
            self.logger.log(url, "blocked_robots", notes="Blocked by robots.txt")
            print(f"  [BLOCKED] {url} — robots.txt says no")
            return None

        # Step 2: Rate limit
        crawl_delay = self.robots.get_crawl_delay(url)
        self.rate_limiter.wait(domain, crawl_delay)

        # Step 3: Fetch
        try:
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                self.logger.log(url, "success", response.status_code, data_collected=True)

                if as_json:
                    return {
                        "url": url,
                        "domain": domain,
                        "status": response.status_code,
                        "data": response.json(),
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "collected_by": USER_AGENT,
                    }
                else:
                    return {
                        "url": url,
                        "domain": domain,
                        "status": response.status_code,
                        "content": response.text,
                        "content_type": response.headers.get("Content-Type", ""),
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "collected_by": USER_AGENT,
                    }

            elif response.status_code == 403:
                self.logger.log(url, "forbidden", response.status_code,
                                notes="Access denied — respecting their decision")
                print(f"  [FORBIDDEN] {url} — they don't want us there")
                return None

            elif response.status_code == 429:
                self.logger.log(url, "rate_limited", response.status_code,
                                notes="Too many requests — backing off")
                print(f"  [RATE LIMITED] {url} — backing off")
                time.sleep(60)  # Back off for a minute
                return None

            else:
                self.logger.log(url, "error", response.status_code)
                return None

        except Exception as e:
            self.logger.log(url, "error", notes=str(e))
            print(f"  [ERROR] {url} — {e}")
            return None

    def fetch_multiple(self, urls: List[str], as_json: bool = False) -> List[Dict]:
        """Fetch multiple URLs ethically with proper delays"""
        results = []
        total = len(urls)

        for i, url in enumerate(urls, 1):
            print(f"  [{i}/{total}] Fetching: {url}")
            result = self.safe_fetch(url, as_json=as_json)
            if result:
                results.append(result)

        print(f"\n  Done: {len(results)}/{total} successful")
        return results

    def get_collection_stats(self) -> Dict:
        """Get today's collection statistics"""
        return self.logger.get_stats()

    def print_status(self):
        """Print collection status"""
        stats = self.get_collection_stats()
        print("\n" + "=" * 50)
        print("  TBN COLLECTOR — STATUS")
        print("=" * 50)
        print(f"  Bot:        {USER_AGENT}")
        print(f"  Today:      {stats['total']} requests")
        print(f"  Success:    {stats['success']}")
        print(f"  Blocked:    {stats['blocked']} (robots.txt)")
        print(f"  Errors:     {stats['errors']}")
        print(f"  Domains:    {', '.join(stats.get('domains', []))}")
        print("=" * 50 + "\n")


# ============================================================================
# BOT INFO PAGE (serve this at /bot-info on tbn.hardinai.co.uk)
# ============================================================================

BOT_INFO_HTML = """
<!DOCTYPE html>
<html>
<head><title>TBN-Bot Information</title></head>
<body style="font-family:monospace;max-width:700px;margin:40px auto;padding:20px;">
<h1>TBN-Bot/1.0</h1>
<p>This is an automated data collection bot operated by <strong>Hardin AI Solutions</strong>.</p>

<h2>What we do</h2>
<p>TBN-Bot collects publicly available data to power the TBN Protocol — a trust infrastructure for AI agents.</p>

<h2>Our rules</h2>
<ul>
<li>We always identify ourselves honestly in our User-Agent header</li>
<li>We respect your robots.txt — if you block us, we stay away</li>
<li>We never access pages behind logins or paywalls</li>
<li>We rate-limit our requests (max 20/minute per domain)</li>
<li>We keep full audit logs of all collection activity</li>
</ul>

<h2>How to block us</h2>
<p>Add this to your robots.txt:</p>
<pre>
User-agent: TBN-Bot
Disallow: /
</pre>

<h2>Contact</h2>
<p>
Email: <a href="mailto:burhan@hardinai.co.uk">burhan@hardinai.co.uk</a><br>
Website: <a href="https://tbn.hardinai.co.uk">tbn.hardinai.co.uk</a><br>
Company: Hardin AI Solutions (Hardin Enterprises Ltd)
</p>
</body>
</html>
"""


# ============================================================================
# DEMO / TEST
# ============================================================================

if __name__ == "__main__":
    print("\n  TBN Ethical Data Collector — Test Run")
    print("  " + "=" * 50)
    print(f"  User-Agent: {USER_AGENT}")
    print()

    collector = TBNCollector()

    # Test: Check robots.txt for a few sites
    test_urls = [
        "https://www.bbc.co.uk/news",
        "https://www.gov.uk/government/statistics",
        "https://www.ons.gov.uk/economy",
    ]

    print("  Checking robots.txt permissions:")
    for url in test_urls:
        allowed = collector.is_allowed(url)
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"    {status} — {url}")

    # Test: Fetch one page
    print("\n  Test fetch (gov.uk):")
    result = collector.safe_fetch("https://www.gov.uk/government/statistics")
    if result:
        print(f"    ✅ Got {len(result['content'])} chars from {result['domain']}")
    else:
        print("    ❌ Could not fetch")

    # Show stats
    collector.print_status()
