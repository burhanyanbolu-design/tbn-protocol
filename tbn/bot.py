"""
Base Bot class — the building block for all TBN agents.
"""

from .identity import BotIdentity, BICA
from .bot_language import BotMessage, Intent, TrustLevel
from .handshake import HandshakeProtocol, TrustChannel, HandshakeError


class Bot:
    """
    A TBN-enabled AI agent.
    Has a cryptographic identity, can perform trust handshakes,
    and exchange verified Bot Language messages.
    """

    def __init__(self, name: str, bica: BICA, ca=None):
        self.name = name
        self.bica = bica
        self.ca = ca  # CertificationAuthority (optional)
        self.identity = BotIdentity(name)
        self._channels: dict[str, TrustChannel] = {}

        # Register with BICA on creation
        self.bica.register(self.identity)

    @property
    def bot_id(self) -> str:
        return self.identity.full_id

    def connect(self, other: "Bot") -> TrustChannel:
        """
        Initiate a trust handshake with another bot.
        If a CertificationAuthority is set, cert compatibility is checked first.
        Returns the established TrustChannel.
        """
        protocol = HandshakeProtocol(self.bica, ca=self.ca or other.ca)
        my_channel, their_channel = protocol.handshake(
            initiator=self.identity,
            responder=other.identity,
        )
        self._channels[other.bot_id] = my_channel
        other._channels[self.bot_id] = their_channel
        return my_channel

    def send(self, to: "Bot", intent: Intent, data: dict = None) -> BotMessage:
        """Send a signed BL message to a trusted bot."""
        channel = self._channels.get(to.bot_id)
        if not channel:
            raise HandshakeError(
                f"No trust channel with {to.bot_id}. Run connect() first."
            )
        msg = channel.send(intent, data)
        print(f"[{self.name}] → [{to.name}] {msg.payload['INTENT']}")
        if data:
            for k, v in data.items():
                print(f"    {k}: {v}")
        return msg

    def receive(self, msg: BotMessage, from_bot: "Bot") -> bool:
        """Receive and verify a message from a trusted bot."""
        channel = self._channels.get(from_bot.bot_id)
        if not channel:
            print(f"[{self.name}] ❌ No channel with {from_bot.bot_id}")
            return False
        valid = channel.verify_incoming(msg)
        status = "✅" if valid else "❌"
        print(f"[{self.name}] {status} Received {msg.payload['INTENT']} from [{from_bot.name}]")
        return valid

    def __repr__(self):
        return f"<Bot name={self.name!r} id={self.bot_id}>"
