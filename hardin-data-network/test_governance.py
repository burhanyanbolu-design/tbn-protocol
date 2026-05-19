import requests

BASE = "http://127.0.0.1:5004/api/govern"

print("=== TESTING GOVERNANCE ENGINE ===\n")

# 1. Trust Ledger - add entry
print("[1] Trust Ledger - Add entry")
r = requests.post(f"{BASE}/ledger", json={
    "bot_id": "football-bot-001",
    "company": "Hardin AI Solutions",
    "action": "READ",
    "resource": "/data/football_matches",
    "outcome": "SUCCESS"
})
print(f"  Status: {r.status_code} - {r.json()}\n")

# 2. Add more entries
for i in range(3):
    requests.post(f"{BASE}/ledger", json={
        "bot_id": "currency-bot-001",
        "company": "Test Company Ltd",
        "action": "READ",
        "resource": "/data/currency_rates",
        "outcome": "SUCCESS"
    })

# 3. Verify ledger
print("[2] Trust Ledger - Verify chain")
r = requests.get(f"{BASE}/ledger/verify")
print(f"  {r.json()}\n")

# 4. Get ledger entries
print("[3] Trust Ledger - Get entries")
r = requests.get(f"{BASE}/ledger/Hardin AI Solutions")
d = r.json()
print(f"  {len(d.get('entries', []))} entries found\n")

# 5. Rules check
print("[4] Rules Engine - Check action")
r = requests.post(f"{BASE}/rules/check", json={
    "bot_id": "football-bot-001",
    "company": "Hardin AI Solutions",
    "action": "READ"
})
print(f"  {r.json()}\n")

# 6. Compliance report - GDPR
print("[5] Compliance Report - GDPR")
r = requests.post(f"{BASE}/compliance/report", json={
    "company": "Hardin AI Solutions",
    "framework": "GDPR"
})
d = r.json()
print(f"  Status: {d.get('status')}")
print(f"  Score: {d.get('summary', {}).get('compliance_score')}%")
print(f"  Controls: {len(d.get('controls', []))} checked\n")

# 7. Compliance report - EU AI Act
print("[6] Compliance Report - EU AI Act")
r = requests.post(f"{BASE}/compliance/report", json={
    "company": "Hardin AI Solutions",
    "framework": "EU_AI_ACT"
})
d = r.json()
print(f"  Status: {d.get('status')}")
print(f"  Risk Level: {d.get('risk_level')}")
print(f"  Score: {d.get('summary', {}).get('compliance_score')}%\n")

# 8. Dashboard
print("[7] Governance Dashboard")
r = requests.get(f"{BASE}/dashboard/Hardin AI Solutions")
d = r.json()
print(f"  Active bots: {d.get('active_bots')}")
print(f"  Ledger entries: {d.get('trust_ledger', {}).get('total_entries')}")
print(f"  Chain valid: {d.get('trust_ledger', {}).get('chain_valid')}")
print(f"  Alerts: {d.get('alerts', {}).get('count')}")
print(f"  GDPR: {d.get('compliance', {}).get('gdpr')}")

print("\n=== ALL GOVERNANCE TESTS PASSED ===")
