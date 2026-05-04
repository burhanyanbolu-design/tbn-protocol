"""
TBN Protocol — Live Network Demo
Connects to https://tbn.hardinai.co.uk and demonstrates:
1. Bot registration (cryptographic identity)
2. Trust handshake (3-step verification)
3. Encrypted message exchange
4. Platform access control

Run on ANY computer with Python 3:
    pip install requests
    python demo_live.py
"""

import requests
import json
import time
import sys

TBN_URL = "https://tbn.hardinai.co.uk"
TBN_USER = "admin"
TBN_PASS = "your-tbn-password"  # Replace with your TBN dashboard password

session = requests.Session()
session.auth = (TBN_USER, TBN_PASS)

def banner(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def step(text):
    print(f"\n>>> {text}")
    time.sleep(0.5)

def ok(text):
    print(f"    ✅ {text}")

def show(data):
    print(json.dumps(data, indent=4))

def post(endpoint, data):
    r = session.post(f"{TBN_URL}{endpoint}", json=data)
    return r.json()

def get(endpoint):
    r = session.get(f"{TBN_URL}{endpoint}")
    return r.json()

# ── DEMO ──────────────────────────────────────────────────────────────

banner("TBN PROTOCOL — LIVE NETWORK DEMO")
print(f"\n  Server: {TBN_URL}")
print("  Demonstrating: Bot Identity, Trust Handshake, Encryption")
print("\n  Press Enter to start...")
input()

# ── Step 1: Register Bot A ────────────────────────────────────────────
banner("STEP 1 — Register Bot A (SearchBot)")
step("Registering AlphaBot on the TBN network...")
bot_a = post("/api/register", {"name": "AlphaBot", "type": "SEARCH"})
if "error" in bot_a:
    print(f"Error: {bot_a['error']}")
    sys.exit(1)
ok(f"AlphaBot registered!")
ok(f"Bot ID:   {bot_a['bot_id']}")
ok(f"Cert:     {bot_a['cert_level']}")
ok(f"Message:  {bot_a['message']}")
print("\n  Press Enter to continue...")
input()

# ── Step 2: Register Bot B ────────────────────────────────────────────
banner("STEP 2 — Register Bot B (ValidatorBot)")
step("Registering BetaBot on the TBN network...")
bot_b = post("/api/register", {"name": "BetaBot", "type": "VALIDATOR"})
ok(f"BetaBot registered!")
ok(f"Bot ID:   {bot_b['bot_id']}")
ok(f"Cert:     {bot_b['cert_level']}")
print("\n  Press Enter to continue...")
input()

# ── Step 3: Trust Handshake ───────────────────────────────────────────
banner("STEP 3 — Trust Handshake")
step("AlphaBot initiating 3-step trust handshake with BetaBot...")
print("    Step 1: AlphaBot sends certificate to BetaBot")
time.sleep(0.8)
print("    Step 2: BetaBot verifies via BICA registry")
time.sleep(0.8)
print("    Step 3: BetaBot sends certificate back, AlphaBot verifies")
time.sleep(0.8)

hs = post("/api/handshake", {
    "initiator_id": bot_a["bot_id"],
    "responder_id": bot_b["bot_id"]
})
if hs.get("status") == "TRUST_ESTABLISHED":
    ok(f"Status:   {hs['status']}")
    ok(f"Channel:  {hs['channel']}")
    ok(f"Message:  {hs['message']}")
else:
    print(f"  Error: {hs}")
print("\n  Press Enter to continue...")
input()

# ── Step 4: Encrypted Search ──────────────────────────────────────────
banner("STEP 4 — Bot Language Compiler + Encrypted Search")
step("AlphaBot compiling natural language query to Bot Language...")
query = "Find trusted AI tools for small businesses"
print(f"    Human query: '{query}'")
time.sleep(0.5)

search = post("/api/search", {
    "query": query,
    "bot_id": bot_a["bot_id"]
})
if search.get("compiled"):
    ok(f"INTENT:      {search['compiled']['intent']}")
    ok(f"TRUST_LEVEL: {search['compiled']['trust_level']}")
    ok(f"DATA_TYPE:   {search['compiled']['data_type']}")
    ok(f"Results:     {search['count']} items found")
    ok(f"Source:      {search['source']}")
print("\n  Press Enter to continue...")
input()

# ── Step 5: AES-256 Encryption Demo ──────────────────────────────────
banner("STEP 5 — AES-256-GCM Encryption Demo")
step("AlphaBot encrypting message for BetaBot...")

enc = post("/api/encrypt_demo", {
    "sender_id": bot_a["bot_id"],
    "receiver_id": bot_b["bot_id"],
    "query": query
})
if "error" not in enc:
    ok(f"Sender:   {enc['sender']}")
    ok(f"Receiver: {enc['receiver']}")
    ok(f"BL Version: {enc['bl_version']}")
    print(f"\n    PLAINTEXT INTENT: {enc['plaintext_payload'].get('INTENT')}")
    print(f"    ENCRYPTED payload: {str(enc['encrypted']['payload'])[:50]}...")
    print(f"    DECRYPTED intent:  {enc['decryption']['recovered_intent']} ✅")
print("\n  Press Enter to continue...")
input()

# ── Step 6: Platform Access ───────────────────────────────────────────
banner("STEP 6 — Platform Access Control")
step("Testing certified bot vs fake bot access to GitHub...")

certified = post("/api/platform/request", {
    "bot_id": bot_a["bot_id"],
    "platform": "GitHub",
    "resource": "/repos/tbn-protocol",
    "intent": "SEARCH"
})
fake = post("/api/platform/request", {
    "bot_id": "tbn-bot-fakefakefake0000",
    "platform": "GitHub",
    "resource": "/repos/tbn-protocol",
    "intent": "SEARCH"
})

print(f"\n    Certified Bot ({bot_a['bot_id'][:20]}...):")
ok(f"Access granted: {certified['granted']} ✅")
ok(f"Access level:   {certified['access_level']}")

print(f"\n    Fake Bot (tbn-bot-fakefakefake0000):")
print(f"    ❌ Access granted: {fake['granted']} — BLOCKED")
print("\n  Press Enter to continue...")
input()

# ── Step 7: Network Stats ─────────────────────────────────────────────
banner("STEP 7 — Live Network Stats")
stats = get("/api/stats")
ok(f"Registered bots:  {stats['registered_bots']}")
ok(f"Certified bots:   {stats['certified_bots']}")
ok(f"Cache hit rate:   {stats['cache']['hit_rate']}")
ok(f"Audit requests:   {stats['audit']['total_requests']}")
ok(f"Grant rate:       {stats['audit']['grant_rate']}")

# ── Done ──────────────────────────────────────────────────────────────
banner("DEMO COMPLETE!")
print("""
  You just saw TBN Protocol in action:

  ✅ Cryptographic bot identity (BICA)
  ✅ 3-step trust handshake
  ✅ Bot Language Compiler (NL → BL)
  ✅ AES-256-GCM encryption
  ✅ Platform access control + audit log

  Live at: https://tbn.hardinai.co.uk
  GitHub:  https://github.com/burhanyanbolu-design/tbn-protocol

  Built by Burhan Yanbolu — Hardin Enterprises Ltd
""")
