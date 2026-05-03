"""
Bot Language Compiler
Translates natural language human input → structured Bot Language messages.

This is the ONLY place translation happens.
Bot-to-bot communication is native Bot Language — no compiler needed.

Example:
    Input:  "Find trusted AI tools for small businesses"
    Output: BotMessage with INTENT=SEARCH, filters, trust level etc.
"""

import re
from .bot_language import BotMessage, Intent, TrustLevel


# ── Keyword maps ────────────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    Intent.SEARCH: [
        "find", "search", "look for", "discover", "get", "fetch",
        "show me", "list", "what are", "give me",
    ],
    Intent.DATA_REQUEST: [
        "request", "retrieve", "pull", "load", "read", "query",
    ],
    Intent.PING: [
        "ping", "check", "status", "alive", "health",
    ],
}

TRUST_KEYWORDS = {
    TrustLevel.HIGH: [
        "trusted", "verified", "secure", "certified", "official", "safe",
    ],
    TrustLevel.MEDIUM: [
        "public", "open", "community",
    ],
    TrustLevel.LOW: [
        "any", "all", "unknown", "unverified",
    ],
}

AUDIENCE_KEYWORDS = [
    "small business", "enterprise", "startup", "developer", "consumer",
    "government", "healthcare", "finance",
]

DATA_TYPE_KEYWORDS = {
    "AI_TOOLS": ["ai tool", "ai app", "ai platform", "ai service", "llm", "model"],
    "CODE": ["code", "repository", "repo", "github", "library", "package"],
    "DATA": ["data", "dataset", "database", "records"],
    "DOCS": ["documentation", "docs", "guide", "tutorial", "manual"],
    "NEWS": ["news", "article", "blog", "update"],
}


class BotLanguageCompiler:
    """
    Compiles a natural language string into a signed BotMessage.
    Only used at the human entry point — bots speak BL natively.
    """

    def compile(self, text: str, sender_id: str, identity=None) -> BotMessage:
        """
        Compile a human query into a Bot Language message.

        Args:
            text:      The human's natural language input
            sender_id: The bot ID sending this message
            identity:  BotIdentity to sign the message (optional)

        Returns:
            A BotMessage ready to send into the network
        """
        text_lower = text.lower().strip()

        intent = self._detect_intent(text_lower)
        trust_level = self._detect_trust(text_lower)
        data_type = self._detect_data_type(text_lower)
        audience = self._detect_audience(text_lower)
        filters = {}
        if audience:
            filters["audience"] = audience

        data = {
            "QUERY": text,
            "DATA_TYPE": data_type,
            "PRIORITY": self._detect_priority(text_lower),
        }
        if filters:
            data["FILTERS"] = filters

        msg = BotMessage(
            sender_id=sender_id,
            intent=intent,
            trust_level=trust_level,
            data=data,
        )

        if identity:
            msg.sign(identity)

        return msg

    # ── Private helpers ──────────────────────────────────────────────

    def _detect_intent(self, text: str) -> Intent:
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return intent
        return Intent.DATA_REQUEST  # default

    def _detect_trust(self, text: str) -> TrustLevel:
        for level, keywords in TRUST_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return level
        return TrustLevel.MEDIUM  # default

    def _detect_data_type(self, text: str) -> str:
        for dtype, keywords in DATA_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return dtype
        return "GENERAL"

    def _detect_audience(self, text: str) -> str | None:
        for audience in AUDIENCE_KEYWORDS:
            if audience in text:
                return audience.replace(" ", "_").upper()
        return None

    def _detect_priority(self, text: str) -> int:
        urgent_words = ["urgent", "asap", "immediately", "now", "critical"]
        if any(w in text for w in urgent_words):
            return 1
        low_words = ["whenever", "low priority", "not urgent"]
        if any(w in text for w in low_words):
            return 3
        return 2  # default medium priority
