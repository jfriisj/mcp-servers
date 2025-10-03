"""
Test the new SOLID MCP server tools
"""
import asyncio
import sys
from pathlib import Path

# Add solid-server to path
sys.path.insert(0, str(Path(__file__).parent / "solid-server" / "src"))

from mcp_handler import MCPHandler


async def test_suggest_refactoring():
    """Test the solid-suggest-refactoring tool"""
    print("\n" + "=" * 60)
    print("Testing solid-suggest-refactoring")
    print("=" * 60)
    
    handler = MCPHandler(Path(__file__).parent / "solid-server")
    
    # Test on the solid-server directory
    result = await handler.call_tool(
        "solid-suggest-refactoring",
        {
            "path": str(Path(__file__).parent / "solid-server" / "src"),
            "max_suggestions": 5,
            "priority": "all"
        }
    )
    
    print(result[0].text)


async def test_dependency_graph():
    """Test the solid-dependency-graph tool"""
    print("\n" + "=" * 60)
    print("Testing solid-dependency-graph (text format)")
    print("=" * 60)
    
    handler = MCPHandler(Path(__file__).parent / "solid-server")
    
    # Test on the solid-server directory
    result = await handler.call_tool(
        "solid-dependency-graph",
        {
            "path": str(Path(__file__).parent / "solid-server" / "src"),
            "format": "text",
            "include_methods": True
        }
    )
    
    print(result[0].text)
    
    print("\n" + "=" * 60)
    print("Testing solid-dependency-graph (mermaid format)")
    print("=" * 60)
    
    # Test mermaid format
    result = await handler.call_tool(
        "solid-dependency-graph",
        {
            "path": str(Path(__file__).parent / "solid-server" / "src"),
            "format": "mermaid",
            "include_methods": False
        }
    )
    
    print(result[0].text)


async def test_analyze_inheritance():
    """Test the solid-analyze-inheritance tool"""
    print("\n" + "=" * 60)
    print("Testing solid-analyze-inheritance")
    print("=" * 60)
    
    handler = MCPHandler(Path(__file__).parent / "solid-server")
    
    # Test on the solid-server directory
    result = await handler.call_tool(
        "solid-analyze-inheritance",
        {
            "path": str(Path(__file__).parent / "solid-server" / "src"),
            "max_depth": 5,
            "include_methods": True
        }
    )
    
    print(result[0].text)


async def main():
    """Run all tests"""
    print("Testing new SOLID MCP server tools...")
    
    try:
        await test_suggest_refactoring()
        await test_dependency_graph()
        await test_analyze_inheritance()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
