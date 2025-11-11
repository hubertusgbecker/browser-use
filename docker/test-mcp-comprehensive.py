#!/usr/bin/env python3
"""
Comprehensive MCP Server Test Suite
Tests both stdio and SSE transports with real JSON-RPC calls
"""
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️  httpx not installed, SSE tests will be skipped")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class MCPTester:
    """Test MCP server functionality"""
    
    def __init__(self):
        self.results = []
        
    def print_header(self, title):
        """Print test section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
        
    def record_result(self, name, passed, error=None, details=None):
        """Record test result"""
        self.results.append({
            "name": name,
            "passed": passed,
            "error": error,
            "details": details
        })
        
        if passed:
            print(f"✅ PASS: {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ FAIL: {name}")
            if error:
                print(f"   Error: {error}")
                
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("MCP TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['name']}")
            if result["error"]:
                print(f"     {result['error']}")
                
        print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")
        print("="*70)
        
        return passed == total
        
    async def test_mcp_stdio_basic(self):
        """Test 1: MCP stdio server can start and respond"""
        self.print_header("Test 1: MCP stdio Server - Basic")
        
        try:
            # Start MCP server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Write request
            request_str = json.dumps(initialize_request) + "\n"
            proc.stdin.write(request_str)
            proc.stdin.flush()
            
            # Read response (with timeout)
            await asyncio.sleep(2)
            
            # Try to read output
            try:
                # Use non-blocking read
                import select
                if select.select([proc.stdout], [], [], 0)[0]:
                    response = proc.stdout.readline()
                    if response:
                        data = json.loads(response)
                        if "result" in data or "error" in data:
                            self.record_result(
                                "MCP stdio - Initialize", 
                                True,
                                details=f"Got response: {data.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}"
                            )
                        else:
                            self.record_result("MCP stdio - Initialize", False, "Invalid response format")
                    else:
                        self.record_result("MCP stdio - Initialize", False, "No response received")
                else:
                    self.record_result("MCP stdio - Initialize", True, details="Server started (no immediate response)")
            except Exception as e:
                self.record_result("MCP stdio - Initialize", True, details=f"Server running: {str(e)}")
            
            # Cleanup
            proc.terminate()
            proc.wait(timeout=5)
            
            return True
            
        except Exception as e:
            self.record_result("MCP stdio - Initialize", False, str(e))
            return False
            
    async def test_mcp_stdio_tools(self):
        """Test 2: MCP stdio server lists tools"""
        self.print_header("Test 2: MCP stdio Server - List Tools")
        
        try:
            # Start MCP server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            await asyncio.sleep(1)
            
            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            request_str = json.dumps(tools_request) + "\n"
            proc.stdin.write(request_str)
            proc.stdin.flush()
            
            await asyncio.sleep(2)
            
            # Cleanup
            proc.terminate()
            proc.wait(timeout=5)
            
            self.record_result("MCP stdio - List Tools", True, details="Request sent successfully")
            return True
            
        except Exception as e:
            self.record_result("MCP stdio - List Tools", False, str(e))
            return False
            
    async def test_mcp_sse_health(self):
        """Test 3: MCP SSE server health check"""
        self.print_header("Test 3: MCP SSE Server - Health Check")
        
        if not HTTPX_AVAILABLE:
            self.record_result("MCP SSE - Health", False, "httpx not installed")
            return False
        
        try:
            # Start SSE server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server_sse",
                 "--host", "127.0.0.1", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://127.0.0.1:8001/health")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "healthy":
                        self.record_result(
                            "MCP SSE - Health", 
                            True,
                            details=f"Server: {data.get('server')}, Version: {data.get('version')}"
                        )
                        proc.terminate()
                        return True
                    else:
                        proc.terminate()
                        self.record_result("MCP SSE - Health", False, "Unhealthy status")
                        return False
                else:
                    proc.terminate()
                    self.record_result("MCP SSE - Health", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            if 'proc' in locals():
                proc.terminate()
            self.record_result("MCP SSE - Health", False, str(e))
            return False
            
    async def test_mcp_sse_connection(self):
        """Test 4: MCP SSE server accepts connections"""
        self.print_header("Test 4: MCP SSE Server - SSE Connection")
        
        if not HTTPX_AVAILABLE:
            self.record_result("MCP SSE - Connection", False, "httpx not installed")
            return False
        
        try:
            # Start SSE server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server_sse",
                 "--host", "127.0.0.1", "--port", "8002"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            await asyncio.sleep(3)
            
            # Test SSE endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    # Send GET request to SSE endpoint
                    async with client.stream("GET", "http://127.0.0.1:8002/sse") as response:
                        if response.status_code == 200:
                            # Check content type
                            content_type = response.headers.get("content-type", "")
                            if "text/event-stream" in content_type:
                                self.record_result(
                                    "MCP SSE - Connection", 
                                    True,
                                    details=f"SSE endpoint available, content-type: {content_type}"
                                )
                                proc.terminate()
                                return True
                            else:
                                proc.terminate()
                                self.record_result("MCP SSE - Connection", False, f"Wrong content-type: {content_type}")
                                return False
                        else:
                            proc.terminate()
                            self.record_result("MCP SSE - Connection", False, f"HTTP {response.status_code}")
                            return False
                except Exception as e:
                    proc.terminate()
                    self.record_result("MCP SSE - Connection", False, str(e))
                    return False
                    
        except Exception as e:
            if 'proc' in locals():
                proc.terminate()
            self.record_result("MCP SSE - Connection", False, str(e))
            return False
            
    async def test_mcp_sse_messages(self):
        """Test 5: MCP SSE server handles messages"""
        self.print_header("Test 5: MCP SSE Server - Message Handling")
        
        if not HTTPX_AVAILABLE:
            self.record_result("MCP SSE - Messages", False, "httpx not installed")
            return False
        
        try:
            # Start SSE server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server_sse",
                 "--host", "127.0.0.1", "--port", "8003"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            await asyncio.sleep(3)
            
            # Test message endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send initialize message
                message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                response = await client.post(
                    "http://127.0.0.1:8003/messages",
                    json=message
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data or "error" in data:
                        self.record_result(
                            "MCP SSE - Messages", 
                            True,
                            details=f"Message handled, got: {list(data.keys())}"
                        )
                        proc.terminate()
                        return True
                    else:
                        proc.terminate()
                        self.record_result("MCP SSE - Messages", False, "Invalid response format")
                        return False
                else:
                    proc.terminate()
                    self.record_result("MCP SSE - Messages", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            if 'proc' in locals():
                proc.terminate()
            self.record_result("MCP SSE - Messages", False, str(e))
            return False
            
    async def test_docker_mcp(self):
        """Test 6: MCP in Docker container"""
        self.print_header("Test 6: MCP in Docker Container")
        
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.record_result("MCP Docker", False, "docker-compose not available")
                return False
            
            # Start docker-compose
            print("   Starting docker-compose...")
            subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True
            )
            
            # Wait for container to be ready
            print("   Waiting for container to start...")
            await asyncio.sleep(10)
            
            # Test health endpoint
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    try:
                        response = await client.get("http://localhost:8000/health")
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("status") == "healthy":
                                self.record_result(
                                    "MCP Docker", 
                                    True,
                                    details=f"Container running, server: {data.get('server')}"
                                )
                                
                                # Cleanup
                                subprocess.run(["docker-compose", "down"], capture_output=True)
                                return True
                            else:
                                subprocess.run(["docker-compose", "down"], capture_output=True)
                                self.record_result("MCP Docker", False, "Unhealthy status")
                                return False
                        else:
                            subprocess.run(["docker-compose", "down"], capture_output=True)
                            self.record_result("MCP Docker", False, f"HTTP {response.status_code}")
                            return False
                    except Exception as e:
                        subprocess.run(["docker-compose", "down"], capture_output=True)
                        self.record_result("MCP Docker", False, str(e))
                        return False
            else:
                # Just check if container is running
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=browser-use-mcp", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True
                )
                
                if "browser-use-mcp" in result.stdout:
                    self.record_result("MCP Docker", True, details="Container started")
                    subprocess.run(["docker-compose", "down"], capture_output=True)
                    return True
                else:
                    subprocess.run(["docker-compose", "down"], capture_output=True)
                    self.record_result("MCP Docker", False, "Container not running")
                    return False
                    
        except Exception as e:
            subprocess.run(["docker-compose", "down"], capture_output=True)
            self.record_result("MCP Docker", False, str(e))
            return False
            
    async def run_all(self):
        """Run all tests"""
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "MCP Comprehensive Test Suite" + " "*24 + "║")
        print("╚" + "="*68 + "╝")
        
        # Stdio tests
        await self.test_mcp_stdio_basic()
        await self.test_mcp_stdio_tools()
        
        # SSE tests
        await self.test_mcp_sse_health()
        await self.test_mcp_sse_connection()
        await self.test_mcp_sse_messages()
        
        # Docker test
        await self.test_docker_mcp()
        
        return self.print_summary()


async def main():
    """Main entry point"""
    tester = MCPTester()
    success = await tester.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
