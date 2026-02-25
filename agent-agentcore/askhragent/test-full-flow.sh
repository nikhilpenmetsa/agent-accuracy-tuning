#!/bin/bash
# Test the complete flow: create conversation, ask questions, switch sessions, load history

set -e

echo "=========================================="
echo "Testing Complete Flow with Message History"
echo "=========================================="
echo ""

# Configuration
TEST_USER="john.doe@acme.com"
TEST_PASSWORD="Password123"
COGNITO_USER_POOL_ID="us-east-1_9sTo5RtFm"
COGNITO_CLIENT_ID="395nqjcnulut82roo9st4afos"

echo "Step 1: Authenticate"
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$COGNITO_CLIENT_ID" \
    --auth-parameters USERNAME="$TEST_USER",PASSWORD="$TEST_PASSWORD" \
    --region us-east-1 \
    --output json)

ID_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])" 2>/dev/null)
echo "✓ Authenticated as $TEST_USER"
echo ""

echo "Step 2: Ask agent a question (creates conversation in memory)"
SESSION_1="test-flow-$(date +%Y%m%d%H%M%S)-session1"

PAYLOAD_1='{
  "prompt": "What is the PTO policy?",
  "session_id": "'"$SESSION_1"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "Session 1 ID: $SESSION_1"
echo "Asking: What is the PTO policy?"
echo ""

cd agent-agentcore/askhragent
if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$PAYLOAD_1" --bearer-token "$ID_TOKEN" | head -20
else
    agentcore invoke "$PAYLOAD_1" --bearer-token "$ID_TOKEN" | head -20
fi
cd ../..

echo ""
echo "Step 3: Ask follow-up question in same session"
PAYLOAD_2='{
  "prompt": "How many days do I get?",
  "session_id": "'"$SESSION_1"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "Asking: How many days do I get?"
echo ""

cd agent-agentcore/askhragent
if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$PAYLOAD_2" --bearer-token "$ID_TOKEN" | head -20
else
    agentcore invoke "$PAYLOAD_2" --bearer-token "$ID_TOKEN" | head -20
fi
cd ../..

echo ""
echo "Step 4: Wait for memory to persist..."
sleep 3

echo ""
echo "Step 5: Retrieve messages from memory via API"
cd session-backend
MESSAGES=$(curl -s -X GET \
    -H "Authorization: Bearer $ID_TOKEN" \
    "https://w4d5kxne67.execute-api.us-east-1.amazonaws.com/prod/sessions/$SESSION_1/messages")

echo "Messages retrieved:"
echo "$MESSAGES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Count: {data['count']}\"); [print(f\"{i+1}. [{m['role']}]: {m['content'][:80]}...\") for i,m in enumerate(data['messages'])]" 2>/dev/null || echo "$MESSAGES"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "If you see messages above, the integration is working!"
echo "Now test in the browser:"
echo "1. Login to http://localhost:8000"
echo "2. Ask a question"
echo "3. Create new conversation"
echo "4. Switch back to first conversation"
echo "5. Messages should load!"
