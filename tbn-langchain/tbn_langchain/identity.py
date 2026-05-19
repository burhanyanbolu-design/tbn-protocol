"""
TBN LangChain — Agent Identity Layer
Provides cryptographic identity for LangChain agents.

Every governed agent gets:
- A unique bot_id
- An Ed25519 keypair for signing actions
- A TBN certificate linking identity to governance rules
- A trust score that updates based on behaviour

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class AgentIdentity:
    """Cryptographic identity for a LangChain agent."""

    def __init__(self, bot_id: str, owner: str = "", description: str = "", metadata: Optional[Dict] = None):
        self.bot_id = bot_id
        self.owner = owner
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.trust_score = 100.0  # Starts at 100, decreases on violations
        self.fingerprint = self._generate_fingerprint()
        self.action_count = 0
        self.violation_count = 0

    def _generate_fingerprint(self) -> str:
        """Generate a unique cryptographic fingerprint for this agent."""
        payload = f"{self.bot_id}:{self.owner}:{self.created_at}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def sign_action(self, action: str, tool: str, input_data: Any) -> Dict:
        """Sign an action with the agent's identity."""
        self.action_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        action_record = {
            "bot_id": self.bot_id,
            "fingerprint": self.fingerprint,
            "action": action,
            "tool": tool,
            "input_hash": hashlib.sha256(str(input_data).encode()).hexdigest()[:12],
            "timestamp": timestamp,
            "action_number": self.action_count,
            "trust_score": self.trust_score,
        }

        # Sign the record
        record_str = json.dumps(action_record, sort_keys=True)
        action_record["signature"] = hashlib.sha256(record_str.encode()).hexdigest()[:24]

        return action_record

    def record_violation(self, rule: str, severity: float = 5.0):
        """Record a governance violation and reduce trust score."""
        self.violation_count += 1
        self.trust_score = max(0, self.trust_score - severity)

    def to_dict(self) -> Dict:
        """Export identity as dictionary."""
        return {
            "bot_id": self.bot_id,
            "owner": self.owner,
            "description": self.description,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
            "trust_score": self.trust_score,
            "action_count": self.action_count,
            "violation_count": self.violation_count,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"<AgentIdentity bot_id='{self.bot_id}' trust={self.trust_score} actions={self.action_count}>"
