#!/bin/bash
# TBN Protocol — Production Deployment with Multi-Node Support
# Enhanced deployment script for live network nodes
#
# Usage:
#   bash deploy/production-deploy.sh
#
# This script:
# 1. Deploys to your existing server (3.11.229.68)
# 2. Sets up distributed TBN network nodes
# 3. Configures GitHub-backed BICA registry
# 4. Enables certification portal

set -e

# Configuration from server-info.md
SERVER_IP="3.11.229.68"
SERVER_USER="ubuntu"
APP_DIR="/opt/tbn-protocol"
DOMAIN="tbn.hardinai.co.uk"

echo "=================================================="
echo "  TBN Protocol — Production Deployment"
echo "  Server: $SERVER_IP"
echo "  Domain: $DOMAIN"
echo "=================================================="

# Check if we can connect to the server (try without key first, then with key if available)
echo ""
echo "[0/8] Testing server connection..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "echo 'Connection successful'" 2>/dev/null; then
    SSH_CMD="ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
    RSYNC_SSH="ssh -o StrictHostKeyChecking=no"
    echo "✅ Connected using default SSH configuration"
elif [ -f ~/.ssh/tbn-key.pem ]; then
    SSH_CMD="ssh -i ~/.ssh/tbn-key.pem -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
    RSYNC_SSH="ssh -i ~/.ssh/tbn-key.pem -o StrictHostKeyChecking=no"
    echo "✅ Connected using ~/.ssh/tbn-key.pem"
elif [ -f ~/Downloads/tbn-key.pem ]; then
    SSH_CMD="ssh -i ~/Downloads/tbn-key.pem -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
    RSYNC_SSH="ssh -i ~/Downloads/tbn-key.pem -o StrictHostKeyChecking=no"
    echo "✅ Connected using ~/Downloads/tbn-key.pem"
else
    echo "❌ Cannot connect to server. Please ensure:"
    echo "   - SSH access is configured"
    echo "   - Server is running at $SERVER_IP"
    echo "   - You have the SSH key file (if required)"
    exit 1
fi

# ── 1. Sync code to server ───────────────────────────
echo ""
echo "[1/8] Syncing code to production server..."
rsync -avz \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  --exclude 'test_pypi_integration.py' \
  --delete \
  -e "$RSYNC_SSH" \
  ./ $SERVER_USER@$SERVER_IP:$APP_DIR/

# ── 2. Install/update dependencies ───────────────────
echo ""
echo "[2/8] Installing Python dependencies..."
$SSH_CMD "
    cd $APP_DIR
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install gunicorn
"

# ── 3. Set up production environment ─────────────────
echo ""
echo "[3/8] Configuring production environment..."
$SSH_CMD "
    # Create necessary directories
    sudo mkdir -p /var/log/tbn
    sudo chown $SERVER_USER:$SERVER_USER /var/log/tbn
    mkdir -p $APP_DIR/data
    mkdir -p $APP_DIR/data/nodes
    mkdir -p $APP_DIR/data/certifications
    
    # Set production environment
    echo 'TBN_ENV=production' > $APP_DIR/.env
    echo 'TBN_GITHUB_TOKEN=' >> $APP_DIR/.env
    echo 'TBN_GITHUB_REPO=burhanyanbolu-design/tbn-bica-registry' >> $APP_DIR/.env
    echo 'TBN_DOMAIN=$DOMAIN' >> $APP_DIR/.env
    echo 'TBN_SERVER_IP=$SERVER_IP' >> $APP_DIR/.env
"

# ── 4. Configure systemd service ─────────────────────
echo ""
echo "[4/8] Installing TBN systemd service..."
$SSH_CMD "
    sudo cp $APP_DIR/deploy/tbn.service /etc/systemd/system/tbn.service
    sudo systemctl daemon-reload
    sudo systemctl enable tbn
"

# ── 5. Configure Nginx ───────────────────────────────
echo ""
echo "[5/8] Configuring Nginx..."
$SSH_CMD "
    sudo cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/tbn
    sudo ln -sf /etc/nginx/sites-available/tbn /etc/nginx/sites-enabled/tbn
    sudo nginx -t
    sudo systemctl reload nginx
"

# ── 6. Set up SSL certificate ────────────────────────
echo ""
echo "[6/8] Setting up SSL certificate..."
$SSH_CMD "
    if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        echo 'Setting up SSL certificate...'
        sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email burhan@hardinai.co.uk
    else
        echo 'SSL certificate already exists'
    fi
"

# ── 7. Initialize GitHub BICA registry ───────────────
echo ""
echo "[7/8] Initializing GitHub BICA registry..."
$SSH_CMD "
    cd $APP_DIR
    .venv/bin/python -c \"
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
\"
"

# ── 8. Start TBN service ─────────────────────────────
echo ""
echo "[8/8] Starting TBN Protocol service..."
$SSH_CMD "
    sudo systemctl restart tbn
    sleep 3
    sudo systemctl status tbn --no-pager
"

# ── Deployment complete ──────────────────────────────
echo ""
echo "=================================================="
echo "  🚀 DEPLOYMENT COMPLETE!"
echo ""
echo "  Dashboard : https://$DOMAIN"
echo "  API       : https://$DOMAIN/api/stats"
echo "  Logs      : ssh $SERVER_USER@$SERVER_IP 'sudo journalctl -u tbn -f'"
echo ""
echo "  Next steps:"
echo "  1. Set GITHUB_TOKEN in /opt/tbn-protocol/.env for GitHub BICA"
echo "  2. Test the live dashboard"
echo "  3. Register your first production bot"
echo "=================================================="

# Test the deployment
echo ""
echo "Testing deployment..."
if curl -s "https://$DOMAIN/api/stats" > /dev/null; then
    echo "✅ TBN Protocol is live at https://$DOMAIN"
else
    echo "⚠️  Service may still be starting up. Check logs if issues persist."
fi