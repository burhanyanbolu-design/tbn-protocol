#!/bin/bash

# VC3 Direct Deployment Script
# This script deploys VC3 directly without needing the tbn-protocol repo

set -e

echo "=========================================="
echo "VC3 Trading Bot Direct Deployment"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/burhanyanbolu-design/vc3-hardin-trader.git"
INSTALL_DIR="/opt/vc3"
SERVICE_NAME="vc3"
PORT=5003

echo -e "${YELLOW}Step 1: Checking if VC3 is already installed...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}VC3 directory exists. Updating...${NC}"
    cd $INSTALL_DIR
    sudo git pull origin master || sudo git pull origin main
else
    echo -e "${GREEN}Cloning VC3 repository...${NC}"
    sudo git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

echo -e "${YELLOW}Step 2: Installing Python3 and pip if needed...${NC}"
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv

echo -e "${YELLOW}Step 3: Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    sudo python3 -m venv venv
fi
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt

echo -e "${YELLOW}Step 4: Configuring environment variables...${NC}"

# Prompt for Alpaca API keys
echo ""
echo -e "${YELLOW}=== Alpaca API Configuration ===${NC}"
echo "Get your API keys from: https://app.alpaca.markets/paper/dashboard/overview"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo -e "${GREEN}.env file already exists${NC}"
    read -p "Do you want to update the API keys? (y/n): " UPDATE_KEYS
    if [ "$UPDATE_KEYS" != "y" ]; then
        echo "Keeping existing .env file"
    else
        read -p "Enter your Alpaca API Key: " ALPACA_KEY
        read -p "Enter your Alpaca Secret Key: " ALPACA_SECRET
        
        sudo tee .env > /dev/null <<EOF
# Alpaca API Configuration
ALPACA_API_KEY=$ALPACA_KEY
ALPACA_SECRET_KEY=$ALPACA_SECRET
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Server Configuration
PORT=$PORT
HOST=127.0.0.1

# Trading Configuration
MAX_POSITIONS=5
POSITION_SIZE=500
STOP_LOSS_PCT=1.5
TAKE_PROFIT_PCT=3.0
MAX_DAILY_LOSS=400

# Market Hours (NY Time)
MARKET_OPEN=09:30
MARKET_CLOSE=16:00
EOF
        echo -e "${GREEN}✓ API keys updated${NC}"
    fi
else
    read -p "Enter your Alpaca API Key (or press Enter to skip): " ALPACA_KEY
    read -p "Enter your Alpaca Secret Key (or press Enter to skip): " ALPACA_SECRET
    
    if [ -z "$ALPACA_KEY" ] || [ -z "$ALPACA_SECRET" ]; then
        ALPACA_KEY="your_api_key_here"
        ALPACA_SECRET="your_secret_key_here"
        echo -e "${RED}⚠️  Using placeholder keys - you MUST update them later!${NC}"
    fi
    
    sudo tee .env > /dev/null <<EOF
# Alpaca API Configuration
ALPACA_API_KEY=$ALPACA_KEY
ALPACA_SECRET_KEY=$ALPACA_SECRET
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Server Configuration
PORT=$PORT
HOST=127.0.0.1

# Trading Configuration
MAX_POSITIONS=5
POSITION_SIZE=500
STOP_LOSS_PCT=1.5
TAKE_PROFIT_PCT=3.0
MAX_DAILY_LOSS=400

# Market Hours (NY Time)
MARKET_OPEN=09:30
MARKET_CLOSE=16:00
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
fi

echo -e "${YELLOW}Step 5: Creating systemd service...${NC}"
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=VC3 Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}Step 6: Setting permissions...${NC}"
sudo chown -R ubuntu:ubuntu $INSTALL_DIR

echo -e "${YELLOW}Step 7: Reloading systemd and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Wait a moment for service to start
sleep 3

echo ""
echo -e "${GREEN}=========================================="
echo "VC3 Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Service Status:"
sudo systemctl status $SERVICE_NAME --no-pager -l || true
echo ""
echo -e "${YELLOW}Checking if bot is running on port $PORT...${NC}"
if sudo netstat -tlnp 2>/dev/null | grep -q ":$PORT"; then
    echo -e "${GREEN}✓ Bot is listening on port $PORT${NC}"
else
    echo -e "${RED}✗ Bot is NOT listening on port $PORT${NC}"
    echo "Check logs: sudo journalctl -u vc3 -n 50"
fi
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  sudo systemctl status vc3       # Check status"
echo "  sudo systemctl restart vc3      # Restart bot"
echo "  sudo systemctl stop vc3         # Stop bot"
echo "  sudo journalctl -u vc3 -f       # View live logs"
echo "  sudo journalctl -u vc3 -n 100   # View last 100 log lines"
echo ""
echo -e "${YELLOW}Visit your dashboard:${NC}"
echo "  https://vc3.hardinai.co.uk"
echo ""
echo -e "${RED}⚠️  Remember: The bot only trades Mon-Fri 9:30am-4:00pm NY time${NC}"
