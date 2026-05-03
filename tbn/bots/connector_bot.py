"""
Connector Bot — bridges the TBN network to external platforms.
Translates Bot Language → platform API calls (GitHub, REST APIs etc.)
External platforms never need to install anything — the Connector Bot
acts as the built-in interpreter.

    Bot A → [Bot Language] → Connector Bot → [REST API] → GitHub
                             (built-in interpreter)
"""

import json
import urllib.request
import urllib.error
from ..bot import Bot
from ..bot_language import BotMessage, Intent, TrustLevel
from ..identity import BICA


class ConnectorBot(Bot):
    """
    Specialised bot for connecting to external platforms via REST APIs.
    Translates BL messages into HTTP requests and returns results.
    """

    BOT_TYPE = "CONNECTOR"

    # Supported platform adapters
    PLATFORMS = {
        "github": "https://api.github.com",
        "hardin": "https://hardin-ai-search.vercel.app/api",
    }

    def __init__(self, name: str, bica: BICA):
        super().__init__(name, bica)
        self._request_count = 0

    def fetch(self, platform: str, endpoint: str, params: dict = None) -> dict:
        """
        Make an authenticated request to an external platform.
        Returns the response data or an error dict.
        """
        base = self.PLATFORMS.get(platform.lower())
        if not base:
            return {
                "STATUS": "ERROR",
                "ERROR": f"Unknown platform: {platform}",
                "SUPPORTED": list(self.PLATFORMS.keys()),
            }

        url = f"{base}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"TBN-ConnectorBot/{self.bot_id}",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                self._request_count += 1
                return {"STATUS": "SUCCESS", "DATA": data}
        except urllib.error.HTTPError as e:
            return {"STATUS": "ERROR", "HTTP_CODE": e.code, "ERROR": str(e)}
        except Exception as e:
            return {"STATUS": "ERROR", "ERROR": str(e)}

    def handle_request(self, msg: BotMessage) -> dict:
        """
        Process a DATA_REQUEST that targets an external platform.
        Expects payload to contain PLATFORM and ENDPOINT keys.
        """
        platform = msg.payload.get("PLATFORM", "github")
        endpoint = msg.payload.get("ENDPOINT", "/")
        params = msg.payload.get("PARAMS", {})
        return self.fetch(platform, endpoint, params)

    def __repr__(self):
        return f"<ConnectorBot name={self.name!r} requests={self._request_count}>"
