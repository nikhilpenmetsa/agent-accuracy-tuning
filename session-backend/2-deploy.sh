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
CASE_BACKEND_STACK="${PROJECT_NAME}-case-backend-stack"

echo "=========================================="
echo "Deploying Session Backend API Stack"
echo "=========================================="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Case Backend Stack: $CASE_BACKEND_STACK"
echo ""

# Check if case-backend stack exists
if ! aws cloudformation describe-stacks --stack-name ${CASE_BACKEND_STACK} --region ${REGION} &> /dev/null; then
    echo "Error: case-backend stack not found. Please deploy case-backend first."
    exit 1
fi

# Check if AgentCore Memory ID is set
if [ -z "$AGENTCORE_MEMORY_ID" ] || [ "$AGENTCORE_MEMORY_ID" = "your-memory-id-here" ]; then
    echo "Error: AGENTCORE_MEMORY_ID not set in .env"
    echo "Please run: bash 1-setup-memory.sh"
    exit 1
fi

# Package Lambda functions
echo "Packaging Lambda functions..."

# Install dependencies if requirements.txt exists
if [ -f "lambda/requirements.txt" ]; then
    echo "Installing Lambda dependencies for Linux..."
    pip install -r lambda/requirements.txt -t lambda/ \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --upgrade \
        --quiet 2>/dev/null || \
    pip install -r lambda/requirements.txt -t lambda/ --upgrade --quiet
fi

python3 -c "
import zipfile
import os

with zipfile.ZipFile('lambda-package.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('lambda'):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.pyc'):
                continue
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

# Export User Pool ARN from case-backend for CloudFormation import
echo "Getting Cognito User Pool ARN from case-backend..."
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name ${CASE_BACKEND_STACK} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

USER_POOL_ARN="arn:aws:cognito-idp:${REGION}:$(aws sts get-caller-identity --query Account --output text):userpool/${USER_POOL_ID}"

# Check if export exists, if not create it
if ! aws cloudformation list-exports --region ${REGION} | grep -q "${CASE_BACKEND_STACK}-UserPoolArn"; then
    echo "Creating User Pool ARN export in case-backend stack..."
    # We'll need to update case-backend CloudFormation to export this
    echo "Warning: case-backend stack needs to export UserPoolArn"
    echo "For now, we'll pass it as a parameter"
fi

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides \
        StackName=${STACK_NAME} \
        CaseBackendStackName=${CASE_BACKEND_STACK} \
    --capabilities CAPABILITY_IAM \
    --region ${REGION}

# Update Lambda function code
echo "Updating Lambda function code..."
FUNCTIONS=(
    "${STACK_NAME}-create-session"
    "${STACK_NAME}-list-sessions"
    "${STACK_NAME}-get-session"
    "${STACK_NAME}-update-session"
    "${STACK_NAME}-delete-session"
    "${STACK_NAME}-get-session-messages"
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

# Get stack outputs and save to file
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs' \
    --output json > outputs.json

aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Clean up
rm -f lambda-package.zip

echo ""
echo "Outputs saved to outputs.json"
echo ""
echo "Next steps:"
echo "1. Run ./3-test-api.sh to test the API"
echo "2. Update frontend to use the Session API"
