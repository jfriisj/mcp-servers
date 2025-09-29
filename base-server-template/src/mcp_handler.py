"""Base MCP handler implementation.

This module provides the base handler for MCP tools and resources, managing tool
registration, schema validation, and resource access.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml
from mcp.types import Resource, Tool, TextContent
from pydantic import ValidationError

from .models import ErrorResponse

logger = logging.getLogger(__name__)


class MCPHandler:
    """Base handler for MCP tools and resources.
    
    This class manages tool registration, schema validation, and resource access.
    Subclasses should override handle_tool to implement specific tool functionality.
    """

    def __init__(self):
        """Initialize the MCP handler."""
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self._load_tools_schema()

    def _load_tools_schema(self) -> None:
        """Load tool definitions from YAML schema file.

        The schema file should be located at tools/tools_schemas.yaml relative to
        the server root directory.
        """
        try:
            schema_path = Path(__file__).parent.parent / 'tools' / 'tools_schemas.yaml'
            if not schema_path.exists():
                logger.warning(f"Tools schema file not found: {schema_path}")
                return

            with open(schema_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                logger.error("Invalid YAML structure in tools schema file")
                return

            for tool_id, tool_data in data.items():
                try:
                    tool = Tool(
                        name=tool_data['name'],
                        description=tool_data['description'],
                        inputSchema=tool_data['inputSchema']
                    )
                    self.tools[tool.name] = tool
                    logger.debug(f"Registered tool: {tool.name}")
                except KeyError as e:
                    logger.error(f"Missing required field in tool definition: {e}")
                except Exception as e:
                    logger.error(f"Error loading tool {tool_id}: {e}")

        except Exception as e:
            logger.error(f"Error loading tools schema: {e}")

    def register_tool(self, tool: Tool) -> None:
        """Register a new tool.

        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_resource(self, resource: Resource) -> None:
        """Register a new resource.

        Args:
            resource: Resource to register
        """
        self.resources[str(resource.uri)] = resource
        logger.info(f"Registered resource: {resource.uri}")

    def get_resources(self) -> List[Resource]:
        """Get list of available resources.

        Returns:
            List of registered resources.
        """
        return list(self.resources.values())

    async def read_resource(self, uri: str) -> str:
        """Read a resource's content.

        Args:
            uri: URI of the resource to read

        Returns:
            Resource content as a string

        Raises:
            ValueError: If the resource URI is not recognized
        """
        if uri not in self.resources:
            raise ValueError(f"Unknown resource: {uri}")

        try:
            return await self.handle_resource(uri)
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise

    def get_tools(self) -> List[Tool]:
        """Get list of available tools.

        Returns:
            List of registered tools.
        """
        return list(self.tools.values())

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
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        tool = self.tools[name]

        try:
            # Basic schema validation using the tool's inputSchema
            self._validate_arguments(tool, arguments)

            # Call the tool implementation
            result = await self.handle_tool(name, arguments)
            return self._format_result(result)

        except ValidationError as e:
            logger.error(f"Validation error for tool {name}: {e}")
            return [self._format_error(str(e))]
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [self._format_error(str(e))]

    def _validate_arguments(self, tool: Tool, arguments: Dict[str, Any]) -> None:
        """Validate tool arguments against its schema.

        Args:
            tool: Tool definition containing the schema
            arguments: Arguments to validate

        Raises:
            ValidationError: If the arguments don't match the schema
        """
        # TODO: Implement schema validation
        # This is a placeholder for schema validation logic
        # In a real implementation, you would validate the arguments against
        # the tool's inputSchema using a JSON Schema validator
        pass

    async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool execution.

        This method should be overridden by subclasses to implement specific tool
        functionality.

        Args:
            name: Name of the tool to execute
            arguments: Validated arguments for the tool

        Returns:
            Tool-specific result that will be formatted into TextContent

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError(f"Tool not implemented: {name}")

    async def handle_resource(self, uri: str) -> str:
        """Handle resource reading.

        This method should be overridden by subclasses to implement specific resource
        reading functionality.

        Args:
            uri: URI of the resource to read

        Returns:
            Resource content as a string

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError(f"Resource not implemented: {uri}")

    def _format_result(self, result: Any) -> List[TextContent]:
        """Format a tool result into TextContent.

        Args:
            result: Tool execution result

        Returns:
            List of TextContent responses
        """
        if isinstance(result, list) and all(isinstance(r, TextContent) for r in result):
            return result
        elif isinstance(result, TextContent):
            return [result]
        else:
            return [TextContent(type="text", text=str(result))]

    def _format_error(self, message: str) -> TextContent:
        """Format an error message into TextContent.

        Args:
            message: Error message

        Returns:
            TextContent containing the error response
        """
        error = ErrorResponse(
            error="Tool execution failed",
            details={"message": message}
        )
        return TextContent(type="text", text=json.dumps(error.dict()))