"""
Entry point for Ruff MCP Server
===============================
Main application entry point with server initialization.
"""

import asyncio
import sys
from pathlib import Path

from server import RuffMCPServer


async def main():
    """Main entry point for the Ruff MCP server."""
    try:
        # Get project root from command line arguments
        project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

        # Create and run the service
        service = RuffMCPServer(project_root)
        await service.serve()

    except Exception as e:
        print(f"[ERROR] Ruff MCP server failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
