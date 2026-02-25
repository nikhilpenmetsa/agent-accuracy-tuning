#!/bin/bash

# Deploy CloudFormation Infrastructure for Bedrock Knowledge Base
# Creates: S3 bucket, IAM roles, OpenSearch Serverless collection and policies

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
    echo "Error: config.env not found in root directory. Copy config.env.example to config.env"
    exit 1
fi

# Load stack-specific configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✓ Loaded KB stack configuration from .env"
else
    echo "Error: .env file not found. Copy .env.example to .env and configure."
    exit 1
fi

# Use environment variables with defaults
STACK_NAME="${STACK_NAME:-hr-assistant-kb-stack}"
TEMPLATE_FILE="${TEMPLATE_FILE:-cloudformation-template.yaml}"
REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Step 1: Deploy Infrastructure${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_NAME"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo "  Template: $TEMPLATE_FILE"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if template file exists
if [ ! -f "$SCRIPT_DIR/$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file '$TEMPLATE_FILE' not found${NC}"
    exit 1
fi

# Check if stack already exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_EXISTS" != "NOT_FOUND" ]; then
    echo -e "${YELLOW}Stack '$STACK_NAME' already exists with status: $STACK_EXISTS${NC}"
    echo ""
    read -p "Do you want to update the stack? (yes/no): " UPDATE_STACK
    
    if [ "$UPDATE_STACK" == "yes" ]; then
        echo ""
        echo -e "${YELLOW}Updating CloudFormation stack...${NC}"
        
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://$SCRIPT_DIR/$TEMPLATE_FILE \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $REGION 2>&1 | grep -v "No updates are to be performed" || true
        
        echo -e "${GREEN}✓ Stack update initiated${NC}"
        echo ""
        echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
        
        aws cloudformation wait stack-update-complete \
            --stack-name $STACK_NAME \
            --region $REGION 2>/dev/null || echo -e "${YELLOW}No changes detected${NC}"
        
        echo -e "${GREEN}✓ Stack update completed${NC}"
    else
        echo -e "${YELLOW}Skipping stack update${NC}"
    fi
else
    # Validate CloudFormation template
    echo -e "${YELLOW}Validating CloudFormation template...${NC}"
    aws cloudformation validate-template \
        --template-body file://$SCRIPT_DIR/$TEMPLATE_FILE \
        --region $REGION > /dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Template validation successful${NC}"
    else
        echo -e "${RED}✗ Template validation failed${NC}"
        exit 1
    fi

    # Deploy CloudFormation stack
    echo ""
    echo -e "${YELLOW}Deploying CloudFormation stack: $STACK_NAME${NC}"
    echo "Region: $REGION"
    echo ""

    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$SCRIPT_DIR/$TEMPLATE_FILE \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Stack creation failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Stack creation initiated${NC}"
    echo ""
    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    echo "This may take 5-10 minutes..."

    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $REGION

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Stack creation completed successfully${NC}"
    else
        echo -e "${RED}✗ Stack creation failed or timed out${NC}"
        echo "Check AWS Console for details"
        exit 1
    fi
fi

# Get stack outputs
echo ""
echo -e "${YELLOW}Retrieving stack outputs...${NC}"

BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
    --output text)

COLLECTION_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchCollectionEndpoint`].OutputValue' \
    --output text)

echo -e "${GREEN}✓ Stack outputs retrieved${NC}"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  OpenSearch Collection: $COLLECTION_ENDPOINT"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Infrastructure Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "S3 Bucket: $BUCKET_NAME"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Run: bash 2-setup-knowledge-base.sh"
echo "   (Creates OpenSearch index, Knowledge Base, and Data Source)"
echo ""
