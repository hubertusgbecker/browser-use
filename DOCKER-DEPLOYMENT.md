# Browser-Use MCP Docker Deployment

Complete guide for deploying Browser-Use with MCP server in Docker.

## Quick Start

### Prerequisites
```bash
# Required
- Docker & docker-compose
- API key (OPENAI_API_KEY or BROWSER_USE_API_KEY)

# Optional for local testing
- Python 3.12+
- uv package manager
```

### 1. Setup Environment

```bash
# Clone and navigate to repo
cd browser-use

# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Either OPENAI_API_KEY or BROWSER_USE_API_KEY
nano .env
```

### 2. Build Docker Image

```bash
# Build the MCP server image
docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:mcp-latest .

# This takes ~10-15 minutes (Chromium + dependencies)
```

### 3. Run with Docker Compose

```bash
# Start the MCP server
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Directory Structure

```
browser-use/
├── data/              # Persistent data (browser profiles, cache)
│   └── .gitkeep       # Keep directory in git
├── downloads/         # Agent file operations
│   └── .gitkeep
├── docker/
│   ├── deploy-test.sh # Pre-deployment validation
│   ├── test-reddit.py # Integration test script
│   └── docker-entrypoint-mcp.sh # Container entrypoint
├── Dockerfile.mcp     # Production Docker image
├── docker-compose.yaml
└── .env.example       # Environment template
```

## Data Persistence

### Local Directories

- `./data` - Mounted to `/data` in container
  - Browser profiles, cookies, session data
  - Persists across container restarts

- `./downloads` - Mounted to `/downloads` in container  
  - Files downloaded or created by agent
  - Accessible from host machine

### Why Not Volumes?

We use **bind mounts** (relative paths) instead of Docker volumes because:
- ✅ Files directly accessible on host
- ✅ Easy to inspect and modify
- ✅ Simple backup (just copy directories)
- ✅ No cleanup of orphaned volumes
- ✅ Portable across systems (relative paths)

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# LLM API Keys (choose one)
OPENAI_API_KEY=sk-...
BROWSER_USE_API_KEY=bu_...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Browser Configuration
BROWSER_USE_HEADLESS=true
BROWSER_USE_DISABLE_SECURITY=false
BROWSER_USE_LOGGING_LEVEL=warning

# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
SESSION_TIMEOUT_MINUTES=30
```

### Port Mappings

| Port | Service | Description |
|------|---------|-------------|
| 8000 | MCP SSE | Main MCP server endpoint |
| 5900 | VNC | Browser viewing (optional) |
| 9222 | CDP | Chrome DevTools Protocol |

## Testing

### Pre-Deployment Validation

```bash
# Run all checks
./docker/deploy-test.sh

# Checks:
# ✅ Directory structure
# ✅ File permissions
# ✅ No absolute paths
# ✅ Naming conventions
# ✅ MCP server imports
```

### Reddit Integration Test

```bash
# Local test (requires API key in .env)
source .venv/bin/activate
python docker/test-reddit.py

# Task: Search Reddit for 'browser-use', click first post, return first comment
# Shows: Steps taken, duration, success status
```

### Docker Container Test

```bash
# Start container
docker-compose up -d

# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "server": "browser-use-mcp",
#   "version": "0.9.5",
#   "transport": "sse"
# }

# Test MCP SSE connection
curl -N http://localhost:8000/sse

# Stop container
docker-compose down
```

## Development Workflow

### 1. Local Development

```bash
# Setup
uv sync --all-extras
source .venv/bin/activate

# Test changes
python docker/test-reddit.py

# Validate
./docker/deploy-test.sh
```

### 2. Build & Test Docker

```bash
# Build
docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:mcp-latest .

# Test
docker-compose up -d
docker-compose logs -f

# Cleanup
docker-compose down
```

### 3. Deploy to Docker Hub

```bash
# Login
docker login

# Tag versions
docker tag hubertusgbecker/browser-use:mcp-latest \
  hubertusgbecker/browser-use:mcp-v0.9.5

# Push
docker push hubertusgbecker/browser-use:mcp-latest
docker push hubertusgbecker/browser-use:mcp-v0.9.5
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Missing API key: Set in .env file
# - Port conflict: Change ports in docker-compose.yaml
# - Permission denied: Check data/ and downloads/ permissions
```

### Permission Errors

```bash
# Fix data directory permissions
chmod 755 data downloads
chown -R $USER:$USER data downloads

# Inside container (automatic):
# - Runs as user 'browseruse' (UID 911)
# - Directories checked on startup
```

### Browser Crashes

```bash
# Increase shared memory
# In docker-compose.yaml:
shm_size: '4gb'  # Increase from 2gb

# Or reduce resource usage
# Set BROWSER_USE_HEADLESS=true
```

### API Connection Issues

```bash
# Verify API key
docker-compose exec browser-use-mcp env | grep API_KEY

# Test manually
docker-compose exec browser-use-mcp \
  python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

## Best Practices

### Security

- ✅ Use environment variables for secrets
- ✅ Never commit `.env` files
- ✅ Run container as non-root user (browseruse)
- ✅ Keep `BROWSER_USE_DISABLE_SECURITY=false`
- ❌ Don't expose MCP port to internet without auth

### Performance

- Use `BROWSER_USE_HEADLESS=true` for production
- Set appropriate resource limits in docker-compose.yaml
- Clean data directory periodically to free space
- Use Browser Use API (`BROWSER_USE_API_KEY`) for fastest performance

### Monitoring

```bash
# Resource usage
docker stats browser-use-mcp-server

# Health checks
watch -n 5 'curl -s http://localhost:8000/health | jq'

# Logs with timestamps
docker-compose logs -f --timestamps
```

## Architecture

### Container Components

```
┌─────────────────────────────────────────┐
│  Browser-Use MCP Container              │
│  ┌───────────────────────────────────┐  │
│  │  MCP SSE Server (Port 8000)       │  │
│  │  - HTTP health endpoint           │  │
│  │  - SSE event stream               │  │
│  │  - Session management             │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Browser-Use Agent                │  │
│  │  - Task execution                 │  │
│  │  - LLM integration                │  │
│  │  - Tool/action execution          │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Chromium Browser                 │  │
│  │  - Headless/headed mode           │  │
│  │  - CDP on port 9222               │  │
│  │  - Extensions (uBlock, etc)       │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Xvfb (Virtual Display)           │  │
│  │  - Display :99                    │  │
│  │  - VNC on port 5900 (optional)    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │              │              │
         ↓              ↓              ↓
    ./data       ./downloads      Port 8000
```

### Data Flow

1. **Client** → HTTP/SSE to port 8000
2. **MCP Server** → Creates Browser-Use Agent
3. **Agent** → Executes task with LLM guidance
4. **Browser** → Interacts with web pages
5. **Results** → Returned via SSE to client

## Files Reference

### Core Files

- `Dockerfile.mcp` - Production Docker image definition
- `docker-compose.yaml` - Container orchestration config
- `docker/docker-entrypoint-mcp.sh` - Container startup script
- `.env.example` - Environment variable template

### Test Files

- `docker/deploy-test.sh` - Pre-deployment validation
- `docker/test-reddit.py` - Integration test example
- `docker/test_progressive.py` - Progressive test suite

### Documentation

- `docker/README-MCP.md` - MCP server documentation
- `DOCKER-MCP-SETUP.md` - Detailed setup guide

## Support

- GitHub Issues: https://github.com/browser-use/browser-use/issues
- Documentation: https://docs.browser-use.com
- Discord: https://link.browser-use.com/discord
