"""
MCP protocol handling for the Hadolint MCP Server
"""

import logging
from typing import Dict, Any, List

from mcp.types import Tool, TextContent

from models import LintConfig, DirectoryLintConfig, RulesConfig
from hadolint_runner import HadolintRunner

logger = logging.getLogger(__name__)


class MCPHandler:
    """Handles MCP protocol interactions for hadolint operations"""

    def __init__(self, hadolint_runner: HadolintRunner):
        self.hadolint_runner = hadolint_runner

    def get_tools(self) -> List[Tool]:
        """List available hadolint tools"""
        return [
            Tool(
                name="hadolint-check",
                description="Lint a Dockerfile using hadolint",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dockerfile_path": {
                            "type": "string",
                            "description": "Path to the Dockerfile to lint",
                        },
                        "config_file": {
                            "type": "string",
                            "description": "Path to hadolint config file",
                        },
                        "ignore_rules": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of rules to ignore "
                            "(e.g., ['DL3006', 'DL3018'])",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["tty", "json", "sarif"],
                            "description": "Output format",
                            "default": "tty",
                        },
                        "no_color": {
                            "type": "boolean",
                            "description": "Disable colored output",
                            "default": False,
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "Enable verbose output",
                            "default": False,
                        },
                    },
                    "required": ["dockerfile_path"],
                },
            ),
            Tool(
                name="hadolint-check-dir",
                description="Lint all Dockerfiles in a directory using hadolint",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to directory containing Dockerfiles",
                            "default": ".",
                        },
                        "config_file": {
                            "type": "string",
                            "description": "Path to hadolint config file",
                        },
                        "ignore_rules": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of rules to ignore "
                            "(e.g., ['DL3006', 'DL3018'])",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["tty", "json", "sarif"],
                            "description": "Output format",
                            "default": "tty",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Recursively search for Dockerfiles",
                            "default": True,
                        },
                        "no_color": {
                            "type": "boolean",
                            "description": "Disable colored output",
                            "default": False,
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "Enable verbose output",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="hadolint-show-rules",
                description="Show available hadolint rules and help information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_all": {
                            "type": "boolean",
                            "description": "Show detailed information about all rules",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            ),
        ]

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle tool calls for hadolint operations"""
        try:
            if name == "hadolint-check":
                return await self._hadolint_check(arguments)
            elif name == "hadolint-check-dir":
                return await self._hadolint_check_dir(arguments)
            elif name == "hadolint-show-rules":
                return await self._hadolint_show_rules(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error("Error calling tool %s: %s", name, e)
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    async def _hadolint_check(self, args: Dict[str, Any]) -> List[TextContent]:
        """Lint a single Dockerfile"""
        config = LintConfig(
            dockerfile_path=args["dockerfile_path"],
            config_file=args.get("config_file"),
            ignore_rules=args.get("ignore_rules"),
            format=args.get("format", "tty"),
            no_color=args.get("no_color", False),
            verbose=args.get("verbose", False),
        )

        result = await self.hadolint_runner.lint_dockerfile(config)

        if result.success:
            response = "✅ Dockerfile linting passed!\n\n"
            if result.issues_found == 0:
                response += "No issues found in the Dockerfile."
            else:
                response += f"Found {result.issues_found} issue(s).\n\n"
                response += f"Linting Output:\n{result.output}"
        else:
            response = "❌ Dockerfile linting failed!\n\n"
            if result.error:
                response += f"Error: {result.error}\n\n"
            if result.output:
                response += f"Linting Output:\n{result.output}"

        return [TextContent(type="text", text=response)]

    async def _hadolint_check_dir(self, args: Dict[str, Any]) -> List[TextContent]:
        """Lint all Dockerfiles in a directory"""
        config = DirectoryLintConfig(
            directory_path=args.get("directory_path", "."),
            config_file=args.get("config_file"),
            ignore_rules=args.get("ignore_rules"),
            format=args.get("format", "tty"),
            recursive=args.get("recursive", True),
            no_color=args.get("no_color", False),
            verbose=args.get("verbose", False),
        )

        result = await self.hadolint_runner.lint_directory(config)

        if result.success:
            response = "✅ Directory linting completed!\n\n"
            if result.issues_found == 0:
                response += "No issues found in any Dockerfiles."
            else:
                response += (
                    f"Found {result.issues_found} issue(s) across all Dockerfiles.\n\n"
                )
                response += f"Linting Output:\n{result.output}"
        else:
            response = "❌ Directory linting failed!\n\n"
            if result.error:
                response += f"Error: {result.error}\n\n"
            if result.output:
                response += f"Linting Output:\n{result.output}"

        return [TextContent(type="text", text=response)]

    async def _hadolint_show_rules(self, args: Dict[str, Any]) -> List[TextContent]:
        """Show hadolint rules and help information"""
        config = RulesConfig(
            format="tty",
            show_all=args.get("show_all", False),
        )

        result = await self.hadolint_runner.show_rules(config)

        if result.success:
            response = "📖 Hadolint Rules and Help Information:\n\n"
            response += result.output
        else:
            response = "❌ Failed to get hadolint help:\n\n"
            if result.error:
                response += f"Error: {result.error}\n\n"
            if result.output:
                response += f"Output:\n{result.output}"

        return [TextContent(type="text", text=response)]
