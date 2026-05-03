"""
TBN Protocol — Bot Language v2 Demo
=====================================
Demonstrates the full Bot Language specification:

  1. BL v2 message structure
  2. Bot Language Compiler (NL → BL)
  3. AES-256-GCM payload encryption
  4. RSA session key exchange
  5. Payload integrity verification
  6. CompilerBot handling COMPILE requests
  7. All Intent types
  8. Tamper detection on encrypted messages

Run:
    python demo_bot_language.py
"""

import json
from tbn.identity import BICA, BotIdentity
from tbn.bot_language import BotMessage, Intent, TrustLevel, Target, DataType
from tbn.compiler import BotLanguageCompiler, CompilerBot
from tbn.bots import SearchBot, ValidatorBot


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print("\n" + "="*60)
    print("  TBN — Bot Language v2.0 Demo")
    print("  Encrypted · Signed · Structured")
    print("="*60)

    bica = BICA()

    # ── 1. Create bots ───────────────────────────────────────────────
    section("1. Creating Bots")
    alice   = SearchBot("Alice",   bica)
    bob     = ValidatorBot("Bob",  bica)
    compiler_bot = CompilerBot("CompilerBot-1", bica)

    print(f"  Alice   : {alice.bot_id}")
    print(f"  Bob     : {bob.bot_id}")
    print(f"  Compiler: {compiler_bot.bot_id}")

    # ── 2. Bot Language Compiler ─────────────────────────────────────
    section("2. Bot Language Compiler — NL → BL")

    compiler = BotLanguageCompiler()
    queries = [
        "Find trusted AI tools for small businesses",
        "Search for verified developer AI platforms",
        "Get private GitHub repositories for the project",
        "Validate these search results urgently",
        "Ping the network",
    ]

    for q in queries:
        msg = compiler.compile(q, sender_id=alice.bot_id)
        print(f"\n  Input : \"{q}\"")
        print(f"  INTENT      : {msg.payload['INTENT']}")
        print(f"  TARGET      : {msg.payload['TARGET']}")
        print(f"  TRUST_LEVEL : {msg.payload['TRUST_LEVEL']}")
        print(f"  DATA_TYPE   : {msg.payload.get('DATA_TYPE', '-')}")
        print(f"  PRIORITY    : {msg.payload.get('PRIORITY', '-')}")
        if "FILTERS" in msg.payload:
            print(f"  FILTERS     : {msg.payload['FILTERS']}")

    # ── 3. Unencrypted BL v2 message ─────────────────────────────────
    section("3. BL v2 Message — Signed, Unencrypted")

    msg_plain = BotMessage(
        sender_id=alice.bot_id,
        intent=Intent.DATA_REQUEST,
        trust_level=TrustLevel.HIGH,
        target=Target.VERIFIED_SOURCES,
        data={
            "QUERY":     "Find trusted AI tools",
            "DATA_TYPE": DataType.AI_TOOLS.value,
            "PRIORITY":  1,
        },
        receiver_id=bob.bot_id,
    )
    msg_plain.sign(alice.identity)

    print(f"\n  Message: {msg_plain}")
    print(f"\n  Full BL v2 message (unencrypted):")
    d = msg_plain.to_dict()
    print(f"    bl_version   : {d['bl_version']}")
    print(f"    message_id   : {d['message_id']}")
    print(f"    sender_id    : {d['sender_id']}")
    print(f"    receiver_id  : {d['receiver_id']}")
    print(f"    timestamp    : {d['timestamp']}")
    print(f"    encrypted    : {d['encrypted']}")
    print(f"    signature    : {d['signature'][:40]}...")
    print(f"    payload      : {json.dumps(d['payload'], indent=6)}")

    # ── 4. Encrypted BL v2 message ───────────────────────────────────
    section("4. BL v2 Message — AES-256-GCM Encrypted")

    msg_enc = BotMessage(
        sender_id=alice.bot_id,
        intent=Intent.DATA_REQUEST,
        trust_level=TrustLevel.HIGH,
        target=Target.VERIFIED_SOURCES,
        data={
            "QUERY":     "Find trusted AI tools for small businesses",
            "DATA_TYPE": DataType.AI_TOOLS.value,
            "FILTERS":   {"audience": "SMALL_BUSINESS"},
            "PRIORITY":  1,
        },
        receiver_id=bob.bot_id,
    )

    print(f"\n  Before encryption:")
    print(f"    INTENT  : {msg_enc.payload['INTENT']}")
    print(f"    QUERY   : {msg_enc.payload['QUERY']}")
    print(f"    encrypted: {msg_enc.encrypted}")

    # Encrypt with Bob's public key
    msg_enc.encrypt(bob.identity.public_key_pem())
    msg_enc.sign(alice.identity)

    print(f"\n  After encryption:")
    d_enc = msg_enc.to_dict()
    print(f"    encrypted    : {d_enc['encrypted']} 🔒")
    print(f"    payload_hash : {d_enc['payload_hash']}")
    print(f"    session_key  : {d_enc['session_key'][:40]}... (RSA-encrypted AES key)")
    print(f"    payload      : {str(d_enc['payload'])[:60]}... (AES-256-GCM ciphertext)")
    print(f"    signature    : {d_enc['signature'][:40]}...")

    # ── 5. Decryption ────────────────────────────────────────────────
    section("5. Decryption — Bob Receives and Decrypts")

    print(f"\n  Bob decrypting message...")
    success = msg_enc.decrypt(bob.identity._private_key)
    print(f"  Decryption success : {success} ✅")
    print(f"  encrypted flag     : {msg_enc.encrypted} (now False)")
    print(f"  Recovered INTENT   : {msg_enc.payload['INTENT']}")
    print(f"  Recovered QUERY    : {msg_enc.payload['QUERY']}")
    print(f"  Recovered FILTERS  : {msg_enc.payload.get('FILTERS')}")

    # ── 6. Integrity check — tamper detection ────────────────────────
    section("6. Integrity Check — Tamper Detection")

    # Re-encrypt a fresh message
    msg_tamper = BotMessage(
        sender_id=alice.bot_id,
        intent=Intent.DATA_REQUEST,
        trust_level=TrustLevel.HIGH,
        target=Target.VERIFIED_SOURCES,
        data={"QUERY": "legitimate query", "PRIORITY": 1},
        receiver_id=bob.bot_id,
    )
    msg_tamper.encrypt(bob.identity.public_key_pem())
    msg_tamper.sign(alice.identity)

    print(f"\n  Original payload hash : {msg_tamper.payload_hash}")

    # Tamper with the ciphertext
    import base64
    raw = base64.b64decode(msg_tamper._payload_ciphertext)
    tampered = raw[:20] + bytes([raw[20] ^ 0xFF]) + raw[21:]  # flip one bit
    msg_tamper._payload_ciphertext = base64.b64encode(tampered).decode()

    print(f"  Tampering with ciphertext (flipping one bit)...")
    result = msg_tamper.decrypt(bob.identity._private_key)
    print(f"  Decryption after tamper : {result}  ← should be False ✅")

    # ── 7. CompilerBot handling COMPILE requests ─────────────────────
    section("7. CompilerBot — Handling COMPILE Requests from Network")

    # Alice sends a COMPILE request to the CompilerBot
    compile_request = BotMessage(
        sender_id=alice.bot_id,
        intent=Intent.COMPILE,
        trust_level=TrustLevel.HIGH,
        target=Target.NETWORK,
        data={"QUERY": "Find verified developer AI platforms urgently"},
        receiver_id=compiler_bot.bot_id,
    )
    compile_request.sign(alice.identity)

    print(f"\n  Alice → CompilerBot: {compile_request}")
    result = compiler_bot.handle_compile_request(compile_request)

    print(f"\n  CompilerBot response:")
    print(f"    STATUS  : {result['STATUS']}")
    print(f"    QUERY   : {result['QUERY']}")
    print(f"    INTENT  : {result['INTENT']}")
    print(f"    TARGET  : {result['TARGET']}")
    print(f"    TRUST   : {result['TRUST']}")

    # ── 8. All Intent types ──────────────────────────────────────────
    section("8. All BL v2 Intent Types")

    intents = [
        (Intent.SEARCH,             "Find AI tools"),
        (Intent.DATA_REQUEST,       "Request dataset"),
        (Intent.DATA_RESPONSE,      "Here are the results"),
        (Intent.VALIDATE,           "Validate these results"),
        (Intent.VALIDATE_RESPONSE,  "Validation complete"),
        (Intent.COMPILE,            "Compile this query"),
        (Intent.COMPILE_RESPONSE,   "Compiled message"),
        (Intent.PING,               "Network check"),
        (Intent.PONG,               "I am alive"),
        (Intent.CLONE_REQUEST,      "Need a clone"),
        (Intent.CLONE_READY,        "Clone is ready"),
        (Intent.ERROR,              "Something went wrong"),
    ]

    for intent, desc in intents:
        msg = BotMessage(
            sender_id=alice.bot_id,
            intent=intent,
            data={"NOTE": desc},
        )
        print(f"  {intent.value:<22} → {msg}")

    # ── Summary ──────────────────────────────────────────────────────
    section("Bot Language v2 — Summary")
    print("""
  ✅ BL v2 message structure (envelope + encrypted payload)
  ✅ Bot Language Compiler (NL → BL, 5 query types)
  ✅ AES-256-GCM payload encryption
  ✅ RSA-encrypted session key per message
  ✅ SHA-256 payload integrity hash
  ✅ RSA-PSS message signing
  ✅ Tamper detection (bit-flip caught)
  ✅ CompilerBot handling COMPILE requests
  ✅ 12 Intent types
  ✅ TARGET field (VERIFIED_SOURCES, RESTRICTED, PLATFORM, NETWORK)

  Spec: docs/BOT-LANGUAGE-SPEC.md
    """)


if __name__ == "__main__":
    main()
