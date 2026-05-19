#!/bin/bash
# Deploy and run expansion bots on AWS server

SERVER="ubuntu@3.11.229.68"
KEY="aws-lightsail.pem"
REMOTE_DIR="/opt/tbn-protocol/hardin-data-network"

echo "======================================================================"
echo "DEPLOYING EXPANSION BOTS TO AWS SERVER"
echo "======================================================================"

# Upload the new bots
echo "Uploading UKAutomotiveBot.py..."
scp -i "$KEY" hardin-data-network/bots/UKAutomotiveBot.py "$SERVER:$REMOTE_DIR/bots/"

echo "Uploading MasterPlanComplete.py..."
scp -i "$KEY" hardin-data-network/bots/MasterPlanComplete.py "$SERVER:$REMOTE_DIR/bots/"

# Make them executable
echo "Making bots executable..."
ssh -i "$KEY" "$SERVER" "chmod +x $REMOTE_DIR/bots/UKAutomotiveBot.py"
ssh -i "$KEY" "$SERVER" "chmod +x $REMOTE_DIR/bots/MasterPlanComplete.py"

echo ""
echo "======================================================================"
echo "RUNNING UK AUTOMOTIVE BOT"
echo "======================================================================"
ssh -i "$KEY" "$SERVER" "cd $REMOTE_DIR && python3 bots/UKAutomotiveBot.py"

echo ""
echo "======================================================================"
echo "RUNNING MASTER PLAN COMPLETION BOT"
echo "======================================================================"
ssh -i "$KEY" "$SERVER" "cd $REMOTE_DIR && python3 bots/MasterPlanComplete.py"

echo ""
echo "======================================================================"
echo "CHECKING STATS"
echo "======================================================================"
ssh -i "$KEY" "$SERVER" "$REMOTE_DIR/stats.sh"

echo ""
echo "======================================================================"
echo "EXPANSION COMPLETE!"
echo "======================================================================"
