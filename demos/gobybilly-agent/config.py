"""
GoByBilly Agent — Configuration
================================
VIP chauffeur & transfer service (Essex & London). Real OpenAI-powered
customer chat agent, governed by TBN Protocol (signed receipt per turn).

Reads OPENAI_API_KEY from the environment. If api/.env exists and the
key isn't already in the environment, loads it from there (same key
already used by other TBN products — no new credential needed).

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import os

def _load_dotenv_fallback():
    """Minimal .env loader — only fills in keys not already set in the
    environment. Matches this repo's existing convention of no external
    dotenv dependency."""
    if os.environ.get("OPENAI_API_KEY"):
        return
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "api", ".env")
    env_path = os.path.abspath(env_path)
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

_load_dotenv_fallback()

# ── OpenAI (conversation brain) ────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("GOBYBILLY_OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# ── Business profile (GoByBilly — VIP chauffeur & transfer, Essex/London) ──
# Fares/areas below match the live gobybilly.co.uk site exactly (checked
# 21 Jul 2026, /var/www/gobybilly/index.html) — keep in sync if the site's
# rule-based chatbot prices ever change.
BUSINESS = {
    "name": "Go By Billy",
    "tagline": "VIP Chauffeur & Transfer Service across Essex & London",
    "base": "Epping, Essex",
    "coverage": "Chigwell, Loughton, Buckhurst Hill, Woodford, Chingford, Epping, "
                "London, and all major airports",
    "phone": "+44 790 1756 001",
    "whatsapp": "https://wa.me/447901756001",
    "booking_policy": "Pre-booking only — licensed operator, 24hrs notice recommended",
    "services": [
        "Airport transfers (fixed prices, no hidden charges, flight tracking included)",
        "VIP chauffeur hire",
        "Hourly hire / as-directed bookings",
        "West End and London journeys",
    ],
    "fares": {
        "Heathrow": "£110",
        "Gatwick": "£140",
        "Luton": "£100",
        "Stansted": "£70",
        "Epping to Heathrow": "£120",
        "West End journeys": "£65",
        "Hourly hire — your car, our driver": "£35/hr",
        "Hourly hire — our car & driver": "£40/hr",
    },
}

# ── Server ──────────────────────────────────────────────────────────────
GOBYBILLY_PORT = int(os.environ.get("GOBYBILLY_PORT", 5010))
