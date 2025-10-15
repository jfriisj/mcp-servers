#!/usr/bin/env python3
"""
Test server startup to see detailed logs
"""
import asyncio
import sys
import traceback
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_server_startup():
    """Test server startup for a few seconds"""
    print("🔍 Testing SLR MCP Server startup...")
    
    try:
        from src.main import SLRMCPServer
        
        print("📡 Creating and running server...")
        server = SLRMCPServer(database_path="test_startup.db")
        
        # Run server for a short time to see if it starts properly
        startup_task = asyncio.create_task(server.run())
        
        # Wait a bit to see if it starts without errors
        print("⏳ Waiting 3 seconds to check server startup...")
        await asyncio.sleep(3)
        
        # If we get here, server started successfully
        print("✅ Server started successfully and is running!")
        
        # Cancel the server task
        startup_task.cancel()
        
        try:
            await startup_task
        except asyncio.CancelledError:
            print("🛑 Server task cancelled cleanly")
        
        return 0
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_server_startup())
    sys.exit(exit_code)