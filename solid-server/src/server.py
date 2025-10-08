"""
Main MCP server implementation for the SOLID Principles MCP Server
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from mcp_handler import MCPHandler

# Import for composition root
from infrastructure.analyzers.ast_analyzer import ASTAnalyzer
from infrastructure.analyzers.principle_checkers import (
    SRPChecker, OCPChecker, LSPChecker, ISPChecker, DIPChecker
)
from infrastructure.formatters.text_formatter import TextFormatter
from application.analyze_file import AnalyzeFileUseCase
from application.analyze_directory import AnalyzeDirectoryUseCase
from application.generate_report import GenerateReportUseCase
from application.suggest_refactoring import SuggestRefactoringUseCase

logger = logging.getLogger(__name__)


class SolidMCPServer:
    """
    Main MCP server for SOLID principles analysis.
    
    This is the Composition Root - where all dependencies are created
    and wired together following Dependency Injection principles.
    """

    def __init__(
        self,
        project_root: Path,
        server: Server,
        mcp_handler: MCPHandler
    ):
        """
        Initialize MCP server with fully injected dependencies.
        
        This constructor follows Dependency Inversion Principle by:
        1. Requiring all dependencies to be injected
        2. Not creating any dependencies internally
        3. Depending on abstractions, not concretions
        
        Args:
            project_root: Root directory for SOLID analysis
            server: MCP server instance
            mcp_handler: Handler for MCP protocol operations
        """
        self.project_root = project_root
        self.server = server
        self.mcp_handler = mcp_handler

    async def list_resources(self) -> List[Resource]:
        """List available resources"""
        return [
            Resource(
                uri=AnyUrl("solid://principles"),
                name="SOLID Principles Reference",
                description="Comprehensive guide to SOLID principles with examples",
                mimeType="text/markdown",
            ),
            Resource(
                uri=AnyUrl("solid://current-score"),
                name="Current Project SOLID Score",
                description="Overall SOLID compliance score for the project",
                mimeType="text/plain",
            ),
        ]

    async def read_resource(self, uri: AnyUrl) -> str:
        """Read a resource"""
        if str(uri) == "solid://principles":
            return self._get_solid_principles_guide()
        elif str(uri) == "solid://current-score":
            # Get overall project score - delegate to use case to avoid DIP violation
            # This eliminates direct instantiation of DirectoryFilters
            return await self._get_project_score()
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    async def _get_project_score(self) -> str:
        """
        Get project SOLID score by delegating to use cases.
        
        This method eliminates DIP violations by:
        1. Not creating DirectoryFilters directly
        2. Using the injected mcp_handler's methods
        3. Avoiding direct instantiation of domain objects
        """
        # Use MCP handler to get analysis (it handles the filters internally)
        # This avoids direct instantiation and follows clean architecture
        try:
            # Call the directory analysis tool which handles filter creation
            result = await self.mcp_handler.call_tool("solid-check-directory", {
                "directory_path": str(self.project_root)
            })
            
            # Extract basic metrics from the result text
            result_text = result[0].text if result else "No analysis available"
            return f"Current SOLID Analysis:\n\n{result_text[:500]}..."
            
        except Exception as e:
            return f"Error getting project score: {str(e)}"

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
        logger.info("Starting SOLID Principles MCP Server")

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

    def _get_solid_principles_guide(self) -> str:
        """Return comprehensive SOLID principles guide"""
        return """
# SOLID Principles Guide

## Overview

SOLID is an acronym for five design principles intended to make software designs more understandable, flexible, and maintainable. These principles were promoted by Robert C. Martin (Uncle Bob).

## The Five Principles

### 1. Single Responsibility Principle (SRP)
**"A class should have only one reason to change."**

- Each class should have only one job or responsibility
- High cohesion within classes, low coupling between classes
- Makes code easier to understand, test, and maintain

### 2. Open-Closed Principle (OCP)
**"Software entities should be open for extension, but closed for modification."**

- You should be able to add new functionality without changing existing code
- Use abstraction and polymorphism to enable extensions
- Protects existing, tested code from breaking

### 3. Liskov Substitution Principle (LSP)
**"Objects of a superclass should be replaceable with objects of its subclasses."**

- Subclasses must be substitutable for their base classes
- Derived classes should not weaken preconditions or strengthen postconditions
- Ensures polymorphism works correctly

### 4. Interface Segregation Principle (ISP)
**"Clients should not be forced to depend on interfaces they do not use."**

- Create smaller, focused interfaces rather than large, monolithic ones
- Classes should only implement methods they actually need
- Reduces coupling and improves flexibility

### 5. Dependency Inversion Principle (DIP)
**"Depend on abstractions, not concretions."**

- High-level modules should not depend on low-level modules
- Both should depend on abstractions (interfaces)
- Enables loose coupling and testability

## Benefits of Following SOLID

1. **Maintainability** - Code is easier to modify and extend
2. **Testability** - Classes are more focused and easier to test
3. **Flexibility** - System can adapt to changing requirements
4. **Readability** - Code is cleaner and more self-documenting
5. **Reusability** - Components can be reused in different contexts

## Common Anti-Patterns

- **God Classes** - Classes that do too many things (violates SRP)
- **Rigid Code** - Hard to extend without modification (violates OCP)
- **Broken Inheritance** - Subclasses can't replace parents (violates LSP)
- **Fat Interfaces** - Interfaces with too many methods (violates ISP)
- **Tight Coupling** - Direct dependencies on concrete classes (violates DIP)

## Using This MCP Server

This server provides tools to:

- **Analyze individual files** for SOLID violations
- **Scan entire directories** for compliance issues
- **Generate comprehensive reports** in multiple formats
- **Explain principles** with examples and best practices
- **Track compliance scores** over time

Use the available tools to improve your code's adherence to SOLID principles!
        """.strip()


async def main():
    """Main entry point using composition root for dependency injection"""
    logging.basicConfig(level=logging.INFO)
    
    # Use composition root to create server with proper dependency injection
    # This eliminates DIP violations by using the composition root pattern
    from presentation.composition_root import create_solid_server
    
    server = create_solid_server()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())