# AskHR Agent - AgentCore Deployment

Deploy the AskHR agent to Amazon Bedrock AgentCore Runtime with Memory integration.

## Quick Deploy

```bash
cd agent-agentcore/askhragent
bash 0-setup-ssm-memory-id.sh  # Store AgentCore Memory ID in SSM
bash 1-create-ssm-parameters.sh
# Manually update .bedrock_agentcore.yaml with Cognito config (see step 3 below)
bash 2-deploy-to-agentcore.sh
bash 3-test-deployed-agent.sh
```

## What's New - Memory Integration

The agent now uses AgentCore Memory for conversation history persistence:

- Conversations are stored per session and user
- Memory retrieves user preferences, facts, and conversation summaries
- Session IDs can be provided in payload or auto-generated
- User IDs are extracted from JWT tokens
- Memory is automatically flushed after each conversation

**New Dependencies**: `bedrock-agentcore[strands-agents]` includes Strands integration

**New SSM Parameter**: `/hr-assistant/AGENTCORE_MEMORY_ID`

## Deployment Steps

**0. Setup AgentCore Memory** - `bash 0-setup-ssm-memory-id.sh`

Stores the AgentCore Memory ID in SSM Parameter Store. The memory resource should already be created by `session-backend/1-setup-memory.sh`.

**1. Create SSM Parameters** - `bash 1-create-ssm-parameters.sh`

Creates parameters for KB_ID, CASE_API_URL, and MODEL_ID.

**2. Update Dependencies** - Already done in `pyproject.toml`

The agent now uses `bedrock-agentcore[strands-agents]` for memory integration.

**3. Configure Cognito** - Update `.bedrock_agentcore.yaml`:
```yaml
identity:
  credential_providers:
    - name: cognito-oauth
      type: oauth2
      config:
        issuer_url: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_bA1L8mO4W/.well-known/openid-configuration
        audiences: []
  workload:
    enabled: true
    token_validation:
      validate_issuer: true
      validate_audience: false
```

**4. Deploy** - `bash 2-deploy-to-agentcore.sh`

AgentCore auto-creates IAM role with required permissions including memory access.

**5. Test** - `bash 3-test-deployed-agent.sh`

Tests the agent with conversation history. The script generates a session_id and shows how to test follow-up questions.

## Memory Configuration

The agent retrieves from three memory namespaces:

1. **Preferences** (`/preferences/{user_id}`): User communication preferences, notification settings
2. **Facts** (`/facts/{user_id}`): Department, role, past requests, personal info
3. **Summaries** (`/summaries/{user_id}/{session_id}`): Conversation summaries for context

## Payload Format

```json
{
  "prompt": "What is the PTO policy?",
  "session_id": "20250224-abc123",  // Optional, auto-generated if not provided
  "user_id": "user@example.com",    // Optional, extracted from JWT if not provided
  "auth_token": "Bearer eyJ..."     // Optional, for Case API calls
}
```

## After Deployment

1. Note the AgentCore HTTP endpoint URL
2. Update `frontend/config.json` with endpoint
3. Update CORS in `main.py` with CloudFront domain
4. Redeploy: `bash 2-deploy-to-agentcore.sh`

## Monitoring

```bash
# Logs
aws logs tail /aws/bedrock/agentcore/askhragent_Agent --follow

# Traces: AWS Console → X-Ray → Traces
```

## Local Dev

Still works with `agentcore dev` - automatically uses `.env` when SSM unavailable.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSM access denied | Verify IAM role has `ssm:GetParameter` for `/hr-assistant/*` |
| KB access denied | Verify `bedrock-agent-runtime:Retrieve` permission |
| Model invocation failed | Verify `bedrock:InvokeModel` permission |
| Memory access denied | Verify `bedrock-agentcore:GetMemory` and related permissions |
| CORS errors | Update `allow_origins` in `main.py`, redeploy |
| Auth errors | Check Cognito config in `.bedrock_agentcore.yaml` |
| Memory not persisting | Check session_id is consistent across requests |
