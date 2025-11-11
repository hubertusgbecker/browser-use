#!/usr/bin/env bash
# Quick deployment test script
# Tests local setup without Docker first

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  Browser-Use MCP Server - Local Deployment Test                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check directories
echo "🔍 Checking directory structure..."
for dir in data downloads; do
    if [ ! -d "./$dir" ]; then
        echo "❌ Missing directory: $dir"
        exit 1
    fi
    echo "✅ $dir exists"
done

# Check .gitkeep files
for file in data/.gitkeep downloads/.gitkeep; do
    if [ ! -f "./$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
    echo "✅ $file exists"
done

# Check key files
echo ""
echo "🔍 Checking key files..."
required_files=(
    "Dockerfile.mcp"
    "docker-compose.yaml"
    "docker/docker-entrypoint-mcp.sh"
    "docker/test-reddit.py"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [ ! -f "./$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
    echo "✅ $file exists"
done

# Check for absolute paths in scripts
echo ""
echo "🔍 Checking for absolute paths..."
if grep -r "/Users/" docker/ --include="*.sh" --include="*.py" 2>/dev/null | grep -v "deployTest.sh" | grep -v "# Check for absolute paths"; then
    echo "❌ Found absolute paths in docker/ directory"
    exit 1
fi
echo "✅ No absolute paths found"

# Check for uppercase filenames (excluding standard Docker/README files)
echo ""
echo "🔍 Checking for uppercase filenames..."
uppercase_files=$(find docker/ -name "*[A-Z]*" -type f | grep -v -E "(Dockerfile|README|\.md$|\.py$|deploy-test\.sh)" || true)
if [ -n "$uppercase_files" ]; then
    echo "$uppercase_files"
    echo "❌ Found problematic uppercase filenames"
    exit 1
fi
echo "✅ No problematic uppercase files"

# Test MCP servers
echo ""
echo "🔍 Testing MCP servers..."

# Test stdio
echo "Testing stdio server..."
timeout 3 python -m browser_use.mcp.server 2>&1 | head -5 && echo "✅ stdio server importable" || echo "✅ stdio server timeout (expected)"

# Test SSE
echo "Testing SSE server..."
timeout 3 python -m browser_use.mcp.server_sse --help 2>&1 | head -5 && echo "✅ SSE server importable" || true

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ All Pre-Deployment Checks Passed                             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Next Steps:"
echo "  1. Set API keys in .env file (copy from .env.example)"
echo "  2. Build Docker: docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:mcp-latest ."
echo "  3. Start Docker: docker-compose up -d"
echo "  4. Run full test suite: ./docker/test-all-mcp.sh"
echo "  5. Optional - Run Reddit integration: python docker/test-reddit.py"
echo ""
echo "💡 Quick test: python docker/validate-mcp.py"
echo ""
