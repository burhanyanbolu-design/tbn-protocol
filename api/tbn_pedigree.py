"""
TBN Pedigree Bot System — Premium Pre-Loaded Bots
===================================================
"Already clever. Has a pedigree. Works immediately."

A Pedigree Bot is:
  - Created & packaged ONLY by Hardin (nobody else can do this)
  - Pre-loaded with inherited knowledge from parent bots
  - Sealed by Hardin — tamper-proof, clone-proof
  - Cracked ONLY by the buyer — permanently bound to them
  - Sold at premium because it saves months of learning
  - Has a Pedigree Certificate showing its lineage

Like a pedigree dog:
  - Stray dog    = basic bot, knows nothing, starts from zero
  - Pedigree dog = born trained, has lineage, worth more, works immediately

The Chain:
  Hardin creates → Hardin packages knowledge → Hardin seals
  → Customer buys → Customer cracks → Bot is live & clever immediately

Nobody else can do the packaging step. That's the moat.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timezone
from api.tbn_inheritance import KNOWLEDGE_PACKAGES, PRESET_PACKAGES, inherit_knowledge


# ── Pedigree Tiers ────────────────────────────────────────────────────

PEDIGREE_CATALOGUE = {

    # ── STARTER PEDIGREES (£299-£499) ────────────────────────────────
    "sports-pedigree-starter": {
        "name":         "Sports Pedigree Bot — Starter",
        "tagline":      "Born knowing UK sports. Works on day one.",
        "star_rating":  3,
        "price_gbp":    299,
        "sources":      ["football-bot-001", "horse-racing-bot-001", "cricket-bot-001"],
        "records":      938,
        "categories":   ["Football", "Horse Racing", "Cricket"],
        "pedigree_line": "RetailBot × FootballBot × HorseRacingBot",
        "what_it_knows": [
            "543 football matches (Premier League, Champions League, International)",
            "245 horse races (UK courses)",
            "150 cricket matches (Test, ODI, T20)",
        ],
        "why_premium": "Arrives knowing 938 data points. A basic bot would take weeks to collect this.",
    },

    "finance-pedigree-starter": {
        "name":         "Finance Pedigree Bot — Starter",
        "tagline":      "Born knowing currency & commodities. Works on day one.",
        "star_rating":  3,
        "price_gbp":    399,
        "sources":      ["currency-bot-001", "commodities-bot-001"],
        "records":      14235,
        "categories":   ["Currency Rates", "Commodities"],
        "pedigree_line": "CurrencyBot × CommoditiesBot",
        "what_it_knows": [
            "9,855 currency exchange rate records",
            "4,380 commodity price records (gold, oil, gas etc.)",
        ],
        "why_premium": "Arrives knowing 14,235 financial data points. Instant financial intelligence.",
    },

    "food-pedigree-starter": {
        "name":         "Food & Restaurant Pedigree Bot — Starter",
        "tagline":      "Born knowing UK restaurants & recipes. Works on day one.",
        "star_rating":  2,
        "price_gbp":    299,
        "sources":      ["restaurant-expansion-bot-001", "recipe-bot-001"],
        "records":      1402,
        "categories":   ["Restaurants", "Recipes"],
        "pedigree_line": "RestaurantExpansionBot × RecipeBot",
        "what_it_knows": [
            "800 UK restaurants (kebab, Indian, Chinese, pizza)",
            "602 world food recipes",
        ],
        "why_premium": "Arrives knowing 1,402 food data points. Perfect for food industry apps.",
    },

    # ── PRO PEDIGREES (£799-£1,499) ───────────────────────────────────
    "sports-pedigree-pro": {
        "name":         "Sports Pedigree Bot — Pro",
        "tagline":      "The complete sports brain. Every sport. Every result.",
        "star_rating":  4,
        "price_gbp":    799,
        "sources":      [
            "football-bot-001", "uk-football-bot-001", "champions-league-bot-001",
            "international-football-bot-001", "horse-racing-bot-001", "cricket-bot-001",
            "rugby-bot-001", "tennis-bot-001", "golf-bot-001", "f1-bot-001",
            "boxing-bot-001", "darts-bot-001", "snooker-bot-001",
        ],
        "records":      1578,
        "categories":   ["All Sports"],
        "pedigree_line": "FootballBot × HorseRacingBot × CricketBot × RugbyBot × TennisBot × GolfBot × F1Bot × BoxingBot × DartsBot × SnookerBot",
        "what_it_knows": [
            "543 football matches across all competitions",
            "245 horse races",
            "150 cricket matches",
            "140 rugby matches",
            "180 tennis matches",
            "50 golf tournaments",
            "60 F1 races",
            "100 boxing matches",
            "60 darts tournaments",
            "50 snooker tournaments",
        ],
        "why_premium": "Complete sports intelligence. 1,578 records. Lineage from 13 parent bots.",
    },

    "finance-pedigree-pro": {
        "name":         "Finance Pedigree Bot — Pro",
        "tagline":      "Complete financial brain. Currency, commodities, trade, companies.",
        "star_rating":  4,
        "price_gbp":    1299,
        "sources":      ["currency-bot-001", "commodities-bot-001", "trade-bot-001",
                         "companies-house-bot-001", "gov-stats-bot-001"],
        "records":      22583,
        "categories":   ["Currency", "Commodities", "Trade", "Companies", "Government Stats"],
        "pedigree_line": "CurrencyBot × CommoditiesBot × TradeDataBot × CompaniesHouseBot × GovernmentStatsBot",
        "what_it_knows": [
            "9,855 currency exchange rate records",
            "4,380 commodity price records",
            "7,200 import/export trade records",
            "700 UK company records",
            "448 government statistics",
        ],
        "why_premium": "22,583 financial data points. The most valuable pedigree we offer.",
    },

    # ── ELITE PEDIGREES (£2,999+) ─────────────────────────────────────
    "omniscient-pedigree": {
        "name":         "Omniscient Pedigree Bot — Elite",
        "tagline":      "Born knowing everything. The most intelligent bot we've ever created.",
        "star_rating":  5,
        "price_gbp":    2999,
        "sources":      list(KNOWLEDGE_PACKAGES.keys()),
        "records":      30903,
        "categories":   ["Everything"],
        "pedigree_line": "All 31 Hardin source bots",
        "what_it_knows": [
            "30,903 total data points across ALL categories",
            "Sports: football, racing, cricket, rugby, tennis, golf, F1, boxing, darts, snooker",
            "Finance: currency, commodities, trade data",
            "Food: restaurants, recipes",
            "Business: UK companies",
            "Government: statistics, geography",
            "Culture: books, news, weather, lottery",
        ],
        "why_premium": (
            "The pinnacle of TBN bot intelligence. "
            "Inherits from ALL 31 Hardin source bots. "
            "30,903 data points on day one. "
            "Would take years to collect independently. "
            "Only a handful will ever be created."
        ),
    },

    # ── SPECIALIST PEDIGREES ──────────────────────────────────────────
    "betting-pedigree": {
        "name":         "Betting Intelligence Pedigree Bot",
        "tagline":      "Built for the betting industry. Sports + lottery + racing.",
        "star_rating":  4,
        "price_gbp":    999,
        "sources":      [
            "football-bot-001", "horse-racing-bot-001", "cricket-bot-001",
            "rugby-bot-001", "tennis-bot-001", "golf-bot-001", "f1-bot-001",
            "boxing-bot-001", "darts-bot-001", "snooker-bot-001", "lottery-bot-001",
        ],
        "records":      1828,
        "categories":   ["Sports", "Lottery"],
        "pedigree_line": "All Sports Bots × LotteryBot",
        "what_it_knows": [
            "All sports results (1,578 records)",
            "250 lottery draws with statistics",
        ],
        "why_premium": "Purpose-built for betting apps. 1,828 records. Instant competitive advantage.",
    },

    "news-intelligence-pedigree": {
        "name":         "News Intelligence Pedigree Bot",
        "tagline":      "Born knowing UK news, weather & geography.",
        "star_rating":  3,
        "price_gbp":    399,
        "sources":      ["news-bot-001", "weather-bot-001", "geo-bot-001"],
        "records":      1540,
        "categories":   ["News", "Weather", "Geography"],
        "pedigree_line": "NewsBot × WeatherBot × GeographicBot",
        "what_it_knows": [
            "340 news articles",
            "1,000 weather records",
            "200 geographic data points",
        ],
        "why_premium": "Perfect for media, publishing and location-based apps.",
    },
}


# ── Pedigree Certificate ──────────────────────────────────────────────

def generate_pedigree_certificate(
    bot_id: str,
    catalogue_key: str,
    owner_company: str,
    owner_email: str,
    purchase_ref: str,
    inheritance_ref: str,
    fingerprint: str,
) -> dict:
    """
    Generate the official Pedigree Certificate for a bot.
    This is the bot's 'birth certificate' showing its lineage.
    Signed by Hardin. Verifiable by anyone.
    """
    product = PEDIGREE_CATALOGUE[catalogue_key]
    now     = datetime.now(timezone.utc).isoformat()

    cert = {
        "certificate_type":  "TBN PEDIGREE CERTIFICATE",
        "certificate_id":    f"PED-{secrets.token_hex(6).upper()}",
        "issued_by":         "Hardin AI Solutions — TBN Bot Factory",
        "issued_at":         now,

        # Bot identity
        "bot_id":            bot_id,
        "bot_name":          product["name"],
        "star_rating":       product["star_rating"],
        "stars":             "⭐" * product["star_rating"],

        # Ownership
        "owner_company":     owner_company,
        "owner_email":       owner_email,
        "purchase_ref":      purchase_ref,
        "transferable":      False,
        "resellable":        False,

        # Pedigree lineage
        "pedigree_line":     product["pedigree_line"],
        "parent_bots":       product["sources"],
        "parent_bot_count":  len(product["sources"]),
        "knowledge_records": product["records"],
        "categories":        product["categories"],
        "what_it_knows":     product["what_it_knows"],

        # Technical
        "inheritance_ref":   inheritance_ref,
        "fingerprint":       fingerprint,
        "verify_url":        f"https://tbn.hardinai.co.uk/verify/{bot_id}",

        # Legal
        "notice": (
            f"This Pedigree Bot was created exclusively for {owner_company}. "
            f"It is non-transferable and non-resellable. "
            f"Its knowledge was inherited from {len(product['sources'])} Hardin source bots. "
            f"Any tampering, cloning or unauthorised use results in immediate revocation. "
            f"© Hardin AI Solutions — tbn.hardinai.co.uk"
        ),
    }

    # Certificate fingerprint
    canonical    = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()
    cert["cert_fingerprint"] = hashlib.sha256(canonical).hexdigest()

    return cert


# ── Order a Pedigree Bot ──────────────────────────────────────────────

def order_pedigree_bot(
    catalogue_key: str,
    custom_name: str,
    owner_company: str,
    owner_email: str,
    purchase_ref: str,
) -> dict:
    """
    The complete order process for a Pedigree Bot.

    1. Hardin creates it (knowledge transfer from parent bots)
    2. Hardin seals it (tamper-proof)
    3. Hardin issues Pedigree Certificate
    4. Activation token sent to buyer (one time only)
    5. Buyer cracks it → bot is live and clever immediately

    Returns everything needed to deliver to the customer.
    """
    if catalogue_key not in PEDIGREE_CATALOGUE:
        raise ValueError(
            f"Unknown pedigree. Available: {list(PEDIGREE_CATALOGUE.keys())}"
        )

    product = PEDIGREE_CATALOGUE[catalogue_key]

    print(f"\n{'='*60}")
    print(f"PEDIGREE BOT ORDER")
    print(f"  Product:  {product['name']}")
    print(f"  Price:    £{product['price_gbp']:,}")
    print(f"  Records:  {product['records']:,}")
    print(f"  Stars:    {'⭐' * product['star_rating']}")
    print(f"  Buyer:    {owner_company} ({owner_email})")
    print(f"  Ref:      {purchase_ref}")
    print(f"{'='*60}")

    # Step 1: Inherit knowledge and create new bot
    result = inherit_knowledge(
        source_bot_ids    = product["sources"],
        new_bot_name      = custom_name or product["name"],
        new_bot_type      = "pedigree",
        new_owner_company = owner_company,
        new_owner_email   = owner_email,
        star_rating       = product["star_rating"],
        purchase_ref      = purchase_ref,
    )

    # Step 2: Generate Pedigree Certificate
    pedigree_cert = generate_pedigree_certificate(
        bot_id          = result["new_bot_id"],
        catalogue_key   = catalogue_key,
        owner_company   = owner_company,
        owner_email     = owner_email,
        purchase_ref    = purchase_ref,
        inheritance_ref = result["inheritance_ref"],
        fingerprint     = result["fingerprint"],
    )

    # Step 3: Save pedigree certificate
    _save_pedigree_cert(result["new_bot_id"], pedigree_cert)

    print(f"\n✅ PEDIGREE BOT READY FOR DELIVERY")
    print(f"   Bot ID:      {result['new_bot_id']}")
    print(f"   Certificate: {pedigree_cert['certificate_id']}")
    print(f"   State:       SEALED (virgin)")
    print(f"   Action:      Send activation token to {owner_email}")
    print(f"   ⚠️  Activation token shown once only — deliver securely!\n")

    return {
        "order_status":       "READY_FOR_DELIVERY",
        "bot_id":             result["new_bot_id"],
        "pedigree_cert":      pedigree_cert,
        "activation_token":   result["activation_token"],   # ⚠️ ONE TIME — send to buyer
        "state":              "SEALED",
        "knowledge_records":  result["total_records"],
        "price_gbp":          product["price_gbp"],
        "delivery_note": (
            f"Your {product['name']} is sealed and ready. "
            f"It already knows {result['total_records']:,} data points from "
            f"{len(product['sources'])} parent bots. "
            f"Use your activation token to crack the egg and bring it to life. "
            f"Once activated, it works immediately — no training required."
        ),
    }


# ── Catalogue display ─────────────────────────────────────────────────

def get_catalogue() -> list:
    """Return the full pedigree catalogue for the pricing page."""
    return [
        {
            "key":          key,
            "name":         p["name"],
            "tagline":      p["tagline"],
            "price_gbp":    p["price_gbp"],
            "star_rating":  p["star_rating"],
            "stars":        "⭐" * p["star_rating"],
            "records":      p["records"],
            "categories":   p["categories"],
            "parent_bots":  len(p["sources"]),
            "what_it_knows": p["what_it_knows"],
            "why_premium":  p["why_premium"],
        }
        for key, p in PEDIGREE_CATALOGUE.items()
    ]


# ── Storage ───────────────────────────────────────────────────────────

PEDIGREE_CERTS_PATH = "data/tbn_pedigree_certs.json"

def _save_pedigree_cert(bot_id: str, cert: dict):
    os.makedirs("data", exist_ok=True)
    certs = {}
    if os.path.exists(PEDIGREE_CERTS_PATH):
        with open(PEDIGREE_CERTS_PATH) as f:
            certs = json.load(f)
    certs[bot_id] = cert
    with open(PEDIGREE_CERTS_PATH, "w") as f:
        json.dump(certs, f, indent=2)


def get_pedigree_cert(bot_id: str) -> dict | None:
    """Look up a bot's pedigree certificate — publicly verifiable."""
    if not os.path.exists(PEDIGREE_CERTS_PATH):
        return None
    with open(PEDIGREE_CERTS_PATH) as f:
        certs = json.load(f)
    return certs.get(bot_id)
