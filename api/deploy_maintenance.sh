#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Deploy Instagram cookie auto-maintenance on the TBN server
# Run from local: scp this + maintain_ig_cookies.py + service files, then
#                 ssh and run this script
# ═══════════════════════════════════════════════════════════════════════
set -e

echo "═══ Setting up TBN Instagram auto-maintenance ═══"

# Move maintenance script to server location
if [ -f /tmp/maintain_ig_cookies.py ]; then
    sudo cp /tmp/maintain_ig_cookies.py /opt/tbn-protocol/maintain_ig_cookies.py
    sudo chmod +x /opt/tbn-protocol/maintain_ig_cookies.py
    echo "[1/5] Maintenance script installed"
fi

# Install systemd service + timer
sudo cp /tmp/tbn-ig-maintenance.service /etc/systemd/system/
sudo cp /tmp/tbn-ig-maintenance.timer /etc/systemd/system/
echo "[2/5] Systemd unit files installed"

# Create log directory
sudo mkdir -p /var/log/tbn
sudo chown root:root /var/log/tbn
echo "[3/5] Log directory ready"

# Reload + enable + start timer
sudo systemctl daemon-reload
sudo systemctl enable tbn-ig-maintenance.timer
sudo systemctl start tbn-ig-maintenance.timer
echo "[4/5] Timer enabled and started"

# Run once immediately to verify and refresh cookies now
echo "[5/5] Running initial maintenance check..."
sudo systemctl start tbn-ig-maintenance.service
sleep 2

# Show status
echo ""
echo "═══ Status ═══"
sudo systemctl list-timers tbn-ig-maintenance.timer --no-pager
echo ""
echo "Latest log entries:"
sudo tail -20 /var/log/tbn/ig_maintenance.log 2>/dev/null || echo "  (log not yet written)"
echo ""
echo "Health file:"
cat /opt/tbn-protocol/ig_cookies_health.json 2>/dev/null || echo "  (not yet written)"
echo ""
echo "═══ Setup complete ═══"
echo ""
echo "The maintenance will run daily at 3:30 AM."
echo "Manual run:    sudo systemctl start tbn-ig-maintenance.service"
echo "View logs:     sudo journalctl -u tbn-ig-maintenance.service"
echo "View timer:    sudo systemctl list-timers tbn-ig-maintenance.timer"
echo "Health status: cat /opt/tbn-protocol/ig_cookies_health.json"
echo ""
echo "If cookies break, the file /opt/tbn-protocol/IG_COOKIES_BROKEN.flag will appear."
