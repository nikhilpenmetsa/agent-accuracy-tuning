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

echo "=========================================="
echo "Creating Test Users in Cognito"
echo "=========================================="

# Get User Pool ID and Client ID from stack outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

echo "User Pool ID: ${USER_POOL_ID}"
echo "Client ID: ${CLIENT_ID}"
echo ""

# Test users from .env
USERS=(
    "${TEST_USER_1_EMAIL}:${TEST_USER_1_PASSWORD}"
    "${TEST_USER_2_EMAIL}:${TEST_USER_2_PASSWORD}"
    "${TEST_USER_3_EMAIL}:${TEST_USER_3_PASSWORD}"
)

for USER_INFO in "${USERS[@]}"; do
    EMAIL="${USER_INFO%%:*}"
    PASSWORD="${USER_INFO##*:}"
    
    echo "Creating user: ${EMAIL}"
    
    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id ${USER_POOL_ID} \
        --username ${EMAIL} \
        --user-attributes Name=email,Value=${EMAIL} Name=email_verified,Value=true \
        --message-action SUPPRESS \
        --region ${REGION} 2>/dev/null || echo "  User already exists"
    
    # Set permanent password
    aws cognito-idp admin-set-user-password \
        --user-pool-id ${USER_POOL_ID} \
        --username ${EMAIL} \
        --password ${PASSWORD} \
        --permanent \
        --region ${REGION}
    
    echo "  ✓ Created with password: ${PASSWORD}"
done

echo ""
echo "=========================================="
echo "Test Users Created!"
echo "=========================================="
echo ""
echo "You can now authenticate with:"
echo "  Email: ${TEST_USER_1_EMAIL}"
echo "  Password: ${TEST_USER_1_PASSWORD}"
echo ""
echo "Run ./test_api.sh to test the API"
