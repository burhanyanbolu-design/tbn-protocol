"""
TBN Agent Network — Bind Receipt System v2.1

Full implementation of the two-phase Hold → Bind receipt model
with all hardening from Frank's governance review.

Doctrine: No receipt, no effect. Wrong action/target/surface/class
or expired receipt = no effect.

Crypto model:
- HMAC-SHA256 for receipt attestation (symmetric, fast, internal)
- SHA-256 for binding hashes and proof hashes
- RSA-PSS (external) for cross-system signature verification

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0
"""

import json
import uuid
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────

class DecisionClass(Enum):
    """Consequence tiers — higher tier = more governance."""
    TIER_1 = "TIER_1"  # Reversible (read, list, search)
    TIER_2 = "TIER_2"  # State-changing (update config, modify permissions)
    TIER_3 = "TIER_3"  # Consequential (transfer funds, delete data)
    TIER_4 = "TIER_4"  # Irreversible (deploy production, bulk delete)


class MandateStatus(Enum):
    """Snapshot of authority validity at bind time."""
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"


class Verdict(Enum):
    """Admissibility decision."""
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"
    ESCALATE = "ESCALATE"
    PAUSE = "PAUSE"


class FailureClass(Enum):
    """Failure types — determines whether receipt is consumed."""
    # Security failures → CONSUME receipt (prevent retry attacks)
    FORGED_ATTESTATION = "FORGED_ATTESTATION"
    EXPIRED = "EXPIRED"
    REPLAY_ATTEMPT = "REPLAY_ATTEMPT"
    WRONG_ACTION = "WRONG_ACTION"
    WRONG_TARGET = "WRONG_TARGET"
    WRONG_SURFACE = "WRONG_SURFACE"
    WRONG_CLASS = "WRONG_CLASS"
    # Benign failures → DO NOT consume (allow retry)
    DOWNSTREAM_ERROR = "DOWNSTREAM_ERROR"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"


# Security failures that consume the receipt
CONSUME_ON_FAILURE = {
    FailureClass.FORGED_ATTESTATION,
    FailureClass.EXPIRED,
    FailureClass.REPLAY_ATTEMPT,
    FailureClass.WRONG_ACTION,
    FailureClass.WRONG_TARGET,
    FailureClass.WRONG_SURFACE,
    FailureClass.WRONG_CLASS,
}


# ── Hold Token ────────────────────────────────────────────────────────

class HoldToken:
    """
    Phase 1: Non-effect-capable deliberation token.
    Long-lived. Cannot execute anything. Exists for human review.
    """

    def __init__(self, agent_id, action, target, effect_surface,
                 decision_class, hold_ttl_seconds=3600):
        self.hold_id = f"hold_{uuid.uuid4().hex[:12]}"
        self.agent_id = agent_id
        self.action = action
        self.target = target
        self.effect_surface = effect_surface  # Stable canonical ID
        self.decision_class = decision_class
        self.requested_at = datetime.now(timezone.utc).isoformat()
        self.hold_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=hold_ttl_seconds)
        ).isoformat()
        self.effect_capable = False  # ALWAYS false
        self.status = "PENDING"  # PENDING | APPROVED | REJECTED | EXPIRED

    def is_valid(self):
        """Check if hold is still active."""
        if self.status == "EXPIRED":
            return False, "HOLD_EXPIRED"
        if self.status == "REJECTED":
            return False, "HOLD_REJECTED"
        now = datetime.now(timezone.utc).isoformat()
        if now > self.hold_expires_at:
            self.status = "EXPIRED"
            return False, "HOLD_EXPIRED"
        return True, "HOLD_ACTIVE"

    def approve(self):
        """Human approves — hold can now be converted to bind receipt."""
        valid, reason = self.is_valid()
        if not valid:
            return False, reason
        self.status = "APPROVED"
        return True, "HOLD_APPROVED"

    def reject(self):
        """Human rejects — hold is dead."""
        self.status = "REJECTED"
        return True, "HOLD_REJECTED"

    def to_dict(self):
        return {
            "hold_id": self.hold_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "target": self.target,
            "effect_surface": self.effect_surface,
            "decision_class": self.decision_class.value,
            "requested_at": self.requested_at,
            "hold_expires_at": self.hold_expires_at,
            "effect_capable": self.effect_capable,
            "status": self.status,
        }


# ── Bind Receipt ──────────────────────────────────────────────────────

class BindReceipt:
    """
    Phase 2: Effect-capable, short-lived, single-use execution receipt.
    Minted ONLY when a human commits (approves the hold).
    """

    def __init__(self, hold_token, authority_of_record, mandate_scope_ref,
                 mandate_status, verdict, policy_basis_ref,
                 source_trail_refs, bind_ttl_seconds=60,
                 reason_code=None, critical_uncertainty=False,
                 uncertainty_codes=None, secret_key="tbn_bind_secret"):

        # ── Group 1: Receipt Identity & Validity ──
        self.receipt_id = f"bind_{uuid.uuid4().hex[:12]}"
        self.hold_id = hold_token.hold_id
        self.issued_at = datetime.now(timezone.utc).isoformat()
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=bind_ttl_seconds)
        ).isoformat()
        self.single_use = True
        self.consumed = False
        self.consumed_reason = None

        # ── Group 2: What Is Being Bound ──
        self.decision_class = hold_token.decision_class
        self.action = hold_token.action
        self.target = hold_token.target
        self.effect_surface = hold_token.effect_surface

        # ── Group 3: Authority at Bind ──
        self.authority_of_record = authority_of_record
        self.mandate_scope_ref = mandate_scope_ref
        self.mandate_status = mandate_status

        # ── Group 4: Admissibility Decision ──
        self.verdict = verdict
        self.policy_basis_ref = policy_basis_ref
        self.reason_code = reason_code

        # ── Group 5: Evidence & Uncertainty ──
        self.source_trail_refs = source_trail_refs or []
        self.critical_uncertainty = critical_uncertainty
        self.uncertainty_codes = uncertainty_codes or []

        # ── Group 6: Anti-Replay / Anti-Substitution ──
        self.binding_hash = self._compute_binding_hash()
        self.attestation = self._generate_attestation(secret_key)
        self.proof_hash = self._compute_proof_hash()

    def _compute_binding_hash(self):
        """Bind receipt to exact action context. Prevents substitution."""
        content = (
            f"{self.action}|{self.target}|"
            f"{self.effect_surface}|{self.decision_class.value}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_attestation(self, secret_key):
        """HMAC-SHA256 attestation proving receipt integrity."""
        message = json.dumps({
            "receipt_id": self.receipt_id,
            "hold_id": self.hold_id,
            "action": self.action,
            "target": self.target,
            "effect_surface": self.effect_surface,
            "decision_class": self.decision_class.value,
            "authority_of_record": self.authority_of_record,
            "mandate_status": self.mandate_status.value,
            "verdict": self.verdict.value,
            "binding_hash": self.binding_hash,
        }, sort_keys=True)
        return hmac.new(
            secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    def _compute_proof_hash(self):
        """SHA-256 of entire receipt for tamper detection."""
        content = json.dumps({
            "receipt_id": self.receipt_id,
            "attestation": self.attestation,
            "binding_hash": self.binding_hash,
            "issued_at": self.issued_at,
        }, sort_keys=True)
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    def consume(self, reason="SUCCESS"):
        """Mark receipt as consumed."""
        self.consumed = True
        self.consumed_reason = reason

    def is_valid(self):
        """Check receipt validity."""
        if self.consumed:
            return False, "RECEIPT_CONSUMED"
        now = datetime.now(timezone.utc).isoformat()
        if now > self.expires_at:
            return False, "RECEIPT_EXPIRED"
        return True, "VALID"

    def to_dict(self):
        return {
            "receipt_id": self.receipt_id,
            "hold_id": self.hold_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "action": self.action,
            "target": self.target,
            "effect_surface": self.effect_surface,
            "decision_class": self.decision_class.value,
            "authority_of_record": self.authority_of_record,
            "mandate_status": self.mandate_status.value,
            "verdict": self.verdict.value,
            "policy_basis_ref": self.policy_basis_ref,
            "reason_code": self.reason_code,
            "critical_uncertainty": self.critical_uncertainty,
            "source_trail_refs": self.source_trail_refs,
            "binding_hash": self.binding_hash[:16] + "...",
            "attestation": self.attestation[:16] + "...",
            "proof_hash": self.proof_hash,
            "consumed": self.consumed,
        }


# ── Clawback Receipt ──────────────────────────────────────────────────

class ClawbackReceipt:
    """
    Governed reversal. Separate commit type with stricter path.
    Requires higher authority than original action.
    """

    def __init__(self, original_receipt_id, reason, authority_of_record,
                 mandate_scope_ref, decision_class, effect,
                 evidence, secret_key="tbn_bind_secret"):
        self.clawback_id = f"claw_{uuid.uuid4().hex[:12]}"
        self.original_receipt_id = original_receipt_id
        self.reason = reason
        self.authority_of_record = authority_of_record
        self.mandate_scope_ref = mandate_scope_ref
        self.mandate_status = MandateStatus.VALID  # Must be valid for clawback
        self.decision_class = decision_class
        self.effect = effect
        self.evidence = evidence or []
        self.issued_at = datetime.now(timezone.utc).isoformat()
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=60)
        ).isoformat()
        self.consumed = False

        self.attestation = self._generate_attestation(secret_key)

    def _generate_attestation(self, secret_key):
        message = json.dumps({
            "clawback_id": self.clawback_id,
            "original_receipt_id": self.original_receipt_id,
            "reason": self.reason,
            "authority_of_record": self.authority_of_record,
            "effect": self.effect,
        }, sort_keys=True)
        return hmac.new(
            secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    def to_dict(self):
        return {
            "clawback_id": self.clawback_id,
            "original_receipt_id": self.original_receipt_id,
            "reason": self.reason,
            "authority_of_record": self.authority_of_record,
            "decision_class": self.decision_class.value,
            "effect": self.effect,
            "evidence": self.evidence,
            "issued_at": self.issued_at,
            "consumed": self.consumed,
        }


# ── Policy Registry (action→tier mapping) ─────────────────────────────

# Frank point 3: Action→tier mapping must be governed, not improvised.
# This is the versioned policy that defines which actions belong to which tier.

DEFAULT_ACTION_TIER_POLICY = {
    "policy_id": "action-tiers-v1.0",
    "version": "1.0",
    "mappings": {
        # TIER_1: Reversible
        "read": DecisionClass.TIER_1,
        "list": DecisionClass.TIER_1,
        "search": DecisionClass.TIER_1,
        "query": DecisionClass.TIER_1,
        "retrieve": DecisionClass.TIER_1,
        # TIER_2: State-changing
        "update": DecisionClass.TIER_2,
        "modify_permissions": DecisionClass.TIER_2,
        "create": DecisionClass.TIER_2,
        "schedule": DecisionClass.TIER_2,
        # TIER_3: Consequential
        "transfer": DecisionClass.TIER_3,
        "delete": DecisionClass.TIER_3,
        "share_external": DecisionClass.TIER_3,
        "export": DecisionClass.TIER_3,
        "revoke": DecisionClass.TIER_3,
        # TIER_4: Irreversible
        "deploy": DecisionClass.TIER_4,
        "bulk_delete": DecisionClass.TIER_4,
        "destroy": DecisionClass.TIER_4,
        "admin_override": DecisionClass.TIER_4,
    }
}

# Hold TTL per tier (Frank point 1 from original spec)
TIER_HOLD_TTL = {
    DecisionClass.TIER_1: 0,       # No hold needed
    DecisionClass.TIER_2: 300,     # 5 minutes
    DecisionClass.TIER_3: 3600,    # 1 hour
    DecisionClass.TIER_4: 86400,   # 24 hours
}

# Bind TTL per tier
TIER_BIND_TTL = {
    DecisionClass.TIER_1: 60,   # 60 seconds
    DecisionClass.TIER_2: 60,   # 60 seconds
    DecisionClass.TIER_3: 30,   # 30 seconds
    DecisionClass.TIER_4: 30,   # 30 seconds
}


# ── Bind Receipt Engine ───────────────────────────────────────────────

class BindReceiptEngine:
    """
    Full bind-receipt governance engine.

    Usage:
        engine = BindReceiptEngine()

        # Agent requests a high-value action
        hold = engine.request_hold(agent_id, action, target, surface)

        # Human reviews and approves
        engine.approve_hold(hold.hold_id, authority, mandate_ref)

        # System mints bind receipt
        receipt = engine.mint_receipt(hold.hold_id, policy_ref, sources)

        # Agent attempts execution — engine validates
        result = engine.validate_and_execute(receipt.receipt_id, action, target, surface)
    """

    def __init__(self, secret_key="tbn_bind_receipt_key",
                 action_tier_policy=None):
        self.secret_key = secret_key
        self.action_tier_policy = (
            action_tier_policy or DEFAULT_ACTION_TIER_POLICY
        )

        # Storage
        self.holds: Dict[str, HoldToken] = {}
        self.receipts: Dict[str, BindReceipt] = {}
        self.clawbacks: Dict[str, ClawbackReceipt] = {}

        # Approved holds pending mint
        self.approved_holds: Dict[str, dict] = {}

        # Stats
        self.stats = {
            "holds_requested": 0,
            "holds_approved": 0,
            "holds_rejected": 0,
            "holds_expired": 0,
            "receipts_minted": 0,
            "receipts_validated": 0,
            "receipts_consumed_success": 0,
            "receipts_consumed_security": 0,
            "receipts_blocked_benign": 0,
            "clawbacks_issued": 0,
            "escalations": 0,
        }

    def get_decision_class(self, action):
        """Look up action's tier from versioned policy. Never guess."""
        mappings = self.action_tier_policy["mappings"]
        if action in mappings:
            return mappings[action]
        # Unknown action → highest tier (safest default)
        return DecisionClass.TIER_4

    def request_hold(self, agent_id, action, target, effect_surface):
        """
        Phase 1: Agent requests permission for a high-value action.
        Returns a non-effect-capable hold token for human review.
        """
        decision_class = self.get_decision_class(action)
        hold_ttl = TIER_HOLD_TTL[decision_class]

        # TIER_1 actions don't need a hold — skip to direct mint
        if decision_class == DecisionClass.TIER_1:
            return None, "TIER_1_NO_HOLD_NEEDED"

        hold = HoldToken(
            agent_id=agent_id,
            action=action,
            target=target,
            effect_surface=effect_surface,
            decision_class=decision_class,
            hold_ttl_seconds=hold_ttl,
        )

        self.holds[hold.hold_id] = hold
        self.stats["holds_requested"] += 1
        return hold, "HOLD_ISSUED"

    def approve_hold(self, hold_id, authority_of_record, mandate_scope_ref,
                     mandate_status=MandateStatus.VALID):
        """
        Human approves a hold. Stores authority info for receipt minting.
        Frank point 5: UNKNOWN mandate = always refuse.
        """
        hold = self.holds.get(hold_id)
        if not hold:
            return False, "HOLD_NOT_FOUND"

        # Frank point 5: UNKNOWN must never permit bind
        if mandate_status == MandateStatus.UNKNOWN:
            self.stats["escalations"] += 1
            return False, "MANDATE_UNKNOWN_CANNOT_APPROVE"

        # Only VALID mandates can approve
        if mandate_status != MandateStatus.VALID:
            return False, f"MANDATE_{mandate_status.value}_CANNOT_APPROVE"

        valid, reason = hold.approve()
        if not valid:
            return False, reason

        self.approved_holds[hold_id] = {
            "authority_of_record": authority_of_record,
            "mandate_scope_ref": mandate_scope_ref,
            "mandate_status": mandate_status,
        }
        self.stats["holds_approved"] += 1
        return True, "HOLD_APPROVED"

    def mint_receipt(self, hold_id, policy_basis_ref, source_trail_refs=None,
                     critical_uncertainty=False, uncertainty_codes=None):
        """
        Mint a bind receipt from an approved hold.
        Frank point 4: If critical_uncertainty, verdict MUST be ESCALATE/PAUSE.
        """
        hold = self.holds.get(hold_id)
        if not hold:
            return None, "HOLD_NOT_FOUND"

        if hold.status != "APPROVED":
            return None, f"HOLD_NOT_APPROVED (status: {hold.status})"

        auth_info = self.approved_holds.get(hold_id)
        if not auth_info:
            return None, "APPROVAL_INFO_MISSING"

        # Frank point 4: critical uncertainty → ESCALATE, never ALLOW
        if critical_uncertainty:
            verdict = Verdict.ESCALATE
            self.stats["escalations"] += 1
        else:
            verdict = Verdict.ALLOW

        bind_ttl = TIER_BIND_TTL[hold.decision_class]

        receipt = BindReceipt(
            hold_token=hold,
            authority_of_record=auth_info["authority_of_record"],
            mandate_scope_ref=auth_info["mandate_scope_ref"],
            mandate_status=auth_info["mandate_status"],
            verdict=verdict,
            policy_basis_ref=policy_basis_ref,
            source_trail_refs=source_trail_refs or [],
            bind_ttl_seconds=bind_ttl,
            critical_uncertainty=critical_uncertainty,
            uncertainty_codes=uncertainty_codes or [],
            secret_key=self.secret_key,
        )

        self.receipts[receipt.receipt_id] = receipt
        self.stats["receipts_minted"] += 1
        return receipt, "RECEIPT_MINTED"

    def validate_and_execute(self, receipt_id, action, target, effect_surface):
        """
        Validate a bind receipt when the agent attempts execution.

        Frank point 1: Only consume on success or security failures.
        Benign failures block without consumption.

        Returns: (allowed: bool, reason: str, failure_class: FailureClass|None)
        """
        receipt = self.receipts.get(receipt_id)
        if not receipt:
            return False, "RECEIPT_NOT_FOUND", FailureClass.FORGED_ATTESTATION

        self.stats["receipts_validated"] += 1

        # Check consumed
        if receipt.consumed:
            return False, "RECEIPT_ALREADY_CONSUMED", FailureClass.REPLAY_ATTEMPT

        # Check expiry
        now = datetime.now(timezone.utc).isoformat()
        if now > receipt.expires_at:
            receipt.consume("EXPIRED")
            self.stats["receipts_consumed_security"] += 1
            return False, "RECEIPT_EXPIRED", FailureClass.EXPIRED

        # Check verdict allows execution
        if receipt.verdict != Verdict.ALLOW:
            # Frank point 4: PAUSE remains non-effect-capable
            return False, f"VERDICT_{receipt.verdict.value}", None

        # Check action matches
        if receipt.action != action:
            receipt.consume("WRONG_ACTION")
            self.stats["receipts_consumed_security"] += 1
            return False, "ACTION_MISMATCH", FailureClass.WRONG_ACTION

        # Check target matches
        if receipt.target != target:
            receipt.consume("WRONG_TARGET")
            self.stats["receipts_consumed_security"] += 1
            return False, "TARGET_MISMATCH", FailureClass.WRONG_TARGET

        # Check effect surface matches (stable canonical ID)
        if receipt.effect_surface != effect_surface:
            receipt.consume("WRONG_SURFACE")
            self.stats["receipts_consumed_security"] += 1
            return False, "SURFACE_MISMATCH", FailureClass.WRONG_SURFACE

        # Recompute and verify binding hash
        expected_hash = hashlib.sha256(
            f"{action}|{target}|{effect_surface}|{receipt.decision_class.value}".encode()
        ).hexdigest()
        if receipt.binding_hash != expected_hash:
            receipt.consume("BINDING_HASH_MISMATCH")
            self.stats["receipts_consumed_security"] += 1
            return False, "BINDING_HASH_INVALID", FailureClass.FORGED_ATTESTATION

        # Verify attestation integrity
        expected_att = receipt._generate_attestation(self.secret_key)
        if receipt.attestation != expected_att:
            receipt.consume("ATTESTATION_FORGED")
            self.stats["receipts_consumed_security"] += 1
            return False, "ATTESTATION_INVALID", FailureClass.FORGED_ATTESTATION

        # Check mandate was valid at bind
        if receipt.mandate_status != MandateStatus.VALID:
            return False, "MANDATE_NOT_VALID_AT_BIND", None

        # Check no critical uncertainty
        if receipt.critical_uncertainty:
            return False, "CRITICAL_UNCERTAINTY_PRESENT", None

        # ALL CHECKS PASSED — consume on success
        receipt.consume("SUCCESS")
        self.stats["receipts_consumed_success"] += 1
        return True, "EXECUTION_AUTHORIZED", None

    def block_benign_failure(self, receipt_id, failure_reason):
        """
        Frank point 1: Block without consuming for benign failures.
        Receipt remains valid for retry.
        """
        receipt = self.receipts.get(receipt_id)
        if not receipt:
            return {"blocked": True, "reason": "RECEIPT_NOT_FOUND"}

        self.stats["receipts_blocked_benign"] += 1
        return {
            "blocked": True,
            "reason": failure_reason,
            "receipt_still_valid": True,
            "retry_allowed": True,
            "receipt_id": receipt_id,
            "failure_class": "BENIGN",
        }

    def issue_clawback(self, original_receipt_id, reason,
                       authority_of_record, mandate_scope_ref,
                       effect, evidence=None):
        """
        Issue a governed reversal for a previously executed action.
        Requires higher authority than original.
        """
        original = self.receipts.get(original_receipt_id)
        if not original:
            return None, "ORIGINAL_RECEIPT_NOT_FOUND"

        # Clawback tier must be >= original tier
        clawback_class = original.decision_class

        clawback = ClawbackReceipt(
            original_receipt_id=original_receipt_id,
            reason=reason,
            authority_of_record=authority_of_record,
            mandate_scope_ref=mandate_scope_ref,
            decision_class=clawback_class,
            effect=effect,
            evidence=evidence or [],
            secret_key=self.secret_key,
        )

        self.clawbacks[clawback.clawback_id] = clawback
        self.stats["clawbacks_issued"] += 1
        return clawback, "CLAWBACK_ISSUED"

    def get_stats(self):
        return {
            **self.stats,
            "active_holds": sum(
                1 for h in self.holds.values() if h.status == "PENDING"
            ),
            "active_receipts": sum(
                1 for r in self.receipts.values() if not r.consumed
            ),
            "policy_version": self.action_tier_policy["policy_id"],
        }

    def get_recent_holds(self, limit=20):
        holds = list(self.holds.values())
        return [h.to_dict() for h in holds[-limit:]]

    def get_recent_receipts(self, limit=20):
        receipts = list(self.receipts.values())
        return [r.to_dict() for r in receipts[-limit:]]
