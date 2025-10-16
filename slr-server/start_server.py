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
        # Get database configuration from environment
        db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        
        if db_type == "postgresql":
            # PostgreSQL configuration from environment variables
            postgres_host = os.getenv("POSTGRES_HOST", "localhost")
            postgres_port = os.getenv("POSTGRES_PORT", "5432")
            postgres_db = os.getenv("POSTGRES_DB", "slr_database")
            postgres_user = os.getenv("POSTGRES_USER", "postgres")
            postgres_password = os.getenv("POSTGRES_PASSWORD", "")
            
            # Build connection string
            if postgres_password:
                connection_string = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
            else:
                connection_string = f"postgresql://{postgres_user}@{postgres_host}:{postgres_port}/{postgres_db}"
            
            # Override with DATABASE_URL if provided
            connection_string = os.getenv("DATABASE_URL", connection_string)
            
            print(f"🐘 Using PostgreSQL database: postgresql://{postgres_user}@{postgres_host}:{postgres_port}/{postgres_db}")
        else:
            # SQLite configuration (default)
            database_path = os.getenv("DATABASE_PATH")
            if not database_path:
                # Default to database directory
                database_dir = Path(__file__).parent / "database"
                database_dir.mkdir(exist_ok=True)
                database_path = str(database_dir / "slr_production.db")
            
            connection_string = database_path
            print(f"📂 Using SQLite database: {database_path}")
        
        # Initialize server with dynamic database configuration
        server = SLRMCPServer(connection_string=connection_string)
        
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