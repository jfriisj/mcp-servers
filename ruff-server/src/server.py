"""
Main MCP server orchestration for Ruff
======================================
Coordinates all components and provides the main server interface.
"""

from pathlib import Path
from typing import Optional

# MCP imports (these would be installed as dependencies)
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

    # Fallback for development without MCP
    class Server:
        def __init__(self, name: str, version: str):
            pass

        def list_tools(self):
            return lambda func: func

        def call_tool(self):
            return lambda func: func

    class NotificationOptions:
        pass

    class InitializationOptions:
        pass


class RuffMCPServer:
    """Main MCP server for Ruff Python linting and formatting."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

        # Initialize components with dependency injection
        from config import ConfigurationManager
        from ruff_runner import RuffRunner
        from mcp_handler import MCPHandler

        self.config_manager = ConfigurationManager(self.project_root)
        self.ruff_runner = RuffRunner(self.config_manager, self.project_root)
        self.mcp_handler = MCPHandler(self.ruff_runner)

        # Setup MCP server
        self.server = Server("ruff-server", "1.0.0")
        self._setup_mcp_handlers()

    def _setup_mcp_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools():
            """List available Ruff tools."""
            return self.mcp_handler.get_tools()

        @self.server.call_tool()
        async def handle_call_tool(name, arguments):
            """Handle tool calls."""
            return await self.mcp_handler.call_tool(name, arguments)

    async def serve(self):
        """Start the MCP server."""
        if not HAS_MCP:
            print("[ERROR] MCP package not available. Install with: pip install mcp")
            return

        # Import the stdio transport
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ruff-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
