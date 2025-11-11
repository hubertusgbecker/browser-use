# Docker Setup for Browser-Use

This directory contains Docker deployment files for browser-use with MCP (Model Context Protocol) support.

## 🚀 Quick Start - MCP Server

```bash
# 1. Pre-deployment validation
./docker/deploy-test.sh

# 2. Build Docker image
docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:mcp-latest .

# 3. Start container
docker-compose up -d

# 4. Run full test suite
./docker/test-all-mcp.sh
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`QUICKSTART.md`](./QUICKSTART.md) | Quick 5-minute setup guide |
| [`DOCKER-DEPLOYMENT.md`](./DOCKER-DEPLOYMENT.md) | Complete deployment guide |
| [`MCP-TESTING.md`](./MCP-TESTING.md) | Testing documentation |

## 🧪 Test Scripts

| Script | Purpose | Tests |
|--------|---------|-------|
| `test-all-mcp.sh` | Master test suite | All |
| `validate-mcp.py` | Quick validation | 4 |
| `test-mcp-e2e.py` | End-to-end | 3 |
| `test-mcp-comprehensive.py` | Deep validation | 6 |
| `test-reddit.py` | Integration | 1 |

## ✅ Status

**MCP Functionality**: Fully tested and validated ✅

- stdio transport: ✅ Working
- SSE transport: ✅ Working  
- Docker deployment: ✅ Working
- Production ready: ✅ Yes

**Version**: v0.9.5  
**Last Validated**: 2024-11-11

---

## 🏗️ Build System (Legacy)

For optimized build system (< 30 second builds):

```bash
# Build base images (only needed once)
./docker/build-base-images.sh

# Fast build
docker build -f Dockerfile.fast -t browseruse .
```

---

## 🏗️ Build System (Legacy)

For optimized build system (< 30 second builds):

```bash
# Build base images (only needed once)
./docker/build-base-images.sh

# Fast build
docker build -f Dockerfile.fast -t browseruse .
```

### Build Performance

| Build Type | Time |
|------------|------|
| Standard Dockerfile | ~2 minutes |
| Fast build (with base images) | ~30 seconds |
| Rebuild after code change | ~16 seconds |

### Files

- `Dockerfile` - Standard self-contained build (~2 min)
- `Dockerfile.fast` - Fast build using pre-built base images (~30 sec)
- `Dockerfile.mcp` - MCP server deployment (production)
- `docker-compose.yaml` - MCP container orchestration
- `base-images/` - Pre-built base image definitions
