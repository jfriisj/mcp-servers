"""
Main MCP server implementation for the Hadolint MCP Server
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from hadolint_runner import HadolintRunner
from mcp_handler import MCPHandler
from models import RulesConfig

logger = logging.getLogger(__name__)


class HadolintMCPServer:
    """Main MCP server for hadolint operations"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.server = Server("hadolint-mcp-server")
        self.hadolint_runner = HadolintRunner(self.project_root)
        self.mcp_handler = MCPHandler(self.hadolint_runner)

    async def list_resources(self) -> List[Resource]:
        """List available resources"""
        return [
            Resource(
                uri=AnyUrl("hadolint://rules"),
                name="Hadolint Rules",
                description="Available hadolint linting rules",
                mimeType="text/plain",
            ),
        ]

    async def read_resource(self, uri: AnyUrl) -> str:
        """Read a resource"""
        if str(uri) == "hadolint://rules":
            # Get hadolint rules information
            result = await self.hadolint_runner.show_rules(
                RulesConfig(format="tty", show_all=False)
            )
            if result.success:
                return result.output
            else:
                return f"Failed to get hadolint rules:\n{result.error}"
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def list_tools(self) -> List[Tool]:
        """List available tools"""
        return self.mcp_handler.get_tools()

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Call a tool"""
        return await self.mcp_handler.call_tool(name, arguments)

    async def serve(self) -> None:
        """Start the MCP server"""
        logger.info("Starting Hadolint MCP Server")

        @self.server.list_resources()
        async def handle_list_resources():
            return await self.list_resources()

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl):
            return await self.read_resource(uri)

        @self.server.list_tools()
        async def handle_list_tools():
            return await self.list_tools()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            return await self.call_tool(name, arguments)

        # Run the server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    server = HadolintMCPServer()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
