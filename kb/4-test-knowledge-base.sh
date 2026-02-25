#!/bin/bash

# Test Bedrock Knowledge Base
# Runs test queries against the knowledge base to verify it's working
# Prerequisites: Knowledge Base must be set up and documents ingested

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

REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Step 4: Test Knowledge Base${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if kb_config.json exists
if [ ! -f "$SCRIPT_DIR/kb_config.json" ]; then
    echo -e "${RED}Error: kb_config.json not found${NC}"
    echo "Please run the deployment steps first:"
    echo "  1. bash 1-deploy-infrastructure.sh"
    echo "  2. bash 2-setup-knowledge-base.sh"
    echo "  3. bash 3-ingest-documents.sh"
    exit 1
fi

# Detect Python command
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Load KB configuration
KB_ID=$($PYTHON_CMD -c "import json; print(json.load(open('$SCRIPT_DIR/kb_config.json'))['knowledge_base_id'])")

echo "Configuration:"
echo "  Knowledge Base ID: $KB_ID"
echo "  Region: $REGION"
echo ""

# Test queries
declare -a TEST_QUERIES=(
    "What are the company holidays?"
    "How much PTO do employees get?"
    "What is the parental leave policy?"
    "How do I submit an expense report?"
    "What are the health insurance options?"
)

echo -e "${YELLOW}Running test queries...${NC}"
echo ""

PASSED=0
FAILED=0

for QUERY in "${TEST_QUERIES[@]}"; do
    echo -e "${BLUE}Query: $QUERY${NC}"
    
    # Run retrieve query
    RESULT=$(aws bedrock-agent-runtime retrieve \
        --knowledge-base-id $KB_ID \
        --retrieval-query text="$QUERY" \
        --region $REGION \
        --output json 2>&1)
    
    if [ $? -eq 0 ]; then
        # Check if we got results
        RESULT_COUNT=$(echo "$RESULT" | $PYTHON_CMD -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('retrievalResults', [])))" 2>/dev/null || echo "0")
        
        if [ "$RESULT_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ Retrieved $RESULT_COUNT results${NC}"
            
            # Show first result snippet
            SNIPPET=$(echo "$RESULT" | $PYTHON_CMD -c "import sys, json; data=json.load(sys.stdin); print(data['retrievalResults'][0]['content']['text'][:200] + '...' if len(data['retrievalResults'][0]['content']['text']) > 200 else data['retrievalResults'][0]['content']['text'])" 2>/dev/null || echo "")
            
            if [ -n "$SNIPPET" ]; then
                echo -e "${BLUE}  Preview: $SNIPPET${NC}"
            fi
            
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠ No results found${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗ Query failed${NC}"
        echo "$RESULT"
        ((FAILED++))
    fi
    
    echo ""
done

# Test RetrieveAndGenerate (if model access is available)
echo -e "${YELLOW}Testing RetrieveAndGenerate (with response generation)...${NC}"
echo ""

TEST_QUESTION="What is the company's PTO policy?"
echo -e "${BLUE}Question: $TEST_QUESTION${NC}"

RAG_RESULT=$(aws bedrock-agent-runtime retrieve-and-generate \
    --input text="$TEST_QUESTION" \
    --retrieve-and-generate-configuration '{
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "'$KB_ID'",
            "modelArn": "arn:aws:bedrock:'$REGION'::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        }
    }' \
    --region $REGION \
    --output json 2>&1)

if [ $? -eq 0 ]; then
    # Extract generated response
    RESPONSE=$(echo "$RAG_RESULT" | $PYTHON_CMD -c "import sys, json; data=json.load(sys.stdin); print(data['output']['text'])" 2>/dev/null || echo "")
    
    if [ -n "$RESPONSE" ]; then
        echo -e "${GREEN}✓ Generated response successfully${NC}"
        echo ""
        echo -e "${BLUE}Response:${NC}"
        echo "$RESPONSE"
        echo ""
        
        # Show citations
        CITATIONS=$(echo "$RAG_RESULT" | $PYTHON_CMD -c "import sys, json; data=json.load(sys.stdin); citations=data.get('citations', []); print(f'{len(citations)} citations' if citations else 'No citations')" 2>/dev/null || echo "")
        echo -e "${BLUE}Citations: $CITATIONS${NC}"
        
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ Response generated but couldn't parse${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ RetrieveAndGenerate failed (may need model access)${NC}"
    echo "Error: $RAG_RESULT"
    echo ""
    echo "To enable this feature:"
    echo "1. Go to AWS Console > Bedrock > Model access"
    echo "2. Request access to Claude 3 Haiku"
    ((FAILED++))
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Results${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
fi
echo ""

if [ $PASSED -gt 0 ]; then
    echo -e "${GREEN}✓ Knowledge Base is working!${NC}"
    echo ""
    echo "You can now:"
    echo "  - Query via AWS Console: Bedrock > Knowledge Bases > Test"
    echo "  - Integrate with Bedrock Agents"
    echo "  - Use in your applications via AWS SDK"
    echo ""
else
    echo -e "${RED}✗ Knowledge Base tests failed${NC}"
    echo "Check that documents were ingested successfully"
    exit 1
fi
