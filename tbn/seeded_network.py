"""
Seeded Network — bots share cached results across the network.
Like a distributed cache: bots "seed" knowledge to their peers.
The network grows stronger over time as more results are cached.

This is the "organic growth" routing model from the architecture doc:
  - Bots spread knowledge across the network
  - Cache and share results
  - Grows stronger over time (like BitTorrent seeding)
"""

import hashlib
import time
from datetime import datetime, timezone


class CachedResult:
    """A single cached search result stored in the seeded network."""

    def __init__(self, query: str, results: list[dict], source_bot_id: str):
        self.query = query
        self.query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:12]
        self.results = results
        self.source_bot_id = source_bot_id
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.hit_count = 0

    def __repr__(self):
        return (
            f"<CachedResult query={self.query!r} "
            f"results={len(self.results)} hits={self.hit_count}>"
        )


class SeededNetwork:
    """
    Distributed result cache shared across all nodes.
    Bots "seed" their results here. Other bots check here before searching.

    Phase 3: in-memory shared cache (single machine).
    Phase 4: distributed across AWS nodes via Redis or GitHub JSON.
    """

    def __init__(self):
        self._cache: dict[str, CachedResult] = {}  # query_hash → CachedResult
        self._seed_count = 0
        self._hit_count = 0
        self._miss_count = 0

    def seed(self, query: str, results: list[dict], source_bot_id: str) -> None:
        """
        Store results in the network cache.
        Called by bots after completing a search.
        """
        cached = CachedResult(query, results, source_bot_id)
        self._cache[cached.query_hash] = cached
        self._seed_count += 1
        print(
            f"[SeededNetwork] 🌱 Seeded: \"{query}\" "
            f"({len(results)} results) from {source_bot_id[:20]}..."
        )

    def lookup(self, query: str) -> list[dict] | None:
        """
        Look up cached results for a query.
        Returns results if found, None if cache miss.
        """
        query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:12]

        if query_hash in self._cache:
            cached = self._cache[query_hash]
            cached.hit_count += 1
            self._hit_count += 1
            print(
                f"[SeededNetwork] ⚡ Cache HIT: \"{query}\" "
                f"({len(cached.results)} results, "
                f"seeded by {cached.source_bot_id[:20]}...)"
            )
            return cached.results

        self._miss_count += 1
        print(f"[SeededNetwork] 🔍 Cache MISS: \"{query}\"")
        return None

    def fuzzy_lookup(self, query: str) -> list[dict] | None:
        """
        Try to find a cached result that partially matches the query.
        Useful when exact query isn't cached but a similar one is.
        """
        query_words = set(query.lower().split())
        best_match = None
        best_overlap = 0

        for cached in self._cache.values():
            cached_words = set(cached.query.lower().split())
            overlap = len(query_words & cached_words)
            if overlap > best_overlap and overlap >= 2:
                best_overlap = overlap
                best_match = cached

        if best_match:
            best_match.hit_count += 1
            self._hit_count += 1
            print(
                f"[SeededNetwork] 🔶 Fuzzy HIT: \"{query}\" matched "
                f"\"{best_match.query}\" (overlap={best_overlap})"
            )
            return best_match.results

        return None

    def stats(self) -> dict:
        hit_rate = (
            self._hit_count / (self._hit_count + self._miss_count)
            if (self._hit_count + self._miss_count) > 0
            else 0.0
        )
        return {
            "cached_queries": len(self._cache),
            "total_seeds": self._seed_count,
            "cache_hits": self._hit_count,
            "cache_misses": self._miss_count,
            "hit_rate": f"{hit_rate:.0%}",
        }

    def list_cache(self) -> list[dict]:
        return [
            {
                "query": c.query,
                "results": len(c.results),
                "hits": c.hit_count,
                "seeded_by": c.source_bot_id[:20] + "...",
                "created_at": c.created_at[:10],
            }
            for c in self._cache.values()
        ]
