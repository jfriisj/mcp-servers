#!/usr/bin/env python3
"""
Test dependency tree tool via MCP interface
"""

import asyncio
import json
from pathlib import Path
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server import ImportTestMCPServer

async def test_dependency_tree_mcp():
    """Test dependency tree tool via MCP server"""
    
    # Create server
    project_root = Path("C:/github/mcp-servers/import-test-server")
    server_instance = ImportTestMCPServer(project_root)
    
    print("🌳 Testing Dependency Tree via MCP Interface")
    print("=" * 60)
    
    # Test the tool
    arguments = {
        "project_path": "C:/github/mcp-servers/solid-server/src",
        "format": "text",
        "max_depth": 3,
        "include_external": False
    }
    
    try:
        result = await server_instance.mcp_handler.call_tool(
            "import-test-dependency-tree", 
            arguments
        )
        
        print("✅ Tool executed successfully!")
        print("\n📊 Result:")
        print("-" * 40)
        print(result[0].text)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n🔧 Testing Mermaid format:")
    print("-" * 40)
    
    arguments["format"] = "mermaid"
    arguments["max_depth"] = 2
    
    try:
        result = await server_instance.mcp_handler.call_tool(
            "import-test-dependency-tree", 
            arguments
        )
        
        print("✅ Mermaid format test successful!")
        print("\n📊 Mermaid Result (truncated):")
        print("-" * 40)
        mermaid_output = result[0].text
        lines = mermaid_output.split('\n')
        # Show first 20 lines of mermaid output
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print("... (truncated)")
            print(f"Total lines: {len(lines)}")
        
    except Exception as e:
        print(f"❌ Mermaid test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dependency_tree_mcp())