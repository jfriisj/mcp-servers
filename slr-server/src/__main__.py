"""
Entry point for running the SLR MCP Server as a module.

Usage:
    python -m slr_server
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())