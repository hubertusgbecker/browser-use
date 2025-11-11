<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/2ccdb752-22fb-41c7-8948-857fc1ad7e24">
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/774a46d5-27a0-490c-b7d0-e65fcbbfa358">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." src="https://github.com/user-attachments/assets/2ccdb752-22fb-41c7-8948-857fc1ad7e24" width="full">
</picture>

<div align="center">
  <h1>Browser-Use with MCP Support</h1>
  <p><strong>The Original Browser-Use + Model Context Protocol (MCP) Integration</strong></p>
  
  <a href="https://github.com/browser-use/browser-use">
    <img src="https://img.shields.io/badge/upstream-browser--use-blue?logo=github" alt="Upstream">
  </a>
  <a href="https://hub.docker.com/r/hubertusgbecker/browser-use">
    <img src="https://img.shields.io/docker/v/hubertusgbecker/browser-use?logo=docker&label=docker" alt="Docker">
  </a>
  <a href="https://github.com/hubertusgbecker/browser-use/releases">
    <img src="https://img.shields.io/github/v/release/hubertusgbecker/browser-use" alt="Release">
  </a>
</div>

---

## 🌟 What is This?

This is a **fork** of the amazing [browser-use](https://github.com/browser-use/browser-use) project by [@mamagnus00](https://x.com/mamagnus00) and [@gregpr07](https://x.com/gregpr07), enhanced with **MCP (Model Context Protocol)** server support.

### Original Browser-Use

Browser-Use is an AI agent that autonomously controls your browser using natural language. It combines LLMs with browser automation to complete complex tasks like form filling, research, shopping, and more.

**→ Original Repository**: [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use)  
**→ Official Docs**: [docs.browser-use.com](https://docs.browser-use.com)  
**→ Cloud Service**: [cloud.browser-use.com](https://cloud.browser-use.com)

### This Fork Adds MCP Support

**MCP (Model Context Protocol)** enables standardized communication between AI applications and external tools. This fork adds:

- ✅ **MCP stdio server** - For local command-line usage
- ✅ **MCP SSE server** - For HTTP-based clients (production-ready)
- ✅ **Docker deployment** - Pre-configured containers with all dependencies
- ✅ **Comprehensive testing** - Validated and production-ready

Use Browser-Use as an MCP server to expose browser automation capabilities to any MCP-compatible client (Claude Desktop, VS Code, custom applications).

---

## 🚀 Quick Start

### Option 1: Use Original Browser-Use (Recommended)

```bash
# Install
uv add browser-use
uv sync

# Get free API key from https://cloud.browser-use.com/new-api-key
echo "BROWSER_USE_API_KEY=your-key" >> .env

# Install browser
uvx browser-use install

# Run
python your_agent.py
```

See the [official quickstart](https://docs.browser-use.com/quickstart) for more details.

---

### Option 2: Use This Fork with MCP

#### Local MCP stdio Server

```bash
# Clone this fork
git clone https://github.com/hubertusgbecker/browser-use.git
cd browser-use

# Setup environment
uv venv --python 3.11
source .venv/bin/activate
uv sync

# Run MCP server (stdio)
python -m browser_use.mcp.server
```

Connect your MCP client to stdin/stdout of this process.

#### MCP SSE Server (HTTP)

```bash
# Start SSE server
python -m browser_use.mcp.server_sse --host 0.0.0.0 --port 8000

# In another terminal, test it
curl http://localhost:8000/health
```

Connect MCP clients to `http://localhost:8000/sse`

#### Docker Deployment (Production)

```bash
# Build image
docker build -f Dockerfile.mcp -t hubertusgbecker/browser-use:0.9.5 .

# Or pull from Docker Hub
docker pull hubertusgbecker/browser-use:0.9.5

# Start with docker-compose
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

**Docker image**: `hubertusgbecker/browser-use:0.9.5`

---

## 🔧 MCP Server Details

### stdio Transport

```bash
python -m browser_use.mcp.server
```

Communicates via JSON-RPC over stdin/stdout. Perfect for local integrations and command-line tools.

### SSE Transport (HTTP)

```bash
python -m browser_use.mcp.server_sse --host 127.0.0.1 --port 8000
```

HTTP-based Server-Sent Events transport. Production-ready with health checks and monitoring.

**Endpoints**:
- `GET /health` - Health check
- `GET /sse` - MCP SSE stream (connect clients here)
- `POST /messages` - Message submission

### Docker Container

The Docker image includes:
- Browser-Use v0.9.5
- MCP servers (stdio + SSE)
- Chromium browser (pre-installed)
- VNC server (port 5900) - for viewing browser
- CDP endpoint (port 9222) - Chrome DevTools Protocol

**Ports**:
- `8000` - MCP SSE server
- `5900` - VNC (view browser)
- `9222` - Chrome DevTools Protocol

**Volumes**:
- `./data` - Persistent data storage
- `./downloads` - Agent file operations

---

## 🧪 Testing

Run comprehensive tests to validate MCP functionality:

```bash
# Quick validation (4 tests)
python docker/validate-mcp.py

# Full test suite
./docker/test-all-mcp.sh

# End-to-end test
python docker/test-mcp-e2e.py

# Integration test (requires API key)
python docker/test-reddit.py
```

All tests are validated and passing ✅

---

## 🐳 Docker Configuration

### docker-compose.yaml

```yaml
services:
  browser-use-mcp-server:
    image: hubertusgbecker/browser-use:0.9.5
    container_name: browser-use-mcp-server
    ports:
      - "8000:8000"  # MCP SSE server
      - "5900:5900"  # VNC
      - "9222:9222"  # CDP
    volumes:
      - ./data:/data
      - ./downloads:/downloads
    environment:
      - BROWSER_USE_API_KEY=${BROWSER_USE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
```

### Environment Variables

Create `.env` file:

```bash
# For ChatBrowserUse (recommended - $10 free credits)
BROWSER_USE_API_KEY=your-key

# Or use other LLMs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

---

## 📚 Documentation

### This Fork

- **MCP Testing**: `docker/MCP-TESTING.md` - Testing guide
- **Docker Deployment**: `DOCKER-DEPLOYMENT.md` - Deployment details

### Original Browser-Use

- **Official Docs**: [docs.browser-use.com](https://docs.browser-use.com)
- **Examples**: [github.com/browser-use/browser-use/examples](https://github.com/browser-use/browser-use/tree/main/examples)
- **Cloud Docs**: [docs.cloud.browser-use.com](https://docs.cloud.browser-use.com)

---

## 🎯 Use Cases

### As MCP Server

Expose browser automation to MCP clients:
- **Claude Desktop** - Control browser through Claude
- **VS Code Extensions** - Browser automation in IDE
- **Custom Applications** - Integrate via MCP protocol

### Direct Usage (Original)

Use Browser-Use directly for:
- Form filling and data entry
- Web scraping and research
- Shopping and price comparison
- Testing and QA automation
- Social media management

See [demos](https://docs.browser-use.com/examples) in the original repository.

---

## 🛠️ Development

### Setup

```bash
git clone https://github.com/hubertusgbecker/browser-use.git
cd browser-use
uv venv --python 3.11
source .venv/bin/activate
uv sync --all-extras --dev
```

### Pre-commit Hooks

```bash
./bin/lint.sh
```

### Run Tests

```bash
./bin/test.sh
```

---

## 🔄 Relationship to Upstream

This fork tracks [browser-use/browser-use](https://github.com/browser-use/browser-use) and adds MCP server capabilities.

**What's the same**:
- ✅ Complete Browser-Use library (v0.9.5)
- ✅ All original features and APIs
- ✅ Compatible with official examples
- ✅ Works with Browser-Use Cloud

**What's added**:
- ✅ MCP stdio server implementation
- ✅ MCP SSE server (HTTP transport)
- ✅ Docker deployment configuration
- ✅ Comprehensive test suite

**To use original Browser-Use without MCP**:
→ Go to [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use)

---

## 📦 Installation Options

### 1. Original Browser-Use (pip)
```bash
pip install browser-use
```

### 2. This Fork (from source)
```bash
git clone https://github.com/hubertusgbecker/browser-use.git
cd browser-use
uv sync
```

### 3. Docker (this fork)
```bash
docker pull hubertusgbecker/browser-use:0.9.5
```

---

## 🤝 Contributing

This is a personal fork. For Browser-Use core development:
→ Contribute to [browser-use/browser-use](https://github.com/browser-use/browser-use)

For MCP-specific features in this fork:
→ Open issues or PRs in this repository

---

## 📄 License

MIT License - Same as original [Browser-Use](https://github.com/browser-use/browser-use)

---

## 🙏 Credits

**Original Browser-Use** by:
- [@mamagnus00](https://x.com/mamagnus00) (Magnus)
- [@gregpr07](https://x.com/gregpr07) (Gregor)
- Made with ❤️ in Zurich and San Francisco

**MCP Integration** by:
- [@hubertusgbecker](https://github.com/hubertusgbecker)

**Community**:
- [Discord](https://link.browser-use.com/discord)
- [Twitter](https://x.com/browser_use)
- [Documentation](https://docs.browser-use.com)

---

## ⚡ Quick Links

| Resource | Link |
|----------|------|
| **Original Repo** | [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use) |
| **This Fork** | [github.com/hubertusgbecker/browser-use](https://github.com/hubertusgbecker/browser-use) |
| **Docker Hub** | [hub.docker.com/r/hubertusgbecker/browser-use](https://hub.docker.com/r/hubertusgbecker/browser-use) |
| **Official Docs** | [docs.browser-use.com](https://docs.browser-use.com) |
| **Cloud Service** | [cloud.browser-use.com](https://cloud.browser-use.com) |
| **MCP Spec** | [modelcontextprotocol.io](https://modelcontextprotocol.io) |

---

<div align="center">
  
**Original Browser-Use**: Tell your computer what to do, and it gets it done.  
**This Fork**: Now accessible via Model Context Protocol.

[![Star the original](https://img.shields.io/github/stars/browser-use/browser-use?style=social)](https://github.com/browser-use/browser-use)
[![Star this fork](https://img.shields.io/github/stars/hubertusgbecker/browser-use?style=social)](https://github.com/hubertusgbecker/browser-use)

</div>
