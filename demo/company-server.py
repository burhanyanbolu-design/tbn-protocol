#!/usr/bin/env python3
"""
Company Server - Computer 1 (AWS Server)
Represents a company that uses TBN infrastructure to verify bots
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuration
COMPANY_NAME = "Acme Corp"
TBN_SERVER = "https://tbn.hardinai.co.uk"
PORT = 5010

# Access log
access_log = []

# Company's tbn.json configuration
TBN_CONFIG = {
    "tbn_version": "1.0",
    "company": COMPANY_NAME,
    "domain": "acme-corp.com",
    "bot_policy": {
        "certified_bots_only": True,
        "require_tbn_certificate": True,
        "minimum_certification_level": "STANDARD",
        "log_all_access": True
    },
    "public_resources": [
        {
            "endpoint": "/api/data",
            "description": "Company data API",
            "authentication": "tbn_certificate_required",
            "rate_limit": "100/hour"
        }
    ],
    "contact": {
        "email": "api@acme-corp.com",
        "tbn_verification_endpoint": "/api/verify-bot"
    }
}

# Company's valuable data
COMPANY_DATA = {
    "company": COMPANY_NAME,
    "products": [
        {"name": "AI Tool Alpha", "category": "NLP", "price": "$99/mo"},
        {"name": "AI Tool Beta", "category": "Computer Vision", "price": "$199/mo"},
        {"name": "AI Tool Gamma", "category": "Predictive Analytics", "price": "$299/mo"}
    ],
    "pricing_tiers": {
        "starter": "$99/month",
        "professional": "$299/month",
        "enterprise": "Contact sales"
    },
    "api_documentation": "https://acme-corp.com/docs",
    "support": "support@acme-corp.com"
}


@app.route('/tbn.json')
def tbn_json():
    """
    Serve the tbn.json file - this tells bots we use TBN infrastructure
    """
    print(f"\n📄 [{COMPANY_NAME}] tbn.json requested")
    return jsonify(TBN_CONFIG)


@app.route('/api/verify-bot', methods=['POST'])
def verify_bot():
    """
    Verify a bot's TBN certificate
    This is the KEY function - company doesn't build verification,
    they just check with TBN!
    """
    data = request.json
    bot_id = data.get('bot_id')
    
    if not bot_id:
        return jsonify({"error": "bot_id required"}), 400
    
    print(f"\n🔍 [{COMPANY_NAME}] Verifying bot: {bot_id}")
    print(f"   Checking with TBN infrastructure at {TBN_SERVER}...")
    
    try:
        # Ask TBN: "Is this bot certified?"
        response = requests.post(
            f"{TBN_SERVER}/api/verify",
            json={"bot_id": bot_id},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("verified"):
                cert_level = result.get("certification_level", "STANDARD")
                bot_name = result.get("name", "Unknown")
                
                print(f"   ✅ Bot verified by TBN!")
                print(f"   📜 Bot name: {bot_name}")
                print(f"   📜 Certification level: {cert_level}")
                
                # Log the verification
                log_entry = {
                    "bot_id": bot_id,
                    "bot_name": bot_name,
                    "timestamp": datetime.now().isoformat(),
                    "action": "verification",
                    "verified": True,
                    "certification_level": cert_level
                }
                access_log.append(log_entry)
                
                return jsonify({
                    "verified": True,
                    "bot_id": bot_id,
                    "bot_name": bot_name,
                    "certification_level": cert_level,
                    "message": "Bot verified by TBN infrastructure"
                })
            else:
                print(f"   ❌ Bot NOT verified by TBN")
                
                log_entry = {
                    "bot_id": bot_id,
                    "timestamp": datetime.now().isoformat(),
                    "action": "verification",
                    "verified": False
                }
                access_log.append(log_entry)
                
                return jsonify({
                    "verified": False,
                    "error": "Bot not certified by TBN"
                }), 403
        else:
            print(f"   ❌ TBN verification failed: {response.status_code}")
            return jsonify({"error": "TBN verification failed"}), 500
            
    except Exception as e:
        print(f"   ❌ Error verifying with TBN: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/data', methods=['GET', 'POST'])
def get_data():
    """
    Provide company data to certified bots only
    """
    # Get bot_id from header or body
    bot_id = request.headers.get('X-TBN-Bot-ID') or request.json.get('bot_id') if request.json else None
    
    if not bot_id:
        print(f"\n❌ [{COMPANY_NAME}] Data request without bot_id")
        return jsonify({"error": "TBN bot_id required"}), 401
    
    print(f"\n📊 [{COMPANY_NAME}] Data requested by bot: {bot_id}")
    
    # Verify the bot with TBN
    verify_response = verify_bot()
    verify_data = verify_response[0].get_json() if isinstance(verify_response, tuple) else verify_response.get_json()
    
    if verify_data.get("verified"):
        print(f"   ✅ Access GRANTED")
        print(f"   Providing company data...")
        
        # Log the data access
        log_entry = {
            "bot_id": bot_id,
            "bot_name": verify_data.get("bot_name"),
            "timestamp": datetime.now().isoformat(),
            "action": "data_access",
            "verified": True,
            "certification_level": verify_data.get("certification_level")
        }
        access_log.append(log_entry)
        
        return jsonify({
            "success": True,
            "data": COMPANY_DATA,
            "message": "Data provided because you have a valid TBN certificate",
            "accessed_at": datetime.now().isoformat()
        })
    else:
        print(f"   ❌ Access DENIED - No valid TBN certificate")
        
        return jsonify({
            "success": False,
            "error": "TBN certification required to access this data"
        }), 403


@app.route('/api/access-log')
def get_access_log():
    """
    Show all bot access attempts
    """
    print(f"\n📊 [{COMPANY_NAME}] Access log requested")
    return jsonify({
        "company": COMPANY_NAME,
        "total_requests": len(access_log),
        "log": access_log
    })


@app.route('/')
def index():
    """
    Company homepage
    """
    return f"""
    <html>
    <head>
        <title>{COMPANY_NAME} - TBN Demo</title>
        <style>
            body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .endpoint {{ background: #3498db; color: white; padding: 10px; border-radius: 3px; margin: 10px 0; }}
            code {{ background: #34495e; color: #ecf0f1; padding: 2px 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>🏢 {COMPANY_NAME}</h1>
        <div class="info">
            <h2>TBN-Protected Company Data</h2>
            <p>This company uses <strong>TBN infrastructure</strong> to verify AI bots.</p>
            <p>Only bots with valid TBN certificates can access our data.</p>
        </div>
        
        <h3>📄 TBN Configuration</h3>
        <div class="endpoint">
            <a href="/tbn.json" style="color: white;">GET /tbn.json</a> - Our TBN policy
        </div>
        
        <h3>🔐 Protected Endpoints</h3>
        <div class="endpoint">
            POST /api/verify-bot - Verify a bot's TBN certificate
        </div>
        <div class="endpoint">
            GET /api/data - Get company data (TBN certificate required)
        </div>
        <div class="endpoint">
            GET /api/access-log - View access log
        </div>
        
        <h3>💡 How It Works</h3>
        <ol>
            <li>Bot presents TBN certificate (bot_id)</li>
            <li>We verify with TBN infrastructure</li>
            <li>If verified, we provide data</li>
            <li>All access is logged</li>
        </ol>
        
        <div class="info">
            <strong>Key Point:</strong> We don't build our own bot verification system.
            We just check with TBN - the infrastructure layer everyone uses.
        </div>
        
        <p><strong>Access Log:</strong> <a href="/api/access-log">View all bot access attempts</a></p>
    </body>
    </html>
    """


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print(f"🏢 {COMPANY_NAME} - Company Data Provider")
    print("=" * 70)
    print(f"\n📄 TBN Configuration:")
    print(json.dumps(TBN_CONFIG, indent=2))
    print(f"\n🔗 Endpoints:")
    print(f"   http://0.0.0.0:{PORT}/tbn.json")
    print(f"   http://0.0.0.0:{PORT}/api/verify-bot")
    print(f"   http://0.0.0.0:{PORT}/api/data")
    print(f"   http://0.0.0.0:{PORT}/api/access-log")
    print(f"\n🔍 Using TBN infrastructure at: {TBN_SERVER}")
    print(f"\n✅ Server starting on port {PORT}...")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
