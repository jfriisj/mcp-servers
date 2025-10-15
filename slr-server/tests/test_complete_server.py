#!/usr/bin/env python3
"""
Test SLR MCP Server Tools

Quick test to verify all 23 tools are accessible and working.
"""

import asyncio
import json
import subprocess
import sys
import os


async def test_slr_tools():
    """Test SLR server tools via MCP protocol."""
    print("🧪 Testing SLR MCP Server Tools")
    print("=" * 50)
    
    # Start the SLR server process
    server_process = subprocess.Popen(
        [sys.executable, "start_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    try:
        # Send initialization message
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        print("📡 Sending initialization...")
        server_process.stdin.write(json.dumps(init_msg) + "\n")
        server_process.stdin.flush()
        
        # Read response
        response = server_process.stdout.readline()
        if response:
            print(f"✅ Init response: {response.strip()}")
        
        # Send tools/list request
        list_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("📋 Requesting tool list...")
        server_process.stdin.write(json.dumps(list_msg) + "\n")
        server_process.stdin.flush()
        
        # Read response
        response = server_process.stdout.readline()
        if response:
            try:
                data = json.loads(response)
                tools = data.get("result", {}).get("tools", [])
                print(f"🎯 Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i:2d}. {tool['name']}")
                
                if len(tools) == 23:
                    print(f"\n✅ SUCCESS: All 23 tools are registered!")
                else:
                    print(f"\n⚠️  WARNING: Expected 23 tools, found {len(tools)}")
                    
            except json.JSONDecodeError:
                print(f"❌ Failed to parse response: {response}")
        
        # Test a simple tool call
        print("\n🧪 Testing upload_paper tool...")
        test_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "upload_paper",
                "arguments": {
                    "file_path": "/tmp/test.pdf",
                    "title": "Test Paper"
                }
            }
        }
        
        server_process.stdin.write(json.dumps(test_msg) + "\n")
        server_process.stdin.flush()
        
        # Read response
        response = server_process.stdout.readline()
        if response:
            print(f"📄 Tool response: {response.strip()}")
        
        print("\n✅ SLR MCP Server test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Clean up
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()


if __name__ == "__main__":
    asyncio.run(test_slr_tools())