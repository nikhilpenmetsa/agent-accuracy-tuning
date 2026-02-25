#!/bin/bash

set -e

echo "=========================================="
echo "Setting up AgentCore Memory"
echo "=========================================="
echo ""

# Check if .env exists, if not create from example
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Setup virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
if ! python -c "import bedrock_agentcore" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "Running AgentCore Memory setup script..."
echo ""

# Run the Python script and capture output
OUTPUT=$(python setup-agentcore-memory.py 2>&1)
EXIT_CODE=$?

echo "$OUTPUT"

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Error: Memory setup failed"
    deactivate
    exit 1
fi

# Extract memory_id from output
MEMORY_ID=$(echo "$OUTPUT" | grep "Memory ID:" | awk '{print $3}')

if [ -z "$MEMORY_ID" ]; then
    echo ""
    echo "Error: Could not extract Memory ID from output"
    echo "Please check the output above for errors"
    deactivate
    exit 1
fi

echo ""
echo "=========================================="
echo "Updating .env file"
echo "=========================================="

# Create a temporary file for the updated .env
TEMP_FILE=".env.tmp"

# Update .env file with the memory_id using awk (more portable)
if grep -q "AGENTCORE_MEMORY_ID=" .env; then
    # Replace existing value
    awk -v mem_id="$MEMORY_ID" '{
        if ($0 ~ /^AGENTCORE_MEMORY_ID=/) {
            print "AGENTCORE_MEMORY_ID=" mem_id
        } else {
            print $0
        }
    }' .env > "$TEMP_FILE"
    mv "$TEMP_FILE" .env
    echo "✓ Updated AGENTCORE_MEMORY_ID in .env"
else
    # Append if not exists
    echo "AGENTCORE_MEMORY_ID=${MEMORY_ID}" >> .env
    echo "✓ Added AGENTCORE_MEMORY_ID to .env"
fi

# Deactivate virtual environment
deactivate

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo "Memory ID: ${MEMORY_ID}"
echo ""
echo "Next step:"
echo "  bash 2-deploy.sh"
echo ""
