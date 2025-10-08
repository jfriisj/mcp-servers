"""
Import Test MCP Server
=====================

MCP server for testing and validating Python imports, exports, and dependencies.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from mcp_handler import MCPHandler
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase

logger = logging.getLogger(__name__)


class ImportTestMCPServer:
    """MCP Server for import testing and validation"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.server = Server("import-test-mcp-server")
        
        # Initialize dependencies following dependency injection pattern
        self.dependency_resolver = DependencyResolver(self.project_root)
        self.import_analyzer = ImportAnalyzer(self.dependency_resolver)
        
        # Initialize use cases
        self.analyze_imports_uc = AnalyzeImportsUseCase(self.import_analyzer)
        self.validate_deps_uc = ValidateDependenciesUseCase(self.dependency_resolver)
        
        # Initialize MCP handler with dependencies
        self.mcp_handler = MCPHandler(
            project_root=self.project_root,
            analyze_imports_uc=self.analyze_imports_uc,
            validate_deps_uc=self.validate_deps_uc,
            import_analyzer=self.import_analyzer,
            dependency_resolver=self.dependency_resolver
        )

    async def list_tools(self) -> List[Tool]:
        """List available tools"""
        return self.mcp_handler.get_tools()

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool"""
        return await self.mcp_handler.call_tool(name, arguments)

    async def serve(self) -> None:
        """Start the MCP server"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP package not available. Install with: pip install mcp")
        
        logger.info("Starting Import Test MCP Server")

        @self.server.list_tools()
        async def handle_list_tools():
            """Return list of available tools"""
            return await self.list_tools()
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls"""
            return await self.call_tool(name, arguments)

        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )