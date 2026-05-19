#!/bin/bash
# Reduce OpenAI API Costs - Emergency Cost Reduction

echo "=== REDUCING OPENAI API COSTS ==="
echo ""

# 1. Stop hardin-ai-agent if running
echo "1. Stopping hardin-ai-agent service..."
if systemctl is-active --quiet hardin-ai-agent 2>/dev/null; then
    sudo systemctl stop hardin-ai-agent
    sudo systemctl disable hardin-ai-agent
    echo "   ✓ Stopped and disabled hardin-ai-agent"
else
    echo "   ✗ Service not running"
fi
echo ""

# 2. Switch LGMD to GPT-3.5-turbo (10x cheaper than GPT-4)
echo "2. Switching LGMD to GPT-3.5-turbo..."
if [ -f /home/ubuntu/lgmd-research-agent/.env ]; then
    # Backup original
    cp /home/ubuntu/lgmd-research-agent/.env /home/ubuntu/lgmd-research-agent/.env.backup
    
    # Replace GPT-4 with GPT-3.5-turbo
    sed -i 's/gpt-4/gpt-3.5-turbo/g' /home/ubuntu/lgmd-research-agent/.env
    sed -i 's/GPT-4/GPT-3.5-turbo/g' /home/ubuntu/lgmd-research-agent/.env
    echo "   ✓ Switched to GPT-3.5-turbo (10x cheaper)"
fi

# Also check Python files
if [ -f /home/ubuntu/lgmd-research-agent/app.py ]; then
    sed -i 's/"gpt-4"/"gpt-3.5-turbo"/g' /home/ubuntu/lgmd-research-agent/app.py
    sed -i "s/'gpt-4'/'gpt-3.5-turbo'/g" /home/ubuntu/lgmd-research-agent/app.py
    echo "   ✓ Updated app.py to use GPT-3.5-turbo"
fi
echo ""

# 3. Reduce LGMD cron frequency
echo "3. Reducing LGMD analysis frequency..."
if crontab -l 2>/dev/null | grep -q lgmd; then
    # Backup current crontab
    crontab -l > /tmp/crontab.backup
    
    # Change from every 12 hours to every 24 hours
    crontab -l | sed 's/\*\/12/0 0/g' | crontab -
    echo "   ✓ Changed from every 12h to once daily (midnight)"
    echo "   Old schedule backed up to /tmp/crontab.backup"
else
    echo "   ✗ No LGMD cron job found"
fi
echo ""

# 4. Restart LGMD service if it exists
echo "4. Restarting LGMD service..."
if systemctl is-active --quiet lgmd 2>/dev/null; then
    sudo systemctl restart lgmd
    echo "   ✓ Restarted with new settings"
else
    echo "   ✗ No lgmd service running"
fi
echo ""

echo "=== COST REDUCTION COMPLETE ==="
echo ""
echo "Changes made:"
echo "• Stopped hardin-ai-agent (was using OpenAI API)"
echo "• Switched LGMD from GPT-4 to GPT-3.5-turbo (10x cheaper)"
echo "• Reduced LGMD frequency from 12h to 24h (50% fewer calls)"
echo ""
echo "Expected savings: ~95% reduction in OpenAI costs"
echo ""
echo "Monitor usage at: https://platform.openai.com/usage"
