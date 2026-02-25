#!/bin/bash

# Cleanup script - deletes the frontend stack and S3 bucket

set -e

# Load environment variables
if [ -f ../config.env ]; then
    source ../config.env
else
    echo "Error: config.env not found"
    exit 1
fi

if [ -f .env ]; then
    source .env
else
    echo "Error: .env not found"
    exit 1
fi

echo "🗑️  Cleaning up AskHR Frontend..."

# Get S3 bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || echo "")

if [ -n "$BUCKET_NAME" ]; then
    echo "📦 Emptying S3 bucket: $BUCKET_NAME"
    aws s3 rm "s3://$BUCKET_NAME" --recursive --region ${AWS_REGION}
fi

# Delete CloudFormation stack
echo "🗑️  Deleting CloudFormation stack: $STACK_NAME"
aws cloudformation delete-stack \
    --stack-name "$STACK_NAME" \
    --region ${AWS_REGION}

echo "⏳ Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region ${AWS_REGION}

echo "✅ Cleanup complete!"
