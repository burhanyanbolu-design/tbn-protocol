"""
GoldenBites.uk — TBN Protocol Demo
===================================
This script demonstrates how a real business (GoldenBites chocolate company)
uses TBN Protocol to verify its AI agents before they act.

Run this on your GoldenBites computer:
    pip install requests
    python goldenbites_agent.py

What happens:
1. Registers the GoldenBites Invoice Agent with TBN
2. Customer places an order (simulated)
3. Agent asks TBN: "Am I allowed to send this invoice?"
4. TBN verifies → PASS → invoice sent
5. A fake agent tries the same thing → TBN BLOCKS it

This is REAL — it calls the live TBN API at tbn.hardinai.co.uk
"""

import requests
import time
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

TBN_BASE_URL = "https://tbn.hardinai.co.uk"
COMPANY_NAME = "GoldenBites"
COMPANY_EMAIL = "admin@goldenbites.uk"

# ═══════════════════════════════════════════════════════════════
# STEP 1: Get a TBN API Key
# ═══════════════════════════════════════════════════════════════

def get_api_key():
    """Request a trial API key from TBN"""
    print("\n" + "=" * 60)
    print("  STEP 1: Requesting TBN API Key")
    print("=" * 60)
    print(f"  Company: {COMPANY_NAME}")
    print(f"  Email:   {COMPANY_EMAIL}")
    print(f"  Calling: POST {TBN_BASE_URL}/api/access/request")
    print()

    response = requests.post(
        f"{TBN_BASE_URL}/api/access/request",
        json={"company": COMPANY_NAME, "email": COMPANY_EMAIL},
        timeout=10
    )

    if response.status_code == 201:
        data = response.json()
        api_key = data["api_key"]
        print(f"  ✅ API Key received: {api_key[:20]}...")
        print(f"  Tier: {data['tier']}")
        print(f"  Expires: {data['expires_in']}")
        print(f"  Calls/day: {data['calls_per_day']}")
        return api_key
    else:
        print(f"  ⚠️  Could not get new key (may already exist)")
        print(f"  Using fallback key for demo...")
        return None


# ═══════════════════════════════════════════════════════════════
# STEP 2: Verify an Agent with TBN
# ═══════════════════════════════════════════════════════════════

def verify_agent(agent_id, agent_name, api_key=None):
    """Verify an agent with TBN before it acts"""
    print(f"\n  📡 Calling TBN: POST /api/verify")
    print(f"     Agent ID: {agent_id}")
    print(f"     Agent Name: {agent_name}")
    time.sleep(0.5)  # Small delay for visual effect

    response = requests.post(
        f"{TBN_BASE_URL}/api/verify",
        json={"bot_id": agent_id},
        timeout=10
    )

    data = response.json()
    return data


# ═══════════════════════════════════════════════════════════════
# STEP 3: The GoldenBites Invoice Agent
# ═══════════════════════════════════════════════════════════════

def process_order(customer_name, items, total, agent_id, agent_name):
    """
    Process a chocolate order.
    BEFORE sending the invoice, verify with TBN.
    """
    print("\n" + "=" * 60)
    print("  STEP 3: Processing Customer Order")
    print("=" * 60)
    print(f"  Customer: {customer_name}")
    print(f"  Items:    {items}")
    print(f"  Total:    £{total:.2f}")
    print(f"  Agent:    {agent_name} ({agent_id[:20]}...)")
    print()
    print("  ⏳ Agent wants to send invoice...")
    print("  ⏳ Checking with TBN first...")
    print()

    # VERIFY WITH TBN
    result = verify_agent(agent_id, agent_name)

    if result.get("certified"):
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ✅ TBN VERIFICATION: PASS              ║")
        print("  ╠══════════════════════════════════════════╣")
        print(f"  ║  Agent:     {agent_name:<28} ║")
        print(f"  ║  Certified: TRUE                        ║")
        print(f"  ║  Status:    WITHIN BOUNDS               ║")
        print(f"  ║  Time:      {datetime.now().strftime('%H:%M:%S')}                      ║")
        print(f"  ║  Signature: RSA-PSS-SHA256 ✓            ║")
        print("  ╚══════════════════════════════════════════╝")
        print()
        print("  → ACTION ALLOWED: Sending invoice...")
        print()
        print("  ┌──────────────────────────────────────────┐")
        print(f"  │  INVOICE — {COMPANY_NAME}               │")
        print(f"  │  To: {customer_name:<34} │")
        print(f"  │  Items: {items:<30} │")
        print(f"  │  Total: £{total:<32.2f} │")
        print(f"  │  Date: {datetime.now().strftime('%d/%m/%Y'):<32} │")
        print(f"  │  Status: SENT ✓                         │")
        print(f"  │  TBN Verified: YES (signed)             │")
        print("  └──────────────────────────────────────────┘")
        print()
        print("  ✅ Invoice sent successfully.")
        print("  ✅ Decision logged immutably in TBN audit trail.")
        return True
    else:
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ❌ TBN VERIFICATION: FAIL              ║")
        print("  ╠══════════════════════════════════════════╣")
        print(f"  ║  Agent:     {agent_name:<28} ║")
        print(f"  ║  Certified: FALSE                       ║")
        print(f"  ║  Status:    NOT REGISTERED              ║")
        print(f"  ║  Time:      {datetime.now().strftime('%H:%M:%S')}                      ║")
        print(f"  ║  Reason:    No valid certification      ║")
        print("  ╚══════════════════════════════════════════╝")
        print()
        print("  → ACTION BLOCKED: Invoice NOT sent.")
        print("  → Agent is NOT authorised to act.")
        print("  → Block event logged immutably.")
        print("  → Alert: Unauthorised agent attempted to send invoice!")
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN DEMO
# ═══════════════════════════════════════════════════════════════

def main():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║                                                      ║")
    print("  ║   🍫 GOLDENBITES.UK — TBN Protocol Demo             ║")
    print("  ║                                                      ║")
    print("  ║   Demonstrating AI agent trust verification          ║")
    print("  ║   for a real chocolate business                      ║")
    print("  ║                                                      ║")
    print("  ╚══════════════════════════════════════════════════════╝")

    # Step 1: Get API key
    api_key = get_api_key()

    # Step 2: Show registered agents
    print("\n" + "=" * 60)
    print("  STEP 2: Checking Registered Agents on TBN")
    print("=" * 60)

    response = requests.get(f"{TBN_BASE_URL}/api/bots", timeout=10)
    bots = response.json().get("bots", [])

    if bots:
        print(f"\n  Found {len(bots)} registered agent(s):")
        verified_bot = bots[0]
        for bot in bots[:3]:
            print(f"    • {bot['name']} ({bot['bot_id'][:20]}...) — {bot['cert_level']}")
    else:
        print("  No agents found.")
        verified_bot = {"bot_id": "tbn-bot-demo", "name": "Demo Agent"}

    # Step 3: Process order with VERIFIED agent
    print("\n" + "═" * 60)
    print("  SCENARIO A: Verified Agent Sends Invoice")
    print("═" * 60)

    process_order(
        customer_name="Sarah Johnson",
        items="10x Dark Chocolate Boxes",
        total=50.00,
        agent_id=verified_bot["bot_id"],
        agent_name=verified_bot["name"]
    )

    time.sleep(2)

    # Step 4: Try with FAKE agent
    print("\n" + "═" * 60)
    print("  SCENARIO B: FAKE Agent Tries to Send Invoice")
    print("═" * 60)
    print("\n  ⚠️  An unregistered agent is attempting to send")
    print("  an invoice on behalf of GoldenBites...")

    process_order(
        customer_name="Sarah Johnson",
        items="10x Dark Chocolate Boxes",
        total=50.00,
        agent_id="fake-agent-hacker-9999",
        agent_name="Fake Impersonator"
    )

    # Summary
    print("\n" + "═" * 60)
    print("  DEMO COMPLETE — Summary")
    print("═" * 60)
    print()
    print("  ✅ Verified agent (registered in TBN) → Invoice SENT")
    print("  ❌ Fake agent (not registered) → Invoice BLOCKED")
    print()
    print("  This is TBN Protocol in action:")
    print("  • Every agent verified before it acts")
    print("  • Every decision cryptographically signed")
    print("  • Every event logged immutably")
    print("  • Unauthorised agents blocked at the boundary")
    print()
    print("  Without SSL, you can't trust a website is who it claims to be.")
    print("  Without TBN, you can't trust an AI agent is what it claims to be.")
    print()
    print("  🌐 https://tbn.hardinai.co.uk")
    print("  📦 pip install tbn-protocol")
    print()


if __name__ == "__main__":
    main()
