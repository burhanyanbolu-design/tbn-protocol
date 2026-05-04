import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Check if sendmail/postfix is available
    print("=== Email tools ===")
    stdin, stdout, stderr = ssh.exec_command('which sendmail postfix msmtp 2>/dev/null; echo "done"')
    print(stdout.read().decode())

    # Check Python email libraries
    print("=== Python email libs ===")
    stdin, stdout, stderr = ssh.exec_command('python3 -c "import smtplib; print(\'smtplib: ok\')"')
    print(stdout.read().decode())

    # Check if .env has any email config
    print("=== Current .env ===")
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/.env')
    print(stdout.read().decode())

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
