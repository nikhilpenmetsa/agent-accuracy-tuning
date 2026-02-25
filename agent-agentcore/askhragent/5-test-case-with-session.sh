#!/bin/bash
# Test case creation with session_id tracking

set -e

echo "=========================================="
echo "Testing Case Creation with Session ID"
echo "=========================================="
echo ""

# Test credentials
TEST_USER="john.doe@acme.com"
TEST_PASSWORD="Password123"
COGNITO_USER_POOL_ID="us-east-1_bA1L8mO4W"
COGNITO_CLIENT_ID="7e9v79qu155qj0beq1gane0sgr"

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
TEST_SESSION_ID="test-case-$(date +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo 'abcd1234')"

echo "Session ID: $TEST_SESSION_ID"
echo ""

# Test 1: Create a case through the agent
echo "=========================================="
echo "Test 1: Creating case through agent"
echo "=========================================="
echo ""

CASE_PAYLOAD='{
  "prompt": "Create a PTO request case for 5 days vacation in March for Sankranthi celebration",
  "session_id": "'"$TEST_SESSION_ID"'",
  "auth_token": "Bearer '"$ID_TOKEN"'"
}'

echo "Asking agent to create case..."
echo ""

if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$CASE_PAYLOAD" --bearer-token "$ID_TOKEN"
else
    agentcore invoke "$CASE_PAYLOAD" --bearer-token "$ID_TOKEN"
fi

echo ""
echo "=========================================="
echo "Test 2: Verify case in DynamoDB"
echo "=========================================="
echo ""

# Wait a moment for case to be created
sleep 2

echo "Fetching cases from DynamoDB..."
CASES=$(aws dynamodb scan \
    --table-name hr-assistant-case-backend-stack-cases \
    --region us-east-1 \
    --output json)

# Get the most recent case
LATEST_CASE=$(echo "$CASES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['Items']:
    # Sort by created_at and get the latest
    items = sorted(data['Items'], key=lambda x: x.get('created_at', {}).get('S', ''), reverse=True)
    latest = items[0]
    print(json.dumps({
        'case_id': latest.get('case_id', {}).get('S', 'N/A'),
        'employee_id': latest.get('employee_id', {}).get('S', 'N/A'),
        'case_type': latest.get('case_type', {}).get('S', 'N/A'),
        'description': latest.get('description', {}).get('S', 'N/A'),
        'session_id': latest.get('session_id', {}).get('S', 'NOT FOUND'),
        'created_at': latest.get('created_at', {}).get('S', 'N/A')
    }, indent=2))
else:
    print('No cases found')
" 2>/dev/null)

echo "$LATEST_CASE"
echo ""

# Check if session_id is present
if echo "$LATEST_CASE" | grep -q "$TEST_SESSION_ID"; then
    echo "✅ SUCCESS: Case includes session_id!"
    echo "   Session ID: $TEST_SESSION_ID"
elif echo "$LATEST_CASE" | grep -q "NOT FOUND"; then
    echo "❌ FAILED: Case does NOT include session_id"
    echo "   This means the session_id was not passed to the case backend"
else
    echo "⚠️  WARNING: Could not verify session_id"
fi

echo ""
echo "=========================================="
echo "Test 3: List cases via API"
echo "=========================================="
echo ""

API_URL="https://hvcezpiaue.execute-api.us-east-1.amazonaws.com/prod"

echo "Fetching cases via API..."
CASES_RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $ID_TOKEN" \
    "$API_URL/cases")

echo "$CASES_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$CASES_RESPONSE"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Session ID used: $TEST_SESSION_ID"
echo "- Check the case object above for 'session_id' field"
echo "- If present, the integration is working correctly!"
