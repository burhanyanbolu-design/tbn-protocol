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
    
    print(f"Total bots before cleanup: {len(registry.get('bots', {}))}")
    
    # Show all bots
    bots = registry.get('bots', {})
    print("\nCurrent bots:")
    for bot_id, bot in bots.items():
        print(f"  - {bot_id}: {bot.get('name', 'Unknown')}")
    
    # Remove test bots (any bot with "Test Bot" in the name)
    test_bot_ids = [bot_id for bot_id, bot in bots.items() 
                    if 'test' in bot.get('name', '').lower() or 
                       'test' in bot_id.lower()]
    
    print(f"\n2. Found {len(test_bot_ids)} test bots to remove:")
    for bot_id in test_bot_ids:
        print(f"  - {bot_id}: {bots[bot_id].get('name', 'Unknown')}")
        del bots[bot_id]
    
    print(f"\nTotal bots after cleanup: {len(bots)}")
    
    # Write cleaned registry back
    registry['bots'] = bots
    cleaned_json = json.dumps(registry, indent=2)
    
    # Transfer via SFTP
    sftp = ssh.open_sftp()
    with sftp.file('/opt/tbn-protocol/data/bica_registry.json', 'w') as f:
        f.write(cleaned_json)
    sftp.close()
    print("\n✓ Registry cleaned and saved")
    
    # Also clean certification log if it exists
    print("\n3. Cleaning certification log...")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/data/certification_log.json 2>/dev/null || echo "[]"')
    cert_log_content = stdout.read().decode()
    cert_log = json.loads(cert_log_content)
    
    # Remove test bot entries
    cleaned_log = [entry for entry in cert_log 
                   if not any(test_id in entry.get('bot_id', '') for test_id in test_bot_ids)]
    
    sftp = ssh.open_sftp()
    with sftp.file('/opt/tbn-protocol/data/certification_log.json', 'w') as f:
        f.write(json.dumps(cleaned_log, indent=2))
    sftp.close()
    print(f"✓ Removed {len(cert_log) - len(cleaned_log)} test entries from certification log")
    
    # Restart service
    print("\n4. Restarting TBN service...")
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart tbn')
    stdout.read()
    print("✓ Service restarted")
    
    ssh.close()
    
    print("\n" + "="*60)
    print("Cleanup complete!")
    print("Visit https://tbn.hardinai.co.uk/certification/portal")
    print("to see the clean registry.")
    print("="*60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
