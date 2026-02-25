# Archive - Historical Documentation

This folder contains historical documentation from the development process. These documents are kept for reference and understanding the evolution of the solution, but are not required for deployment.

## Contents

### Implementation History

**MEMORY_INTEGRATION.md**
- Details of AgentCore Memory integration
- Code changes and technical implementation
- Useful for understanding how memory works

**SESSION_ID_INTEGRATION.md**
- Session tracking implementation
- How cases are linked to conversations
- Technical details of session_id flow

**UUID_MIGRATION_COMPLETE.md**
- Complete UUID migration documentation
- Why we migrated from email to UUID
- Benefits and architecture decisions

**FRONTEND_INTEGRATION.md**
- Frontend session management implementation
- UI components and flow
- Technical details of message loading

**INTEGRATION.md**
- Early integration guide
- Code examples for connecting components
- Some information may be outdated

## Why Archive These?

These documents were created during development to:
- Track implementation decisions
- Document troubleshooting steps
- Explain architectural choices
- Guide integration work

They contain valuable context but are not needed for:
- Deploying the solution
- Day-to-day operations
- New user onboarding

## For Deployment

See the main documentation:
- Root `README.md` - Complete overview
- `agent-agentcore/askhragent/README.md` - Agent documentation
- `agent-agentcore/askhragent/DEPLOYMENT.md` - Deployment guide
- Component-specific READMEs in each folder

## For Understanding Architecture

If you want to understand why certain decisions were made:
1. Read `UUID_MIGRATION_COMPLETE.md` - Why UUID everywhere
2. Read `MEMORY_INTEGRATION.md` - How memory works
3. Read `SESSION_ID_INTEGRATION.md` - How session tracking works
