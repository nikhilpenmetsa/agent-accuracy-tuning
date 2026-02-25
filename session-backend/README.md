# Session Backend

Session management API for HR Assistant with AgentCore Memory integration. Provides authenticated REST endpoints to manage conversation sessions.

## What It Does

Creates an AWS stack with:
- API Gateway with 5 endpoints (create, list, get, update, delete sessions)
- Cognito authentication (reuses case-backend User Pool)
- DynamoDB for session metadata storage
- AgentCore Memory for conversation history
- Python Lambda functions

## Setup

1. Ensure `../config.env` exists with:
```bash
PROJECT_NAME=your-project-name
AWS_REGION=us-east-1
```

2. Ensure case-backend is deployed (for Cognito User Pool)

## How to Run

```bash
# Step 1: Setup AgentCore Memory (one-time)
bash 1-setup-memory.sh

# Step 2: Deploy the stack
bash 2-deploy.sh

# Step 3: Test the API
bash 3-test-api.sh

# Clean up
bash cleanup.sh
```

## Configuration

Stack name is automatically set to `${PROJECT_NAME}-session-backend-stack` using the PROJECT_NAME from `../config.env`.

The stack reuses the Cognito User Pool from case-backend for authentication.

## API Endpoints

All endpoints require Cognito authentication token in Authorization header.

**POST /sessions** - Create a new session
```json
{"session_title": "Benefits questions"}
```

**GET /sessions** - List all sessions for authenticated user

**GET /sessions/{session_id}** - Get session details

**PATCH /sessions/{session_id}** - Update session metadata
```json
{"session_title": "Updated title"}
```

**DELETE /sessions/{session_id}** - Delete session metadata

## Architecture

Session metadata (title, timestamps) stored in DynamoDB for fast listing.
Conversation messages stored in AgentCore Memory for intelligent retrieval.
Agent integration via Strands AgentCoreMemorySessionManager.
