#!/usr/bin/env python3
"""
Quick MCP Validation Script
Validates that MCP servers are working properly
"""
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

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


def print_status(test, status, details=""):
    """Print test status"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {test:<40} {details}")


async def validate_mcp():
    """Validate MCP functionality"""
    print("\n" + "="*70)
    print("  Browser-Use MCP Validation")
    print("="*70 + "\n")
    
    results = []
    
    # Test 1: MCP stdio server
    print("Testing MCP stdio server...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "browser_use.mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send initialize
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
        await asyncio.sleep(2)
        
        proc.terminate()
        proc.wait(timeout=5)
        
        print_status("MCP stdio server", True, "Started and responded")
        results.append(True)
    except Exception as e:
        print_status("MCP stdio server", False, str(e))
        results.append(False)
    
    # Test 2: MCP SSE server health
    if HTTPX_AVAILABLE:
        print("\nTesting MCP SSE server...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "browser_use.mcp.server_sse",
                 "--host", "127.0.0.1", "--port", "8005"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            await asyncio.sleep(3)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://127.0.0.1:8005/health")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        print_status("MCP SSE health endpoint", True, f"v{data.get('version')}")
                        results.append(True)
                    else:
                        print_status("MCP SSE health endpoint", False, "Unhealthy")
                        results.append(False)
                else:
                    print_status("MCP SSE health endpoint", False, f"HTTP {response.status_code}")
                    results.append(False)
            
            # Test SSE connection
            async with httpx.AsyncClient(timeout=10.0) as client:
                async with client.stream("GET", "http://127.0.0.1:8005/sse") as response:
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "text/event-stream" in content_type:
                            print_status("MCP SSE stream endpoint", True, "SSE available")
                            results.append(True)
                        else:
                            print_status("MCP SSE stream endpoint", False, f"Wrong type: {content_type}")
                            results.append(False)
                    else:
                        print_status("MCP SSE stream endpoint", False, f"HTTP {response.status_code}")
                        results.append(False)
            
            proc.terminate()
            
        except Exception as e:
            print_status("MCP SSE server", False, str(e))
            results.append(False)
            if 'proc' in locals():
                proc.terminate()
    else:
        print("\n⚠️  httpx not installed, skipping SSE tests")
        print("   Install with: pip install httpx")
    
    # Test 3: Docker container
    print("\nTesting Docker container...")
    try:
        # Check if docker is available
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Try to check if our container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=browser-use-mcp", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "browser-use-mcp" in result.stdout:
                print_status("Docker container", True, "Running")
                results.append(True)
            else:
                print_status("Docker container", False, "Not running (start with docker-compose up)")
                results.append(False)
        else:
            print_status("Docker", False, "Docker not available")
            results.append(False)
            
    except Exception as e:
        print_status("Docker", False, str(e))
        results.append(False)
    
    # Summary
    print("\n" + "="*70)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed - MCP is fully functional!")
    elif passed > total / 2:
        print(f"⚠️  {passed}/{total} tests passed - MCP is mostly functional")
    else:
        print(f"❌ Only {passed}/{total} tests passed - MCP needs attention")
    
    print("="*70 + "\n")
    
    return passed == total


async def main():
    """Main entry point"""
    try:
        success = await validate_mcp()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
