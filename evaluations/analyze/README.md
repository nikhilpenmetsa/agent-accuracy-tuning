# Session Data Extraction and Analysis

Extracts and analyzes session data from your HR Assistant, including session metadata, conversation messages, and OTEL spans.

## Quick Start

```bash
cd evaluations/analyze

# Extract session data
python extract_session_data.py \
    --ui-session 20260225193457-89b5ba8f \
    --user-id 245874d8-5051-706e-f8ed-cd94ee41440d

# Analyze
python analyze_session_data.py session_data_<timestamp> --summary
```

## Scripts

**extract_session_data.py** - Extracts session data from AWS
**analyze_session_data.py** - Interactive analyzer with summary, conversation, and tool analysis

## What Gets Extracted

- Session metadata (DynamoDB)
- Conversation messages with tool calls (AgentCore Memory)
- OTEL spans with trace context (CloudWatch Logs)

## Note on OTEL Data

The detailed API call spans (ListEvents, CreateEvent timing) visible in CloudWatch GenAI Observability dashboard are captured by ADOT instrumentation and stored in a backend telemetry system. They're not directly accessible via API. 

What you CAN extract:
- Application logs with trace context
- Memory operation log messages
- Conversation history and tool calls

## Cleanup

Consolidated from multiple exploratory scripts into 2 main scripts.
