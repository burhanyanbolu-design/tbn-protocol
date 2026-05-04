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

    # Read the current broken blog config
    print("\n1. Reading current blog config...")
    stdin, stdout, stderr = ssh.exec_command('cat -n /etc/nginx/sites-available/blog.hardinai.co.uk')
    print(stdout.read().decode())

    # Read the original from sites-available backup or reconstruct
    print("\n2. Restoring blog config from git or backup...")
    stdin, stdout, stderr = ssh.exec_command('ls /etc/nginx/sites-available/')
    print(stdout.read().decode())

    # Check if there's a backup
    stdin, stdout, stderr = ssh.exec_command('ls /etc/nginx/sites-available/blog* 2>/dev/null')
    print(stdout.read().decode())

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
