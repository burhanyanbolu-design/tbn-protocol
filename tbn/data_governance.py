"""
TBN Protocol — Data Governance Layer
Controls what data flows between bots, how much, and under what rules.

This is the enterprise layer on top of the trust/identity foundation.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ── Data Types ────────────────────────────────────────────────────────

ALLOWED_DATA_TYPES = [
    "patient_demographics",
    "medical_records",
    "financial_data",
    "personal_identifiable_info",
    "public_data",
    "product_catalog",
    "search_results",
    "analytics",
    "audit_logs",
    "custom",
]

ACCESS_LEVELS = ["FULL", "LIMITED", "RESTRICTED"]

RETENTION_POLICIES = ["session_only", "24_hours", "7_days", "30_days", "permanent"]


# ── Data Scope Declaration ────────────────────────────────────────────

class DataScopeDeclaration:
    """
    A bot declares exactly what data it needs before accessing a system.
    The receiving system validates this against its data sharing agreement.
    """

    def __init__(
        self,
        bot_id: str,
        data_type: str,
        fields_requested: List[str],
        max_records: int = 100,
        purpose: str = "",
        retention: str = "session_only",
        environment: str = "external",  # external or internal
    ):
        self.bot_id = bot_id
        self.data_type = data_type
        self.fields_requested = fields_requested
        self.max_records = max_records
        self.purpose = purpose
        self.retention = retention
        self.environment = environment
        self.declared_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "bot_id": self.bot_id,
            "data_type": self.data_type,
            "fields_requested": self.fields_requested,
            "max_records": self.max_records,
            "purpose": self.purpose,
            "retention": self.retention,
            "environment": self.environment,
            "declared_at": self.declared_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataScopeDeclaration":
        return cls(
            bot_id=data["bot_id"],
            data_type=data["data_type"],
            fields_requested=data.get("fields_requested", []),
            max_records=data.get("max_records", 100),
            purpose=data.get("purpose", ""),
            retention=data.get("retention", "session_only"),
            environment=data.get("environment", "external"),
        )


# ── Data Sharing Agreement ────────────────────────────────────────────

class DataSharingAgreement:
    """
    A company defines what data bots can access.
    This is the policy that governs all bot interactions.
    """

    def __init__(
        self,
        company_id: str,
        company_name: str,
        allowed_data_types: List[str],
        allowed_fields: Dict[str, List[str]],  # data_type -> allowed fields
        blocked_fields: Dict[str, List[str]],  # data_type -> blocked fields
        max_records_per_request: int = 100,
        rate_limit_per_minute: int = 60,
        access_level: str = "LIMITED",
        allowed_bot_ids: List[str] = None,  # None = all certified bots
        allowed_cert_levels: List[str] = None,  # None = all levels
        internal_bots: List[str] = None,  # bots with relaxed restrictions
        created_at: str = None,
        updated_at: str = None,
    ):
        self.company_id = company_id
        self.company_name = company_name
        self.allowed_data_types = allowed_data_types
        self.allowed_fields = allowed_fields
        self.blocked_fields = blocked_fields
        self.max_records_per_request = max_records_per_request
        self.rate_limit_per_minute = rate_limit_per_minute
        self.access_level = access_level
        self.allowed_bot_ids = allowed_bot_ids or []
        self.allowed_cert_levels = allowed_cert_levels or ["COMMUNITY", "STANDARD"]
        self.internal_bots = internal_bots or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "allowed_data_types": self.allowed_data_types,
            "allowed_fields": self.allowed_fields,
            "blocked_fields": self.blocked_fields,
            "max_records_per_request": self.max_records_per_request,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "access_level": self.access_level,
            "allowed_bot_ids": self.allowed_bot_ids,
            "allowed_cert_levels": self.allowed_cert_levels,
            "internal_bots": self.internal_bots,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataSharingAgreement":
        return cls(**{k: v for k, v in data.items() if k in cls.__init__.__code__.co_varnames})


# ── Governance Engine ─────────────────────────────────────────────────

class DataGovernanceEngine:
    """
    The core engine that validates data scope declarations against
    data sharing agreements and enforces data governance policies.
    """

    def __init__(self, agreements_path: str = "data/governance_agreements.json"):
        self.agreements_path = agreements_path
        self._agreements: Dict[str, DataSharingAgreement] = {}
        self._access_log: List[dict] = []
        self._rate_tracker: Dict[str, List[float]] = {}
        self._load()

    def _load(self):
        """Load agreements from file."""
        if os.path.exists(self.agreements_path):
            with open(self.agreements_path) as f:
                data = json.load(f)
                for company_id, agreement_data in data.items():
                    self._agreements[company_id] = DataSharingAgreement.from_dict(agreement_data)
            print(f"[Governance] Loaded {len(self._agreements)} data sharing agreements")

    def _save(self):
        """Save agreements to file."""
        os.makedirs(os.path.dirname(self.agreements_path) or ".", exist_ok=True)
        with open(self.agreements_path, "w") as f:
            json.dump(
                {k: v.to_dict() for k, v in self._agreements.items()},
                f, indent=2
            )

    def create_agreement(self, agreement: DataSharingAgreement) -> dict:
        """Create or update a data sharing agreement."""
        self._agreements[agreement.company_id] = agreement
        self._save()
        print(f"[Governance] Agreement created: {agreement.company_name}")
        return {"success": True, "company_id": agreement.company_id}

    def get_agreement(self, company_id: str) -> Optional[DataSharingAgreement]:
        """Get a company's data sharing agreement."""
        return self._agreements.get(company_id)

    def list_agreements(self) -> List[dict]:
        """List all agreements."""
        return [a.to_dict() for a in self._agreements.values()]

    def update_access_level(self, company_id: str, new_level: str) -> dict:
        """Dynamically change a company's access level."""
        if company_id not in self._agreements:
            return {"success": False, "error": "Agreement not found"}
        if new_level not in ACCESS_LEVELS:
            return {"success": False, "error": f"Invalid level. Use: {ACCESS_LEVELS}"}

        old_level = self._agreements[company_id].access_level
        self._agreements[company_id].access_level = new_level
        self._agreements[company_id].updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

        print(f"[Governance] Access level changed: {company_id} {old_level} → {new_level}")
        return {"success": True, "old_level": old_level, "new_level": new_level}

    def validate_scope(
        self,
        scope: DataScopeDeclaration,
        company_id: str,
        bot_cert_level: str = "STANDARD",
    ) -> dict:
        """
        Validate a bot's data scope declaration against a company's agreement.
        Returns: {allowed: bool, reason: str, filtered_fields: list}
        """
        import time

        agreement = self._agreements.get(company_id)

        # No agreement = default deny
        if not agreement:
            return self._deny(scope, "No data sharing agreement found for this company")

        # Check bot certification level
        if bot_cert_level not in agreement.allowed_cert_levels:
            return self._deny(scope, f"Bot certification level {bot_cert_level} not allowed. Required: {agreement.allowed_cert_levels}")

        # Check specific bot whitelist
        if agreement.allowed_bot_ids and scope.bot_id not in agreement.allowed_bot_ids:
            # Check if it's an internal bot
            if scope.bot_id not in agreement.internal_bots:
                return self._deny(scope, "Bot not in allowed list for this company")

        # Check data type
        if scope.data_type not in agreement.allowed_data_types:
            return self._deny(scope, f"Data type '{scope.data_type}' not allowed. Allowed: {agreement.allowed_data_types}")

        # Check rate limit
        now = time.time()
        bot_key = f"{scope.bot_id}:{company_id}"
        if bot_key not in self._rate_tracker:
            self._rate_tracker[bot_key] = []
        # Clean old entries (older than 60 seconds)
        self._rate_tracker[bot_key] = [t for t in self._rate_tracker[bot_key] if now - t < 60]
        if len(self._rate_tracker[bot_key]) >= agreement.rate_limit_per_minute:
            return self._deny(scope, f"Rate limit exceeded: {agreement.rate_limit_per_minute} requests/minute")
        self._rate_tracker[bot_key].append(now)

        # Check max records
        if scope.max_records > agreement.max_records_per_request:
            scope.max_records = agreement.max_records_per_request  # Cap it

        # Filter fields
        allowed_fields = agreement.allowed_fields.get(scope.data_type, [])
        blocked_fields = agreement.blocked_fields.get(scope.data_type, [])

        # Internal bots get relaxed restrictions
        is_internal = scope.bot_id in agreement.internal_bots
        if is_internal and agreement.access_level == "FULL":
            filtered_fields = scope.fields_requested
        else:
            # Filter: only allowed fields, remove blocked fields
            if allowed_fields:
                filtered_fields = [f for f in scope.fields_requested if f in allowed_fields]
            else:
                filtered_fields = scope.fields_requested
            filtered_fields = [f for f in filtered_fields if f not in blocked_fields]

        if not filtered_fields:
            return self._deny(scope, "No allowed fields in request after filtering")

        # Log the access
        self._log_access(scope, company_id, True, filtered_fields)

        return {
            "allowed": True,
            "bot_id": scope.bot_id,
            "company_id": company_id,
            "data_type": scope.data_type,
            "filtered_fields": filtered_fields,
            "max_records": scope.max_records,
            "retention": scope.retention,
            "access_level": agreement.access_level,
            "is_internal": is_internal,
            "reason": "Access granted — scope validated against data sharing agreement",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _deny(self, scope: DataScopeDeclaration, reason: str) -> dict:
        """Deny access and log it."""
        self._log_access(scope, "unknown", False, [], reason)
        return {
            "allowed": False,
            "bot_id": scope.bot_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _log_access(
        self,
        scope: DataScopeDeclaration,
        company_id: str,
        allowed: bool,
        fields: List[str],
        reason: str = "",
    ):
        """Log every access attempt."""
        entry = {
            "bot_id": scope.bot_id,
            "company_id": company_id,
            "data_type": scope.data_type,
            "fields_requested": scope.fields_requested,
            "fields_granted": fields,
            "allowed": allowed,
            "reason": reason,
            "purpose": scope.purpose,
            "environment": scope.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._access_log.append(entry)

        # Persist log
        log_path = "data/governance_log.json"
        try:
            existing = []
            if os.path.exists(log_path):
                with open(log_path) as f:
                    existing = json.load(f)
            existing.append(entry)
            # Keep last 1000 entries
            if len(existing) > 1000:
                existing = existing[-1000:]
            os.makedirs("data", exist_ok=True)
            with open(log_path, "w") as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            print(f"[Governance] Log error: {e}")

    def get_access_log(self, limit: int = 50) -> List[dict]:
        """Get recent access log entries."""
        log_path = "data/governance_log.json"
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = json.load(f)
            return list(reversed(log[-limit:]))
        return []

    def get_stats(self) -> dict:
        """Get governance statistics."""
        log = self.get_access_log(1000)
        total = len(log)
        allowed = sum(1 for e in log if e.get("allowed"))
        denied = total - allowed
        return {
            "total_agreements": len(self._agreements),
            "total_access_attempts": total,
            "allowed": allowed,
            "denied": denied,
            "deny_rate": f"{(denied/total*100):.1f}%" if total > 0 else "0%",
        }


# ── Default NHS Agreement (example) ──────────────────────────────────

def create_nhs_example_agreement() -> DataSharingAgreement:
    """Example NHS data sharing agreement."""
    return DataSharingAgreement(
        company_id="nhs-royal-london",
        company_name="Royal London Hospital NHS Trust",
        allowed_data_types=["patient_demographics", "medical_records"],
        allowed_fields={
            "patient_demographics": ["nhs_number", "name", "dob", "postcode"],
            "medical_records": ["diagnosis_code", "appointment_date", "department"],
        },
        blocked_fields={
            "patient_demographics": ["address", "phone", "email", "next_of_kin"],
            "medical_records": ["full_notes", "prescriptions", "test_results"],
        },
        max_records_per_request=50,
        rate_limit_per_minute=30,
        access_level="LIMITED",
        allowed_cert_levels=["COMMUNITY"],
        internal_bots=[],
    )
