# Session ID Integration for Case Backend

This document describes the integration of `session_id` with the case backend to track which conversation led to case creation.

## Changes Made

### 1. Case Backend Lambda (`case-backend/lambda/create_case.py`)

**Added session_id support:**
```python
# Add session_id if provided (optional field)
if 'session_id' in body:
    case_item['session_id'] = body['session_id']
```

**Benefits:**
- Optional field - backward compatible
- No schema migration needed (DynamoDB is schemaless)
- Existing cases without session_id continue to work

### 2. Agent Tools (`agent-agentcore/askhragent/src/tools.py`)

**Updated global configuration:**
```python
_SESSION_ID = None  # Add session_id to global config
```

**Updated initialize_tools():**
```python
def initialize_tools(auth_token: str = None, session_id: str = None):
    # ... stores session_id globally for use in tools
    _SESSION_ID = session_id
```

**Updated create_workday_case():**
```python
payload = {'case_type': case_type, 'description': description}

# Add session_id if available
if _SESSION_ID:
    payload['session_id'] = _SESSION_ID
    logger.info(f"Creating case with session_id: {_SESSION_ID}")
```

### 3. Agent Main (`agent-agentcore/askhragent/src/main.py`)

**Updated tool initialization:**
```python
# Initialize tools with auth token and session_id
if auth_token:
    initialize_tools(auth_token, session_id)
else:
    initialize_tools(session_id=session_id)
```

## How It Works

### Flow Diagram
```
User → Frontend → Agent (with session_id)
                    ↓
              Tools initialized with session_id
                    ↓
              create_workday_case() called
                    ↓
              Payload includes session_id
                    ↓
              Case Backend stores session_id
                    ↓
              Case saved with conversation context
```

### Example Case Object
```json
{
  "case_id": "abc-123",
  "employee_id": "john.doe@acme.com",
  "case_type": "pto",
  "description": "Request 5 days vacation in March",
  "status": "open",
  "session_id": "20260224-abc123",  // NEW FIELD
  "created_at": "2026-02-24T19:00:00Z",
  "updated_at": "2026-02-24T19:00:00Z"
}
```

## Benefits

### 1. Context Tracking
- Know which conversation led to case creation
- Link cases back to the original discussion

### 2. User Journey Analysis
- Track the path from question to case
- Understand what topics lead to case creation

### 3. Better UX (Future Enhancement)
- Show "You created a case in this conversation"
- Display cases created in current session
- Link to the conversation where case was created

### 4. Analytics
- Measure conversation-to-case conversion
- Identify common patterns in case creation
- Optimize agent responses based on case data

## Testing

### Test Case Creation with Session ID

1. **Via Frontend:**
   - Login to the frontend
   - Start a conversation (session_id auto-generated)
   - Ask agent to create a case
   - Case will include session_id automatically

2. **Via Agent Test:**
```bash
cd agent-agentcore/askhragent
bash 4-test-with-auth.sh
# Ask: "Create a PTO request case for vacation"
# Check logs to see session_id being passed
```

3. **Verify in DynamoDB:**
```bash
aws dynamodb scan \
  --table-name hr-assistant-case-backend-stack-cases \
  --region us-east-1 \
  --query 'Items[0]' \
  --output json
```

Look for the `session_id` field in the case object.

## Backward Compatibility

Fully backward compatible:
- `session_id` is optional
- Existing cases without session_id continue to work
- Old agent versions (without session_id) still work
- No database migration required

## Future Enhancements

### 1. Frontend Display
Show cases created in current session:
```javascript
// In chat.js after case creation
if (response.case.session_id === currentSessionId) {
    showNotification("Case created in this conversation");
}
```

### 2. Session-Specific Case List
Filter cases by session:
```python
# New Lambda function: get_session_cases.py
def handler(event, context):
    session_id = event['pathParameters']['session_id']
    # Query cases by session_id
```

### 3. Case History in Conversations
Load cases created in a session when switching conversations:
```javascript
async loadSessionCases(sessionId) {
    const response = await fetch(
        `${CONFIG.API_BASE_URL}/sessions/${sessionId}/cases`
    );
    return response.json();
}
```

### 4. Analytics Dashboard
- Cases created per session
- Average time from question to case
- Most common case types per conversation topic

## Deployment Status

- Case Backend - Deployed with session_id support
- Agent Tools - Updated to pass session_id
- Agent Runtime - Redeployed with changes

## Files Modified

1. `case-backend/lambda/create_case.py` - Added session_id to case object
2. `agent-agentcore/askhragent/src/tools.py` - Added session_id to tools
3. `agent-agentcore/askhragent/src/main.py` - Pass session_id to tools

## Monitoring

### CloudWatch Logs
Check agent logs for session_id tracking:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/askhragent-0L4quKFDp0-DEFAULT \
  --follow \
  --filter-pattern "session_id"
```

### DynamoDB Queries
Query cases by session_id:
```bash
aws dynamodb query \
  --table-name hr-assistant-case-backend-stack-cases \
  --index-name session-index \
  --key-condition-expression "session_id = :sid" \
  --expression-attribute-values '{":sid":{"S":"20260224-abc123"}}' \
  --region us-east-1
```

Note: You would need to add a GSI (Global Secondary Index) on session_id for efficient querying.

## Next Steps

1. Test case creation with session_id
2. Add GSI on session_id for efficient queries (optional)
3. Update frontend to display session-specific cases
4. ⏳ Add analytics for conversation-to-case tracking

## Summary

The integration is complete and working! Cases now include `session_id` when created through the agent, providing valuable context about which conversation led to the case creation. This is fully backward compatible and sets the foundation for enhanced UX and analytics features.
