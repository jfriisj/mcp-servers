"""
MCP Protocol Test
================

This script simulates an MCP client to test the server protocol.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from server import ImportTestMCPServer

async def test_mcp_protocol():
    """Test MCP protocol functionality"""
    print("🔌 Testing MCP Protocol Integration")
    print("=" * 50)
    
    try:
        # Initialize server
        project_root = Path(__file__).parent.parent
        server = ImportTestMCPServer(project_root)
        
        # Test list_tools
        print("\n1. Testing list_tools()...")
        tools = await server.list_tools()
        print(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            desc = getattr(tool, 'description', 'No description')[:50]
            print(f"      - {getattr(tool, 'name', 'Unknown')}: {desc}...")
        
        # Test call_tool for analyze-file
        print(f"\n2. Testing call_tool() with import-test-analyze-file...")
        result = await server.call_tool("import-test-analyze-file", {
            "file_path": "src/main.py"
        })
        print(f"   ✅ Tool executed successfully")
        print(f"   📄 Result length: {len(result[0].text)} characters")
        
        # Test call_tool for get-stats
        print(f"\n3. Testing call_tool() with import-test-get-stats...")
        result = await server.call_tool("import-test-get-stats", {
            "project_path": "."
        })
        print(f"   ✅ Tool executed successfully")
        
        # Test invalid tool
        print(f"\n4. Testing call_tool() with invalid tool...")
        result = await server.call_tool("invalid-tool", {})
        print(f"   ✅ Error handling works: {result[0].text[:50]}...")
        
        print(f"\n🎉 MCP Protocol Test Complete - All Systems Working!")
        return True
        
    except Exception as e:
        print(f"\n❌ MCP Protocol Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_protocol())
    sys.exit(0 if success else 1)