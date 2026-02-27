#!/bin/bash
# Extract and Analyze Session Data
# 
# This script extracts session data from DynamoDB, AgentCore Memory, and CloudWatch,
# then launches the interactive analyzer.
#
# Usage:
#   ./extract_and_analyze.sh

set -e

# Load configuration
if [ -f "../config.env" ]; then
    source ../config.env
elif [ -f "config.env" ]; then
    source config.env
fi

# Default values
UI_SESSION="20260225184304-c338801e"
USER_ID="d4e83478-60e1-7084-76a6-884f78d662a6"
TRACE_ID="699f47041e534f81661794b32b7df31d"
OTEL_SESSION="f26e44bf-a514-4218-8509-50712b7e7a23"
REGION="${AWS_REGION:-us-east-1}"
HOURS=24

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ui-session)
            UI_SESSION="$2"
            shift 2
            ;;
        --user-id)
            USER_ID="$2"
            shift 2
            ;;
        --trace-id)
            TRACE_ID="$2"
            shift 2
            ;;
        --otel-session)
            OTEL_SESSION="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --hours)
            HOURS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --ui-session <id>      UI session ID (default: 20260225184304-c338801e)"
            echo "  --user-id <id>         User ID UUID (default: d4e83478-60e1-7084-76a6-884f78d662a6)"
            echo "  --trace-id <id>        CloudWatch X-Ray trace ID (default: 699f47041e534f81661794b32b7df31d)"
            echo "  --otel-session <id>    OTEL session ID (default: f26e44bf-a514-4218-8509-50712b7e7a23)"
            echo "  --region <region>      AWS region (default: us-east-1)"
            echo "  --hours <n>            Hours to look back (default: 24)"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Session Data Extraction and Analysis"
echo "========================================"
echo ""
echo "Configuration:"
echo "  UI Session:   $UI_SESSION"
echo "  User ID:      $USER_ID"
echo "  Trace ID:     $TRACE_ID"
echo "  OTEL Session: $OTEL_SESSION"
echo "  Region:       $REGION"
echo "  Hours back:   $HOURS"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured or credentials are invalid"
    exit 1
fi

echo "Step 1: Extracting session data..."
echo "-----------------------------------"

# Run extraction script
python3 extract_session_data.py \
    --ui-session "$UI_SESSION" \
    --user-id "$USER_ID" \
    --trace-id "$TRACE_ID" \
    --otel-session "$OTEL_SESSION" \
    --region "$REGION" \
    --hours "$HOURS"

# Find the most recent output directory
OUTPUT_DIR=$(ls -td evaluations/session_data_* 2>/dev/null | head -1)

if [ -z "$OUTPUT_DIR" ]; then
    # Try without evaluations/ prefix
    OUTPUT_DIR=$(ls -td session_data_* 2>/dev/null | head -1)
fi

if [ -z "$OUTPUT_DIR" ]; then
    echo ""
    echo "Error: Could not find output directory"
    exit 1
fi

echo ""
echo "Step 2: Launching analyzer..."
echo "-----------------------------------"
echo ""

# Launch analyzer
python3 analyze_session_data.py "$OUTPUT_DIR"

echo ""
echo "========================================"
echo "Analysis complete!"
echo "Data saved in: $OUTPUT_DIR"
echo "========================================"
