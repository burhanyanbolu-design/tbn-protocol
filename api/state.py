"""
Shared server state — single BICA, seeded network, and bot registry
shared across all API routes.
"""

from tbn.identity import BICA
from tbn.seeded_network import SeededNetwork
from tbn.cloning import CloneManager
from tbn.platform_integration import PlatformAdapter, PublicBICARegistry, AuditLog
from tbn.compiler import BotLanguageCompiler
from tbn.certification import CertificationAuthority, CertLevel, BotCertificate

# ── Shared singletons ────────────────────────────────────────────────
bica         = BICA(registry_path="data/bica_registry.json")
seeded_net   = SeededNetwork()
clone_mgr    = CloneManager(bica)
compiler     = BotLanguageCompiler()
public_reg   = PublicBICARegistry(bica)
audit_log    = AuditLog()

# bot_id → Bot instance
bots: dict = {}

# activity feed — last 50 events shown on dashboard
activity: list[dict] = []

# ── Certification Authority with persistence ─────────────────────────
ca = CertificationAuthority(bica)

def _load_certifications():
    """
    Load certifications from BICA registry on startup.
    This ensures bots remain certified across server restarts.
    """
    count = 0
    for bot_id, cert_data in bica._registry.items():
        cert_level_str = cert_data.get("cert_level", "STANDARD")
        try:
            level = CertLevel(cert_level_str)
        except ValueError:
            level = CertLevel.STANDARD

        # Create a BotCertificate directly in the CA
        cert = BotCertificate(
            bot_id=bot_id,
            name=cert_data.get("name", "Unknown"),
            level=level,
            public_key_pem=cert_data.get("public_key_pem", ""),
            purpose=cert_data.get("purpose", ""),
            ethical_declaration=True,
        )
        ca._certs[bot_id] = cert
        count += 1

    if count:
        print(f"[CA] Loaded {count} certifications from registry")

_load_certifications()


def log_activity(event_type: str, message: str, data: dict = None):
    from datetime import datetime, timezone
    entry = {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "type": event_type,   # register | handshake | search | verify | error
        "message": message,
        "data": data or {},
    }
    activity.insert(0, entry)
    if len(activity) > 50:
        activity.pop()
