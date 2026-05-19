import paramiko

hostname = '3.11.229.68'
username = 'ubuntu'
port = 22
key_path = 'aws-lightsail.pem'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname, port=port, username=username, key_filename=key_path)

    # Read current .env
    stdin, stdout, stderr = ssh.exec_command('cat /opt/tbn-protocol/.env')
    env_content = stdout.read().decode()

    # Remove duplicate GitHub lines and add email config
    lines = env_content.split('\n')
    seen = set()
    clean_lines = []
    for line in lines:
        key = line.split('=')[0].strip()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        clean_lines.append(line)

    # Add email config if not present
    if 'TBN_EMAIL_USER' not in env_content:
        clean_lines.extend([
            '',
            '# Email Notifications',
            'TBN_EMAIL_USER=burhanyanbolu@gmail.com',
            'TBN_EMAIL_PASS=bfrxbotiropa ejtx',
            'TBN_NOTIFY_EMAIL=burhan@hardinai.co.uk',
            ''
        ])

    new_env = '\n'.join(clean_lines)

    sftp = ssh.open_sftp()
    with sftp.file('/opt/tbn-protocol/.env', 'w') as f:
        f.write(new_env)
    sftp.close()
    print("✓ Email config added to .env")

    # Test email
    print("\nTesting email...")
    test_cmd = '''
cd /opt/tbn-protocol
python3 << 'PYEOF'
import os
os.environ['TBN_EMAIL_USER'] = 'burhanyanbolu@gmail.com'
os.environ['TBN_EMAIL_PASS'] = 'bfrxbotiropa ejtx'
os.environ['TBN_NOTIFY_EMAIL'] = 'burhan@hardinai.co.uk'

from tbn.notifications import send_email

result = send_email(
    subject="[TBN] ✅ Email Notifications Active",
    html_body="<h2 style='color:#3fb950'>TBN Protocol email notifications are now active!</h2><p>You will receive alerts for violations, certifications, and new bot registrations.</p>",
    text_body="TBN Protocol email notifications are now active!"
)
print(f"Email sent: {result}")
PYEOF
'''
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("Errors:", err)

    ssh.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
