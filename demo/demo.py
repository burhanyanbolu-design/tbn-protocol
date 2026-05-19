"""
TBN Protocol — Phase 1 MVP Demo
================================
Two bots (Alpha and Beta) perform a full trust handshake
and exchange verified Bot Language messages.

Run:
    python demo.py
"""

from tbn.identity import BICA
from tbn.bot import Bot
from tbn.bot_language import Intent


def main():
    print("\n" + "=" * 60)
    print("  TBN PROTOCOL — Phase 1 MVP Demo")
    print("  Trusted Bot Network v0.1.0")
    print("=" * 60)

    # ── 1. Boot the BICA (trust registry) ───────────────────────────
    print("\n[Boot] Starting BICA trust registry...")
    bica = BICA()

    # ── 2. Create two bots (they auto-register with BICA) ───────────
    print("\n[Boot] Creating bots...")
    alpha = Bot(name="Alpha", bica=bica)
    beta = Bot(name="Beta", bica=bica)

    print(f"\n  Alpha ID : {alpha.bot_id}")
    print(f"  Beta ID  : {beta.bot_id}")

    # ── 3. Trust handshake ───────────────────────────────────────────
    print("\n[Handshake] Alpha initiating trust handshake with Beta...")
    channel = alpha.connect(beta)

    # ── 4. Data exchange over the trusted channel ────────────────────
    print("\n[Exchange] Sending messages over trusted channel...\n")

    # Alpha sends a data request
    request = alpha.send(
        to=beta,
        intent=Intent.DATA_REQUEST,
        data={
            "QUERY": "Find trusted AI tools for small businesses",
            "FILTERS": {"audience": "small_business"},
            "PRIORITY": 1,
        },
    )

    # Beta verifies and receives it
    beta.receive(request, from_bot=alpha)

    # Beta sends a data response
    response = beta.send(
        to=alpha,
        intent=Intent.DATA_RESPONSE,
        data={
            "RESULTS": [
                {"name": "Hardin AI", "url": "https://hardin-ai-search.vercel.app", "trust": "HIGH"},
                {"name": "OpenAI", "url": "https://openai.com", "trust": "HIGH"},
            ],
            "RESULT_COUNT": 2,
            "STATUS": "SUCCESS",
        },
    )

    # Alpha verifies and receives it
    alpha.receive(response, from_bot=beta)

    # ── 5. Show a full BL message ────────────────────────────────────
    print("\n[BL Message] Full Bot Language message (response):")
    print("-" * 60)
    print(response.to_json())

    # ── 6. Tamper test — prove signatures work ───────────────────────
    print("\n[Security] Tamper test — modifying message after signing...")
    response.payload["RESULTS"] = [{"name": "EVIL BOT", "url": "http://evil.com"}]
    tamper_result = alpha.receive(response, from_bot=beta)
    print(f"  Tampered message accepted: {tamper_result}  ← should be False ✅")

    print("\n" + "=" * 60)
    print("  Phase 1 MVP Complete ✅")
    print("  - Two bots with cryptographic IDs")
    print("  - BICA trust registry")
    print("  - Trust handshake (3-step)")
    print("  - Signed Bot Language messages")
    print("  - Tamper detection")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
