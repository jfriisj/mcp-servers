#!/usr/bin/env python3
"""
SLR MCP Server Startup Script

Production server for systematic literature review MCP operations.
Initializes the server with proper database schema and configuration.

Usage: python start_server.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import SLRMCPServer


async def main():
    """Start the SLR MCP server with MCP stdio transport."""
    print("🚀 Starting SLR MCP Server...")
    
    try:
        # Get database path from environment or use default
        database_path = os.getenv("DATABASE_PATH")
        if not database_path:
            # Default to database directory with corrected schema
            database_dir = Path(__file__).parent / "database"
            database_dir.mkdir(exist_ok=True)
            database_path = str(database_dir / "slr_production.db")
        
        print(f"📂 Using database: {database_path}")
        
        # Initialize server with dynamic database path
        server = SLRMCPServer(database_path=database_path)
        
        print("✅ SLR MCP Server created")
        print("📡 Starting server with MCP stdio transport...")
        
        # Run the server (this will handle MCP protocol via stdio)
        await server.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  Server shutdown requested")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 SLR MCP Server stopped")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))