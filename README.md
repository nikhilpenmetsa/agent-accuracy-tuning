# Agent Accuracy Tuning

A reference implementation for building and tuning AI agents to achieve accurate, reliable tool usage. This project demonstrates best practices for prompt engineering, model configuration, and policy tuning to improve agent accuracy and reduce hallucinations or inappropriate tool calls.

## Overview

This solution implements an HR assistant agent that showcases:
- **Tool calling accuracy** with knowledge base search and case management
- **Conversation memory** for context-aware interactions
- **Session tracking** to measure and analyze tool usage
- **Iterative tuning** framework for improving accuracy

**Current State:** Functional agent with liberal case creation
**Goal:** Tune prompts, models, and policies for accurate, appropriate tool usage

## Use Case: HR Assistant

The HR assistant demonstrates accuracy tuning with:
- Knowledge base queries (when to search vs. answer directly)
- Case creation (when to create vs. just provide information)
- Multi-turn conversations (maintaining context appropriately)
- Tool selection (choosing the right tool for the task)

## Architecture

```
Frontend (React-like SPA)
    ↓
Amazon Bedrock AgentCore Runtime
    ├── Agent with Memory
    ├── Knowledge Base (HR Docs)
    └── Tools (Case Management)
        ↓
    ┌───────────┴───────────┐
    ↓           ↓           ↓
Session API  Case API   AgentCore Memory
(DynamoDB)  (DynamoDB)  (Conversations)
```

## Features

- Conversation Memory - Persistent chat history across sessions
- Knowledge Base - Search company HR policies and documents
- Case Management - Create and track HR cases in Workday
- Authentication - Cognito-based user authentication
- Session Tracking - Link cases to conversations
- Responsive UI - Works on desktop and mobile

## Project Structure

This reference implementation includes all components needed for agent tuning:

### 1. Frontend (`frontend/`)
- User interface for testing agent behavior
- Session management for tracking conversations
- Real-time streaming responses
- Conversation history for analyzing agent decisions

### 2. Agent (`agent-agentcore/askhragent/`)
- **Core tuning target** - Prompts, model config, tool policies
- Bedrock AgentCore Runtime deployment
- Strands Agents framework
- AgentCore Memory integration
- Tools: KB search, case creation, case listing

### 3. Session Backend (`session-backend/`)
- Session metadata and conversation tracking
- Message history retrieval for analysis
- REST API for session management

### 4. Case Backend (`case-backend/`)
- Case storage for measuring tool usage
- Cognito user pool for authentication
- REST API for case operations

### 5. Knowledge Base (`kb/`)
- HR document corpus
- Vector search for retrieval
- Bedrock Knowledge Base

## Tuning Framework

### What Can Be Tuned:

**1. System Prompt** (`agent-agentcore/askhragent/src/main.py`)
- Adjust agent personality and behavior
- Define when to use tools vs. answer directly
- Set guidelines for case creation

**2. Model Configuration**
- Temperature (currently 0.3)
- Model selection (Claude 3.5 Sonnet)
- Top-k, top-p parameters

**3. Tool Policies**
- When to search knowledge base
- Criteria for case creation
- Tool selection logic

**4. Memory Configuration**
- Retrieval thresholds
- Context window size
- Preference learning

### Measuring Determinism:

**Metrics to Track:**
- Case creation rate (cases per conversation)
- Tool usage patterns (which tools, when)
- Response consistency (same question → same answer)
- Conversation length (turns to resolution)
- Tool call accuracy (appropriate vs. inappropriate calls)

**Data Sources:**
- Session table: Conversation metadata
- Case table: Tool usage (with session_id)
- AgentCore Memory: Full conversation history
- CloudWatch: Agent execution logs

### Iteration Process:

1. **Baseline** - Current behavior (liberal case creation)
2. **Hypothesis** - Adjust prompt to improve accuracy
3. **Test** - Run test conversations
4. **Measure** - Check case creation rate, tool usage accuracy
5. **Iterate** - Refine based on results

## Components

### 1. Frontend (`frontend/`)
- Single-page application with session management
- Real-time streaming responses
- Conversation history loading
- Session sidebar with conversation list

### 2. Agent (`agent-agentcore/askhragent/`)
- Bedrock AgentCore Runtime deployment
- Strands Agents framework
- AgentCore Memory integration
- Tools: KB search, case creation, case listing

### 3. Session Backend (`session-backend/`)
- Session metadata storage (DynamoDB)
- Message history retrieval from AgentCore Memory
- REST API for session management

### 4. Case Backend (`case-backend/`)
- Case storage (DynamoDB)
- Cognito user pool
- REST API for case operations

### 5. Knowledge Base (`kb/`)
- Bedrock Knowledge Base setup
- HR document ingestion
- Vector search configuration

## Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.10+
- AgentCore CLI installed
- Bash shell
- **CloudWatch Transaction Search enabled** (one-time account setup)

### One-Time Account Setup

**Enable CloudWatch Transaction Search** (required for observability):
```bash
bash setup-observability.sh
```

This enables traces, sessions, and metrics in the GenAI Observability dashboard. Wait 10 minutes after enabling for data to appear.

### Deployment Order

1. **Deploy Case Backend** (creates Cognito)
```bash
cd case-backend
bash deploy.sh
bash create_users.sh
```

2. **Setup Knowledge Base**
```bash
cd kb
bash 1-deploy-infrastructure.sh
bash 2-setup-knowledge-base.sh
bash 3-ingest-documents.sh
```

3. **Setup AgentCore Memory**
```bash
cd session-backend
bash 1-setup-memory.sh
```

4. **Deploy Session Backend**
```bash
bash 2-deploy.sh
```

5. **Deploy Agent**
```bash
cd agent-agentcore/askhragent
bash 0-setup-ssm-memory-id.sh
bash 1-create-ssm-parameters.sh
# Update .bedrock_agentcore.yaml with Cognito config
bash 2-deploy-to-agentcore.sh
```

6. **Deploy Frontend**
```bash
cd frontend
bash deploy.sh
```

## Testing

### Test Backends
```bash
# Test case backend
cd case-backend
bash test_api.sh

# Test session backend
cd session-backend
bash 3-test-api.sh

# Test agent
cd agent-agentcore/askhragent
bash 4-test-with-auth.sh
```

### Test Frontend Locally
```bash
cd frontend
bash serve-local.sh
# Open http://localhost:8000
```

## Key Features Implemented

### UUID-Based Identity
All systems use Cognito UUID (`sub` claim) as primary identifier:
- Consistent across memory, sessions, and cases
- Email stored separately for display
- Stable identifier (email can change)

### Conversation Memory
- Messages persisted in AgentCore Memory
- History loads when switching sessions
- Context maintained across conversations

### Session Tracking
- Cases linked to conversation sessions
- Track which conversation led to case creation
- Analytics-ready architecture

## Configuration

### Environment Variables

**Case Backend** (`.env`):
```bash
STACK_NAME=hr-assistant-case-backend-stack
TEST_USER_1_EMAIL=john.doe@acme.com
TEST_USER_1_PASSWORD=Password123
```

**Session Backend** (`.env`):
```bash
STACK_NAME=hr-assistant-session-backend-stack
AGENTCORE_MEMORY_ID=hr_assistant_memory-QzY4Jx5O7Z
```

**Agent** (`.env`):
```bash
KB_ID=8WTHFPVP3H
CASE_API_URL=https://xxx.execute-api.us-east-1.amazonaws.com/prod
AGENTCORE_MEMORY_ID=hr_assistant_memory-QzY4Jx5O7Z
MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Frontend** (`config.json`):
```json
{
  "COGNITO_USER_POOL_ID": "us-east-1_xxx",
  "COGNITO_CLIENT_ID": "xxx",
  "API_BASE_URL": "https://xxx.execute-api.us-east-1.amazonaws.com/prod",
  "SESSION_API_URL": "https://xxx.execute-api.us-east-1.amazonaws.com/prod",
  "AGENT_ENDPOINT": "https://bedrock-agentcore.us-east-1.amazonaws.com/..."
}
```

## Documentation

Detailed documentation available in `docs/`:
- `SESSION_ID_INTEGRATION.md` - Session tracking implementation
- `UUID_MIGRATION_COMPLETE.md` - UUID migration details

Component-specific docs:
- `agent-agentcore/askhragent/README.md` - Agent documentation
- `agent-agentcore/askhragent/DEPLOYMENT.md` - Deployment guide
- `session-backend/INTEGRATION.md` - Integration guide
- `frontend/FRONTEND_INTEGRATION.md` - Frontend integration

## Cleanup

To remove all resources:

```bash
# Delete in reverse order
cd frontend
bash cleanup.sh

cd ../agent-agentcore/askhragent
# Use agentcore CLI to delete agent

cd ../../session-backend
bash cleanup.sh --force

cd ../case-backend
bash cleanup.sh --force

cd ../kb
bash cleanup.sh
```

## Architecture Decisions

### Why UUID?
- Stable identifier (email can change)
- Required by AgentCore Memory
- Better security (no PII in keys)
- Consistent across all systems

### Why AgentCore Memory?
- Managed service (no infrastructure)
- Intelligent retrieval (preferences, facts, summaries)
- Scalable and reliable
- Integrated with Bedrock

### Why Separate Backends?
- Separation of concerns
- Independent scaling
- Easier maintenance
- Reusable components

## Monitoring

### CloudWatch Logs
```bash
# Agent logs
aws logs tail /aws/bedrock-agentcore/runtimes/askhragent-xxx-DEFAULT --follow

# Lambda logs
aws logs tail /aws/lambda/hr-assistant-session-backend-stack-get-session-messages --follow
```

### X-Ray Traces
View in AWS Console → X-Ray → Traces

### GenAI Observability Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#gen-ai-observability/agent-core

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Check OPTIONS methods deployed, verify API URLs |
| Messages not loading | Check UUID consistency, verify memory permissions |
| Agent not responding | Check CloudWatch logs, verify SSM parameters |
| Cases not creating | Verify auth token passed, check case backend logs |

## Tech Stack

- **Frontend**: Vanilla JS, HTML, CSS
- **Agent Framework**: Strands Agents
- **Agent Runtime**: Amazon Bedrock AgentCore
- **Memory**: AgentCore Memory
- **Knowledge Base**: Amazon Bedrock Knowledge Base
- **APIs**: API Gateway + Lambda
- **Database**: DynamoDB
- **Auth**: Amazon Cognito
- **Model**: Claude 3.5 Sonnet

## Tuning Examples

### Example 1: Reduce Case Creation

**Problem:** Agent creates cases too liberally

**Current Prompt:**
```
Use this when a user wants to submit an HR request, report an issue, or create a case.
```

**Tuned Prompt:**
```
Use this ONLY when the user explicitly requests to create a case or submit a formal request. 
If the user is just asking questions, provide information from the knowledge base instead.
```

### Example 2: Improve Tool Selection

**Add to System Prompt:**
```
Tool Usage Guidelines:
1. ALWAYS search knowledge base first for policy questions
2. ONLY create cases when user explicitly requests it
3. List cases only when user asks to see their cases
4. Prefer answering from knowledge base over creating cases
```

### Example 3: Adjust Temperature

Lower temperature for more deterministic responses:
```python
model = BedrockModel(
    model_id=model_id,
    temperature=0.1  # Lower = more deterministic (was 0.3)
)
```

## Measuring Success

Track these metrics before and after tuning:

1. **Tool Call Accuracy**: Appropriate tool calls / Total tool calls
2. **Case Creation Rate**: Cases per 100 conversations
3. **KB Search Effectiveness**: Questions answered without case creation
4. **Response Consistency**: Same input → same output
5. **User Satisfaction**: Resolved without unnecessary escalation

Query DynamoDB to analyze:
```bash
# Cases with session_id
aws dynamodb scan --table-name hr-assistant-case-backend-stack-cases \
  --filter-expression "attribute_exists(session_id)"

# Sessions by user
aws dynamodb query --table-name hr-assistant-session-backend-stack-sessions \
  --key-condition-expression "user_id = :uid"
```

## License

This is a sample application for demonstration purposes.

## Support

For issues or questions, check:
- CloudWatch logs for errors
- API Gateway execution logs
- DynamoDB tables for data
- AgentCore Memory events
