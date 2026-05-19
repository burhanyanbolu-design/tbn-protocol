#!/usr/bin/env python3
"""
SSH into the production server and apply the Boomi fix
"""

import paramiko
import sys

def main():
    # SSH connection details
    hostname = "3.11.229.68"
    username = "ubuntu"
    key_path = r"C:\Users\Burhan Yanbolu\Desktop\tbn-protocol\aws-lightsail.pem"
    
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect
        print(f"🔗 Connecting to {hostname}...")
        client.connect(hostname, username=username, key_filename=key_path, timeout=10)
        print("✅ Connected!")
        
        # Run the fix command
        fix_cmd = """cd /opt/tbn-protocol && python3 << 'PYEOF'
with open('api/routes.py', 'r') as f:
    content = f.read()

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
    print("⚠️  Pattern not found")

with open('api/routes.py', 'w') as f:
    f.write(content)
PYEOF
"""
        
        print("\n🔧 Applying fix...")
        stdin, stdout, stderr = client.exec_command(fix_cmd)
        output = stdout.read().decode()
        print(output)
        if stderr:
            err = stderr.read().decode()
            if err:
                print("Errors:", err)
        
        # Restart service
        print("\n🔄 Restarting TBN service...")
        stdin, stdout, stderr = client.exec_command("sudo systemctl restart tbn && sleep 3")
        stdout.read()
        
        # Verify
        print("\n✅ Verifying...")
        stdin, stdout, stderr = client.exec_command("curl -s https://tbn.hardinai.co.uk/api/boomi/health")
        result = stdout.read().decode()
        print(result)
        
        client.close()
        print("\n✅ Done! Boomi integration is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
