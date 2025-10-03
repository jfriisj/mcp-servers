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

logger = logging.getLogger(__name__)


class SolidMCPServer:
    """Main MCP server for SOLID principles analysis"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.server = Server("solid-mcp-server")
        self.mcp_handler = MCPHandler(self.project_root)

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
            # Get overall project score
            reports = self.mcp_handler.batch_analyzer.analyze_directory(self.project_root)
            summary = self.mcp_handler.batch_analyzer.generate_summary_report(reports)
            return f"""
Current SOLID Compliance Score: {summary['average_score']}/100

Project: {self.project_root.name}
Files analyzed: {summary['total_files']}
Files with violations: {summary['files_with_violations']}
Total violations: {summary['total_violations']}

Violations by principle:
- SRP: {summary['violations_by_principle']['SRP']}
- OCP: {summary['violations_by_principle']['OCP']}
- LSP: {summary['violations_by_principle']['LSP']}
- ISP: {summary['violations_by_principle']['ISP']}
- DIP: {summary['violations_by_principle']['DIP']}
            """.strip()
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
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    server = SolidMCPServer()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())