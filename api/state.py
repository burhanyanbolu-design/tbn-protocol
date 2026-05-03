"""
Shared server state — single BICA, seeded network, and bot registry
shared across all API routes.
"""

from tbn.identity import BICA
from tbn.seeded_network import SeededNetwork
from tbn.cloning import CloneManager
from tbn.platform_integration import PlatformAdapter, PublicBICARegistry, AuditLog
from tbn.compiler import BotLanguageCompiler

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
