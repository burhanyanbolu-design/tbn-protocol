#!/bin/bash
# Deploy UK Education Bot to AWS server

SERVER="ubuntu@3.11.229.68"
KEY="aws-lightsail.pem"
REMOTE_DIR="/opt/tbn-protocol/hardin-data-network"

echo "======================================================================"
echo "DEPLOYING UK EDUCATION BOT TO AWS SERVER"
echo "======================================================================"

# Upload the bot
echo "Uploading UKEducationBot.py..."
scp -i "$KEY" hardin-data-network/bots/UKEducationBot.py "$SERVER:$REMOTE_DIR/bots/"

# Make it executable
echo "Making bot executable..."
ssh -i "$KEY" "$SERVER" "chmod +x $REMOTE_DIR/bots/UKEducationBot.py"

echo ""
echo "======================================================================"
echo "RUNNING UK EDUCATION BOT"
echo "======================================================================"
ssh -i "$KEY" "$SERVER" "cd $REMOTE_DIR && python3 bots/UKEducationBot.py"

echo ""
echo "======================================================================"
echo "CHECKING STATS"
echo "======================================================================"
ssh -i "$KEY" "$SERVER" "$REMOTE_DIR/stats.sh"

echo ""
echo "======================================================================"
echo "UK EDUCATION DATA COLLECTION COMPLETE!"
echo "======================================================================"
