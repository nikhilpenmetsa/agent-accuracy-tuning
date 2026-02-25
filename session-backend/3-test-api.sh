#!/bin/bash

set -e

# Source configuration files
if [ -f "../config.env" ]; then
    source ../config.env
else
    echo "Error: ../config.env not found"
    exit 1
fi

if [ -f ".env" ]; then
    source .env
else
    echo "Error: .env not found"
    exit 1
fi

# Check if case-backend outputs exist
CASE_BACKEND_DIR="../case-backend"
if [ ! -f "${CASE_BACKEND_DIR}/.env" ]; then
    echo "Error: case-backend .env not found"
    exit 1
fi

source "${CASE_BACKEND_DIR}/.env"

REGION="${AWS_REGION}"

# Get API URL from outputs
if [ ! -f "outputs.json" ]; then
    echo "Error: outputs.json not found. Run deploy.sh first."
    exit 1
fi

API_URL=$(cat outputs.json | python3 -c "import sys, json; print([o['OutputValue'] for o in json.load(sys.stdin) if o['OutputKey']=='ApiUrl'][0])")

# Get Cognito details from case-backend
CASE_BACKEND_STACK="${PROJECT_NAME}-case-backend-stack"
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name ${CASE_BACKEND_STACK} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name ${CASE_BACKEND_STACK} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

echo "=========================================="
echo "Testing Session Backend API"
echo "=========================================="
echo "API URL: $API_URL"
echo "User Pool ID: $USER_POOL_ID"
echo ""

# Test user credentials
TEST_EMAIL="${TEST_USER_1_EMAIL}"
TEST_PASSWORD="${TEST_USER_1_PASSWORD}"

echo "Authenticating as: $TEST_EMAIL"

# Authenticate and get token
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id ${USER_POOL_CLIENT_ID} \
    --auth-parameters USERNAME=${TEST_EMAIL},PASSWORD=${TEST_PASSWORD} \
    --region ${REGION})

ID_TOKEN=$(echo $AUTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")

echo "✓ Authentication successful"
echo ""

# Test 1: Create a session
echo "Test 1: Creating a new session..."
CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/sessions" \
    -H "Authorization: Bearer ${ID_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"session_title": "Test Session"}')

echo "$CREATE_RESPONSE" | python3 -m json.tool
SESSION_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['session_id'])")
echo ""

# Test 2: List sessions
echo "Test 2: Listing all sessions..."
curl -s -X GET "${API_URL}/sessions" \
    -H "Authorization: Bearer ${ID_TOKEN}" | python3 -m json.tool
echo ""

# Test 3: Get specific session
echo "Test 3: Getting session details..."
curl -s -X GET "${API_URL}/sessions/${SESSION_ID}" \
    -H "Authorization: Bearer ${ID_TOKEN}" | python3 -m json.tool
echo ""

# Test 4: Update session
echo "Test 4: Updating session title..."
curl -s -X PATCH "${API_URL}/sessions/${SESSION_ID}" \
    -H "Authorization: Bearer ${ID_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"session_title": "Updated Test Session"}' | python3 -m json.tool
echo ""

# Test 5: Create another session
echo "Test 5: Creating another session..."
curl -s -X POST "${API_URL}/sessions" \
    -H "Authorization: Bearer ${ID_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"session_title": "Second Test Session"}' | python3 -m json.tool
echo ""

# Test 6: List sessions again
echo "Test 6: Listing all sessions (should show 2)..."
curl -s -X GET "${API_URL}/sessions" \
    -H "Authorization: Bearer ${ID_TOKEN}" | python3 -m json.tool
echo ""

# Test 7: Delete session
echo "Test 7: Deleting first session..."
curl -s -X DELETE "${API_URL}/sessions/${SESSION_ID}" \
    -H "Authorization: Bearer ${ID_TOKEN}" | python3 -m json.tool
echo ""

# Test 8: List sessions after delete
echo "Test 8: Listing sessions after delete (should show 1)..."
curl -s -X GET "${API_URL}/sessions" \
    -H "Authorization: Bearer ${ID_TOKEN}" | python3 -m json.tool
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
