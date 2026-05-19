"""
TBN Certificate Authority — Hardin AI Solutions
================================================
THE ONLY system that can create and sign TBN bots.

Rules:
  1. Only Hardin can CREATE a TBN bot (master private key)
  2. Every bot is REGISTERED to ONE owner (non-transferable)
  3. If a cloned/tampered bot appears → auto-deleted, owner notified
  4. Cloned bot is USELESS — rejected by every other bot in the network
  5. There is ONE TBN. There can be no other.
  6. No reselling. Bot is locked to the registered owner forever.

Like a crypto token but Hardin controls the supply AND the price:
  - Bitcoin: algorithm decides supply
  - TBN Bot: Hardin decides supply, price, and who gets one
  - Clone detected → auto-revoked → must buy genuine from Hardin

Like a government passport:
  - Anyone can CHECK it's real (public key)
  - Only Hardin can ISSUE one (private key)
  - Tampering is instantly visible (signature)
  - Tied to ONE person — non-transferable
"""

import os
import json
import hashlib
import secrets
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


# ── Key paths ────────────────────────────────────────────────────────
# Private key NEVER leaves the server. Never in git. Never in PyPI.
PRIVATE_KEY_PATH = os.environ.get("TBN_PRIVATE_KEY_PATH", "/opt/tbn-protocol/keys/tbn_master.pem")
PUBLIC_KEY_PATH  = os.environ.get("TBN_PUBLIC_KEY_PATH",  "/opt/tbn-protocol/keys/tbn_public.pem")
TBN_ISSUER       = "Hardin AI Solutions — TBN Certificate Authority"
TBN_VERSION      = "1.0"


# ── Master Key Management ─────────────────────────────────────────────

def generate_master_keys():
    """
    Generate the RSA-4096 master key pair.
    Run ONCE on the server. Store private key securely.
    NEVER run this again — it would invalidate all existing bots.
    """
    os.makedirs(os.path.dirname(PRIVATE_KEY_PATH), exist_ok=True)

    if os.path.exists(PRIVATE_KEY_PATH):
        raise RuntimeError(
            "Master key already exists! "
            "Regenerating would invalidate ALL existing TBN bots. "
            "Delete manually only if you are absolutely sure."
        )

    print("Generating RSA-4096 master key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )

    # Save private key (chmod 600 — owner read only)
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(pem_private)
    os.chmod(PRIVATE_KEY_PATH, 0o600)

    # Save public key (can be shared publicly)
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(pem_public)
    os.chmod(PUBLIC_KEY_PATH, 0o644)

    print(f"✅ Private key saved to: {PRIVATE_KEY_PATH}  (KEEP SECRET)")
    print(f"✅ Public key saved to:  {PUBLIC_KEY_PATH}   (share freely)")
    print()
    print("⚠️  IMPORTANT: Back up the private key to an offline location NOW.")
    print("⚠️  If lost, all existing TBN bots become unverifiable.")

    return private_key.public_key()


def _load_private_key():
    """Load the master private key. Fails loudly if missing."""
    if not os.path.exists(PRIVATE_KEY_PATH):
        raise RuntimeError(
            f"TBN master private key not found at {PRIVATE_KEY_PATH}. "
            "Run generate_master_keys() on the server first."
        )
    with open(PRIVATE_KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())


def _load_public_key():
    """Load the master public key."""
    if not os.path.exists(PUBLIC_KEY_PATH):
        raise RuntimeError(f"TBN public key not found at {PUBLIC_KEY_PATH}.")
    with open(PUBLIC_KEY_PATH, "rb") as f:
        return serialization.load_pem_public_key(f.read(), backend=default_backend())


def get_public_key_pem() -> str:
    """Return the public key as PEM string — safe to publish."""
    return _load_public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()


# ── TBN Bot Creation (Hardin only) ───────────────────────────────────

def create_tbn_bot(
    bot_name: str,
    bot_type: str,
    owner_company: str,
    star_rating: int,
    capabilities: list,
    data_categories: list,
) -> dict:
    """
    Create and cryptographically sign a new TBN bot.

    Only callable server-side with the master private key.
    The resulting certificate proves:
      - This bot was created by Hardin AI Solutions
      - The bot's identity has not been tampered with
      - The bot is the ONLY one with this ID

    Returns the full bot record including the signed certificate.
    """
    if not 1 <= star_rating <= 5:
        raise ValueError("star_rating must be 1-5")

    # Generate unique bot ID
    random_suffix = secrets.token_hex(8)
    bot_id = f"tbn-{bot_type.lower()}-{random_suffix}"

    # Build the canonical payload (what we sign)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "bot_id":          bot_id,
        "bot_name":        bot_name,
        "bot_type":        bot_type.upper(),
        "owner_company":   owner_company,
        "star_rating":     star_rating,
        "capabilities":    sorted(capabilities),
        "data_categories": sorted(data_categories),
        "issued_by":       TBN_ISSUER,
        "issued_at":       now,
        "tbn_version":     TBN_VERSION,
    }

    # Canonical JSON (sorted keys, no whitespace) — deterministic
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    # Sign with master private key (RSA-PSS + SHA-512)
    private_key = _load_private_key()
    signature   = private_key.sign(
        canonical,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA512()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA512()
    )
    signature_b64 = base64.b64encode(signature).decode()

    # Fingerprint = SHA-256 of canonical payload
    fingerprint = hashlib.sha256(canonical).hexdigest()

    certificate = {
        **payload,
        "fingerprint":  fingerprint,
        "signature":    signature_b64,
        "algorithm":    "RSA-PSS-SHA512",
        "key_size":     4096,
        "verify_url":   f"https://tbn.hardinai.co.uk/verify/{bot_id}",
        "public_key_url": "https://tbn.hardinai.co.uk/public-key",
    }

    return certificate


# ── Verification (anyone can do this) ────────────────────────────────

def verify_tbn_bot(certificate: dict) -> tuple[bool, str]:
    """
    Verify a TBN bot certificate using the PUBLIC key.

    Anyone can call this — no private key needed.
    Returns (valid: bool, reason: str)

    If valid=True  → bot was genuinely created by Hardin AI Solutions
    If valid=False → bot is fake, tampered, or from a different system
    """
    try:
        # Extract and remove signature fields before re-canonicalising
        cert = dict(certificate)
        signature_b64 = cert.pop("signature", None)
        cert.pop("fingerprint", None)
        cert.pop("algorithm", None)
        cert.pop("key_size", None)
        cert.pop("verify_url", None)
        cert.pop("public_key_url", None)

        if not signature_b64:
            return False, "No signature found — this is not a genuine TBN certificate"

        # Rebuild canonical payload
        canonical = json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()

        # Verify fingerprint
        expected_fp = hashlib.sha256(canonical).hexdigest()
        if certificate.get("fingerprint") != expected_fp:
            return False, "Fingerprint mismatch — certificate has been tampered with"

        # Verify signature with public key
        public_key = _load_public_key()
        signature  = base64.b64decode(signature_b64)

        public_key.verify(
            signature,
            canonical,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512()
        )

        # Check issuer
        if cert.get("issued_by") != TBN_ISSUER:
            return False, f"Invalid issuer: '{cert.get('issued_by')}' — only Hardin AI Solutions can issue TBN certificates"

        return True, f"✅ Genuine TBN bot — issued by {TBN_ISSUER}"

    except InvalidSignature:
        return False, "❌ Invalid signature — this certificate was NOT issued by Hardin AI Solutions"
    except Exception as e:
        return False, f"❌ Verification error: {str(e)}"


def verify_bot_id(bot_id: str, registry_path: str = "data/tbn_registry.json") -> tuple[bool, dict | None, str]:
    """
    Look up a bot by ID in the registry and verify its certificate.
    """
    if not os.path.exists(registry_path):
        return False, None, "Registry not found"

    with open(registry_path) as f:
        registry = json.load(f)

    cert = registry.get(bot_id)
    if not cert:
        return False, None, f"Bot ID '{bot_id}' not found in TBN registry"

    valid, reason = verify_tbn_bot(cert)
    return valid, cert, reason


# ── Registry Management (server-side only) ───────────────────────────

REGISTRY_PATH = "data/tbn_registry.json"

def register_bot_in_registry(certificate: dict):
    """Save a newly created bot to the official TBN registry."""
    os.makedirs("data", exist_ok=True)

    registry = {}
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)

    bot_id = certificate["bot_id"]
    if bot_id in registry:
        raise ValueError(f"Bot ID {bot_id} already exists in registry")

    registry[bot_id] = certificate

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"✅ Bot registered: {bot_id} ({certificate['bot_name']})")
    return bot_id


def list_registry() -> list:
    """List all bots in the official TBN registry."""
    if not os.path.exists(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    return list(registry.values())


def get_registry_stats() -> dict:
    """Stats about the TBN registry."""
    bots = list_registry()
    by_type   = {}
    by_rating = {}
    for b in bots:
        t = b.get("bot_type", "UNKNOWN")
        r = b.get("star_rating", 0)
        by_type[t]   = by_type.get(t, 0) + 1
        by_rating[r] = by_rating.get(r, 0) + 1

    return {
        "total_bots":  len(bots),
        "by_type":     by_type,
        "by_rating":   by_rating,
        "issuer":      TBN_ISSUER,
        "tbn_version": TBN_VERSION,
    }


# ── Clone Detection & Auto-Revocation ────────────────────────────────
"""
Clone Detection System
======================
Every time a bot makes an API call, we check:
  1. Is the bot ID in our official registry?         → if not: FAKE
  2. Does the signature verify with our public key?  → if not: TAMPERED
  3. Is the owner_company correct for this bot ID?   → if not: STOLEN/RESOLD
  4. Is this bot ID appearing from multiple owners?  → if yes: CLONED

Any failure → bot is auto-revoked + logged + owner notified to buy genuine.
"""

REVOKED_PATH    = "data/tbn_revoked.json"
CLONE_LOG_PATH  = "data/tbn_clone_log.json"


def _load_revoked() -> dict:
    if os.path.exists(REVOKED_PATH):
        with open(REVOKED_PATH) as f:
            return json.load(f)
    return {}


def _save_revoked(revoked: dict):
    os.makedirs("data", exist_ok=True)
    with open(REVOKED_PATH, "w") as f:
        json.dump(revoked, f, indent=2)


def _log_clone_attempt(bot_id: str, reason: str, caller_info: dict):
    """Log every clone/tamper attempt for audit trail."""
    os.makedirs("data", exist_ok=True)
    log = []
    if os.path.exists(CLONE_LOG_PATH):
        with open(CLONE_LOG_PATH) as f:
            log = json.load(f)

    log.append({
        "bot_id":      bot_id,
        "reason":      reason,
        "caller_info": caller_info,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    })

    with open(CLONE_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def auto_revoke_bot(bot_id: str, reason: str, caller_info: dict = None):
    """
    Immediately revoke a bot and log the reason.
    The bot becomes useless — rejected by every other bot in the network.
    Owner is forced to purchase a genuine bot from Hardin.
    """
    revoked = _load_revoked()
    revoked[bot_id] = {
        "bot_id":     bot_id,
        "reason":     reason,
        "revoked_at": datetime.now(timezone.utc).isoformat(),
        "action":     "AUTO_REVOKED — purchase genuine bot at tbn.hardinai.co.uk/pricing",
    }
    _save_revoked(revoked)
    _log_clone_attempt(bot_id, reason, caller_info or {})
    print(f"🚨 AUTO-REVOKED: {bot_id} — {reason}")


def is_revoked(bot_id: str) -> tuple[bool, str]:
    """Check if a bot has been revoked."""
    revoked = _load_revoked()
    if bot_id in revoked:
        return True, revoked[bot_id]["reason"]
    return False, ""


def validate_bot_request(bot_id: str, claimed_owner: str, certificate: dict, caller_info: dict = None) -> tuple[bool, str]:
    """
    Full validation check every time a bot makes an API call.

    Checks (in order):
      1. Not already revoked
      2. Bot ID exists in official registry
      3. Signature is valid (not tampered)
      4. Owner matches registry (not stolen/resold)
      5. No duplicate bot ID from different owner (not cloned)

    Returns (allowed: bool, reason: str)
    If allowed=False → bot is auto-revoked and caller told to buy genuine.
    """
    caller_info = caller_info or {}

    # ── Check 1: Already revoked? ─────────────────────────────────────
    revoked, rev_reason = is_revoked(bot_id)
    if revoked:
        return False, (
            f"Bot {bot_id} has been revoked: {rev_reason}. "
            f"Purchase a genuine TBN bot at tbn.hardinai.co.uk/pricing"
        )

    # ── Check 2: In official registry? ───────────────────────────────
    valid_id, reg_cert, reason = verify_bot_id(bot_id)
    if not valid_id:
        # Not in registry = fake/cloned bot
        auto_revoke_bot(bot_id, f"FAKE — not in official TBN registry: {reason}", caller_info)
        return False, (
            f"❌ Bot {bot_id} is not a genuine TBN bot. "
            f"It has been blocked. Purchase a genuine bot at tbn.hardinai.co.uk/pricing"
        )

    # ── Check 3: Signature valid? (tamper detection) ──────────────────
    sig_valid, sig_reason = verify_tbn_bot(certificate)
    if not sig_valid:
        auto_revoke_bot(bot_id, f"TAMPERED — {sig_reason}", caller_info)
        return False, (
            f"❌ Bot {bot_id} certificate has been tampered with and has been blocked. "
            f"Purchase a genuine bot at tbn.hardinai.co.uk/pricing"
        )

    # ── Check 4: Owner matches? (stolen/resold detection) ─────────────
    registered_owner = reg_cert.get("owner_company", "")
    if claimed_owner and registered_owner and claimed_owner.strip().lower() != registered_owner.strip().lower():
        auto_revoke_bot(
            bot_id,
            f"OWNERSHIP MISMATCH — registered to '{registered_owner}', "
            f"used by '{claimed_owner}'. Bots are non-transferable.",
            caller_info
        )
        return False, (
            f"❌ Bot {bot_id} is registered to a different company. "
            f"TBN bots are non-transferable. "
            f"Purchase your own bot at tbn.hardinai.co.uk/pricing"
        )

    # ── Check 5: Clone detection (same ID, different fingerprint) ─────
    submitted_fp  = certificate.get("fingerprint", "")
    registered_fp = reg_cert.get("fingerprint", "")
    if submitted_fp and registered_fp and submitted_fp != registered_fp:
        auto_revoke_bot(
            bot_id,
            f"CLONED — fingerprint mismatch. "
            f"Registered: {registered_fp[:16]}... "
            f"Submitted: {submitted_fp[:16]}...",
            caller_info
        )
        return False, (
            f"❌ A cloned version of bot {bot_id} has been detected and blocked. "
            f"The original bot has also been revoked for security. "
            f"Purchase a new genuine bot at tbn.hardinai.co.uk/pricing"
        )

    # ── All checks passed ─────────────────────────────────────────────
    return True, f"✅ Bot {bot_id} verified — genuine TBN bot owned by {registered_owner}"


# ── Bot Factory (the ONLY way to create TBN bots) ────────────────────

def bot_factory(
    bot_name: str,
    bot_type: str,
    owner_company: str,
    owner_email: str,
    star_rating: int,
    capabilities: list,
    data_categories: list,
    purchase_ref: str,          # payment/order reference
) -> dict:
    """
    THE BOT FACTORY — the only place TBN bots are born.

    Every bot created here is:
      - Cryptographically signed by Hardin's master key
      - Registered to ONE owner (non-transferable)
      - Assigned a unique ID that can never be duplicated
      - Immediately added to the official registry
      - Useless if cloned, tampered, or transferred

    Returns the complete bot certificate (save it — shown once).
    """
    # Create and sign the bot
    certificate = create_tbn_bot(
        bot_name=bot_name,
        bot_type=bot_type,
        owner_company=owner_company,
        star_rating=star_rating,
        capabilities=capabilities,
        data_categories=data_categories,
    )

    # Add ownership and purchase info
    certificate["owner_email"]   = owner_email
    certificate["purchase_ref"]  = purchase_ref
    certificate["transferable"]  = False
    certificate["resellable"]    = False
    certificate["notice"]        = (
        "This TBN bot is licensed exclusively to the registered owner. "
        "It cannot be transferred, resold, or shared. "
        "Any attempt to clone or tamper will result in immediate revocation. "
        "© Hardin AI Solutions — tbn.hardinai.co.uk"
    )

    # Register in official registry
    register_bot_in_registry(certificate)

    print(f"🏭 BOT FACTORY: Created {certificate['bot_id']} for {owner_company}")
    print(f"   Type: {bot_type} | Rating: {'⭐' * star_rating} | Owner: {owner_email}")
    print(f"   Purchase ref: {purchase_ref}")

    return certificate


# ── Network-wide clone check (runs on every API call) ────────────────

def network_clone_check(bot_id: str, certificate: dict, api_key_owner: str, caller_ip: str) -> tuple[bool, str]:
    """
    Called automatically on EVERY API request.
    If anything is wrong → bot is dead instantly.
    No warnings. No second chances.
    """
    caller_info = {
        "api_key_owner": api_key_owner,
        "caller_ip":     caller_ip,
        "checked_at":    datetime.now(timezone.utc).isoformat(),
    }

    allowed, reason = validate_bot_request(
        bot_id=bot_id,
        claimed_owner=api_key_owner,
        certificate=certificate,
        caller_info=caller_info,
    )

    if not allowed:
        # Log to security alert
        print(f"🚨 SECURITY ALERT: {reason}")
        print(f"   Bot ID: {bot_id} | IP: {caller_ip} | Owner claim: {api_key_owner}")

    return allowed, reason


def get_clone_stats() -> dict:
    """Stats on clone/tamper attempts — for admin dashboard."""
    log = []
    if os.path.exists(CLONE_LOG_PATH):
        with open(CLONE_LOG_PATH) as f:
            log = json.load(f)

    revoked = _load_revoked()

    return {
        "total_clone_attempts": len(log),
        "total_revoked_bots":   len(revoked),
        "recent_attempts":      log[-10:] if log else [],
        "revoked_bots":         list(revoked.keys()),
    }
