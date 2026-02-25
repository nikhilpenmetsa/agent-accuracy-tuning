#!/bin/bash
# Test Jane's session messages

set -e

TEST_USER="jane.smith@acme.com"
TEST_PASSWORD="Password123"
COGNITO_CLIENT_ID="395nqjcnulut82roo9st4afos"
SESSION_ID="20260224233605-35f38f82"

echo "Authenticating as: $TEST_USER"

AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$COGNITO_CLIENT_ID" \
    --auth-parameters USERNAME="$TEST_USER",PASSWORD="$TEST_PASSWORD" \
    --region us-east-1 \
    --output json)

ID_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")

echo "✓ Authenticated"
echo ""
echo "Testing messages for session: $SESSION_ID"
echo ""

curl -s -X GET \
    -H "Authorization: Bearer $ID_TOKEN" \
    "https://w4d5kxne67.execute-api.us-east-1.amazonaws.com/prod/sessions/$SESSION_ID/messages" \
    | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
