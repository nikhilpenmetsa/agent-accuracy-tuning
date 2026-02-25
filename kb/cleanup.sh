#!/bin/bash

# Cleanup Bedrock Knowledge Base CloudFormation Stack
# This script removes all resources created by the deployment

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load global configuration first
if [ -f "$SCRIPT_DIR/../config.env" ]; then
    set -a  # Automatically export all variables
    source "$SCRIPT_DIR/../config.env"
    set +a
    echo "✓ Loaded global configuration from config.env"
else
    echo "Warning: config.env not found. Using defaults."
fi

# Load stack-specific configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✓ Loaded KB stack configuration from .env"
else
    echo "Warning: .env file not found. Using defaults."
fi

# Use environment variables with defaults
STACK_NAME="${STACK_NAME:-hr-assistant-kb-stack}"
REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Bedrock Knowledge Base Cleanup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_NAME"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if stack exists
echo -e "${YELLOW}Checking if stack exists...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
    echo -e "${YELLOW}Stack '$STACK_NAME' not found. Nothing to clean up.${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Stack found: $STACK_NAME${NC}"
echo "  Status: $STACK_STATUS"

# Get bucket name before deletion
echo ""
echo -e "${YELLOW}Retrieving S3 bucket name...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$BUCKET_NAME" ]; then
    echo -e "${GREEN}✓ Bucket found: $BUCKET_NAME${NC}"
    
    # Empty the S3 bucket
    echo ""
    echo -e "${YELLOW}Emptying S3 bucket...${NC}"
    
    # Delete all object versions
    aws s3api list-object-versions \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --output json \
        --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
    aws s3api delete-objects \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --delete file:///dev/stdin 2>/dev/null || true
    
    # Delete all delete markers
    aws s3api list-object-versions \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --output json \
        --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
    aws s3api delete-objects \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --delete file:///dev/stdin 2>/dev/null || true
    
    echo -e "${GREEN}✓ S3 bucket emptied${NC}"
else
    echo -e "${YELLOW}No S3 bucket found or already deleted${NC}"
fi

# Delete Knowledge Base and Data Source if they exist (created outside CFN)
if [ -f "kb_config.json" ]; then
    echo ""
    echo -e "${YELLOW}Deleting Knowledge Base resources...${NC}"
    
    KB_ID=$(python -c "import json; print(json.load(open('kb_config.json'))['knowledge_base_id'])" 2>/dev/null || echo "")
    DS_ID=$(python -c "import json; print(json.load(open('kb_config.json'))['data_source_id'])" 2>/dev/null || echo "")
    
    if [ -n "$DS_ID" ]; then
        echo "  Deleting data source: $DS_ID"
        aws bedrock-agent delete-data-source \
            --knowledge-base-id $KB_ID \
            --data-source-id $DS_ID \
            --region $REGION 2>/dev/null || true
    fi
    
    if [ -n "$KB_ID" ]; then
        echo "  Deleting knowledge base: $KB_ID"
        aws bedrock-agent delete-knowledge-base \
            --knowledge-base-id $KB_ID \
            --region $REGION 2>/dev/null || true
    fi
    
    rm -f kb_config.json
    echo -e "${GREEN}✓ Knowledge Base resources deleted${NC}"
fi

# Confirmation prompt
echo ""
echo -e "${RED}WARNING: This will delete all resources in the stack!${NC}"
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

# Delete CloudFormation stack
echo ""
echo -e "${YELLOW}Deleting CloudFormation stack...${NC}"

aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deletion initiated${NC}"
else
    echo -e "${RED}✗ Failed to initiate stack deletion${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Waiting for stack deletion to complete...${NC}"
echo "This may take several minutes..."

aws cloudformation wait stack-delete-complete \
    --stack-name $STACK_NAME \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deleted successfully${NC}"
else
    echo -e "${RED}✗ Stack deletion failed or timed out${NC}"
    echo "Check AWS Console for details"
    echo ""
    echo "Common issues:"
    echo "- S3 bucket not empty (should be handled automatically)"
    echo "- Resources in use by other services"
    echo "- IAM roles still attached to resources"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All resources have been removed:"
echo "  ✓ S3 bucket and contents"
echo "  ✓ Bedrock Knowledge Base"
echo "  ✓ OpenSearch Serverless collection"
echo "  ✓ IAM roles and policies"
echo "  ✓ CloudFormation stack"
echo ""
