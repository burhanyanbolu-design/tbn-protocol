"""
TBN Protocol — Trusted Bot Network
A trust and identity layer for AI agents.

Quick start (SDK):
    from tbn.sdk import TBNClient

    client = TBNClient(bot_name="MyBot")
    client.register()
    result = client.search("Find AI tools for developers")

Full protocol:
    from tbn.identity import BICA, BotIdentity
    from tbn.bot import Bot
    from tbn.bot_language import BotMessage, Intent, TrustLevel
    from tbn.handshake import HandshakeProtocol
    from tbn.compiler import BotLanguageCompiler
    from tbn.bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot
    from tbn.network import NetworkNode
    from tbn.cloning import CloneManager
    from tbn.seeded_network import SeededNetwork
    from tbn.platform_integration import PlatformAdapter, PublicBICARegistry
    from tbn.sdk import TBNClient
"""

__version__ = "0.1.0"
__author__ = "Burhan Yanbolu"
__description__ = "Trusted Bot Network — trust and identity protocol for AI agents"
