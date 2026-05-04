#!/bin/bash
# Quick setup for port 5001 on Ubuntu
# Run this on your Ubuntu server

set -e

echo "=================================================="
echo "  TBN Protocol — Port 5001 Setup"
echo "=================================================="

# ── 1. Check if port 5001 is available ──────────────
echo ""
echo "[1/5] Checking port 5001..."
if sudo lsof -i :5001 > /dev/null 2>&1; then
    echo "⚠️  Port 5001 is already in use. Stopping existing service..."
    sudo systemctl stop tbn || true
    sudo fuser -k 5001/tcp || true
else
    echo "✓ Port 5001 is available"
fi

# ── 2. Create log directory ─────────────────────────
echo ""
echo "[2/5] Creating log directory..."
sudo mkdir -p /var/log/tbn
sudo chown ubuntu:ubuntu /var/log/tbn
echo "✓ Log directory created"

# ── 3. Allow port 5001 in firewall (if needed) ──────
echo ""
echo "[3/5] Configuring firewall..."
# Port 5001 is internal (127.0.0.1), so we don't expose it externally
# Only Nginx (port 80/443) needs to be open
sudo ufw status | grep -q "Status: active" && echo "✓ Firewall is active" || echo "⚠️  Firewall is not active"

# ── 4. Test Python and dependencies ─────────────────
echo ""
echo "[4/5] Checking Python environment..."
if [ -f "/opt/tbn-protocol/.venv/bin/python" ]; then
    echo "✓ Virtual environment exists"
    /opt/tbn-protocol/.venv/bin/python --version
else
    echo "⚠️  Virtual environment not found. Creating..."
    cd /opt/tbn-protocol
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    echo "✓ Virtual environment created"
fi

# ── 5. Start the TBN service ────────────────────────
echo ""
echo "[5/5] Starting TBN service on port 5001..."
sudo systemctl daemon-reload
sudo systemctl enable tbn
sudo systemctl restart tbn

# Wait a moment for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet tbn; then
    echo "✓ TBN service is running"
    sudo systemctl status tbn --no-pager -l
else
    echo "❌ TBN service failed to start"
    echo "Checking logs..."
    sudo journalctl -u tbn -n 50 --no-pager
    exit 1
fi

# ── 6. Test port 5001 ────────────────────────────────
echo ""
echo "Testing port 5001..."
sleep 2
if curl -s http://127.0.0.1:5001/api/stats > /dev/null; then
    echo "✓ Port 5001 is responding"
    curl -s http://127.0.0.1:5001/api/stats | head -n 10
else
    echo "⚠️  Port 5001 is not responding yet"
    echo "Check logs: sudo journalctl -u tbn -f"
fi

echo ""
echo "=================================================="
echo "  Port 5001 Setup Complete!"
echo "  Service: sudo systemctl status tbn"
echo "  Logs:    sudo journalctl -u tbn -f"
echo "  Test:    curl http://127.0.0.1:5001/api/stats"
echo "=================================================="
