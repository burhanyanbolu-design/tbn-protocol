import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

# The correct blog nginx config
correct_config = """server {

    server_name blog.hardinai.co.uk;

    root /var/www/blog;

    index index.html;

    location /admin {
        proxy_pass http://127.0.0.1:5007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {

        try_files $uri $uri/ =404;

    }



    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/blog.hardinai.co.uk/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/blog.hardinai.co.uk/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}

server {
    if ($host = blog.hardinai.co.uk) {
        return 301 https://$host$request_uri;
    } # managed by Certbot



    listen 80;

    server_name blog.hardinai.co.uk;
    return 404; # managed by Certbot


}
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Write fixed config via SFTP
    print("\n1. Writing fixed blog config...")
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/blog_fixed.conf', 'w') as f:
        f.write(correct_config)
    sftp.close()

    # Copy to nginx
    print("2. Copying to nginx sites-available...")
    stdin, stdout, stderr = ssh.exec_command('sudo cp /tmp/blog_fixed.conf /etc/nginx/sites-available/blog.hardinai.co.uk')
    stdout.read()
    print("✓ Done")

    # Test nginx
    print("\n3. Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command('sudo nginx -t 2>&1')
    result = stdout.read().decode()
    print(result)

    if 'successful' in result:
        print("4. Reloading nginx...")
        stdin, stdout, stderr = ssh.exec_command('sudo systemctl reload nginx 2>&1')
        print(stdout.read().decode())
        print("✓ Nginx reloaded!")
        print("\n✓ All fixed! Now run: python test_certification_api.py")
    else:
        print("✗ Config test failed")

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
