"""
Search Bot — finds information across the TBN network.
Receives a DATA_REQUEST, searches its knowledge, returns DATA_RESPONSE.
"""

from ..bot import Bot
from ..bot_language import BotMessage, Intent, TrustLevel, BotMessage
from ..identity import BICA


class SearchBot(Bot):
    """
    Specialised bot for finding and returning information.
    In Phase 2 this searches a local index.
    Phase 3+ will query distributed nodes.
    """

    BOT_TYPE = "SEARCH"

    def __init__(self, name: str, bica: BICA, index: list[dict] = None, ca=None, **kwargs):
        super().__init__(name, bica, ca=ca, **kwargs)
        # Local knowledge index — list of records
        self._index: list[dict] = index or []

    def add_to_index(self, record: dict) -> None:
        """Add a record to this bot's local search index."""
        self._index.append(record)

    def handle_request(self, msg: BotMessage) -> dict:
        """
        Process a DATA_REQUEST message and return result data.
        Searches the local index for matching records.
        """
        query = msg.payload.get("QUERY", "").lower()
        filters = msg.payload.get("FILTERS", {})
        trust_level = msg.payload.get("TRUST_LEVEL", "MEDIUM")

        results = []
        for record in self._index:
            # Simple keyword match
            searchable = " ".join(str(v) for v in record.values()).lower()
            if any(word in searchable for word in query.split()):
                # Apply audience filter if present
                if "audience" in filters:
                    audience = filters["audience"].lower().replace("_", " ")
                    if audience not in searchable:
                        continue
                results.append(record)

        return {
            "RESULTS": results,
            "RESULT_COUNT": len(results),
            "QUERY": msg.payload.get("QUERY"),
            "STATUS": "SUCCESS" if results else "NO_RESULTS",
        }

    def __repr__(self):
        return f"<SearchBot name={self.name!r} index_size={len(self._index)}>"
