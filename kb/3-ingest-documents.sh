#!/bin/bash

# Ingest Documents into Knowledge Base
# Uploads documents to S3 and starts ingestion job
# Prerequisites: Infrastructure and Knowledge Base must be set up

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
HR_DOCS_DIR="${HR_DOCS_DIR:-../hr-docs}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Step 3: Ingest Documents${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if HR docs directory exists
if [ ! -d "$SCRIPT_DIR/$HR_DOCS_DIR" ]; then
    echo -e "${RED}Error: HR documents directory '$HR_DOCS_DIR' not found${NC}"
    exit 1
fi

# Check if kb_config.json exists
if [ ! -f "$SCRIPT_DIR/kb_config.json" ]; then
    echo -e "${RED}Error: kb_config.json not found${NC}"
    echo "Please run: bash 2-setup-knowledge-base.sh first"
    exit 1
fi

# Detect Python command
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Load KB configuration
KB_ID=$($PYTHON_CMD -c "import json; print(json.load(open('$SCRIPT_DIR/kb_config.json'))['knowledge_base_id'])")
DS_ID=$($PYTHON_CMD -c "import json; print(json.load(open('$SCRIPT_DIR/kb_config.json'))['data_source_id'])")
BUCKET_NAME=$($PYTHON_CMD -c "import json; print(json.load(open('$SCRIPT_DIR/kb_config.json'))['bucket_name'])")

echo "Configuration:"
echo "  Knowledge Base ID: $KB_ID"
echo "  Data Source ID: $DS_ID"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  Documents: $HR_DOCS_DIR"
echo ""

# Upload HR documents to S3
echo -e "${YELLOW}Uploading HR documents to S3...${NC}"

aws s3 sync $SCRIPT_DIR/$HR_DOCS_DIR s3://$BUCKET_NAME/hr-docs/ \
    --region $REGION \
    --exclude ".*" \
    --delete

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Documents uploaded successfully${NC}"
    
    # Count uploaded files
    FILE_COUNT=$(find $SCRIPT_DIR/$HR_DOCS_DIR -type f -name "*.md" | wc -l)
    echo "  Uploaded $FILE_COUNT markdown files"
else
    echo -e "${RED}✗ Document upload failed${NC}"
    exit 1
fi

# Start ingestion job
echo ""
echo -e "${YELLOW}Starting knowledge base ingestion job...${NC}"

INGESTION_JOB_ID=$(aws bedrock-agent start-ingestion-job \
    --knowledge-base-id $KB_ID \
    --data-source-id $DS_ID \
    --region $REGION \
    --query 'ingestionJob.ingestionJobId' \
    --output text)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ingestion job started${NC}"
    echo "  Job ID: $INGESTION_JOB_ID"
    echo ""
    echo -e "${YELLOW}Waiting for ingestion to complete...${NC}"
    echo "This may take several minutes..."
    
    # Poll ingestion job status
    while true; do
        STATUS=$(aws bedrock-agent get-ingestion-job \
            --knowledge-base-id $KB_ID \
            --data-source-id $DS_ID \
            --ingestion-job-id $INGESTION_JOB_ID \
            --region $REGION \
            --query 'ingestionJob.status' \
            --output text)
        
        if [ "$STATUS" == "COMPLETE" ]; then
            echo -e "${GREEN}✓ Ingestion completed successfully${NC}"
            
            # Get ingestion statistics
            STATS=$(aws bedrock-agent get-ingestion-job \
                --knowledge-base-id $KB_ID \
                --data-source-id $DS_ID \
                --ingestion-job-id $INGESTION_JOB_ID \
                --region $REGION \
                --query 'ingestionJob.statistics' \
                --output json)
            
            echo ""
            echo "Ingestion Statistics:"
            echo "$STATS" | $PYTHON_CMD -m json.tool 2>/dev/null || echo "$STATS"
            break
        elif [ "$STATUS" == "FAILED" ]; then
            echo -e "${RED}✗ Ingestion failed${NC}"
            
            # Get failure reasons
            aws bedrock-agent get-ingestion-job \
                --knowledge-base-id $KB_ID \
                --data-source-id $DS_ID \
                --ingestion-job-id $INGESTION_JOB_ID \
                --region $REGION \
                --query 'ingestionJob.failureReasons' \
                --output text
            exit 1
        else
            echo "  Status: $STATUS"
            sleep 10
        fi
    done
else
    echo -e "${RED}✗ Failed to start ingestion job${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Document Ingestion Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Knowledge Base ID: $KB_ID"
echo "S3 Bucket: $BUCKET_NAME"
echo "Documents Ingested: $FILE_COUNT files"
echo ""
echo -e "${YELLOW}Your Knowledge Base is ready to use!${NC}"
echo ""
echo "Test it with:"
echo "  - AWS Console: Bedrock > Knowledge Bases"
echo "  - AWS CLI: aws bedrock-agent-runtime retrieve ..."
echo ""
echo -e "${YELLOW}To update documents:${NC}"
echo "  1. Modify files in $HR_DOCS_DIR"
echo "  2. Run: bash 3-ingest-documents.sh"
echo ""
