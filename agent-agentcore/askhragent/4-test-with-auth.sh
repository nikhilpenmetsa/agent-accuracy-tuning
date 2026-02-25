#!/bin/bash
# Test the deployed AgentCore agent with authentication

set -e

echo "Testing deployed AskHR Agent with Authentication..."
echo ""

# Get Cognito configuration from case-backend
COGNITO_USER_POOL_ID="us-east-1_bA1L8mO4W"
COGNITO_CLIENT_ID="7e9v79qu155qj0beq1gane0sgr"
TEST_USER="john.doe@acme.com"
TEST_PASSWORD="Password123"

echo "Authenticating as: $TEST_USER"

# Authenticate and get ID token
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$COGNITO_CLIENT_ID" \
    --auth-parameters USERNAME="$TEST_USER",PASSWORD="$TEST_PASSWORD" \
    --region us-east-1 \
    --output json)

ID_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])" 2>/dev/null)

if [ -z "$ID_TOKEN" ] || [ "$ID_TOKEN" = "null" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✓ Authentication successful"
echo ""

# Generate a test session ID
TEST_SESSION_ID="test-$(date +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo 'abcd1234')"

# Test payload with session_id
TEST_PAYLOAD='{
  "prompt": "What is the company PTO policy?",
  "session_id": "'"$TEST_SESSION_ID"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "Test payload:"
echo "$TEST_PAYLOAD"
echo ""
echo "Session ID: $TEST_SESSION_ID"
echo ""

# Invoke the agent with authentication
echo "Invoking agent with authentication..."
if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$TEST_PAYLOAD" --bearer-token "$ID_TOKEN"
else
    agentcore invoke "$TEST_PAYLOAD" --bearer-token "$ID_TOKEN"
fi

echo ""
echo "=========================================="
echo "Test conversation history (use same session_id):"
echo "=========================================="
echo ""
echo "Follow-up question to test memory:"
FOLLOWUP_PAYLOAD='{
  "prompt": "How many days did you say I get?",
  "session_id": "'"$TEST_SESSION_ID"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "$FOLLOWUP_PAYLOAD"
echo ""
echo "Run this to test conversation memory:"
if command -v agentcore.exe &> /dev/null; then
    echo "  agentcore.exe invoke '$FOLLOWUP_PAYLOAD' --bearer-token \"$ID_TOKEN\""
else
    echo "  agentcore invoke '$FOLLOWUP_PAYLOAD' --bearer-token \"$ID_TOKEN\""
fi

echo ""
echo "Or run this script again to test with a new session"
