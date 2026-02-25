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
echo "Cleaning up Session Backend Stack"
echo "=========================================="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Check for --force flag
if [ "$1" != "--force" ]; then
    read -p "Are you sure you want to delete the stack? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cleanup cancelled"
        exit 0
    fi
else
    echo "Force mode: Skipping confirmation"
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

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name ${STACK_NAME} \
    --region ${REGION}

# Clean up local files
rm -f outputs.json
rm -f lambda-package.zip

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Note: AgentCore Memory resource was NOT deleted."
echo "To delete it manually:"
echo "1. Go to AWS Console > Bedrock > AgentCore > Memory"
echo "2. Delete the memory resource: ${AGENTCORE_MEMORY_NAME}"
echo ""
echo "Or use the AWS CLI:"
echo "aws bedrock-agent delete-memory --memory-id <MEMORY_ID> --region ${REGION}"
