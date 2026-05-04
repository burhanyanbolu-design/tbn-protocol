"""
Community Bot Certification Portal
Web interface for bot certification management.
Handles certification applications, approvals, and violations.
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone
import json
import os

from ..tbn.github_bica import GitHubBICA
from ..tbn.identity import BICA

certification = Blueprint('certification', __name__)

# Initialize BICA (GitHub-backed in production, local in development)
def get_bica():
    """Get BICA instance based on environment."""
    if os.environ.get("TBN_ENV") == "production":
        github_token = os.environ.get("TBN_GITHUB_TOKEN", "")
        github_repo = os.environ.get("TBN_GITHUB_REPO", "burhanyanbolu-design/tbn-bica-registry")
        
        if github_token:
            return GitHubBICA(repo=github_repo, token=github_token)
        else:
            print("⚠️  No GitHub token configured, using local BICA")
            return BICA(registry_path="data/bica_registry.json")
    else:
        return BICA(registry_path="data/bica_registry.json")

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
        
        # Get BICA instance
        bica = get_bica()
        
        # Check if bot exists
        if hasattr(bica, 'get_bot_certificate'):
            # GitHub BICA
            cert = bica.get_bot_certificate(bot_id)
            if not cert:
                return jsonify({"error": "Bot not found in registry"}), 404
            
            # Certify the bot
            success = bica.certify_bot(bot_id, level, purpose, ethical_declaration)
        else:
            # Local BICA
            bots = bica.list_bots()
            bot_cert = next((b for b in bots if b["bot_id"] == bot_id), None)
            if not bot_cert:
                return jsonify({"error": "Bot not found in registry"}), 404
            
            # For local BICA, we'll simulate certification
            success = True
        
        if success:
            # Log certification event
            _log_certification_event(bot_id, level, purpose, ethical_declaration)
            
            return jsonify({
                "success": True,
                "bot_id": bot_id,
                "cert_level": level,
                "purpose": purpose if level == "COMMUNITY" else None,
                "certified_at": datetime.now(timezone.utc).isoformat(),
                "message": f"Bot certified as {level}"
            })
        else:
            return jsonify({"error": "Certification failed"}), 500
            
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
        
        # For now, we'll just log violations
        # In a full implementation, this would trigger a review process
        
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
        bica = get_bica()
        bots = bica.list_bots()
        
        # Group by certification level
        certifications = {
            "COMMUNITY": [],
            "STANDARD": [],
            "RESTRICTED": []
        }
        
        for bot in bots:
            level = bot.get("cert_level", "STANDARD")
            if level in certifications:
                certifications[level].append({
                    "bot_id": bot["bot_id"],
                    "name": bot["name"],
                    "cert_level": level,
                    "certified_at": bot.get("certified_at", bot.get("created_at")),
                    "purpose": bot.get("purpose", "")
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
        bica = get_bica()
        
        if hasattr(bica, 'get_bot_certificate'):
            # GitHub BICA
            cert = bica.get_bot_certificate(bot_id)
        else:
            # Local BICA
            bots = bica.list_bots()
            cert = next((b for b in bots if b["bot_id"] == bot_id), None)
        
        if not cert:
            return jsonify({"error": "Bot not found"}), 404
        
        return jsonify({
            "success": True,
            "certification": {
                "bot_id": cert["bot_id"],
                "name": cert["name"],
                "cert_level": cert.get("cert_level", "STANDARD"),
                "certified_at": cert.get("certified_at", cert.get("created_at")),
                "purpose": cert.get("purpose", ""),
                "ethical_declaration": cert.get("ethical_declaration", False),
                "created_at": cert["created_at"]
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