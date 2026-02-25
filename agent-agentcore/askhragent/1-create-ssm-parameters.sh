#!/bin/bash
# Create SSM Parameter Store parameters for AskHR Agent

set -e

echo "Creating SSM Parameter Store parameters for AskHR Agent..."

# Load configuration from .env (handle Windows line endings)
export $(grep -v '^#' .env | sed 's/\r$//' | xargs)

# Create parameters
aws ssm put-parameter \
    --name "/hr-assistant/KB_ID" \
    --value "${KB_ID}" \
    --type "String" \
    --overwrite \
    --description "Bedrock Knowledge Base ID for HR documents"

aws ssm put-parameter \
    --name "/hr-assistant/CASE_API_URL" \
    --value "${CASE_API_URL}" \
    --type "String" \
    --overwrite \
    --description "Case Backend API Gateway URL"

aws ssm put-parameter \
    --name "/hr-assistant/MODEL_ID" \
    --value "${MODEL_ID}" \
    --type "String" \
    --overwrite \
    --description "Bedrock model ID for the agent"

echo "✓ SSM parameters created successfully"
echo ""
echo "Created parameters:"
echo "  /hr-assistant/KB_ID = ${KB_ID}"
echo "  /hr-assistant/CASE_API_URL = ${CASE_API_URL}"
echo "  /hr-assistant/MODEL_ID = ${MODEL_ID}"
