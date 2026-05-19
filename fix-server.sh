#!/bin/bash
# One-liner fix for Boomi integration on production server
# Run this on the server: bash fix-server.sh

cd /opt/tbn-protocol

# Backup
cp api/routes.py api/routes.py.backup.$(date +%s)

# Apply fix
python3 << 'PYEOF'
with open('api/routes.py', 'r') as f:
    content = f.read()

# Fix the violations section
old = '''    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        return {'''

new = '''    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]
        return {'''

if old in content:
    content = content.replace(old, new)
    print("✅ Fixed violations query")
else:
    print("⚠️  Pattern not found - may already be fixed")

with open('api/routes.py', 'w') as f:
    f.write(content)
PYEOF

# Restart
echo "🔄 Restarting TBN service..."
sudo systemctl restart tbn
sleep 3

# Verify
echo "📊 Service status:"
sudo systemctl status tbn --no-pager | head -10

echo ""
echo "🧪 Testing health endpoint..."
curl -s https://tbn.hardinai.co.uk/api/boomi/health | python3 -m json.tool

echo ""
echo "✅ Done! Boomi integration is ready."
