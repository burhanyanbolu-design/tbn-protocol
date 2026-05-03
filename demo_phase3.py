"""
TBN Protocol — Phase 3 Demo
=============================
Demonstrates:
  1. Distributed routing across 3 network nodes (London, New York, Singapore)
  2. Self-cloning bots under parallel load
  3. Seeded network cache (bots share results)

Run:
    python demo_phase3.py
"""

from tbn.identity import BICA
from tbn.network import NetworkNode
from tbn.cloning import CloneManager
from tbn.seeded_network import SeededNetwork
from tbn.bots import SearchBot, ValidatorBot, MessengerBot
from tbn.compiler import BotLanguageCompiler
from tbn.bot_language import Intent


def main():
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — Phase 3 Demo")
    print("  Distributed Routing + Self-Cloning + Seeded Network")
    print("=" * 60)

    # ── 1. Boot shared infrastructure ───────────────────────────────
    print("\n[Boot] Starting shared infrastructure...")
    bica = BICA(registry_path="data/bica_registry.json")
    seeded_net = SeededNetwork()
    clone_manager = CloneManager(bica)

    # ── 2. Create 3 network nodes ────────────────────────────────────
    print("\n[Boot] Spinning up network nodes...")
    node_london    = NetworkNode("node-lon-01", "London, UK",      bica)
    node_newyork   = NetworkNode("node-nyc-01", "New York, USA",   bica)
    node_singapore = NetworkNode("node-sgp-01", "Singapore",       bica)

    # ── 3. Connect nodes as peers ────────────────────────────────────
    print("\n[Network] Connecting peer nodes...")
    node_london.connect_peer(node_newyork)
    node_newyork.connect_peer(node_singapore)
    node_london.connect_peer(node_singapore)

    # ── 4. Deploy bots across nodes ──────────────────────────────────
    print("\n[Deploy] Deploying bots across nodes...")

    # London node — search + validator
    search_lon = SearchBot("SearchBot-London", bica)
    validator_lon = ValidatorBot("ValidatorBot-London", bica)
    node_london.add_bot(search_lon)
    node_london.add_bot(validator_lon)

    # New York node — search + messenger
    search_nyc = SearchBot("SearchBot-NewYork", bica)
    messenger_nyc = MessengerBot("MessengerBot-NewYork", bica)
    node_newyork.add_bot(search_nyc)
    node_newyork.add_bot(messenger_nyc)

    # Singapore node — search + validator
    search_sgp = SearchBot("SearchBot-Singapore", bica)
    validator_sgp = ValidatorBot("ValidatorBot-Singapore", bica)
    node_singapore.add_bot(search_sgp)
    node_singapore.add_bot(validator_sgp)

    # ── 5. Load knowledge into search bots ──────────────────────────
    ai_tools = [
        {"name": "Hardin AI Search",  "url": "https://hardin-ai-search.vercel.app", "category": "AI Search",      "audience": "small business", "region": "global"},
        {"name": "OpenAI API",        "url": "https://openai.com",                  "category": "AI Platform",    "audience": "developer",      "region": "global"},
        {"name": "HuggingFace",       "url": "https://huggingface.co",              "category": "AI Models",      "audience": "developer",      "region": "global"},
        {"name": "Notion AI",         "url": "https://notion.so",                   "category": "Productivity",   "audience": "small business", "region": "global"},
        {"name": "GitHub Copilot",    "url": "https://github.com/features/copilot", "category": "Code AI",        "audience": "developer",      "region": "global"},
        {"name": "Jasper AI",         "url": "https://jasper.ai",                   "category": "Content AI",     "audience": "small business", "region": "us"},
        {"name": "Midjourney",        "url": "https://midjourney.com",              "category": "Image AI",       "audience": "developer",      "region": "global"},
        {"name": "Anthropic Claude",  "url": "https://anthropic.com",               "category": "AI Platform",    "audience": "enterprise",     "region": "global"},
    ]

    for tool in ai_tools:
        search_lon.add_to_index(tool)
        search_nyc.add_to_index(tool)
        search_sgp.add_to_index(tool)

    print(f"\n  Each search bot loaded with {len(ai_tools)} records")

    # ── 6. Distributed routing demo ─────────────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 3A] Distributed Routing")
    print("=" * 60)

    # Route a message from London to a bot on Singapore
    print(f"\n  Routing from London → Singapore...")
    node_london.route_message(
        msg=None,  # simplified for routing demo
        target_bot_id=search_sgp.bot_id,
    )

    # Route from New York to London
    print(f"\n  Routing from New York → London...")
    node_newyork.route_message(
        msg=None,
        target_bot_id=validator_lon.bot_id,
    )

    # Find a bot by type across the network
    print(f"\n  Finding a ValidatorBot anywhere on the network from New York...")
    found = node_newyork.find_bot_by_type("VALIDATOR")
    print(f"  Found: {found}")

    # ── 7. Self-cloning under parallel load ─────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 3B] Self-Cloning Under Parallel Load")
    print("=" * 60)

    # Simulate 5 simultaneous queries hitting the London search bot
    parallel_queries = [
        {"query": "AI tools for small business", "filters": {}},
        {"query": "developer AI platforms",      "filters": {}},
        {"query": "code AI tools",               "filters": {}},
        {"query": "content AI small business",   "filters": {}},
        {"query": "image generation AI",         "filters": {}},
    ]

    print(f"\n  {len(parallel_queries)} queries arriving simultaneously at SearchBot-London")
    print(f"  Clone threshold: {3} tasks → spawning clones...\n")

    merged_results = clone_manager.parallel_search(search_lon, parallel_queries)

    print(f"\n  Merged unique results: {len(merged_results)}")
    for r in merged_results:
        print(f"    - {r['name']}")

    print(f"\n  Clone stats: {clone_manager.stats()}")

    # ── 8. Seeded network cache ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Phase 3C] Seeded Network Cache")
    print("=" * 60)

    # London bot seeds its results
    print("\n  SearchBot-London seeding results to network...")
    compiler = BotLanguageCompiler()
    query1 = "Find trusted AI tools for small businesses"
    bl_msg = compiler.compile(query1, sender_id=search_lon.bot_id)
    results1 = search_lon.handle_request(bl_msg)
    seeded_net.seed(query1, results1["RESULTS"], search_lon.bot_id)

    # New York bot seeds different results
    query2 = "developer AI platforms and APIs"
    bl_msg2 = compiler.compile(query2, sender_id=search_nyc.bot_id)
    results2 = search_nyc.handle_request(bl_msg2)
    seeded_net.seed(query2, results2["RESULTS"], search_nyc.bot_id)

    # Singapore bot checks cache before searching (exact hit)
    print("\n  SearchBot-Singapore checking cache before searching...")
    cached = seeded_net.lookup(query1)
    if cached:
        print(f"  ⚡ Used cached results — no search needed!")
        for r in cached:
            print(f"    - {r['name']}")

    # Fuzzy match test
    print("\n  Testing fuzzy cache lookup...")
    fuzzy_query = "trusted AI tools businesses"
    fuzzy_result = seeded_net.fuzzy_lookup(fuzzy_query)
    if fuzzy_result:
        print(f"  🔶 Fuzzy match found {len(fuzzy_result)} results")

    # Cache miss
    print("\n  Testing cache miss...")
    seeded_net.lookup("quantum computing hardware")

    print(f"\n  Seeded network stats: {seeded_net.stats()}")
    print(f"\n  Cached queries:")
    for entry in seeded_net.list_cache():
        print(f"    \"{entry['query']}\" | {entry['results']} results | {entry['hits']} hits")

    # ── 9. Node stats ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[Network] Node Stats")
    print("=" * 60)
    for node in [node_london, node_newyork, node_singapore]:
        s = node.stats()
        print(
            f"  {s['location']:20s} | bots={s['bots']} | "
            f"peers={s['peers']} | messages={s['messages_handled']} | "
            f"routed={s['messages_routed']}"
        )

    # ── 10. Full BICA registry ───────────────────────────────────────
    print(f"\n[BICA] {len(bica.list_bots())} bots registered (including clones)")

    print("\n" + "=" * 60)
    print("  Phase 3 Complete ✅")
    print("  - 3 distributed network nodes (London, New York, Singapore)")
    print("  - Cross-node message routing")
    print("  - Self-cloning under parallel load (5 clones, threaded)")
    print("  - Seeded network cache with fuzzy matching")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
