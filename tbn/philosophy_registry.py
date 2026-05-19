"""
TBN Philosophy Registry
Central registry of all bot philosophies in the TBN Protocol network.
Allows querying which bots have internalized which books/authors.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path


class TBNPhilosophyRegistry:
    """
    Central registry for all bot philosophies in TBN Protocol.
    Tracks which bots have internalized which books, and whether
    their philosophy has been TBN-verified.
    """

    def __init__(self, registry_path: str = "data/tbn_philosophy_registry.json"):
        self.registry_path = registry_path
        self.registry: Dict = {}
        self._load()

    def _load(self):
        """Load existing registry"""
        if Path(self.registry_path).exists():
            with open(self.registry_path, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {"bots": {}, "created_at": datetime.now(timezone.utc).isoformat()}

    def _save(self):
        """Save registry to file"""
        Path(self.registry_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_bot_philosophy(
        self,
        bot_id: str,
        bot_name: str,
        book_title: str,
        author: str,
        philosophy_core_path: str,
        bot_identity_path: str,
    ) -> Dict:
        """Register a new bot with its internalized philosophy"""
        entry = {
            "bot_id": bot_id,
            "bot_name": bot_name,
            "book_title": book_title,
            "author": author,
            "philosophy_core_path": philosophy_core_path,
            "bot_identity_path": bot_identity_path,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "philosophy_verified": False,   # Set True after TBN review
            "verified_at": None,
        }
        self.registry["bots"][bot_id] = entry
        self._save()
        print(f"📚 Registered: {bot_name} ({book_title} by {author})")
        return entry

    def verify_bot_philosophy(self, bot_id: str) -> bool:
        """Mark a bot's philosophy as TBN-verified"""
        if bot_id not in self.registry["bots"]:
            return False
        self.registry["bots"][bot_id]["philosophy_verified"] = True
        self.registry["bots"][bot_id]["verified_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        print(f"✅ Philosophy verified: {bot_id}")
        return True

    def get_bot_philosophy(self, bot_id: str) -> Optional[Dict]:
        """Get a bot's philosophy registration info"""
        return self.registry["bots"].get(bot_id)

    def list_all_bots(self) -> List[Dict]:
        """List all registered bots and their philosophies"""
        return list(self.registry["bots"].values())

    def query_by_book(self, book_title: str) -> List[Dict]:
        """Find all bots that have internalized a specific book"""
        return [
            bot for bot in self.registry["bots"].values()
            if bot["book_title"].lower() == book_title.lower()
        ]

    def query_by_author(self, author: str) -> List[Dict]:
        """Find all bots that have internalized books by a specific author"""
        return [
            bot for bot in self.registry["bots"].values()
            if bot["author"].lower() == author.lower()
        ]

    def stats(self) -> Dict:
        """Registry statistics"""
        bots = list(self.registry["bots"].values())
        return {
            "total_bots": len(bots),
            "verified": sum(1 for b in bots if b["philosophy_verified"]),
            "pending_verification": sum(1 for b in bots if not b["philosophy_verified"]),
            "unique_books": len({b["book_title"] for b in bots}),
            "unique_authors": len({b["author"] for b in bots}),
        }


if __name__ == "__main__":
    registry = TBNPhilosophyRegistry()

    # Only register if not already present
    if not registry.get_bot_philosophy("tbn-bot-santiago-001"):
        registry.register_bot_philosophy(
            bot_id="tbn-bot-santiago-001",
            bot_name="Santiago",
            book_title="The Alchemist",
            author="Paulo Coelho",
            philosophy_core_path="data/santiago_philosophy_core.json",
            bot_identity_path="data/santiago_bot_identity.json",
        )
        registry.verify_bot_philosophy("tbn-bot-santiago-001")

    print("\nAll registered bots:")
    for bot in registry.list_all_bots():
        status = "✅ VERIFIED" if bot["philosophy_verified"] else "⏳ Pending"
        print(f"  {bot['bot_name']}: {bot['book_title']} by {bot['author']} — {status}")

    print(f"\nRegistry stats: {registry.stats()}")
