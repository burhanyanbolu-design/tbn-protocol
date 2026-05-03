"""
TBN Network Node
Represents a single node in the distributed TBN network.
Each node runs locally and can connect to other nodes.
In Phase 3 these run on separate AWS Lightsail instances.
For now they run as separate processes/threads on one machine.

Network topology:
    Node A (London) ←→ Node B (New York) ←→ Node C (Singapore)
         ↕                    ↕                    ↕
    [Bot Army]           [Bot Army]           [Bot Army]
"""

import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from .identity import BICA, BotIdentity
from .bot_language import BotMessage, Intent, TrustLevel
from .bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot


class NetworkNode:
    """
    A TBN network node — runs a local bot army and connects to peer nodes.
    Handles:
      - Local bot registry
      - Peer node connections
      - Message routing between nodes
      - Load monitoring (triggers cloning when overloaded)
    """

    def __init__(self, node_id: str, location: str, bica: BICA):
        self.node_id = node_id
        self.location = location
        self.bica = bica
        self.created_at = datetime.now(timezone.utc).isoformat()

        self._bots: dict[str, object] = {}       # bot_id → Bot
        self._peers: dict[str, "NetworkNode"] = {}  # node_id → Node
        self._message_queue: list[BotMessage] = []
        self._lock = threading.Lock()
        self._message_count = 0
        self._routed_count = 0

        print(f"[Node:{self.node_id}] Online at {self.location}")

    def add_bot(self, bot) -> None:
        """Register a bot on this node."""
        self._bots[bot.bot_id] = bot
        print(f"[Node:{self.node_id}] Bot joined: {bot.name} ({bot.bot_id})")

    def connect_peer(self, peer: "NetworkNode") -> None:
        """Connect this node to a peer node."""
        self._peers[peer.node_id] = peer
        peer._peers[self.node_id] = self
        print(f"[Node:{self.node_id}] ↔ Peered with Node:{peer.node_id} ({peer.location})")

    def route_message(self, msg: BotMessage, target_bot_id: str) -> bool:
        """
        Route a message to a bot — either local or on a peer node.
        Returns True if delivered, False if bot not found anywhere.
        """
        # Check local bots first
        if target_bot_id in self._bots:
            self._message_count += 1
            print(f"[Node:{self.node_id}] Local delivery → {target_bot_id[:20]}...")
            return True

        # Check peer nodes
        for peer_id, peer in self._peers.items():
            if target_bot_id in peer._bots:
                self._routed_count += 1
                print(
                    f"[Node:{self.node_id}] Remote delivery → "
                    f"Node:{peer_id} ({peer.location}) → {target_bot_id[:20]}..."
                )
                peer._message_count += 1
                return True

        print(f"[Node:{self.node_id}] ❌ Bot not found: {target_bot_id}")
        return False

    def find_bot_by_type(self, bot_type: str) -> object | None:
        """Find the first bot of a given type on this node or peers."""
        # Local first
        for bot in self._bots.values():
            if getattr(bot, "BOT_TYPE", None) == bot_type:
                return bot
        # Then peers
        for peer in self._peers.values():
            for bot in peer._bots.values():
                if getattr(bot, "BOT_TYPE", None) == bot_type:
                    return bot
        return None

    def load(self) -> float:
        """
        Returns current load as a float 0.0–1.0.
        Based on queue size relative to capacity.
        """
        capacity = 100
        return min(len(self._message_queue) / capacity, 1.0)

    def stats(self) -> dict:
        return {
            "node_id": self.node_id,
            "location": self.location,
            "bots": len(self._bots),
            "peers": len(self._peers),
            "messages_handled": self._message_count,
            "messages_routed": self._routed_count,
            "load": self.load(),
        }

    def __repr__(self):
        return f"<NetworkNode id={self.node_id} location={self.location!r} bots={len(self._bots)}>"
