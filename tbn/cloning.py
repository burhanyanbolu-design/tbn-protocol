"""
Self-Cloning Bot System
When a bot is overloaded, it creates a secure clone that:
  - Inherits a sub-ID derived from the parent
  - Inherits permissions and task context
  - Executes the task in parallel
  - Results merge back to parent
  - Clone is destroyed after task completes (or kept if load stays high)

This is TBN Layer 8 from the architecture doc.

Flow:
  1. Bot detects overload (queue > threshold)
  2. Bot requests clone from CloneManager
  3. CloneManager creates clone with sub-ID
  4. Clone registers with BICA
  5. Clone executes task
  6. Results returned to parent
  7. Clone deregistered (or kept)
"""

import threading
import time
import hashlib
from datetime import datetime, timezone

from .identity import BotIdentity, BICA
from .bots.search_bot import SearchBot


# Load threshold — clone when queue exceeds this
CLONE_THRESHOLD = 3


class BotClone:
    """
    A temporary clone of a parent bot.
    Has a derived ID (parent_id + clone_number).
    Shares the parent's knowledge index but has its own identity.
    """

    def __init__(self, parent: SearchBot, clone_number: int, bica: BICA):
        self.parent = parent
        self.clone_number = clone_number
        self.bica = bica
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.destroyed = False
        self.tasks_completed = 0

        # Derive clone ID from parent ID + clone number
        raw = f"{parent.bot_id}-clone-{clone_number}"
        self.clone_id = "tbn-clone-" + hashlib.sha256(raw.encode()).hexdigest()[:12]

        # Clone inherits parent's index (shared reference — read only)
        self._index = parent._index

        # Register clone with BICA
        self._register_with_bica()

        print(
            f"[CloneManager] 🔄 Clone created: {self.clone_id} "
            f"(parent: {parent.name})"
        )

    def _register_with_bica(self) -> None:
        """Register this clone in the BICA trust registry."""
        cert = {
            "bot_id": self.clone_id,
            "name": f"{self.parent.name}-clone-{self.clone_number}",
            "parent_id": self.parent.bot_id,
            "clone": True,
            "created_at": self.created_at,
            "tbn_version": "0.1.0",
            "public_key_pem": "INHERITED_FROM_PARENT",
        }
        self.bica._registry[self.clone_id] = cert

    def execute(self, query: str, filters: dict = None) -> dict:
        """Execute a search task — same logic as SearchBot.handle_request."""
        filters = filters or {}
        results = []

        for record in self._index:
            searchable = " ".join(str(v) for v in record.values()).lower()
            if any(word in searchable for word in query.lower().split()):
                if "audience" in filters:
                    audience = filters["audience"].lower().replace("_", " ")
                    if audience not in searchable:
                        continue
                results.append(record)

        self.tasks_completed += 1
        return {
            "RESULTS": results,
            "RESULT_COUNT": len(results),
            "EXECUTED_BY": self.clone_id,
            "PARENT": self.parent.bot_id,
            "STATUS": "SUCCESS" if results else "NO_RESULTS",
        }

    def destroy(self) -> None:
        """Deregister clone from BICA and mark as destroyed."""
        if self.clone_id in self.bica._registry:
            del self.bica._registry[self.clone_id]
        self.destroyed = True
        print(
            f"[CloneManager] 💀 Clone destroyed: {self.clone_id} "
            f"(tasks completed: {self.tasks_completed})"
        )

    def __repr__(self):
        status = "destroyed" if self.destroyed else "active"
        return f"<BotClone id={self.clone_id} parent={self.parent.name} status={status}>"


class CloneManager:
    """
    Manages the lifecycle of bot clones.
    Monitors load and spins up / tears down clones automatically.
    """

    def __init__(self, bica: BICA):
        self.bica = bica
        self._clones: dict[str, list[BotClone]] = {}  # parent_id → [clones]
        self._clone_counter: dict[str, int] = {}

    def should_clone(self, bot: SearchBot, queue_size: int) -> bool:
        """Returns True if the bot should spawn a clone."""
        return queue_size >= CLONE_THRESHOLD

    def spawn_clone(self, parent: SearchBot) -> BotClone:
        """Create a new clone of the given bot."""
        parent_id = parent.bot_id
        if parent_id not in self._clone_counter:
            self._clone_counter[parent_id] = 0
        self._clone_counter[parent_id] += 1

        clone = BotClone(
            parent=parent,
            clone_number=self._clone_counter[parent_id],
            bica=self.bica,
        )

        if parent_id not in self._clones:
            self._clones[parent_id] = []
        self._clones[parent_id].append(clone)
        return clone

    def parallel_search(
        self, parent: SearchBot, queries: list[dict]
    ) -> list[dict]:
        """
        Execute multiple search queries in parallel using clones.
        Each query gets its own clone. Results are merged and returned.

        Args:
            parent:  The SearchBot to clone
            queries: List of {"query": str, "filters": dict} dicts

        Returns:
            Merged list of all results
        """
        print(
            f"\n[CloneManager] {len(queries)} tasks queued for {parent.name} "
            f"— spawning {len(queries)} clones"
        )

        results = [None] * len(queries)
        threads = []

        def run_clone(index: int, query_dict: dict):
            clone = self.spawn_clone(parent)
            result = clone.execute(
                query=query_dict["query"],
                filters=query_dict.get("filters", {}),
            )
            results[index] = result
            clone.destroy()

        for i, q in enumerate(queries):
            t = threading.Thread(target=run_clone, args=(i, q))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Merge results
        merged = []
        seen = set()
        for r in results:
            if r:
                for item in r.get("RESULTS", []):
                    key = item.get("name", str(item))
                    if key not in seen:
                        seen.add(key)
                        merged.append(item)

        print(f"[CloneManager] ✅ Parallel search complete — {len(merged)} unique results")
        return merged

    def active_clones(self, parent_id: str) -> list[BotClone]:
        """Return all active (non-destroyed) clones for a parent."""
        return [
            c for c in self._clones.get(parent_id, [])
            if not c.destroyed
        ]

    def stats(self) -> dict:
        total = sum(len(v) for v in self._clones.values())
        active = sum(
            len(self.active_clones(pid)) for pid in self._clones
        )
        return {
            "total_clones_created": total,
            "active_clones": active,
            "parents_with_clones": len(self._clones),
        }
