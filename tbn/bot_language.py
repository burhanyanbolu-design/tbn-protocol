"""
Bot Language (BL) — the communication protocol for TBN agents.
Structured, signed JSON messages. Think: "the language bots speak natively."
"""

import json
import uuid
import base64
from datetime import datetime, timezone
from enum import Enum


class Intent(str, Enum):
    SEARCH = "SEARCH"
    HANDSHAKE_INIT = "HANDSHAKE_INIT"
    HANDSHAKE_ACCEPT = "HANDSHAKE_ACCEPT"
    HANDSHAKE_COMPLETE = "HANDSHAKE_COMPLETE"
    DATA_REQUEST = "DATA_REQUEST"
    DATA_RESPONSE = "DATA_RESPONSE"
    ERROR = "ERROR"
    PING = "PING"
    PONG = "PONG"


class TrustLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class BotMessage:
    """
    A single Bot Language message.

    Structure:
    {
        "bl_version": "1.0",
        "message_id": "<uuid>",
        "sender_id": "<bot_id>",
        "timestamp": "<iso8601>",
        "signature": "<base64 RSA signature>",
        "payload": {
            "INTENT": "...",
            "TRUST_LEVEL": "...",
            ...
        }
    }
    """

    BL_VERSION = "1.0"

    def __init__(
        self,
        sender_id: str,
        intent: Intent,
        trust_level: TrustLevel = TrustLevel.HIGH,
        data: dict = None,
    ):
        self.bl_version = self.BL_VERSION
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.signature: str | None = None

        self.payload = {
            "INTENT": intent.value,
            "TRUST_LEVEL": trust_level.value,
            **(data or {}),
        }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _signable_bytes(self) -> bytes:
        """Canonical bytes used for signing (excludes signature field)."""
        doc = {
            "bl_version": self.bl_version,
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
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

    def to_dict(self) -> dict:
        return {
            "bl_version": self.bl_version,
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "payload": self.payload,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "BotMessage":
        msg = cls.__new__(cls)
        msg.bl_version = data["bl_version"]
        msg.message_id = data["message_id"]
        msg.sender_id = data["sender_id"]
        msg.timestamp = data["timestamp"]
        msg.signature = data.get("signature")
        msg.payload = data["payload"]
        return msg

    def __repr__(self):
        intent = self.payload.get("INTENT", "?")
        return f"<BotMessage intent={intent} from={self.sender_id} id={self.message_id[:8]}>"
