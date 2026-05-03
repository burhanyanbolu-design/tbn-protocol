"""
External Platform Integration
Allows external platforms (GitHub, Notion, Slack, APIs) to:
  - Verify incoming bot requests
  - Grant conditional access based on bot certification level
  - Log all bot activity for audit trail

The Connector Bot acts as the built-in interpreter —
external platforms never need to install anything.

Flow:
    Bot A → [Bot Language] → Connector Bot → [REST API] → Platform
                             (built-in interpreter)

For platforms that WANT to integrate natively, they install
the lightweight PlatformAdapter which verifies bot certificates
against the public BICA registry.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Callable


class AccessLevel:
    """Defines what a bot can do on a platform."""
    READ_PUBLIC  = "READ_PUBLIC"
    READ_PRIVATE = "READ_PRIVATE"
    WRITE        = "WRITE"
    ADMIN        = "ADMIN"


class BotRequest:
    """
    Represents an incoming request from a bot to a platform.
    The platform uses this to decide whether to grant access.
    """

    def __init__(
        self,
        bot_id: str,
        certificate: dict,
        intent: str,
        resource: str,
        signature: str = None,
    ):
        self.bot_id = bot_id
        self.certificate = certificate
        self.intent = intent
        self.resource = resource
        self.signature = signature
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.request_id = hashlib.sha256(
            f"{bot_id}{resource}{self.timestamp}".encode()
        ).hexdigest()[:12]


class AuditLog:
    """
    Immutable audit trail of all bot activity on a platform.
    Every access attempt is logged — granted or denied.
    This is the compliance layer for enterprise customers.
    """

    def __init__(self):
        self._entries: list[dict] = []

    def log(
        self,
        request: BotRequest,
        granted: bool,
        reason: str = "",
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "bot_id": request.bot_id,
            "intent": request.intent,
            "resource": request.resource,
            "granted": granted,
            "reason": reason,
        }
        self._entries.append(entry)
        status = "✅ GRANTED" if granted else "❌ DENIED"
        print(
            f"[AuditLog] {status} | bot={request.bot_id[:20]}... | "
            f"resource={request.resource} | {reason}"
        )

    def entries(self) -> list[dict]:
        return list(self._entries)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2)

    def stats(self) -> dict:
        granted = sum(1 for e in self._entries if e["granted"])
        denied = len(self._entries) - granted
        return {
            "total_requests": len(self._entries),
            "granted": granted,
            "denied": denied,
            "grant_rate": f"{granted / len(self._entries):.0%}" if self._entries else "0%",
        }


class PlatformAdapter:
    """
    Lightweight adapter that platforms install to verify TBN bots.
    Checks bot certificates against the BICA registry before granting access.

    Platforms using this:
      - GitHub (verify bots before repo access)
      - Notion (verify bots before workspace access)
      - Any REST API wanting certified-bot-only access

    Usage (on the platform side):
        adapter = PlatformAdapter(name="GitHub", bica=bica)
        adapter.add_permission_rule("READ_PUBLIC",  lambda cert: True)
        adapter.add_permission_rule("READ_PRIVATE", lambda cert: cert.get("trust_level") == "HIGH")

        granted, level = adapter.verify_request(bot_request)
    """

    def __init__(self, name: str, bica, require_certification: bool = True):
        self.name = name
        self.bica = bica
        self.require_certification = require_certification
        self.audit_log = AuditLog()
        self._permission_rules: dict[str, Callable] = {}
        self._request_count = 0

        # Default rules
        self.add_permission_rule(
            AccessLevel.READ_PUBLIC,
            lambda cert: True,  # any registered bot
        )
        self.add_permission_rule(
            AccessLevel.READ_PRIVATE,
            lambda cert: cert.get("tbn_version") is not None,  # certified bots
        )
        self.add_permission_rule(
            AccessLevel.WRITE,
            lambda cert: False,  # disabled by default — platform must enable
        )

        print(f"[Platform:{self.name}] Adapter initialised")

    def add_permission_rule(self, access_level: str, rule: Callable) -> None:
        """Add a custom permission rule for an access level."""
        self._permission_rules[access_level] = rule

    def verify_request(self, request: BotRequest) -> tuple[bool, str]:
        """
        Verify an incoming bot request.
        Returns (granted: bool, access_level: str).
        """
        self._request_count += 1
        cert = request.certificate

        # Step 1: Check bot is registered in BICA
        if self.require_certification:
            if not self.bica.verify_certificate(cert):
                self.audit_log.log(request, False, "Bot not in BICA registry")
                return False, AccessLevel.READ_PUBLIC

        # Step 2: Determine access level based on intent
        intent_to_level = {
            "SEARCH":       AccessLevel.READ_PUBLIC,
            "DATA_REQUEST": AccessLevel.READ_PUBLIC,
            "DATA_RESPONSE":AccessLevel.READ_PUBLIC,
            "WRITE":        AccessLevel.WRITE,
            "ADMIN":        AccessLevel.ADMIN,
        }
        required_level = intent_to_level.get(request.intent, AccessLevel.READ_PUBLIC)

        # Step 3: Apply permission rule
        rule = self._permission_rules.get(required_level)
        if rule and rule(cert):
            self.audit_log.log(request, True, f"Access level: {required_level}")
            return True, required_level

        self.audit_log.log(request, False, f"Permission denied for {required_level}")
        return False, required_level

    def stats(self) -> dict:
        return {
            "platform": self.name,
            "total_requests": self._request_count,
            **self.audit_log.stats(),
        }

    def __repr__(self):
        return f"<PlatformAdapter name={self.name!r} requests={self._request_count}>"


class PublicBICARegistry:
    """
    Public BICA Registry — the global trust registry for the TBN network.
    In Phase 4 this is a public HTTP endpoint.
    For now it wraps the local BICA and exposes a public API interface.

    Future: hosted at https://registry.tbn-protocol.io/bots/{bot_id}
    """

    def __init__(self, bica):
        self.bica = bica
        self._lookup_count = 0

    def lookup(self, bot_id: str) -> dict | None:
        """Look up a bot certificate by ID. Returns None if not found."""
        self._lookup_count += 1
        cert = self.bica._registry.get(bot_id)
        if cert:
            print(f"[PublicRegistry] Found: {bot_id}")
        else:
            print(f"[PublicRegistry] Not found: {bot_id}")
        return cert

    def is_certified(self, bot_id: str) -> bool:
        """Quick check — is this bot certified?"""
        return bot_id in self.bica._registry

    def all_certified_bots(self) -> list[dict]:
        """Return all certified bots (public certificates only)."""
        return [
            {
                "bot_id": c["bot_id"],
                "name": c["name"],
                "tbn_version": c.get("tbn_version"),
                "created_at": c.get("created_at", "")[:10],
            }
            for c in self.bica.list_bots()
        ]

    def stats(self) -> dict:
        return {
            "total_certified_bots": len(self.bica._registry),
            "total_lookups": self._lookup_count,
        }
