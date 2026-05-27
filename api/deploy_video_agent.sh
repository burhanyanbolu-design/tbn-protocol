#!/bin/bash
# Deploy TBN Video Agent to production server
# Run: ssh -i .ssh_temp_key ubuntu@3.11.229.68 'bash -s' < api/deploy_video_agent.sh

set -e

echo "=== Deploying TBN Video Agent ==="

cd /opt/tbn-protocol

# 1. Ensure ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "[1/5] Installing ffmpeg..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
else
    echo "[1/5] ffmpeg already installed ✓"
fi

# 2. Ensure requests available
echo "[2/5] Checking Python dependencies..."
pip3 install --quiet requests 2>/dev/null || true

# 3. Register the video_agent blueprint in server.py (if not already)
if ! grep -q "video_agent" server.py; then
    echo "[3/5] Registering video_agent blueprint in server.py..."
    # Add import after other api imports
    sed -i '/from api.digiemu_interop import digiemu_bp/a from api.video_agent import video_agent' server.py 2>/dev/null || \
    sed -i '/from api.routes import api/a from api.video_agent import video_agent' server.py 2>/dev/null || \
    # Fallback: add before app creation
    sed -i '/^app = Flask/i from api.video_agent import video_agent' server.py

    # Register blueprint (after other register_blueprint calls)
    sed -i '/app.register_blueprint(digiemu_bp/a app.register_blueprint(video_agent, url_prefix="/api")' server.py 2>/dev/null || \
    sed -i '/app.register_blueprint(api/a app.register_blueprint(video_agent, url_prefix="/api")' server.py
    echo "    Blueprint registered ✓"
else
    echo "[3/5] video_agent already registered ✓"
fi

# 4. Create upload directory
echo "[4/5] Creating upload directory..."
mkdir -p /tmp/tbn_video_agent

# 5. Restart the service
echo "[5/5] Restarting TBN service..."
sudo systemctl restart tbn
sleep 2

# Verify
if systemctl is-active --quiet tbn; then
    echo ""
    echo "=== SUCCESS ==="
    echo "Video Agent is LIVE at:"
    echo "  Page:   https://tbn.hardinai.co.uk/api/video-agent"
    echo "  API:    https://tbn.hardinai.co.uk/api/video-agent/process"
    echo "  Health: https://tbn.hardinai.co.uk/api/video-agent/health"
    echo ""
    echo "NOTE: Set GEMINI_API_KEY environment variable for real video analysis."
    echo "      Without it, only the demo mode will work."
else
    echo "ERROR: TBN service failed to start!"
    sudo journalctl -u tbn --no-pager -n 20
fi
