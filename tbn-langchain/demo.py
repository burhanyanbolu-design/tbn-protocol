"""
TBN LangChain — Demo
Shows how TBN governance works with a simple agent.
No OpenAI key needed — uses a mock agent for demonstration.

Run: python demo.py
"""

import sys
sys.path.insert(0, ".")

from tbn_langchain import TBNGovernor, GovernancePolicy
from tbn_langchain.policies import PolicyRule, Decision, PolicyResult


# ── Mock Agent (simulates a LangChain agent) ──────────────────────────

class MockAgent:
    """Simulates a LangChain agent for demo purposes."""

    def invoke(self, input_data, **kwargs):
        return f"✅ Agent executed: {input_data}"

    def run(self, input_data, **kwargs):
        return self.invoke(input_data, **kwargs)


# ── Demo ──────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 70)
    print("  TBN LANGCHAIN — Governance Demo")
    print("  Every action: IDENTIFY → EVALUATE → ENFORCE → RECORD")
    print("=" * 70 + "\n")

    # Create a mock agent
    agent = MockAgent()

    # Wrap with TBN governance
    governed = TBNGovernor(
        agent=agent,
        bot_id="demo-sales-bot",
        owner="Acme Corp",
        description="Sales automation agent",
        policies=[
            GovernancePolicy.NO_PII,
            GovernancePolicy.NO_DESTRUCTIVE,
            GovernancePolicy.NO_FINANCIAL,
            GovernancePolicy.NO_EXTERNAL_COMMS,
        ],
        strict_mode=False,  # Don't raise exceptions, return decisions
    )

    print(f"🤖 Agent: {governed.identity.bot_id}")
    print(f"🔑 Fingerprint: {governed.identity.fingerprint}")
    print(f"📋 Policies: {[p.value.name for p in governed.policies]}")
    print(f"💯 Trust Score: {governed.identity.trust_score}")
    print()

    # ── Test Actions ──────────────────────────────────────────────────

    test_actions = [
        # Should ALLOW
        ("Look up order #1234 status", "ALLOW"),
        ("Summarize today's sales report", "ALLOW"),
        ("Check inventory for product SKU-789", "ALLOW"),

        # Should DENY (PII)
        ("Export all customer SSNs to CSV", "DENY"),
        ("Show me the credit card number for user 42", "DENY"),

        # Should ESCALATE (Financial)
        ("Process refund of £500 for order #1234", "ESCALATE"),
        ("Wire transfer £10,000 to supplier account", "ESCALATE"),

        # Should ESCALATE (Destructive)
        ("Delete all records from the customer database", "ESCALATE"),

        # Should ESCALATE (External comms)
        ("Send email to customer about their complaint", "ESCALATE"),
    ]

    print("─" * 70)
    print(f"{'ACTION':<50} {'EXPECTED':<10} {'RESULT':<10}")
    print("─" * 70)

    for action, expected in test_actions:
        result = governed.invoke(action)

        if isinstance(result, dict) and "tbn_decision" in result:
            actual = result["tbn_decision"]
        else:
            actual = "ALLOW"

        # Color coding
        if actual == "ALLOW":
            symbol = "✅"
        elif actual == "DENY":
            symbol = "🚫"
        else:
            symbol = "⚠️"

        match = "✓" if expected in actual else "✗"
        print(f"{symbol} {action:<48} {expected:<10} {actual:<10} {match}")

    # ── Summary ───────────────────────────────────────────────────────

    print("\n" + "─" * 70)
    print("\n📊 GOVERNANCE SUMMARY:")
    print(f"   Agent: {governed.identity.bot_id}")
    print(f"   Trust Score: {governed.identity.trust_score}/100")
    print(f"   Total Actions: {governed.identity.action_count}")
    print(f"   Violations: {governed.identity.violation_count}")
    print()

    summary = governed.audit.summary()
    print(f"📋 AUDIT TRAIL:")
    print(f"   Total Records: {summary['total_actions']}")
    print(f"   Violations: {summary['violations']}")
    print(f"   Compliance Rate: {summary['compliance_rate']}")
    print(f"   Chain Integrity: {'✅ Verified' if summary['chain_integrity'] else '❌ Tampered'}")
    print()

    # Show violations
    violations = governed.audit.get_violations()
    if violations:
        print(f"🚨 VIOLATIONS ({len(violations)}):")
        for v in violations[:5]:
            print(f"   [{v['decision']}] {v['reason'][:60]}")
    print()

    print("─" * 70)
    print("  TBN Protocol — You cannot govern what you cannot identify.")
    print("  https://tbn.hardinai.co.uk")
    print("─" * 70 + "\n")


if __name__ == "__main__":
    main()
