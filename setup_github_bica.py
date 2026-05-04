import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

# GitHub configuration
github_token = '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'
github_repo = 'burhanyanbolu-design/tbn-bica-registry'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Check if .env file exists
    print("\n1. Checking environment configuration...")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/.env 2>/dev/null || echo "# TBN Environment"')
    env_content = stdout.read().decode()
    print("Current .env content:")
    print(env_content)

    # Add GitHub configuration to .env
    print("\n2. Adding GitHub BICA configuration...")
    
    # Remove any existing GitHub config lines
    env_lines = [line for line in env_content.split('\n') 
                 if not line.startswith('TBN_GITHUB_TOKEN=') 
                 and not line.startswith('TBN_GITHUB_REPO=')
                 and not line.startswith('TBN_USE_GITHUB_BICA=')]
    
    # Add new config
    env_lines.extend([
        '',
        '# GitHub BICA Registry',
        f'TBN_GITHUB_TOKEN={github_token}',
        f'TBN_GITHUB_REPO={github_repo}',
        'TBN_USE_GITHUB_BICA=true',
        ''
    ])
    
    new_env = '\n'.join(env_lines)
    
    # Write via SFTP
    sftp = ssh.open_sftp()
    with sftp.file('/opt/tbn-protocol/.env', 'w') as f:
        f.write(new_env)
    sftp.close()
    print("✓ GitHub configuration added to .env")

    # Test GitHub access
    print("\n3. Testing GitHub API access...")
    test_cmd = f'''
cd /opt/tbn-protocol
python3 << 'PYEOF'
import requests
token = "{github_token}"
repo = "{github_repo}"
headers = {{"Authorization": f"Bearer {{token}}"}}
response = requests.get(f"https://api.github.com/repos/{{repo}}", headers=headers)
if response.status_code == 200:
    print(f"✓ GitHub API access successful")
    print(f"  Repo: {{response.json()['full_name']}}")
    print(f"  Visibility: {{response.json()['visibility']}}")
else:
    print(f"✗ GitHub API error: {{response.status_code}}")
    print(response.text)
PYEOF
'''
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    print(stdout.read().decode())
    error = stderr.read().decode()
    if error:
        print("Errors:", error)

    # Migrate existing bots to GitHub
    print("\n4. Migrating existing bots to GitHub...")
    migrate_cmd = f'''
cd /opt/tbn-protocol
python3 << 'PYEOF'
import json
import requests
from datetime import datetime, timezone

token = '{github_token}'
repo = '{github_repo}'
headers = {{
    "Authorization": f"Bearer {{token}}",
    "Accept": "application/vnd.github.v3+json"
}}

def push_file(path, content, message):
    import base64
    url = f"https://api.github.com/repos/{{repo}}/contents/{{path}}"
    # Check if file exists
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {{
        "message": message,
        "content": base64.b64encode(content.encode()).decode()
    }}
    if sha:
        payload["sha"] = sha
    
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

# Load local registry
with open('data/bica_registry.json', 'r') as f:
    local_registry = json.load(f)

bot_entries = {{k: v for k, v in local_registry.items() 
               if isinstance(v, dict) and 'bot_id' in v}}

print(f"Found {{len(bot_entries)}} bots to migrate")

success = 0
for bot_id, bot_data in bot_entries.items():
    try:
        cert = {{
            "bot_id": bot_data['bot_id'],
            "name": bot_data['name'],
            "public_key_pem": bot_data['public_key_pem'],
            "cert_level": bot_data.get('cert_level', 'STANDARD'),
            "created_at": bot_data.get('created_at', datetime.now(timezone.utc).isoformat()),
            "tbn_version": bot_data.get('tbn_version', '0.1.0'),
            "purpose": bot_data.get('purpose', ''),
            "capabilities": bot_data.get('capabilities', [])
        }}
        
        path = f"registry/bots/{{bot_data['bot_id']}}.json"
        if push_file(path, json.dumps(cert, indent=2), f"Register bot: {{bot_data['name']}}"):
            print(f"  ✓ Migrated: {{bot_data['name']}} ({{bot_id}})")
            success += 1
        else:
            print(f"  ✗ Failed: {{bot_id}}")
    except Exception as e:
        print(f"  ✗ Error {{bot_id}}: {{e}}")

# Create stats file
stats = {{
    "total_bots": len(bot_entries),
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "network": "TBN Protocol",
    "version": "0.1.0"
}}
push_file("registry/stats.json", json.dumps(stats, indent=2), "Update network stats")

# Create README
readme = f"""# TBN BICA Registry

**Trusted Bot Network — Bot Identity & Certification Authority**

This repository serves as the public, verifiable registry for all bots on the TBN Protocol network.

## Network Statistics
- **Total Bots**: {{len(bot_entries)}}
- **Last Updated**: {{datetime.now(timezone.utc).strftime('%Y-%m-%d')}}

## Certification Levels
- 🟢 **COMMUNITY** — Full network access
- 🔵 **STANDARD** — Public data access  
- 🟡 **RESTRICTED** — Read-only access

## Verify a Bot
Each bot certificate is stored in `registry/bots/<bot_id>.json`

## Links
- [TBN Protocol Dashboard](https://tbn.hardinai.co.uk)
- [Certification Portal](https://tbn.hardinai.co.uk/certification/portal)
- [PyPI Package](https://pypi.org/project/tbn-protocol/)
- [Hardin AI Solutions](https://hardinai.co.uk)

---
*© 2026 Hardin Enterprises Ltd (trading as Hardin AI Solutions)*
"""
push_file("README.md", readme, "Update registry README")

print(f"\\n✓ Migration complete! {{success}}/{{len(bot_entries)}} bots migrated")
print(f"View: https://github.com/{{repo}}")
PYEOF
'''
    stdin, stdout, stderr = ssh.exec_command(migrate_cmd)
    print(stdout.read().decode())
    error = stderr.read().decode()
    if error and 'warning' not in error.lower():
        print("Errors:", error)

    # Restart service
    print("\n5. Restarting TBN service...")
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart tbn')
    stdout.read()
    print("✓ Service restarted with GitHub BICA enabled")

    ssh.close()

    print("\n" + "="*60)
    print("GitHub BICA Registry Setup Complete!")
    print("="*60)
    print(f"Registry URL: https://github.com/{github_repo}")
    print("\nAll future bot registrations will be stored on GitHub.")
    print("Existing bots have been migrated to the GitHub registry.")
    print("="*60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
