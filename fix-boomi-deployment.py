#!/usr/bin/env python3
"""
Fix the Boomi integration deployment on the server.
This script:
1. Adds the missing datetime import
2. Restarts the TBN service
3. Tests the health endpoint
"""

import subprocess
import sys

# Server details
SERVER_IP = "3.11.229.68"
SERVER_USER = "ubuntu"
SSH_KEY = "aws-lightsail.pem"
PROJECT_PATH = "/opt/tbn-protocol"

def run_ssh_command(command):
    """Run a command on the server via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, f"{SERVER_USER}@{SERVER_IP}", command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    print("🚀 Fixing Boomi Integration Deployment")
    print("=" * 60)
    
    # Step 1: Check if datetime import exists
    print("\n1️⃣  Checking for datetime import...")
    code, stdout, stderr = run_ssh_command(
        f"grep 'from datetime import' {PROJECT_PATH}/api/routes.py"
    )
    
    if code == 0:
        print("✅ datetime import already exists")
    else:
        print("❌ datetime import missing, adding it...")
        
        # Add the import after "import os"
        fix_command = f"""
cd {PROJECT_PATH}
cp api/routes.py api/routes.py.backup2
python3 << 'PYTHON_EOF'
with open('api/routes.py', 'r') as f:
    lines = f.readlines()

# Find the line with "import os" and add datetime import after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if line.strip() == 'import os' and i < 10:  # Should be near the top
        new_lines.append('from datetime import datetime, timezone\\n')

with open('api/routes.py', 'w') as f:
    f.writelines(new_lines)
print('✅ Added datetime import')
PYTHON_EOF
"""
        code, stdout, stderr = run_ssh_command(fix_command)
        if code != 0:
            print(f"❌ Error adding import: {stderr}")
            return False
        print(stdout)
    
    # Step 2: Restart the service
    print("\n2️⃣  Restarting TBN service...")
    code, stdout, stderr = run_ssh_command("sudo systemctl restart tbn")
    if code != 0:
        print(f"❌ Error restarting service: {stderr}")
        return False
    print("✅ Service restarted")
    
    # Step 3: Wait for service to start
    print("\n3️⃣  Waiting for service to start...")
    import time
    time.sleep(3)
    
    # Step 4: Test the health endpoint
    print("\n4️⃣  Testing health endpoint...")
    code, stdout, stderr = run_ssh_command(
        "curl -s https://tbn.hardinai.co.uk/api/boomi/health"
    )
    
    if code == 0 and "healthy" in stdout:
        print("✅ Health check passed!")
        print(f"\nResponse:\n{stdout}")
        return True
    else:
        print(f"❌ Health check failed")
        print(f"Response: {stdout}")
        print(f"Error: {stderr}")
        
        # Show service status
        print("\n5️⃣  Checking service status...")
        code, stdout, stderr = run_ssh_command("sudo systemctl status tbn")
        print(stdout)
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("🎉 Boomi integration deployed successfully!")
        sys.exit(0)
    else:
        print("❌ Deployment failed. Check the errors above.")
        sys.exit(1)
