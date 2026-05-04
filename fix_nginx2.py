import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Check the blog config for duplicate /admin
    print("\n1. Checking blog nginx config...")
    stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/blog.hardinai.co.uk')
    blog_config = stdout.read().decode()
    print(blog_config)

    # Fix duplicate /admin in blog config
    print("\n2. Fixing duplicate /admin in blog config...")
    lines = blog_config.split('\n')
    seen_admin = False
    new_lines = []
    for line in lines:
        if 'location /admin' in line:
            if seen_admin:
                # Skip this duplicate block - find its closing brace
                print(f"  Skipping duplicate: {line}")
                continue
            seen_admin = True
        new_lines.append(line)
    
    new_blog_config = '\n'.join(new_lines)
    
    # Write fixed blog config
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/blog_nginx.conf', 'w') as f:
        f.write(new_blog_config)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('sudo cp /tmp/blog_nginx.conf /etc/nginx/sites-available/blog.hardinai.co.uk')
    stdout.read()
    print("✓ Blog config updated")

    # Test nginx config
    print("\n3. Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command('sudo nginx -t 2>&1')
    test_result = stdout.read().decode()
    print(test_result)

    if 'successful' in test_result:
        print("\n4. Reloading nginx...")
        stdin, stdout, stderr = ssh.exec_command('sudo systemctl reload nginx')
        stdout.read()
        print("✓ Nginx reloaded successfully!")
    else:
        print("Still failing - trying force reload anyway...")
        stdin, stdout, stderr = ssh.exec_command('sudo systemctl reload nginx 2>&1')
        result = stdout.read().decode()
        print(result)

    # Check current tbn config
    print("\n5. Verifying tbn config has no auth_basic...")
    stdin, stdout, stderr = ssh.exec_command('grep -n "auth_basic" /etc/nginx/sites-available/tbn')
    result = stdout.read().decode()
    print(result if result else "✓ No active auth_basic found in tbn config")

    ssh.close()
    print("\n" + "="*60)
    print("Done! Now run: python test_certification_api.py")
    print("="*60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
