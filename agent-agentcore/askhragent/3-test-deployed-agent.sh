#!/bin/bash
# Test the deployed AgentCore agent with Memory integration

set -e

echo "Testing deployed AskHR Agent with AgentCore Memory..."
echo ""

# Generate a test session ID
TEST_SESSION_ID="test-$(date +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo 'abcd1234')"

# Test payload with session_id
TEST_PAYLOAD='{
  "prompt": "What is the company PTO policy?",
  "user_id": "test-user@example.com",
  "session_id": "'"$TEST_SESSION_ID"'"
}'

echo "Test payload:"
echo "$TEST_PAYLOAD"
echo ""
echo "Session ID: $TEST_SESSION_ID"
echo ""

# Invoke the agent (use .exe on Windows)
echo "Invoking agent..."
if command -v agentcore.exe &> /dev/null; then
    agentcore.exe invoke "$TEST_PAYLOAD"
else
    agentcore invoke "$TEST_PAYLOAD"
fi

echo ""
echo "=========================================="
echo "Test conversation history (use same session_id):"
echo "=========================================="
echo ""
echo "Follow-up question to test memory:"
FOLLOWUP_PAYLOAD='{
  "prompt": "How many days did you say I get?",
  "user_id": "test-user@example.com",
  "session_id": "'"$TEST_SESSION_ID"'"
}'

echo "$FOLLOWUP_PAYLOAD"
echo ""
echo "Run this to test conversation memory:"
if command -v agentcore.exe &> /dev/null; then
    echo "  agentcore.exe invoke '$FOLLOWUP_PAYLOAD'"
else
    echo "  agentcore invoke '$FOLLOWUP_PAYLOAD'"
fi

echo ""
echo "=========================================="
echo "Additional test commands:"
echo "=========================================="
echo ""
echo "Test case creation:"
echo '  agentcore invoke '"'"'{"prompt": "Create a PTO request case for vacation", "user_id": "test@example.com", "session_id": "'"$TEST_SESSION_ID"'"}'"'"''
echo ""
echo "Test case listing:"
echo '  agentcore invoke '"'"'{"prompt": "Show me my cases", "user_id": "test@example.com", "session_id": "'"$TEST_SESSION_ID"'"}'"'"''
echo ""
echo "View logs:"
echo "  aws logs tail /aws/bedrock-agentcore/runtimes/askhragent-0L4quKFDp0-DEFAULT --follow"
echo ""
