#!/bin/bash
# Force API Gateway redeployment

set -e

echo "=========================================="
echo "Force API Gateway Redeployment"
echo "=========================================="

# Get the REST API ID
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='hr-assistant-session-backend-stack-api'].id" \
    --output text \
    --region us-east-1)

echo "REST API ID: $REST_API_ID"

# Create new deployment
echo "Creating new deployment..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id "$REST_API_ID" \
    --stage-name prod \
    --description "Manual deployment with CORS OPTIONS" \
    --region us-east-1 \
    --query 'id' \
    --output text)

echo "New deployment ID: $DEPLOYMENT_ID"
echo ""
echo "✓ API redeployed successfully!"
echo ""
echo "Test CORS with:"
echo "  curl -X OPTIONS https://wyut1ctgc1.execute-api.us-east-1.amazonaws.com/prod/sessions \\"
echo "    -H 'Origin: http://localhost:8000' \\"
echo "    -H 'Access-Control-Request-Method: GET' -i"
