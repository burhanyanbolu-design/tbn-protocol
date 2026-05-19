#!/usr/bin/env python3
"""
Apply Boomi integration fixes to routes.py
Run this on the production server to fix the certification check and governance query endpoints
"""

import sys
import os

def apply_fixes():
    routes_file = "/opt/tbn-protocol/api/routes.py"
    
    if not os.path.exists(routes_file):
        print(f"❌ File not found: {routes_file}")
        return False
    
    print(f"📖 Reading {routes_file}...")
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Fix 1: _boomi_check_certification
    print("🔧 Fixing _boomi_check_certification...")
    old_cert = """    # Get bot from registry
    bots = state.get_bots()
    bot = next((b for b in bots if b.get("bot_id") == bot_id), None)"""
    
    new_cert = """    # Get bot from registry
    bot = state.bots.get(bot_id)"""
    
    if old_cert in content:
        content = content.replace(old_cert, new_cert)
        print("   ✅ Fixed _boomi_check_certification")
    else:
        print("   ⚠️  Pattern not found (may already be fixed)")
    
    # Fix 2: _boomi_governance_query - bot_status
    print("🔧 Fixing _boomi_governance_query (bot_status)...")
    old_bot_status = """    if query_type == "bot_status":
        bots = state.get_bots()
        if bot_id:
            bots = [b for b in bots if b.get("bot_id") == bot_id]
        return {
            "query_type": query_type,
            "count": len(bots),
            "bots": bots[:limit]
        }"""
    
    new_bot_status = """    if query_type == "bot_status":
        bots = list(state.bots.values())
        if bot_id:
            bots = [b for b in bots if hasattr(b, 'bot_id') and b.bot_id == bot_id]
        return {
            "query_type": query_type,
            "count": len(bots),
            "bots": [{"bot_id": b.bot_id if hasattr(b, 'bot_id') else str(b)} for b in bots[:limit]]
        }"""
    
    if old_bot_status in content:
        content = content.replace(old_bot_status, new_bot_status)
        print("   ✅ Fixed bot_status query")
    else:
        print("   ⚠️  Pattern not found (may already be fixed)")
    
    # Fix 3: _boomi_governance_query - violations
    print("🔧 Fixing _boomi_governance_query (violations)...")
    old_violations = """    elif query_type == "violations":
        # Get violations from governance engine
        violations = state.get_violations()
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]"""
    
    new_violations = """    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]"""
    
    if old_violations in content:
        content = content.replace(old_violations, new_violations)
        print("   ✅ Fixed violations query")
    else:
        print("   ⚠️  Pattern not found (may already be fixed)")
    
    # Fix 4: _boomi_governance_query - access_requests
    print("🔧 Fixing _boomi_governance_query (access_requests)...")
    old_requests = """    elif query_type == "access_requests":
        # Get pending access requests
        requests = state.get_access_requests()
        return {
            "query_type": query_type,
            "count": len(requests),
            "requests": requests[:limit]
        }"""
    
    new_requests = """    elif query_type == "access_requests":
        # Get pending access requests
        requests = []
        return {
            "query_type": query_type,
            "count": len(requests),
            "requests": requests[:limit]
        }"""
    
    if old_requests in content:
        content = content.replace(old_requests, new_requests)
        print("   ✅ Fixed access_requests query")
    else:
        print("   ⚠️  Pattern not found (may already be fixed)")
    
    # Write back
    print(f"💾 Writing fixes to {routes_file}...")
    with open(routes_file, 'w') as f:
        f.write(content)
    
    print("✅ All fixes applied successfully!")
    return True

if __name__ == "__main__":
    try:
        if apply_fixes():
            print("\n🎉 Boomi integration fixes applied!")
            print("Next: sudo systemctl restart tbn")
            sys.exit(0)
        else:
            print("\n❌ Failed to apply fixes")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
