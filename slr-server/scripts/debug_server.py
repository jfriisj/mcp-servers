#!/usr/bin/env python3
"""
Debug server startup issues
"""
import asyncio
import sys
import traceback

async def debug_server():
    """Debug server startup with proper async handling"""
    try:
        print("🔍 Debugging server startup...")
        
        # Try importing the main server module
        from src.main import main
        print("✅ Successfully imported main module")
        
        # Try running the main function (properly awaited)
        print("🚀 Attempting to start server...")
        await main()
        
    except Exception as e:
        print(f"❌ Error during server startup: {e}")
        print(f"📋 Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(debug_server())
