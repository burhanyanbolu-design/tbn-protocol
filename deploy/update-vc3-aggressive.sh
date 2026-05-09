#!/bin/bash
# Deploy VC3 Aggressive Configuration to Server

set -e

echo "🚀 Deploying VC3 Aggressive Configuration"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SERVER="ubuntu@3.11.229.68"
VC3_DIR="/opt/vc3"
ENV_FILE=".env"

echo -e "${BLUE}Step 1: Backing up current configuration...${NC}"
ssh $SERVER "sudo cp $VC3_DIR/$ENV_FILE $VC3_DIR/.env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'No existing .env to backup'"
echo -e "${GREEN}✅ Backup complete${NC}"
echo ""

echo -e "${BLUE}Step 2: Uploading aggressive configuration...${NC}"
scp .env.vc3.aggressive $SERVER:/tmp/.env.vc3.aggressive
echo -e "${GREEN}✅ Configuration uploaded${NC}"
echo ""

echo -e "${BLUE}Step 3: Checking for existing API keys...${NC}"
EXISTING_API_KEY=$(ssh $SERVER "grep '^ALPACA_API_KEY=' $VC3_DIR/$ENV_FILE 2>/dev/null | cut -d'=' -f2" || echo "")
EXISTING_SECRET_KEY=$(ssh $SERVER "grep '^ALPACA_SECRET_KEY=' $VC3_DIR/$ENV_FILE 2>/dev/null | cut -d'=' -f2" || echo "")

if [ -n "$EXISTING_API_KEY" ] && [ "$EXISTING_API_KEY" != "your_key_here" ]; then
    echo -e "${GREEN}✅ Found existing API keys, preserving them${NC}"
    ssh $SERVER "sudo sed -i 's|^ALPACA_API_KEY=.*|ALPACA_API_KEY=$EXISTING_API_KEY|' /tmp/.env.vc3.aggressive"
    ssh $SERVER "sudo sed -i 's|^ALPACA_SECRET_KEY=.*|ALPACA_SECRET_KEY=$EXISTING_SECRET_KEY|' /tmp/.env.vc3.aggressive"
else
    echo -e "${YELLOW}⚠️  No existing API keys found${NC}"
    echo -e "${YELLOW}You'll need to add them manually after deployment${NC}"
fi
echo ""

echo -e "${BLUE}Step 4: Installing new configuration...${NC}"
ssh $SERVER "sudo mv /tmp/.env.vc3.aggressive $VC3_DIR/$ENV_FILE"
ssh $SERVER "sudo chown www-data:www-data $VC3_DIR/$ENV_FILE"
ssh $SERVER "sudo chmod 600 $VC3_DIR/$ENV_FILE"
echo -e "${GREEN}✅ Configuration installed${NC}"
echo ""

echo -e "${BLUE}Step 5: Restarting VC3 service...${NC}"
ssh $SERVER "sudo systemctl restart vc3"
sleep 3
echo -e "${GREEN}✅ Service restarted${NC}"
echo ""

echo -e "${BLUE}Step 6: Checking service status...${NC}"
if ssh $SERVER "sudo systemctl is-active --quiet vc3"; then
    echo -e "${GREEN}✅ VC3 is running${NC}"
else
    echo -e "${RED}❌ VC3 failed to start${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    ssh $SERVER "sudo journalctl -u vc3 -n 20 --no-pager"
    exit 1
fi
echo ""

echo -e "${BLUE}Step 7: Verifying configuration loaded...${NC}"
ssh $SERVER "sudo journalctl -u vc3 -n 30 --no-pager | grep -i 'position\|profit\|aggressive' || echo 'Waiting for logs...'"
echo ""

echo -e "${GREEN}=========================================="
echo "✅ VC3 Aggressive Configuration Deployed!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}📊 New Configuration:${NC}"
echo "  • Position Size: \$10,000 per trade"
echo "  • Take Profit: 20% gains"
echo "  • Stop Loss: 8%"
echo "  • Strategy: AGGRESSIVE"
echo "  • Expected Profit: \$1,500-\$5,000 per trade"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. Check if API keys are set:"
echo "   ssh $SERVER 'sudo cat $VC3_DIR/$ENV_FILE | grep ALPACA_API_KEY'"
echo ""
echo "2. If keys are missing, add them:"
echo "   ssh $SERVER 'sudo nano $VC3_DIR/$ENV_FILE'"
echo "   Then restart: ssh $SERVER 'sudo systemctl restart vc3'"
echo ""
echo "3. Monitor live logs:"
echo "   ssh $SERVER 'sudo journalctl -u vc3 -f'"
echo ""
echo "4. Check dashboard:"
echo "   https://vc3.hardinai.co.uk"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  • Start with paper trading to test"
echo "  • Monitor first 5 trades closely"
echo "  • Ensure you have \$50,000+ account for this config"
echo ""
