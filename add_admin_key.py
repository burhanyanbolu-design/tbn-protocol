"""Add admin API key for testing."""
import json

KEY_FILE = "data/api_keys.json"
KEY_HASH = "ec9da9a171b5d766c09975e72a70f55ea2d81275ff32269812d344c76d4491c0"

with open(KEY_FILE, "r") as f:
    keys = json.load(f)

keys[KEY_HASH] = {
    "key_hash": KEY_HASH,
    "company": "Hardin Admin",
    "email": "burhan@hardinai.co.uk",
    "tier": "ENTERPRISE",
    "active": True,
    "created_at": "2026-05-19T00:00:00+00:00",
    "expires_at": "2027-05-19T00:00:00+00:00",
    "calls_today": 0,
    "calls_total": 0,
    "last_call_date": None,
    "bots_accessed": []
}

with open(KEY_FILE, "w") as f:
    json.dump(keys, f, indent=2)

print("Admin key added successfully")
print("Use: Authorization: Bearer tbn_live_hardin_admin_2026")
