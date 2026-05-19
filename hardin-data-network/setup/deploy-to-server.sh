#!/bin/bash
# Deploy Hardin Data Network to AWS Server
# Run this from LOCAL machine
#
# Usage: bash deploy-to-server.sh

set -e

SERVER_IP="3.11.229.68"
SERVER_USER="ubuntu"
PEM_KEY="aws-lightsail.pem"
PROJECT_DIR="/opt/tbn-protocol"

echo "=================================================="
echo "  Hardin Data Network - Deploy to Server"
echo "=================================================="

# Check if PEM key exists
if [ ! -f "$PEM_KEY" ]; then
    echo "❌ Error: PEM key not found: $PEM_KEY"
    echo "Please ensure aws-lightsail.pem is in the current directory"
    exit 1
fi

# Copy hardin-data-network folder to server
echo ""
echo "[1/4] Copying files to server..."
scp -i $PEM_KEY -r hardin-data-network/ $SERVER_USER@$SERVER_IP:$PROJECT_DIR/

# Make setup script executable
echo ""
echo "[2/4] Making setup script executable..."
ssh -i $PEM_KEY $SERVER_USER@$SERVER_IP "chmod +x $PROJECT_DIR/hardin-data-network/setup/setup-database.sh"

# Run database setup
echo ""
echo "[3/4] Running database setup on server..."
ssh -i $PEM_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && bash hardin-data-network/setup/setup-database.sh"

# Install Python dependencies for bots
echo ""
echo "[4/4] Installing Python dependencies..."
ssh -i $PEM_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && sudo pip3 install psycopg2-binary requests"

echo ""
echo "=================================================="
echo "  ✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. SSH to server: ssh -i $PEM_KEY $SERVER_USER@$SERVER_IP"
echo "  2. Test RetailBot: cd /opt/tbn-protocol && python3 hardin-data-network/bots/RetailBot.py"
echo "  3. Check database: psql -h localhost -U hardin_admin -d hardin_data_network"
echo ""
echo "=================================================="
