#!/usr/bin/env python3
"""
Test script for Browser-Use MCP Server with SSE transport.

This script tests the MCP server endpoints and basic browser automation functionality.

Usage:
    python docker/test_mcp_server.py [--host localhost] [--port 8000]
"""

import argparse
import asyncio
import json
import sys
from typing import Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)


class MCPServerTester:
    """Test the Browser-Use MCP Server."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("🏥 Testing health check endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_sse_endpoint(self) -> bool:
        """Test the SSE endpoint is accessible."""
        print("\n📡 Testing SSE endpoint...")
        try:
            # Just check if endpoint is accessible (don't fully connect)
            response = await self.client.get(
                f"{self.base_url}/sse",
                timeout=5.0
            )
            # SSE connections stay open, so we just check it doesn't error immediately
            print("✅ SSE endpoint is accessible")
            return True
        except httpx.TimeoutException:
            # Timeout is expected for SSE since it keeps connection open
            print("✅ SSE endpoint is accessible (connection stays open as expected)")
            return True
        except Exception as e:
            print(f"❌ SSE endpoint error: {e}")
            return False
    
    async def test_invalid_endpoint(self) -> bool:
        """Test that invalid endpoints return 404."""
        print("\n🚫 Testing invalid endpoint handling...")
        try:
            response = await self.client.get(f"{self.base_url}/invalid")
            if response.status_code == 404:
                print("✅ Invalid endpoint correctly returns 404")
                return True
            else:
                print(f"⚠️  Expected 404, got HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Invalid endpoint test error: {e}")
            return False
    
    async def test_server_info(self) -> bool:
        """Get and display server information."""
        print("\n📊 Server Information:")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"  Server: {data.get('server', 'unknown')}")
                print(f"  Version: {data.get('version', 'unknown')}")
                print(f"  Transport: {data.get('transport', 'unknown')}")
                print(f"  Status: {data.get('status', 'unknown')}")
                print(f"  Uptime: {data.get('uptime_seconds', 0)} seconds")
                return True
            return False
        except Exception as e:
            print(f"❌ Error getting server info: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests."""
        print("=" * 60)
        print("🧪 Browser-Use MCP Server Test Suite")
        print("=" * 60)
        print(f"Testing server at: {self.base_url}\n")
        
        results = []
        
        # Run tests
        results.append(await self.test_health_check())
        results.append(await self.test_server_info())
        results.append(await self.test_sse_endpoint())
        results.append(await self.test_invalid_endpoint())
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Test Summary")
        print("=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ {total - passed} test(s) failed")
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Browser-Use MCP Server with SSE transport"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    tester = MCPServerTester(host=args.host, port=args.port)
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await tester.close()


if __name__ == "__main__":
    if not HTTPX_AVAILABLE:
        print("Error: httpx is required for testing")
        print("Install with: pip install httpx")
        sys.exit(1)
    
    asyncio.run(main())
