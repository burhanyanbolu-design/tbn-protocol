import paramiko
import json

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Read current registry
    print("\n1. Reading current BICA registry...")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/data/bica_registry.json')
    registry_content = stdout.read().decode()
    registry = json.loads(registry_content)

    # The bots are stored at top level (not inside a "bots" key)
    # Find all bot entries (they have bot_id fields)
    bot_entries = {k: v for k, v in registry.items() 
                   if isinstance(v, dict) and 'bot_id' in v}
    
    print(f"Total bots found: {len(bot_entries)}")
    print("\nCurrent bots:")
    for bot_id, bot in bot_entries.items():
        print(f"  - {bot_id}: {bot.get('name', 'Unknown')} [{bot.get('cert_level', 'STANDARD')}]")

    # Find test bots
    test_bot_ids = [bot_id for bot_id, bot in bot_entries.items()
                    if 'test' in bot.get('name', '').lower() or
                       'test' in bot_id.lower()]

    print(f"\n2. Found {len(test_bot_ids)} test bots to remove:")
    for bot_id in test_bot_ids:
        print(f"  Removing: {bot_id}: {registry[bot_id].get('name', 'Unknown')}")
        del registry[bot_id]

    # Write cleaned registry back
    cleaned_json = json.dumps(registry, indent=2)
    sftp = ssh.open_sftp()
    with sftp.file('/opt/tbn-protocol/data/bica_registry.json', 'w') as f:
        f.write(cleaned_json)
    sftp.close()
    print(f"\n✓ Registry cleaned - {len(test_bot_ids)} test bots removed")

    # Verify
    remaining = {k: v for k, v in registry.items() 
                 if isinstance(v, dict) and 'bot_id' in v}
    print(f"✓ Remaining bots: {len(remaining)}")
    for bot_id, bot in remaining.items():
        print(f"  - {bot_id}: {bot.get('name', 'Unknown')} [{bot.get('cert_level', 'STANDARD')}]")

    # Restart service
    print("\n3. Restarting TBN service...")
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart tbn')
    stdout.read()
    print("✓ Service restarted")

    ssh.close()

    print("\n" + "="*60)
    print("Cleanup complete!")
    print("Visit https://tbn.hardinai.co.uk/certification/portal")
    print("="*60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
