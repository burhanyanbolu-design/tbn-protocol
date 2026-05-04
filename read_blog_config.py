import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    stdin, stdout, stderr = ssh.exec_command('cat -n /etc/nginx/sites-available/blog.hardinai.co.uk')
    content = stdout.read().decode()
    print(content)

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
