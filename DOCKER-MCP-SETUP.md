# Browser-Use MCP Server - Complete Setup Guide

This document provides complete instructions for building, testing, and deploying the Browser-Use MCP (Model Context Protocol) Server with SSE (Server-Sent Events) transport.

## 📁 Files Created

### Core MCP Server
- **`browser_use/mcp/server_sse.py`** - SSE transport wrapper for MCP server
- **`pyproject.toml`** - Updated with `mcp-server` optional dependencies

### Docker Files
- **`Dockerfile.mcp`** - Full-featured Dockerfile with build cache (requires BuildKit)
- **`Dockerfile.mcp.simple`** - Simplified Dockerfile (works with legacy Docker)
- **`docker-compose.yaml`** - Docker Compose configuration
- **`docker/docker-entrypoint-mcp.sh`** - Entrypoint script for Docker container
- **`.env.example.mcp`** - Example environment configuration

### Documentation & Testing
- **`docker/README-MCP.md`** - Complete MCP server documentation
- **`docker/test_mcp_server.py`** - Automated test suite for MCP server
- **`docker/test_local_mcp_server.sh`** - Quick local testing script
- **`docker/build-and-push-mcp.sh`** - Build and push to Docker Hub

## 🚀 Quick Start

### Option 1: Local Testing (Fastest)

```bash
# Install dependencies
cd /Users/hubertus/Projects/browser-use
uv venv
source .venv/bin/activate
uv sync --all-extras

# Set API key
export OPENAI_API_KEY=your-key-here

# Start MCP server
python -m browser_use.mcp.server_sse --host 0.0.0.0 --port 8000

# In another terminal, test it
python docker/test_mcp_server.py
```

### Option 2: Docker Compose (Production)

```bash
# Copy environment template
cp .env.example.mcp .env

# Edit .env and add your API key
nano .env

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f browser-use-mcp

# Test the server
curl http://localhost:8000/health
```

### Option 3: Build and Push to Docker Hub

```bash
# Build and push to your Docker Hub account
./docker/build-and-push-mcp.sh

# Or manually:
docker build -f Dockerfile.mcp.simple -t hubertusgbecker/browser-use:mcp-latest .
docker push hubertusgbecker/browser-use:mcp-latest
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                           │
│            (Claude Desktop, Python, etc.)               │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/SSE
                      │ Port 8000
┌─────────────────────▼───────────────────────────────────┐
│           Browser-Use MCP Server (SSE)                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Endpoints:                                     │   │
│  │  - GET  /health     (Health check)             │   │
│  │  - GET  /sse        (SSE connection)           │   │
│  │  - POST /messages   (MCP messages)             │   │
│  └─────────────────────────────────────────────────┘   │
│                       │                                 │
│                       │                                 │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │         Browser-Use Core Agent                  │   │
│  │  - Browser automation                           │   │
│  │  - LLM integration                              │   │
│  │  - Tool execution                               │   │
│  └─────────────────────────────────────────────────┘   │
│                       │                                 │
│                       │ CDP (Port 9222)                 │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │           Chromium Browser                      │   │
│  │  - Headless mode                                │   │
│  │  - VNC viewable (Port 5900)                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing Status

### ✅ Local Testing (Completed)
- MCP SSE server starts successfully
- Health endpoint responds correctly
- SSE endpoint is accessible
- All test cases pass (4/4)

### Test Results
```
============================================================
🧪 Browser-Use MCP Server Test Suite
============================================================
Testing server at: http://localhost:8000

✅ Health check passed
✅ Server information retrieved
✅ SSE endpoint is accessible
✅ Invalid endpoint handling works correctly

Tests passed: 4/4
✅ All tests passed!
```

## 🐳 Docker Build Status

### Current Status
- ✅ `Dockerfile.mcp.simple` created and ready
- ✅ `docker-compose.yaml` configured
- ✅ Entrypoint script created
- ✅ Environment template created
- ⏳ Docker image build pending (estimated: 10-15 minutes)
- ⏳ Docker Hub push pending

### To Build Docker Image

```bash
# Build the image (takes 10-15 minutes)
docker build -f Dockerfile.mcp.simple -t hubertusgbecker/browser-use:mcp-latest .

# Or use the helper script
./docker/build-and-push-mcp.sh
```

## 📦 MCP Server Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Health check and server info | JSON with status, version, uptime |
| `/sse` | GET | SSE connection for MCP | Server-Sent Events stream |
| `/messages` | POST | Send messages to MCP | Message acknowledgment |

## 🔧 Configuration

### Environment Variables

```bash
# Required: At least one LLM API key
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
BROWSER_USE_API_KEY=...

# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
SESSION_TIMEOUT_MINUTES=30

# Browser Configuration
BROWSER_USE_HEADLESS=true
BROWSER_USE_DISABLE_SECURITY=false
BROWSER_USE_LOGGING_LEVEL=warning

# Optional: VNC for browser viewing
ENABLE_VNC=false
VNC_PASSWORD=browseruse
```

### Ports

| Port | Service | Purpose |
|------|---------|---------|
| 8000 | MCP SSE Server | HTTP API for MCP clients |
| 5900 | VNC Server | Remote browser viewing (optional) |
| 9222 | CDP | Chrome DevTools Protocol |

## 🎯 Available MCP Tools

The server exposes these browser automation tools:

### Direct Browser Control
- `browser_navigate` - Navigate to URLs
- `browser_click` - Click elements by index
- `browser_type` - Type text into inputs
- `browser_get_state` - Get page state with interactive elements
- `browser_scroll` - Scroll the page
- `browser_go_back` - Navigate back

### Tab Management
- `browser_list_tabs` - List all open tabs
- `browser_switch_tab` - Switch to specific tab
- `browser_close_tab` - Close a tab

### Content & Session
- `browser_extract_content` - Extract structured content
- `browser_list_sessions` - List active sessions
- `browser_close_session` - Close specific session
- `browser_close_all` - Close all sessions

### Autonomous Agent
- `retry_with_browser_use_agent` - Run full AI agent for complex tasks

## 📊 Resource Requirements

### Minimum
- **CPU**: 1 core
- **Memory**: 2GB
- **Disk**: 2GB
- **Network**: Internet access for LLM APIs

### Recommended
- **CPU**: 2 cores
- **Memory**: 4GB
- **Disk**: 5GB
- **Shared Memory**: 2GB for Chrome

## 🔐 Security Considerations

1. **API Keys**: Use secrets management, not plain environment variables
2. **Network**: Place behind reverse proxy (nginx, traefik)
3. **Authentication**: Add auth layer if exposing publicly
4. **Resource Limits**: Configure appropriate CPU/memory limits
5. **Firewall**: Restrict access to trusted IPs only

## 📝 Usage Examples

### Python Client

```python
import asyncio
import httpx

async def test_mcp_server():
    client = httpx.AsyncClient()
    
    # Health check
    response = await client.get("http://localhost:8000/health")
    print(response.json())
    
    await client.aclose()

asyncio.run(test_mcp_server())
```

### curl

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "server": "browser-use-mcp",
#   "version": "0.9.5",
#   "transport": "sse",
#   "uptime_seconds": 42
# }
```

## 🐛 Troubleshooting

### Server Won't Start

**Check logs:**
```bash
docker-compose logs browser-use-mcp
```

**Common issues:**
- No API key configured
- Port 8000 already in use
- Insufficient memory

### Connection Refused

**Verify server is running:**
```bash
docker-compose ps
curl http://localhost:8000/health
```

### Browser Crashes

**Increase shared memory:**
```yaml
# In docker-compose.yaml
shm_size: '4gb'
```

### High Memory Usage

**Adjust limits:**
```yaml
deploy:
  resources:
    limits:
      memory: 2G
environment:
  SESSION_TIMEOUT_MINUTES: "10"
```

## 🚀 Next Steps

### To Complete Deployment:

1. **Build Docker Image** (10-15 minutes):
   ```bash
   docker build -f Dockerfile.mcp.simple -t hubertusgbecker/browser-use:mcp-latest .
   ```

2. **Test Docker Image**:
   ```bash
   docker-compose up -d
   docker-compose logs -f
   curl http://localhost:8000/health
   ```

3. **Push to Docker Hub**:
   ```bash
   docker push hubertusgbecker/browser-use:mcp-latest
   docker tag hubertusgbecker/browser-use:mcp-latest hubertusgbecker/browser-use:mcp-v0.9.5
   docker push hubertusgbecker/browser-use:mcp-v0.9.5
   ```

4. **Test from Another Machine**:
   ```bash
   docker pull hubertusgbecker/browser-use:mcp-latest
   docker run -p 8000:8000 -e OPENAI_API_KEY=xxx hubertusgbecker/browser-use:mcp-latest
   ```

## 📚 Documentation

- **Main README**: `docker/README-MCP.md`
- **MCP Documentation**: https://docs.browser-use.com/customize/mcp/quickstart
- **Browser-Use Docs**: https://docs.browser-use.com

## 🎉 Success Criteria

- ✅ Local MCP server runs successfully
- ✅ Health endpoint responds correctly
- ✅ All test cases pass
- ✅ Docker configuration created
- ⏳ Docker image built and tested
- ⏳ Image pushed to Docker Hub
- ⏳ Image accessible from remote machines

## 📞 Support

- **GitHub**: https://github.com/browser-use/browser-use
- **Discord**: https://link.browser-use.com/discord
- **Issues**: https://github.com/browser-use/browser-use/issues

---

**Status**: ✅ Core implementation complete, ready for Docker build and deployment
**Next**: Run `./docker/build-and-push-mcp.sh` to build and push to Docker Hub
