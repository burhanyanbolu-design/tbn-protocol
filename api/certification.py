"""
Community Bot Certification Portal
Web interface for bot certification management.
Handles certification applications, approvals, and violations.
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone
import json
import os

certification = Blueprint('certification', __name__)

@certification.route("/portal")
def certification_portal():
    """Render the certification portal web interface."""
    return render_template("certification_portal.html")

@certification.route("/api/certify", methods=["POST"])
def certify_bot():
    """
    Certify a bot with a specific level.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "level": "COMMUNITY|STANDARD|RESTRICTED",
        "purpose": "Required for COMMUNITY level",
        "ethical_declaration": true
    }
    """
    try:
        # Import here to avoid circular imports
        from .state import bica
        from tbn.certification import CertificationAuthority, CertLevel
        
        data = request.get_json()
        bot_id = data.get("bot_id", "").strip()
        level = data.get("level", "STANDARD").upper()
        purpose = data.get("purpose", "").strip()
        ethical_declaration = data.get("ethical_declaration", False)
        
        if not bot_id:
            return jsonify({"error": "bot_id is required"}), 400
        
        if level not in ["COMMUNITY", "STANDARD", "RESTRICTED"]:
            return jsonify({"error": "Invalid certification level"}), 400
        
        # Validate COMMUNITY certification requirements
        if level == "COMMUNITY":
            if not purpose:
                return jsonify({"error": "Purpose is required for COMMUNITY certification"}), 400
            if not ethical_declaration:
                return jsonify({"error": "Ethical declaration is required for COMMUNITY certification"}), 400
        
        # Get certification authority
        ca = CertificationAuthority(bica)
        
        # Check if bot exists
        bots = bica.list_bots()
        bot_cert = next((b for b in bots if b["bot_id"] == bot_id), None)
        if not bot_cert:
            return jsonify({"error": "Bot not found in registry"}), 404
        
        # Get bot identity for certification
        from .state import bots as registered_bots
        bot = registered_bots.get(bot_id)
        if not bot:
            return jsonify({"error": "Bot not found in active registry"}), 404
        
        # Certify the bot
        try:
            cert_level = CertLevel(level)
            cert = ca.certify(
                identity=bot.identity,
                level=cert_level,
                purpose=purpose,
                ethical_declaration=ethical_declaration,
            )
            
            # Log certification event
            _log_certification_event(bot_id, level, purpose, ethical_declaration)
            
            return jsonify({
                "success": True,
                "bot_id": bot_id,
                "cert_level": level,
                "purpose": purpose if level == "COMMUNITY" else None,
                "certified_at": cert.issued_at,
                "message": f"Bot certified as {level}"
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@certification.route("/api/violation", methods=["POST"])
def report_violation():
    """
    Report a bot violation.
    
    Body:
    {
        "bot_id": "tbn-bot-xxxx",
        "violation": "Description of violation",
        "reporter": "Optional reporter info"
    }
    """
    try:
        data = request.get_json()
        bot_id = data.get("bot_id", "").strip()
        violation = data.get("violation", "").strip()
        reporter = data.get("reporter", "anonymous")
        
        if not bot_id or not violation:
            return jsonify({"error": "bot_id and violation are required"}), 400
        
        # Log violation
        violation_record = {
            "bot_id": bot_id,
            "violation": violation,
            "reporter": reporter,
            "reported_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review"
        }
        
        _log_violation(violation_record)
        
        return jsonify({
            "success": True,
            "message": "Violation reported successfully",
            "violation_id": f"viol-{bot_id}-{int(datetime.now().timestamp())}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@certification.route("/api/certifications", methods=["GET"])
def list_certifications():
    """List all bot certifications."""
    try:
        from .state import bica
        from tbn.certification import CertificationAuthority
        
        ca = CertificationAuthority(bica)
        bots = bica.list_bots()
        
        # Group by certification level
        certifications = {
            "COMMUNITY": [],
            "STANDARD": [],
            "RESTRICTED": []
        }
        
        for bot in bots:
            cert = ca.get_cert(bot["bot_id"])
            level = cert.level.value if cert else "STANDARD"
            
            if level in certifications:
                certifications[level].append({
                    "bot_id": bot["bot_id"],
                    "name": bot["name"],
                    "cert_level": level,
                    "certified_at": cert.issued_at if cert else bot.get("created_at"),
                    "purpose": cert.purpose if cert else ""
                })
        
        return jsonify({
            "success": True,
            "certifications": certifications,
            "total": len(bots)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@certification.route("/api/certification/<bot_id>", methods=["GET"])
def get_certification(bot_id):
    """Get certification details for a specific bot."""
    try:
        from .state import bica
        from tbn.certification import CertificationAuthority
        
        ca = CertificationAuthority(bica)
        bots = bica.list_bots()
        bot_cert = next((b for b in bots if b["bot_id"] == bot_id), None)
        
        if not bot_cert:
            return jsonify({"error": "Bot not found"}), 404
        
        cert = ca.get_cert(bot_id)
        
        return jsonify({
            "success": True,
            "certification": {
                "bot_id": bot_cert["bot_id"],
                "name": bot_cert["name"],
                "cert_level": cert.level.value if cert else "STANDARD",
                "certified_at": cert.issued_at if cert else bot_cert.get("created_at"),
                "purpose": cert.purpose if cert else "",
                "ethical_declaration": cert.ethical_declaration if cert else False,
                "created_at": bot_cert["created_at"]
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@certification.route("/api/violations", methods=["GET"])
def list_violations():
    """List recent violations (admin endpoint)."""
    try:
        violations_file = "data/violations.json"
        
        if os.path.exists(violations_file):
            with open(violations_file, "r") as f:
                violations = json.load(f)
        else:
            violations = []
        
        # Return recent violations (last 50)
        recent_violations = violations[-50:] if len(violations) > 50 else violations
        
        return jsonify({
            "success": True,
            "violations": recent_violations,
            "total": len(violations)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper functions

def _log_certification_event(bot_id: str, level: str, purpose: str, ethical_declaration: bool):
    """Log a certification event."""
    try:
        log_file = "data/certification_log.json"
        
        event = {
            "bot_id": bot_id,
            "level": level,
            "purpose": purpose,
            "ethical_declaration": ethical_declaration,
            "certified_at": datetime.now(timezone.utc).isoformat(),
            "certified_by": "system"
        }
        
        # Load existing log
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                log = json.load(f)
        else:
            log = []
        
        # Add new event
        log.append(event)
        
        # Save log
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        with open(log_file, "w") as f:
            json.dump(log, f, indent=2)
            
    except Exception as e:
        print(f"❌ Error logging certification event: {e}")

def _log_violation(violation_record: dict):
    """Log a violation report."""
    try:
        violations_file = "data/violations.json"
        
        # Load existing violations
        if os.path.exists(violations_file):
            with open(violations_file, "r") as f:
                violations = json.load(f)
        else:
            violations = []
        
        # Add new violation
        violations.append(violation_record)
        
        # Save violations
        os.makedirs(os.path.dirname(violations_file) or ".", exist_ok=True)
        with open(violations_file, "w") as f:
            json.dump(violations, f, indent=2)
            
    except Exception as e:
        print(f"❌ Error logging violation: {e}")