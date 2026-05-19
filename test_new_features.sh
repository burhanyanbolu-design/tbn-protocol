#!/bin/bash
BASE="http://localhost:5004"
echo "=== Testing Webhooks + Compliance Drift ==="
echo ""

# Use an existing bot ID from earlier tests
BOT_ID="tbn-bot-fc6f6510f39e1bff"

# 1. Register webhook
echo "1. Register Webhook..."
curl -s -X POST $BASE/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"_global","url":"https://httpbin.org/post","type":"custom","events":["all"]}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',''))"
echo ""

# 2. List webhooks
echo "2. List Webhooks..."
curl -s $BASE/api/webhooks/list | python3 -c "import sys,json; print(f'  Total: {json.load(sys.stdin).get(\"total_webhooks\")}')"
echo ""

# 3. Set compliance policy
echo "3. Set Compliance Policy..."
curl -s -X POST $BASE/api/compliance/policy/set \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"policy\":{\"max_daily_spend\":50.0,\"max_response_time_ms\":5000,\"allowed_models\":[\"gpt-4\",\"gpt-3.5-turbo\"],\"max_tokens_per_request\":4000,\"allowed_endpoints\":[\"https://test.example.com\"]}}" | python3 -c "import sys,json; print(f'  {json.load(sys.stdin).get(\"message\")}')"
echo ""

# 4. Check drift (compliant)
echo "4. Check Drift (compliant state)..."
curl -s -X POST $BASE/api/compliance/check \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"current_state\":{\"daily_spend\":20.0,\"response_time_ms\":3000,\"model_used\":\"gpt-4\",\"tokens_used\":2000,\"endpoint\":\"https://test.example.com\"}}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Score: {d.get(\"compliance_score\")} | Drifts: {d.get(\"new_drifts\")} | {d.get(\"message\")}')"
echo ""

# 5. Check drift (drifting - over budget, wrong model)
echo "5. Check Drift (drifting state)..."
curl -s -X POST $BASE/api/compliance/check \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"current_state\":{\"daily_spend\":60.0,\"response_time_ms\":8000,\"model_used\":\"claude-3\",\"tokens_used\":5000,\"endpoint\":\"https://WRONG.example.com\"}}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Score: {d.get(\"compliance_score\")} | Drifts: {d.get(\"new_drifts\")} | {d.get(\"message\")}')"
echo ""

# 6. Dashboard
echo "6. Compliance Dashboard..."
curl -s $BASE/api/compliance/dashboard | python3 -c "import sys,json; d=json.load(sys.stdin).get('summary',{}); print(f'  Avg Score: {d.get(\"average_compliance_score\")}% | Critical: {d.get(\"total_critical_drifts\")} | Compliant: {d.get(\"compliant\")} | Drifting: {d.get(\"drifting\")} | Non-compliant: {d.get(\"non_compliant\")}')"
echo ""

# 7. Resolve drifts
echo "7. Resolve All Drifts..."
curl -s -X POST $BASE/api/compliance/resolve \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"resolve_all\":true}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  New Score: {d.get(\"new_score\")} | {d.get(\"message\")}')"
echo ""

echo "=== ALL TESTS COMPLETE ==="
