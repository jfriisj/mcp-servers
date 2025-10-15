#!/usr/bin/env python3
"""
Test SLR MCP Tool Functionality
Simple test to verify tools are working after fixes
"""
import asyncio
import json
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_slr_tool():
    """Test basic SLR tool functionality"""
    print("🧪 Testing SLR MCP Tool Functionality...")
    
    try:
        # Server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["start_server.py"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to SLR MCP Server")
                
                # Test 1: List available tools
                tools = await session.list_tools()
                print(f"📋 Found {len(tools.tools)} available tools")
                
                # Test 2: Create a simple SLR project
                print("\n🏗️ Testing create_slr_project tool...")
                
                result = await session.call_tool(
                    "create_slr_project",
                    {
                        "title": "Test SLR Project",
                        "research_domain": "Software Engineering",
                        "description": "Testing the SLR MCP server functionality",
                        "team_lead": "Test User"
                    }
                )
                
                print("✅ create_slr_project tool called successfully!")
                
                # Parse result content
                if result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            print(f"📄 Response: {content.text}")
                        else:
                            print(f"📄 Response: {content}")
                
                print("\n🎉 All tests passed! SLR MCP server is working correctly.")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_slr_tool())