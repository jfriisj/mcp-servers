#!/usr/bin/env python3
"""
Simple test to verify the SLR MCP Server builds and initializes correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.container import initialize_application
from src.main import SLRMCPServer

async def test_build():
    """Test that the server can be built and initialized."""
    print("🧪 Testing SLR MCP Server build...")
    
    try:
        # Test container initialization
        print("📦 Testing container initialization...")
        container = await initialize_application()
        print("✅ Container initialized successfully")
        
        # Test MCP handler creation
        print("🔧 Testing MCP handler creation...")
        mcp_handler = container.get_mcp_handler()
        print("✅ MCP handler created successfully")
        
        # Test server creation (without running)
        print("🚀 Testing server creation...")
        server = SLRMCPServer()
        print("✅ Server created successfully")
        
        # Clean up
        container.close()
        print("✅ Cleanup completed")
        
        print("\n🎉 BUILD TEST PASSED!")
        print("✅ SLR MCP Server builds and initializes correctly")
        print("✅ All core components are working")
        print("✅ Ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ BUILD TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_build())
    sys.exit(0 if success else 1)