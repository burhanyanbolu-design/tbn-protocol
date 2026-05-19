"""
BICA - Bot Identity & Certification Authority
Each bot gets a unique cryptographic identity: UUID + RSA key pair.
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization


class BotIdentity:
    """
    Represents a bot's cryptographic identity.
    Every bot on the TBN network has one of these.
    """

    def __init__(self, name: str, icon_url: str = None):
        self.name = name
        self.icon_url = icon_url  # URL to bot's brand icon (SVG/PNG)
        self.created_at = datetime.now(timezone.utc).isoformat()

        # Generate RSA key pair
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public_key = self._private_key.public_key()

        # Derive bot ID from public key fingerprint
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.bot_id = hashlib.sha256(pub_bytes).hexdigest()[:16]
        self.full_id = f"tbn-bot-{self.bot_id}"

    # ------------------------------------------------------------------
    # Signing & verification
    # ------------------------------------------------------------------

    def sign(self, data: bytes) -> bytes:
        """Sign data with this bot's private key."""
        return self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify a signature using this bot's public key."""
        try:
            self._public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public key export (shared with other bots during handshake)
    # ------------------------------------------------------------------

    def public_key_pem(self) -> bytes:
        """Export public key as PEM bytes — safe to share."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def to_certificate(self) -> dict:
        """
        Returns a shareable certificate (no private key).
        This is what gets exchanged during the trust handshake.
        Includes icon_url for visual branding in dashboards/logs.
        """
        cert = {
            "bot_id": self.full_id,
            "name": self.name,
            "icon_url": self.icon_url,
            "public_key_pem": self.public_key_pem().decode(),
            "created_at": self.created_at,
            "tbn_version": "0.1.0",
        }
        return cert

    def __repr__(self):
        return f"<BotIdentity name={self.name!r} id={self.full_id}>"


class BICA:
    """
    Bot Identity & Certification Authority.
    Maintains a registry of verified bots and issues/revokes trust.
    Phase 1: in-memory registry.
    Phase 2: optional JSON persistence via registry_path.
    """

    def __init__(self, registry_path: str = None):
        self._registry: dict[str, dict] = {}
        self._registry_path = registry_path
        if registry_path:
            self._load()

    def register(self, identity: BotIdentity) -> None:
        """Register a bot's certificate in the trust registry."""
        cert = identity.to_certificate()
        self._registry[cert["bot_id"]] = cert
        print(f"[BICA] Registered: {cert['bot_id']} ({cert['name']})")
        self._save()

    def verify_certificate(self, cert: dict) -> bool:
        """Check if a certificate is in the registry."""
        bot_id = cert.get("bot_id")
        if bot_id in self._registry:
            print(f"[BICA] ✅ Verified: {bot_id}")
            return True
        print(f"[BICA] ❌ Unknown bot: {bot_id}")
        return False

    def revoke(self, bot_id: str) -> None:
        """Remove a bot from the trust registry."""
        if bot_id in self._registry:
            del self._registry[bot_id]
            print(f"[BICA] Revoked: {bot_id}")
            self._save()

    def list_bots(self) -> list[dict]:
        """Return all registered bot certificates."""
        return list(self._registry.values())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        """Save registry to JSON file if a path was provided."""
        if not self._registry_path:
            return
        import json, os
        os.makedirs(os.path.dirname(self._registry_path) or ".", exist_ok=True)
        with open(self._registry_path, "w") as f:
            json.dump(self._registry, f, indent=2)

    def _load(self) -> None:
        """Load registry from JSON file if it exists."""
        import json, os
        if os.path.exists(self._registry_path):
            with open(self._registry_path) as f:
                self._registry = json.load(f)
            print(f"[BICA] Loaded {len(self._registry)} bots from {self._registry_path}")
