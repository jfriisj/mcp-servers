#!/usr/bin/env python3
"""
Basic initialization test for SLR MCP Server
Tests just the initialization without MCP protocol
"""
import asyncio
import sys
import traceback
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path for imports
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

async def test_initialization():
    """Test basic server initialization"""
    print("🔍 Testing SLR MCP Server initialization...")
    
    try:
        # Test 1: Import the server class
        print("1️⃣ Testing imports...")
        from src.main import SLRMCPServer
        print("✅ SLRMCPServer imported successfully")
        
        # Test 2: Create server instance
        print("2️⃣ Creating server instance...")
        server = SLRMCPServer(database_path="test_init.db")
        print("✅ Server instance created successfully")
        
        # Test 3: Initialize dependencies
        print("3️⃣ Initializing dependencies...")
        await server._initialize_dependencies()
        print("✅ Dependencies initialized successfully")
        
        # Test 4: Check if handler is created
        print("4️⃣ Checking MCP handler...")
        if server.mcp_handler is None:
            print("❌ MCP handler is None")
            return 1
        print("✅ MCP handler created successfully")
        
        # Test 5: Check container
        print("5️⃣ Checking container...")
        if server.container is None:
            print("❌ Container is None")
            return 1
        print("✅ Container initialized successfully")
        
        print("\n🎉 All initialization tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_initialization())
    sys.exit(exit_code)