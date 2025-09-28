#!/usr/bin/env python3
"""
Main entry point for the Hadolint MCP Server
"""

import asyncio
import logging
from pathlib import Path

from server import HadolintMCPServer


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)

    # Use current directory as project root
    project_root = Path.cwd()

    server = HadolintMCPServer(project_root)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
