#!/bin/bash
# Monitor bot progress on server

SERVER="ubuntu@3.11.229.68"
KEY=".ssh_temp_key"

echo "======================================================================"
echo "MONITORING BOT PROGRESS"
echo "======================================================================"
echo ""

echo "📊 Current Data Counts:"
ssh -i "$KEY" "$SERVER" "sudo -u postgres psql -d hardin_data_network -c 'SELECT COUNT(*) as currency_rates FROM currency_rates;'"
ssh -i "$KEY" "$SERVER" "sudo -u postgres psql -d hardin_data_network -c 'SELECT COUNT(*) as commodities FROM commodities;'"
ssh -i "$KEY" "$SERVER" "sudo -u postgres psql -d hardin_data_network -c 'SELECT COUNT(*) as trade_data FROM uk_trade;'"
ssh -i "$KEY" "$SERVER" "sudo -u postgres psql -d hardin_data_network -c 'SELECT COUNT(*) as gov_stats FROM uk_government_stats;'"

echo ""
echo "🤖 Running Bots:"
ssh -i "$KEY" "$SERVER" "ps aux | grep -E '(MasterPlan|Automotive|Education)' | grep -v grep"

echo ""
echo "💾 System Resources:"
ssh -i "$KEY" "$SERVER" "free -h | grep Mem"
ssh -i "$KEY" "$SERVER" "df -h | grep /dev/root"

echo ""
echo "======================================================================"
