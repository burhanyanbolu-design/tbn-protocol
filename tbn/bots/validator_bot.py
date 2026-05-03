"""
Validator Bot — verifies the accuracy and trustworthiness of data.
Checks results returned by Search Bots before they reach the user.
"""

from ..bot import Bot
from ..bot_language import BotMessage, Intent, TrustLevel
from ..identity import BICA


# Simple domain trust list — Phase 3 will use a distributed registry
TRUSTED_DOMAINS = {
    "openai.com": "HIGH",
    "anthropic.com": "HIGH",
    "github.com": "HIGH",
    "hardin-ai-search.vercel.app": "HIGH",
    "huggingface.co": "HIGH",
    "google.com": "MEDIUM",
    "microsoft.com": "MEDIUM",
    "arxiv.org": "HIGH",
}


class ValidatorBot(Bot):
    """
    Specialised bot for validating data accuracy and trust.
    Scores each result and flags low-trust or suspicious entries.
    """

    BOT_TYPE = "VALIDATOR"

    def __init__(self, name: str, bica: BICA):
        super().__init__(name, bica)
        self._validation_count = 0

    def validate(self, results: list[dict]) -> list[dict]:
        """
        Validate a list of result records.
        Adds a 'validated' flag and 'trust_score' to each.
        """
        validated = []
        for record in results:
            url = record.get("url", "")
            domain = self._extract_domain(url)
            trust = TRUSTED_DOMAINS.get(domain, "LOW")

            validated_record = {
                **record,
                "validated": True,
                "trust_score": trust,
                "validator_id": self.bot_id,
            }
            validated.append(validated_record)
            self._validation_count += 1

        return validated

    def handle_response(self, msg: BotMessage) -> dict:
        """
        Process a DATA_RESPONSE message, validate its results,
        and return a validated payload.
        """
        results = msg.payload.get("RESULTS", [])
        validated = self.validate(results)

        # Filter out LOW trust if original request was HIGH trust
        trust_level = msg.payload.get("TRUST_LEVEL", "MEDIUM")
        if trust_level == "HIGH":
            validated = [r for r in validated if r["trust_score"] != "LOW"]

        return {
            "RESULTS": validated,
            "RESULT_COUNT": len(validated),
            "STATUS": "VALIDATED",
            "TOTAL_VALIDATED": self._validation_count,
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from a URL string."""
        url = url.replace("https://", "").replace("http://", "")
        return url.split("/")[0]

    def __repr__(self):
        return f"<ValidatorBot name={self.name!r} validated={self._validation_count}>"
