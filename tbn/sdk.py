"""
TBN SDK — Public SDK for third-party bot developers.
"Add verified identity to your AI agent in 5 lines of code."

Usage:
    from tbn.sdk import TBNClient

    client = TBNClient(bot_name="MyBot")
    client.register()
    client.connect_to("tbn-bot-xxxx")
    client.send(intent="SEARCH", data={"QUERY": "..."})
"""

from .identity import BotIdentity, BICA
from .bot import Bot
from .compiler import BotLanguageCompiler
from .bot_language import Intent, TrustLevel, BotMessage
from .handshake import HandshakeProtocol, TrustChannel
from .network import NetworkNode
from .seeded_network import SeededNetwork
from .cloning import CloneManager
from .bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot


class TBNClient:
    """
    The main entry point for the TBN SDK.
    Wraps all TBN functionality into a simple interface.

    Quick start:
        client = TBNClient(bot_name="MySearchBot")
        client.register()
        result = client.search("Find AI tools for developers")
        print(result)
    """

    VERSION = "0.1.0"

    def __init__(
        self,
        bot_name: str,
        bot_type: str = "SEARCH",
        registry_path: str = "data/bica_registry.json",
        bica: BICA = None,
        seeded_net: SeededNetwork = None,
    ):
        self.bot_name = bot_name
        self.bot_type = bot_type.upper()
        self._registry_path = registry_path
        self._bica: BICA | None = bica  # allow shared BICA
        self._bot: Bot | None = None
        self._compiler = BotLanguageCompiler()
        self._seeded_net = seeded_net or SeededNetwork()
        self._registered = False

        print(f"[TBN SDK v{self.VERSION}] Client created for '{bot_name}'")

    def register(self) -> str:
        """
        Register your bot with the TBN network.
        Returns the bot's unique ID.
        """
        if self._bica is None:
            self._bica = BICA(registry_path=self._registry_path)

        bot_classes = {
            "SEARCH":    SearchBot,
            "VALIDATOR": ValidatorBot,
            "CONNECTOR": ConnectorBot,
            "MESSENGER": MessengerBot,
        }
        cls = bot_classes.get(self.bot_type, SearchBot)
        self._bot = cls(name=self.bot_name, bica=self._bica)
        self._registered = True

        print(f"[TBN SDK] ✅ Registered: {self._bot.bot_id}")
        return self._bot.bot_id

    def search(self, query: str) -> dict:
        """
        Compile a natural language query and run it through the bot network.
        Returns validated results.
        """
        self._ensure_registered()
        assert isinstance(self._bot, SearchBot), "search() requires a SEARCH bot"

        # Check seeded cache first
        cached = self._seeded_net.lookup(query)
        if cached:
            return {"source": "cache", "results": cached, "count": len(cached)}

        # Compile and search
        msg = self._compiler.compile(query, sender_id=self._bot.bot_id, identity=self._bot.identity)
        result = self._bot.handle_request(msg)

        # Seed results back to network
        if result["RESULTS"]:
            self._seeded_net.seed(query, result["RESULTS"], self._bot.bot_id)

        return {
            "source": "search",
            "results": result["RESULTS"],
            "count": result["RESULT_COUNT"],
            "status": result["STATUS"],
        }

    def connect(self, other_client: "TBNClient") -> TrustChannel:
        """Establish a trust channel with another TBN client."""
        self._ensure_registered()
        other_client._ensure_registered()
        return self._bot.connect(other_client._bot)

    def send(self, to: "TBNClient", intent: str, data: dict = None) -> BotMessage:
        """Send a signed Bot Language message to another client."""
        self._ensure_registered()
        return self._bot.send(
            to=to._bot,
            intent=Intent(intent),
            data=data,
        )

    def receive(self, msg: BotMessage, from_client: "TBNClient") -> bool:
        """Receive and verify a message from another client."""
        self._ensure_registered()
        return self._bot.receive(msg, from_bot=from_client._bot)

    @property
    def bot_id(self) -> str:
        self._ensure_registered()
        return self._bot.bot_id

    @property
    def certificate(self) -> dict:
        """Return this bot's shareable certificate."""
        self._ensure_registered()
        return self._bot.identity.to_certificate()

    def _ensure_registered(self):
        if not self._registered:
            raise RuntimeError("Call client.register() before using the SDK.")

    def __repr__(self):
        status = self._bot.bot_id if self._registered else "unregistered"
        return f"<TBNClient name={self.bot_name!r} id={status}>"
