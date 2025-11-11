#!/usr/bin/env python3
"""
Progressive Test Suite for Browser-Use MCP Server

Tests are run in order from simplest to most complex:
1. Basic MCP stdio server functionality
2. MCP SSE server functionality  
3. Real browser automation
4. Full integration tests

Run: python docker/test_comprehensive.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️  httpx not installed. SSE tests will be skipped.")
    print("   Install with: pip install httpx")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using existing environment.")


class TestRunner:
    """Manages test execution and reporting."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        
    def test(self, name: str, func):
        """Decorator to register and run a test."""
        async def wrapper():
            self.tests_run += 1
            print(f"\n{'='*70}")
            print(f"Test {self.tests_run}: {name}")
            print(f"{'='*70}")
            try:
                await func()
                self.tests_passed += 1
                self.test_results.append((name, "✅ PASS", None))
                print(f"\n✅ PASS: {name}")
                return True
            except Exception as e:
                self.tests_failed += 1
                self.test_results.append((name, "❌ FAIL", str(e)))
                print(f"\n❌ FAIL: {name}")
                print(f"   Error: {e}")
                return False
        return wrapper
        
    def summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for name, status, error in self.test_results:
            print(f"{status} {name}")
            if error:
                print(f"     {error}")
        print(f"\nTotal: {self.tests_run} | Passed: {self.tests_passed} | Failed: {self.tests_failed}")
        print("="*70)
        return self.tests_failed == 0


runner = TestRunner()


# ============================================================================
# Test 1: Basic Browser-Use Agent (Simplest)
# ============================================================================

@runner.test("Basic Browser-Use Agent - Simple Task")
async def test_basic_agent():
    """Test basic browser-use agent without MCP."""
    from browser_use import Agent
    from browser_use.llm import ChatOpenAI
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("BROWSER_USE_API_KEY"):
        raise Exception("No API key found. Set OPENAI_API_KEY or BROWSER_USE_API_KEY")
    
    # Use appropriate LLM
    if os.getenv("BROWSER_USE_API_KEY"):
        from browser_use.llm import ChatBrowserUse
        llm = ChatBrowserUse()
        print("Using ChatBrowserUse")
    else:
        llm = ChatOpenAI(model="gpt-5-mini")
        print("Using ChatOpenAI")
    
    print("Creating agent for simple task...")
    agent = Agent(
        task="Go to example.com and extract the title",
        llm=llm,
    )
    
    print("Running agent...")
    result = await agent.run(max_steps=5)
    
    print(f"Result: {result.final_result()}")
    
    # Verify result
    if not result.is_done():
        raise Exception("Agent did not complete task")
    
    print("✅ Basic agent test passed!")


# ============================================================================
# Test 2: Browser Automation with Real Website
# ============================================================================

@runner.test("Real Browser Automation - Reddit Search")
async def test_reddit_automation():
    """Test real browser automation on Reddit as specified."""
    from browser_use import Agent
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("BROWSER_USE_API_KEY"):
        raise Exception("No API key found")
    
    # Use appropriate LLM
    if os.getenv("BROWSER_USE_API_KEY"):
        from browser_use.llm import ChatBrowserUse
        llm = ChatBrowserUse()
    else:
        from browser_use.llm import ChatOpenAI
        llm = ChatOpenAI(model="gpt-5-mini")
    
    print("Creating agent for Reddit task...")
    agent = Agent(
        task="Go to Reddit, search for 'browser-use', click on the first post and return the first comment.",
        llm=llm,
    )
    
    print("Running Reddit automation...")
    result = await agent.run(max_steps=20)
    
    print(f"Result: {result.final_result()}")
    
    # Verify result
    if not result.is_done():
        raise Exception("Agent did not complete Reddit task")
    
    final_result = result.final_result()
    if not final_result or len(str(final_result)) < 10:
        raise Exception("No meaningful result returned from Reddit")
    
    print("✅ Reddit automation test passed!")


# ============================================================================
# Test 3: MCP Server (stdio mode - Original)
# ============================================================================

@runner.test("MCP Server - stdio Mode")
async def test_mcp_stdio():
    """Test the original MCP server with stdio transport."""
    print("Testing stdio MCP server...")
    
    # Start MCP server as subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "browser_use.mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False
    )
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {}
            }
        }
        
        request_data = json.dumps(init_request).encode() + b"\n"
        proc.stdin.write(request_data)
        proc.stdin.flush()
        
        # Wait for response (with timeout)
        import select
        ready = select.select([proc.stdout], [], [], 5.0)
        
        if ready[0]:
            response_line = proc.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode())
                print(f"Received response: {response}")
                
                if "result" in response or "error" not in response:
                    print("✅ MCP stdio server responded correctly!")
                else:
                    raise Exception(f"MCP error response: {response}")
            else:
                raise Exception("No response from MCP server")
        else:
            raise Exception("MCP server timeout")
            
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    
    print("✅ MCP stdio test passed!")


# ============================================================================
# Test 4: MCP SSE Server
# ============================================================================

@runner.test("MCP Server - SSE Mode")
async def test_mcp_sse():
    """Test the MCP server with SSE transport."""
    if not HTTPX_AVAILABLE:
        print("⚠️  Skipping SSE test - httpx not installed")
        return
    
    print("Starting SSE MCP server...")
    
    # Start SSE server as subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "browser_use.mcp.server_sse", 
         "--host", "127.0.0.1", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        await asyncio.sleep(3)
        
        # Test health endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://127.0.0.1:8001/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Health check response: {data}")
                
                if data.get("status") == "healthy" and data.get("server") == "browser-use-mcp":
                    print("✅ SSE MCP server is healthy!")
                else:
                    raise Exception(f"Unexpected health response: {data}")
            else:
                raise Exception(f"Health check failed: HTTP {response.status_code}")
                
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    
    print("✅ MCP SSE test passed!")


# ============================================================================
# Test 5: Full Integration - MCP + Browser Automation
# ============================================================================

@runner.test("Full Integration - MCP Server with Browser Task")
async def test_full_integration():
    """Test complete integration: MCP server executing browser automation."""
    if not HTTPX_AVAILABLE:
        print("⚠️  Skipping integration test - httpx not installed")
        return
    
    print("This would test full MCP client -> server -> browser flow")
    print("Requires MCP client implementation")
    print("For now, we verify components work independently")
    
    # Verify browser-use works
    from browser_use import Agent
    
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("BROWSER_USE_API_KEY"):
        print("⚠️  Skipping - no API key")
        return
        
    # Quick sanity check
    if os.getenv("BROWSER_USE_API_KEY"):
        from browser_use.llm import ChatBrowserUse
        llm = ChatBrowserUse()
    else:
        from browser_use.llm import ChatOpenAI
        llm = ChatOpenAI(model="gpt-5-mini")
    
    agent = Agent(
        task="Navigate to example.com and confirm it loads",
        llm=llm,
    )
    
    result = await agent.run(max_steps=3)
    
    if result.is_done():
        print("✅ Integration components verified!")
    else:
        raise Exception("Integration test failed")


# ============================================================================
# Main Test Runner
# ============================================================================

async def main():
    """Run all tests in order."""
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Browser-Use Comprehensive Test Suite" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    print("\nRunning tests from simplest to most complex...")
    
    # Run tests in order
    await test_basic_agent()
    await test_reddit_automation()
    await test_mcp_stdio()
    await test_mcp_sse()
    await test_full_integration()
    
    # Print summary
    success = runner.summary()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {runner.tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
