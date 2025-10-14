#!/usr/bin/env python3
"""
Basic test script to verify SLR MCP Server initializes correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import SLRMCPServer

async def test_basic_server():
    """Test that server initializes properly."""
    try:
        # Initialize server
        print("🚀 Initializing SLR MCP Server...")
        server = SLRMCPServer()
        
        # Initialize dependencies
        print("⚙️ Initializing dependencies...")
        await server._initialize_dependencies()
        
        print("✅ Server initialization successful")
        
        # Check basic handler availability
        print("\n📋 Basic handler check:")
        handler = server.mcp_handler
        print(f"✅ MCP Handler initialized: {handler is not None}")
        
        print("\n🎉 Basic server verification complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic_server())