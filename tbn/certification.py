"""
TBN Community Bot Certification Programme
==========================================
Three certification tiers as defined in the architecture doc:

  COMMUNITY  — trusted, ethical, verified (highest access)
  STANDARD   — basic access
  RESTRICTED — limited permissions, read-only

Each tier has:
  - Access rules (what it can do)
  - Requirements (what it must prove to get certified)
  - Permissions (what platforms will grant it)

The certification level is stored in the BICA registry and
checked during the Trust Handshake — bots with incompatible
trust levels cannot establish a channel.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Callable


# ── Certification Tiers ──────────────────────────────────────────────

class CertLevel(str, Enum):
    COMMUNITY  = "COMMUNITY"   # trusted, ethical, verified
    STANDARD   = "STANDARD"    # basic access
    RESTRICTED = "RESTRICTED"  # limited, read-only
    NONE       = "NONE"        # unverified / unknown


# ── What each tier can do ────────────────────────────────────────────

CERT_PERMISSIONS = {
    CertLevel.COMMUNITY: {
        "can_search":           True,
        "can_read_private":     True,
        "can_write":            True,
        "can_clone":            True,
        "can_certify_others":   False,   # only BICA can certify
        "can_access_restricted":True,
        "max_connections":      None,    # unlimited
        "trust_compatible_with":[CertLevel.COMMUNITY, CertLevel.STANDARD],
        "description": "Trusted, ethical, verified bot. Full network access.",
    },
    CertLevel.STANDARD: {
        "can_search":           True,
        "can_read_private":     False,
        "can_write":            False,
        "can_clone":            True,
        "can_certify_others":   False,
        "can_access_restricted":False,
        "max_connections":      50,
        "trust_compatible_with":[CertLevel.COMMUNITY, CertLevel.STANDARD],
        "description": "Basic access. Public data only. Cannot access private resources.",
    },
    CertLevel.RESTRICTED: {
        "can_search":           True,
        "can_read_private":     False,
        "can_write":            False,
        "can_clone":            False,
        "can_certify_others":   False,
        "can_access_restricted":False,
        "max_connections":      10,
        "trust_compatible_with":[CertLevel.COMMUNITY],  # can only connect to Community bots
        "description": "Limited permissions. Read-only. Must route through Community Bot.",
    },
    CertLevel.NONE: {
        "can_search":           False,
        "can_read_private":     False,
        "can_write":            False,
        "can_clone":            False,
        "can_certify_others":   False,
        "can_access_restricted":False,
        "max_connections":      0,
        "trust_compatible_with":[],
        "description": "Unverified. No network access.",
    },
}


# ── Certification Requirements ───────────────────────────────────────

CERT_REQUIREMENTS = {
    CertLevel.COMMUNITY: [
        "Valid RSA key pair (2048-bit minimum)",
        "Registered in BICA registry",
        "Passed ethical use declaration",
        "Bot name and purpose declared",
        "No prior violations",
    ],
    CertLevel.STANDARD: [
        "Valid RSA key pair (2048-bit minimum)",
        "Registered in BICA registry",
        "Bot name declared",
    ],
    CertLevel.RESTRICTED: [
        "Valid RSA key pair",
        "Registered in BICA registry",
    ],
}


# ── Certificate ──────────────────────────────────────────────────────

class BotCertificate:
    """
    A bot's full certification record.
    Stored in BICA. Shared during handshake.
    """

    def __init__(
        self,
        bot_id: str,
        name: str,
        level: CertLevel,
        public_key_pem: str,
        purpose: str = "",
        ethical_declaration: bool = False,
    ):
        self.bot_id              = bot_id
        self.name                = name
        self.level               = level
        self.public_key_pem      = public_key_pem
        self.purpose             = purpose
        self.ethical_declaration = ethical_declaration
        self.issued_at           = datetime.now(timezone.utc).isoformat()
        self.tbn_version         = "0.1.0"
        self.permissions         = CERT_PERMISSIONS[level]
        self.valid               = True
        self.violation_count     = 0

    def can(self, action: str) -> bool:
        """Check if this bot is permitted to perform an action."""
        return self.permissions.get(action, False)

    def is_compatible_with(self, other: "BotCertificate") -> bool:
        """Check if this bot can establish a trust channel with another."""
        return other.level in self.permissions["trust_compatible_with"]

    def to_dict(self) -> dict:
        return {
            "bot_id":               self.bot_id,
            "name":                 self.name,
            "cert_level":           self.level.value,
            "public_key_pem":       self.public_key_pem,
            "purpose":              self.purpose,
            "ethical_declaration":  self.ethical_declaration,
            "issued_at":            self.issued_at,
            "tbn_version":          self.tbn_version,
            "valid":                self.valid,
            "violation_count":      self.violation_count,
            "permissions": {
                k: v for k, v in self.permissions.items()
                if k != "trust_compatible_with"
            },
        }

    def __repr__(self):
        badge = {"COMMUNITY": "🟢", "STANDARD": "🔵", "RESTRICTED": "🟡", "NONE": "🔴"}
        return (
            f"<BotCertificate {badge.get(self.level.value,'?')} "
            f"{self.level.value} | {self.name} | {self.bot_id[:20]}...>"
        )


# ── Certification Authority ──────────────────────────────────────────

class CertificationAuthority:
    """
    Issues, verifies, and revokes bot certificates.
    This is the certification arm of BICA.

    In Phase 4+: this becomes a public HTTP endpoint.
    For now: in-memory + JSON persistence via BICA.
    """

    def __init__(self, bica):
        self.bica = bica
        self._certs: dict[str, BotCertificate] = {}
        self._issued_count   = 0
        self._revoked_count  = 0
        self._violation_count = 0

    def certify(
        self,
        identity,
        level: CertLevel = CertLevel.STANDARD,
        purpose: str = "",
        ethical_declaration: bool = False,
    ) -> BotCertificate:
        """
        Issue a certificate to a bot.
        Validates requirements before issuing.
        """
        # Validate requirements
        if level == CertLevel.COMMUNITY and not ethical_declaration:
            raise ValueError(
                "Community Bot certification requires ethical_declaration=True"
            )
        if level == CertLevel.COMMUNITY and not purpose:
            raise ValueError(
                "Community Bot certification requires a purpose declaration"
            )

        cert = BotCertificate(
            bot_id=identity.full_id,
            name=identity.name,
            level=level,
            public_key_pem=identity.public_key_pem().decode(),
            purpose=purpose,
            ethical_declaration=ethical_declaration,
        )

        self._certs[identity.full_id] = cert
        self._issued_count += 1

        # Update BICA registry with cert level
        if identity.full_id in self.bica._registry:
            self.bica._registry[identity.full_id]["cert_level"] = level.value
            self.bica._registry[identity.full_id]["purpose"]    = purpose
            self.bica._save()

        badge = {"COMMUNITY": "🟢", "STANDARD": "🔵", "RESTRICTED": "🟡"}
        print(
            f"[CA] {badge.get(level.value,'?')} Certified: {identity.name} "
            f"as {level.value} Bot"
        )
        return cert

    def get_cert(self, bot_id: str) -> BotCertificate | None:
        """Retrieve a bot's certificate."""
        return self._certs.get(bot_id)

    def get_level(self, bot_id: str) -> CertLevel:
        """Get a bot's certification level. Returns NONE if not certified."""
        cert = self._certs.get(bot_id)
        return cert.level if cert else CertLevel.NONE

    def revoke(self, bot_id: str, reason: str = "") -> None:
        """Revoke a bot's certificate."""
        cert = self._certs.get(bot_id)
        if cert:
            cert.valid = False
            self._revoked_count += 1
            print(f"[CA] 🔴 Revoked: {cert.name} | Reason: {reason}")
            self.bica.revoke(bot_id)

    def report_violation(self, bot_id: str, violation: str) -> None:
        """Record a violation against a bot."""
        cert = self._certs.get(bot_id)
        if cert:
            cert.violation_count += 1
            self._violation_count += 1
            print(
                f"[CA] ⚠️  Violation #{cert.violation_count} "
                f"for {cert.name}: {violation}"
            )
            # Auto-revoke after 3 violations
            if cert.violation_count >= 3:
                self.revoke(bot_id, reason="3 violations — auto-revoked")

    def check_compatibility(
        self, bot_a_id: str, bot_b_id: str
    ) -> tuple[bool, str]:
        """
        Check if two bots are trust-compatible.
        Bidirectional — if A accepts B, or B accepts A, they can connect.
        Called during the handshake before establishing a channel.
        Returns (compatible: bool, reason: str).
        """
        cert_a = self._certs.get(bot_a_id)
        cert_b = self._certs.get(bot_b_id)

        if not cert_a:
            return False, f"{bot_a_id[:20]}... has no certificate"
        if not cert_b:
            return False, f"{bot_b_id[:20]}... has no certificate"
        if not cert_a.valid:
            return False, f"{cert_a.name} certificate is revoked"
        if not cert_b.valid:
            return False, f"{cert_b.name} certificate is revoked"

        # Bidirectional check — either side can accept the other
        a_accepts_b = cert_a.is_compatible_with(cert_b)
        b_accepts_a = cert_b.is_compatible_with(cert_a)

        if a_accepts_b or b_accepts_a:
            return True, (
                f"{cert_a.name} ({cert_a.level.value}) ↔ "
                f"{cert_b.name} ({cert_b.level.value}) — compatible"
            )

        return False, (
            f"{cert_a.name} ({cert_a.level.value}) is not compatible "
            f"with {cert_b.name} ({cert_b.level.value})"
        )

    def list_certified(self, level: CertLevel = None) -> list[BotCertificate]:
        """List all certified bots, optionally filtered by level."""
        certs = list(self._certs.values())
        if level:
            certs = [c for c in certs if c.level == level]
        return certs

    def stats(self) -> dict:
        by_level = {}
        for level in CertLevel:
            by_level[level.value] = len([
                c for c in self._certs.values() if c.level == level
            ])
        return {
            "total_issued":   self._issued_count,
            "total_revoked":  self._revoked_count,
            "total_violations": self._violation_count,
            "by_level":       by_level,
        }
