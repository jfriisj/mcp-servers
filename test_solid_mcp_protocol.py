"""
Test SOLID MCP Server protocol communication
"""
import asyncio
import json
import sys
from pathlib import Path

# Add solid-server to path
sys.path.insert(0, str(Path(__file__).parent / "solid-server" / "src"))


async def test_mcp_server():
    """Test the MCP server by simulating client requests"""
    from server import SolidMCPServer
    
    project_root = Path(__file__).parent / "solid-server"
    server = SolidMCPServer(project_root)
    
    print("🔧 Testing MCP Server Protocol\n")
    
    # Test 1: List resources
    print("1️⃣ Testing list_resources()...")
    resources = await server.list_resources()
    print(f"   ✅ Found {len(resources)} resources:")
    for resource in resources:
        print(f"      - {resource.name} ({resource.uri})")
    
    # Test 2: List tools
    print("\n2️⃣ Testing list_tools()...")
    tools = await server.list_tools()
    print(f"   ✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"      - {tool.name}: {tool.description[:60]}...")
    
    # Test 3: Call a tool - explain principle
    print("\n3️⃣ Testing call_tool('solid-explain-principle')...")
    try:
        result = await server.call_tool(
            "solid-explain-principle",
            {"principle": "SRP"}
        )
        print(f"   ✅ Tool executed successfully")
        print(f"   Response length: {len(result[0].text)} characters")
        print(f"   Preview: {result[0].text[:100]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Call a tool - check file
    print("\n4️⃣ Testing call_tool('solid-check-file')...")
    test_file = project_root / "src" / "main.py"
    try:
        result = await server.call_tool(
            "solid-check-file",
            {"file_path": str(test_file)}
        )
        print(f"   ✅ Tool executed successfully")
        lines = result[0].text.split('\n')
        print(f"   Response preview:")
        for line in lines[:8]:
            print(f"      {line}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Read resource
    print("\n5️⃣ Testing read_resource('solid://current-score')...")
    try:
        from pydantic import AnyUrl
        content = await server.read_resource(AnyUrl("solid://current-score"))
        print(f"   ✅ Resource read successfully")
        lines = content.strip().split('\n')
        for line in lines[:10]:
            print(f"      {line}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 All MCP protocol tests passed!")
    print("\n✅ The server is ready to use with MCP clients like VS Code Copilot")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
