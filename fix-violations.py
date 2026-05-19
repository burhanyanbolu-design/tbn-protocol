#!/usr/bin/env python3
"""Fix violations query on remote server"""
import subprocess
import sys

key_path = r"C:\Users\Burhan Yanbolu\Desktop\tbn-protocol\aws-lightsail.pem"
server = "ubuntu@3.11.229.68"

# Create the Python fix script
fix_script = """
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

content = content.replace(old, new)

with open('api/routes.py', 'w') as f:
    f.write(content)

print('✅ Fixed violations query!')
"""

# Execute on remote server
cmd = [
    "ssh",
    "-i", key_path,
    server,
    f"cd /opt/tbn-protocol && python3 << 'PYEOF'\n{fix_script}\nPYEOF"
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
