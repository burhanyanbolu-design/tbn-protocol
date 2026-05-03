"""
Bot Language (BL) v2.0
The native communication protocol for TBN agents.

v2 adds:
  - AES-256-GCM payload encryption (end-to-end)
  - RSA-encrypted session key per message
  - receiver_id field (required for encryption)
  - TARGET field in payload
  - payload_hash for integrity verification
  - Backward-compatible with v1 (unencrypted) messages

Think: JSON + AES encryption + RSA signatures + intent logic
"""

import json
import uuid
import base64
import hashlib
import os
from datetime import datetime, timezone
from enum import Enum

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ── Enums ────────────────────────────────────────────────────────────

class Intent(str, Enum):
    SEARCH            = "SEARCH"
    HANDSHAKE_INIT    = "HANDSHAKE_INIT"
    HANDSHAKE_ACCEPT  = "HANDSHAKE_ACCEPT"
    HANDSHAKE_COMPLETE= "HANDSHAKE_COMPLETE"
    DATA_REQUEST      = "DATA_REQUEST"
    DATA_RESPONSE     = "DATA_RESPONSE"
    VALIDATE          = "VALIDATE"
    VALIDATE_RESPONSE = "VALIDATE_RESPONSE"
    COMPILE           = "COMPILE"
    COMPILE_RESPONSE  = "COMPILE_RESPONSE"
    PING              = "PING"
    PONG              = "PONG"
    ERROR             = "ERROR"
    CLONE_REQUEST     = "CLONE_REQUEST"
    CLONE_READY       = "CLONE_READY"


class TrustLevel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"
    NONE   = "NONE"


class Target(str, Enum):
    VERIFIED_SOURCES = "VERIFIED_SOURCES"
    PUBLIC_SOURCES   = "PUBLIC_SOURCES"
    RESTRICTED       = "RESTRICTED"
    NETWORK          = "NETWORK"
    PLATFORM         = "PLATFORM"


class DataType(str, Enum):
    AI_TOOLS = "AI_TOOLS"
    CODE     = "CODE"
    DATA     = "DATA"
    DOCS     = "DOCS"
    NEWS     = "NEWS"
    GENERAL  = "GENERAL"


# ── BL v2 Message ────────────────────────────────────────────────────

class BotMessage:
    """
    A Bot Language v2 message.

    Envelope (plaintext — routing):
      bl_version, message_id, sender_id, receiver_id,
      timestamp, signature, encrypted, session_key, payload_hash

    Payload (AES-256-GCM encrypted when receiver_id is set):
      INTENT, TARGET, TRUST_LEVEL, DATA_TYPE, QUERY, FILTERS,
      PRIORITY, RESPONSE, ...custom fields
    """

    BL_VERSION = "2.0"

    def __init__(
        self,
        sender_id: str,
        intent: Intent,
        trust_level: TrustLevel = TrustLevel.HIGH,
        target: Target = Target.VERIFIED_SOURCES,
        data: dict = None,
        receiver_id: str = None,
    ):
        self.bl_version  = self.BL_VERSION
        self.message_id  = str(uuid.uuid4())
        self.sender_id   = sender_id
        self.receiver_id = receiver_id
        self.timestamp   = datetime.now(timezone.utc).isoformat()
        self.signature: str | None = None
        self.encrypted   = False
        self.session_key: str | None = None   # RSA-encrypted AES key (b64)
        self.payload_hash: str | None = None  # SHA-256 of plaintext payload

        # Plaintext payload (encrypted before sending if receiver_id set)
        self._plaintext_payload = {
            "INTENT":      intent.value,
            "TARGET":      target.value,
            "TRUST_LEVEL": trust_level.value,
            **(data or {}),
        }
        # After encryption this holds the base64 ciphertext
        self._payload_ciphertext: str | None = None

    # ── Payload access ───────────────────────────────────────────────

    @property
    def payload(self) -> dict:
        """Always returns the plaintext payload dict."""
        return self._plaintext_payload

    # ── Encryption ───────────────────────────────────────────────────

    def encrypt(self, receiver_public_key_pem: bytes) -> None:
        """
        Encrypt the payload with AES-256-GCM.
        The AES session key is encrypted with the receiver's RSA public key.
        """
        # 1. Serialise plaintext payload
        plaintext = json.dumps(self._plaintext_payload, sort_keys=True).encode()

        # 2. Compute payload hash (integrity check)
        self.payload_hash = hashlib.sha256(plaintext).hexdigest()

        # 3. Generate random 256-bit AES session key + 96-bit nonce
        aes_key = os.urandom(32)
        nonce   = os.urandom(12)

        # 4. Encrypt payload with AES-256-GCM
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # 5. Store nonce + ciphertext together (nonce is needed for decryption)
        self._payload_ciphertext = base64.b64encode(nonce + ciphertext).decode()

        # 6. Encrypt AES key with receiver's RSA public key
        receiver_pub = serialization.load_pem_public_key(receiver_public_key_pem)
        encrypted_key = receiver_pub.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        self.session_key = base64.b64encode(encrypted_key).decode()
        self.encrypted = True

    def decrypt(self, receiver_private_key) -> bool:
        """
        Decrypt the payload using the receiver's private key.
        Returns True on success, False on failure.
        """
        if not self.encrypted or not self._payload_ciphertext:
            return True  # already plaintext

        try:
            # 1. Decrypt AES session key with receiver's RSA private key
            encrypted_key = base64.b64decode(self.session_key)
            aes_key = receiver_private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # 2. Decrypt payload with AES-256-GCM
            raw = base64.b64decode(self._payload_ciphertext)
            nonce      = raw[:12]
            ciphertext = raw[12:]
            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # 3. Verify integrity
            actual_hash = hashlib.sha256(plaintext).hexdigest()
            if actual_hash != self.payload_hash:
                return False

            # 4. Restore plaintext payload
            self._plaintext_payload = json.loads(plaintext.decode())
            self.encrypted = False
            return True

        except Exception:
            return False

    # ── Signing ──────────────────────────────────────────────────────

    def _signable_bytes(self) -> bytes:
        """Canonical bytes for signing — covers envelope fields."""
        doc = {
            "bl_version":   self.bl_version,
            "message_id":   self.message_id,
            "sender_id":    self.sender_id,
            "receiver_id":  self.receiver_id,
            "timestamp":    self.timestamp,
            "payload_hash": self.payload_hash or hashlib.sha256(
                json.dumps(self._plaintext_payload, sort_keys=True).encode()
            ).hexdigest(),
        }
        return json.dumps(doc, sort_keys=True).encode()

    def sign(self, identity) -> None:
        """Sign this message with the sender's private key."""
        raw_sig = identity.sign(self._signable_bytes())
        self.signature = base64.b64encode(raw_sig).decode()

    def verify_signature(self, identity) -> bool:
        """Verify the message signature using the sender's identity."""
        if not self.signature:
            return False
        raw_sig = base64.b64decode(self.signature)
        return identity.verify(self._signable_bytes(), raw_sig)

    # ── Serialisation ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise to dict. Payload is ciphertext if encrypted."""
        return {
            "bl_version":   self.bl_version,
            "message_id":   self.message_id,
            "sender_id":    self.sender_id,
            "receiver_id":  self.receiver_id,
            "timestamp":    self.timestamp,
            "signature":    self.signature,
            "encrypted":    self.encrypted,
            "session_key":  self.session_key,
            "payload_hash": self.payload_hash,
            "payload": (
                self._payload_ciphertext
                if self.encrypted
                else self._plaintext_payload
            ),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "BotMessage":
        msg = cls.__new__(cls)
        msg.bl_version   = data["bl_version"]
        msg.message_id   = data["message_id"]
        msg.sender_id    = data["sender_id"]
        msg.receiver_id  = data.get("receiver_id")
        msg.timestamp    = data["timestamp"]
        msg.signature    = data.get("signature")
        msg.encrypted    = data.get("encrypted", False)
        msg.session_key  = data.get("session_key")
        msg.payload_hash = data.get("payload_hash")

        if msg.encrypted:
            msg._payload_ciphertext = data["payload"]
            msg._plaintext_payload  = {}
        else:
            msg._plaintext_payload  = data.get("payload", {})
            msg._payload_ciphertext = None
        return msg

    def __repr__(self):
        intent = self._plaintext_payload.get("INTENT", "?")
        enc    = "🔒" if self.encrypted else "🔓"
        return (
            f"<BotMessage v{self.bl_version} {enc} "
            f"intent={intent} "
            f"from={self.sender_id[:20]}... "
            f"id={self.message_id[:8]}>"
        )
