#!/bin/bash
# Simple test: Ask one question with authentication

set -e

echo "Testing: Can I expense a rental car for a trip to Boston?"
echo ""

# Cognito configuration
COGNITO_USER_POOL_ID="us-east-1_9sTo5RtFm"
COGNITO_CLIENT_ID="395nqjcnulut82roo9st4afos"
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
TEST_SESSION_ID="debug-$(date +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo 'abcd1234')"

echo "Session ID: $TEST_SESSION_ID"
echo ""

# Test payload
TEST_PAYLOAD='{
  "prompt": "Can I expense a rental car for a trip to Boston?",
  "session_id": "'"$TEST_SESSION_ID"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "Invoking agent..."
echo ""

if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$TEST_PAYLOAD" --bearer-token "$ID_TOKEN"
else
    agentcore invoke "$TEST_PAYLOAD" --bearer-token "$ID_TOKEN"
fi

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Session ID: $TEST_SESSION_ID"
echo ""
echo "To view logs with debug info:"
echo "  aws logs tail /aws/bedrock-agentcore/runtimes/askhragent-0L4quKFDp0-DEFAULT --follow"
echo ""
echo "To extract and analyze this session:"
echo "  cd ../../evaluations/analyze"
echo "  python extract_session_data.py --ui-session $TEST_SESSION_ID --user-id <user-uuid> --hours 1"
