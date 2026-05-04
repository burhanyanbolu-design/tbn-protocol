import paramiko
import json

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Check registry file raw content
    print("=== bica_registry.json ===")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/data/bica_registry.json')
    print(stdout.read().decode())

    # Check all data files
    print("\n=== Data directory ===")
    stdin, stdout, stderr = ssh.exec_command('ls -la /opt/tbn-protocol/data/')
    print(stdout.read().decode())

    # Check certification log
    print("\n=== certification_log.json ===")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/data/certification_log.json 2>/dev/null || echo "Not found"')
    print(stdout.read().decode())

    # Check violations
    print("\n=== violations.json ===")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/data/violations.json 2>/dev/null || echo "Not found"')
    print(stdout.read().decode())

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
