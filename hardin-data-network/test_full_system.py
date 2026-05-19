"""
Step 3 — Full System Test
Tests: handshake, clone detection, seal verification, egg system
"""
import requests
import psycopg2
import json
import sys

BASE   = "http://127.0.0.1:5004"
ADMIN  = {"X-Admin-Secret": "hardin-admin-2026-secret"}
DB     = dict(dbname="hardin_data_network", user="hardin_admin", password="hardin2026", host="localhost", port=5433)

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  ❌ {msg}")

print("\n" + "="*55)
print("  TBN FULL SYSTEM TEST")
print("="*55)

# ── Test 1: Service health ────────────────────────────────
print("\n[1] Service Health")
r = requests.get(f"{BASE}/health").json()
if r.get("status") == "ok":
    ok("TBN service is running")
else:
    fail(f"Service unhealthy: {r}")

# ── Test 2: Register two bots (admin only) ────────────────
print("\n[2] Bot Registration (admin only)")
b1 = requests.post(f"{BASE}/api/register", json={"name": "TestSportsBot", "type": "SEARCH"}, headers=ADMIN).json()
b2 = requests.post(f"{BASE}/api/register", json={"name": "TestFinanceBot", "type": "VALIDATOR"}, headers=ADMIN).json()

if b1.get("bot_id"):
    ok(f"Bot 1 registered: {b1['bot_id']}")
else:
    fail(f"Bot 1 failed: {b1}")

if b2.get("bot_id"):
    ok(f"Bot 2 registered: {b2['bot_id']}")
else:
    fail(f"Bot 2 failed: {b2}")

# ── Test 3: Public registration is blocked ────────────────
print("\n[3] Public Registration Blocked")
r = requests.post(f"{BASE}/api/register", json={"name": "HackerBot", "type": "SEARCH"}).json()
if "error" in r and "not available publicly" in r["error"]:
    ok("Public registration correctly blocked")
else:
    fail(f"Public registration NOT blocked: {r}")

# ── Test 4: Handshake between two bots ───────────────────
print("\n[4] Handshake")
if b1.get("bot_id") and b2.get("bot_id"):
    hs = requests.post(f"{BASE}/api/handshake", json={
        "initiator_id": b1["bot_id"],
        "responder_id": b2["bot_id"]
    }).json()
    if hs.get("status") == "TRUST_ESTABLISHED":
        ok(f"Handshake: {b1['name']} ↔ {b2['name']}")
    else:
        fail(f"Handshake failed: {hs}")

# ── Test 5: Handshake logged to database ─────────────────
print("\n[5] Handshake Logged to Database")
try:
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tbn_handshake_log WHERE status='SUCCESS'")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    if count > 0:
        ok(f"{count} successful handshake(s) logged in database")
    else:
        fail("No handshakes in database")
except Exception as e:
    fail(f"DB check failed: {e}")

# ── Test 6: Verify a bot ─────────────────────────────────
print("\n[6] Bot Verification")
if b1.get("bot_id"):
    r = requests.post(f"{BASE}/api/verify", json={"bot_id": b1["bot_id"]}).json()
    if r.get("certified"):
        ok(f"Bot verified as certified: {b1['bot_id'][:20]}...")
    else:
        fail(f"Bot not certified: {r}")

# ── Test 7: Fake bot rejected ─────────────────────────────
print("\n[7] Fake Bot Rejected")
r = requests.post(f"{BASE}/api/verify", json={"bot_id": "tbn-bot-fakefake000000"}).json()
if not r.get("certified"):
    ok("Fake bot correctly rejected")
else:
    fail("Fake bot was NOT rejected!")

# ── Test 8: Sealed bots registry ─────────────────────────
print("\n[8] Sealed Bots Registry")
try:
    with open("/opt/tbn-protocol/data/hardin_sealed_bots.json") as f:
        sealed = json.load(f)
    if len(sealed) == 31:
        ok(f"All 31 Hardin bots sealed and in registry")
    else:
        fail(f"Only {len(sealed)} bots in sealed registry (expected 31)")
except Exception as e:
    fail(f"Sealed registry error: {e}")

# ── Test 9: Sealed bot tamper detection ──────────────────
print("\n[9] Tamper Detection")
try:
    with open("/opt/tbn-protocol/data/hardin_sealed_bots.json") as f:
        sealed = json.load(f)
    
    # Get a real seal and verify it
    bot_id = "football-bot-001"
    seal   = sealed[bot_id]["seal"]
    
    # Verify intact seal
    import sys
    sys.path.insert(0, '/opt/tbn-protocol')
    from seal_hardin_bots import verify_seal
    valid, reason = verify_seal(seal)
    if valid:
        ok("Intact seal verified correctly")
    else:
        fail(f"Valid seal failed verification: {reason}")
    
    # Tamper with the seal
    tampered = dict(seal)
    tampered["star_rating"] = 5  # try to upgrade rating
    valid2, reason2 = verify_seal(tampered)
    if not valid2:
        ok(f"Tampered seal detected: {reason2[:50]}")
    else:
        fail("Tampered seal was NOT detected!")
except Exception as e:
    fail(f"Tamper test error: {e}")

# ── Test 10: Data count ───────────────────────────────────
print("\n[10] Database Data Count")
try:
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM restaurants) +
            (SELECT COUNT(*) FROM football_matches) +
            (SELECT COUNT(*) FROM currency_rates) +
            (SELECT COUNT(*) FROM commodities) +
            (SELECT COUNT(*) FROM trade_data) +
            (SELECT COUNT(*) FROM uk_schools) +
            (SELECT COUNT(*) FROM uk_universities)
        AS sample_total
    """)
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    ok(f"Database has {total:,}+ data points (sample check)")
except Exception as e:
    fail(f"Data count error: {e}")

# ── Summary ───────────────────────────────────────────────
print("\n" + "="*55)
print(f"  RESULTS: {passed} passed  |  {failed} failed")
print("="*55 + "\n")

if failed == 0:
    print("🎉 ALL TESTS PASSED — System is fully operational!")
else:
    print(f"⚠️  {failed} test(s) need attention")
