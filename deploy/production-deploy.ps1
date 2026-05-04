# TBN Protocol — Production Deployment (PowerShell)
# Enhanced deployment script for Windows
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File deploy/production-deploy.ps1
#
# This script:
# 1. Deploys to your existing server (3.11.229.68)
# 2. Sets up distributed TBN network nodes
# 3. Configures GitHub-backed BICA registry
# 4. Enables certification portal

# Configuration from server-info.md
$SERVER_IP = "3.11.229.68"
$SERVER_USER = "ubuntu"
$APP_DIR = "/opt/tbn-protocol"
$DOMAIN = "tbn.hardinai.co.uk"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  TBN Protocol — Production Deployment" -ForegroundColor Cyan
Write-Host "  Server: $SERVER_IP" -ForegroundColor Cyan
Write-Host "  Domain: $DOMAIN" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if we can connect to the server
Write-Host ""
Write-Host "[0/8] Testing server connection..." -ForegroundColor Yellow

# Try to connect using different SSH methods
$SSH_CMD = $null
$RSYNC_CMD = $null

# Test basic SSH connection
try {
    $result = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $SSH_CMD = "ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
        Write-Host "✅ Connected using default SSH configuration" -ForegroundColor Green
    }
} catch {
    # Try with common key locations
    $keyPaths = @(
        "$env:USERPROFILE\.ssh\tbn-key.pem",
        "$env:USERPROFILE\Downloads\tbn-key.pem",
        ".\tbn-key.pem"
    )
    
    foreach ($keyPath in $keyPaths) {
        if (Test-Path $keyPath) {
            try {
                $result = ssh -i $keyPath -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $SSH_CMD = "ssh -i $keyPath -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
                    Write-Host "✅ Connected using $keyPath" -ForegroundColor Green
                    break
                }
            } catch {
                continue
            }
        }
    }
}

if (-not $SSH_CMD) {
    Write-Host "❌ Cannot connect to server. Please ensure:" -ForegroundColor Red
    Write-Host "   - SSH access is configured" -ForegroundColor Red
    Write-Host "   - Server is running at $SERVER_IP" -ForegroundColor Red
    Write-Host "   - You have the SSH key file (if required)" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install SSH on Windows:" -ForegroundColor Yellow
    Write-Host "   1. Install Git for Windows (includes SSH)" -ForegroundColor Yellow
    Write-Host "   2. Or enable OpenSSH in Windows Features" -ForegroundColor Yellow
    exit 1
}

# Function to execute SSH commands
function Invoke-SSHCommand {
    param([string]$Command)
    
    $fullCommand = "$SSH_CMD `"$Command`""
    Write-Host "Executing: $Command" -ForegroundColor Gray
    Invoke-Expression $fullCommand
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Command failed: $Command" -ForegroundColor Red
        exit 1
    }
}

# Function to sync files (using scp since rsync might not be available on Windows)
function Sync-Files {
    Write-Host "Syncing files to server..." -ForegroundColor Gray
    
    # Create a temporary directory with only the files we want to upload
    $tempDir = "$env:TEMP\tbn-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    # Copy files excluding unwanted directories
    $excludeDirs = @('.git', '__pycache__', '.venv', 'node_modules')
    $excludeFiles = @('*.pyc', 'test_pypi_integration.py')
    
    Get-ChildItem -Path . -Recurse | Where-Object {
        $relativePath = $_.FullName.Substring((Get-Location).Path.Length + 1)
        $shouldExclude = $false
        
        foreach ($excludeDir in $excludeDirs) {
            if ($relativePath -like "*$excludeDir*") {
                $shouldExclude = $true
                break
            }
        }
        
        foreach ($excludeFile in $excludeFiles) {
            if ($_.Name -like $excludeFile) {
                $shouldExclude = $true
                break
            }
        }
        
        return -not $shouldExclude
    } | ForEach-Object {
        $relativePath = $_.FullName.Substring((Get-Location).Path.Length + 1)
        $destPath = Join-Path $tempDir $relativePath
        $destDir = Split-Path $destPath -Parent
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if (-not $_.PSIsContainer) {
            Copy-Item $_.FullName $destPath
        }
    }
    
    # Use scp to upload files
    $scpCmd = $SSH_CMD -replace "ssh", "scp" -replace "$SERVER_USER@$SERVER_IP", ""
    $scpCmd = "scp -r $($scpCmd.Trim()) `"$tempDir\*`" $SERVER_USER@$SERVER_IP`:$APP_DIR/"
    
    Write-Host "Uploading files..." -ForegroundColor Gray
    Invoke-Expression $scpCmd
    
    # Clean up temp directory
    Remove-Item -Path $tempDir -Recurse -Force
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ File sync failed" -ForegroundColor Red
        exit 1
    }
}

# ── 1. Sync code to server ───────────────────────────
Write-Host ""
Write-Host "[1/8] Syncing code to production server..." -ForegroundColor Yellow
Sync-Files

# ── 2. Install/update dependencies ───────────────────
Write-Host ""
Write-Host "[2/8] Installing Python dependencies..." -ForegroundColor Yellow
Invoke-SSHCommand @"
cd $APP_DIR
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install gunicorn
"@

# ── 3. Set up production environment ─────────────────
Write-Host ""
Write-Host "[3/8] Configuring production environment..." -ForegroundColor Yellow
Invoke-SSHCommand @"
# Create necessary directories
sudo mkdir -p /var/log/tbn
sudo chown $SERVER_USER`:$SERVER_USER /var/log/tbn
mkdir -p $APP_DIR/data
mkdir -p $APP_DIR/data/nodes
mkdir -p $APP_DIR/data/certifications

# Set production environment
echo 'TBN_ENV=production' > $APP_DIR/.env
echo 'TBN_GITHUB_TOKEN=' >> $APP_DIR/.env
echo 'TBN_GITHUB_REPO=burhanyanbolu-design/tbn-bica-registry' >> $APP_DIR/.env
echo 'TBN_DOMAIN=$DOMAIN' >> $APP_DIR/.env
echo 'TBN_SERVER_IP=$SERVER_IP' >> $APP_DIR/.env
"@

# ── 4. Configure systemd service ─────────────────────
Write-Host ""
Write-Host "[4/8] Installing TBN systemd service..." -ForegroundColor Yellow
Invoke-SSHCommand @"
sudo cp $APP_DIR/deploy/tbn.service /etc/systemd/system/tbn.service
sudo systemctl daemon-reload
sudo systemctl enable tbn
"@

# ── 5. Configure Nginx ───────────────────────────────
Write-Host ""
Write-Host "[5/8] Configuring Nginx..." -ForegroundColor Yellow
Invoke-SSHCommand @"
sudo cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/tbn
sudo ln -sf /etc/nginx/sites-available/tbn /etc/nginx/sites-enabled/tbn
sudo nginx -t
sudo systemctl reload nginx
"@

# ── 6. Set up SSL certificate ────────────────────────
Write-Host ""
Write-Host "[6/8] Setting up SSL certificate..." -ForegroundColor Yellow
Invoke-SSHCommand @"
if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo 'Setting up SSL certificate...'
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email burhan@hardinai.co.uk
else
    echo 'SSL certificate already exists'
fi
"@

# ── 7. Initialize GitHub BICA registry ───────────────
Write-Host ""
Write-Host "[7/8] Initializing GitHub BICA registry..." -ForegroundColor Yellow
Invoke-SSHCommand @"
cd $APP_DIR
.venv/bin/python -c `"
from tbn.github_bica import GitHubBICA
import os

# Initialize GitHub BICA registry
print('Initializing GitHub BICA registry...')
github_bica = GitHubBICA(
    repo='burhanyanbolu-design/tbn-bica-registry',
    token=os.environ.get('GITHUB_TOKEN', '')
)

# Create initial registry structure
try:
    github_bica.initialize_registry()
    print('✅ GitHub BICA registry initialized')
except Exception as e:
    print(f'⚠️  GitHub registry setup: {e}')
    print('   (Will use local registry until GitHub token is configured)')
`"
"@

# ── 8. Start TBN service ─────────────────────────────
Write-Host ""
Write-Host "[8/8] Starting TBN Protocol service..." -ForegroundColor Yellow
Invoke-SSHCommand @"
sudo systemctl restart tbn
sleep 3
sudo systemctl status tbn --no-pager
"@

# ── Deployment complete ──────────────────────────────
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  🚀 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard : https://$DOMAIN" -ForegroundColor Cyan
Write-Host "  API       : https://$DOMAIN/api/stats" -ForegroundColor Cyan
Write-Host "  Certification Portal : https://$DOMAIN/certification/portal" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Set GITHUB_TOKEN in /opt/tbn-protocol/.env for GitHub BICA" -ForegroundColor Yellow
Write-Host "  2. Test the live dashboard" -ForegroundColor Yellow
Write-Host "  3. Register your first production bot" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Green

# Test the deployment
Write-Host ""
Write-Host "Testing deployment..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$DOMAIN/api/stats" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ TBN Protocol is live at https://$DOMAIN" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Service responded with status $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Service may still be starting up. Check logs if issues persist." -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}