#!/bin/bash
# Deploy updated TBN dashboard with logo, copyright, and Google Analytics

echo "=========================================="
echo "  TBN Dashboard Update Deployment"
echo "=========================================="
echo ""

# Upload updated dashboard
echo "📤 Uploading updated dashboard.html..."
scp api/templates/dashboard.html ubuntu@3.11.229.68:/home/ubuntu/tbn-protocol/api/templates/dashboard.html

if [ $? -eq 0 ]; then
    echo "✅ Dashboard uploaded successfully"
else
    echo "❌ Upload failed"
    exit 1
fi

# Restart the service
echo ""
echo "🔄 Restarting TBN service..."
ssh ubuntu@3.11.229.68 "sudo systemctl restart tbn"

if [ $? -eq 0 ]; then
    echo "✅ Service restarted successfully"
else
    echo "❌ Restart failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Visit: https://tbn.hardinai.co.uk"
echo ""
echo "Changes deployed:"
echo "  ✅ Hardin AI Solutions logo in header"
echo "  ✅ Copyright footer with legal notice"
echo "  ✅ Google Analytics tracking (G-EF6RKG8KY2)"
echo ""
