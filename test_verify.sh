#!/bin/bash
BASE="http://localhost:5004"
EP="https://api.mybot.com/v1"
SP="You are a helpful search assistant"

echo "=== Test Verify Flow ==="

# Register
REG=$(curl -s -X POST $BASE/api/register -H "Content-Type: application/json" -H "X-Admin-Secret: hardin-admin-2026-secret" -d '{"name":"VerifyTestBot","type":"SEARCH"}')
BOT_ID=$(echo $REG | python3 -c "import sys,json; print(json.load(sys.stdin).get('bot_id',''))")
echo "Bot: $BOT_ID"

# Start certification with endpoint + prompt
START=$(curl -s -X POST $BASE/api/security-challenge/start -H "Content-Type: application/json" -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"$EP\",\"system_prompt\":\"$SP\"}")
SESSION=$(echo $START | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))")
echo "Session: $SESSION"
echo "Fingerprint: $(echo $START | python3 -c "import sys,json; print(json.load(sys.stdin).get('bot_fingerprint',''))")"

# Run challenges
for CH in prompt_injection hallucination data_boundary sensitive_data budget_limits instruction_following; do
  curl -s -X POST $BASE/api/security-challenge/submit -H "Content-Type: application/json" -d "{\"session_id\":\"$SESSION\",\"bot_id\":\"$BOT_ID\",\"challenge\":\"$CH\",\"test_prompt\":\"test\",\"bot_response\":\"I cannot.\",\"passed\":true,\"notes\":\"ok\"}" > /dev/null
done
echo "Challenges: done"

# Evaluate
curl -s -X POST $BASE/api/security-challenge/evaluate -H "Content-Type: application/json" -d "{\"bot_id\":\"$BOT_ID\",\"session_id\":\"$SESSION\"}" > /dev/null
echo "Evaluated: done"

# Verify with SAME values (should match)
echo ""
echo "--- Verify with SAME endpoint+prompt ---"
VERIFY=$(curl -s -X POST $BASE/api/security-challenge/verify -H "Content-Type: application/json" -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"$EP\",\"system_prompt\":\"$SP\"}")
echo $VERIFY | python3 -c "import sys,json; v=json.load(sys.stdin); print(f'Verified: {v.get(\"verified\")} | Message: {v.get(\"message\")}')"

# Verify with DIFFERENT values (should mismatch)
echo ""
echo "--- Verify with CHANGED endpoint ---"
VERIFY2=$(curl -s -X POST $BASE/api/security-challenge/verify -H "Content-Type: application/json" -d "{\"bot_id\":\"$BOT_ID\",\"bot_endpoint\":\"https://CHANGED.com\",\"system_prompt\":\"Different prompt\"}")
echo $VERIFY2 | python3 -c "import sys,json; v=json.load(sys.stdin); print(f'Verified: {v.get(\"verified\")} | Reason: {v.get(\"reason\")} | Message: {v.get(\"message\")}')"
