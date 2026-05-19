"""
TBN LangChain — Governor
The main wrapper that adds TBN governance to any LangChain agent.

Usage:
    from tbn_langchain import TBNGovernor, GovernancePolicy

    governed = TBNGovernor(
        agent=your_langchain_agent,
        bot_id="sales-bot-001",
        owner="Acme Corp",
        policies=[
            GovernancePolicy.NO_PII,
            GovernancePolicy.NO_DESTRUCTIVE,
            GovernancePolicy.NO_FINANCIAL,
        ],
    )

    # Every action is now: IDENTIFY → EVALUATE → ENFORCE → RECORD
    result = governed.invoke("Process the customer refund for order #1234")

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import time
import logging
from typing import List, Optional, Dict, Any, Callable

from tbn_langchain.identity import AgentIdentity
from tbn_langchain.policies import GovernancePolicy, PolicyRule, evaluate_policies, Decision, PolicyResult
from tbn_langchain.audit import AuditTrail

logger = logging.getLogger("tbn_langchain")


class GovernanceViolation(Exception):
    """Raised when an action is denied by governance policies."""

    def __init__(self, result: PolicyResult):
        self.result = result
        super().__init__(f"[TBN DENY] {result.rule_name}: {result.reason}")


class EscalationRequired(Exception):
    """Raised when an action requires human approval."""

    def __init__(self, result: PolicyResult):
        self.result = result
        super().__init__(f"[TBN ESCALATE] {result.rule_name}: {result.reason}")


class TBNGovernor:
    """
    Wraps a LangChain agent with TBN Protocol governance.

    Intercepts every tool call and agent action, evaluates against
    governance policies, and either allows, denies, or escalates.
    All actions are recorded in an immutable audit trail.
    """

    def __init__(
        self,
        agent: Any,
        bot_id: str,
        owner: str = "",
        description: str = "",
        policies: Optional[List[GovernancePolicy]] = None,
        custom_rules: Optional[List[PolicyRule]] = None,
        on_escalate: Optional[Callable] = None,
        on_violation: Optional[Callable] = None,
        audit_path: str = "data/tbn_audit",
        strict_mode: bool = True,
        rate_limit: int = 100,  # Max actions per minute
        tbn_server: Optional[str] = None,  # TBN server URL for remote registration
    ):
        self.agent = agent
        self.strict_mode = strict_mode
        self.rate_limit = rate_limit
        self.tbn_server = tbn_server
        self._action_timestamps: List[float] = []

        # Layer 1: Identity
        self.identity = AgentIdentity(
            bot_id=bot_id,
            owner=owner,
            description=description,
            metadata={"framework": "langchain", "governed": True},
        )

        # Layer 2: Policies
        self.policies = policies or [
            GovernancePolicy.NO_PII,
            GovernancePolicy.NO_DESTRUCTIVE,
        ]
        self.custom_rules = custom_rules or []

        # Layer 3: Audit
        self.audit = AuditTrail(bot_id=bot_id, storage_path=audit_path)

        # Callbacks
        self.on_escalate = on_escalate
        self.on_violation = on_violation

        # Register with TBN server if configured
        if self.tbn_server:
            self._register_with_tbn()

        logger.info(f"[TBN] Governor initialized for '{bot_id}' with {len(self.policies)} policies")

    def _register_with_tbn(self):
        """Register this agent with the TBN server."""
        try:
            import requests
            resp = requests.post(
                f"{self.tbn_server}/api/bots",
                json={
                    "name": self.identity.bot_id,
                    "owner": self.identity.owner,
                    "description": self.identity.description,
                    "framework": "langchain",
                    "governed": True,
                    "fingerprint": self.identity.fingerprint,
                },
                timeout=5,
            )
            if resp.status_code == 200:
                logger.info(f"[TBN] Registered with server: {self.tbn_server}")
            else:
                logger.warning(f"[TBN] Registration failed: {resp.status_code}")
        except Exception as e:
            logger.warning(f"[TBN] Could not reach server: {e}")

    def _check_rate_limit(self) -> bool:
        """Check if agent is within rate limits."""
        now = time.time()
        # Remove timestamps older than 60 seconds
        self._action_timestamps = [t for t in self._action_timestamps if now - t < 60]
        if len(self._action_timestamps) >= self.rate_limit:
            return False
        self._action_timestamps.append(now)
        return True

    def evaluate(self, action: str, tool: str = "", input_data: Any = "") -> PolicyResult:
        """
        Evaluate an action against all governance policies.
        Returns the governance decision without executing.
        """
        # Rate limit check
        if not self._check_rate_limit():
            return PolicyResult(
                decision=Decision.DENY,
                rule_name="RATE_LIMIT",
                reason=f"Rate limit exceeded: {self.rate_limit} actions/minute"
            )

        # Evaluate built-in policies
        result = evaluate_policies(self.policies, action, tool, input_data)

        # Evaluate custom rules if built-in policies passed
        if result.decision == Decision.ALLOW and self.custom_rules:
            for rule in self.custom_rules:
                if not rule.enabled:
                    continue
                custom_result = rule.check(action, tool, input_data)
                if custom_result.decision in (Decision.DENY, Decision.ESCALATE):
                    return custom_result

        return result

    def invoke(self, input_data: Any, **kwargs) -> Any:
        """
        Invoke the wrapped agent with governance enforcement.

        Flow: IDENTIFY → EVALUATE → ENFORCE → EXECUTE → RECORD
        """
        start_time = time.time()
        action = str(input_data)[:200]
        tool = kwargs.get("tool", "agent_invoke")

        # Step 1: IDENTIFY
        signed = self.identity.sign_action(action, tool, input_data)
        logger.debug(f"[TBN] Action #{signed['action_number']} by {self.identity.bot_id}")

        # Step 2: EVALUATE
        result = self.evaluate(action, tool, input_data)

        # Step 3: ENFORCE
        if result.decision == Decision.DENY:
            self.identity.record_violation(result.rule_name, severity=10.0)
            duration_ms = (time.time() - start_time) * 1000

            # Record in audit trail
            self.audit.record(
                action=action, tool=tool, decision="DENY",
                reason=result.reason, input_data=input_data,
                duration_ms=duration_ms,
            )

            # Callback
            if self.on_violation:
                self.on_violation(result)

            if self.strict_mode:
                raise GovernanceViolation(result)
            else:
                logger.warning(f"[TBN] DENIED (non-strict): {result.reason}")
                return {"tbn_decision": "DENY", "reason": result.reason}

        elif result.decision == Decision.ESCALATE:
            duration_ms = (time.time() - start_time) * 1000

            # Record in audit trail
            self.audit.record(
                action=action, tool=tool, decision="ESCALATE",
                reason=result.reason, input_data=input_data,
                duration_ms=duration_ms,
            )

            # Callback
            if self.on_escalate:
                approved = self.on_escalate(result, input_data)
                if not approved:
                    self.identity.record_violation(result.rule_name, severity=5.0)
                    if self.strict_mode:
                        raise EscalationRequired(result)
                    return {"tbn_decision": "ESCALATE_DENIED", "reason": result.reason}
            else:
                if self.strict_mode:
                    raise EscalationRequired(result)
                return {"tbn_decision": "ESCALATE", "reason": result.reason}

        # Step 4: EXECUTE (action is allowed)
        try:
            # Call the underlying LangChain agent
            if hasattr(self.agent, 'invoke'):
                output = self.agent.invoke(input_data, **kwargs)
            elif hasattr(self.agent, 'run'):
                output = self.agent.run(input_data, **kwargs)
            elif callable(self.agent):
                output = self.agent(input_data, **kwargs)
            else:
                raise ValueError("Agent must have 'invoke', 'run', or be callable")

            duration_ms = (time.time() - start_time) * 1000

            # Step 5: RECORD
            self.audit.record(
                action=action, tool=tool, decision="ALLOW",
                reason="All policies passed", input_data=input_data,
                output_data=output, duration_ms=duration_ms,
            )

            return output

        except (GovernanceViolation, EscalationRequired):
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.audit.record(
                action=action, tool=tool, decision="ERROR",
                reason=str(e), input_data=input_data,
                duration_ms=duration_ms,
            )
            raise

    def run(self, input_data: Any, **kwargs) -> Any:
        """Alias for invoke() — matches LangChain agent.run() interface."""
        return self.invoke(input_data, **kwargs)

    def __call__(self, input_data: Any, **kwargs) -> Any:
        """Make the governor callable like the original agent."""
        return self.invoke(input_data, **kwargs)

    def status(self) -> Dict:
        """Get current governance status."""
        return {
            "identity": self.identity.to_dict(),
            "audit_summary": self.audit.summary(),
            "policies": [p.value.name for p in self.policies],
            "custom_rules": [r.name for r in self.custom_rules],
            "strict_mode": self.strict_mode,
            "rate_limit": self.rate_limit,
        }

    def __repr__(self):
        return (
            f"<TBNGovernor agent='{self.identity.bot_id}' "
            f"trust={self.identity.trust_score} "
            f"policies={len(self.policies)} "
            f"actions={self.identity.action_count}>"
        )
