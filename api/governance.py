"""
TBN Protocol — Data Governance API
Endpoints for managing data sharing agreements and validating data scope.
"""

from flask import Blueprint, request, jsonify, render_template
from tbn.data_governance import (
    DataGovernanceEngine,
    DataSharingAgreement,
    DataScopeDeclaration,
    ACCESS_LEVELS,
    ALLOWED_DATA_TYPES,
    RETENTION_POLICIES,
)

governance = Blueprint('governance', __name__)

# Shared governance engine
_engine = None

def get_engine() -> DataGovernanceEngine:
    global _engine
    if _engine is None:
        _engine = DataGovernanceEngine()
    return _engine


# ── Portal ────────────────────────────────────────────────────────────

@governance.route("/portal")
def governance_portal():
    """Render the data governance dashboard."""
    return render_template("governance_dashboard.html")


# ── Agreements ────────────────────────────────────────────────────────

@governance.route("/agreements", methods=["GET"])
def list_agreements():
    """List all data sharing agreements."""
    try:
        agreements = get_engine().list_agreements()
        return jsonify({"success": True, "agreements": agreements, "total": len(agreements)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance.route("/agreements", methods=["POST"])
def create_agreement():
    """Create a new data sharing agreement."""
    try:
        data = request.get_json()

        agreement = DataSharingAgreement(
            company_id=data.get("company_id", "").strip(),
            company_name=data.get("company_name", "").strip(),
            allowed_data_types=data.get("allowed_data_types", []),
            allowed_fields=data.get("allowed_fields", {}),
            blocked_fields=data.get("blocked_fields", {}),
            max_records_per_request=data.get("max_records_per_request", 100),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 60),
            access_level=data.get("access_level", "LIMITED"),
            allowed_bot_ids=data.get("allowed_bot_ids", []),
            allowed_cert_levels=data.get("allowed_cert_levels", ["COMMUNITY", "STANDARD"]),
            internal_bots=data.get("internal_bots", []),
        )

        if not agreement.company_id or not agreement.company_name:
            return jsonify({"error": "company_id and company_name are required"}), 400

        result = get_engine().create_agreement(agreement)
        return jsonify(result), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance.route("/agreements/<company_id>", methods=["GET"])
def get_agreement(company_id):
    """Get a specific company's data sharing agreement."""
    try:
        agreement = get_engine().get_agreement(company_id)
        if not agreement:
            return jsonify({"error": "Agreement not found"}), 404
        return jsonify({"success": True, "agreement": agreement.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance.route("/agreements/<company_id>/access-level", methods=["PATCH"])
def update_access_level(company_id):
    """Dynamically change a company's access level."""
    try:
        data = request.get_json()
        new_level = data.get("access_level", "").upper()
        result = get_engine().update_access_level(company_id, new_level)
        if not result["success"]:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Scope Validation ──────────────────────────────────────────────────

@governance.route("/validate", methods=["POST"])
def validate_scope():
    """
    Validate a bot's data scope declaration against a company's agreement.

    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "company_id": "company-id",
        "data_type": "patient_demographics",
        "fields_requested": ["name", "dob", "nhs_number"],
        "max_records": 50,
        "purpose": "Clinical decision support",
        "retention": "session_only",
        "environment": "external",
        "bot_cert_level": "COMMUNITY"
    }
    """
    try:
        data = request.get_json()

        scope = DataScopeDeclaration(
            bot_id=data.get("bot_id", "").strip(),
            data_type=data.get("data_type", "").strip(),
            fields_requested=data.get("fields_requested", []),
            max_records=data.get("max_records", 100),
            purpose=data.get("purpose", ""),
            retention=data.get("retention", "session_only"),
            environment=data.get("environment", "external"),
        )

        company_id = data.get("company_id", "").strip()
        bot_cert_level = data.get("bot_cert_level", "STANDARD").upper()

        if not scope.bot_id or not company_id or not scope.data_type:
            return jsonify({"error": "bot_id, company_id, and data_type are required"}), 400

        result = get_engine().validate_scope(scope, company_id, bot_cert_level)

        status_code = 200 if result["allowed"] else 403
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Access Log ────────────────────────────────────────────────────────

@governance.route("/log", methods=["GET"])
def access_log():
    """Get recent data access log."""
    try:
        limit = int(request.args.get("limit", 50))
        log = get_engine().get_access_log(limit)
        return jsonify({"success": True, "log": log, "total": len(log)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Stats ─────────────────────────────────────────────────────────────

@governance.route("/stats", methods=["GET"])
def governance_stats():
    """Get governance statistics."""
    try:
        stats = get_engine().get_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Schema Info ───────────────────────────────────────────────────────

@governance.route("/schema", methods=["GET"])
def schema_info():
    """Get available data types, access levels, and retention policies."""
    return jsonify({
        "success": True,
        "allowed_data_types": ALLOWED_DATA_TYPES,
        "access_levels": ACCESS_LEVELS,
        "retention_policies": RETENTION_POLICIES,
    })
