#!/bin/bash
# TBN Protocol — Deploy to Lightsail
# Run this from your LOCAL machine to push code to the server
#
# Usage:
#   bash deploy/deploy.sh <server-ip> <path-to-pem-key>
#
# Example:
#   bash deploy/deploy.sh 18.134.22.45 ~/Downloads/tbn-key.pem

set -e

SERVER_IP=${1:-"YOUR_SERVER_IP"}
PEM_KEY=${2:-"~/Downloads/tbn-key.pem"}
SERVER_USER="ubuntu"
APP_DIR="/opt/tbn-protocol"

echo "=================================================="
echo "  TBN Protocol — Deploying to $SERVER_IP"
echo "=================================================="

# ── 1. Copy code to server ───────────────────────────
echo ""
echo "[1/5] Copying code to server..."
rsync -avz \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  -e "ssh -i $PEM_KEY -o StrictHostKeyChecking=no" \
  ./ $SERVER_USER@$SERVER_IP:$APP_DIR/

# ── 2. Install dependencies ──────────────────────────
echo ""
echo "[2/5] Installing Python dependencies..."
ssh -i $PEM_KEY -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \
  "cd $APP_DIR && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"

# ── 3. Create data directory ─────────────────────────
echo ""
echo "[3/5] Setting up data directory..."
ssh -i $PEM_KEY -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \
  "mkdir -p $APP_DIR/data && chmod 755 $APP_DIR/data"

# ── 4. Install nginx config ──────────────────────────
echo ""
echo "[4/5] Configuring Nginx..."
ssh -i $PEM_KEY -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \
  "sudo cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/tbn && \
   sudo ln -sf /etc/nginx/sites-available/tbn /etc/nginx/sites-enabled/tbn && \
   sudo rm -f /etc/nginx/sites-enabled/default && \
   sudo nginx -t && sudo systemctl reload nginx"

# ── 5. Restart TBN service ───────────────────────────
echo ""
echo "[5/5] Starting TBN service..."
ssh -i $PEM_KEY -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \
  "sudo cp $APP_DIR/deploy/tbn.service /etc/systemd/system/tbn.service && \
   sudo systemctl daemon-reload && \
   sudo systemctl restart tbn && \
   sudo systemctl status tbn --no-pager"

echo ""
echo "=================================================="
echo "  Deployed! TBN is live at http://$SERVER_IP"
echo "  Dashboard : http://$SERVER_IP"
echo "  API       : http://$SERVER_IP/api/bots"
echo "=================================================="
