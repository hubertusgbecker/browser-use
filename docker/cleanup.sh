#!/usr/bin/env bash
# Cleanup script for Browser-Use MCP development

set -e

echo "🧹 Cleaning up Browser-Use MCP development environment..."

# Remove old/duplicate files if they exist
echo "[1/5] Removing duplicate/old files..."
rm -f .env.example.mcp 2>/dev/null || true
rm -f Dockerfile.mcp.simple 2>/dev/null || true
rm -f docker/test_comprehensive.py 2>/dev/null || true
echo "✅ Duplicate files cleaned"

# Clean Docker artifacts
echo "[2/5] Cleaning Docker artifacts..."
docker stop browseruse-mcp 2>/dev/null || true
docker rm browseruse-mcp 2>/dev/null || true
echo "✅ Docker containers cleaned"

# Clean Python cache
echo "[3/5] Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python cache cleaned"

# Clean browser data if it exists
echo "[4/5] Cleaning browser data..."
rm -rf /tmp/browser-use-* 2>/dev/null || true
rm -rf ~/.cache/browser-use 2>/dev/null || true
echo "✅ Browser data cleaned"

# Show final status
echo "[5/5] Cleanup summary:"
echo "  - Configuration: Single .env.example"
echo "  - Dockerfile: Single Dockerfile.mcp"
echo "  - Test suite: docker/test_progressive.py"
echo "  - Documentation: README-MCP.md, DOCKER-MCP-SETUP.md"
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Run tests: python docker/test_progressive.py"
echo "  2. Build Docker: docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:mcp-latest ."
echo "  3. Start container: docker-compose up -d"
echo "  4. Check health: curl http://localhost:8000/health"
echo "  5. Push to Docker Hub: docker push hubertusgbecker/browser-use:mcp-latest"
