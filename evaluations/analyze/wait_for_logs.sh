#!/bin/bash
# Wait for new session logs to appear

SESSION_ID="debug-20260226121457-f2de1488"

echo "Waiting for logs for session: $SESSION_ID"
echo "Checking every 30 seconds..."
echo ""

for i in {1..20}; do
    echo "Check $i/20..."
    
    python extract_session_data.py \
        --ui-session "$SESSION_ID" \
        --user-id "d4e83478-60e1-7084-76a6-884f78d662a6" \
        --trace-id "69a0a9c46d1826bb2037b528559e2b2c" \
        --hours 2 \
        --output-dir "session_data_latest" > /dev/null 2>&1
    
    # Check if we got data
    if [ -f "session_data_latest/otel_spans.json" ]; then
        SPAN_COUNT=$(python -c "import json; print(len(json.load(open('session_data_latest/otel_spans.json'))))" 2>/dev/null)
        
        if [ "$SPAN_COUNT" -gt "0" ]; then
            echo ""
            echo "✓ Found $SPAN_COUNT OTEL spans!"
            echo ""
            echo "Analyzing..."
            python analyze_session_data.py session_data_latest --summary
            exit 0
        fi
    fi
    
    sleep 30
done

echo ""
echo "Timeout - logs not found after 10 minutes"
echo "They may take longer to appear"
