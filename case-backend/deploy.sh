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
echo "Deploying Case Backend API Stack"
echo "=========================================="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Package Lambda functions
echo "Packaging Lambda functions..."
python3 -c "
import zipfile
import os
from pathlib import Path

with zipfile.ZipFile('lambda-package.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('lambda'):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, 'lambda')
            zipf.write(file_path, arcname)
"

# Create S3 bucket for Lambda code if it doesn't exist
BUCKET_NAME="${STACK_NAME}-lambda-code-$(aws sts get-caller-identity --query Account --output text)"
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>&1 > /dev/null; then
    echo "Creating S3 bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}" --region ${REGION}
fi

# Upload Lambda package
echo "Uploading Lambda package to S3..."
aws s3 cp lambda-package.zip "s3://${BUCKET_NAME}/lambda-package.zip"

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides StackName=${STACK_NAME} \
    --capabilities CAPABILITY_IAM \
    --region ${REGION}

# Update Lambda function code
echo "Updating Lambda function code..."
FUNCTIONS=(
    "${STACK_NAME}-create-case"
    "${STACK_NAME}-get-cases"
    "${STACK_NAME}-get-case-types"
)

for FUNCTION in "${FUNCTIONS[@]}"; do
    echo "  Updating ${FUNCTION}..."
    aws lambda update-function-code \
        --function-name ${FUNCTION} \
        --s3-bucket ${BUCKET_NAME} \
        --s3-key lambda-package.zip \
        --region ${REGION} > /dev/null
done

# Wait for functions to be updated
echo "Waiting for Lambda functions to be ready..."
sleep 5

# Get stack outputs
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Clean up
rm -f lambda-package.zip

echo ""
echo "Next steps:"
echo "1. Run ./create_users.sh to create test users"
echo "2. Run ./test_api.sh to test the API"
