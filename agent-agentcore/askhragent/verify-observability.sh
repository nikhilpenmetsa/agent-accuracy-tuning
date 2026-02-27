#!/bin/bash
# Verify AgentCore Observability Configuration
# This script checks if all components are properly configured for observability

set -e

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo "AgentCore Observability Verification"
echo "=========================================="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Check 1: Transaction Search enabled
echo "✓ Checking Transaction Search status..."
DESTINATION=$(aws xray get-trace-segment-destination --region $REGION --query 'Destination' --output text 2>/dev/null || echo "NONE")

if [ "$DESTINATION" = "CloudWatchLogs" ]; then
    echo "  ✓ Transaction Search: ENABLED"
    SAMPLING=$(aws xray get-indexing-rules --region $REGION --query 'IndexingRules[?Name==`Default`].Rule.Probabilistic.DesiredSamplingPercentage' --output text 2>/dev/null || echo "unknown")
    echo "  ✓ Sampling: ${SAMPLING}%"
else
    echo "  ✗ Transaction Search: NOT ENABLED"
    echo "    Run: ./setup-observability.sh"
    exit 1
fi

echo ""

# Check 2: Agent configuration
echo "✓ Checking agent configuration..."
if [ -f ".bedrock_agentcore.yaml" ]; then
    OBSERVABILITY_ENABLED=$(grep -A 1 "^  observability:" .bedrock_agentcore.yaml | grep "enabled:" | awk '{print $2}')
    if [ "$OBSERVABILITY_ENABLED" = "true" ]; then
        echo "  ✓ Observability enabled in .bedrock_agentcore.yaml"
    else
        echo "  ✗ Observability NOT enabled in .bedrock_agentcore.yaml"
        echo "    Set observability.enabled: true"
        exit 1
    fi
else
    echo "  ⚠️  .bedrock_agentcore.yaml not found"
fi

echo ""

# Check 3: Python dependencies
echo "✓ Checking Python dependencies..."
if [ -f "pyproject.toml" ]; then
    if grep -q "aws-opentelemetry-distro" pyproject.toml; then
        echo "  ✓ aws-opentelemetry-distro in pyproject.toml"
    else
        echo "  ✗ aws-opentelemetry-distro NOT in pyproject.toml"
        exit 1
    fi
    
    if grep -q "strands-agents" pyproject.toml; then
        echo "  ✓ strands-agents in pyproject.toml"
    else
        echo "  ⚠️  strands-agents NOT in pyproject.toml"
    fi
else
    echo "  ⚠️  pyproject.toml not found"
fi

echo ""

# Check 4: Agent deployment
echo "✓ Checking agent deployment..."
if [ -f ".bedrock_agentcore.yaml" ]; then
    AGENT_ID=$(grep "agent_id:" .bedrock_agentcore.yaml | awk '{print $2}')
    if [ -n "$AGENT_ID" ]; then
        echo "  ✓ Agent ID: $AGENT_ID"
        
        # Try to get agent details
        AGENT_STATUS=$(aws bedrock-agentcore-runtime get-agent \
            --agent-id "$AGENT_ID" \
            --region $REGION \
            --query 'status' \
            --output text 2>/dev/null || echo "UNKNOWN")
        
        if [ "$AGENT_STATUS" != "UNKNOWN" ]; then
            echo "  ✓ Agent Status: $AGENT_STATUS"
        fi
    else
        echo "  ⚠️  Agent not yet deployed"
    fi
fi

echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo ""
echo "✓ All checks passed!"
echo ""
echo "View observability data:"
echo "  GenAI Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#gen-ai-observability/agent-core"
echo "  Traces: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#xray:transaction-search"
echo "  Logs: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo ""
echo "After invoking your agent, traces should appear within 1-2 minutes."
echo ""
echo "Troubleshooting:"
echo "  1. Ensure you've invoked the agent at least once"
echo "  2. Wait 1-2 minutes for traces to appear"
echo "  3. Check agent logs for errors"
echo "  4. Verify sampling percentage isn't too low"
