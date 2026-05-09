#!/bin/bash
# Deploy Free TTS to LGMD Patient Page

echo "🚀 Deploying Free TTS to LGMD..."

# Upload the file
scp lgmd-free-tts-implementation.html ubuntu@3.11.229.68:/tmp/patient.html

# SSH and deploy
ssh ubuntu@3.11.229.68 << 'ENDSSH'
# Find LGMD directory
if [ -d "/home/ubuntu/lgmd-research-agent" ]; then
    LGMD_DIR="/home/ubuntu/lgmd-research-agent"
elif [ -d "/var/www/lgmd" ]; then
    LGMD_DIR="/var/www/lgmd"
elif [ -d "/opt/lgmd" ]; then
    LGMD_DIR="/opt/lgmd"
else
    echo "❌ LGMD directory not found"
    exit 1
fi

echo "✅ Found LGMD at: $LGMD_DIR"

# Backup existing patient page
if [ -f "$LGMD_DIR/patient.html" ]; then
    sudo cp "$LGMD_DIR/patient.html" "$LGMD_DIR/patient.html.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backed up existing patient.html"
fi

# Copy new file
sudo cp /tmp/patient.html "$LGMD_DIR/patient.html"
sudo chown www-data:www-data "$LGMD_DIR/patient.html"
echo "✅ Deployed new patient.html"

# Restart services
if systemctl list-units --type=service | grep -q "lgmd"; then
    sudo systemctl restart lgmd
    echo "✅ Restarted lgmd service"
fi

sudo systemctl reload nginx
echo "✅ Reloaded nginx"

# Clean up
rm /tmp/patient.html

echo ""
echo "🎉 Deployment complete!"
echo "Visit: https://lgmd.hardinai.co.uk/patient"
ENDSSH
