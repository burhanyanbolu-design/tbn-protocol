#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# TBN Video Agent — Instagram Download Setup
# ═══════════════════════════════════════════════════════════════════════
# Run this on the Ubuntu server (3.11.229.68) to enable Instagram reel
# downloads. Installs instaloader + playwright as download strategies.
#
# Usage: sudo bash setup_instagram.sh
# ═══════════════════════════════════════════════════════════════════════

set -e

echo "═══ TBN Video Agent: Instagram Setup ═══"
echo ""

# 1. Update yt-dlp to latest (may fix some Instagram issues)
echo "[1/4] Updating yt-dlp..."
pip3 install -U yt-dlp 2>/dev/null || pip install -U yt-dlp

# 2. Install instaloader (primary Instagram strategy)
echo "[2/4] Installing instaloader..."
pip3 install -U instaloader 2>/dev/null || pip install -U instaloader

# 3. Install playwright (browser-based fallback)
echo "[3/4] Installing playwright..."
pip3 install playwright 2>/dev/null || pip install playwright

echo "[3b/4] Installing Chromium for Playwright..."
python3 -m playwright install chromium
# Install system dependencies for Chromium
python3 -m playwright install-deps chromium 2>/dev/null || true

# 4. Create instaloader session (optional but recommended)
echo "[4/4] Instaloader session setup..."
echo ""
echo "  To enable authenticated Instagram access (recommended):"
echo "  1. Run: python3 -c \"import instaloader; L = instaloader.Instaloader(); L.login('YOUR_IG_USERNAME', 'YOUR_IG_PASSWORD'); L.save_session_to_file('/opt/tbn-protocol/instaloader_session')\""
echo "  2. Set env var: export INSTAGRAM_USER=YOUR_IG_USERNAME"
echo "  3. Add to /etc/environment: INSTAGRAM_USER=YOUR_IG_USERNAME"
echo ""
echo "  NOTE: Use a secondary/burner Instagram account, not your main one."
echo "  Instagram may flag automated access on the account."
echo ""

# Restart the service
echo "Restarting TBN service..."
systemctl restart tbn 2>/dev/null || echo "  (run 'sudo systemctl restart tbn' manually)"

echo ""
echo "═══ Setup complete! ═══"
echo ""
echo "Instagram download strategies now available:"
echo "  ✓ instaloader (with optional session auth)"
echo "  ✓ playwright (headless browser extraction)"
echo "  ✓ graphql-scrape (lightweight embed scraping)"
echo "  ✓ yt-dlp (fallback)"
echo ""
echo "Test with: curl -X POST https://tbn.hardinai.co.uk/api/video-agent/health"
echo ""
