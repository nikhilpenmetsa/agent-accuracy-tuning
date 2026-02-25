#!/bin/bash
# Store AgentCore Memory ID in SSM Parameter Store

set -e

echo "Setting up SSM Parameter for AgentCore Memory ID..."
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if AGENTCORE_MEMORY_ID is set
if [ -z "$AGENTCORE_MEMORY_ID" ]; then
    echo "Error: AGENTCORE_MEMORY_ID not found in .env file"
    echo "Please run session-backend/1-setup-memory.sh first"
    exit 1
fi

echo "AgentCore Memory ID: $AGENTCORE_MEMORY_ID"
echo ""

# Store in SSM Parameter Store
echo "Storing in SSM Parameter Store..."
aws ssm put-parameter \
    --name "/hr-assistant/AGENTCORE_MEMORY_ID" \
    --value "$AGENTCORE_MEMORY_ID" \
    --type "String" \
    --overwrite \
    --region us-east-1

echo ""
echo "✓ AgentCore Memory ID stored in SSM Parameter Store"
echo "  Parameter: /hr-assistant/AGENTCORE_MEMORY_ID"
echo "  Value: $AGENTCORE_MEMORY_ID"
echo ""
echo "The agent will now use AgentCore Memory for conversation persistence."
