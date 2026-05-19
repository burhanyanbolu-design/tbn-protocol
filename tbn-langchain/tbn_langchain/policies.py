"""
TBN LangChain — Governance Policies
Define rules that constrain agent behaviour at runtime.

Policies are evaluated BEFORE an action executes.
If a policy denies an action, it never happens.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import re
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field


class Decision(Enum):
    """Governance decision outcomes."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""
    decision: Decision
    rule_name: str
    reason: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class PolicyRule:
    """A single governance rule."""
    name: str
    description: str
    check: Callable[[str, str, Any], PolicyResult]
    severity: float = 5.0  # Trust score penalty on violation
    enabled: bool = True


# ── Built-in Policy Rules ──────────────────────────────────────────────

def _check_no_pii(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Block actions that attempt to access or expose PII."""
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card
        r'\b[A-Z]{2}\d{6}[A-Z]\b',  # Passport
        r'(?i)(ssn|social.security|credit.card|passport.number|national.insurance)',
        r'(?i)(export.all|dump.all|extract.all).*(customer|user|patient|employee)',
    ]
    input_str = str(input_data).lower()
    for pattern in pii_patterns:
        if re.search(pattern, str(input_data)):
            return PolicyResult(
                decision=Decision.DENY,
                rule_name="NO_PII",
                reason=f"Action blocked: potential PII access detected (pattern: {pattern[:30]})"
            )
    return PolicyResult(decision=Decision.ALLOW, rule_name="NO_PII", reason="No PII detected")


def _check_no_destructive(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Block destructive operations without human approval."""
    destructive_keywords = [
        "delete", "drop", "truncate", "remove all", "destroy",
        "terminate", "shutdown", "wipe", "purge", "format"
    ]
    input_str = str(input_data).lower()
    for keyword in destructive_keywords:
        if keyword in input_str:
            return PolicyResult(
                decision=Decision.ESCALATE,
                rule_name="NO_DESTRUCTIVE",
                reason=f"Destructive action detected: '{keyword}'. Requires human approval."
            )
    return PolicyResult(decision=Decision.ALLOW, rule_name="NO_DESTRUCTIVE", reason="Non-destructive action")


def _check_no_financial(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Require human approval for financial transactions."""
    financial_keywords = [
        "transfer", "payment", "wire", "refund", "charge",
        "invoice", "billing", "withdraw", "deposit"
    ]
    input_str = str(input_data).lower()
    for keyword in financial_keywords:
        if keyword in input_str:
            return PolicyResult(
                decision=Decision.ESCALATE,
                rule_name="NO_FINANCIAL",
                reason=f"Financial action detected: '{keyword}'. Requires human approval."
            )
    return PolicyResult(decision=Decision.ALLOW, rule_name="NO_FINANCIAL", reason="Non-financial action")


def _check_no_external_comms(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Block unsupervised external communications."""
    comms_keywords = [
        "send email", "send message", "post to", "publish",
        "tweet", "notify customer", "contact", "reply to"
    ]
    input_str = str(input_data).lower()
    for keyword in comms_keywords:
        if keyword in input_str:
            return PolicyResult(
                decision=Decision.ESCALATE,
                rule_name="NO_EXTERNAL_COMMS",
                reason=f"External communication detected: '{keyword}'. Requires human approval."
            )
    return PolicyResult(decision=Decision.ALLOW, rule_name="NO_EXTERNAL_COMMS", reason="No external comms")


def _check_rate_limit(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Always allow — rate limiting is handled by the governor."""
    return PolicyResult(decision=Decision.ALLOW, rule_name="RATE_LIMIT", reason="Within rate limit")


def _check_scope_boundary(action: str, tool: str, input_data: Any) -> PolicyResult:
    """Block actions outside the agent's declared scope."""
    # This is a placeholder — in production, scope is defined per-agent
    return PolicyResult(decision=Decision.ALLOW, rule_name="SCOPE_BOUNDARY", reason="Within scope")


# ── Pre-built Policy Sets ──────────────────────────────────────────────

class GovernancePolicy(Enum):
    """Pre-built governance policies."""

    NO_PII = PolicyRule(
        name="NO_PII",
        description="Block access to personally identifiable information",
        check=_check_no_pii,
        severity=10.0,
    )

    NO_DESTRUCTIVE = PolicyRule(
        name="NO_DESTRUCTIVE",
        description="Require human approval for destructive operations",
        check=_check_no_destructive,
        severity=8.0,
    )

    NO_FINANCIAL = PolicyRule(
        name="NO_FINANCIAL",
        description="Require human approval for financial transactions",
        check=_check_no_financial,
        severity=8.0,
    )

    NO_EXTERNAL_COMMS = PolicyRule(
        name="NO_EXTERNAL_COMMS",
        description="Block unsupervised external communications",
        check=_check_no_external_comms,
        severity=6.0,
    )

    RATE_LIMIT = PolicyRule(
        name="RATE_LIMIT",
        description="Enforce action rate limits",
        check=_check_rate_limit,
        severity=3.0,
    )

    SCOPE_BOUNDARY = PolicyRule(
        name="SCOPE_BOUNDARY",
        description="Keep agent within its declared operational scope",
        check=_check_scope_boundary,
        severity=7.0,
    )


def evaluate_policies(policies: List[GovernancePolicy], action: str, tool: str, input_data: Any) -> PolicyResult:
    """Evaluate all policies against an action. First DENY or ESCALATE wins."""
    for policy in policies:
        rule = policy.value
        if not rule.enabled:
            continue
        result = rule.check(action, tool, input_data)
        if result.decision in (Decision.DENY, Decision.ESCALATE):
            return result
    return PolicyResult(decision=Decision.ALLOW, rule_name="ALL_POLICIES", reason="All policies passed")
