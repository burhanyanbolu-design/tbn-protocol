# TBN LangChain — Governance for AI Agents

**Add identity, enforcement, and audit to any LangChain agent in 3 lines of code.**

TBN LangChain wraps your LangChain agents with the TBN Protocol governance layer. Every action is identified, evaluated against policies, enforced at runtime, and recorded in an immutable audit trail.

## Installation

```bash
pip install tbn-langchain
```

## Quick Start

```python
from langchain.agents import create_openai_agent
from tbn_langchain import TBNGovernor, GovernancePolicy

# Build your agent normally
agent = create_openai_agent(llm, tools, prompt)

# Wrap with TBN governance (3 lines)
governed = TBNGovernor(
    agent=agent,
    bot_id="sales-bot-001",
    owner="Acme Corp",
    policies=[
        GovernancePolicy.NO_PII,
        GovernancePolicy.NO_DESTRUCTIVE,
        GovernancePolicy.NO_FINANCIAL,
    ],
)

# Every action is now governed
result = governed.invoke("Process customer refund for order #1234")
# → ESCALATE: Financial action detected. Requires human approval.
```

## What It Does

Every agent action flows through:

```
① IDENTIFY  →  ② EVALUATE  →  ③ ENFORCE  →  ④ EXECUTE  →  ⑤ RECORD
```

1. **IDENTIFY** — Agent signs the action with its cryptographic identity
2. **EVALUATE** — Action is checked against all governance policies
3. **ENFORCE** — Decision is made: ALLOW / DENY / ESCALATE
4. **EXECUTE** — If allowed, the action proceeds
5. **RECORD** — Everything is logged in the immutable audit trail

## Built-in Policies

| Policy | What it does |
|--------|-------------|
| `NO_PII` | Blocks access to personally identifiable information |
| `NO_DESTRUCTIVE` | Requires human approval for delete/drop/destroy operations |
| `NO_FINANCIAL` | Requires human approval for payments, transfers, refunds |
| `NO_EXTERNAL_COMMS` | Blocks unsupervised emails, messages, posts |
| `RATE_LIMIT` | Enforces action rate limits (default: 100/min) |
| `SCOPE_BOUNDARY` | Keeps agent within its declared operational scope |

## Custom Rules

```python
from tbn_langchain import PolicyRule, TBNGovernor
from tbn_langchain.policies import Decision, PolicyResult

def no_production_access(action, tool, input_data):
    if "production" in str(input_data).lower():
        return PolicyResult(
            decision=Decision.DENY,
            rule_name="NO_PRODUCTION",
            reason="Production access is not permitted for this agent"
        )
    return PolicyResult(decision=Decision.ALLOW, rule_name="NO_PRODUCTION", reason="OK")

governed = TBNGovernor(
    agent=agent,
    bot_id="dev-bot-001",
    custom_rules=[
        PolicyRule(name="NO_PRODUCTION", description="Block production access", check=no_production_access)
    ],
)
```

## Human Escalation

```python
def approval_handler(result, input_data):
    """Called when an action requires human approval."""
    print(f"⚠️  ESCALATION: {result.reason}")
    print(f"   Action: {input_data}")
    response = input("   Approve? (y/n): ")
    return response.lower() == "y"

governed = TBNGovernor(
    agent=agent,
    bot_id="finance-bot-001",
    policies=[GovernancePolicy.NO_FINANCIAL],
    on_escalate=approval_handler,
)
```

## Audit Trail

```python
# Get audit summary
print(governed.audit.summary())
# {'bot_id': 'sales-bot-001', 'total_actions': 47, 'violations': 3,
#  'compliance_rate': '93.6%', 'chain_integrity': True}

# Get all violations
violations = governed.audit.get_violations()

# Verify chain integrity (tamper detection)
assert governed.audit.verify_integrity() == True
```

## Connect to TBN Server

```python
governed = TBNGovernor(
    agent=agent,
    bot_id="sales-bot-001",
    tbn_server="https://tbn.hardinai.co.uk",  # Register with TBN
)
```

## Governance Status

```python
print(governed.status())
# {
#   'identity': {'bot_id': 'sales-bot-001', 'trust_score': 95.0, ...},
#   'audit_summary': {'total_actions': 47, 'violations': 3, ...},
#   'policies': ['NO_PII', 'NO_DESTRUCTIVE', 'NO_FINANCIAL'],
#   'strict_mode': True,
# }
```

## Why TBN?

| Without TBN | With TBN |
|-------------|----------|
| Agent has no identity | Cryptographic identity (verifiable) |
| No rules enforced at runtime | Policy-as-code, enforced before execution |
| No audit trail | Immutable, tamper-proof action log |
| Violations discovered after damage | Violations blocked before they happen |
| "Trust me" | "Verify me" |

## Architecture

```
┌─────────────────────────────────────────┐
│         Your LangChain Agent            │
│   (tools, chains, memory, prompts)      │
└────────────────┬────────────────────────┘
                 │
    ┌────────────▼────────────────┐
    │      TBN Governor           │
    │  ┌──────────────────────┐   │
    │  │ Layer 1: Identity    │   │
    │  │ (Ed25519, fingerprint)│  │
    │  ├──────────────────────┤   │
    │  │ Layer 2: Policies    │   │
    │  │ (ALLOW/DENY/ESCALATE)│   │
    │  ├──────────────────────┤   │
    │  │ Layer 3: Audit Trail │   │
    │  │ (immutable, chained) │   │
    │  └──────────────────────┘   │
    └────────────┬────────────────┘
                 │
    ┌────────────▼────────────────┐
    │    Execution / Real World   │
    │  (APIs, databases, actions) │
    └─────────────────────────────┘
```

## License

AGPL-3.0 — Open source with commercial licensing available.

**Built by [Hardin AI Solutions](https://tbn.hardinai.co.uk)**
