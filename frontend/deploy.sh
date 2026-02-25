#!/bin/bash

# Frontend Deployment Script
# Deploys the frontend to S3 and CloudFront

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

echo "🚀 Deploying AskHR Frontend..."

# Deploy CloudFormation stack
echo "📦 Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        StackName="$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --no-fail-on-empty-changeset \
    --region ${AWS_REGION}

# Get S3 bucket and CloudFront distribution from outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

echo "✓ S3 Bucket: $BUCKET_NAME"
echo "✓ CloudFront Distribution: $CLOUDFRONT_ID"
echo "✓ CloudFront URL: $CLOUDFRONT_URL"

# Generate config.json
echo "⚙️  Generating config.json..."
bash generate-config.sh

# Upload files to S3
echo "📤 Uploading files to S3..."

# Upload static assets with long cache
aws s3 sync . "s3://$BUCKET_NAME/" \
    --exclude "*.sh" \
    --exclude ".env" \
    --exclude "*.yaml" \
    --exclude "README.md" \
    --exclude ".git/*" \
    --exclude "*.html" \
    --exclude "config.json" \
    --cache-control "public, max-age=31536000" \
    --region ${AWS_REGION}

# Upload HTML and config with no-cache
aws s3 cp index.html "s3://$BUCKET_NAME/index.html" \
    --content-type "text/html" \
    --cache-control "no-cache" \
    --region ${AWS_REGION}

aws s3 cp config.json "s3://$BUCKET_NAME/config.json" \
    --content-type "application/json" \
    --cache-control "no-cache" \
    --region ${AWS_REGION}

echo "✓ Files uploaded"

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_ID" \
    --paths "/*" \
    --region ${AWS_REGION} > /dev/null

echo "✓ Cache invalidated"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Frontend URL: $CLOUDFRONT_URL"
echo ""
echo "📝 Next steps:"
echo "   1. Update agent CORS to allow: *.cloudfront.net"
echo "   2. Redeploy agent: cd ../agent-agentcore/askhragent && bash 2-deploy-to-agentcore.sh"
echo ""
echo "📝 Test users:"
echo "   • john.doe@acme.com / Password123"
echo "   • jane.smith@acme.com / Password123"
echo "   • bob.johnson@acme.com / Password123"
echo ""
