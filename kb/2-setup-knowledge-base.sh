#!/bin/bash

# Setup Bedrock Knowledge Base
# Creates: OpenSearch index, Bedrock Knowledge Base, Data Source
# Prerequisites: Infrastructure stack must be deployed (run 1-deploy-infrastructure.sh first)

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load global configuration
if [ -f "$SCRIPT_DIR/../config.env" ]; then
    set -a
    source "$SCRIPT_DIR/../config.env"
    set +a
else
    echo "Error: config.env not found"
    exit 1
fi

# Load stack-specific configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "Error: .env file not found"
    exit 1
fi

STACK_NAME="${STACK_NAME:-hr-assistant-kb-stack}"
REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Step 2: Setup Knowledge Base${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python is not installed${NC}"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Check if required Python packages are installed
echo -e "${YELLOW}Checking Python dependencies...${NC}"
$PYTHON_CMD -c "import opensearchpy, boto3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install opensearch-py boto3 requests-aws4auth
fi
echo -e "${GREEN}✓ Python dependencies ready${NC}"

# Check if infrastructure stack exists
echo ""
echo -e "${YELLOW}Checking infrastructure stack...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
    echo -e "${RED}Error: Infrastructure stack '$STACK_NAME' not found${NC}"
    echo "Please run: bash 1-deploy-infrastructure.sh first"
    exit 1
elif [ "$STACK_STATUS" != "CREATE_COMPLETE" ] && [ "$STACK_STATUS" != "UPDATE_COMPLETE" ]; then
    echo -e "${RED}Error: Stack is in state: $STACK_STATUS${NC}"
    echo "Stack must be in CREATE_COMPLETE or UPDATE_COMPLETE state"
    exit 1
fi

echo -e "${GREEN}✓ Infrastructure stack is ready${NC}"

# Run Python setup script
echo ""
echo -e "${YELLOW}Running Knowledge Base setup...${NC}"
echo "This will:"
echo "  1. Create OpenSearch Serverless index"
echo "  2. Create Bedrock Knowledge Base"
echo "  3. Create S3 Data Source"
echo ""

cd "$SCRIPT_DIR"
$PYTHON_CMD setup_kb.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Knowledge Base Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # Display KB info
    if [ -f "kb_config.json" ]; then
        KB_ID=$($PYTHON_CMD -c "import json; print(json.load(open('kb_config.json'))['knowledge_base_id'])")
        DS_ID=$($PYTHON_CMD -c "import json; print(json.load(open('kb_config.json'))['data_source_id'])")
        
        echo "Knowledge Base ID: $KB_ID"
        echo "Data Source ID: $DS_ID"
        echo ""
        echo -e "${YELLOW}Next Steps:${NC}"
        echo "1. Run: bash 3-ingest-documents.sh"
        echo "   (Uploads HR documents and starts ingestion)"
        echo ""
    fi
else
    echo -e "${RED}✗ Knowledge Base setup failed${NC}"
    exit 1
fi
