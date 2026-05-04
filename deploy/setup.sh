#!/bin/bash
# TBN Protocol — Lightsail Ubuntu Server Setup
# Run this ONCE on a fresh Ubuntu server
# Usage: bash setup.sh

set -e

echo "=================================================="
echo "  TBN Protocol — Server Setup"
echo "  Ubuntu / AWS Lightsail"
echo "=================================================="

# ── 1. System update ─────────────────────────────────
echo ""
echo "[1/7] Updating system..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ── 2. Install Python 3.11+ ──────────────────────────
echo ""
echo "[2/7] Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv git curl

# ── 3. Install Nginx ─────────────────────────────────
echo ""
echo "[3/7] Installing Nginx..."
sudo apt-get install -y nginx

# ── 4. Install Certbot (SSL) ─────────────────────────
echo ""
echo "[4/7] Installing Certbot for SSL..."
sudo apt-get install -y certbot python3-certbot-nginx

# ── 5. Create app directory ──────────────────────────
echo ""
echo "[5/7] Creating app directory..."
sudo mkdir -p /opt/tbn-protocol
sudo chown $USER:$USER /opt/tbn-protocol

# ── 6. Install systemd service ───────────────────────
echo ""
echo "[6/7] Installing TBN systemd service..."
sudo cp /opt/tbn-protocol/deploy/tbn.service /etc/systemd/system/tbn.service
sudo systemctl daemon-reload
sudo systemctl enable tbn

# ── 7. Configure firewall ────────────────────────────
echo ""
echo "[7/7] Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo ""
echo "=================================================="
echo "  Setup complete!"
echo "  Next: run deploy/deploy.sh to push the app"
echo "=================================================="
