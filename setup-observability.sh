#!/bin/bash
# One-time setup: Enable CloudWatch Transaction Search for AgentCore Observability
# This is an account-level setting required to view traces and spans in CloudWatch

set -e

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo "AgentCore Observability Setup"
echo "=========================================="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Check if Transaction Search is already enabled
echo "Checking if Transaction Search is enabled..."
CURRENT_DESTINATION=$(aws xray get-trace-segment-destination --region $REGION --query 'Destination' --output text 2>/dev/null || echo "NONE")

if [ "$CURRENT_DESTINATION" = "CloudWatchLogs" ]; then
    echo "✓ Transaction Search is already enabled"
    echo "  Trace destination: CloudWatchLogs"
    echo ""
    
    # Check indexing rule
    SAMPLING=$(aws xray get-indexing-rules --region $REGION --query 'IndexingRules[?Name==`Default`].Rule.Probabilistic.DesiredSamplingPercentage' --output text 2>/dev/null || echo "unknown")
    if [ "$SAMPLING" != "unknown" ]; then
        echo "  Sampling percentage: ${SAMPLING}%"
    fi
    
    echo ""
    echo "No action needed. You can view observability data at:"
    echo "https://console.aws.amazon.com/cloudwatch/home?region=$REGION#gen-ai-observability/agent-core"
    exit 0
fi

echo "⚠️  Transaction Search is NOT enabled"
echo "   Current destination: $CURRENT_DESTINATION"
echo ""
echo "Enabling Transaction Search..."
echo ""

# Step 1: Create CloudWatch Logs resource policy
echo "Step 1: Creating CloudWatch Logs resource policy..."

POLICY_DOCUMENT=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TransactionSearchXRayAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "xray.amazonaws.com"
      },
      "Action": "logs:PutLogEvents",
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:aws/spans:*",
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/application-signals/data:*"
      ],
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:xray:${REGION}:${ACCOUNT_ID}:*"
        },
        "StringEquals": {
          "aws:SourceAccount": "${ACCOUNT_ID}"
        }
      }
    }
  ]
}
EOF
)

aws logs put-resource-policy \
    --policy-name TransactionSearchXRayAccess \
    --policy-document "$POLICY_DOCUMENT" \
    --region $REGION > /dev/null

echo "✓ Resource policy created"

# Step 2: Configure trace segment destination
echo "Step 2: Configuring trace segment destination..."

aws xray update-trace-segment-destination \
    --destination CloudWatchLogs \
    --region $REGION > /dev/null

echo "✓ Trace destination set to CloudWatchLogs"

# Step 3: Configure indexing rule (1% sampling - free tier)
echo "Step 3: Configuring indexing rule (1% sampling)..."

aws xray update-indexing-rule \
    --name "Default" \
    --rule '{"Probabilistic": {"DesiredSamplingPercentage": 1}}' \
    --region $REGION > /dev/null

echo "✓ Indexing rule configured (1% sampling)"

echo ""
echo "=========================================="
echo "Transaction Search Enabled Successfully!"
echo "=========================================="
echo ""
echo "⏱️  Important: Wait 10 minutes for spans to become available"
echo ""
echo "After 10 minutes, view observability data at:"
echo "https://console.aws.amazon.com/cloudwatch/home?region=$REGION#gen-ai-observability/agent-core"
echo ""
echo "What you'll see:"
echo "  • Agents View - All your agents and their metrics"
echo "  • Sessions View - Conversation sessions"
echo "  • Traces View - Detailed execution traces"
echo ""
echo "CloudWatch Logs:"
echo "  • Agent logs: /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT"
echo "  • Spans: /aws/spans/default"
echo ""
echo "To adjust sampling percentage later:"
echo "  aws xray update-indexing-rule --name Default \\"
echo "    --rule '{\"Probabilistic\": {\"DesiredSamplingPercentage\": 10}}' \\"
echo "    --region $REGION"
