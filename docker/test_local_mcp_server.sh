#!/bin/bash
# Quick test script for the MCP SSE server without Docker

set -e

echo "==================================================================="
echo "Testing Browser-Use MCP Server (Local Mode - No Docker)"
echo "==================================================================="
echo ""

# Check if we're in the browser-use directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from browser-use project root directory"
    exit 1
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$BROWSER_USE_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API key found in environment!"
    echo "   Please set one of: OPENAI_API_KEY, BROWSER_USE_API_KEY, or ANTHROPIC_API_KEY"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import starlette" 2>/dev/null; then
    echo "Installing MCP server dependencies..."
    uv pip install starlette uvicorn || pip install starlette uvicorn
fi

if ! python -c "import browser_use" 2>/dev/null; then
    echo "Installing browser-use..."
    uv sync --all-extras || pip install -e .
fi

echo "✅ Dependencies installed"
echo ""

# Run the MCP SSE server
echo "🚀 Starting MCP SSE Server..."
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo ""
echo "📋 Available endpoints:"
echo "   - Health Check: http://localhost:8000/health"
echo "   - SSE Endpoint: http://localhost:8000/sse"
echo "   - Messages:     http://localhost:8000/messages"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==================================================================="
echo ""

# Run the server
python -m browser_use.mcp.server_sse --host 0.0.0.0 --port 8000 --session-timeout 30
