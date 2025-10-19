#!/usr/bin/env python3
"""
Test MCP handlers directly to isolate connection issues
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path for imports
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

async def test_mcp_handlers():
    """Test MCP handlers directly"""
    print("🔍 Testing MCP handlers directly...")
    
    try:
        from src.main import SLRMCPServer
        
        # Create and initialize server
        print("1️⃣ Creating server...")
        server = SLRMCPServer(database_path="test_handlers.db")
        await server._initialize_dependencies()
        print("✅ Server initialized")
        
        # Test the list_tools handler directly
        print("2️⃣ Testing list_tools handler...")
        
        # Get the registered list_tools handler
        list_tools_handlers = [handler for handler in server.server._handlers if handler.__name__ == 'handle_list_tools']
        if not list_tools_handlers:
            print("❌ No list_tools handler found")
            return 1
            
        list_tools_handler = list_tools_handlers[0]
        print("✅ Found list_tools handler")
        
        # Call the handler
        print("3️⃣ Calling list_tools handler...")
        tools = await list_tools_handler()
        print(f"✅ Got {len(tools)} tools")
        
        # Print first few tools
        for i, tool in enumerate(tools[:3]):
            print(f"   {i+1}. {tool.name}: {tool.description}")
        
        # Test tool calling handler
        print("4️⃣ Testing call_tool handler...")
        
        call_tool_handlers = [handler for handler in server.server._handlers if handler.__name__ == 'handle_call_tool']
        if not call_tool_handlers:
            print("❌ No call_tool handler found")
            return 1
            
        call_tool_handler = call_tool_handlers[0]
        print("✅ Found call_tool handler")
        
        # Try calling a simple tool
        print("5️⃣ Testing create_slr_project tool call...")
        result = await call_tool_handler(
            "create_slr_project", 
            {
                "title": "Test Project",
                "research_domain": "Software Engineering"
            }
        )
        print("✅ Tool call successful")
        print(f"   Result type: {type(result)}")
        if result:
            print(f"   Result length: {len(result)}")
            if hasattr(result[0], 'text'):
                print(f"   Result preview: {result[0].text[:100]}...")
        
        print("\n🎉 All handler tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_mcp_handlers())
    sys.exit(exit_code)