# Case Backend

Mock Workday API for testing HR agents. Provides authenticated REST endpoints to create and retrieve HR cases.

## What It Does

Creates an AWS stack with:
- API Gateway with 3 endpoints (get case types, create case, list cases)
- Cognito authentication
- DynamoDB for case storage
- Python Lambda functions

## Setup

1. Copy environment template:
```bash
cp .env.example .env
```

2. Ensure `../config.env` exists with:
```bash
PROJECT_NAME=your-project-name
AWS_REGION=us-east-1
```

3. Customize `.env` if needed (test users, etc.)

## How to Run

```bash
# Deploy everything
bash deploy.sh

# Create test users
bash create_users.sh

# Test the API
bash test_api.sh

# Clean up
bash cleanup.sh
```

## Configuration

Stack name is automatically set to `${PROJECT_NAME}-case-backend-stack` using the PROJECT_NAME from `../config.env`.

Test users are configured in `.env`:
- TEST_USER_1_EMAIL / TEST_USER_1_PASSWORD
- TEST_USER_2_EMAIL / TEST_USER_2_PASSWORD
- TEST_USER_3_EMAIL / TEST_USER_3_PASSWORD

## API Endpoints

All endpoints require Cognito authentication token in Authorization header.

**GET /case-types** - List available case types (compensation, benefits, pto, etc.)

**POST /cases** - Create a case
```json
{"case_type": "pto", "description": "Request for vacation"}
```

**GET /cases** - List all cases for authenticated user
