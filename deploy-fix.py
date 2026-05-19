#!/usr/bin/env python3
"""
Deploy the Boomi fix to the production server
Run: python3 deploy-fix.py
"""

import subprocess
import sys
import os

def run_command(cmd, description=""):
    """Run a shell command and return output"""
    if description:
        print(f"\n{description}")
    print(f"$ {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Deploying Boomi fix to production server...")
    print("=" * 60)
    
    # Configuration
    key_path = r"C:\Users\Burhan Yanbolu\Desktop\tbn-protocol\aws-lightsail.pem"
    server = "ubuntu@3.11.229.68"
    
    # Check if key exists
    if not os.path.exists(key_path):
        print(f"❌ SSH key not found: {key_path}")
        return False
    
    print(f"✅ SSH key found: {key_path}")
    
    # Create the fix script content
    fix_script = '''#!/bin/bash
cd /opt/tbn-protocol

# Backup
cp api/routes.py api/routes.py.backup.$(date +%s)
echo "✅ Backup created"

# Apply fix
python3 << 'PYEOF'
with open('api/routes.py', 'r') as f:
    content = f.read()

# Fix the violations section
old = """    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        return {"""

new = """    elif query_type == "violations":
        # Get violations from governance engine
        violations = []
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]
        return {"""

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
'''
    
    # Write fix script to temp file
    temp_script = "/tmp/fix-boomi.sh"
    print(f"\n📝 Creating fix script...")
    
    # Use SSH to create and run the script directly
    print(f"\n🔗 Connecting to {server}...")
    
    # Create the command that will be run on the server
    server_cmd = f'''ssh -i "{key_path}" {server} 'bash -s' << 'BASHEOF'
{fix_script}
BASHEOF
'''
    
    # Run it
    if run_command(server_cmd, "🚀 Deploying fix..."):
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Boomi integration fix deployed!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ Deployment failed")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
