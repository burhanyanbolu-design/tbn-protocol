#!/bin/bash

# Hardin-AI Phone - Asterisk Installation Script
# Ubuntu 22.04 LTS
# Date: May 12, 2026

set -e

echo "=========================================="
echo "Hardin-AI Phone - Asterisk Installation"
echo "=========================================="
echo ""

# Update system packages
echo "[1/8] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
echo "[2/8] Installing dependencies..."
sudo apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    libssl-dev \
    libncurses5-dev \
    libsqlite3-dev \
    libxml2-dev \
    libjansson-dev \
    uuid-dev \
    sqlite3 \
    libedit-dev \
    pkg-config

# Download Asterisk
echo "[3/8] Downloading Asterisk 20..."
cd /tmp
wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz
tar -xzf asterisk-20-current.tar.gz
cd asterisk-20*/

# Install Asterisk
echo "[4/8] Installing Asterisk..."
./configure --libdir=/usr/lib64 --with-jansson-bundled
make menuselect.makeopts
make -j$(nproc)
sudo make install
sudo make config
sudo make samples

# Create asterisk user
echo "[5/8] Creating asterisk user..."
sudo useradd -m asterisk || true
sudo chown -R asterisk:asterisk /etc/asterisk
sudo chown -R asterisk:asterisk /var/lib/asterisk
sudo chown -R asterisk:asterisk /var/spool/asterisk
sudo chown -R asterisk:asterisk /var/log/asterisk
sudo chown -R asterisk:asterisk /var/run/asterisk

# Configure Asterisk service
echo "[6/8] Configuring Asterisk service..."
sudo systemctl daemon-reload
sudo systemctl enable asterisk
sudo systemctl start asterisk

# Verify installation
echo "[7/8] Verifying installation..."
sleep 2
asterisk -r -x "core show version"

# Configure basic settings
echo "[8/8] Configuring basic settings..."
sudo tee /etc/asterisk/sip.conf > /dev/null <<EOF
[general]
context=default
allowoverlap=no
bindport=5060
bindaddr=0.0.0.0
srvlookup=yes
disallow=all
allow=ulaw
allow=alaw
allow=gsm

[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_USERNAME
secret=YOUR_PASSWORD
fromuser=YOUR_USERNAME
fromdomain=sip.vodafone.co.uk
insecure=port,invite
EOF

echo ""
echo "=========================================="
echo "✅ Asterisk Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update SIP trunk credentials in /etc/asterisk/sip.conf"
echo "2. Configure dialplan in /etc/asterisk/extensions.conf"
echo "3. Restart Asterisk: sudo systemctl restart asterisk"
echo "4. Check status: asterisk -r -x 'sip show peers'"
echo ""
