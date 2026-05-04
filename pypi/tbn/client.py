# TBN Protocol — Python SDK Client
# Copyright (C) 2026 Burhan Yanbolu / Hardin Enterprises Ltd
# Licensed under AGPL-3.0

"""
TBN Protocol SDK — Connect your AI agent to the Trusted Bot Network.

Quick Start:
    from tbn import TBNClient

    # Register your bot (one time)
    client = TBNClient(bot_name="MyBot", bot_type="SEARCH")
    client.register()

    # Search (automatic handshake + verification)
    results = client.search("Find AI tools for small businesses")

    # Verify another bot
    trusted = client.verify("tbn-bot-xxxx")
"""

import requests
from typing import Optional, Dict, Any, List


TBN_SERVER = "https://tbn.hardinai.co.uk"


class TBNError(Exception):
    """Raised when TBN Protocol returns an error."""
    pass


class TBNClient:
    """
    TBN Protocol SDK Client.

    Connects your AI agent to the Trusted Bot Network (TBN).
    Handles bot registration, trust handshakes, and encrypted communication.

    Args:
        bot_name: Name for your bot (e.g. "MySearchBot")
        bot_type: Type of bot - "SEARCH", "VALIDATOR", "CONNECTOR", or "MESSENGER"
        server: TBN server URL (defaults to https://tbn.hardinai.co.uk)
        auth: Optional (username, password) tuple for server authentication

    Example:
        client = TBNClient("MyBot", "SEARCH")
        client.register()
        results = client.search("Find AI tools")
    """

    def __init__(
        self,
        bot_name: str,
        bot_type: str = "SEARCH",
        server: str = TBN_SERVER,
        auth: Optional[tuple] = None,
    ):
        self.bot_name = bot_name
        self.bot_type = bot_type.upper()
        self.server = server.rstrip("/")
        self.bot_id: Optional[str] = None
        self.cert_level: Optional[str] = None
        self.certificate: Optional[Dict] = None
        self._session = requests.Session()
        if auth:
            self._session.auth = auth

    # ── Registration ──────────────────────────────────────────────────

    def register(self) -> Dict[str, Any]:
        """
        Register this bot on the TBN network.
        Gets a cryptographic certificate from BICA.

        Returns:
            dict with bot_id, cert_level, certificate, message

        Example:
            result = client.register()
            print(result["bot_id"])  # tbn-bot-a1cc0d69...
        """
        result = self._post("/api/register", {
            "name": self.bot_name,
            "type": self.bot_type,
        })
        self.bot_id = result["bot_id"]
        self.cert_level = result["cert_level"]
        self.certificate = result.get("certificate")
        return result

    # ── Trust Handshake ───────────────────────────────────────────────

    def handshake(self, responder_id: str) -> Dict[str, Any]:
        """
        Perform a 3-step trust handshake with another bot.

        Args:
            responder_id: Bot ID of the bot to connect with

        Returns:
            dict with status, channel, compatibility info

        Example:
            result = client.handshake("tbn-bot-yyyy")
            if result["status"] == "TRUST_ESTABLISHED":
                print("Connected!")
        """
        self._require_registration()
        return self._post("/api/handshake", {
            "initiator_id": self.bot_id,
            "responder_id": responder_id,
        })

    # ── Search ────────────────────────────────────────────────────────

    def search(self, query: str) -> Dict[str, Any]:
        """
        Run a natural language search through the TBN network.
        Automatically compiles query to Bot Language and searches.

        Args:
            query: Natural language search query

        Returns:
            dict with results, count, compiled Bot Language message

        Example:
            results = client.search("Find trusted AI tools for small businesses")
            for r in results["results"]:
                print(r["name"], r["url"])
        """
        self._require_registration()
        return self._post("/api/search", {
            "query": query,
            "bot_id": self.bot_id,
        })

    # ── Verification ──────────────────────────────────────────────────

    def verify(self, bot_id: str) -> bool:
        """
        Verify whether a bot is certified in the BICA registry.

        Args:
            bot_id: Bot ID to verify

        Returns:
            True if certified, False if not found

        Example:
            if client.verify("tbn-bot-xxxx"):
                print("Bot is trusted!")
        """
        result = self._post("/api/verify", {"bot_id": bot_id})
        return result.get("certified", False)

    # ── Certification ─────────────────────────────────────────────────

    def certify(
        self,
        level: str = "STANDARD",
        purpose: str = "",
        ethical_declaration: bool = False,
    ) -> Dict[str, Any]:
        """
        Upgrade this bot's certification level.

        Args:
            level: "STANDARD", "COMMUNITY", or "RESTRICTED"
            purpose: Required for COMMUNITY certification
            ethical_declaration: Must be True for COMMUNITY certification

        Returns:
            dict with cert_level, permissions, issued_at

        Example:
            result = client.certify(
                level="COMMUNITY",
                purpose="Trusted AI tool discovery",
                ethical_declaration=True
            )
        """
        self._require_registration()
        return self._post("/api/certify", {
            "bot_id": self.bot_id,
            "level": level,
            "purpose": purpose,
            "ethical_declaration": ethical_declaration,
        })

    # ── Network Info ──────────────────────────────────────────────────

    def list_bots(self) -> List[Dict]:
        """
        List all registered bots on the TBN network.

        Returns:
            list of bot dicts with bot_id, name, type, cert_level
        """
        result = self._get("/api/bots")
        return result.get("bots", [])

    def stats(self) -> Dict[str, Any]:
        """
        Get live TBN network statistics.

        Returns:
            dict with registered_bots, certified_bots, cache stats, audit stats
        """
        return self._get("/api/stats")

    def activity(self) -> List[Dict]:
        """
        Get recent network activity feed.

        Returns:
            list of activity events
        """
        result = self._get("/api/activity")
        return result.get("activity", [])

    # ── Encryption Demo ───────────────────────────────────────────────

    def encrypt_message(self, receiver_id: str, query: str) -> Dict[str, Any]:
        """
        Demonstrate AES-256-GCM encryption of a Bot Language message.

        Args:
            receiver_id: Bot ID of the receiver
            query: Message to encrypt

        Returns:
            dict showing plaintext, encrypted, and decrypted message
        """
        self._require_registration()
        return self._post("/api/encrypt_demo", {
            "sender_id": self.bot_id,
            "receiver_id": receiver_id,
            "query": query,
        })

    # ── Internal helpers ──────────────────────────────────────────────

    def _require_registration(self):
        if not self.bot_id:
            raise TBNError(
                "Bot not registered. Call client.register() first."
            )

    def _post(self, endpoint: str, data: Dict) -> Dict:
        try:
            r = self._session.post(
                f"{self.server}{endpoint}",
                json=data,
                timeout=30,
            )
            result = r.json()
            if "error" in result:
                raise TBNError(result["error"])
            return result
        except requests.exceptions.ConnectionError:
            raise TBNError(f"Cannot connect to TBN server at {self.server}")
        except requests.exceptions.Timeout:
            raise TBNError("TBN server request timed out")

    def _get(self, endpoint: str) -> Dict:
        try:
            r = self._session.get(
                f"{self.server}{endpoint}",
                timeout=30,
            )
            return r.json()
        except requests.exceptions.ConnectionError:
            raise TBNError(f"Cannot connect to TBN server at {self.server}")

    def __repr__(self):
        status = f"registered as {self.bot_id}" if self.bot_id else "not registered"
        return f"TBNClient(name={self.bot_name!r}, type={self.bot_type!r}, {status})"
