#!/usr/bin/env python3
"""
Main entry point for the Coverage MCP Server
"""

import asyncio
import logging
from pathlib import Path

from server import CoverageMCPServer


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)

    # Use current directory as project root
    project_root = Path.cwd()

    server = CoverageMCPServer(project_root)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
