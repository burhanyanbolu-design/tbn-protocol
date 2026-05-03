"""
TBN Protocol — Phase 2 Demo
=============================
Demonstrates:
  1. Bot Language Compiler (natural language → BL message)
  2. All 4 bot types working together
  3. BICA registry persisted to JSON
  4. Messenger Bot routing between bots

Run:
    python demo_phase2.py
"""

from tbn.identity import BICA
from tbn.compiler import BotLanguageCompiler
from tbn.bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot
from tbn.bot_language import Intent


def main():
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — Phase 2 Demo")
    print("  Bot Language Compiler + 4 Bot Types")
    print("=" * 60)

    # ── 1. Boot BICA with persistence ───────────────────────────────
    print("\n[Boot] Starting BICA (persistent registry)...")
    bica = BICA(registry_path="data/bica_registry.json")

    # ── 2. Create the 4 bot types ────────────────────────────────────
    print("\n[Boot] Creating bot network...")
    search  = SearchBot(name="SearchBot-1", bica=bica)
    validator = ValidatorBot(name="ValidatorBot-1", bica=bica)
    connector = ConnectorBot(name="ConnectorBot-1", bica=bica)
    messenger = MessengerBot(name="MessengerBot-1", bica=bica)

    print(f"\n  SearchBot    : {search.bot_id}")
    print(f"  ValidatorBot : {validator.bot_id}")
    print(f"  ConnectorBot : {connector.bot_id}")
    print(f"  MessengerBot : {messenger.bot_id}")

    # ── 3. Load search index ─────────────────────────────────────────
    print("\n[SearchBot] Loading knowledge index...")
    search.add_to_index({
        "name": "Hardin AI Search",
        "url": "https://hardin-ai-search.vercel.app",
        "category": "AI Tools",
        "audience": "small business",
        "trust": "HIGH",
    })
    search.add_to_index({
        "name": "OpenAI API",
        "url": "https://openai.com",
        "category": "AI Platform",
        "audience": "developer",
        "trust": "HIGH",
    })
    search.add_to_index({
        "name": "HuggingFace",
        "url": "https://huggingface.co",
        "category": "AI Models",
        "audience": "developer",
        "trust": "HIGH",
    })
    search.add_to_index({
        "name": "Notion AI",
        "url": "https://notion.so",
        "category": "Productivity AI",
        "audience": "small business",
        "trust": "MEDIUM",
    })
    print(f"  Index loaded: {len(search._index)} records")

    # ── 4. Bot Language Compiler ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Compiler] Translating human query → Bot Language")
    print("=" * 60)

    compiler = BotLanguageCompiler()
    human_query = "Find trusted AI tools for small businesses"
    print(f"\n  Human input : \"{human_query}\"")

    bl_message = compiler.compile(
        text=human_query,
        sender_id="human-entry-point",
    )
    print(f"\n  Compiled BL message:")
    print(f"    INTENT      : {bl_message.payload['INTENT']}")
    print(f"    TRUST_LEVEL : {bl_message.payload['TRUST_LEVEL']}")
    print(f"    DATA_TYPE   : {bl_message.payload['DATA_TYPE']}")
    print(f"    FILTERS     : {bl_message.payload.get('FILTERS', {})}")
    print(f"    PRIORITY    : {bl_message.payload['PRIORITY']}")

    # ── 5. Trust handshakes ──────────────────────────────────────────
    print("\n[Network] Establishing trust channels...")
    search.connect(validator)
    search.connect(messenger)
    validator.connect(messenger)
    connector.connect(messenger)

    # ── 6. Messenger registers all routes ────────────────────────────
    messenger.register_route(search)
    messenger.register_route(validator)
    messenger.register_route(connector)

    # ── 7. Search Bot handles the compiled query ─────────────────────
    print("\n" + "=" * 60)
    print("[Pipeline] Running search → validate pipeline")
    print("=" * 60)

    print(f"\n[SearchBot] Processing query: \"{human_query}\"")
    search_results = search.handle_request(bl_message)
    print(f"  Found {search_results['RESULT_COUNT']} results")
    for r in search_results["RESULTS"]:
        print(f"    - {r['name']} ({r['url']})")

    # ── 8. Validator Bot validates the results ───────────────────────
    print(f"\n[ValidatorBot] Validating {search_results['RESULT_COUNT']} results...")

    # Send results from search to validator via trusted channel
    result_msg = search.send(
        to=validator,
        intent=Intent.DATA_RESPONSE,
        data={**search_results},
    )
    validator.receive(result_msg, from_bot=search)

    validated = validator.validate(search_results["RESULTS"])
    print(f"  Validated results:")
    for r in validated:
        print(f"    - {r['name']} | trust_score={r['trust_score']} | validated={r['validated']}")

    # ── 9. Messenger Bot routing demo ────────────────────────────────
    print("\n" + "=" * 60)
    print("[MessengerBot] Routing demo")
    print("=" * 60)

    ping_msg = search.send(
        to=messenger,
        intent=Intent.PING,
        data={"message": "Network check"},
    )
    messenger.receive(ping_msg, from_bot=search)

    # Route from search to validator via messenger
    routed = messenger.route(result_msg, from_bot=search, to_bot_id=validator.bot_id)
    print(f"  Message routed successfully: {routed}")
    print(f"  Messenger stats: {messenger.stats()}")

    # ── 10. Connector Bot demo ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("[ConnectorBot] External platform connection demo")
    print("=" * 60)
    print("\n  Fetching GitHub API (public endpoint)...")
    result = connector.fetch("github", "/zen")
    print(f"  Status : {result['STATUS']}")
    if result["STATUS"] == "SUCCESS":
        print(f"  GitHub says: {result['DATA']}")

    # ── 11. Show BICA registry ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("[BICA] Trust Registry")
    print("=" * 60)
    for bot in bica.list_bots():
        print(f"  {bot['bot_id']} | {bot['name']} | registered: {bot['created_at'][:10]}")
    print(f"\n  Registry saved to: data/bica_registry.json")

    print("\n" + "=" * 60)
    print("  Phase 2 Complete ✅")
    print("  - Bot Language Compiler")
    print("  - SearchBot, ValidatorBot, ConnectorBot, MessengerBot")
    print("  - BICA persistent registry")
    print("  - Messenger routing")
    print("  - External platform connection")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
