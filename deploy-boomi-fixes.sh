#!/bin/bash

# Deploy Boomi Integration Fixes to Production Server
# Run this on the production server: ubuntu@3.11.229.68

echo "🚀 Deploying Boomi Integration Fixes..."
echo ""

# Navigate to project directory
cd /opt/tbn-protocol || exit 1

# Initialize git if not already a repo
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git remote add origin https://github.com/burhanyanbolu-design/tbn-protocol.git
fi

# Fetch latest changes
echo "📥 Fetching latest changes from GitHub..."
git fetch origin main

# Reset to latest main branch
echo "🔄 Resetting to latest main branch..."
git reset --hard origin/main

# Check if reset was successful
if [ $? -eq 0 ]; then
    echo "✅ Code updated successfully"
else
    echo "❌ Failed to update code"
    exit 1
fi

# Restart the TBN service
echo "🔄 Restarting TBN service..."
sudo systemctl restart tbn

# Wait for service to start
sleep 3

# Check service status
echo "📊 Checking service status..."
sudo systemctl status tbn

# Test health endpoint
echo ""
echo "🧪 Testing health endpoint..."
curl -s -X GET https://tbn.hardinai.co.uk/api/boomi/health | python3 -m json.tool

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test bot registration: curl -X POST https://tbn.hardinai.co.uk/api/boomi/process ..."
echo "2. Test certification check: curl -X POST https://tbn.hardinai.co.uk/api/boomi/process ..."
echo "3. Test governance query: curl -X POST https://tbn.hardinai.co.uk/api/boomi/process ..."
