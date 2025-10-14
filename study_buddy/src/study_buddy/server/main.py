#!/usr/bin/env python3
"""
Study Buddy MCP Server - Main Entry Point

A Model Context Protocol server for document processing and analysis.
Provides tools for uploading, parsing, chunking, and managing documents.

This is the single canonical entry point for the MCP server.
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path


def setup_python_path() -> None:
    """Setup Python path for reliable imports."""
    # Get absolute path to this script
    script_path = Path(__file__).resolve()
    
    # Calculate paths
    server_dir = script_path.parent                    # .../server/
    study_buddy_dir = server_dir.parent                # .../study_buddy/
    src_dir = study_buddy_dir.parent                   # .../src/
    project_root = src_dir.parent                      # project root
    
    # Add paths to sys.path if not already present
    paths_to_add = [str(src_dir), str(project_root)]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)


async def main() -> None:
    """Main entry point for the Study Buddy MCP Server."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Study Buddy MCP Server - Document processing and analysis"
    )
    parser.add_argument(
        "--database-path",
        type=str,
        help="Path to SQLite database file (overrides environment variable)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (don't start MCP server, just verify setup)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Study Buddy MCP Server")
    
    # Setup Python path for imports
    setup_python_path()
    
    try:
        # Import the main server implementation
        logger.info("🔧 Loading Study Buddy MCP Server...")
        
        from study_buddy.server.server import StudyBuddyMCPServer
        
        # Determine database path: CLI arg > env var > default
        database_path = args.database_path or os.getenv("STUDY_BUDDY_DB_PATH")
        
        # Create server instance
        server = StudyBuddyMCPServer(database_path)
        
        if args.test:
            logger.info("🧪 Running in test mode - verifying server setup")
            
            # Test initialization
            await server._initialize_dependencies()
            
            logger.info("✅ Test mode completed successfully")
            return
        
        logger.info("✅ Study Buddy MCP Server ready - starting stdio communication")
        
        # Start the MCP server
        await server.run()
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Check Python path and module structure")
        raise
        
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
        
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
        
    finally:
        logger.info("✅ Study Buddy MCP Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())