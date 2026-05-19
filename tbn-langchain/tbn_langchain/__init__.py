"""
TBN LangChain — Governance layer for LangChain AI agents.

Usage:
    from tbn_langchain import TBNGovernor, GovernancePolicy

    # Wrap any LangChain agent with TBN governance
    governed = TBNGovernor(
        agent=your_agent,
        bot_id="sales-bot-001",
        policies=[GovernancePolicy.NO_PII, GovernancePolicy.HUMAN_APPROVAL_WRITES],
    )
    result = governed.invoke("Process customer refund")

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

from tbn_langchain.governor import TBNGovernor
from tbn_langchain.policies import GovernancePolicy, PolicyRule
from tbn_langchain.audit import AuditTrail
from tbn_langchain.identity import AgentIdentity

__version__ = "0.1.0"
__all__ = ["TBNGovernor", "GovernancePolicy", "PolicyRule", "AuditTrail", "AgentIdentity"]
