"""SSE (Server-Sent Events) transport wrapper for browser-use MCP server.

This module provides SSE transport support for the browser-use MCP server,
allowing it to be accessed via HTTP instead of stdio.

Usage:
    python -m browser_use.mcp.server_sse --port 8000
    
Or via browser-use CLI:
    browser-use --mcp-sse --port 8000
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# Set environment variables BEFORE any browser_use imports
os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'warning'
os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'

# Add browser-use to path if running from source
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

try:
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import Response, StreamingResponse
    from starlette.requests import Request
    import uvicorn
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False
    print("Starlette/Uvicorn not available. Install with: pip install starlette uvicorn", file=sys.stderr)
    sys.exit(1)

try:
    from mcp.server.sse import SseServerTransport
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions
    MCP_SSE_AVAILABLE = True
except ImportError:
    MCP_SSE_AVAILABLE = False
    print("MCP SSE support not available. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from browser_use.mcp.server import BrowserUseServer, _configure_mcp_server_logging, _ensure_all_loggers_use_stderr
from browser_use.utils import get_browser_use_version
from browser_use.telemetry import MCPServerTelemetryEvent, ProductTelemetry

# Configure logging for MCP SSE mode
_configure_mcp_server_logging()
_ensure_all_loggers_use_stderr()

logger = logging.getLogger(__name__)


class SSEMCPServer:
    """SSE transport wrapper for Browser Use MCP server."""
    
    def __init__(self, browser_server: BrowserUseServer, host: str = "0.0.0.0", port: int = 8000):
        self.browser_server = browser_server
        self.host = host
        self.port = port
        self.sse = SseServerTransport("/messages")
        self._start_time = time.time()
        self._telemetry = ProductTelemetry()
        
    async def handle_sse(self, request: Request) -> Response:
        """Handle SSE connection endpoint."""
        async with self.sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # type: ignore
        ) as streams:
            await self.browser_server.server.run(
                streams[0],
                streams[1],
                InitializationOptions(
                    server_name="browser-use",
                    server_version=get_browser_use_version(),
                    capabilities=self.browser_server.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        return Response()
    
    async def handle_messages(self, request: Request) -> Response:
        """Handle incoming messages endpoint.
        
        Supports two content types:
        1. application/json - Direct JSON body (standard MCP SSE)
        2. multipart/form-data - Extracts 'data' field containing JSON
        """
        try:
            content_type = request.headers.get("content-type", "")
            
            # Check if this is a multipart/form-data request
            if "multipart/form-data" in content_type:
                # Parse form data and extract the 'data' field
                form = await request.form()
                data_field = form.get("data")
                
                if not data_field:
                    return Response(
                        content="Missing 'data' field in form",
                        status_code=400,
                        media_type="text/plain"
                    )
                
                # Get the JSON content from the data field
                if hasattr(data_field, 'read'):
                    # It's an UploadFile
                    json_body_bytes = await data_field.read()  # type: ignore
                    json_body = json_body_bytes.decode('utf-8') if isinstance(json_body_bytes, bytes) else str(json_body_bytes)
                else:
                    # It's a string
                    json_body = str(data_field)
                
                # Create a new scope/receive/send that will provide the JSON body
                # to the SSE transport's handle_post_message
                from starlette.datastructures import Headers
                
                # Build new scope with modified headers and body
                new_scope = dict(request.scope)
                new_headers = [(b"content-type", b"application/json")]
                
                # Preserve other headers except content-type and content-length
                for name, value in request.scope.get("headers", []):
                    if name.lower() not in (b"content-type", b"content-length"):
                        new_headers.append((name, value))
                
                # Add new content-length
                json_bytes = json_body.encode('utf-8') if isinstance(json_body, str) else json_body
                new_headers.append((b"content-length", str(len(json_bytes)).encode('ascii')))
                new_scope["headers"] = new_headers
                
                # Create a new receive function that returns our JSON body
                async def new_receive():
                    return {
                        "type": "http.request",
                        "body": json_bytes,
                        "more_body": False
                    }
                
                # Forward to SSE transport with modified scope/receive
                await self.sse.handle_post_message(new_scope, new_receive, request._send)  # type: ignore
                return Response(status_code=200)
            else:
                # Standard JSON POST - forward directly to SSE transport
                await self.sse.handle_post_message(request.scope, request.receive, request._send)  # type: ignore
                return Response(status_code=200)
                
        except Exception as exc:
            logger.exception("Error handling POST /messages")
            return Response(content=str(exc), status_code=500, media_type="text/plain")
    
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint."""
        return Response(
            content=json.dumps({
                "status": "healthy",
                "server": "browser-use-mcp",
                "version": get_browser_use_version(),
                "transport": "sse",
                "uptime_seconds": int(time.time() - self._start_time)
            }),
            media_type="application/json"
        )
    
    def create_app(self) -> Starlette:
        """Create the Starlette application."""
        app = Starlette(
            debug=False,
            routes=[
                Route("/sse", self.handle_sse, methods=["GET"]),
                Route("/messages", self.handle_messages, methods=["POST"]),
                Route("/health", self.health_check, methods=["GET"]),
            ],
        )
        
        # Add CORS middleware
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app


async def main_sse(host: str = "0.0.0.0", port: int = 8000, session_timeout_minutes: int = 10):
    """Run the MCP server with SSE transport."""
    if not MCP_SSE_AVAILABLE or not STARLETTE_AVAILABLE:
        print("Required dependencies not available.", file=sys.stderr)
        print("Install with: pip install starlette uvicorn mcp", file=sys.stderr)
        sys.exit(1)
    
    print(f"🚀 Starting browser-use MCP server with SSE transport...", file=sys.stderr)
    print(f"📡 Listening on http://{host}:{port}", file=sys.stderr)
    print(f"🔌 SSE endpoint: http://{host}:{port}/sse", file=sys.stderr)
    print(f"💬 Messages endpoint: http://{host}:{port}/messages", file=sys.stderr)
    print(f"❤️  Health check: http://{host}:{port}/health", file=sys.stderr)
    
    # Create browser server
    browser_server = BrowserUseServer(session_timeout_minutes=session_timeout_minutes)
    
    # Start cleanup task
    await browser_server._start_cleanup_task()
    
    # Create SSE server
    sse_server = SSEMCPServer(browser_server, host, port)
    app = sse_server.create_app()
    
    # Send telemetry
    sse_server._telemetry.capture(
        MCPServerTelemetryEvent(
            version=get_browser_use_version(),
            action='start',
            parent_process_cmdline=None,
        )
    )
    
    print(f"✅ Server started successfully", file=sys.stderr)
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...", file=sys.stderr)
    finally:
        duration = time.time() - sse_server._start_time
        sse_server._telemetry.capture(
            MCPServerTelemetryEvent(
                version=get_browser_use_version(),
                action='stop',
                duration_seconds=duration,
                parent_process_cmdline=None,
            )
        )
        sse_server._telemetry.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run browser-use MCP server with SSE transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--session-timeout", type=int, default=10, 
                       help="Session timeout in minutes (default: 10)")
    
    args = parser.parse_args()
    
    asyncio.run(main_sse(
        host=args.host,
        port=args.port,
        session_timeout_minutes=args.session_timeout
    ))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run browser-use MCP server with SSE transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--session-timeout", type=int, default=10, 
                       help="Session timeout in minutes (default: 10)")
    
    args = parser.parse_args()
    
    asyncio.run(main_sse(
        host=args.host,
        port=args.port,
        session_timeout_minutes=args.session_timeout
    ))
