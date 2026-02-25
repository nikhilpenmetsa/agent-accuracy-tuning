#!/bin/bash
# Deploy AskHR Agent to Amazon Bedrock AgentCore Runtime

set -e

echo "=========================================="
echo "Deploying AskHR Agent to AgentCore Runtime"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    echo "Error: Must run from agent-agentcore/askhragent directory"
    exit 1
fi

# Verify agentcore CLI is available (check both Unix and Windows paths)
if ! command -v agentcore &> /dev/null && ! command -v agentcore.exe &> /dev/null; then
    echo "Error: agentcore CLI not found. Install with: pip install bedrock-agentcore"
    exit 1
fi

echo "Starting deployment..."
echo ""

# Deploy using AgentCore CLI (use .exe on Windows)
if command -v agentcore.exe &> /dev/null; then
    agentcore.exe launch
else
    agentcore launch
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Note the Agent ARN and HTTP endpoint URL from the output above"
echo "2. Check CloudWatch Logs: /aws/bedrock/agentcore/<agent-name>"
echo "3. View X-Ray traces in AWS Console"
echo "4. Test the deployed agent with: agentcore invoke --payload '{\"prompt\": \"What is the PTO policy?\"}'"
echo ""
echo "To update frontend with the new endpoint:"
echo "  - Update frontend/config.json with the AgentCore HTTP endpoint URL"
echo "  - Update CORS in main.py with the CloudFront domain"
echo ""
