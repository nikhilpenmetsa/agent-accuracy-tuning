# AskHR Frontend

Single Page Application (SPA) for the AskHR agent - ACME's HR assistant.

## What It Does

Provides a web interface with:
- Cognito authentication with quick-login for testing
- Chat interface with streaming responses
- Integration with deployed AgentCore agent
- Responsive design

## Setup

Ensure prerequisites are deployed:
- Case Backend (see `../case-backend/`)
- AgentCore Agent (see `../agent-agentcore/`)

## How to Run Locally

```bash
cd frontend
python -m http.server 8000
```

Open **http://localhost:8000**

Config is loaded from `config.json` (generate with `bash generate-config.sh`)

## Deploy to CloudFront

```bash
bash deploy.sh
```

This will:
1. Deploy S3 bucket and CloudFront distribution
2. Generate `config.json` from stack outputs
3. Upload files to S3
4. Invalidate CloudFront cache

## Configuration

Stack name is automatically set to `${PROJECT_NAME}-frontend-stack` using PROJECT_NAME from `../config.env`.

Quick login can be disabled by setting `ENABLE_QUICK_LOGIN=false` in `.env`

## Test Users

- john.doe@acme.com / Password123
- jane.smith@acme.com / Password123
- bob.johnson@acme.com / Password123

## After Deployment

The agent's CORS is already configured to allow `*.cloudfront.net`. If you need to update it:

1. Edit `../agent-agentcore/askhragent/src/main.py`
2. Redeploy: `cd ../agent-agentcore/askhragent && bash 2-deploy-to-agentcore.sh`

