#!/bin/bash
# Check OpenAI API Usage - Run on server

echo "=== ACTIVE SERVICES USING OPENAI ==="
echo ""

# Check running services
echo "1. Running AI Services:"
sudo systemctl list-units --type=service --state=running | grep -E "hardin|lgmd|ai" || echo "None found"
echo ""

# Check hardin-ai-agent
echo "2. Hardin AI Agent Status:"
if [ -f /home/ubuntu/hardin-ai-agent/.env ]; then
    echo "   ✓ .env file exists"
    if grep -q "OPENAI_API_KEY=sk-" /home/ubuntu/hardin-ai-agent/.env 2>/dev/null; then
        echo "   ✓ OpenAI API key configured"
    fi
fi
if systemctl is-active --quiet hardin-ai-agent 2>/dev/null; then
    echo "   ✓ Service is RUNNING (COSTING MONEY)"
else
    echo "   ✗ Service not running"
fi
echo ""

# Check LGMD research agent
echo "3. LGMD Research Agent Status:"
if [ -d /home/ubuntu/lgmd-research-agent ]; then
    echo "   ✓ Directory exists"
    if [ -f /home/ubuntu/lgmd-research-agent/.env ]; then
        if grep -q "OPENAI_API_KEY=sk-" /home/ubuntu/lgmd-research-agent/.env 2>/dev/null; then
            echo "   ✓ OpenAI API key configured"
        fi
    fi
    # Check for cron jobs
    if crontab -l 2>/dev/null | grep -q lgmd; then
        echo "   ✓ Cron job found (runs periodically)"
        crontab -l | grep lgmd
    fi
fi
echo ""

# Check recent OpenAI API calls in logs
echo "4. Recent OpenAI API Activity (last 1 hour):"
sudo journalctl --since "1 hour ago" | grep -i "openai\|gpt-4\|gpt-3" | tail -20 || echo "No recent activity"
echo ""

# Check Docker containers
echo "5. Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "hardin|ai" || echo "None found"
echo ""

echo "=== COST REDUCTION RECOMMENDATIONS ==="
echo "• If hardin-ai-agent is running: Stop it or switch to GPT-3.5-turbo"
echo "• If LGMD runs every 12h: Reduce to 24h or use local models"
echo "• Check OpenAI dashboard for exact usage: https://platform.openai.com/usage"
