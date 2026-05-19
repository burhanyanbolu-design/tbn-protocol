"""
Messenger Bot — routes Bot Language messages between bots in the network.
Acts as a trusted relay: verifies sender, forwards to correct recipient.
In Phase 3 this becomes the distributed routing layer.
"""

from ..bot import Bot
from ..bot_language import BotMessage, Intent, TrustLevel
from ..identity import BICA


class MessengerBot(Bot):
    """
    Specialised bot for routing messages between other bots.
    Maintains a routing table: bot_id → Bot instance.
    Verifies message integrity before forwarding.
    """

    BOT_TYPE = "MESSENGER"

    def __init__(self, name: str, bica: BICA, ca=None, **kwargs):
        super().__init__(name, bica, ca=ca, **kwargs)
        self._routing_table: dict[str, object] = {}  # bot_id → Bot
        self._forwarded_count = 0
        self._rejected_count = 0

    def register_route(self, bot) -> None:
        """Register a bot in the routing table."""
        self._routing_table[bot.bot_id] = bot
        print(f"[{self.name}] Route registered: {bot.bot_id} ({bot.name})")

    def route(self, msg: BotMessage, from_bot, to_bot_id: str) -> bool:
        """
        Forward a message from one bot to another.
        Verifies the message is from a trusted sender before forwarding.
        Returns True if forwarded, False if rejected.
        """
        # Check sender has a channel with us
        channel = self._channels.get(from_bot.bot_id)
        if not channel:
            print(f"[{self.name}] ❌ Rejected: no channel with {from_bot.bot_id}")
            self._rejected_count += 1
            return False

        # Verify message signature
        if not channel.verify_incoming(msg):
            print(f"[{self.name}] ❌ Rejected: invalid signature from {from_bot.bot_id}")
            self._rejected_count += 1
            return False

        # Look up destination
        destination = self._routing_table.get(to_bot_id)
        if not destination:
            print(f"[{self.name}] ❌ Unknown destination: {to_bot_id}")
            self._rejected_count += 1
            return False

        print(f"[{self.name}] → Forwarding {msg.payload['INTENT']} to {destination.name}")
        self._forwarded_count += 1
        return True

    def broadcast(self, msg: BotMessage, from_bot, exclude: list = None) -> int:
        """
        Broadcast a message to all registered bots except the sender.
        Returns the number of bots the message was forwarded to.
        """
        exclude_ids = {from_bot.bot_id}
        if exclude:
            exclude_ids.update(b.bot_id for b in exclude)

        count = 0
        for bot_id, bot in self._routing_table.items():
            if bot_id not in exclude_ids:
                if self.route(msg, from_bot, bot_id):
                    count += 1
        return count

    def stats(self) -> dict:
        return {
            "routes": len(self._routing_table),
            "forwarded": self._forwarded_count,
            "rejected": self._rejected_count,
        }

    def __repr__(self):
        return (
            f"<MessengerBot name={self.name!r} "
            f"routes={len(self._routing_table)} "
            f"forwarded={self._forwarded_count}>"
        )
