#!/bin/bash
# Test the messages endpoint

set -e

echo "Testing GET /sessions/{id}/messages endpoint"
echo ""

# Test credentials
TEST_USER="john.doe@acme.com"
TEST_PASSWORD="Password123"
COGNITO_USER_POOL_ID="us-east-1_9sTo5RtFm"
COGNITO_CLIENT_ID="395nqjcnulut82roo9st4afos"
API_URL="https://w4d5kxne67.execute-api.us-east-1.amazonaws.com/prod"

echo "Authenticating as: $TEST_USER"

# Authenticate
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$COGNITO_CLIENT_ID" \
    --auth-parameters USERNAME="$TEST_USER",PASSWORD="$TEST_PASSWORD" \
    --region us-east-1 \
    --output json)

ID_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])" 2>/dev/null)

echo "✓ Authenticated"
echo ""

# List sessions first
echo "Listing sessions..."
SESSIONS=$(curl -s -X GET \
    -H "Authorization: Bearer $ID_TOKEN" \
    "$API_URL/sessions")

echo "$SESSIONS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Found {data['count']} sessions\"); [print(f\"  - {s['session_id']}: {s['session_title']}\") for s in data['sessions'][:3]]"
echo ""

# Get first session ID
SESSION_ID=$(echo "$SESSIONS" | python3 -c "import sys, json; print(json.load(sys.stdin)['sessions'][0]['session_id'])" 2>/dev/null)

echo "Testing messages for session: $SESSION_ID"
echo ""

# Get messages
MESSAGES=$(curl -s -X GET \
    -H "Authorization: Bearer $ID_TOKEN" \
    "$API_URL/sessions/$SESSION_ID/messages")

echo "Response:"
echo "$MESSAGES" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$MESSAGES"
