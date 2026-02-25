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

REGION="${AWS_REGION}"
EMAIL="${TEST_USER_EMAIL:-${TEST_USER_1_EMAIL}}"
PASSWORD="${TEST_USER_PASSWORD:-${TEST_USER_1_PASSWORD}}"

echo "=========================================="
echo "Testing Case Backend API"
echo "=========================================="

# Get stack outputs
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

echo "API URL: ${API_URL}"
echo "Test User: ${EMAIL}"
echo ""

# Authenticate and get token
echo "1. Authenticating user..."
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id ${CLIENT_ID} \
    --auth-parameters USERNAME=${EMAIL},PASSWORD=${PASSWORD} \
    --region ${REGION})

ID_TOKEN=$(echo ${AUTH_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])" 2>/dev/null)

if [ -z "$ID_TOKEN" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✓ Authentication successful"
echo ""

# Test GET /case-types
echo "2. Testing GET /case-types..."
CASE_TYPES_RESPONSE=$(curl -s -X GET \
    -H "Authorization: ${ID_TOKEN}" \
    "${API_URL}/case-types")

echo "Response:"
echo ${CASE_TYPES_RESPONSE} | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# Test POST /cases
echo "3. Testing POST /cases (Create Case)..."
CREATE_CASE_RESPONSE=$(curl -s -X POST \
    -H "Authorization: ${ID_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "case_type": "pto",
        "description": "Request for 5 days vacation in March"
    }' \
    "${API_URL}/cases")

echo "Response:"
echo ${CREATE_CASE_RESPONSE} | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# Test GET /cases
echo "4. Testing GET /cases (List Cases)..."
GET_CASES_RESPONSE=$(curl -s -X GET \
    -H "Authorization: ${ID_TOKEN}" \
    "${API_URL}/cases")

echo "Response:"
echo ${GET_CASES_RESPONSE} | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# Create another case
echo "5. Creating another case..."
curl -s -X POST \
    -H "Authorization: ${ID_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "case_type": "compensation",
        "description": "Question about annual bonus structure"
    }' \
    "${API_URL}/cases" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

# List all cases again
echo "6. Listing all cases..."
curl -s -X GET \
    -H "Authorization: ${ID_TOKEN}" \
    "${API_URL}/cases" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"

echo ""
echo "=========================================="
echo "API Testing Complete!"
echo "=========================================="
