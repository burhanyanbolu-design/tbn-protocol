"""Test handshake logging"""
import requests
import json

BASE = "http://127.0.0.1:5004"

# Register two bots
print("Registering bots...")
b1 = requests.post(f"{BASE}/api/register", json={"name": "FootballBot", "type": "SEARCH"}, headers={"X-Admin-Secret": "hardin-admin-2026-secret"}).json()
b2 = requests.post(f"{BASE}/api/register", json={"name": "CurrencyBot", "type": "VALIDATOR"}, headers={"X-Admin-Secret": "hardin-admin-2026-secret"}).json()

print(f"Bot 1: {b1.get('bot_id')} - {b1.get('cert_level')}")
print(f"Bot 2: {b2.get('bot_id')} - {b2.get('cert_level')}")

# Do handshake
print("\nPerforming handshake...")
hs = requests.post(f"{BASE}/api/handshake", json={
    "initiator_id": b1["bot_id"],
    "responder_id": b2["bot_id"]
}).json()
print(f"Status: {hs.get('status')}")
print(f"Message: {hs.get('message')}")

# Check database log
print("\nChecking database log...")
import subprocess
result = subprocess.run(
    ["sudo", "-u", "postgres", "psql", "-d", "hardin_data_network", "-c",
     "SELECT initiator_bot_id, responder_bot_id, status, initiated_at FROM tbn_handshake_log ORDER BY initiated_at DESC LIMIT 5;"],
    capture_output=True, text=True, cwd="/tmp"
)
print(result.stdout)
print("DONE - handshake logged to database!")
