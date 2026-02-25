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
echo "Cleaning up Case Backend API Stack"
echo "=========================================="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Get User Pool ID before deleting stack
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text 2>/dev/null || echo "")

# Delete all users from Cognito User Pool
if [ ! -z "$USER_POOL_ID" ]; then
    echo "Deleting users from Cognito User Pool..."
    USERS=$(aws cognito-idp list-users \
        --user-pool-id ${USER_POOL_ID} \
        --region ${REGION} \
        --query 'Users[*].Username' \
        --output text 2>/dev/null || echo "")
    
    if [ ! -z "$USERS" ]; then
        for USER in $USERS; do
            echo "  Deleting user: ${USER}"
            aws cognito-idp admin-delete-user \
                --user-pool-id ${USER_POOL_ID} \
                --username ${USER} \
                --region ${REGION} 2>/dev/null || true
        done
    fi
fi

# Delete S3 bucket with Lambda code
BUCKET_NAME="${STACK_NAME}-lambda-code-$(aws sts get-caller-identity --query Account --output text)"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 > /dev/null; then
    echo "Deleting S3 bucket: ${BUCKET_NAME}"
    aws s3 rb "s3://${BUCKET_NAME}" --force --region ${REGION}
fi

# Delete CloudFormation stack
echo "Deleting CloudFormation stack..."
aws cloudformation delete-stack \
    --stack-name ${STACK_NAME} \
    --region ${REGION}

echo "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name ${STACK_NAME} \
    --region ${REGION}

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
