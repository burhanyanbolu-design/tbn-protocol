"""
Bot Language Compiler v2
Translates natural language → BL v2 messages.

Rules (from architecture doc):
  - Compiler ONLY needed at the human entry point
  - Bot-to-bot communication is native BL — no compiler needed
  - Output is a fully structured, signed, optionally encrypted BL message

CompilerBot is a dedicated bot type that handles compilation requests
from the network (INTENT=COMPILE → INTENT=COMPILE_RESPONSE).
"""

from .bot import Bot
from .bot_language import BotMessage, Intent, TrustLevel, Target, DataType
from .identity import BICA


# ── Keyword maps ─────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    Intent.SEARCH: [
        "find", "search", "look for", "discover", "get", "fetch",
        "show me", "list", "what are", "give me", "where can i",
    ],
    Intent.VALIDATE: [
        "validate", "verify", "check", "confirm", "is this correct",
        "is this trusted", "fact check",
    ],
    Intent.DATA_REQUEST: [
        "request", "retrieve", "pull", "load", "read", "query", "fetch data",
    ],
    Intent.PING: [
        "ping", "status", "alive", "health", "is it up",
    ],
}

TRUST_KEYWORDS = {
    TrustLevel.HIGH: [
        "trusted", "verified", "secure", "certified", "official", "safe",
        "reliable", "authoritative",
    ],
    TrustLevel.MEDIUM: [
        "public", "open", "community", "general",
    ],
    TrustLevel.LOW: [
        "any", "all", "unknown", "unverified", "whatever",
    ],
}

TARGET_KEYWORDS = {
    Target.VERIFIED_SOURCES: [
        "trusted", "verified", "certified", "official", "safe",
    ],
    Target.RESTRICTED: [
        "private", "restricted", "internal", "confidential", "secret",
    ],
    Target.PLATFORM: [
        "github", "notion", "slack", "api", "platform",
    ],
    Target.NETWORK: [
        "network", "bots", "agents", "tbn",
    ],
}

DATA_TYPE_KEYWORDS = {
    DataType.AI_TOOLS: [
        "ai tool", "ai app", "ai platform", "ai service", "llm",
        "model", "ai product", "machine learning tool",
    ],
    DataType.CODE: [
        "code", "repository", "repo", "github", "library",
        "package", "framework", "sdk",
    ],
    DataType.DATA: [
        "data", "dataset", "database", "records", "csv",
    ],
    DataType.DOCS: [
        "documentation", "docs", "guide", "tutorial", "manual", "readme",
    ],
    DataType.NEWS: [
        "news", "article", "blog", "update", "announcement",
    ],
}

AUDIENCE_KEYWORDS = [
    "small business", "enterprise", "startup", "developer",
    "consumer", "government", "healthcare", "finance",
]


class BotLanguageCompiler:
    """
    Compiles a natural language string into a BL v2 message.
    Only used at the human entry point.

    Usage:
        compiler = BotLanguageCompiler()
        msg = compiler.compile(
            text="Find trusted AI tools for small businesses",
            sender_id="human-entry-point",
        )
    """

    def compile(
        self,
        text: str,
        sender_id: str,
        identity=None,
        receiver_id: str = None,
        receiver_public_key_pem: bytes = None,
    ) -> BotMessage:
        """
        Compile a human query into a BL v2 message.

        Args:
            text:                    Human natural language input
            sender_id:               Bot ID of the sender
            identity:                BotIdentity to sign the message
            receiver_id:             Bot ID of the intended receiver
            receiver_public_key_pem: Receiver's public key for encryption

        Returns:
            Signed (and optionally encrypted) BotMessage
        """
        text_lower = text.lower().strip()

        intent     = self._detect_intent(text_lower)
        trust      = self._detect_trust(text_lower)
        target     = self._detect_target(text_lower)
        data_type  = self._detect_data_type(text_lower)
        audience   = self._detect_audience(text_lower)
        priority   = self._detect_priority(text_lower)

        data = {
            "QUERY":     text,
            "DATA_TYPE": data_type.value,
            "PRIORITY":  priority,
        }
        if audience:
            data["FILTERS"] = {"audience": audience}

        msg = BotMessage(
            sender_id=sender_id,
            intent=intent,
            trust_level=trust,
            target=target,
            data=data,
            receiver_id=receiver_id,
        )

        # Encrypt if receiver public key provided
        if receiver_id and receiver_public_key_pem:
            msg.encrypt(receiver_public_key_pem)

        # Sign after encryption (signature covers payload_hash)
        if identity:
            msg.sign(identity)

        return msg

    # ── Private helpers ──────────────────────────────────────────────

    def _detect_intent(self, text: str) -> Intent:
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return intent
        return Intent.DATA_REQUEST

    def _detect_trust(self, text: str) -> TrustLevel:
        for level, keywords in TRUST_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return level
        return TrustLevel.MEDIUM

    def _detect_target(self, text: str) -> Target:
        for target, keywords in TARGET_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return target
        return Target.PUBLIC_SOURCES

    def _detect_data_type(self, text: str) -> DataType:
        for dtype, keywords in DATA_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return dtype
        return DataType.GENERAL

    def _detect_audience(self, text: str) -> str | None:
        for audience in AUDIENCE_KEYWORDS:
            if audience in text:
                return audience.replace(" ", "_").upper()
        return None

    def _detect_priority(self, text: str) -> int:
        if any(w in text for w in ["urgent", "asap", "immediately", "now", "critical"]):
            return 1
        if any(w in text for w in ["whenever", "low priority", "not urgent"]):
            return 3
        return 2


class CompilerBot(Bot):
    """
    A dedicated CompilerBot — handles COMPILE requests from the network.
    Receives a COMPILE intent with a human query,
    returns a COMPILE_RESPONSE with the compiled BL message.

    This is Layer 2 of the TBN architecture.
    """

    BOT_TYPE = "COMPILER"

    def __init__(self, name: str, bica: BICA):
        super().__init__(name, bica)
        self._compiler = BotLanguageCompiler()
        self._compiled_count = 0

    def handle_compile_request(self, msg: BotMessage) -> dict:
        """
        Process a COMPILE intent message.
        Returns the compiled BL message as a dict.
        """
        query = msg.payload.get("QUERY", "")
        if not query:
            return {"STATUS": "ERROR", "ERROR": "No QUERY in compile request"}

        compiled = self._compiler.compile(
            text=query,
            sender_id=self.bot_id,
            identity=self.identity,
        )
        self._compiled_count += 1

        return {
            "STATUS":   "COMPILED",
            "QUERY":    query,
            "COMPILED": compiled.to_dict(),
            "INTENT":   compiled.payload["INTENT"],
            "TARGET":   compiled.payload["TARGET"],
            "TRUST":    compiled.payload["TRUST_LEVEL"],
        }

    def __repr__(self):
        return f"<CompilerBot name={self.name!r} compiled={self._compiled_count}>"
