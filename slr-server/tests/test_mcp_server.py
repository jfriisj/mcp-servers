#!/usr/bin/env python3
"""
Test SLR MCP Server using proper MCP client protocol
"""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_slr_server():
    """Test the SLR MCP server using MCP client protocol"""
    print("🧪 Testing SLR MCP Server...")
    
    try:
        # Setup server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python",
            args=["start_server.py"],
            env=None
        )
        
        print("🔗 Connecting to SLR MCP server...")
        
        # Connect to server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected successfully!")
                
                # Test 1: List available tools
                print("\n🔧 Testing list_tools...")
                tools_response = await session.list_tools()
                tools = tools_response.tools
                print(f"📋 Found {len(tools)} tools")
                
                # Show first few tools
                for i, tool in enumerate(tools[:3]):
                    print(f"  {i+1}. {tool.name}: {tool.description}")
                
                # Test 2: Call a simple tool (create_slr_project)
                print("\n🏗️ Testing create_slr_project tool...")
                
                result = await session.call_tool(
                    "create_slr_project",
                    {
                        "title": "Test SLR Project",
                        "research_domain": "Software Engineering", 
                        "description": "A test project to verify MCP server functionality"
                    }
                )
                
                print("✅ Tool call successful!")
                
                # Display result
                if result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            print(f"📄 Result: {content.text[:200]}...")
                
                print("\n🎉 All tests passed! SLR MCP server is working correctly.")
                
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(test_slr_server())
    sys.exit(exit_code)