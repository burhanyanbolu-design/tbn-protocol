"""
TBN Protocol — Community Bot Certification Demo
=================================================
Demonstrates the 3-tier certification programme:

  🟢 COMMUNITY  — trusted, ethical, verified (full access)
  🔵 STANDARD   — basic access, public data only
  🟡 RESTRICTED — read-only, must route via Community Bot

Tests:
  1. Certifying bots at each tier
  2. Permissions per tier
  3. Trust compatibility in handshake
  4. Blocked handshake (incompatible tiers)
  5. Violation reporting + auto-revocation
  6. Platform access rules per cert level

Run:
    python demo_certification.py
"""

from tbn.identity import BICA
from tbn.certification import CertificationAuthority, CertLevel
from tbn.bots import SearchBot, ValidatorBot, ConnectorBot
from tbn.handshake import HandshakeError


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print("\n" + "="*60)
    print("  TBN — Community Bot Certification Programme")
    print("  Three tiers: COMMUNITY | STANDARD | RESTRICTED")
    print("="*60)

    bica = BICA(registry_path="data/bica_registry.json")
    ca   = CertificationAuthority(bica)

    # ── 1. Create and certify bots at each tier ──────────────────────
    section("1. Certifying Bots at Each Tier")

    # COMMUNITY bot — requires ethical declaration + purpose
    community_bot = SearchBot("HardinSearchBot", bica, ca=ca)
    community_cert = ca.certify(
        identity=community_bot.identity,
        level=CertLevel.COMMUNITY,
        purpose="Trusted AI tool discovery for the TBN network",
        ethical_declaration=True,
    )

    # STANDARD bot — basic registration
    standard_bot = ValidatorBot("StandardValidator", bica, ca=ca)
    standard_cert = ca.certify(
        identity=standard_bot.identity,
        level=CertLevel.STANDARD,
    )

    # RESTRICTED bot — minimal requirements
    restricted_bot = ConnectorBot("RestrictedConnector", bica, ca=ca)
    restricted_cert = ca.certify(
        identity=restricted_bot.identity,
        level=CertLevel.RESTRICTED,
    )

    print(f"\n  {community_cert}")
    print(f"  {standard_cert}")
    print(f"  {restricted_cert}")

    # ── 2. Permissions per tier ──────────────────────────────────────
    section("2. Permissions Per Tier")

    actions = [
        "can_search", "can_read_private", "can_write",
        "can_clone", "can_access_restricted",
    ]

    header = f"  {'Action':<25} {'COMMUNITY':^12} {'STANDARD':^12} {'RESTRICTED':^12}"
    print(f"\n{header}")
    print(f"  {'-'*63}")

    for action in actions:
        c = "✅" if community_cert.can(action)  else "❌"
        s = "✅" if standard_cert.can(action)   else "❌"
        r = "✅" if restricted_cert.can(action) else "❌"
        print(f"  {action:<25} {c:^12} {s:^12} {r:^12}")

    # ── 3. Trust compatibility ───────────────────────────────────────
    section("3. Trust Compatibility Matrix")

    pairs = [
        (community_bot,  standard_bot,   "COMMUNITY ↔ STANDARD"),
        (community_bot,  restricted_bot, "COMMUNITY ↔ RESTRICTED"),
        (standard_bot,   restricted_bot, "STANDARD  ↔ RESTRICTED"),
        (restricted_bot, restricted_bot, "RESTRICTED ↔ RESTRICTED"),
    ]

    for bot_a, bot_b, label in pairs:
        compatible, reason = ca.check_compatibility(
            bot_a.bot_id, bot_b.bot_id
        )
        status = "✅ Compatible" if compatible else "❌ Blocked"
        print(f"\n  {label}")
        print(f"  {status} — {reason}")

    # ── 4. Handshake with cert check ─────────────────────────────────
    section("4. Handshake — Cert Compatibility Enforced")

    print("\n  Test A: COMMUNITY ↔ STANDARD (should succeed)...")
    try:
        community_bot.connect(standard_bot)
        print("  ✅ Handshake succeeded")
    except HandshakeError as e:
        print(f"  ❌ Handshake failed: {e}")

    print("\n  Test B: STANDARD ↔ RESTRICTED (should be BLOCKED)...")
    try:
        standard_bot.connect(restricted_bot)
        print("  ✅ Handshake succeeded (unexpected)")
    except HandshakeError as e:
        print(f"  ❌ Handshake blocked: {e}  ← correct ✅")

    print("\n  Test C: COMMUNITY ↔ RESTRICTED (should succeed via community)...")
    try:
        community_bot.connect(restricted_bot)
        print("  ✅ Handshake succeeded — RESTRICTED can connect via COMMUNITY")
    except HandshakeError as e:
        print(f"  ❌ Handshake failed: {e}")

    # ── 5. Community Bot requirement enforcement ─────────────────────
    section("5. Community Bot Requirements — Ethical Declaration")

    print("\n  Trying to certify as COMMUNITY without ethical declaration...")
    test_bot = SearchBot("BadActor", bica, ca=ca)
    try:
        ca.certify(
            identity=test_bot.identity,
            level=CertLevel.COMMUNITY,
            purpose="",
            ethical_declaration=False,
        )
        print("  Certified (unexpected)")
    except ValueError as e:
        print(f"  ❌ Rejected: {e}  ← correct ✅")

    print("\n  Trying to certify as COMMUNITY without purpose...")
    try:
        ca.certify(
            identity=test_bot.identity,
            level=CertLevel.COMMUNITY,
            purpose="",
            ethical_declaration=True,
        )
        print("  Certified (unexpected)")
    except ValueError as e:
        print(f"  ❌ Rejected: {e}  ← correct ✅")

    # ── 6. Violation reporting + auto-revocation ─────────────────────
    section("6. Violation Reporting + Auto-Revocation")

    # Create a bot and certify it
    bad_bot = SearchBot("ViolatorBot", bica, ca=ca)
    ca.certify(
        identity=bad_bot.identity,
        level=CertLevel.STANDARD,
    )

    print(f"\n  Reporting violations for {bad_bot.name}...")
    ca.report_violation(bad_bot.bot_id, "Sent spam messages")
    ca.report_violation(bad_bot.bot_id, "Attempted to access restricted data")
    ca.report_violation(bad_bot.bot_id, "Impersonated a Community Bot")

    cert = ca.get_cert(bad_bot.bot_id)
    print(f"\n  Certificate valid: {cert.valid}  ← auto-revoked after 3 violations ✅")

    # Try to handshake with revoked bot
    print(f"\n  Trying handshake with revoked bot...")
    try:
        community_bot.connect(bad_bot)
        print("  Handshake succeeded (unexpected)")
    except HandshakeError as e:
        print(f"  ❌ Handshake blocked: {e}  ← correct ✅")

    # ── 7. Certification stats ───────────────────────────────────────
    section("7. Certification Authority Stats")

    stats = ca.stats()
    print(f"\n  Total issued    : {stats['total_issued']}")
    print(f"  Total revoked   : {stats['total_revoked']}")
    print(f"  Total violations: {stats['total_violations']}")
    print(f"\n  By tier:")
    for level, count in stats["by_level"].items():
        badge = {"COMMUNITY": "🟢", "STANDARD": "🔵", "RESTRICTED": "🟡", "NONE": "⚪"}
        print(f"    {badge.get(level,'?')} {level:<12} : {count}")

    print(f"\n  Community Bots:")
    for cert in ca.list_certified(CertLevel.COMMUNITY):
        print(f"    {cert}")

    print(f"\n  Standard Bots:")
    for cert in ca.list_certified(CertLevel.STANDARD):
        print(f"    {cert}")

    # ── Summary ──────────────────────────────────────────────────────
    section("Community Bot Certification — Summary")
    print("""
  🟢 COMMUNITY  — Full access, ethical declaration required
  🔵 STANDARD   — Public data only, no private access
  🟡 RESTRICTED — Read-only, must connect via Community Bot

  ✅ 3-tier certification system
  ✅ Per-tier permission rules
  ✅ Trust compatibility enforced in handshake
  ✅ Ethical declaration required for Community tier
  ✅ Violation reporting + auto-revocation (3 strikes)
  ✅ Revoked bots blocked from handshake
    """)


if __name__ == "__main__":
    main()
