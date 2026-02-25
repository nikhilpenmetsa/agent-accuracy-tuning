#!/bin/bash

# Fetch configuration from deployed case-backend stack for local testing

set -e

# Load environment variables
if [ -f ../config.env ]; then
    source ../config.env
else
    echo "Error: config.env not found"
    exit 1
fi

echo "📋 Fetching case-backend stack outputs..."
CASE_BACKEND_STACK="${PROJECT_NAME}-case-backend-stack"

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
    --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

echo "✓ User Pool ID: $USER_POOL_ID"
echo "✓ Client ID: $CLIENT_ID"
echo "✓ API URL: $API_URL"

# Generate config.json
cat > config.json << EOF
{
    "ENABLE_QUICK_LOGIN": true,
    "COGNITO_USER_POOL_ID": "$USER_POOL_ID",
    "COGNITO_CLIENT_ID": "$CLIENT_ID",
    "API_BASE_URL": "$API_URL",
    "AWS_REGION": "${AWS_REGION:-us-east-1}",
    "AGENT_ENDPOINT": null
}
EOF

echo "✓ config.json created"
echo ""
echo "Refresh your browser to use real Cognito authentication"
