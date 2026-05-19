"""Test the /api/verify/full and /api/verify/batch endpoints."""
import requests
import json

BASE = "http://localhost:5004"
KEY = "tbn_live_hardin_admin_2026"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {KEY}"
}

print("=" * 60)
print("TEST 1: /api/verify/full")
print("=" * 60)

resp = requests.post(f"{BASE}/api/verify/full", json={"agent_id": "tbn-bot-test123"}, headers=HEADERS)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

print("\n" + "=" * 60)
print("TEST 2: /api/verify/batch")
print("=" * 60)

resp = requests.post(f"{BASE}/api/verify/batch", json={
    "agent_ids": ["tbn-bot-test123", "tbn-bot-fake999", "tbn-bot-another"]
}, headers=HEADERS)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

print("\n" + "=" * 60)
print("TEST 3: /api/verify/cached/tbn_vrf_abc123")
print("=" * 60)

resp = requests.get(f"{BASE}/api/verify/cached/tbn_vrf_abc123", headers=HEADERS)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
