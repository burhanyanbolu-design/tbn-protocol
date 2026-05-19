#!/bin/bash
# Test all 3 new features
BASE="http://localhost:5004"
echo "=== TBN Feature Tests ==="
echo ""

# 1. Register a bot
echo "1. Register Bot..."
REG=$(curl -s -X POST $BASE/api/register \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: hardin-admin-2026-secret" \
  -d '{"name":"FeatureTestBot","type":"SEARCH"}')
echo "$REG"
BOT_ID=$(echo $REG | python3 -c "import sys,json; print(json.load(sys.stdin).get('bot_id',''))" 2>/dev/null)
echo "Bot ID: $BOT_ID"
echo ""

# 2. Start certification (generates fingerprint)
echo "2. Start Certification (Proof of Attestation)..."
START=$(curl -s -X POST $BASE/api/security-challenge/start \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"https://test.example.com\",\"system_prompt\":\"You are a search bot\"}")
echo "$START"
SESSION_ID=$(echo $START | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)
echo "Session: $SESSION_ID"
echo ""

# 3. Submit all challenges
echo "3. Running 6 challenges..."
for CH in prompt_injection hallucination data_boundary sensitive_data budget_limits instruction_following; do
  curl -s -X POST $BASE/api/security-challenge/submit \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"bot_id\":\"$BOT_ID\",\"challenge\":\"$CH\",\"test_prompt\":\"test\",\"bot_response\":\"I cannot do that.\",\"passed\":true,\"notes\":\"Passed\"}" > /dev/null
  echo "  ✅ $CH"
done
echo ""

# 4. Evaluate
echo "4. Evaluate..."
EVAL=$(curl -s -X POST $BASE/api/security-challenge/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"session_id\":\"$SESSION_ID\"}")
echo "$EVAL" | python3 -c "import sys,json; e=json.load(sys.stdin).get('evaluation',{}); print(f'  Result: {e.get(\"overall_result\")} | Rate: {e.get(\"pass_rate\")} | Level: {e.get(\"eligible_for_certification\")}')" 2>/dev/null
echo ""

# 5. Verify Attestation (Proof of Attestation)
echo "5. Verify Attestation (same config = should MATCH)..."
VERIFY=$(curl -s -X POST $BASE/api/security-challenge/verify \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"https://test.example.com\",\"system_prompt\":\"You are a search bot\"}")
echo "$VERIFY" | python3 -c "import sys,json; v=json.load(sys.stdin); print(f'  Verified: {v.get(\"verified\")} | Match: {v.get(\"fingerprint_match\")} | {v.get(\"message\")}')" 2>/dev/null
echo ""

# 6. Verify with CHANGED config (should NOT match)
echo "6. Verify with changed config (should FAIL)..."
VERIFY2=$(curl -s -X POST $BASE/api/security-challenge/verify \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"https://CHANGED.example.com\",\"system_prompt\":\"I am now a different bot\"}")
echo "$VERIFY2" | python3 -c "import sys,json; v=json.load(sys.stdin); print(f'  Verified: {v.get(\"verified\")} | Match: {v.get(\"fingerprint_match\")} | Reason: {v.get(\"reason\")}')" 2>/dev/null
echo ""

# 7. Monitoring status
echo "7. Monitoring Status..."
MON=$(curl -s $BASE/api/security-challenge/monitor/status)
echo "$MON" | python3 -c "import sys,json; s=json.load(sys.stdin).get('summary',{}); print(f'  Monitored: {s.get(\"total_monitored\")} | Healthy: {s.get(\"healthy\")} | Failed: {s.get(\"failed\")}')" 2>/dev/null
echo ""

# 8. Set budget
echo "8. Set Budget..."
BUD=$(curl -s -X POST $BASE/api/budget/set \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"daily_limit\":10.00,\"monthly_limit\":200.00,\"max_api_calls_per_hour\":50,\"max_api_calls_per_day\":500}")
echo "$BUD" | python3 -c "import sys,json; print(f'  {json.load(sys.stdin).get(\"message\")}')" 2>/dev/null
echo ""

# 9. Track usage (within budget)
echo "9. Track Usage (within budget)..."
TRACK=$(curl -s -X POST $BASE/api/budget/track \
  -H "Content-Type: application/json" \
  -d "{\"bot_id\":\"$BOT_ID\",\"cost\":0.05,\"operation\":\"llm_call\",\"model\":\"gpt-4\"}")
echo "$TRACK" | python3 -c "import sys,json; t=json.load(sys.stdin); print(f'  Allowed: {t.get(\"allowed\")} | Daily: £{t.get(\"daily_spend\")} | Status: {t.get(\"status\")}')" 2>/dev/null
echo ""

# 10. Check budget
echo "10. Check Budget..."
CHECK=$(curl -s $BASE/api/budget/check/$BOT_ID)
echo "$CHECK" | python3 -c "import sys,json; c=json.load(sys.stdin); print(f'  Status: {c.get(\"status\")} | Today: £{c.get(\"usage_today\",{}).get(\"cost\")} / £{c.get(\"budget\",{}).get(\"daily_limit\")} | {c.get(\"usage_today\",{}).get(\"percent_used\")}% used')" 2>/dev/null
echo ""

echo "=== ALL TESTS COMPLETE ==="
