# Verify Asterisk Installation
# Date: May 12, 2026

$ServerIP = "3.11.229.68"
$SSHUser = "ubuntu"
$SSHKeyPath = ".\.ssh_temp_key"

Write-Host "=========================================="
Write-Host "Verifying Asterisk Installation"
Write-Host "=========================================="
Write-Host ""

# Check Asterisk version
Write-Host "[1/3] Checking Asterisk version..."
ssh -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    "${SSHUser}@${ServerIP}" `
    "asterisk -V"

Write-Host ""

# Check Asterisk service status
Write-Host "[2/3] Checking Asterisk service status..."
ssh -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    "${SSHUser}@${ServerIP}" `
    "sudo systemctl status asterisk"

Write-Host ""

# Check SIP configuration
Write-Host "[3/3] Checking SIP configuration..."
ssh -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    "${SSHUser}@${ServerIP}" `
    "cat /etc/asterisk/sip.conf | grep -A 10 '\[vodafone-trunk\]'"

Write-Host ""
Write-Host "=========================================="
Write-Host "✅ Verification Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. SSH into server: ssh -i .\.ssh_temp_key ubuntu@$ServerIP"
Write-Host "2. Edit SIP config: sudo nano /etc/asterisk/sip.conf"
Write-Host "3. Update Vodafone credentials"
Write-Host "4. Restart Asterisk: sudo systemctl restart asterisk"
Write-Host ""
