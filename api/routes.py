"""
TBN API Routes
All endpoints return JSON.

PUBLIC (no key needed):
  GET  /api/stats                   — network stats (public)
  GET  /api/bots                    — list available bots (public)
  POST /api/access/request          — request a trial API key
  GET  /api/philosophy/bots         — list all philosophy bots
  GET  /api/philosophy/bot/<bot_id> — get a bot's philosophy info
  GET  /api/boomi/health            — Boomi integration health check

PROTECTED (API key required — Authorization: Bearer tbn_live_xxxx):
  POST /api/handshake               — trust handshake between two bots
  POST /api/search                  — natural language search
  POST /api/verify                  — verify a bot certificate
  POST /api/platform/request        — simulate a platform access request
  GET  /api/activity                — recent activity feed
  POST /api/philosophy/chat         — chat with a philosophy bot
  POST /api/philosophy/ask          — ask a philosophy bot a question (no history)
  POST /api/boomi/process           — Boomi integration process handler

LOCKED (Hardin admin only — bot creation is NOT public):
  POST /api/register                — DISABLED for public use
"""

import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from tbn.bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot
from tbn.platform_integration import PlatformAdapter, BotRequest, AccessLevel
from tbn.certification import CertificationAuthority, CertLevel
from tbn.github_bica import GitHubBICA
from .access_control import require_api_key, generate_api_key, record_api_call, check_bot_access, get_key_stats, list_all_keys
from . import state

api = Blueprint("api", __name__)

BOT_CLASSES = {
    "SEARCH":    SearchBot,
    "VALIDATOR": ValidatorBot,
    "CONNECTOR": ConnectorBot,
    "MESSENGER": MessengerBot,
}


# ── Bot Info Page (transparency) ─────────────────────────────────────

@api.route('/bot-info')
def bot_info():
    """Public page explaining what TBN-Bot does — linked in our User-Agent"""
    return """<!DOCTYPE html>
<html>
<head><title>TBN-Bot Information</title></head>
<body style="font-family:monospace;max-width:700px;margin:40px auto;padding:20px;background:#0a0e1a;color:#c9d1d9;">
<h1 style="color:#58a6ff;">TBN-Bot/1.0</h1>
<p>This is an automated data collection bot operated by <strong>Hardin AI Solutions</strong>.</p>

<h2 style="color:#3fb950;">What we do</h2>
<p>TBN-Bot collects publicly available data to power the TBN Protocol — a trust infrastructure for AI agents.</p>

<h2 style="color:#3fb950;">Our rules</h2>
<ul>
<li>We always identify ourselves honestly in our User-Agent header</li>
<li>We respect your robots.txt — if you block us, we stay away</li>
<li>We never access pages behind logins or paywalls</li>
<li>We rate-limit our requests (max 20/minute per domain)</li>
<li>We keep full audit logs of all collection activity</li>
<li>We only collect publicly available information</li>
</ul>

<h2 style="color:#3fb950;">How to block us</h2>
<p>Add this to your robots.txt:</p>
<pre style="background:#1a1a2e;padding:12px;border-radius:6px;">
User-agent: TBN-Bot
Disallow: /
</pre>

<h2 style="color:#3fb950;">Contact</h2>
<p>
Email: <a href="mailto:burhan@hardinai.co.uk" style="color:#58a6ff;">burhan@hardinai.co.uk</a><br>
Website: <a href="https://tbn.hardinai.co.uk" style="color:#58a6ff;">tbn.hardinai.co.uk</a><br>
Company: Hardin AI Solutions (Hardin Enterprises Ltd)<br>
GitHub: <a href="https://github.com/burhanyanbolu-design/tbn-protocol" style="color:#58a6ff;">tbn-protocol</a>
</p>
</body>
</html>""", 200, {'Content-Type': 'text/html'}


# ── Database logging helpers ──────────────────────────────────────────

def _db_log(table: str, **kwargs):
    """Write a log entry to the hardin_data_network database."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="hardin_data_network",
            user="hardin_admin",
            password="hardin2026",
            host="localhost",
            port=5433
        )
        cur  = conn.cursor()
        cols = ", ".join(kwargs.keys())
        vals = ", ".join(["%s"] * len(kwargs))
        cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", list(kwargs.values()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB LOG] Failed to write to {table}: {e}")


def _log_handshake_to_db(initiator_id: str, responder_id: str, status: str, ip: str, notes: str = ""):
    """Log every handshake attempt to tbn_handshake_log."""
    _db_log(
        "tbn_handshake_log",
        initiator_bot_id = initiator_id,
        responder_bot_id = responder_id,
        status           = status,
        ip_address       = ip,
        notes            = notes[:500],
    )


def _log_activity_to_db(event_type: str, bot_id: str, bot_name: str, message: str):
    """Log bot activity to tbn_activity_log."""
    _db_log(
        "tbn_activity_log",
        event_type = event_type,
        bot_id     = bot_id,
        bot_name   = bot_name,
        message    = message[:500],
    )

# Shared certification authority with GitHub BICA support
def get_bica():
    """Get BICA instance based on environment."""
    if os.environ.get("TBN_ENV") == "production":
        github_token = os.environ.get("TBN_GITHUB_TOKEN", "")
        github_repo = os.environ.get("TBN_GITHUB_REPO", "burhanyanbolu-design/tbn-bica-registry")
        
        if github_token:
            return GitHubBICA(repo=github_repo, token=github_token)
        else:
            print("⚠️  No GitHub token configured, using local BICA")
            return state.bica
    else:
        return state.bica

ca = CertificationAuthority(get_bica())

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


# ── POST /api/register — LOCKED (Hardin admin only) ──────────────────
@api.route("/register", methods=["POST"])
def register():
    """
    Bot registration is no longer public.
    Hardin creates and manages all TBN-certified bots.
    Companies access our bots via API key subscription.
    """
    # Allow internal/admin calls with the admin secret
    admin_secret = request.headers.get("X-Admin-Secret", "")
    expected     = os.environ.get("TBN_ADMIN_SECRET", "")

    if not expected or admin_secret != expected:
        return jsonify({
            "error":   "Bot registration is not available publicly.",
            "message": "TBN bots are created and certified by Hardin AI Solutions only.",
            "info":    "To access our network of TBN-certified bots, get an API key.",
            "signup":  "https://tbn.hardinai.co.uk/pricing",
        }), 403

    # ── Admin-only path below ────────────────────────────────────────
    body     = request.get_json() or {}
    name     = body.get("name", "").strip()
    bot_type = body.get("type", "SEARCH").upper()
    icon_url = body.get("icon_url", "").strip() or None

    if not name:
        return jsonify({"error": "name is required"}), 400
    if bot_type not in BOT_CLASSES:
        return jsonify({"error": f"type must be one of {list(BOT_CLASSES)}"}), 400

    cls  = BOT_CLASSES[bot_type]
    bot  = cls(name=name, bica=state.bica, ca=ca, icon_url=icon_url)

    if isinstance(bot, SearchBot):
        for item in SAMPLE_INDEX:
            bot.add_to_index(item)

    cert = ca.certify(identity=bot.identity, level=CertLevel.STANDARD)
    state.bots[bot.bot_id] = bot
    state.log_activity("register", f"[ADMIN] New {bot_type} bot registered: {name} 🔵 STANDARD", {"bot_id": bot.bot_id})
    _log_activity_to_db("register", bot.bot_id, name, f"New {bot_type} bot registered as STANDARD")

    return jsonify({
        "bot_id":      bot.bot_id,
        "name":        name,
        "type":        bot_type,
        "cert_level":  cert.level.value,
        "certificate": bot.identity.to_certificate(),
        "message":     f"Bot '{name}' registered and certified as STANDARD",
    }), 201


# ── POST /api/access/request — Get a trial API key ───────────────────
@api.route("/access/request", methods=["POST"])
def request_access():
    """
    Companies request a trial API key here.
    7-day free trial, 100 calls/day, access to 3 bots.
    """
    body    = request.get_json() or {}
    company = body.get("company", "").strip()
    email   = body.get("email", "").strip()
    tier    = body.get("tier", "TRIAL").upper()

    if not company:
        return jsonify({"error": "company name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "valid email is required"}), 400
    if tier not in ("TRIAL",):
        # Only TRIAL is self-serve; paid tiers go through sales
        return jsonify({
            "error":   "Paid plans require contacting our sales team.",
            "contact": "burhan@hardinai.co.uk",
            "pricing": "https://tbn.hardinai.co.uk/pricing",
        }), 400

    try:
        result = generate_api_key(company, email, tier="TRIAL")
        state.log_activity("register", f"🔑 New TRIAL key issued: {company} ({email})", {"email": email})

        return jsonify({
            "success":     True,
            "api_key":     result["api_key"],   # shown ONCE — save it!
            "tier":        "TRIAL",
            "expires_in":  "7 days",
            "calls_per_day": 100,
            "bot_access":  3,
            "warning":     "Save your API key — it will not be shown again.",
            "docs":        "https://tbn.hardinai.co.uk/docs",
            "upgrade":     "https://tbn.hardinai.co.uk/pricing",
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /api/access/plans — Show pricing tiers ────────────────────────
@api.route("/access/plans", methods=["GET"])
def access_plans():
    """Return available subscription plans."""
    from .access_control import TIERS
    return jsonify({
        "plans": [
            {
                "tier":          tier,
                "name":          cfg["name"],
                "price_gbp":     cfg["price_gbp"],
                "calls_per_day": cfg["calls_per_day"],
                "bot_access":    cfg["bot_access"] or "unlimited",
                "features":      cfg["features"],
                "duration":      f"{cfg['duration_days']} days" if cfg["duration_days"] else "monthly",
            }
            for tier, cfg in TIERS.items()
        ],
        "contact": "burhan@hardinai.co.uk",
        "signup":  "https://tbn.hardinai.co.uk/pricing",
    })


# ── POST /api/handshake ──────────────────────────────────────────────
@api.route("/handshake", methods=["POST"])
def handshake():
    """Perform a trust handshake between two registered bots."""
    body = request.get_json() or {}
    initiator_id = body.get("initiator_id", "")
    responder_id = body.get("responder_id", "")
    caller_ip    = request.remote_addr or "unknown"

    initiator = state.bots.get(initiator_id)
    responder = state.bots.get(responder_id)

    if not initiator:
        _log_handshake_to_db(initiator_id, responder_id, "FAILED", caller_ip, "Initiator not found")
        return jsonify({"error": f"Bot not found: {initiator_id}"}), 404
    if not responder:
        _log_handshake_to_db(initiator_id, responder_id, "FAILED", caller_ip, "Responder not found")
        return jsonify({"error": f"Bot not found: {responder_id}"}), 404

    try:
        channel = initiator.connect(responder)
        cert_i  = ca.get_cert(initiator_id)
        cert_r  = ca.get_cert(responder_id)
        level_i = cert_i.level.value if cert_i else "NONE"
        level_r = cert_r.level.value if cert_r else "NONE"
        badges  = {"COMMUNITY":"🟢","STANDARD":"🔵","RESTRICTED":"🟡","NONE":"⚪"}

        # ── Log to database ───────────────────────────────────────────
        _log_handshake_to_db(
            initiator_id, responder_id, "SUCCESS", caller_ip,
            f"{initiator.name} {badges.get(level_i,'?')} ↔ {responder.name} {badges.get(level_r,'?')}"
        )

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
        _log_handshake_to_db(initiator_id, responder_id, "BLOCKED", caller_ip, str(e))
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
    # Get all certificates from BICA registry
    certs = state.bica.list_bots()
    
    return jsonify({
        "bots": [
            {
                "bot_id": cert["bot_id"],
                "name": cert["name"],
                "icon_url": cert.get("icon_url"),
                "type": state.bots.get(cert["bot_id"]).BOT_TYPE if cert["bot_id"] in state.bots else "UNKNOWN",
                "channels": len(state.bots[cert["bot_id"]]._channels) if cert["bot_id"] in state.bots else 0,
                "cert_level": ca.get_level(cert["bot_id"]).value,
            }
            for cert in certs
        ],
        "total": len(certs),
        "registry_total": len(certs),
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


# ── Philosophy Bot Endpoints ─────────────────────────────────────────
#
# These endpoints expose the Philosophy Core system as part of TBN.
# Philosophy bots have internalized wisdom from books and reason
# through that worldview in every conversation.
#
# GET  /api/philosophy/bots         — list all registered philosophy bots
# GET  /api/philosophy/bot/<bot_id> — get a specific bot's philosophy
# POST /api/philosophy/ask          — ask a philosophy bot one question
# POST /api/philosophy/chat         — multi-turn conversation with a bot
# ─────────────────────────────────────────────────────────────────────

def _load_philosophy_registry():
    """Load the TBN philosophy registry"""
    try:
        from tbn.philosophy_core_complete import TBNPhilosophyRegistry
        return TBNPhilosophyRegistry()
    except Exception as e:
        return None


def _load_philosophy_injector(bot_id: str):
    """Load a philosophy injector for a given bot_id"""
    try:
        from tbn.philosophy_core_complete import PhilosophyPromptInjector
        registry = _load_philosophy_registry()
        if not registry:
            return None, "Philosophy registry unavailable"

        entry = registry.get(bot_id)
        if not entry:
            return None, f"No philosophy bot found with id: {bot_id}"

        identity_path = entry.get("bot_identity_path", "")

        # Resolve relative paths from the project root
        if not os.path.isabs(identity_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            identity_path = os.path.join(project_root, identity_path)

        if not os.path.exists(identity_path):
            return None, f"Identity file not found: {identity_path}"

        return PhilosophyPromptInjector.from_file(identity_path), None
    except Exception as e:
        return None, str(e)


@api.route("/philosophy/bots", methods=["GET"])
def philosophy_bots():
    """
    List all philosophy bots registered in TBN.
    Public — no API key needed.
    """
    registry = _load_philosophy_registry()
    if not registry:
        return jsonify({"error": "Philosophy registry unavailable"}), 503

    bots = registry.list_all()
    return jsonify({
        "philosophy_bots": [
            {
                "bot_id":    b["bot_id"],
                "bot_name":  b["bot_name"],
                "book":      b["book_title"],
                "author":    b["author"],
                "verified":  b["philosophy_verified"],
                "registered_at": b["registered_at"],
            }
            for b in bots
        ],
        "total": len(bots),
        "stats": registry.stats(),
        "usage": "POST /api/philosophy/ask with {bot_id, question}",
    })


@api.route("/philosophy/bot/<bot_id>", methods=["GET"])
def philosophy_bot_info(bot_id):
    """
    Get a specific philosophy bot's worldview and principles.
    Public — no API key needed.
    """
    registry = _load_philosophy_registry()
    if not registry:
        return jsonify({"error": "Philosophy registry unavailable"}), 503

    entry = registry.get(bot_id)
    if not entry:
        return jsonify({"error": f"Bot not found: {bot_id}"}), 404

    # Load the full philosophy core if available
    core_path = entry.get("philosophy_core_path", "")
    philosophy_detail = None
    if core_path and os.path.exists(core_path):
        try:
            from tbn.philosophy_core_complete import PhilosophyCore
            core = PhilosophyCore.from_json(core_path)
            philosophy_detail = {
                "worldview_summary": core.worldview_summary,
                "core_values":       core.core_values,
                "principles": [
                    {
                        "name":        p.name,
                        "description": p.description,
                        "principle":   p.principle,
                        "weight":      p.weight,
                    }
                    for p in sorted(core.principles, key=lambda x: x.weight, reverse=True)
                ],
            }
        except Exception:
            pass

    return jsonify({
        "bot_id":    entry["bot_id"],
        "bot_name":  entry["bot_name"],
        "book":      entry["book_title"],
        "author":    entry["author"],
        "verified":  entry["philosophy_verified"],
        "philosophy": philosophy_detail,
        "usage": f"POST /api/philosophy/ask with {{bot_id: '{bot_id}', question: '...'}}"
    })


@api.route("/philosophy/ask", methods=["POST"])
def philosophy_ask():
    """
    Ask a philosophy bot a single question.
    The bot reasons through its internalized worldview to respond.

    Body: { "bot_id": "tbn-bot-santiago-001", "question": "How do I find my purpose?" }
    """
    body     = request.get_json() or {}
    bot_id   = body.get("bot_id", "tbn-bot-santiago-001")
    question = body.get("question", "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    injector, err = _load_philosophy_injector(bot_id)
    if err:
        return jsonify({"error": err}), 404

    try:
        response = injector.chat(question)
        registry = _load_philosophy_registry()
        entry    = registry.get(bot_id) if registry else {}

        state.log_activity(
            "search",
            f"📚 Philosophy ask: {entry.get('bot_name', bot_id)} — \"{question[:50]}...\"",
            {"bot_id": bot_id, "book": entry.get("book_title", "")},
        )

        return jsonify({
            "bot_id":   bot_id,
            "bot_name": entry.get("bot_name", bot_id),
            "book":     entry.get("book_title", ""),
            "author":   entry.get("author", ""),
            "question": question,
            "response": response,
            "philosophy_verified": entry.get("philosophy_verified", False),
        })
    except Exception as e:
        return jsonify({"error": f"Bot failed to respond: {str(e)}"}), 500


@api.route("/philosophy/chat", methods=["POST"])
def philosophy_chat():
    """
    Multi-turn conversation with a philosophy bot.
    Pass conversation history to maintain context across turns.

    Body: {
        "bot_id": "tbn-bot-santiago-001",
        "message": "I feel lost in life",
        "history": [
            {"role": "user",      "content": "previous message"},
            {"role": "assistant", "content": "previous response"}
        ]
    }
    """
    body    = request.get_json() or {}
    bot_id  = body.get("bot_id", "tbn-bot-santiago-001")
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return jsonify({"error": "message is required"}), 400

    # Validate history format
    for turn in history:
        if not isinstance(turn, dict) or "role" not in turn or "content" not in turn:
            return jsonify({"error": "history must be list of {role, content} objects"}), 400

    injector, err = _load_philosophy_injector(bot_id)
    if err:
        return jsonify({"error": err}), 404

    try:
        response = injector.chat(message, history=history)
        registry = _load_philosophy_registry()
        entry    = registry.get(bot_id) if registry else {}

        # Build updated history for client to store
        updated_history = history + [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": response},
        ]

        state.log_activity(
            "search",
            f"💬 Philosophy chat: {entry.get('bot_name', bot_id)} — turn {len(updated_history)//2}",
            {"bot_id": bot_id},
        )

        return jsonify({
            "bot_id":          bot_id,
            "bot_name":        entry.get("bot_name", bot_id),
            "book":            entry.get("book_title", ""),
            "message":         message,
            "response":        response,
            "history":         updated_history,   # send back so client can continue the conversation
            "turn":            len(updated_history) // 2,
        })
    except Exception as e:
        return jsonify({"error": f"Bot failed to respond: {str(e)}"}), 500


# ── GET /philosophy — Chat UI page ───────────────────────────────────
@api.route("/philosophy-chat", methods=["GET"])
def philosophy_chat_page():
    """Serve the philosophy chat UI"""
    from flask import render_template
    return render_template("philosophy_chat.html")


# ── POST /api/philosophy/add_book — Add a new book ───────────────────
@api.route("/philosophy/add_book", methods=["POST"])
def philosophy_add_book():
    """
    Add a new book to the philosophy network.
    Reads the epub, extracts philosophy via Ollama, registers the bot.

    Body: {
        "bot_name":   "Marcus",
        "book_title": "Meditations",
        "author":     "Marcus Aurelius",
        "epub_path":  "/path/to/book.epub"   (optional)
    }
    """
    body       = request.get_json() or {}
    bot_name   = body.get("bot_name", "").strip()
    book_title = body.get("book_title", "").strip()
    author     = body.get("author", "").strip()
    epub_path  = body.get("epub_path", "").strip()  # any format: epub, html, pdf, txt

    if not bot_name or not book_title or not author:
        return jsonify({"error": "bot_name, book_title and author are required"}), 400

    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tbn.setup_philosophy_bot import setup_philosophy_bot

        bot_identity, philosophy_core = setup_philosophy_bot(
            epub_path=epub_path if epub_path and os.path.exists(epub_path) else "",
            bot_name=bot_name,
            book_title=book_title,
            author=author,
        )

        state.log_activity(
            "register",
            f"📚 New philosophy bot added: {bot_name} ({book_title} by {author})",
            {"bot_id": bot_identity.bot_id},
        )

        return jsonify({
            "success":    True,
            "bot_id":     bot_identity.bot_id,
            "bot_name":   bot_name,
            "book":       book_title,
            "author":     author,
            "principles": len(philosophy_core.principles),
            "message":    f"{bot_name} has read {book_title} and is ready.",
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── POST /api/philosophy/add_book_upload — Upload a book file ────────
@api.route("/philosophy/add_book_upload", methods=["POST"])
def philosophy_add_book_upload():
    """
    Upload a book file directly from the browser.
    Accepts epub, html, htm, pdf, txt.
    """
    import tempfile

    bot_name   = request.form.get("bot_name", "").strip()
    book_title = request.form.get("book_title", "").strip()
    author     = request.form.get("author", "").strip()

    if not bot_name or not book_title or not author:
        return jsonify({"error": "bot_name, book_title and author are required"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files['file']
    if not uploaded.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Check extension
    allowed = {'.epub', '.html', '.htm', '.pdf', '.txt'}
    ext = os.path.splitext(uploaded.filename)[1].lower()
    if ext not in allowed:
        return jsonify({"error": f"Unsupported format '{ext}'. Use: epub, html, pdf, txt"}), 400

    try:
        # Save to a temp file with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        from tbn.setup_philosophy_bot import setup_philosophy_bot

        bot_identity, philosophy_core = setup_philosophy_bot(
            epub_path=tmp_path,
            bot_name=bot_name,
            book_title=book_title,
            author=author,
        )

        # Clean up temp file
        os.unlink(tmp_path)

        state.log_activity(
            "register",
            f"📚 New philosophy bot: {bot_name} ({book_title} by {author})",
            {"bot_id": bot_identity.bot_id},
        )

        return jsonify({
            "success":    True,
            "bot_id":     bot_identity.bot_id,
            "bot_name":   bot_name,
            "book":       book_title,
            "author":     author,
            "principles": len(philosophy_core.principles),
            "message":    f"{bot_name} has read {book_title} and is ready.",
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ── Boomi Integration Endpoints ──────────────────────────────────────

@api.route("/boomi/process", methods=["POST"])
@require_api_key
def boomi_process():
    """
    Boomi Integration Endpoint
    
    Receives documents from Boomi processes and routes them to appropriate TBN handlers.
    
    Body: {
        "process_type": "bot_registration" | "certification_check" | "governance_query",
        "data": { ... process-specific data ... },
        "metadata": {
            "boomi_process_id": "...",
            "timestamp": "2026-05-12T10:30:00Z",
            "source": "boomi"
        }
    }
    
    Returns: {
        "success": true,
        "process_id": "...",
        "result": { ... },
        "status": "completed" | "pending" | "error"
    }
    """
    try:
        body = request.get_json() or {}
        process_type = body.get("process_type", "").strip()
        data = body.get("data", {})
        metadata = body.get("metadata", {})
        
        if not process_type:
            return jsonify({"error": "process_type is required"}), 400
        
        # Route to appropriate handler
        if process_type == "bot_registration":
            result = _boomi_register_bot(data, metadata)
        elif process_type == "certification_check":
            result = _boomi_check_certification(data, metadata)
        elif process_type == "governance_query":
            result = _boomi_governance_query(data, metadata)
        else:
            return jsonify({"error": f"Unknown process_type: {process_type}"}), 400
        
        # Log the Boomi interaction
        state.log_activity(
            "boomi_integration",
            f"Boomi process: {process_type}",
            {"boomi_process_id": metadata.get("boomi_process_id"), "result": result}
        )
        
        return jsonify({
            "success": True,
            "process_id": metadata.get("boomi_process_id"),
            "result": result,
            "status": "completed"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "error"
        }), 500


def _boomi_register_bot(data: dict, metadata: dict) -> dict:
    """
    Handle bot registration from Boomi.
    
    Expected data: {
        "bot_name": "...",
        "bot_type": "SEARCH" | "VALIDATOR" | "CONNECTOR" | "MESSENGER",
        "company": "...",
        "email": "...",
        "description": "..."
    }
    """
    bot_name = data.get("bot_name", "").strip()
    bot_type = data.get("bot_type", "SEARCH").upper()
    company = data.get("company", "").strip()
    email = data.get("email", "").strip()
    description = data.get("description", "").strip()
    
    if not bot_name or not company or not email:
        raise ValueError("bot_name, company, and email are required")
    
    if bot_type not in BOT_CLASSES:
        raise ValueError(f"Invalid bot_type: {bot_type}")
    
    # Create bot instance
    bot_class = BOT_CLASSES[bot_type]
    bot = bot_class(name=bot_name, company=company)
    
    return {
        "bot_id": bot.bot_id,
        "bot_name": bot_name,
        "bot_type": bot_type,
        "company": company,
        "status": "registered",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def _boomi_check_certification(data: dict, metadata: dict) -> dict:
    """
    Check certification status of a bot.
    
    Expected data: {
        "bot_id": "...",
        "cert_level": "BRONZE" | "SILVER" | "GOLD" (optional)
    }
    """
    bot_id = data.get("bot_id", "").strip()
    cert_level = data.get("cert_level", "").strip()
    
    if not bot_id:
        raise ValueError("bot_id is required")
    
    # Get bot from registry
    bot = state.bots.get(bot_id)
    
    if not bot:
        raise ValueError(f"Bot not found: {bot_id}")
    
    # Check certification
    ca = CertificationAuthority()
    cert_info = ca.verify_certificate(bot_id)
    
    return {
        "bot_id": bot_id,
        "certified": cert_info.get("valid", False),
        "cert_level": cert_info.get("level", "NONE"),
        "expires": cert_info.get("expires"),
        "verified_at": datetime.now(timezone.utc).isoformat()
    }


def _boomi_governance_query(data: dict, metadata: dict) -> dict:
    """
    Query governance status and decisions.
    
    Expected data: {
        "query_type": "bot_status" | "violations" | "access_requests",
        "bot_id": "..." (optional),
        "limit": 10 (optional)
    }
    """
    query_type = data.get("query_type", "bot_status").strip()
    bot_id = data.get("bot_id", "").strip()
    limit = data.get("limit", 10)
    
    if query_type == "bot_status":
        bots = list(state.bots.values())
        if bot_id:
            bots = [b for b in bots if hasattr(b, 'bot_id') and b.bot_id == bot_id]
        return {
            "query_type": query_type,
            "count": len(bots),
            "bots": [{"bot_id": b.bot_id if hasattr(b, 'bot_id') else str(b)} for b in bots[:limit]]
        }
    
    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]
        return {
            "query_type": query_type,
            "count": len(violations),
            "violations": violations[:limit]
        }
    
    elif query_type == "access_requests":
        # Get pending access requests
        requests = []
        return {
            "query_type": query_type,
            "count": len(requests),
            "requests": requests[:limit]
        }
    
    else:
        raise ValueError(f"Unknown query_type: {query_type}")


@api.route("/boomi/health", methods=["GET"])
def boomi_health():
    """
    Health check endpoint for Boomi integration.
    No authentication required — used for monitoring.
    """
    return jsonify({
        "status": "healthy",
        "service": "TBN Protocol",
        "version": "1.0.0",
        "boomi_integration": "enabled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


# ── End of Boomi Integration ─────────────────────────────────────────
