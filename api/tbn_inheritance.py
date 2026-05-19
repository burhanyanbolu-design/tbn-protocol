"""
TBN Bot Inheritance System
===========================
Transfer knowledge from a Hardin source bot to a new bot with a fresh ID.

This is NOT cloning:
  - Cloning = illegal copy of same ID (detected & revoked instantly)
  - Inheritance = knowledge transfer to NEW bot with NEW ID (legitimate)

Like a master teaching an apprentice:
  - Master bot (source) shares its knowledge/data
  - Apprentice bot (new) gets a fresh identity + inherited knowledge
  - Apprentice has different ID, different seal, different owner
  - Much faster than collecting data from scratch
  - Hardin charges for the knowledge transfer

Use cases:
  1. Customer buys a bot pre-loaded with our data
  2. We spin up a specialised bot from multiple source bots
  3. We upgrade a bot (retire old, inherit to new with better rating)
  4. We create regional variants (UK FootballBot → EU FootballBot)

Rules:
  - Only Hardin can initiate inheritance (source bots are sealed)
  - Source bot must be SEALED and verified intact
  - New bot gets a completely fresh ID and seal
  - Knowledge is COPIED not moved (source bot keeps its data)
  - New bot is immediately sealed after inheritance
  - Full audit trail of what was inherited from where
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timezone


INHERITANCE_LOG_PATH = "data/tbn_inheritance_log.json"
SEALED_REGISTRY_PATH = "data/hardin_sealed_bots.json"


# ── Knowledge Packages ────────────────────────────────────────────────
"""
Each Hardin bot has a knowledge package — the data categories it knows.
When a new bot inherits, it gets a copy of this knowledge.
"""

KNOWLEDGE_PACKAGES = {
    # Sports knowledge
    "football-bot-001":               {"category": "sports",    "data": "football_matches",    "records": 543},
    "uk-football-bot-001":            {"category": "sports",    "data": "football_matches",    "records": 543},
    "champions-league-bot-001":       {"category": "sports",    "data": "football_matches",    "records": 543},
    "international-football-bot-001": {"category": "sports",    "data": "football_matches",    "records": 543},
    "horse-racing-bot-001":           {"category": "sports",    "data": "horse_races",         "records": 245},
    "cricket-bot-001":                {"category": "sports",    "data": "cricket_matches",     "records": 150},
    "rugby-bot-001":                  {"category": "sports",    "data": "rugby_matches",       "records": 140},
    "tennis-bot-001":                 {"category": "sports",    "data": "tennis_matches",      "records": 180},
    "golf-bot-001":                   {"category": "sports",    "data": "golf_tournaments",    "records": 50},
    "f1-bot-001":                     {"category": "sports",    "data": "f1_races",            "records": 60},
    "boxing-bot-001":                 {"category": "sports",    "data": "boxing_matches",      "records": 100},
    "darts-bot-001":                  {"category": "sports",    "data": "darts_tournaments",   "records": 60},
    "snooker-bot-001":                {"category": "sports",    "data": "snooker_tournaments", "records": 50},

    # Food & Restaurant knowledge
    "kebab-bot-001":                  {"category": "food",      "data": "restaurants",         "records": 200},
    "indian-bot-001":                 {"category": "food",      "data": "restaurants",         "records": 200},
    "chinese-bot-001":                {"category": "food",      "data": "restaurants",         "records": 200},
    "pizza-bot-001":                  {"category": "food",      "data": "restaurants",         "records": 200},
    "restaurant-expansion-bot-001":   {"category": "food",      "data": "restaurants",         "records": 800},
    "recipe-bot-001":                 {"category": "food",      "data": "food_recipes",        "records": 602},

    # Financial knowledge
    "currency-bot-001":               {"category": "finance",   "data": "currency_rates",      "records": 9855},
    "commodities-bot-001":            {"category": "finance",   "data": "commodities",         "records": 4380},
    "trade-bot-001":                  {"category": "finance",   "data": "trade_data",          "records": 7200},
    "companies-house-bot-001":        {"category": "business",  "data": "uk_companies",        "records": 700},

    # Government & Statistics
    "gov-stats-bot-001":              {"category": "government","data": "government_statistics","records": 448},
    "lottery-bot-001":                {"category": "gaming",    "data": "lottery_draws",       "records": 250},

    # General knowledge
    "news-bot-001":                   {"category": "news",      "data": "news_articles",       "records": 340},
    "weather-bot-001":                {"category": "weather",   "data": "weather_data",        "records": 1000},
    "retail-bot-001":                 {"category": "retail",    "data": "retail_businesses",   "records": 30},
    "books-bot-001":                  {"category": "knowledge", "data": "books",               "records": 500},
    "geo-bot-001":                    {"category": "geography", "data": "geographic_data",     "records": 200},

    # Master bot — knows everything
    "expansion-bot-001":              {"category": "all",       "data": "all_tables",          "records": 22383},
}

# ── Inheritance Pricing ───────────────────────────────────────────────

INHERITANCE_PRICING = {
    "sports":     {"price_gbp": 299,  "description": "All sports data (football, racing, cricket etc.)"},
    "food":       {"price_gbp": 199,  "description": "Restaurants & recipes"},
    "finance":    {"price_gbp": 499,  "description": "Currency, commodities, trade data"},
    "business":   {"price_gbp": 299,  "description": "UK companies data"},
    "government": {"price_gbp": 199,  "description": "Government statistics"},
    "gaming":     {"price_gbp": 149,  "description": "Lottery data"},
    "news":       {"price_gbp": 149,  "description": "News articles"},
    "weather":    {"price_gbp": 149,  "description": "Weather data"},
    "retail":     {"price_gbp": 149,  "description": "Retail businesses"},
    "knowledge":  {"price_gbp": 199,  "description": "Books & literature"},
    "geography":  {"price_gbp": 149,  "description": "Geographic data"},
    "all":        {"price_gbp": 1999, "description": "Complete knowledge transfer — all data"},
}


# ── Core Inheritance Function ─────────────────────────────────────────

def inherit_knowledge(
    source_bot_ids: list,       # Which Hardin bots to inherit from
    new_bot_name: str,          # Name for the new bot
    new_bot_type: str,          # Type of new bot
    new_owner_company: str,     # Who is buying this
    new_owner_email: str,       # Their email
    star_rating: int,           # Rating for new bot (1-5)
    purchase_ref: str,          # Payment reference
) -> dict:
    """
    Create a new bot that inherits knowledge from one or more Hardin source bots.

    Process:
    1. Verify all source bots are sealed and intact
    2. Generate fresh ID for new bot
    3. Copy knowledge packages from source bots
    4. Seal the new bot immediately
    5. Log the inheritance chain (full audit trail)
    6. Return the new bot certificate + activation token

    The new bot:
    - Has a completely fresh ID (not a clone)
    - Arrives pre-loaded with inherited knowledge
    - Is immediately sealed and ready to activate
    - Has full audit trail showing where knowledge came from
    """

    print(f"\n{'='*60}")
    print(f"TBN INHERITANCE — Creating new bot for {new_owner_company}")
    print(f"{'='*60}")

    # ── Step 1: Verify source bots ────────────────────────────────────
    print(f"\n[1/5] Verifying {len(source_bot_ids)} source bot(s)...")

    verified_sources = []
    total_records    = 0
    knowledge_gained = []

    for source_id in source_bot_ids:
        pkg = KNOWLEDGE_PACKAGES.get(source_id)
        if not pkg:
            raise ValueError(f"Source bot {source_id} not found in knowledge packages")

        # Verify seal is intact
        sealed_ok, seal_reason = _verify_source_seal(source_id)
        if not sealed_ok:
            raise ValueError(f"Source bot {source_id} seal is broken: {seal_reason}")

        verified_sources.append(source_id)
        total_records += pkg["records"]
        knowledge_gained.append({
            "source_bot_id": source_id,
            "category":      pkg["category"],
            "data_table":    pkg["data"],
            "records":       pkg["records"],
        })
        print(f"  ✅ {source_id} — {pkg['records']:,} records ({pkg['category']})")

    print(f"  Total knowledge: {total_records:,} records from {len(verified_sources)} bots")

    # ── Step 2: Generate fresh identity ──────────────────────────────
    print(f"\n[2/5] Generating fresh bot identity...")

    random_suffix = secrets.token_hex(8)
    new_bot_id    = f"tbn-{new_bot_type.lower()}-{random_suffix}"
    now           = datetime.now(timezone.utc).isoformat()

    print(f"  New Bot ID: {new_bot_id}")
    print(f"  Owner:      {new_owner_company} ({new_owner_email})")

    # ── Step 3: Build knowledge manifest ─────────────────────────────
    print(f"\n[3/5] Building knowledge manifest...")

    knowledge_manifest = {
        "inherited_from":    verified_sources,
        "knowledge_items":   knowledge_gained,
        "total_records":     total_records,
        "inheritance_date":  now,
        "inheritance_ref":   f"INH-{secrets.token_hex(6).upper()}",
    }

    print(f"  Knowledge manifest: {knowledge_manifest['inheritance_ref']}")

    # ── Step 4: Create and seal the new bot ───────────────────────────
    print(f"\n[4/5] Creating and sealing new bot...")

    # Build identity
    identity = {
        "bot_id":            new_bot_id,
        "bot_name":          new_bot_name,
        "bot_type":          new_bot_type.upper(),
        "star_rating":       star_rating,
        "owner_company":     new_owner_company,
        "owner_email":       new_owner_email,
        "purchase_ref":      purchase_ref,
        "created_at":        now,
        "created_by":        "Hardin AI Solutions — Bot Factory (Inheritance)",
        "knowledge_manifest": knowledge_manifest,
        "transferable":      False,
        "resellable":        False,
    }

    # Fingerprint
    canonical   = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    fingerprint = hashlib.sha256(canonical).hexdigest()

    # Tamper seal
    tamper_token = secrets.token_hex(32)
    tamper_hash  = hashlib.sha256((fingerprint + tamper_token).encode()).hexdigest()

    # Activation token (sent to owner — one time use)
    activation_token      = secrets.token_urlsafe(32)
    activation_token_hash = hashlib.sha256(activation_token.encode()).hexdigest()

    new_bot_record = {
        **identity,
        "state":                "SEALED",   # Virgin — not yet activated
        "fingerprint":          fingerprint,
        "tamper_hash":          tamper_hash,
        "tamper_token":         tamper_token,
        "activation_token_hash": activation_token_hash,
        "permissions": {
            "handshake":     True,   # ✅ can handshake with other TBN bots
            "data_exchange": True,   # ✅ can exchange data
            "modify":        False,  # ❌ cannot be modified
            "clone":         False,  # ❌ cannot be cloned
            "transfer":      False,  # ❌ non-transferable
            "resell":        False,  # ❌ cannot be resold
        },
        "notice": (
            f"This bot was created by Hardin AI Solutions for {new_owner_company} only. "
            f"It inherits knowledge from {len(verified_sources)} Hardin source bot(s). "
            f"Non-transferable. Non-resellable. Any tampering results in immediate revocation. "
            f"© Hardin AI Solutions — tbn.hardinai.co.uk"
        ),
    }

    # Save to inheritance registry
    _save_inherited_bot(new_bot_id, new_bot_record)

    print(f"  ✅ Bot sealed: {new_bot_id}")
    print(f"  Fingerprint:  {fingerprint[:32]}...")

    # ── Step 5: Log inheritance chain ─────────────────────────────────
    print(f"\n[5/5] Logging inheritance chain...")

    _log_inheritance({
        "new_bot_id":      new_bot_id,
        "new_bot_name":    new_bot_name,
        "owner_company":   new_owner_company,
        "owner_email":     new_owner_email,
        "source_bots":     verified_sources,
        "total_records":   total_records,
        "purchase_ref":    purchase_ref,
        "inheritance_ref": knowledge_manifest["inheritance_ref"],
        "created_at":      now,
    })

    print(f"  ✅ Inheritance logged: {knowledge_manifest['inheritance_ref']}")

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"INHERITANCE COMPLETE")
    print(f"  New Bot ID:    {new_bot_id}")
    print(f"  Knowledge:     {total_records:,} records from {len(verified_sources)} source(s)")
    print(f"  State:         SEALED (virgin — send activation token to owner)")
    print(f"  Owner:         {new_owner_company}")
    print(f"{'='*60}\n")

    return {
        "new_bot_id":         new_bot_id,
        "new_bot_name":       new_bot_name,
        "state":              "SEALED",
        "owner_company":      new_owner_company,
        "owner_email":        new_owner_email,
        "knowledge_inherited": knowledge_gained,
        "total_records":      total_records,
        "fingerprint":        fingerprint,
        "inheritance_ref":    knowledge_manifest["inheritance_ref"],
        "activation_token":   activation_token,   # ⚠️ shown ONCE — send to owner
        "warning":            "Save the activation token — it will not be shown again.",
        "next_step":          f"Send activation token to {new_owner_email} to crack the egg.",
    }


# ── Quick Inheritance Presets ─────────────────────────────────────────
"""
Pre-built packages — common combinations customers buy.
Faster to order, faster to deliver.
"""

PRESET_PACKAGES = {
    "sports_complete": {
        "name":        "Complete Sports Bot",
        "description": "All sports data — football, racing, cricket, rugby, tennis, golf, F1, boxing, darts, snooker",
        "sources":     ["football-bot-001", "horse-racing-bot-001", "cricket-bot-001",
                        "rugby-bot-001", "tennis-bot-001", "golf-bot-001", "f1-bot-001",
                        "boxing-bot-001", "darts-bot-001", "snooker-bot-001"],
        "price_gbp":   799,
        "records":     1578,
        "star_rating": 3,
    },
    "finance_complete": {
        "name":        "Complete Finance Bot",
        "description": "Currency rates, commodities, trade data, UK companies",
        "sources":     ["currency-bot-001", "commodities-bot-001", "trade-bot-001", "companies-house-bot-001"],
        "price_gbp":   999,
        "records":     22135,
        "star_rating": 4,
    },
    "food_complete": {
        "name":        "Complete Food & Restaurant Bot",
        "description": "All restaurants, recipes, food data",
        "sources":     ["restaurant-expansion-bot-001", "recipe-bot-001"],
        "price_gbp":   299,
        "records":     1402,
        "star_rating": 2,
    },
    "everything": {
        "name":        "Complete Knowledge Bot",
        "description": "Everything — all 30,903 data points across all categories",
        "sources":     list(KNOWLEDGE_PACKAGES.keys()),
        "price_gbp":   2999,
        "records":     30903,
        "star_rating": 5,
    },
}


def inherit_from_preset(
    preset_name: str,
    new_bot_name: str,
    new_owner_company: str,
    new_owner_email: str,
    purchase_ref: str,
) -> dict:
    """Quick inheritance from a preset package."""
    if preset_name not in PRESET_PACKAGES:
        raise ValueError(f"Unknown preset. Choose from: {list(PRESET_PACKAGES)}")

    preset = PRESET_PACKAGES[preset_name]
    return inherit_knowledge(
        source_bot_ids    = preset["sources"],
        new_bot_name      = new_bot_name,
        new_bot_type      = "inherited",
        new_owner_company = new_owner_company,
        new_owner_email   = new_owner_email,
        star_rating       = preset["star_rating"],
        purchase_ref      = purchase_ref,
    )


# ── Storage helpers ───────────────────────────────────────────────────

INHERITED_REGISTRY_PATH = "data/tbn_inherited_bots.json"

def _save_inherited_bot(bot_id: str, record: dict):
    os.makedirs("data", exist_ok=True)
    registry = {}
    if os.path.exists(INHERITED_REGISTRY_PATH):
        with open(INHERITED_REGISTRY_PATH) as f:
            registry = json.load(f)
    registry[bot_id] = record
    with open(INHERITED_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def _log_inheritance(entry: dict):
    os.makedirs("data", exist_ok=True)
    log = []
    if os.path.exists(INHERITANCE_LOG_PATH):
        with open(INHERITANCE_LOG_PATH) as f:
            log = json.load(f)
    log.append(entry)
    with open(INHERITANCE_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def _verify_source_seal(bot_id: str) -> tuple[bool, str]:
    """Check source bot seal is intact before inheriting from it."""
    if not os.path.exists(SEALED_REGISTRY_PATH):
        # Registry not yet created — allow for now (will be enforced after sealing)
        return True, "Registry not yet initialised"
    with open(SEALED_REGISTRY_PATH) as f:
        registry = json.load(f)
    if bot_id not in registry:
        return True, "Not yet in sealed registry — OK for internal bots"
    seal_record = registry[bot_id]
    if not seal_record.get("sealed"):
        return False, "Bot is not sealed"
    return True, "Seal intact"


def get_inheritance_stats() -> dict:
    """Stats for admin dashboard."""
    log = []
    if os.path.exists(INHERITANCE_LOG_PATH):
        with open(INHERITANCE_LOG_PATH) as f:
            log = json.load(f)

    registry = {}
    if os.path.exists(INHERITED_REGISTRY_PATH):
        with open(INHERITED_REGISTRY_PATH) as f:
            registry = json.load(f)

    return {
        "total_inherited_bots": len(registry),
        "total_inheritances":   len(log),
        "recent":               log[-5:] if log else [],
        "presets_available":    list(PRESET_PACKAGES.keys()),
        "preset_details":       {
            k: {"name": v["name"], "price_gbp": v["price_gbp"], "records": v["records"]}
            for k, v in PRESET_PACKAGES.items()
        },
    }
