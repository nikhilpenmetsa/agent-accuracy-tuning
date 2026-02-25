# AskHR Agent - HR Assistant with AgentCore Memory

An intelligent HR assistant powered by Amazon Bedrock AgentCore with conversation memory, knowledge base search, and Workday case management.

## Features

- **AgentCore Memory Integration**: Persistent conversation history across sessions
- **Knowledge Base Search**: Search company HR policies, benefits, and procedures
- **Case Management**: Create and manage Workday cases
- **JWT Authentication**: Secure user identification and authorization
- **Streaming Responses**: Real-time agent responses
- **Multi-tool Support**: KB search, case creation, case listing, case types

## Architecture

```
User → Frontend → AgentCore Runtime → Agent (with Memory)
                                    ↓
                        ┌───────────┴───────────┐
                        ↓           ↓           ↓
                   Knowledge    Case API    Memory
                     Base                   (Sessions)
```

## Quick Start

### Prerequisites

- AWS CLI configured with credentials
- Python 3.10+
- AgentCore CLI installed
- Session backend deployed (for memory)
- Case backend deployed (for case management)
- Knowledge base created and ingested

### Setup

1. **Setup AgentCore Memory ID**
```bash
cd agent-agentcore/askhragent
bash 0-setup-ssm-memory-id.sh
```

2. **Create SSM Parameters**
```bash
bash 1-create-ssm-parameters.sh
```

3. **Configure Cognito** (update `.bedrock_agentcore.yaml`)

4. **Deploy to AgentCore**
```bash
bash 2-deploy-to-agentcore.sh
```

5. **Test**
```bash
bash 3-test-deployed-agent.sh
```

## Project Structure

```
agent-agentcore/askhragent/
├── src/
│   ├── main.py           # Agent entrypoint with Memory integration
│   └── tools.py          # KB search and Case API tools
├── test/
│   └── test_main.py      # Unit tests
├── .bedrock_agentcore.yaml  # AgentCore configuration
├── pyproject.toml        # Dependencies
├── .env                  # Local configuration
├── 0-setup-ssm-memory-id.sh
├── 1-create-ssm-parameters.sh
├── 2-deploy-to-agentcore.sh
├── 3-test-deployed-agent.sh
├── DEPLOYMENT.md         # Detailed deployment guide
└── README.md            # This file
```

## Memory Integration

The agent uses AgentCore Memory to persist conversations:

- **Session-based**: Each conversation has a unique session_id
- **User-scoped**: Memory is isolated per user (extracted from JWT)
- **Three namespaces**:
  - `/preferences/{user_id}`: User preferences and settings
  - `/facts/{user_id}`: User facts (department, role, history)
  - `/summaries/{user_id}/{session_id}`: Conversation summaries

### Payload Format

```json
{
  "prompt": "What is the PTO policy?",
  "session_id": "20250224-abc123",  // Optional, auto-generated if not provided
  "user_id": "user@example.com",    // Optional, extracted from JWT
  "auth_token": "Bearer eyJ..."     // Optional, for Case API calls
}
```

## Tools

### search_hr_knowledge_base
Search company HR policies and documentation using Bedrock Knowledge Base.

### get_available_case_types
List available case types that can be created in Workday.

### create_workday_case
Create a new HR case in Workday with type and description.

### list_my_cases
List all cases created by the current user.

## Configuration

### Environment Variables (.env)

```bash
AWS_REGION=us-east-1
KB_ID=8WTHFPVP3H
MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
CASE_API_URL=https://xxx.execute-api.us-east-1.amazonaws.com/prod
AGENTCORE_MEMORY_ID=hr_assistant_memory-QzY4Jx5O7Z
```

### SSM Parameters

The agent reads configuration from SSM Parameter Store in production:

- `/hr-assistant/KB_ID`
- `/hr-assistant/CASE_API_URL`
- `/hr-assistant/MODEL_ID`
- `/hr-assistant/AGENTCORE_MEMORY_ID`

## Local Development

1. **Activate virtual environment**
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. **Start local server**
```bash
agentcore dev
```

3. **Test locally**
```bash
agentcore invoke --dev '{"prompt": "What is the PTO policy?", "user_id": "test@example.com"}'
```

## Monitoring

### Logs
```bash
aws logs tail /aws/bedrock/agentcore/askhragent_Agent --follow
```

### Traces
View in AWS Console → X-Ray → Traces

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Memory not persisting | Ensure session_id is consistent across requests |
| SSM access denied | Verify IAM role has `ssm:GetParameter` permission |
| KB access denied | Verify `bedrock:Retrieve` permission |
| Memory access denied | Verify `bedrock-agentcore:GetMemory` permission |
| Case API fails | Check auth_token is provided and valid |

## Dependencies

- `bedrock-agentcore[strands-agents]` - AgentCore runtime with Strands integration
- `strands-agents` - Agent framework
- `python-dotenv` - Environment variable management
- `boto3` - AWS SDK

See `pyproject.toml` for complete list.

## Next Steps

1. Update frontend to pass session_id in requests
2. Integrate with session-backend API for session management
3. Configure CORS with CloudFront domain
4. Monitor memory usage and conversation quality
5. Add more tools as needed

## Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment guide
- [session-backend/INTEGRATION.md](../../session-backend/INTEGRATION.md) - Integration guide
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
