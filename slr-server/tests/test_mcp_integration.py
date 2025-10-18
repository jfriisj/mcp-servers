#!/usr/bin/env python3
"""
Test MCP server startup and tool registration
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_mcp_server():
    """Test MCP server initialization and tool listing"""
    print("=" * 80)
    print("TESTING: MCP Server and Tool Registration")
    print("=" * 80)
    print()
    
    try:
        print("1️⃣ Importing SLRMCPServer...")
        from src.main import SLRMCPServer
        print("✅ Import successful")
        print()
        
        print("2️⃣ Initializing server...")
        server = SLRMCPServer(database_path="database/slr_database.db")
        print("✅ Server initialized")
        print()
        
        print("3️⃣ Initializing dependencies...")
        await server._initialize_dependencies()
        print("✅ Dependencies initialized")
        print()
        
        print("4️⃣ Listing available tools...")
        # Get the list_tools handler
        tools = None
        for item in dir(server.server):
            if 'list_tools' in item.lower():
                print(f"   Found method: {item}")
        
        # Try to get tools through the MCP handler
        if hasattr(server, 'mcp_handler'):
            tools = server.mcp_handler.get_tools()
            print(f"✅ Found {len(tools)} tools via mcp_handler")
        elif hasattr(server, '_tools'):
            tools = server._tools
            print(f"✅ Found {len(tools)} tools via _tools")
        print()
        
        if tools:
            print("5️⃣ Searching for create_slr_project tool...")
            project_tool = None
            for tool in tools:
                if hasattr(tool, 'name') and tool.name == 'create_slr_project':
                    project_tool = tool
                    break
            
            if project_tool:
                print("✅ Found create_slr_project tool!")
                print(f"   Name: {project_tool.name}")
                print(f"   Description: {project_tool.description}")
                if hasattr(project_tool, 'inputSchema'):
                    schema = project_tool.inputSchema
                    if 'properties' in schema:
                        print(f"   Parameters:")
                        for param, details in schema['properties'].items():
                            required = param in schema.get('required', [])
                            req_str = " (required)" if required else ""
                            print(f"     - {param}{req_str}: {details.get('description', 'N/A')}")
                print()
                return True
            else:
                print("❌ create_slr_project tool NOT found")
                print("   Available tools:")
                for tool in tools[:10]:
                    if hasattr(tool, 'name'):
                        print(f"     - {tool.name}")
                return False
        else:
            print("❌ No tools found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    print()
    if success:
        print("=" * 80)
        print("✅ MCP SERVER TEST PASSED")
        print("=" * 80)
        print()
        print("The create_slr_project tool is properly registered and ready to use!")
        print("You can now use it via:")
        print("  - Claude Desktop (with MCP configuration)")
        print("  - VS Code (with MCP extension)")
    else:
        print("=" * 80)
        print("❌ MCP SERVER TEST FAILED")
        print("=" * 80)
    
    sys.exit(0 if success else 1)
