"""  
Main MCP server orchestration for Whisper
==========================================
Coordinates all components and provides the main server interface.

Refactored to use Clean Architecture with CompositionRoot.
"""

from pathlib import Path
from typing import Optional

# MCP imports (these would be installed as dependencies)
try:
    from mcp.server import NotificationOptions, Server
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
class WhisperMCPServer:
    """Main MCP server for Whisper audio transcription."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize MCP server with CompositionRoot.
        
        Args:
            project_root: Optional project root path for configuration
        """
        # Create composition root with dependency injection
        from presentation.mcp.handler import MCPHandler
        from presentation.composition_root import CompositionRoot

        root_path = str(project_root) if project_root else None
        self.composition_root = CompositionRoot(root_path)
        self.mcp_handler = MCPHandler(self.composition_root)

        # Setup MCP server
        self.server = Server("whisper-server", "1.0.0")
        self._setup_mcp_handlers()

    def _setup_mcp_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools():
            """List available Whisper tools."""
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
                    server_name="whisper-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
