# Documentation Guide

This guide helps you navigate the documentation for the AskHR solution.

## Quick Start

**New to the project?** Start here:
1. Read root `README.md` - Complete overview
2. Follow deployment order in README
3. Refer to component-specific docs as needed

## Documentation Structure

### Root Level
- **README.md** - Complete solution overview, architecture, quick start

### Component Documentation

#### Agent (`agent-agentcore/askhragent/`)
- **README.md** - Agent overview, features, configuration
- **DEPLOYMENT.md** - Step-by-step deployment guide
- **Test scripts**: `4-test-with-auth.sh`, `5-test-case-with-session.sh`

#### Case Backend (`case-backend/`)
- **README.md** - Case API documentation
- **Test scripts**: `test_api.sh`

#### Session Backend (`session-backend/`)
- **README.md** - Session API documentation
- **Test scripts**: `3-test-api.sh`, `test-jane-session.sh`
- **Debug tools**: `check-memory-directly.py`

#### Knowledge Base (`kb/`)
- **README.md** - KB setup and ingestion

#### Frontend (`frontend/`)
- **README.md** - Frontend setup and usage (if exists)

### Historical Documentation (`docs/archive/`)

Implementation notes and migration guides:
- `MEMORY_INTEGRATION.md` - How memory was integrated
- `SESSION_ID_INTEGRATION.md` - Session tracking implementation
- `UUID_MIGRATION_COMPLETE.md` - UUID migration details
- `FRONTEND_INTEGRATION.md` - Frontend implementation notes
- `INTEGRATION.md` - Early integration guide

**When to read archive docs:**
- Understanding architectural decisions
- Troubleshooting integration issues
- Learning how components work together
- Contributing to the project

## Documentation by Task

### Deploying the Solution
1. Root `README.md` - Deployment order
2. `agent-agentcore/askhragent/DEPLOYMENT.md` - Agent deployment
3. Component READMEs for specific setup

### Understanding Architecture
1. Root `README.md` - High-level architecture
2. `docs/archive/UUID_MIGRATION_COMPLETE.md` - Identity architecture
3. `docs/archive/MEMORY_INTEGRATION.md` - Memory architecture

### Troubleshooting
1. Component READMEs - Troubleshooting sections
2. `agent-agentcore/askhragent/DEPLOYMENT.md` - Common issues
3. Archive docs for deep dives

### Testing
1. Component test scripts in each folder
2. Root `README.md` - Testing section

## Keeping Documentation Updated

When making changes:
- Update component READMEs for user-facing changes
- Update DEPLOYMENT.md for deployment process changes
- Create new archive docs for major architectural changes
- Keep root README.md current with latest architecture

## Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Provide troubleshooting sections
- Keep deployment steps up-to-date
- Archive historical implementation notes
