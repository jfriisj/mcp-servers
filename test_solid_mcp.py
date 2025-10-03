"""
Test script to verify SOLID MCP server is working
"""

import sys
import os

# Add solid-server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'solid-server', 'src'))

try:
    # Test imports
    from server import SolidMCPServer
    from mcp_handler import MCPHandler
    from solid_analyzer import SolidAnalyzer
    
    print("✅ All imports successful!")
    
    # Test creating server instance
    from pathlib import Path
    project_root = Path(__file__).parent / "solid-server"
    
    server = SolidMCPServer(project_root)
    print(f"✅ Server instance created with project root: {project_root}")
    
    # Test getting tools
    tools = server.mcp_handler.get_tools()
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool.name}")
    
    print("\n🎉 SOLID MCP Server is properly configured!")
    print("\nTo use with VS Code Copilot:")
    print("1. Make sure the .vscode/mcp.json configuration is correct")
    print("2. Reload VS Code window (Ctrl+Shift+P -> Reload Window)")
    print("3. Check the MCP logs in Output panel (View -> Output -> MCP)")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have installed the requirements:")
    print("   pip install -r solid-server/requirements.txt")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
