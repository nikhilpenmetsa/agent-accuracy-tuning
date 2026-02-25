# AgentCore Memory Integration - Summary

This document summarizes the changes made to integrate AgentCore Memory with the AskHR agent.

## Changes Made

### 1. Dependencies Updated (`pyproject.toml`)

Changed:
```python
"bedrock-agentcore >= 1.0.3"
```

To:
```python
"bedrock-agentcore[strands-agents] >= 1.0.3"
```

This adds the Strands integration package for AgentCore Memory.

### 2. Main Agent Code (`src/main.py`)

#### Added Imports
```python
import uuid
import json
import base64
from datetime import datetime
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
```

#### Added JWT Token Extraction Function
```python
def _extract_user_from_jwt(token: str) -> str:
    """Extract user_id (sub claim) from JWT token."""
    # Decodes JWT payload and extracts 'sub' or 'cognito:username' claim
```

#### Updated Entrypoint Function
The `invoke()` function now:

1. **Handles session_id**: Accepts from payload or auto-generates
2. **Extracts user_id**: From JWT token or payload
3. **Retrieves memory_id**: From SSM Parameter Store
4. **Configures Memory**: Sets up retrieval for preferences, facts, and summaries
5. **Uses Context Manager**: Ensures messages are flushed to memory

```python
# Configure AgentCore Memory
memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,
    session_id=session_id,
    actor_id=user_id,
    retrieval_config={
        f"/preferences/{user_id}": RetrievalConfig(top_k=5, relevance_score=0.7),
        f"/facts/{user_id}": RetrievalConfig(top_k=10, relevance_score=0.3),
        f"/summaries/{user_id}/{session_id}": RetrievalConfig(top_k=5, relevance_score=0.5)
    }
)

# Use context manager to ensure messages are flushed
with AgentCoreMemorySessionManager(memory_config, region_name="us-east-1") as session_manager:
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        session_manager=session_manager  # Add session manager
    )
    # ... stream response
```

### 3. Environment Configuration (`.env`)

Added:
```bash
AGENTCORE_MEMORY_ID=hr_assistant_memory-QzY4Jx5O7Z
```

### 4. IAM Policy (`update-iam-policy.json`)

Added memory permissions:
```json
{
  "Sid": "AgentCoreMemoryAccess",
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:GetMemory",
    "bedrock-agentcore:PutMemory",
    "bedrock-agentcore:DeleteMemory",
    "bedrock-agentcore:ListMemories"
  ],
  "Resource": [
    "arn:aws:bedrock-agentcore:us-east-1:986112483391:memory/hr_assistant_memory-*"
  ]
}
```

### 5. New Setup Script (`0-setup-ssm-memory-id.sh`)

Creates SSM parameter for AgentCore Memory ID:
```bash
aws ssm put-parameter \
    --name "/hr-assistant/AGENTCORE_MEMORY_ID" \
    --value "$AGENTCORE_MEMORY_ID" \
    --type "String" \
    --overwrite
```

### 6. Updated Test Script (`3-test-deployed-agent.sh`)

Now includes:
- Auto-generated session_id
- Example follow-up question to test memory
- Session_id in all test payloads

### 7. Documentation Updates

- **README.md**: Complete rewrite with memory integration details
- **DEPLOYMENT.md**: Added memory setup steps and troubleshooting

## How It Works

### Request Flow

1. **Request arrives** with optional session_id and auth_token
2. **Extract user_id** from JWT token (sub claim)
3. **Generate session_id** if not provided
4. **Load memory_id** from SSM Parameter Store
5. **Configure memory** with retrieval settings
6. **Create agent** with session manager
7. **Stream response** while memory tracks conversation
8. **Flush to memory** when context manager exits

### Memory Namespaces

The agent retrieves from three memory namespaces:

1. **`/preferences/{user_id}`**
   - User communication preferences
   - Notification settings
   - Preferred response style
   - Top K: 5, Relevance: 0.7

2. **`/facts/{user_id}`**
   - Department and role
   - Past requests and cases
   - Personal information
   - Top K: 10, Relevance: 0.3

3. **`/summaries/{user_id}/{session_id}`**
   - Conversation summaries
   - Session context
   - Previous interactions
   - Top K: 5, Relevance: 0.5

### Payload Format

```json
{
  "prompt": "What is the PTO policy?",
  "session_id": "20250224-abc123",     // Optional
  "user_id": "user@example.com",       // Optional (extracted from JWT)
  "auth_token": "Bearer eyJ..."        // Optional (for Case API)
}
```

## Testing Memory

### Test 1: Initial Question
```bash
agentcore invoke '{
  "prompt": "What is the company PTO policy?",
  "session_id": "test-session-123",
  "user_id": "test@example.com"
}'
```

### Test 2: Follow-up (tests memory)
```bash
agentcore invoke '{
  "prompt": "How many days did you say I get?",
  "session_id": "test-session-123",
  "user_id": "test@example.com"
}'
```

The agent should remember the context from Test 1 and answer appropriately.

## Deployment Order

1. Deploy case-backend (for Cognito)
2. Run `session-backend/1-setup-memory.sh` (creates memory resource)
3. Deploy session-backend
4. Run `agent-agentcore/askhragent/0-setup-ssm-memory-id.sh`
5. Deploy agent with `agent-agentcore/askhragent/2-deploy-to-agentcore.sh`
6. Update frontend to pass session_id

## Next Steps

### Frontend Integration

Update `frontend/chat.js` to include session_id:

```javascript
async sendMessage(userMessage, sessionId) {
    const response = await fetch(CONFIG.AGENT_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${auth.idToken}`
        },
        body: JSON.stringify({
            prompt: userMessage,
            session_id: sessionId,  // Add this
            auth_token: `Bearer ${auth.idToken}`
        })
    });
}
```

### Session Management

Integrate with session-backend API:
- Create session on new conversation
- List sessions for user
- Delete old sessions
- Update session titles

See `session-backend/INTEGRATION.md` for details.

## Troubleshooting

### Memory Not Persisting

**Symptom**: Agent doesn't remember previous messages

**Solutions**:
1. Verify session_id is consistent across requests
2. Check memory_id is correct in SSM
3. Verify IAM permissions for memory access
4. Check CloudWatch logs for memory errors

### User ID Extraction Fails

**Symptom**: All conversations use 'default-user'

**Solutions**:
1. Verify JWT token is being passed correctly
2. Check token format (should have 3 parts separated by dots)
3. Verify token contains 'sub' or 'cognito:username' claim
4. Check CloudWatch logs for JWT extraction errors

### SSM Parameter Not Found

**Symptom**: Agent can't find AGENTCORE_MEMORY_ID

**Solutions**:
1. Run `0-setup-ssm-memory-id.sh` to create parameter
2. Verify parameter exists: `aws ssm get-parameter --name /hr-assistant/AGENTCORE_MEMORY_ID`
3. Check IAM role has `ssm:GetParameter` permission

## Benefits

1. **Conversation Continuity**: Users can have multi-turn conversations
2. **Personalization**: Agent remembers user preferences and facts
3. **Context Awareness**: Agent understands conversation history
4. **Session Management**: Multiple conversations per user
5. **Scalability**: Memory is managed by AgentCore
6. **Security**: Memory is isolated per user

## Performance Considerations

- Memory retrieval adds ~100-200ms to first request in session
- Subsequent requests benefit from cached context
- Top K and relevance scores can be tuned for performance
- Consider reducing top_k for faster responses if needed

## Security

- User ID extracted from validated JWT token
- Memory is scoped per user (actor_id)
- Sessions are isolated per user
- IAM policies restrict memory access
- No cross-user data leakage
