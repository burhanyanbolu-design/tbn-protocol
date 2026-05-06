#!/bin/bash

# VC3 Trading Bot Diagnostic Script
# Checks the current state of VC3 deployment

echo "=========================================="
echo "VC3 Trading Bot Diagnostics"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if directory exists
echo -e "${YELLOW}1. Checking installation directory...${NC}"
if [ -d "/opt/vc3" ]; then
    echo -e "${GREEN}✓ /opt/vc3 exists${NC}"
    ls -la /opt/vc3
else
    echo -e "${RED}✗ /opt/vc3 does NOT exist${NC}"
fi
echo ""

# Check if service exists
echo -e "${YELLOW}2. Checking systemd service...${NC}"
if systemctl list-unit-files | grep -q "vc3.service"; then
    echo -e "${GREEN}✓ vc3.service exists${NC}"
    sudo systemctl status vc3 --no-pager -l || true
else
    echo -e "${RED}✗ vc3.service does NOT exist${NC}"
fi
echo ""

# Check if process is running
echo -e "${YELLOW}3. Checking running processes...${NC}"
VC3_PROCESS=$(ps aux | grep -i "vc3" | grep -v grep | grep -v check-vc3)
if [ -n "$VC3_PROCESS" ]; then
    echo -e "${GREEN}✓ VC3 process found:${NC}"
    echo "$VC3_PROCESS"
else
    echo -e "${RED}✗ No VC3 process running${NC}"
fi
echo ""

# Check if port 5003 is listening
echo -e "${YELLOW}4. Checking port 5003...${NC}"
if sudo netstat -tlnp | grep -q ":5003"; then
    echo -e "${GREEN}✓ Port 5003 is listening:${NC}"
    sudo netstat -tlnp | grep ":5003"
else
    echo -e "${RED}✗ Port 5003 is NOT listening${NC}"
fi
echo ""

# Check nginx config
echo -e "${YELLOW}5. Checking nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-enabled/vc3" ]; then
    echo -e "${GREEN}✓ Nginx config exists${NC}"
    echo "Proxy configuration:"
    grep "proxy_pass" /etc/nginx/sites-enabled/vc3 || echo "No proxy_pass found"
else
    echo -e "${RED}✗ Nginx config does NOT exist${NC}"
fi
echo ""

# Check recent logs
echo -e "${YELLOW}6. Recent logs (last 20 lines):${NC}"
if systemctl list-unit-files | grep -q "vc3.service"; then
    sudo journalctl -u vc3 -n 20 --no-pager || echo "No logs available"
else
    echo "Service not installed, no logs available"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
if [ -d "/opt/vc3" ] && systemctl list-unit-files | grep -q "vc3.service" && sudo netstat -tlnp | grep -q ":5003"; then
    echo -e "${GREEN}✓ VC3 appears to be fully deployed and running${NC}"
elif [ -d "/opt/vc3" ]; then
    echo -e "${YELLOW}⚠ VC3 is partially deployed but not running properly${NC}"
    echo "Run: sudo systemctl restart vc3"
else
    echo -e "${RED}✗ VC3 is NOT deployed${NC}"
    echo "Run: sudo bash /opt/tbn-protocol/deploy/deploy-vc3.sh"
fi
echo ""
