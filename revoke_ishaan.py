"""Revoke Ishaan's API key."""
import json

KEYS_FILE = "data/api_keys.json"

with open(KEYS_FILE, "r") as f:
    keys = json.load(f)

revoked = []
for key_hash in list(keys.keys()):
    if keys[key_hash].get("company") == "Shango":
        keys[key_hash]["revoked"] = True
        revoked.append(key_hash)

with open(KEYS_FILE, "w") as f:
    json.dump(keys, f, indent=2)

print(f"Revoked {len(revoked)} key(s) for Shango/Ishaan.")
