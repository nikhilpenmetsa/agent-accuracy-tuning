#!/bin/bash
# Fix CORS by manually adding OPTIONS methods to API Gateway

set -e

echo "=========================================="
echo "Adding CORS OPTIONS methods to Session API"
echo "=========================================="

# Get the REST API ID
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='hr-assistant-session-backend-stack-api'].id" \
    --output text \
    --region us-east-1)

if [ -z "$REST_API_ID" ]; then
    echo "Error: Could not find REST API"
    exit 1
fi

echo "REST API ID: $REST_API_ID"

# Get resource IDs
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id "$REST_API_ID" \
    --query "items[?path=='/'].id" \
    --output text \
    --region us-east-1)

SESSIONS_ID=$(aws apigateway get-resources \
    --rest-api-id "$REST_API_ID" \
    --query "items[?path=='/sessions'].id" \
    --output text \
    --region us-east-1)

SESSION_ID_RESOURCE=$(aws apigateway get-resources \
    --rest-api-id "$REST_API_ID" \
    --query "items[?path=='/sessions/{session_id}'].id" \
    --output text \
    --region us-east-1)

echo "Sessions resource ID: $SESSIONS_ID"
echo "Session ID resource ID: $SESSION_ID_RESOURCE"

# Function to create OPTIONS method
create_options_method() {
    local RESOURCE_ID=$1
    local METHODS=$2
    local PATH=$3
    
    echo ""
    echo "Creating OPTIONS method for $PATH..."
    
    # Check if OPTIONS already exists
    EXISTING=$(aws apigateway get-method \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --region us-east-1 2>&1 || echo "not found")
    
    if [[ "$EXISTING" != *"not found"* ]]; then
        echo "  OPTIONS method already exists, deleting first..."
        aws apigateway delete-method \
            --rest-api-id "$REST_API_ID" \
            --resource-id "$RESOURCE_ID" \
            --http-method OPTIONS \
            --region us-east-1
    fi
    
    # Create OPTIONS method
    aws apigateway put-method \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region us-east-1
    
    # Create method response
    aws apigateway put-method-response \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters \
            "method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true" \
        --region us-east-1
    
    # Create integration
    aws apigateway put-integration \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region us-east-1
    
    # Create integration response
    aws apigateway put-integration-response \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters \
            "method.response.header.Access-Control-Allow-Headers='Content-Type,Authorization',method.response.header.Access-Control-Allow-Methods='$METHODS',method.response.header.Access-Control-Allow-Origin='*'" \
        --region us-east-1
    
    echo "  ✓ OPTIONS method created for $PATH"
}

# Create OPTIONS for /sessions
create_options_method "$SESSIONS_ID" "GET,POST,OPTIONS" "/sessions"

# Create OPTIONS for /sessions/{session_id}
create_options_method "$SESSION_ID_RESOURCE" "GET,PATCH,DELETE,OPTIONS" "/sessions/{session_id}"

# Create new deployment
echo ""
echo "Creating new API deployment..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id "$REST_API_ID" \
    --stage-name prod \
    --description "CORS fix deployment" \
    --region us-east-1 \
    --query 'id' \
    --output text)

echo "  ✓ Deployment created: $DEPLOYMENT_ID"

echo ""
echo "=========================================="
echo "CORS OPTIONS methods added successfully!"
echo "=========================================="
echo ""
echo "Test with:"
echo "  curl -X OPTIONS https://wyut1ctgc1.execute-api.us-east-1.amazonaws.com/prod/sessions \\"
echo "    -H 'Origin: http://localhost:8000' \\"
echo "    -H 'Access-Control-Request-Method: GET' \\"
echo "    -H 'Access-Control-Request-Headers: Authorization,Content-Type' -i"
