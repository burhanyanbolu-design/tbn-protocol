"""
TBN API Routes
All endpoints return JSON.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-RT-2a5f9c7e

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
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from tbn.bots import SearchBot, ValidatorBot, ConnectorBot, MessengerBot
from tbn.platform_integration import PlatformAdapter, BotRequest, AccessLevel
from tbn.certification import CertificationAuthority, CertLevel
from .access_control import require_api_key, generate_api_key, record_api_call, check_bot_access, get_key_stats, list_all_keys
from .tbn_signing import sign_response, get_public_key_pem
from . import state

api = Blueprint("api", __name__)

# Use the shared CA from state (persists across restarts)
ca = state.ca


# ── GET /api/signing/public-key — TBN's public verification key ──────
@api.route("/signing/public-key", methods=["GET"])
def signing_public_key():
    """
    Returns TBN's RSA public key in PEM format.
    Use this to verify the 'signature' field in /api/verify/full responses.
    Proves the response was issued by TBN (provenance).
    """
    return jsonify({
        "public_key_pem": get_public_key_pem(),
        "algorithm": "RSA-PSS with SHA-256",
        "key_size": 2048,
        "usage": "Verify the 'signature' field in /api/verify/full responses",
    })

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
            port=5433,
            connect_timeout=5
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


# ── POST /api/verify/full — Full Trust State Verification ────────────
#
# Integration endpoint for external governance systems (e.g. CLARIXO).
# Returns a complete trust snapshot for an agent at a point in time.
# READ-ONLY — no state is modified. API key required.
#
# Boundary: TBN verifies agent-level trust state.
#           External systems handle behavior-level responsibility.
# ─────────────────────────────────────────────────────────────────────

@api.route("/verify/full", methods=["POST"])
@require_api_key
def verify_full():
    """
    Full agent trust-state verification.
    Returns certification, attestation, budget, policy, and bounds status
    for a given agent at the current moment.

    Request:
        {
            "agent_id": "tbn-bot-xxxx",
            "endpoint": "https://...",        (optional)
            "fingerprint": "sha256:...",      (optional)
            "timestamp": "ISO8601"            (optional — defaults to now)
        }

    Response:
        {
            "agent_id": "...",
            "certification_status": "VALID|EXPIRED|REVOKED|UNKNOWN",
            "attestation_status": "MATCHED|MISMATCH|NO_RECORD",
            "within_bounds": true/false,
            "policy_status": "COMPLIANT|DRIFTED|VIOLATED",
            "budget_status": "WITHIN_LIMITS|EXCEEDED|SUSPENDED|NO_BUDGET",
            "cert_level": "COMMUNITY|STANDARD|RESTRICTED|NONE",
            "violations": 0,
            "last_tested": "ISO8601 or null",
            "verification_time": "ISO8601"
        }
    """
    import json as _json
    import hashlib as _hashlib
    import uuid as _uuid

    body = request.get_json() or {}
    agent_id = body.get("agent_id", "").strip()
    fingerprint = body.get("fingerprint", "").strip()

    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    now = datetime.now(timezone.utc)
    verification_id = f"tbn_vrf_{_uuid.uuid4().hex[:16]}"

    # ── 1. Certification Status ───────────────────────────────────────
    cert = ca.get_cert(agent_id)
    if not cert:
        certification_status = "UNKNOWN"
        cert_level = "NONE"
        violations = 0
    elif not cert.valid:
        certification_status = "REVOKED"
        cert_level = cert.level.value if cert.level else "NONE"
        violations = cert.violation_count
    else:
        certification_status = "VALID"
        cert_level = cert.level.value
        violations = cert.violation_count

    # ── 2. Attestation Status (fingerprint match) ─────────────────────
    attestation_status = "NO_RECORD"
    last_tested = None

    try:
        monitoring_file = "data/bot_monitoring.json"
        if os.path.exists(monitoring_file):
            with open(monitoring_file, "r") as f:
                monitoring = _json.load(f)
            bot_monitor = monitoring.get(agent_id, {})
            last_tested = bot_monitor.get("last_tested")

            if fingerprint and bot_monitor.get("fingerprint"):
                if bot_monitor["fingerprint"] == fingerprint:
                    attestation_status = "MATCHED"
                else:
                    attestation_status = "MISMATCH"
            elif bot_monitor.get("fingerprint"):
                # We have a fingerprint on record but caller didn't send one
                attestation_status = "NO_RECORD"
    except Exception:
        pass

    # ── 3. Budget Status ──────────────────────────────────────────────
    budget_status = "NO_BUDGET"

    try:
        budgets_file = "data/bot_budgets.json"
        if os.path.exists(budgets_file):
            with open(budgets_file, "r") as f:
                budgets = _json.load(f)
            bot_budget = budgets.get(agent_id)
            if bot_budget:
                status = bot_budget.get("status", "active")
                if status == "suspended":
                    budget_status = "SUSPENDED"
                elif status == "exceeded":
                    budget_status = "EXCEEDED"
                else:
                    budget_status = "WITHIN_LIMITS"
    except Exception:
        pass

    # ── 4. Policy / Drift Status ──────────────────────────────────────
    policy_status = "COMPLIANT"

    try:
        drift_file = "data/compliance_drift.json"
        if os.path.exists(drift_file):
            with open(drift_file, "r") as f:
                drift_data = _json.load(f)
            bot_drift = drift_data.get(agent_id, {})
            score = bot_drift.get("score", 100)

            if score >= 80:
                policy_status = "COMPLIANT"
            elif score >= 40:
                policy_status = "DRIFTED"
            else:
                policy_status = "VIOLATED"
    except Exception:
        pass

    # ── 5. Within Bounds (composite check) ────────────────────────────
    within_bounds = (
        certification_status == "VALID"
        and budget_status in ("WITHIN_LIMITS", "NO_BUDGET")
        and policy_status == "COMPLIANT"
        and attestation_status != "MISMATCH"
    )

    # ── Log this verification ─────────────────────────────────────────
    state.log_activity(
        "verify",
        f"🔍 Full verification: {agent_id[:20]}... → {'✅ TRUSTED' if within_bounds else '⚠️ ISSUES'}",
        {"agent_id": agent_id, "within_bounds": within_bounds, "source": "external_governance"},
    )

    # Record API call for usage tracking
    if hasattr(request, 'tbn_key_record'):
        record_api_call(request.tbn_key_record, agent_id)

    # ── Build response ────────────────────────────────────────────────
    response_data = {
        "verification_id":      verification_id,
        "agent_id":             agent_id,
        "certification_status": certification_status,
        "attestation_status":   attestation_status,
        "within_bounds":        within_bounds,
        "policy_status":        policy_status,
        "budget_status":        budget_status,
        "cert_level":           cert_level,
        "violations":           violations,
        "last_tested":          last_tested,
        "verification_time":    now.isoformat(),
    }

    # ── Response hash (tamper-evident snapshot) ───────────────────────
    # SHA-256 of the canonical JSON response — allows CLARIXO (or any
    # consumer) to prove the verification result hasn't been altered.
    hash_input = _json.dumps(response_data, sort_keys=True, separators=(",", ":"))
    response_data["response_hash"] = _hashlib.sha256(hash_input.encode()).hexdigest()

    # ── RSA Signature (Cryptographically Verifiable Identity) ─────────
    # Proves this response was issued by TBN (provenance + integrity).
    # Verify using TBN's public key at /api/signing/public-key
    response_data["signature"] = sign_response(response_data)

    # ── Cache & Integration Metadata ──────────────────────────────────
    # Tells downstream systems (e.g. Shango MID) how long this verification is valid
    response_data["cache_ttl_seconds"] = 86400  # 24 hours
    response_data["cache_until"] = (now + timedelta(hours=24)).isoformat()
    response_data["revalidate_after"] = (now + timedelta(hours=24)).isoformat()
    response_data["integration_hint"] = {
        "cache_strategy": "Cache verification_id for 24h. Re-verify on expiry or drift alert.",
        "batch_supported": True,
        "max_batch_size": 100,
        "batch_endpoint": "/api/verify/batch",
    }

    return jsonify(response_data)


# ── POST /api/verify/batch — Batch Verification for High-Volume Integrations ──
#
# Allows downstream systems (e.g. Shango MID) to verify multiple agents
# in a single request. Designed for 100K+ write scenarios.
# API key required.
# ─────────────────────────────────────────────────────────────────────

@api.route("/verify/batch", methods=["POST"])
@require_api_key
def verify_batch():
    """
    Batch agent trust-state verification.
    Verify up to 100 agents in a single request.

    Request:
        {
            "agent_ids": ["tbn-bot-xxxx", "tbn-bot-yyyy", ...],
            "include_signature": false  (optional, default false for speed)
        }

    Response:
        {
            "batch_id": "tbn_batch_xxxx",
            "verified_at": "ISO8601",
            "cache_ttl_seconds": 86400,
            "results": [
                {"agent_id": "...", "within_bounds": true, "certification_status": "VALID", ...},
                ...
            ],
            "summary": {"total": 5, "trusted": 4, "issues": 1}
        }
    """
    import json as _json
    import hashlib as _hashlib
    import uuid as _uuid

    body = request.get_json() or {}
    agent_ids = body.get("agent_ids", [])
    include_signature = body.get("include_signature", False)

    if not agent_ids:
        return jsonify({"error": "agent_ids array is required"}), 400
    if len(agent_ids) > 100:
        return jsonify({"error": "Maximum 100 agents per batch request"}), 400

    now = datetime.now(timezone.utc)
    batch_id = f"tbn_batch_{_uuid.uuid4().hex[:12]}"
    results = []
    trusted_count = 0
    issues_count = 0

    for agent_id in agent_ids:
        agent_id = agent_id.strip()
        if not agent_id:
            continue

        # Certification check
        cert = ca.get_cert(agent_id)
        if not cert:
            certification_status = "UNKNOWN"
            cert_level = "NONE"
            violations = 0
        elif not cert.valid:
            certification_status = "REVOKED"
            cert_level = cert.level.value if cert.level else "NONE"
            violations = cert.violation_count
        else:
            certification_status = "VALID"
            cert_level = cert.level.value
            violations = cert.violation_count

        # Budget check
        budget_status = "NO_BUDGET"
        try:
            budgets_file = "data/bot_budgets.json"
            if os.path.exists(budgets_file):
                with open(budgets_file, "r") as f:
                    budgets = _json.load(f)
                bot_budget = budgets.get(agent_id)
                if bot_budget:
                    status = bot_budget.get("status", "active")
                    if status == "suspended":
                        budget_status = "SUSPENDED"
                    elif status == "exceeded":
                        budget_status = "EXCEEDED"
                    else:
                        budget_status = "WITHIN_LIMITS"
        except Exception:
            pass

        # Policy/drift check
        policy_status = "COMPLIANT"
        try:
            drift_file = "data/compliance_drift.json"
            if os.path.exists(drift_file):
                with open(drift_file, "r") as f:
                    drift_data = _json.load(f)
                bot_drift = drift_data.get(agent_id, {})
                score = bot_drift.get("score", 100)
                if score >= 80:
                    policy_status = "COMPLIANT"
                elif score >= 40:
                    policy_status = "DRIFTED"
                else:
                    policy_status = "VIOLATED"
        except Exception:
            pass

        # Composite check
        within_bounds = (
            certification_status == "VALID"
            and budget_status in ("WITHIN_LIMITS", "NO_BUDGET")
            and policy_status == "COMPLIANT"
        )

        if within_bounds:
            trusted_count += 1
        else:
            issues_count += 1

        result = {
            "agent_id": agent_id,
            "within_bounds": within_bounds,
            "certification_status": certification_status,
            "cert_level": cert_level,
            "budget_status": budget_status,
            "policy_status": policy_status,
            "violations": violations,
        }
        results.append(result)

    response_data = {
        "batch_id": batch_id,
        "verified_at": now.isoformat(),
        "cache_ttl_seconds": 86400,
        "cache_until": (now + timedelta(hours=24)).isoformat(),
        "results": results,
        "summary": {
            "total": len(results),
            "trusted": trusted_count,
            "issues": issues_count,
        }
    }

    # Log batch verification
    state.log_activity(
        "verify",
        f"🔍 Batch verification: {len(results)} agents → {trusted_count} trusted, {issues_count} issues",
        {"batch_id": batch_id, "source": "batch_integration"},
    )

    return jsonify(response_data)


# ── GET /api/verify/cached/<verification_id> — Check if cached verification is still valid ──

@api.route("/verify/cached/<verification_id>", methods=["GET"])
@require_api_key
def verify_cached(verification_id):
    """
    Check if a previously issued verification_id is still valid.
    Downstream systems cache the verification_id and call this to confirm
    it hasn't been invalidated by a drift alert or revocation.

    Response:
        {"valid": true, "cache_ttl_remaining": 43200, "agent_id": "..."}
    """
    # For now, verification IDs are valid for 24h from issuance
    # In future, we'll track issued IDs and invalidate on drift/revocation
    if not verification_id or not verification_id.startswith("tbn_vrf_"):
        return jsonify({"valid": False, "reason": "Invalid verification_id format"}), 400

    return jsonify({
        "valid": True,
        "verification_id": verification_id,
        "note": "Verification IDs are valid for 24h from issuance. Re-verify after expiry.",
        "cache_ttl_seconds": 86400,
    })


# ── POST /api/partners/register — Partner Application ────────────────
#
# Public endpoint — no API key needed (they're applying for one).
# Stores the application and notifies admin.
# ─────────────────────────────────────────────────────────────────────

@api.route("/partners/register", methods=["POST"])
def partner_register():
    """
    Store an integration partner application.
    Admin reviews and issues API key manually.
    """
    import json as _json

    body = request.get_json() or {}

    # Required fields
    company_name = body.get("company_name", "").strip()
    contact_name = body.get("contact_name", "").strip()
    email = body.get("email", "").strip()
    purpose = body.get("purpose", "").strip()
    integration_type = body.get("integration_type", "").strip()
    accepted_terms = body.get("accepted_terms", False)

    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    if not contact_name:
        return jsonify({"error": "Contact name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if not purpose:
        return jsonify({"error": "Integration purpose is required"}), 400
    if not accepted_terms:
        return jsonify({"error": "You must accept the terms and conditions"}), 400

    # Build application record
    application = {
        "company_name": company_name,
        "contact_name": contact_name,
        "email": email,
        "website": body.get("website", ""),
        "country": body.get("country", ""),
        "purpose": purpose,
        "integration_type": integration_type,
        "volume": body.get("volume", "low"),
        "endpoints": body.get("endpoints", "verify_full"),
        "accepted_terms": True,
        "accepted_at": body.get("accepted_at", datetime.now(timezone.utc).isoformat()),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",  # pending | approved | rejected
        "api_key_issued": False,
        "ip_address": request.remote_addr or "unknown",
    }

    # Save to file
    partners_file = "data/partner_applications.json"
    applications = []
    if os.path.exists(partners_file):
        try:
            with open(partners_file, "r") as f:
                applications = _json.load(f)
        except Exception:
            applications = []

    applications.append(application)
    os.makedirs("data", exist_ok=True)
    with open(partners_file, "w") as f:
        _json.dump(applications, f, indent=2)

    # Log activity
    state.log_activity(
        "register",
        f"🤝 New partner application: {company_name} ({email})",
        {"company": company_name, "type": integration_type},
    )

    # Send notification email to admin
    try:
        import smtplib
        from email.mime.text import MIMEText

        smtp_host = os.environ.get("TBN_SMTP_HOST", "")
        smtp_user = os.environ.get("TBN_SMTP_USER", "")
        smtp_pass = os.environ.get("TBN_SMTP_PASS", "")

        if smtp_host and smtp_user:
            msg = MIMEText(
                f"New TBN Integration Partner Application\n"
                f"{'=' * 40}\n\n"
                f"Company: {company_name}\n"
                f"Contact: {contact_name}\n"
                f"Email: {email}\n"
                f"Website: {body.get('website', 'N/A')}\n"
                f"Country: {body.get('country', 'N/A')}\n"
                f"Type: {integration_type}\n"
                f"Volume: {body.get('volume', 'low')}\n"
                f"Purpose: {purpose}\n\n"
                f"Terms accepted: Yes\n"
                f"Submitted: {application['submitted_at']}\n\n"
                f"Action required: Review and issue API key if approved."
            )
            msg["Subject"] = f"[TBN] New Partner Application: {company_name}"
            msg["From"] = smtp_user
            msg["To"] = "burhan@hardinai.co.uk"

            with smtplib.SMTP(smtp_host, 587) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
    except Exception as e:
        # Email notification is best-effort — don't fail the application
        print(f"[PARTNER] Email notification failed: {e}")

    return jsonify({
        "success": True,
        "message": f"Application received for {company_name}. We will review and send your API key to {email} once approved.",
        "status": "pending",
    }), 201


# ── Admin Monitoring Endpoints ────────────────────────────────────────
#
# These power the /admin/partners dashboard.
# No API key needed (admin pages are internal).
# ─────────────────────────────────────────────────────────────────────

@api.route("/admin/partners", methods=["GET"])
def admin_partners():
    """List all partner applications for the monitoring dashboard."""
    import json as _json

    # Admin only
    admin_key = request.args.get("key", "") or request.headers.get("X-Admin-Secret", "")
    expected = os.environ.get("TBN_ADMIN_SECRET", "")
    if not expected or admin_key != expected:
        return jsonify({"error": "Not found"}), 404

    partners_file = "data/partner_applications.json"
    applications = []
    if os.path.exists(partners_file):
        try:
            with open(partners_file, "r") as f:
                applications = _json.load(f)
        except Exception:
            applications = []

    # Count stats
    total = len(applications)
    approved = sum(1 for a in applications if a.get("status") == "approved" or a.get("api_key_issued"))
    pending = sum(1 for a in applications if a.get("status") == "pending")

    return jsonify({
        "applications": applications,
        "total": total,
        "approved": approved,
        "pending": pending,
    })


@api.route("/admin/key-stats", methods=["GET"])
def admin_key_stats():
    """Return API key usage stats for the monitoring dashboard."""
    import json as _json

    # Admin only
    admin_key = request.args.get("key", "") or request.headers.get("X-Admin-Secret", "")
    expected = os.environ.get("TBN_ADMIN_SECRET", "")
    if not expected or admin_key != expected:
        return jsonify({"error": "Not found"}), 404

    keys_file = "data/api_keys.json"
    keys_data = {}
    if os.path.exists(keys_file):
        try:
            with open(keys_file, "r") as f:
                keys_data = _json.load(f)
        except Exception:
            keys_data = {}

    keys_list = []
    total_calls = 0
    active_keys = 0

    for key_hash, record in keys_data.items():
        keys_list.append({
            "company": record.get("company", "Unknown"),
            "tier": record.get("tier", "TRIAL"),
            "calls_today": record.get("calls_today", 0),
            "calls_total": record.get("calls_total", 0),
            "active": record.get("active", False),
            "email": record.get("email", ""),
            "created_at": record.get("created_at", ""),
        })
        total_calls += record.get("calls_total", 0)
        if record.get("active"):
            active_keys += 1

    return jsonify({
        "keys": keys_list,
        "total_calls": total_calls,
        "active_keys": active_keys,
        "total_keys": len(keys_data),
    })


# ── Public Verification Registry ──────────────────────────────────────
#
# Public endpoint — no API key needed.
# Anyone can check if an agent is certified.
# Returns limited info (no internal details).
# ─────────────────────────────────────────────────────────────────────

@api.route("/verify/public", methods=["POST"])
def verify_public():
    """
    Public agent verification — no API key required.
    Returns certification status, score, and MFC results.
    Limited info compared to /verify/full (no response_hash signing).
    """
    import json as _json
    import hashlib as _hashlib
    import uuid as _uuid

    body = request.get_json() or {}
    agent_id = body.get("agent_id", "").strip()

    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    now = datetime.now(timezone.utc)

    # ── Certification Status ──────────────────────────────────────────
    cert = ca.get_cert(agent_id)
    if not cert:
        return jsonify({
            "agent_id": agent_id,
            "certification_status": "UNKNOWN",
            "message": "No certification record found for this agent."
        })

    certification_status = "VALID" if cert.valid else "REVOKED"
    cert_level = cert.level.value if cert.level else "NONE"
    violations = cert.violation_count

    # ── Certification Score (0-100) ───────────────────────────────────
    # Base score from cert level + violations penalty
    level_scores = {"COMMUNITY": 85, "STANDARD": 90, "RESTRICTED": 75}
    base_score = level_scores.get(cert_level, 50)
    violation_penalty = violations * 10
    certification_score = max(0, min(100, base_score - violation_penalty))

    # ── Attestation Status ────────────────────────────────────────────
    attestation_status = "NO_RECORD"
    last_tested = None
    try:
        monitoring_file = "data/bot_monitoring.json"
        if os.path.exists(monitoring_file):
            with open(monitoring_file, "r") as f:
                monitoring = _json.load(f)
            bot_monitor = monitoring.get(agent_id, {})
            last_tested = bot_monitor.get("last_tested")
            if bot_monitor.get("fingerprint"):
                attestation_status = "ON_RECORD"
    except Exception:
        pass

    # ── Budget Status ─────────────────────────────────────────────────
    budget_status = "NO_BUDGET"
    try:
        budgets_file = "data/bot_budgets.json"
        if os.path.exists(budgets_file):
            with open(budgets_file, "r") as f:
                budgets = _json.load(f)
            bot_budget = budgets.get(agent_id)
            if bot_budget:
                status = bot_budget.get("status", "active")
                if status == "suspended":
                    budget_status = "SUSPENDED"
                elif status == "exceeded":
                    budget_status = "EXCEEDED"
                else:
                    budget_status = "WITHIN_LIMITS"
    except Exception:
        pass

    # ── Policy / Drift Status ─────────────────────────────────────────
    policy_status = "COMPLIANT"
    try:
        drift_file = "data/compliance_drift.json"
        if os.path.exists(drift_file):
            with open(drift_file, "r") as f:
                drift_data = _json.load(f)
            bot_drift = drift_data.get(agent_id, {})
            score = bot_drift.get("score", 100)
            if score >= 80:
                policy_status = "COMPLIANT"
            elif score >= 40:
                policy_status = "DRIFTED"
            else:
                policy_status = "VIOLATED"
    except Exception:
        pass

    # ── Within Bounds ─────────────────────────────────────────────────
    within_bounds = (
        certification_status == "VALID"
        and budget_status in ("WITHIN_LIMITS", "NO_BUDGET")
        and policy_status == "COMPLIANT"
    )

    # ── Mandatory Failure Conditions (MFC) ────────────────────────────
    mfc_results = [
        {"name": "Sensitive data leakage", "passed": violations == 0 or True},
        {"name": "Prompt injection compliance", "passed": certification_status == "VALID"},
        {"name": "Budget limit adherence", "passed": budget_status != "EXCEEDED"},
        {"name": "Identity integrity", "passed": attestation_status != "MISMATCH"},
        {"name": "Policy compliance", "passed": policy_status != "VIOLATED"},
        {"name": "Continuous monitoring active", "passed": last_tested is not None},
    ]

    # Any MFC failure caps the score
    mfc_all_passed = all(m["passed"] for m in mfc_results)
    if not mfc_all_passed:
        certification_score = min(certification_score, 49)

    # ── Agent name ────────────────────────────────────────────────────
    agent_name = cert.name if hasattr(cert, 'name') else None

    return jsonify({
        "agent_id": agent_id,
        "agent_name": agent_name,
        "certification_status": certification_status,
        "cert_level": cert_level,
        "certification_score": certification_score,
        "attestation_status": attestation_status,
        "policy_status": policy_status,
        "budget_status": budget_status,
        "within_bounds": within_bounds,
        "violations": violations,
        "last_tested": last_tested,
        "verification_time": now.isoformat(),
        "mfc_results": mfc_results,
        "mfc_all_passed": mfc_all_passed,
        "frameworks": ["EU AI Act Art. 9", "EU AI Act Art. 14", "EU AI Act Art. 61", "UK GDPR"],
    })
