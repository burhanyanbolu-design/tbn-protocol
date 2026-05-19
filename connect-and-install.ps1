# Hardin-AI Phone - Connect to Ubuntu Server and Install Asterisk
# Date: May 12, 2026

$ServerIP = "3.11.229.68"
$SSHUser = "ubuntu"
$SSHKeyPath = ".\.ssh_temp_key"
$InstallScriptPath = ".\install-asterisk.sh"

Write-Host "=========================================="
Write-Host "Hardin-AI Phone - Asterisk Installation"
Write-Host "=========================================="
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSHKeyPath)) {
    Write-Host "❌ SSH key not found at: $SSHKeyPath"
    exit 1
}

# Fix SSH key permissions (Windows)
Write-Host "[1/4] Setting SSH key permissions..."
icacls $SSHKeyPath /inheritance:r /grant:r "$($env:USERNAME):(F)" | Out-Null

# Copy installation script to server
Write-Host "[2/4] Copying installation script to server..."
scp -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    $InstallScriptPath "${SSHUser}@${ServerIP}:/tmp/install-asterisk.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to copy script to server"
    exit 1
}

# SSH into server and run installation
Write-Host "[3/4] Connecting to server and running installation..."
Write-Host "Server: $ServerIP"
Write-Host "User: $SSHUser"
Write-Host ""

ssh -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    "${SSHUser}@${ServerIP}" `
    "chmod +x /tmp/install-asterisk.sh && /tmp/install-asterisk.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Installation failed"
    exit 1
}

# Verify installation
Write-Host "[4/4] Verifying installation..."
ssh -i $SSHKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `
    "${SSHUser}@${ServerIP}" `
    "asterisk -r -x 'core show version'"

Write-Host ""
Write-Host "=========================================="
Write-Host "✅ Asterisk Installation Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. SSH into server: ssh -i .\.ssh_temp_key ubuntu@$ServerIP"
Write-Host "2. Edit SIP config: sudo nano /etc/asterisk/sip.conf"
Write-Host "3. Update Vodafone credentials"
Write-Host "4. Restart Asterisk: sudo systemctl restart asterisk"
Write-Host "5. Check status: asterisk -r -x 'sip show peers'"
Write-Host ""
