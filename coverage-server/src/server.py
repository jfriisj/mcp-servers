"""
Main MCP server implementation for the Coverage MCP Server
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from config import ConfigurationManager
from coverage_runner import CoverageRunner
from coverage_reporter import CoverageReporter
from coverage_analyzer import CoverageAnalyzer
from mcp_handler import MCPHandler

logger = logging.getLogger(__name__)


class CoverageMCPServer:
    """Main MCP server for coverage operations"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.server = Server("coverage-mcp-server")
        self.config_manager = ConfigurationManager()
        self.coverage_runner = CoverageRunner(self.project_root, self.config_manager)
        self.coverage_reporter = CoverageReporter(
            self.coverage_runner, self.project_root
        )
        self.coverage_analyzer = CoverageAnalyzer()
        self.mcp_handler = MCPHandler(
            self.coverage_runner, self.coverage_reporter, self.coverage_analyzer
        )

    async def list_resources(self) -> List[Resource]:
        """List available resources"""
        return [
            Resource(
                uri=AnyUrl("coverage://current"),
                name="Current Coverage Report",
                description="Current test coverage report",
                mimeType="text/plain",
            ),
            Resource(
                uri=AnyUrl("coverage://summary"),
                name="Coverage Summary",
                description="Summary of coverage metrics",
                mimeType="text/plain",
            ),
        ]

    async def read_resource(self, uri: AnyUrl) -> str:
        """Read a resource"""
        if str(uri) == "coverage://current":
            # Get current coverage report
            cmd = ["coverage", "report", "--show-missing"]
            output, _, returncode = await self.coverage_runner.run_coverage_command(cmd)
            if returncode == 0:
                return output
            else:
                return f"Failed to get coverage report:\n{output}"
        elif str(uri) == "coverage://summary":
            # Get coverage summary
            cmd = ["coverage", "report"]
            output, _, returncode = await self.coverage_runner.run_coverage_command(cmd)
            if returncode == 0:
                total_coverage = self.coverage_analyzer.parse_coverage_percentage(
                    output
                )
                if total_coverage:
                    return f"Total Coverage: {total_coverage:.1f}%"
                else:
                    return "Unable to parse coverage"
            else:
                return f"Failed to get coverage summary:\n{output}"
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
        logger.info("Starting Coverage MCP Server")

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
    server = CoverageMCPServer()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
