import paramiko

# SSH connection details
hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

# Connect
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)
    
    # Find the active nginx config
    print("\n1. Finding active nginx config...")
    stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/')
    print(stdout.read().decode())
    
    # Check for tbn config
    print("\n2. Checking tbn nginx config...")
    stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/tbn')
    config_content = stdout.read().decode()
    print(config_content)
    
    # Check if auth_basic is active (not commented out)
    lines = config_content.split('\n')
    has_active_auth = any('auth_basic' in line and not line.strip().startswith('#') for line in lines)
    
    if has_active_auth:
        print("\n3. Found active auth_basic. Commenting it out...")
        
        # Comment out auth_basic lines
        new_lines = []
        for line in lines:
            if 'auth_basic' in line and not line.strip().startswith('#'):
                new_lines.append('        # ' + line.strip())
            else:
                new_lines.append(line)
        new_config = '\n'.join(new_lines)
        
        # Write new config via sftp
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/tbn_nginx.conf', 'w') as f:
            f.write(new_config)
        sftp.close()
        
        # Copy to nginx config (requires sudo)
        print("\n4. Updating nginx config...")
        stdin, stdout, stderr = ssh.exec_command('sudo cp /tmp/tbn_nginx.conf /etc/nginx/sites-available/tbn')
        stdout.read()
        
        # Test nginx config
        print("\n5. Testing nginx config...")
        stdin, stdout, stderr = ssh.exec_command('sudo nginx -t 2>&1')
        test_result = stdout.read().decode()
        print(test_result)
        
        if 'successful' in test_result:
            print("\n6. Reloading nginx...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl reload nginx')
            stdout.read()
            print("✓ Nginx reloaded successfully!")
        else:
            print("✗ Nginx config test failed. Not reloading.")
    else:
        print("\n✓ No active auth_basic found.")
    
    ssh.close()
    print("\n" + "="*60)
    print("Done! Try running the API tests again:")
    print("  python test_certification_api.py")
    print("="*60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
