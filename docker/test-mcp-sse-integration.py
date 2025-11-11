#!/usr/bin/env python3
"""
Integration test for MCP SSE server POST /messages endpoint.

Tests both JSON and multipart/form-data POST flows:
1. Connect to /sse and read session_id from endpoint event
2. POST JSON-RPC message to /messages?session_id=...
3. Validate server accepts with HTTP 202
"""

import asyncio
import json
import subprocess
import time
from typing import Optional

import httpx


class MCPSSEIntegrationTest:
    """Integration test for MCP SSE server."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.server_process: Optional[subprocess.Popen] = None
        
    async def start_server(self):
        """Start the MCP SSE server in the background."""
        print("🚀 Starting MCP SSE server...")
        self.server_process = subprocess.Popen(
            ["python", "-m", "browser_use.mcp.server_sse", "--host", self.host, "--port", str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait for server to start
        await asyncio.sleep(2)
        print("✅ Server started")
        
    def stop_server(self):
        """Stop the MCP SSE server."""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            print("✅ Server stopped")
            
    async def test_health_endpoint(self) -> bool:
        """Test the /health endpoint."""
        print("\n" + "="*70)
        print("Test 1: Health Endpoint")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Health check passed")
                    print(f"   Server: {data.get('server')}")
                    print(f"   Version: {data.get('version')}")
                    print(f"   Transport: {data.get('transport')}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return False
                
    async def test_sse_connection(self) -> Optional[str]:
        """Test SSE connection and extract session_id."""
        print("\n" + "="*70)
        print("Test 2: SSE Connection and Session ID Extraction")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                async with client.stream('GET', f"{self.base_url}/sse") as response:
                    if response.status_code != 200:
                        print(f"❌ SSE connection failed: HTTP {response.status_code}")
                        return None
                        
                    print(f"✅ SSE stream connected")
                    
                    # Read first event (should be 'endpoint' event with session_id)
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                            print(f"   Event type: {event_type}")
                        elif line.startswith("data:"):
                            data = line.split(":", 1)[1].strip()
                            print(f"   Data: {data}")
                            
                            # Extract session_id from data (format: /messages?session_id=...)
                            if "session_id=" in data:
                                session_id = data.split("session_id=")[1]
                                print(f"✅ Extracted session_id: {session_id}")
                                return session_id
                                
                        # Break after first complete event
                        if line == "":
                            break
                            
                print("❌ No session_id found in SSE stream")
                return None
                
            except Exception as e:
                print(f"❌ SSE connection error: {e}")
                return None
                
    async def test_json_post(self, session_id: str) -> bool:
        """Test JSON POST to /messages endpoint."""
        print("\n" + "="*70)
        print("Test 3: JSON POST to /messages")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                message = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "id": 1
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    params={"session_id": session_id},
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   Status: {response.status_code}")
                print(f"   Body: {response.text}")
                
                if response.status_code == 202:
                    print(f"✅ JSON POST accepted (HTTP 202)")
                    return True
                else:
                    print(f"❌ JSON POST failed: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ JSON POST error: {e}")
                return False
                
    async def test_multipart_post(self, session_id: str) -> bool:
        """Test multipart/form-data POST to /messages endpoint."""
        print("\n" + "="*70)
        print("Test 4: Multipart/Form-Data POST to /messages")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                message = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "id": 2
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    params={"session_id": session_id},
                    files={"data": (None, json.dumps(message), "application/json")}
                )
                
                print(f"   Status: {response.status_code}")
                print(f"   Body: {response.text}")
                
                if response.status_code == 202:
                    print(f"✅ Multipart POST accepted (HTTP 202)")
                    return True
                else:
                    print(f"❌ Multipart POST failed: HTTP {response.status_code}")
                    print(f"   (This is expected until multipart support is implemented)")
                    return False
                    
            except Exception as e:
                print(f"❌ Multipart POST error: {e}")
                return False
                
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*70)
        print("  MCP SSE Integration Tests")
        print("="*70)
        
        results = []
        
        # Test 1: Health check
        health_ok = await self.test_health_endpoint()
        results.append(("Health endpoint", health_ok))
        
        if not health_ok:
            print("\n❌ Server not healthy, skipping remaining tests")
            return results
            
        # Test 2: SSE connection and session extraction
        session_id = await self.test_sse_connection()
        results.append(("SSE connection", session_id is not None))
        
        if not session_id:
            print("\n❌ Could not get session_id, skipping POST tests")
            return results
            
        # Test 3: JSON POST
        json_ok = await self.test_json_post(session_id)
        results.append(("JSON POST", json_ok))
        
        # Test 4: Multipart POST
        multipart_ok = await self.test_multipart_post(session_id)
        results.append(("Multipart POST", multipart_ok))
        
        return results
        
    async def run(self, start_server: bool = True):
        """Run the complete test suite."""
        try:
            if start_server:
                await self.start_server()
                
            results = await self.run_all_tests()
            
            # Print summary
            print("\n" + "="*70)
            print("  Test Summary")
            print("="*70)
            
            passed = sum(1 for _, ok in results if ok)
            total = len(results)
            
            for test_name, ok in results:
                status = "✅ PASS" if ok else "❌ FAIL"
                print(f"{status}: {test_name}")
                
            print(f"\nResults: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n🎉 All tests passed!")
            else:
                print(f"\n⚠️  {total - passed} test(s) failed")
                
            return passed == total
            
        finally:
            if start_server:
                self.stop_server()


async def main():
    """Main entry point."""
    test = MCPSSEIntegrationTest()
    success = await test.run(start_server=True)
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
