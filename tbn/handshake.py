"""
Trust Handshake Protocol
Two bots verify each other via BICA before exchanging any data.

Flow:
  Bot A → HANDSHAKE_INIT  (sends certificate) → Bot B
  Bot B → HANDSHAKE_ACCEPT (sends certificate, verifies A) → Bot A
  Bot A → HANDSHAKE_COMPLETE (verifies B, confirms) → Bot B
  ✅ Encrypted channel established
"""

import json
import base64

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

from .identity import BotIdentity, BICA
from .bot_language import BotMessage, Intent, TrustLevel


class HandshakeError(Exception):
    pass


class TrustChannel:
    """
    Represents an established trust channel between two bots.
    After a successful handshake, bots use this to exchange messages.
    """

    def __init__(self, local_id: BotIdentity, remote_cert: dict):
        self.local_id = local_id
        self.remote_cert = remote_cert
        self.remote_bot_id = remote_cert["bot_id"]
        self._remote_public_key = serialization.load_pem_public_key(
            remote_cert["public_key_pem"].encode()
        )

    def send(self, intent: Intent, data: dict = None) -> BotMessage:
        """Create a signed BL message to send over this channel."""
        msg = BotMessage(
            sender_id=self.local_id.full_id,
            intent=intent,
            trust_level=TrustLevel.HIGH,
            data=data,
        )
        msg.sign(self.local_id)
        return msg

    def verify_incoming(self, msg: BotMessage) -> bool:
        """Verify a message came from the trusted remote bot."""
        if msg.sender_id != self.remote_bot_id:
            return False
        # Reconstruct a temporary identity-like verifier using remote public key
        raw_sig = base64.b64decode(msg.signature)
        try:
            self._remote_public_key.verify(
                raw_sig,
                msg._signable_bytes(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    def __repr__(self):
        return (
            f"<TrustChannel "
            f"{self.local_id.full_id} ↔ {self.remote_bot_id}>"
        )


class HandshakeProtocol:
    """
    Executes the 3-step TBN Trust Handshake between two bots.
    In Phase 1 this runs in-process (simulated network).
    Phase 2+ will run over HTTP/WebSocket.
    """

    def __init__(self, bica: BICA):
        self.bica = bica

    def handshake(
        self, initiator: BotIdentity, responder: BotIdentity
    ) -> tuple[TrustChannel, TrustChannel]:
        """
        Perform a full trust handshake.
        Returns (initiator_channel, responder_channel) on success.
        Raises HandshakeError on failure.
        """
        print(f"\n{'='*60}")
        print(f"TBN TRUST HANDSHAKE")
        print(f"  Initiator : {initiator.full_id} ({initiator.name})")
        print(f"  Responder : {responder.full_id} ({responder.name})")
        print(f"{'='*60}")

        # ── Step 1: Initiator sends HANDSHAKE_INIT ──────────────────
        print("\n[Step 1] Initiator → HANDSHAKE_INIT")
        init_msg = BotMessage(
            sender_id=initiator.full_id,
            intent=Intent.HANDSHAKE_INIT,
            data={"certificate": initiator.to_certificate()},
        )
        init_msg.sign(initiator)
        print(f"  Sent: {init_msg}")

        # ── Step 2: Responder verifies initiator, sends HANDSHAKE_ACCEPT ──
        print("\n[Step 2] Responder verifying initiator certificate...")
        init_cert = init_msg.payload["certificate"]

        if not self.bica.verify_certificate(init_cert):
            raise HandshakeError(
                f"Responder rejected initiator: {init_cert['bot_id']}"
            )

        # Verify message signature using initiator's public key
        initiator_pub = serialization.load_pem_public_key(
            init_cert["public_key_pem"].encode()
        )
        raw_sig = base64.b64decode(init_msg.signature)
        try:
            initiator_pub.verify(
                raw_sig,
                init_msg._signable_bytes(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            print("  ✅ Initiator signature valid")
        except Exception:
            raise HandshakeError("Initiator message signature invalid")

        accept_msg = BotMessage(
            sender_id=responder.full_id,
            intent=Intent.HANDSHAKE_ACCEPT,
            data={"certificate": responder.to_certificate()},
        )
        accept_msg.sign(responder)
        print(f"  Sent: {accept_msg}")

        # ── Step 3: Initiator verifies responder, sends HANDSHAKE_COMPLETE ──
        print("\n[Step 3] Initiator verifying responder certificate...")
        accept_cert = accept_msg.payload["certificate"]

        if not self.bica.verify_certificate(accept_cert):
            raise HandshakeError(
                f"Initiator rejected responder: {accept_cert['bot_id']}"
            )

        responder_pub = serialization.load_pem_public_key(
            accept_cert["public_key_pem"].encode()
        )
        raw_sig2 = base64.b64decode(accept_msg.signature)
        try:
            responder_pub.verify(
                raw_sig2,
                accept_msg._signable_bytes(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            print("  ✅ Responder signature valid")
        except Exception:
            raise HandshakeError("Responder message signature invalid")

        complete_msg = BotMessage(
            sender_id=initiator.full_id,
            intent=Intent.HANDSHAKE_COMPLETE,
            data={"status": "TRUST_ESTABLISHED"},
        )
        complete_msg.sign(initiator)
        print(f"  Sent: {complete_msg}")

        # ── Handshake complete — create trust channels ───────────────
        initiator_channel = TrustChannel(initiator, accept_cert)
        responder_channel = TrustChannel(responder, init_cert)

        print(f"\n{'='*60}")
        print(f"✅ TRUST ESTABLISHED")
        print(f"  {initiator_channel}")
        print(f"{'='*60}\n")

        return initiator_channel, responder_channel
