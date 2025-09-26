"""
MCP protocol handling for Ruff Server
=====================================
Manages MCP tool definitions and protocol interactions.
"""

from typing import Any, Dict, List

# MCP imports (these would be installed as dependencies)
try:
    from mcp import types

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

    # Fallback for development without MCP
    class types:
        @staticmethod
        def Tool(**kwargs):
            return kwargs

        @staticmethod
        def TextContent(**kwargs):
            return kwargs


class MCPHandler:
    """Handles MCP protocol interactions and tool definitions."""

    def __init__(self, ruff_runner):
        self.ruff_runner = ruff_runner

    def get_tools(self) -> List[types.Tool]:
        """Get list of available MCP tools."""
        return [
            types.Tool(
                name="ruff-check",
                description="Run Ruff linter to identify code issues",
                inputSchema=self._get_ruff_check_schema(),
            ),
            types.Tool(
                name="ruff-format",
                description="Format Python code using Ruff (Black-compatible)",
                inputSchema=self._get_ruff_format_schema(),
            ),
            types.Tool(
                name="ruff-check-diff",
                description="Check Ruff issues on changed files only (git diff)",
                inputSchema=self._get_ruff_check_diff_schema(),
            ),
            types.Tool(
                name="ruff-show-settings",
                description="Show active Ruff configuration settings",
                inputSchema=self._get_ruff_show_settings_schema(),
            ),
            types.Tool(
                name="ruff-explain-rule",
                description="Explain a specific Ruff rule",
                inputSchema=self._get_ruff_explain_rule_schema(),
            ),
        ]

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle tool calls."""
        try:
            if name == "ruff-check":
                return await self._handle_ruff_check(arguments)
            elif name == "ruff-format":
                return await self._handle_ruff_format(arguments)
            elif name == "ruff-check-diff":
                return await self._handle_ruff_check_diff(arguments)
            elif name == "ruff-show-settings":
                return await self._handle_ruff_show_settings(arguments)
            elif name == "ruff-explain-rule":
                return await self._handle_ruff_explain_rule(arguments)
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"Error executing tool {name}: {str(e)}"
                )
            ]

    async def _handle_ruff_check(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Handle ruff-check tool call."""
        from models import RuffCheckConfig

        config = RuffCheckConfig(
            path=args.get("path", "."),
            fix=args.get("fix", False),
            format=args.get("format", "text"),
            select=args.get("select"),
            ignore=args.get("ignore"),
            show_fixes=args.get("show_fixes", False),
        )

        result = await self.ruff_runner.run_check(config)
        return [self._format_command_result("Ruff check", result)]

    async def _handle_ruff_format(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-format tool call."""
        from models import RuffFormatConfig

        config = RuffFormatConfig(
            path=args.get("path", "."),
            check=args.get("check", False),
            diff=args.get("diff", False),
        )

        result = await self.ruff_runner.run_format(config)
        return [self._format_command_result("Ruff format", result)]

    async def _handle_ruff_check_diff(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-check-diff tool call."""
        from models import RuffCheckDiffConfig

        config = RuffCheckDiffConfig(
            base=args.get("base", "HEAD~1"),
            format=args.get("format", "text"),
        )

        result = await self.ruff_runner.run_check_diff(config)
        return [self._format_command_result("Ruff check-diff", result)]

    async def _handle_ruff_show_settings(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-show-settings tool call."""
        from models import RuffShowSettingsConfig

        config = RuffShowSettingsConfig(
            path=args.get("path", "."),
        )

        result = await self.ruff_runner.run_show_settings(config)
        return [self._format_command_result("Ruff show-settings", result)]

    async def _handle_ruff_explain_rule(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-explain-rule tool call."""
        from models import RuffExplainRuleConfig

        rule = args.get("rule")
        if not rule:
            return [
                types.TextContent(
                    type="text", text="❌ Rule code is required (e.g., 'E501', 'F401')"
                )
            ]

        config = RuffExplainRuleConfig(rule=rule)
        result = await self.ruff_runner.run_explain_rule(config)
        return [self._format_command_result(f"Ruff rule {rule}", result)]

    def _format_command_result(self, command_name: str, result) -> types.TextContent:
        """Format command result for MCP response."""
        if result.success:
            if result.returncode == 0:
                response = f"✅ {command_name} passed - no issues found!"
                if result.stdout:
                    response += f"\n\n{result.stdout}"
            else:
                response = f"✅ {command_name} completed successfully!"
                if result.stdout:
                    response += f"\n\n{result.stdout}"
        else:
            response = f"❌ {command_name} found issues:\n\n{result.output}"

        return types.TextContent(type="text", text=response)

    def _get_ruff_check_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-check tool."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to check (file or directory)",
                    "default": ".",
                },
                "fix": {
                    "type": "boolean",
                    "description": "Automatically fix issues where possible",
                    "default": False,
                },
                "format": {
                    "type": "string",
                    "enum": [
                        "text",
                        "json",
                        "github",
                        "gitlab",
                        "junit",
                        "sarif",
                    ],
                    "description": "Output format",
                    "default": "text",
                },
                "select": {
                    "type": "string",
                    "description": "Comma-separated list of rule codes to select",
                },
                "ignore": {
                    "type": "string",
                    "description": "Comma-separated list of rule codes to ignore",
                },
                "show_fixes": {
                    "type": "boolean",
                    "description": "Show available fixes for issues",
                    "default": False,
                },
            },
            "required": [],
        }

    def _get_ruff_format_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-format tool."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to format (file or directory)",
                    "default": ".",
                },
                "check": {
                    "type": "boolean",
                    "description": "Only check formatting without making changes",
                    "default": False,
                },
                "diff": {
                    "type": "boolean",
                    "description": "Show diff of formatting changes",
                    "default": False,
                },
            },
            "required": [],
        }

    def _get_ruff_check_diff_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-check-diff tool."""
        return {
            "type": "object",
            "properties": {
                "base": {
                    "type": "string",
                    "description": "Base commit/branch to compare against",
                    "default": "HEAD~1",
                },
                "format": {
                    "type": "string",
                    "enum": ["text", "json", "github"],
                    "description": "Output format",
                    "default": "text",
                },
            },
            "required": [],
        }

    def _get_ruff_show_settings_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-show-settings tool."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to show settings for",
                    "default": ".",
                }
            },
            "required": [],
        }

    def _get_ruff_explain_rule_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-explain-rule tool."""
        return {
            "type": "object",
            "properties": {
                "rule": {
                    "type": "string",
                    "description": "Rule code to explain (e.g., 'E501', 'F401')",
                }
            },
            "required": ["rule"],
        }
