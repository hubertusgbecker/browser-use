#!/bin/bash
set -e

# Docker entrypoint script for browser-use MCP server

echo "🐳 Starting browser-use in Docker..."
echo "Environment: IN_DOCKER=${IN_DOCKER}"
echo "Mode: MCP Server (SSE Transport)"

# Check if running as root and switch to browseruse user if needed
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, switching to browseruse user..."
    
    # Set PUID/PGID if provided
    PUID=${PUID:-911}
    PGID=${PGID:-911}
    
    # Update user/group IDs if different
    if [ "$(id -u browseruse)" != "$PUID" ]; then
        usermod -u "$PUID" browseruse
    fi
    if [ "$(id -g browseruse)" != "$PGID" ]; then
        groupmod -g "$PGID" browseruse
    fi
    
    # Ensure data directory permissions
    chown -R browseruse:browseruse /data /downloads /home/browseruse
    
    # Switch to browseruse user and re-execute this script
    exec su-exec browseruse "$0" "$@"
fi

# Now running as browseruse user
echo "Running as user: $(whoami) (UID=$(id -u), GID=$(id -g))"

# Verify required directories exist and have correct permissions
echo "🔍 Checking directory structure..."
REQUIRED_DIRS="/data /downloads /home/browseruse"
for dir in $REQUIRED_DIRS; do
    if [ ! -d "$dir" ]; then
        echo "❌ ERROR: Required directory missing: $dir"
        exit 1
    fi
    
    # Check if directory is writable
    if [ ! -w "$dir" ]; then
        echo "❌ ERROR: Directory not writable: $dir"
        exit 1
    fi
    
    echo "✅ $dir exists and is writable"
done

# Set up Xvfb for headless browser if DISPLAY is not set
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:99
    echo "Starting Xvfb on display $DISPLAY..."
    Xvfb $DISPLAY -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    echo "Xvfb started with PID $XVFB_PID"
    
    # Wait for Xvfb to be ready
    sleep 2
fi

# Start VNC server if requested
if [ "$ENABLE_VNC" = "true" ]; then
    echo "Starting VNC server on port 5900..."
    x11vnc -display $DISPLAY -forever -shared -rfbport 5900 -passwd "${VNC_PASSWORD:-browseruse}" &
    VNC_PID=$!
    echo "VNC server started with PID $VNC_PID"
fi

# Print configuration
echo "📋 Configuration:"
echo "  - SSE Server Host: ${HOST:-0.0.0.0}"
echo "  - SSE Server Port: ${PORT:-8000}"
echo "  - Session Timeout: ${SESSION_TIMEOUT_MINUTES:-30} minutes"
echo "  - Headless Mode: ${BROWSER_USE_HEADLESS:-true}"
echo "  - Data Directory: /data"

# Check for API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ] && [ -z "$BROWSER_USE_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API keys configured!"
    echo "   Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or BROWSER_USE_API_KEY"
else
    echo "✅ LLM API key(s) detected"
fi

# Execute the main command
echo "🚀 Starting MCP server with SSE transport..."
echo "Command: $@"
echo ""

# If no command provided, run the MCP SSE server
if [ $# -eq 0 ]; then
    exec python -m browser_use.mcp.server_sse \
        --host "${HOST:-0.0.0.0}" \
        --port "${PORT:-8000}" \
        --session-timeout "${SESSION_TIMEOUT_MINUTES:-30}"
else
    # Run provided command
    exec "$@"
fi
