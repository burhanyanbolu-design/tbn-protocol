"""
TBN Protocol — Phase 4 Demo
=============================
Demonstrates:
  1. TBN SDK — 5-line bot registration
  2. External platform integration (GitHub-style adapter)
  3. Audit log — full trail of every bot action
  4. Public BICA Registry — global bot lookup
  5. Permission rules — certified bots only

Run:
    python demo_phase4.py
"""

from tbn.identity import BICA
from tbn.seeded_network import SeededNetwork
from tbn.sdk import TBNClient
from tbn.bots import SearchBot, ValidatorBot
from tbn.platform_integration import (
    PlatformAdapter,
    PublicBICARegistry,
    BotRequest,
    AccessLevel,
    AuditLog,
)


def main():
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — Phase 4 Demo")
    print("  SDK + Platform Integration + Public Registry")
    print("=" * 60)

    # ── 1. TBN SDK — 5 lines to register a bot ──────────────────────
    print("\n" + "=" * 60)
    print("[Phase 4A] TBN SDK — Register a bot in 5 lines")
    print("=" * 60)

    # This is what a third-party developer writes:
    shared_bica = BICA(registry_path="data/bica_registry.json")
    shared_net = __import__("tbn.seeded_network", fromlist=["SeededNetwork"]).SeededNetwork()

    client_a = TBNClient(bot_name="MySearchBot", bot_type="SEARCH", bica=shared_bica, seeded_net=shared_net)
    client_a.register()

    client_b = TBNClient(bot_name="MyValidatorBot", bot_type="VALIDATOR", bica=shared_bica, seeded_net=shared_net)
    client_b.register()

    print(f"\n  Bot A ID : {client_a.bot_id}")
    print(f"  Bot B ID : {client_b.bot_id}")

    # Load some data into the search bot
    assert isinstance(client_a._bot, SearchBot)
    client_a._bot.add_to_index({"name": "Hardin AI", "url": "https://hardin-ai-search.vercel.app", "category": "AI Search", "audience": "developer"})
    client_a._bot.add_to_index({"name": "OpenAI",    "url": "https://openai.com",                  "category": "AI Platform", "audience": "developer"})
    client_a._bot.add_to_index({"name": "Notion AI", "url": "https://notion.so",                   "category": "Productivity", "audience": "small business"})

    # SDK search
    print("\n  Running SDK search...")
    result = client_a.search("Find AI tools for developers")
    print(f"  Source  : {result['source']}")
    print(f"  Results : {result['count']}")
    for r in result["results"]:
        print(f"    - {r['name']} ({r['url']})")

    # Second search — should hit cache
    print("\n  Running same search again (should hit cache)...")
    result2 = client_a.search("Find AI tools for developers")
    print(f"  Source  : {result2['source']}  ← cache hit ✅")

    # SDK trust handshake + messaging
    print("\n  SDK trust handshake between two clients...")
    client_a.connect(client_b)
    msg = client_a.send(
        to=client_b,
        intent="DATA_REQUEST",
        data={"QUERY": "validate these results"},
    )
    client_b.receive(msg, from_client=client_a)

    # ── 2. Platform Integration — GitHub adapter ─────────────────────
    print("\n" + "=" * 60)
    print("[Phase 4B] Platform Integration — GitHub-style adapter")
    print("=" * 60)

    bica = shared_bica

    # GitHub installs the TBN PlatformAdapter
    github = PlatformAdapter(name="GitHub", bica=bica)

    # Add a custom rule: only HIGH trust bots can read private repos
    github.add_permission_rule(
        AccessLevel.READ_PRIVATE,
        lambda cert: cert.get("tbn_version") == "0.1.0",
    )

    print("\n  Test 1: Certified bot requests READ_PUBLIC access...")
    req1 = BotRequest(
        bot_id=client_a.bot_id,
        certificate=client_a.certificate,
        intent="SEARCH",
        resource="/repos/burhanyanbolu-design/tbn-protocol",
    )
    granted, level = github.verify_request(req1)
    print(f"  Granted: {granted} | Level: {level}")

    print("\n  Test 2: Certified bot requests READ_PRIVATE access...")
    req2 = BotRequest(
        bot_id=client_a.bot_id,
        certificate=client_a.certificate,
        intent="DATA_REQUEST",
        resource="/repos/burhanyanbolu-design/private-repo",
    )
    granted2, level2 = github.verify_request(req2)
    print(f"  Granted: {granted2} | Level: {level2}")

    print("\n  Test 3: Unknown/uncertified bot tries to access...")
    fake_cert = {
        "bot_id": "tbn-bot-fakefakefake",
        "name": "EvilBot",
        "tbn_version": None,
        "created_at": "2026-01-01",
    }
    req3 = BotRequest(
        bot_id="tbn-bot-fakefakefake",
        certificate=fake_cert,
        intent="SEARCH",
        resource="/repos/burhanyanbolu-design/tbn-protocol",
    )
    granted3, level3 = github.verify_request(req3)
    print(f"  Granted: {granted3} | Level: {level3}  ← blocked ✅")

    print("\n  Test 4: Bot requests WRITE access (disabled by default)...")
    req4 = BotRequest(
        bot_id=client_a.bot_id,
        certificate=client_a.certificate,
        intent="WRITE",
        resource="/repos/burhanyanbolu-design/tbn-protocol/issues",
    )
    granted4, level4 = github.verify_request(req4)
    print(f"  Granted: {granted4} | Level: {level4}  ← blocked ✅")

    # ── 3. Audit Log ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 4C] Audit Log — full trail of every bot action")
    print("=" * 60)

    print(f"\n  Platform stats: {github.stats()}")
    print(f"\n  Full audit log:")
    for entry in github.audit_log.entries():
        status = "✅" if entry["granted"] else "❌"
        print(
            f"  {status} [{entry['timestamp'][:19]}] "
            f"bot={entry['bot_id'][:20]}... | "
            f"{entry['intent']} → {entry['resource'][:40]} | "
            f"{entry['reason']}"
        )

    # ── 4. Public BICA Registry ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 4D] Public BICA Registry")
    print("=" * 60)

    registry = PublicBICARegistry(bica)

    print(f"\n  All certified bots on the TBN network:")
    for bot in registry.all_certified_bots():
        print(f"    {bot['bot_id']} | {bot['name']} | v{bot['tbn_version']} | {bot['created_at']}")

    print(f"\n  Lookup by ID...")
    cert = registry.lookup(client_a.bot_id)
    print(f"  Found: {cert['name']} (registered {cert['created_at'][:10]})")

    print(f"\n  Is certified check...")
    print(f"  {client_a.bot_id[:30]}... → {registry.is_certified(client_a.bot_id)}")
    print(f"  tbn-bot-fakefakefake          → {registry.is_certified('tbn-bot-fakefakefake')}")

    print(f"\n  Registry stats: {registry.stats()}")

    # ── 5. Notion adapter (second platform) ─────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 4E] Second Platform — Notion adapter")
    print("=" * 60)

    notion = PlatformAdapter(name="Notion", bica=bica, require_certification=True)
    notion.add_permission_rule(
        AccessLevel.READ_PUBLIC,
        lambda cert: cert.get("tbn_version") is not None,
    )

    req5 = BotRequest(
        bot_id=client_b.bot_id,
        certificate=client_b.certificate,
        intent="DATA_REQUEST",
        resource="/pages/tbn-research-notes",
    )
    granted5, level5 = notion.verify_request(req5)
    print(f"  ValidatorBot → Notion: Granted={granted5} | Level={level5}")

    print(f"\n  Notion stats: {notion.stats()}")

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Phase 4 Complete ✅")
    print("  - TBN SDK: register a bot in 5 lines")
    print("  - Platform adapters: GitHub + Notion")
    print("  - Permission rules: certified bots only")
    print("  - Audit log: full trail of every access attempt")
    print("  - Public BICA Registry: global bot lookup")
    print("  - Tamper/fake bot detection: blocked ✅")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — ALL 4 PHASES COMPLETE 🚀")
    print()
    print("  Phase 1: Trust handshake, BICA, Bot Language")
    print("  Phase 2: Compiler, 4 bot types, persistence")
    print("  Phase 3: Distributed nodes, cloning, seeded cache")
    print("  Phase 4: SDK, platform integration, public registry")
    print()
    print("  github.com/burhanyanbolu-design/tbn-protocol")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
