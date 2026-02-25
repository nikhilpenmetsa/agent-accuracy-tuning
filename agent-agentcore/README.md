# AskHR Agent - AgentCore

HR assistant agent that helps employees with company policies, benefits, and Workday case management using Amazon Bedrock AgentCore.

## What It Does

Provides an AI agent with:
- HR Knowledge Base search (company policies, benefits, time off)
- Workday case management (create and retrieve cases)
- Streaming responses via AgentCore
- Cognito authentication integration

## Setup

1. Ensure prerequisites are deployed:
   - Knowledge Base (see `../kb/`)
   - Case Backend API (see `../case-backend/`)

2. Install dependencies:
```bash
cd agent-agentcore
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Configure environment in `askhragent/.env`:
```bash
AWS_REGION=us-east-1
KB_ID=your-kb-id-here
MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
CASE_API_URL=https://your-api-gateway-url.amazonaws.com/prod
```

## How to Run Locally

```bash
cd askhragent
..\.venv\Scripts\agentcore.exe dev
```

Server runs at **http://localhost:8080** with hot-reload enabled.

Test with CLI:
```bash
..\.venv\Scripts\agentcore.exe invoke --dev "What are the company holidays?"
```

Or use the frontend at **http://localhost:8000**

## Deploy to AWS

```bash
cd askhragent
..\.venv\Scripts\agentcore.exe deploy
```

Uses AWS CodeBuild (no Docker needed).

## Architecture

```
Frontend → AgentCore (port 8080) → Strands Agent
                                    ├─→ Bedrock KB
                                    ├─→ Bedrock LLM
                                    └─→ Case Backend API
```

## Key Features

- **Hot Reload**: Code changes auto-reload during development
- **CORS Enabled**: Frontend can connect from localhost:8000
- **Auth Flow**: Frontend → Cognito token → AgentCore → Tools → Case API
- **Streaming**: Real-time response streaming via SSE

