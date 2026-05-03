"""
TBN API Routes
All endpoints return JSON.

POST /api/register          — register a new bot
POST /api/handshake         — trust handshake between two bots
POST /api/search            — natural language search
POST /api/verify            — verify a bot certificate
POST /api/platform/request  — simulate a platform access request
GET  /api/bots              — list all registered bots
GET  /api/activity          — recent activity feed
GET  /api/stats             — network stats
"""

from flask import Blueprint, request, jsonify
from tbn.bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot
from tbn.platform_integration import PlatformAdapter, BotRequest, AccessLevel
from tbn.certification import CertificationAuthority, CertLevel
from . import state

api = Blueprint("api", __name__)

BOT_CLASSES = {
    "SEARCH":    SearchBot,
    "VALIDATOR": ValidatorBot,
    "CONNECTOR": ConnectorBot,
    "MESSENGER": MessengerBot,
}

# Shared certification authority
ca = CertificationAuthority(state.bica)

# ── Sample data loaded into every SearchBot ──────────────────────────
SAMPLE_INDEX = [
    {"name": "Hardin AI Search",  "url": "https://hardin-ai-search.vercel.app", "category": "AI Search",    "audience": "small business"},
    {"name": "OpenAI API",        "url": "https://openai.com",                  "category": "AI Platform",  "audience": "developer"},
    {"name": "HuggingFace",       "url": "https://huggingface.co",              "category": "AI Models",    "audience": "developer"},
    {"name": "Notion AI",         "url": "https://notion.so",                   "category": "Productivity", "audience": "small business"},
    {"name": "GitHub Copilot",    "url": "https://github.com/features/copilot", "category": "Code AI",      "audience": "developer"},
    {"name": "Anthropic Claude",  "url": "https://anthropic.com",               "category": "AI Platform",  "audience": "enterprise"},
    {"name": "Jasper AI",         "url": "https://jasper.ai",                   "category": "Content AI",   "audience": "small business"},
    {"name": "Midjourney",        "url": "https://midjourney.com",              "category": "Image AI",     "audience": "developer"},
]


# ── POST /api/register ───────────────────────────────────────────────
@api.route("/register", methods=["POST"])
def register():
    """Register a new bot on the TBN network."""
    body = request.get_json() or {}
    name = body.get("name", "").strip()
    bot_type = body.get("type", "SEARCH").upper()

    if not name:
        return jsonify({"error": "name is required"}), 400
    if bot_type not in BOT_CLASSES:
        return jsonify({"error": f"type must be one of {list(BOT_CLASSES)}"}), 400

    cls = BOT_CLASSES[bot_type]
    bot = cls(name=name, bica=state.bica, ca=ca)

    # Load sample data into search bots
    if isinstance(bot, SearchBot):
        for item in SAMPLE_INDEX:
            bot.add_to_index(item)

    # Auto-certify at STANDARD level on registration
    cert = ca.certify(identity=bot.identity, level=CertLevel.STANDARD)

    state.bots[bot.bot_id] = bot
    state.log_activity("register", f"New {bot_type} bot registered: {name} 🔵 STANDARD", {"bot_id": bot.bot_id})

    return jsonify({
        "bot_id": bot.bot_id,
        "name": name,
        "type": bot_type,
        "cert_level": cert.level.value,
        "certificate": bot.identity.to_certificate(),
        "message": f"Bot '{name}' registered and certified as STANDARD",
    }), 201


# ── POST /api/handshake ──────────────────────────────────────────────
@api.route("/handshake", methods=["POST"])
def handshake():
    """Perform a trust handshake between two registered bots."""
    body = request.get_json() or {}
    initiator_id = body.get("initiator_id", "")
    responder_id = body.get("responder_id", "")

    initiator = state.bots.get(initiator_id)
    responder = state.bots.get(responder_id)

    if not initiator:
        return jsonify({"error": f"Bot not found: {initiator_id}"}), 404
    if not responder:
        return jsonify({"error": f"Bot not found: {responder_id}"}), 404

    try:
        channel = initiator.connect(responder)
        # Get cert levels for display
        cert_i = ca.get_cert(initiator_id)
        cert_r = ca.get_cert(responder_id)
        level_i = cert_i.level.value if cert_i else "NONE"
        level_r = cert_r.level.value if cert_r else "NONE"
        badges  = {"COMMUNITY":"🟢","STANDARD":"🔵","RESTRICTED":"🟡","NONE":"⚪"}

        state.log_activity(
            "handshake",
            f"Trust established: {initiator.name} {badges.get(level_i,'?')} ↔ {responder.name} {badges.get(level_r,'?')}",
            {"initiator": initiator_id, "responder": responder_id},
        )
        return jsonify({
            "status": "TRUST_ESTABLISHED",
            "initiator": {"id": initiator_id, "name": initiator.name, "cert_level": level_i},
            "responder": {"id": responder_id, "name": responder.name, "cert_level": level_r},
            "channel": str(channel),
            "compatibility": f"{level_i} ↔ {level_r} — compatible",
            "message": f"Trust channel established between {initiator.name} and {responder.name}",
        })
    except Exception as e:
        state.log_activity("error", f"Handshake failed: {str(e)}")
        return jsonify({"error": str(e), "status": "BLOCKED"}), 400


# ── POST /api/search ─────────────────────────────────────────────────
@api.route("/search", methods=["POST"])
def search():
    """Run a natural language search through a registered SearchBot."""
    body = request.get_json() or {}
    bot_id = body.get("bot_id", "")
    query  = body.get("query", "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    # Find a search bot — use specified one or first available
    bot = state.bots.get(bot_id)
    if not bot:
        bot = next((b for b in state.bots.values() if isinstance(b, SearchBot)), None)
    if not bot or not isinstance(bot, SearchBot):
        return jsonify({"error": "No SearchBot registered. POST /api/register first."}), 404

    # Check seeded cache
    cached = state.seeded_net.lookup(query)
    if cached:
        state.log_activity("search", f"Cache hit: \"{query}\"", {"results": len(cached), "source": "cache"})
        return jsonify({
            "source": "cache",
            "query": query,
            "bot_id": bot.bot_id,
            "bot_name": bot.name,
            "results": cached,
            "count": len(cached),
        })

    # Compile and search
    msg = state.compiler.compile(query, sender_id=bot.bot_id, identity=bot.identity)
    result = bot.handle_request(msg)

    # Seed results
    if result["RESULTS"]:
        state.seeded_net.seed(query, result["RESULTS"], bot.bot_id)

    state.log_activity(
        "search",
        f"Search: \"{query}\" → {result['RESULT_COUNT']} results",
        {"results": result["RESULT_COUNT"], "source": "search", "intent": msg.payload["INTENT"]},
    )

    return jsonify({
        "source": "search",
        "query": query,
        "bot_id": bot.bot_id,
        "bot_name": bot.name,
        "compiled": {
            "intent":      msg.payload["INTENT"],
            "trust_level": msg.payload["TRUST_LEVEL"],
            "data_type":   msg.payload["DATA_TYPE"],
            "filters":     msg.payload.get("FILTERS", {}),
            "priority":    msg.payload["PRIORITY"],
        },
        "results": result["RESULTS"],
        "count": result["RESULT_COUNT"],
        "status": result["STATUS"],
    })


# ── POST /api/verify ─────────────────────────────────────────────────
@api.route("/verify", methods=["POST"])
def verify():
    """Verify whether a bot ID is certified in the BICA registry."""
    body = request.get_json() or {}
    bot_id = body.get("bot_id", "")

    certified = state.public_reg.is_certified(bot_id)
    cert = state.public_reg.lookup(bot_id)

    state.log_activity(
        "verify",
        f"Verification: {bot_id[:20]}... → {'✅ certified' if certified else '❌ not found'}",
        {"bot_id": bot_id, "certified": certified},
    )

    return jsonify({
        "bot_id": bot_id,
        "certified": certified,
        "certificate": cert,
    })


# ── POST /api/platform/request ───────────────────────────────────────
@api.route("/platform/request", methods=["POST"])
def platform_request():
    """Simulate a bot requesting access to an external platform."""
    body = request.get_json() or {}
    bot_id   = body.get("bot_id", "")
    platform = body.get("platform", "GitHub")
    resource = body.get("resource", "/repos/tbn-protocol")
    intent   = body.get("intent", "SEARCH")

    bot = state.bots.get(bot_id)
    cert = bot.identity.to_certificate() if bot else {"bot_id": bot_id, "name": "Unknown"}

    adapter = PlatformAdapter(name=platform, bica=state.bica)
    req = BotRequest(
        bot_id=bot_id,
        certificate=cert,
        intent=intent,
        resource=resource,
    )
    granted, level = adapter.verify_request(req)

    # Log to shared audit log
    state.audit_log.log(req, granted, f"Platform: {platform} | Level: {level}")
    state.log_activity(
        "verify",
        f"Platform access {'granted' if granted else 'denied'}: {bot_id[:16]}... → {platform}{resource}",
        {"granted": granted, "platform": platform, "level": level},
    )

    return jsonify({
        "granted": granted,
        "access_level": level,
        "platform": platform,
        "resource": resource,
        "bot_id": bot_id,
        "certified": state.public_reg.is_certified(bot_id),
    })


# ── GET /api/bots ────────────────────────────────────────────────────
@api.route("/bots", methods=["GET"])
def list_bots():
    """List all registered bots."""
    return jsonify({
        "bots": [
            {
                "bot_id": b.bot_id,
                "name": b.name,
                "type": getattr(b, "BOT_TYPE", "BOT"),
                "channels": len(b._channels),
                "cert_level": ca.get_level(b.bot_id).value,
            }
            for b in state.bots.values()
        ],
        "total": len(state.bots),
        "registry_total": len(state.bica.list_bots()),
    })


# ── GET /api/activity ────────────────────────────────────────────────
@api.route("/activity", methods=["GET"])
def activity():
    """Return recent activity feed."""
    return jsonify({"activity": state.activity})


# ── GET /api/stats ───────────────────────────────────────────────────
@api.route("/stats", methods=["GET"])
def stats():
    """Return network stats."""
    cert_stats = ca.stats()
    return jsonify({
        "registered_bots": len(state.bots),
        "certified_bots": len(state.bica.list_bots()),
        "cache": state.seeded_net.stats(),
        "clones": state.clone_mgr.stats(),
        "audit": state.audit_log.stats(),
        "certification": cert_stats,
    })


# ── POST /api/certify ────────────────────────────────────────────────
@api.route("/certify", methods=["POST"])
def certify():
    """
    Upgrade a bot's certification level.
    COMMUNITY requires ethical_declaration=true and a purpose.
    """
    body    = request.get_json() or {}
    bot_id  = body.get("bot_id", "")
    level   = body.get("level", "STANDARD").upper()
    purpose = body.get("purpose", "")
    ethical = body.get("ethical_declaration", False)

    bot = state.bots.get(bot_id)
    if not bot:
        return jsonify({"error": f"Bot not found: {bot_id}"}), 404

    try:
        cert_level = CertLevel(level)
    except ValueError:
        return jsonify({"error": f"Invalid level. Use: COMMUNITY, STANDARD, RESTRICTED"}), 400

    try:
        cert = ca.certify(
            identity=bot.identity,
            level=cert_level,
            purpose=purpose,
            ethical_declaration=ethical,
        )
        badges = {"COMMUNITY":"🟢","STANDARD":"🔵","RESTRICTED":"🟡"}
        badge  = badges.get(level, "?")

        state.log_activity(
            "register",
            f"{badge} {bot.name} certified as {level}",
            {"bot_id": bot_id, "level": level},
        )
        return jsonify({
            "bot_id":     bot_id,
            "name":       bot.name,
            "cert_level": cert.level.value,
            "purpose":    cert.purpose,
            "issued_at":  cert.issued_at,
            "permissions": {
                k: v for k, v in cert.permissions.items()
                if k != "trust_compatible_with"
            },
            "message": f"{bot.name} certified as {level} {badge}",
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── POST /api/violation ──────────────────────────────────────────────
@api.route("/violation", methods=["POST"])
def report_violation():
    """Report a violation against a bot (3 = auto-revoke)."""
    body      = request.get_json() or {}
    bot_id    = body.get("bot_id", "")
    violation = body.get("violation", "Unspecified violation")

    bot = state.bots.get(bot_id)
    if not bot:
        return jsonify({"error": f"Bot not found: {bot_id}"}), 404

    ca.report_violation(bot_id, violation)
    cert = ca.get_cert(bot_id)

    state.log_activity(
        "error",
        f"⚠️ Violation reported: {bot.name} — {violation}",
        {"bot_id": bot_id, "violations": cert.violation_count if cert else 0},
    )

    return jsonify({
        "bot_id":          bot_id,
        "name":            bot.name,
        "violation":       violation,
        "violation_count": cert.violation_count if cert else 0,
        "cert_valid":      cert.valid if cert else False,
        "revoked":         not cert.valid if cert else True,
        "message": (
            f"Auto-revoked after {cert.violation_count} violations"
            if cert and not cert.valid
            else f"Violation #{cert.violation_count if cert else '?'} recorded"
        ),
    })


# ── POST /api/encrypt_demo ───────────────────────────────────────────
@api.route("/encrypt_demo", methods=["POST"])
def encrypt_demo():
    """
    Demonstrate BL v2 encryption end-to-end.
    Encrypts a message from bot A to bot B and shows before/after.
    """
    body       = request.get_json() or {}
    sender_id  = body.get("sender_id", "")
    receiver_id= body.get("receiver_id", "")
    query      = body.get("query", "Find trusted AI tools")

    sender   = state.bots.get(sender_id)
    receiver = state.bots.get(receiver_id)

    if not sender:
        return jsonify({"error": f"Sender not found: {sender_id}"}), 404
    if not receiver:
        return jsonify({"error": f"Receiver not found: {receiver_id}"}), 404

    # Compile plaintext message
    msg = state.compiler.compile(
        text=query,
        sender_id=sender.bot_id,
        identity=sender.identity,
        receiver_id=receiver.bot_id,
    )

    plaintext_payload = dict(msg.payload)

    # Encrypt with receiver's public key
    msg.encrypt(receiver.identity.public_key_pem())
    msg.sign(sender.identity)

    encrypted_dict = msg.to_dict()

    # Decrypt to prove it works
    decrypt_ok = msg.decrypt(receiver.identity._private_key)

    state.log_activity(
        "search",
        f"🔒 BL v2 encrypted: {sender.name} → {receiver.name}",
        {"encrypted": True, "query": query},
    )

    return jsonify({
        "query":            query,
        "sender":           sender.name,
        "receiver":         receiver.name,
        "bl_version":       "2.0",
        "plaintext_payload": plaintext_payload,
        "encrypted": {
            "encrypted":    True,
            "payload_hash": encrypted_dict["payload_hash"],
            "session_key":  encrypted_dict["session_key"][:40] + "... (RSA-encrypted AES key)",
            "payload":      str(encrypted_dict["payload"])[:80] + "... (AES-256-GCM ciphertext)",
            "signature":    encrypted_dict["signature"][:40] + "...",
        },
        "decryption": {
            "success":          decrypt_ok,
            "recovered_intent": msg.payload.get("INTENT"),
            "recovered_query":  msg.payload.get("QUERY"),
        },
    })
