#!/bin/bash

# Simple local development server
# Run this to test the frontend locally before deploying

echo "🚀 Starting local development server..."
echo ""
echo "📝 Note: Quick login will use mock streaming responses"
echo "   Real Cognito auth requires deployed backend"
echo ""
echo "🌐 Open: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start simple HTTP server
python3 -m http.server 8000 2>/dev/null || python -m http.server 8000
