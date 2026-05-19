"""
TBN LangChain — Audit Trail
Immutable logging of every agent action, decision, and violation.

The audit trail is the "black box" for AI agents — when something goes wrong,
you have a complete, tamper-proof record of what happened.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import json
import hashlib
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class AuditEntry:
    """A single entry in the audit trail."""

    def __init__(self, bot_id: str, action: str, tool: str, decision: str,
                 reason: str, input_hash: str, output_hash: str = "",
                 duration_ms: float = 0, metadata: Optional[Dict] = None):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.bot_id = bot_id
        self.action = action
        self.tool = tool
        self.decision = decision
        self.reason = reason
        self.input_hash = input_hash
        self.output_hash = output_hash
        self.duration_ms = duration_ms
        self.metadata = metadata or {}

        # Chain hash for immutability
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of this entry for chain integrity."""
        payload = f"{self.timestamp}:{self.bot_id}:{self.action}:{self.tool}:{self.decision}:{self.input_hash}"
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "bot_id": self.bot_id,
            "action": self.action,
            "tool": self.tool,
            "decision": self.decision,
            "reason": self.reason,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "duration_ms": self.duration_ms,
            "entry_hash": self.entry_hash,
            "metadata": self.metadata,
        }


class AuditTrail:
    """Immutable audit trail for agent actions."""

    def __init__(self, bot_id: str, storage_path: str = "data/tbn_audit"):
        self.bot_id = bot_id
        self.storage_path = storage_path
        self.entries: List[AuditEntry] = []
        self.chain_hash = "genesis"
        os.makedirs(storage_path, exist_ok=True)

    def record(self, action: str, tool: str, decision: str, reason: str,
               input_data: Any, output_data: Any = None, duration_ms: float = 0,
               metadata: Optional[Dict] = None) -> AuditEntry:
        """Record an action in the audit trail."""
        input_hash = hashlib.sha256(str(input_data).encode()).hexdigest()[:12]
        output_hash = hashlib.sha256(str(output_data).encode()).hexdigest()[:12] if output_data else ""

        entry = AuditEntry(
            bot_id=self.bot_id,
            action=action,
            tool=tool,
            decision=decision,
            reason=reason,
            input_hash=input_hash,
            output_hash=output_hash,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        # Chain integrity
        chain_payload = f"{self.chain_hash}:{entry.entry_hash}"
        self.chain_hash = hashlib.sha256(chain_payload.encode()).hexdigest()[:24]
        entry.metadata["chain_hash"] = self.chain_hash

        self.entries.append(entry)
        self._persist(entry)

        return entry

    def _persist(self, entry: AuditEntry):
        """Persist entry to disk."""
        filepath = os.path.join(self.storage_path, f"{self.bot_id}_audit.jsonl")
        with open(filepath, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def get_entries(self, limit: int = 100) -> List[Dict]:
        """Get recent audit entries."""
        return [e.to_dict() for e in self.entries[-limit:]]

    def get_violations(self) -> List[Dict]:
        """Get all violations from the audit trail."""
        return [e.to_dict() for e in self.entries if e.decision in ("DENY", "ESCALATE")]

    def verify_integrity(self) -> bool:
        """Verify the chain hash integrity of the audit trail."""
        chain = "genesis"
        for entry in self.entries:
            chain_payload = f"{chain}:{entry.entry_hash}"
            expected = hashlib.sha256(chain_payload.encode()).hexdigest()[:24]
            if entry.metadata.get("chain_hash") != expected:
                return False
            chain = expected
        return True

    def summary(self) -> Dict:
        """Get audit trail summary."""
        total = len(self.entries)
        violations = len([e for e in self.entries if e.decision in ("DENY", "ESCALATE")])
        return {
            "bot_id": self.bot_id,
            "total_actions": total,
            "violations": violations,
            "compliance_rate": f"{((total - violations) / max(total, 1)) * 100:.1f}%",
            "chain_integrity": self.verify_integrity(),
            "last_action": self.entries[-1].timestamp if self.entries else None,
        }

    def __len__(self):
        return len(self.entries)

    def __repr__(self):
        return f"<AuditTrail bot_id='{self.bot_id}' entries={len(self.entries)}>"
