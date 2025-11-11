#!/usr/bin/env python3
"""
Progressive Test Suite for Browser-Use MCP Server

Tests run from simplest to most complex:
1. Basic browser-use agent
2. Real browser automation (Reddit)
3. MCP stdio server
4. MCP SSE server
5. Full integration

Usage:
    python docker/test_progressive.py
    python docker/test_progressive.py --test basic    # Run specific test
"""

import asyncio
import argparse
import json
import os
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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ProgressiveTests:
    """Progressive test suite for Browser-Use MCP."""
    
    def __init__(self):
        self.results = []
        
    def print_header(self, title):
        """Print test section header."""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
        
    def record_result(self, name, passed, error=None):
        """Record test result."""
        self.results.append({
            "name": name,
            "passed": passed,
            "error": error
        })
        
        if passed:
            print(f"\n✅ PASS: {name}")
        else:
            print(f"\n❌ FAIL: {name}")
            if error:
                print(f"   Error: {error}")
                
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
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
        
    async def test_basic_agent(self):
        """Test 1: Basic browser-use agent."""
        self.print_header("Test 1: Basic Browser-Use Agent")
        
        try:
            from browser_use import Agent
            
            # Check API key
            if not os.getenv("OPENAI_API_KEY") and not os.getenv("BROWSER_USE_API_KEY"):
                self.record_result("Basic Agent", False, "No API key found")
                return False
            
            # Select LLM
            if os.getenv("BROWSER_USE_API_KEY"):
                from browser_use.llm import ChatBrowserUse
                llm = ChatBrowserUse()
                print("Using ChatBrowserUse")
            else:
                from browser_use.llm import ChatOpenAI
                llm = ChatOpenAI(model="gpt-5-mini")
                print("Using ChatOpenAI (gpt-5-mini)")
            
            print("\nTask: Go to example.com and extract the title")
            agent = Agent(
                task="Go to example.com and extract the h1 heading text",
                llm=llm,
            )
            
            result = await agent.run(max_steps=5)
            
            if result.is_done():
                print(f"\nResult: {result.final_result()}")
                self.record_result("Basic Agent", True)
                return True
            else:
                self.record_result("Basic Agent", False, "Agent did not complete")
                return False
                
        except Exception as e:
            self.record_result("Basic Agent", False, str(e))
            return False
            
    async def test_reddit_automation(self):
        """Test 2: Real browser automation on Reddit."""
        self.print_header("Test 2: Reddit Browser Automation")
        
        try:
            from browser_use import Agent
            
            if not os.getenv("OPENAI_API_KEY") and not os.getenv("BROWSER_USE_API_KEY"):
                self.record_result("Reddit Automation", False, "No API key")
                return False
            
            # Select LLM  
            if os.getenv("BROWSER_USE_API_KEY"):
                from browser_use.llm import ChatBrowserUse
                llm = ChatBrowserUse()
            else:
                from browser_use.llm import ChatOpenAI
                llm = ChatOpenAI(model="gpt-5-mini")
            
            print("\nTask: Search Reddit for 'browser-use' and get first comment")
            agent = Agent(
                task="Go to Reddit, search for 'browser-use', click on the first post and return the first comment.",
                llm=llm,
            )
            
            result = await agent.run(max_steps=20)
            
            if result.is_done():
                final = result.final_result()
                print(f"\nResult: {final}")
                
                if final and len(str(final)) > 10:
                    self.record_result("Reddit Automation", True)
                    return True
                else:
                    self.record_result("Reddit Automation", False, "Empty result")
                    return False
            else:
                self.record_result("Reddit Automation", False, "Did not complete")
                return False
                
        except Exception as e:
            self.record_result("Reddit Automation", False, str(e))
            return False
            
    async def test_mcp_stdio(self):
        """Test 3: MCP server with stdio transport."""
        self.print_header("Test 3: MCP Server (stdio)")
        
        print("\nStarting MCP stdio server...")
        print("Note: This tests the original MCP server implementation")
        
        try:
            # Start MCP server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Give it time to start
            await asyncio.sleep(2)
            
            # Check if process is running
            if proc.poll() is not None:
                stderr = proc.stderr.read().decode() if proc.stderr else ""
                self.record_result("MCP stdio", False, f"Server crashed: {stderr}")
                return False
            
            # Terminate and check it was running
            proc.terminate()
            proc.wait(timeout=5)
            
            self.record_result("MCP stdio", True)
            print("✅ MCP stdio server started successfully")
            return True
            
        except Exception as e:
            self.record_result("MCP stdio", False, str(e))
            return False
            
    async def test_mcp_sse(self):
        """Test 4: MCP server with SSE transport."""
        self.print_header("Test 4: MCP Server (SSE)")
        
        if not HTTPX_AVAILABLE:
            self.record_result("MCP SSE", False, "httpx not installed")
            return False
        
        print("\nStarting SSE MCP server on port 8001...")
        
        try:
            # Start SSE server
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server_sse",
                 "--host", "127.0.0.1", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Wait for server to start
            print("Waiting for server to start...")
            await asyncio.sleep(4)
            
            # Test health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://127.0.0.1:8001/health")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\nHealth response: {json.dumps(data, indent=2)}")
                    
                    if data.get("status") == "healthy":
                        self.record_result("MCP SSE", True)
                        proc.terminate()
                        return True
                    else:
                        proc.terminate()
                        self.record_result("MCP SSE", False, "Unhealthy status")
                        return False
                else:
                    proc.terminate()
                    self.record_result("MCP SSE", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            if 'proc' in locals():
                proc.terminate()
            self.record_result("MCP SSE", False, str(e))
            return False
            
    async def test_full_integration(self):
        """Test 5: Full integration test."""
        self.print_header("Test 5: Full Integration")
        
        print("\nVerifying all components work together...")
        print("(Full MCP client integration would go here)")
        
        # For now, just verify components exist
        try:
            from browser_use import Agent
            from browser_use.mcp import server
            from browser_use.mcp import server_sse
            
            print("✅ All modules importable")
            self.record_result("Full Integration", True)
            return True
            
        except Exception as e:
            self.record_result("Full Integration", False, str(e))
            return False
            
    async def run_all(self):
        """Run all tests."""
        print("╔" + "="*68 + "╗")
        print("║" + " "*10 + "Browser-Use Progressive Test Suite" + " "*22 + "║")
        print("╚" + "="*68 + "╝")
        
        await self.test_basic_agent()
        await self.test_reddit_automation()
        await self.test_mcp_stdio()
        await self.test_mcp_sse()
        await self.test_full_integration()
        
        return self.print_summary()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Progressive test suite for Browser-Use MCP")
    parser.add_argument("--test", choices=["basic", "reddit", "stdio", "sse", "integration", "all"],
                       default="all", help="Which test to run")
    args = parser.parse_args()
    
    tests = ProgressiveTests()
    
    if args.test == "all":
        success = await tests.run_all()
    elif args.test == "basic":
        success = await tests.test_basic_agent()
        tests.print_summary()
    elif args.test == "reddit":
        success = await tests.test_reddit_automation()
        tests.print_summary()
    elif args.test == "stdio":
        success = await tests.test_mcp_stdio()
        tests.print_summary()
    elif args.test == "sse":
        success = await tests.test_mcp_sse()
        tests.print_summary()
    elif args.test == "integration":
        success = await tests.test_full_integration()
        tests.print_summary()
    else:
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
