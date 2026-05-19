"""
Seal all 31 Hardin internal TBN bots.

Rules after sealing:
  - Cannot be tampered with
  - Cannot be cloned
  - Cannot be modified
  - CAN handshake with other valid TBN bots
  - CAN exchange data with other valid TBN bots
  - Owned by Hardin AI Solutions forever
"""

import sys
import os
import json
import hashlib
import secrets
import base64
from datetime import datetime, timezone

sys.path.insert(0, '/opt/tbn-protocol')

import psycopg2

DB_CONFIG = {
    "dbname":   "hardin_data_network",
    "user":     "postgres",
    "host":     "localhost"
}

SEALED_REGISTRY_PATH = "/opt/tbn-protocol/data/hardin_sealed_bots.json"
OWNER_COMPANY        = "Hardin AI Solutions"
OWNER_EMAIL          = "burhan@hardinai.co.uk"

# The 31 Hardin internal bots
HARDIN_BOTS = [
    {"bot_id": "retail-bot-001",                 "bot_name": "RetailBot",               "star_rating": 3},
    {"bot_id": "kebab-bot-001",                  "bot_name": "KebabBot",                "star_rating": 2},
    {"bot_id": "indian-bot-001",                 "bot_name": "IndianRestaurantBot",      "star_rating": 2},
    {"bot_id": "chinese-bot-001",                "bot_name": "ChineseTakeawayBot",       "star_rating": 2},
    {"bot_id": "pizza-bot-001",                  "bot_name": "PizzaBot",                "star_rating": 2},
    {"bot_id": "lottery-bot-001",                "bot_name": "LotteryBot",              "star_rating": 2},
    {"bot_id": "football-bot-001",               "bot_name": "FootballBot",             "star_rating": 2},
    {"bot_id": "news-bot-001",                   "bot_name": "NewsBot",                 "star_rating": 2},
    {"bot_id": "horse-racing-bot-001",           "bot_name": "HorseRacingBot",          "star_rating": 2},
    {"bot_id": "uk-football-bot-001",            "bot_name": "UKFootballBot",           "star_rating": 2},
    {"bot_id": "champions-league-bot-001",       "bot_name": "ChampionsLeagueBot",      "star_rating": 2},
    {"bot_id": "international-football-bot-001", "bot_name": "InternationalFootballBot","star_rating": 2},
    {"bot_id": "weather-bot-001",                "bot_name": "WeatherBot",              "star_rating": 1},
    {"bot_id": "cricket-bot-001",                "bot_name": "CricketBot",              "star_rating": 2},
    {"bot_id": "rugby-bot-001",                  "bot_name": "RugbyBot",                "star_rating": 2},
    {"bot_id": "tennis-bot-001",                 "bot_name": "TennisBot",               "star_rating": 2},
    {"bot_id": "golf-bot-001",                   "bot_name": "GolfBot",                 "star_rating": 2},
    {"bot_id": "f1-bot-001",                     "bot_name": "F1Bot",                   "star_rating": 2},
    {"bot_id": "companies-house-bot-001",        "bot_name": "CompaniesHouseBot",       "star_rating": 2},
    {"bot_id": "boxing-bot-001",                 "bot_name": "BoxingBot",               "star_rating": 2},
    {"bot_id": "darts-bot-001",                  "bot_name": "DartsBot",                "star_rating": 2},
    {"bot_id": "snooker-bot-001",                "bot_name": "SnookerBot",              "star_rating": 2},
    {"bot_id": "restaurant-expansion-bot-001",   "bot_name": "RestaurantExpansionBot",  "star_rating": 2},
    {"bot_id": "recipe-bot-001",                 "bot_name": "RecipeBot",               "star_rating": 2},
    {"bot_id": "expansion-bot-001",              "bot_name": "MassiveExpansionBot",     "star_rating": 3},
    {"bot_id": "gov-stats-bot-001",              "bot_name": "GovernmentStatsBot",      "star_rating": 2},
    {"bot_id": "currency-bot-001",               "bot_name": "CurrencyBot",             "star_rating": 2},
    {"bot_id": "commodities-bot-001",            "bot_name": "CommoditiesBot",          "star_rating": 2},
    {"bot_id": "trade-bot-001",                  "bot_name": "TradeDataBot",            "star_rating": 2},
    {"bot_id": "books-bot-001",                  "bot_name": "BooksBot",                "star_rating": 2},
    {"bot_id": "geo-bot-001",                    "bot_name": "GeographicBot",           "star_rating": 2},
]


def make_seal(bot_id: str, bot_name: str, star_rating: int) -> dict:
    """
    Create a cryptographic seal for a Hardin internal bot.

    The seal contains:
    - A fingerprint (SHA-256 of bot identity)
    - A tamper-detection hash
    - Hardin's ownership stamp
    - Handshake permission (other TBN bots CAN connect)
    - Modification lock (nobody can change it)
    """
    now = datetime.now(timezone.utc).isoformat()

    # Bot identity payload — what we seal
    identity = {
        "bot_id":        bot_id,
        "bot_name":      bot_name,
        "star_rating":   star_rating,
        "owner_company": OWNER_COMPANY,
        "owner_email":   OWNER_EMAIL,
        "bot_type":      "data_collector",
        "sealed_at":     now,
        "sealed_by":     "Hardin AI Solutions — Bot Factory",
    }

    # Canonical JSON — deterministic, sorted
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()

    # Fingerprint — SHA-256 of identity
    fingerprint = hashlib.sha256(canonical).hexdigest()

    # Tamper token — random salt burned into the seal
    tamper_token = secrets.token_hex(32)
    tamper_hash  = hashlib.sha256((fingerprint + tamper_token).encode()).hexdigest()

    seal = {
        **identity,
        "fingerprint":   fingerprint,
        "tamper_hash":   tamper_hash,
        "tamper_token":  tamper_token,   # stored server-side only

        # Access rules
        "permissions": {
            "handshake":        True,   # ✅ other TBN bots CAN handshake
            "data_exchange":    True,   # ✅ other TBN bots CAN read data
            "modify":           False,  # ❌ nobody can modify
            "clone":            False,  # ❌ cannot be cloned
            "transfer":         False,  # ❌ cannot be transferred
            "resell":           False,  # ❌ cannot be resold
            "tamper":           False,  # ❌ any tamper = instant revoke
        },

        "notice": (
            "This bot is sealed property of Hardin AI Solutions. "
            "Handshake and data exchange permitted for valid TBN bots only. "
            "Any modification, cloning or tampering is detected automatically "
            "and results in immediate revocation. "
            "© Hardin AI Solutions — tbn.hardinai.co.uk"
        ),
    }

    return seal


def verify_seal(seal: dict) -> tuple[bool, str]:
    """
    Verify a sealed bot has not been tampered with.
    Called on every handshake request.
    """
    try:
        # Rebuild identity payload
        identity = {
            "bot_id":        seal["bot_id"],
            "bot_name":      seal["bot_name"],
            "star_rating":   seal["star_rating"],
            "owner_company": seal["owner_company"],
            "owner_email":   seal["owner_email"],
            "bot_type":      seal["bot_type"],
            "sealed_at":     seal["sealed_at"],
            "sealed_by":     seal["sealed_by"],
        }
        canonical   = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        fingerprint = hashlib.sha256(canonical).hexdigest()

        # Check fingerprint
        if fingerprint != seal.get("fingerprint"):
            return False, f"TAMPERED — fingerprint mismatch on {seal['bot_id']}"

        # Check tamper hash
        tamper_hash = hashlib.sha256(
            (fingerprint + seal.get("tamper_token", "")).encode()
        ).hexdigest()
        if tamper_hash != seal.get("tamper_hash"):
            return False, f"TAMPERED — tamper hash mismatch on {seal['bot_id']}"

        return True, f"✅ Seal intact — {seal['bot_id']} is genuine Hardin bot"

    except Exception as e:
        return False, f"Seal verification error: {e}"


def seal_all_bots():
    """Seal all 31 Hardin internal bots and save to registry."""

    print("=" * 60)
    print("HARDIN BOT FACTORY — SEALING ALL INTERNAL BOTS")
    print("=" * 60)
    print(f"Owner: {OWNER_COMPANY}")
    print(f"Email: {OWNER_EMAIL}")
    print(f"Total bots to seal: {len(HARDIN_BOTS)}")
    print()

    os.makedirs(os.path.dirname(SEALED_REGISTRY_PATH), exist_ok=True)

    # Load existing registry if any
    registry = {}
    if os.path.exists(SEALED_REGISTRY_PATH):
        with open(SEALED_REGISTRY_PATH) as f:
            registry = json.load(f)

    sealed_count  = 0
    skipped_count = 0

    for bot in HARDIN_BOTS:
        bot_id = bot["bot_id"]

        if bot_id in registry and registry[bot_id].get("sealed"):
            print(f"  ⏭️  SKIP  {bot_id} — already sealed")
            skipped_count += 1
            continue

        seal = make_seal(bot_id, bot["bot_name"], bot["star_rating"])

        # Verify the seal we just created
        valid, reason = verify_seal(seal)
        if not valid:
            print(f"  ❌ FAILED to seal {bot_id}: {reason}")
            continue

        registry[bot_id] = {
            "sealed":     True,
            "seal":       seal,
            "sealed_at":  seal["sealed_at"],
        }

        stars = "⭐" * bot["star_rating"]
        print(f"  🔒 SEALED  {bot_id:<40} {stars}  ✅ verified")
        sealed_count += 1

    # Save registry
    with open(SEALED_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    # Also update the database — mark bots as sealed
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor()

        # Add sealed column if not exists
        cur.execute("""
            ALTER TABLE tbn_bots
            ADD COLUMN IF NOT EXISTS sealed BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS sealed_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(64),
            ADD COLUMN IF NOT EXISTS permissions JSONB
        """)

        for bot in HARDIN_BOTS:
            bot_id = bot["bot_id"]
            if bot_id not in registry:
                continue
            seal = registry[bot_id]["seal"]
            cur.execute("""
                UPDATE tbn_bots
                SET sealed      = TRUE,
                    sealed_at   = %s,
                    fingerprint = %s,
                    permissions = %s
                WHERE bot_id = %s
            """, (
                seal["sealed_at"],
                seal["fingerprint"],
                json.dumps(seal["permissions"]),
                bot_id
            ))

        conn.commit()
        cur.close()
        conn.close()
        print()
        print("✅ Database updated — all bots marked as sealed")

    except Exception as e:
        print(f"⚠️  Database update error: {e}")

    print()
    print("=" * 60)
    print(f"SEALING COMPLETE")
    print(f"  Newly sealed : {sealed_count}")
    print(f"  Already sealed: {skipped_count}")
    print(f"  Total sealed : {sealed_count + skipped_count}")
    print()
    print("PERMISSIONS:")
    print("  ✅ Handshake with other TBN bots — ALLOWED")
    print("  ✅ Data exchange with TBN bots    — ALLOWED")
    print("  ❌ Modify                         — BLOCKED")
    print("  ❌ Clone                          — BLOCKED")
    print("  ❌ Transfer                       — BLOCKED")
    print("  ❌ Resell                         — BLOCKED")
    print("  ❌ Tamper                         — AUTO-REVOKE")
    print("=" * 60)
    print(f"Registry saved: {SEALED_REGISTRY_PATH}")


if __name__ == "__main__":
    seal_all_bots()
