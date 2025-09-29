"""Content Organization Server implementation.

This module provides the MCP server for content organization operations,
including course content organization, file reorganization, and cross-referencing.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

from .mcp_handlers.course_content_handler import CourseContentHandler
from .mcp_handlers.file_reorganization_handler import FileReorganizationHandler
from .mcp_handlers.cross_reference_handler import CrossReferenceHandler
from .mcp_handler import MCPHandler
from .models import ServerConfig

logger = logging.getLogger(__name__)


class ContentOrganizationServer(Server):
    """MCP server for content organization operations.
    
    This server provides tools for organizing course content, restructuring files,
    and generating cross-references between content.
    """

    def __init__(self):
        """Initialize the content organization server."""
        super().__init__("content-organization-server")
        self.mcp_handler = MCPHandler()
        
        # Register tool handlers on MCP handler
        self.mcp_handler.register_tool('organize_course_content', CourseContentHandler())
        self.mcp_handler.register_tool('reorganize_files', FileReorganizationHandler())
        self.mcp_handler.register_tool('generate_cross_references', CrossReferenceHandler())
        
        # Load tool schemas
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'tools_schemas.yaml')
        self.mcp_handler._load_tools_schema()  # Ensure schemas are loaded
        
        logger.info("Content Organization Server initialized successfully")

    async def list_resources(self) -> List[Resource]:
        """List available MCP resources.

        Returns:
            List of available resources that can be accessed via read_resource.
        """
        return self.mcp_handler.get_resources()

    async def read_resource(self, uri: str) -> str:
        """Read a specific resource's content.

        Args:
            uri: The URI of the resource to read

        Returns:
            The resource content as a string

        Raises:
            ValueError: If the resource URI is not recognized
        """
        return await self.mcp_handler.read_resource(uri)

    async def list_tools(self) -> List[Tool]:
        """List available MCP tools.

        Returns:
            List of available tools that can be called via call_tool.
        """
        return self.mcp_handler.get_tools()

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a specific tool with arguments.

        Args:
            name: Name of the tool to call
            arguments: Dictionary of arguments for the tool

        Returns:
            List of TextContent responses from the tool

        Raises:
            ValueError: If the tool name is not recognized
            TypeError: If the arguments don't match the tool's schema
        """
        return await self.mcp_handler.call_tool(name, arguments)

    async def serve(self) -> None:
        """Start the MCP server using stdio communication.

        This method sets up the decorated handlers and runs the server using
        stdio for communication.
        """
        # Set up decorated handlers
        @self.list_resources()
        async def _list_resources():
            return await self.list_resources()

        @self.read_resource()
        async def _read_resource(uri: str):
            return await self.read_resource(uri)

        @self.list_tools()
        async def _list_tools():
            return await self.list_tools()

        @self.call_tool()
        async def _call_tool(name: str, arguments: Dict[str, Any]):
            return await self.call_tool(name, arguments)

        # Run via stdio
        logger.info(f"Starting {self.name} MCP server")
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"Error running {self.name} MCP server: {str(e)}")
            raise

    @classmethod
    async def run(cls) -> None:
        """Create and run an MCP server.

        This is a convenience method for creating and running a server in one step.

        Args:
            name: Name of the MCP server
            config: Optional server configuration

        Example:
            ```python
            if __name__ == "__main__":
                asyncio.run(MCPServerBase.run("example-server"))
            ```
        """
        server = cls()
        await server.serve()
