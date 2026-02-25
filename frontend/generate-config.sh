#!/bin/bash

# Generate config.json from CloudFormation outputs and AgentCore config

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

echo "📋 Generating config.json..."

# Get Cognito config from case-backend stack
CASE_BACKEND_STACK="${PROJECT_NAME}-case-backend-stack"

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$CASE_BACKEND_STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

echo "✓ Cognito User Pool ID: $USER_POOL_ID"
echo "✓ Cognito Client ID: $CLIENT_ID"
echo "✓ Case API URL: $API_URL"

# Get AgentCore endpoint from agent config
AGENT_CONFIG="../agent-agentcore/askhragent/.bedrock_agentcore.yaml"

if [ ! -f "$AGENT_CONFIG" ]; then
    echo "Error: AgentCore config not found at $AGENT_CONFIG"
    exit 1
fi

# Extract agent ARN from YAML
AGENT_ARN=$(grep "agent_arn:" "$AGENT_CONFIG" | head -1 | awk '{print $2}' | tr -d '\r')

if [ -z "$AGENT_ARN" ]; then
    echo "Error: Could not find agent_arn in $AGENT_CONFIG"
    exit 1
fi

# URL encode the ARN
ENCODED_ARN=$(echo "$AGENT_ARN" | sed 's/:/%3A/g' | sed 's/\//%2F/g' | tr -d '\r')

# Build AgentCore HTTP endpoint
AGENT_ENDPOINT="https://bedrock-agentcore.${AWS_REGION}.amazonaws.com/runtimes/${ENCODED_ARN}/invocations"

echo "✓ Agent ARN: $AGENT_ARN"
echo "✓ Agent Endpoint: $AGENT_ENDPOINT"

# Generate config.json using printf for clean output
printf '{
    "ENABLE_QUICK_LOGIN": %s,
    "COGNITO_USER_POOL_ID": "%s",
    "COGNITO_CLIENT_ID": "%s",
    "API_BASE_URL": "%s",
    "AWS_REGION": "%s",
    "AGENT_ENDPOINT": "%s"
}\n' \
    "${ENABLE_QUICK_LOGIN:-true}" \
    "$USER_POOL_ID" \
    "$CLIENT_ID" \
    "$API_URL" \
    "${AWS_REGION}" \
    "$AGENT_ENDPOINT" > config.json

echo "✓ config.json generated"
echo ""
cat config.json
