"""Approve Ishaan's partner application."""
import json

PARTNER_FILE = "data/partner_applications.json"

with open(PARTNER_FILE, "r") as f:
    partners = json.load(f)

for p in partners:
    if p.get("company_name") == "Shango" and p.get("contact_name") == "Ishaan Ghosh":
        p["status"] = "approved"
        print(f"Approved: {p['company_name']} ({p['contact_name']})")
        print(f"Email: {p['email']}")
        print(f"Purpose: {p['purpose'][:80]}...")
        break

with open(PARTNER_FILE, "w") as f:
    json.dump(partners, f, indent=2)

print("\nDone. API key will be issued on the call.")
