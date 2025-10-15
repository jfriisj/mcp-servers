#!/usr/bin/env python3
"""
List All SLR MCP Server Tools

This script connects to the SLR MCP Server and displays all available tools
with their descriptions and parameters.

Run with: python list_slr_tools.py
"""

import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def list_all_slr_tools():
    """List all available tools on the SLR MCP Server"""
    print("🔍 SLR MCP Server - Complete Tool Listing")
    print("=" * 50)
    
    server_params = StdioServerParameters(
        command='python',
        args=['-m', 'src.main'],
        cwd=str(Path.cwd())
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("✅ Connected to SLR MCP Server")
                print("\n📋 Available Tools:")
                print("-" * 50)
                
                tools_result = await session.list_tools()
                
                for i, tool in enumerate(tools_result.tools, 1):
                    print(f"\n{i}. **{tool.name}**")
                    print(f"   Description: {tool.description}")
                    
                    # Show input schema if available
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        schema = tool.inputSchema
                        if 'properties' in schema:
                            print("   Parameters:")
                            for param_name, param_info in schema['properties'].items():
                                param_type = param_info.get('type', 'unknown')
                                description = param_info.get('description', 'No description')
                                required = param_name in schema.get('required', [])
                                req_marker = " (required)" if required else " (optional)"
                                print(f"     - {param_name}: {param_type}{req_marker}")
                                print(f"       {description}")
                
                print("\n" + "=" * 50)
                print(f"🎯 Total: {len(tools_result.tools)} tools available")
                print("✅ All tools listed successfully!")
                
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")


if __name__ == "__main__":
    asyncio.run(list_all_slr_tools())