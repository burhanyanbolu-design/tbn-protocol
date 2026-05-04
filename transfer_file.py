import paramiko
import os

# Files to transfer
files_to_transfer = [
    ('api/certification.py', '/opt/tbn-protocol/api/certification.py'),
    ('api/templates/certification_portal.html', '/opt/tbn-protocol/api/templates/certification_portal.html'),
    ('server.py', '/opt/tbn-protocol/server.py'),
    ('tbn/github_bica.py', '/opt/tbn-protocol/tbn/github_bica.py'),
]

# SSH connection details
hostname = '3.11.229.68'
username = 'ubuntu'
port = 22

# Connect and transfer
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Use the PEM key file
key_path = 'aws-lightsail.pem'

try:
    print(f"Connecting to {hostname} using key: {key_path}")
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)
    
    # Use SFTP to write the files
    sftp = ssh.open_sftp()
    
    for local_path, remote_path in files_to_transfer:
        print(f"\nTransferring {local_path}...")
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(content)
        
        print(f"✓ Transferred to {remote_path}")
        print(f"✓ File size: {len(content)} bytes")
    
    print("\n" + "="*60)
    print("All files transferred successfully!")
    print("Now restart the service on the server:")
    print("  sudo systemctl restart tbn")
    print("="*60)
    
    sftp.close()
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("\nAlternative: Use SCP command:")
    print(f'scp "api/templates/certification_portal.html" ubuntu@3.11.229.68:/opt/tbn-protocol/api/templates/')
