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
        """Load tool definitions from YAML file and return as Tool objects."""
        import yaml
        import os
        tools_path = os.path.join(os.path.dirname(__file__), "..", "tools", "tools_schemas.yaml")
        with open(tools_path, "r", encoding="utf-8") as f:
            tool_defs = yaml.safe_load(f)
        tools = []
        for tool in tool_defs:
            tools.append(
                types.Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
            )
        self._tool_handlers = {tool["name"]: tool.get("handler", tool["name"]) for tool in tool_defs}
        return tools

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Dispatch tool call to the correct handler based on YAML config."""
        try:
            handler_map = {
                "ruff-check": self._handle_ruff_check,
                "ruff-format": self._handle_ruff_format,
                "ruff-check-diff": self._handle_ruff_check_diff,
                "ruff-show-settings": self._handle_ruff_show_settings,
                "ruff-explain-rule": self._handle_ruff_explain_rule,
                "ruff-config": self._handle_ruff_config,
                "ruff-linter": self._handle_ruff_linter,
                "ruff-clean": self._handle_ruff_clean,
                "ruff-analyze-graph": self._handle_ruff_analyze_graph,
            }
            if not hasattr(self, "_tool_handlers"):
                self.get_tools()  # ensure _tool_handlers is loaded
            handler_name = self._tool_handlers.get(name, name)
            handler = handler_map.get(handler_name)
            if handler:
                return await handler(arguments)
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

    async def _handle_ruff_config(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-config tool call."""
        from models import RuffConfigConfig

        config = RuffConfigConfig(
            option=args.get("option"),
            output_format=args.get("output_format", "text"),
        )

        result = await self.ruff_runner.run_config(config)
        command_name = f"Ruff config{' ' + config.option if config.option else ''}"
        return [self._format_command_result(command_name, result)]

    async def _handle_ruff_linter(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-linter tool call."""
        from models import RuffLinterConfig

        config = RuffLinterConfig(
            output_format=args.get("output_format", "text"),
        )

        result = await self.ruff_runner.run_linter(config)
        return [self._format_command_result("Ruff linter", result)]

    async def _handle_ruff_clean(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-clean tool call."""
        from models import RuffCleanConfig

        config = RuffCleanConfig()
        result = await self.ruff_runner.run_clean(config)
        return [self._format_command_result("Ruff clean", result)]

    async def _handle_ruff_analyze_graph(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle ruff-analyze-graph tool call."""
        from models import RuffAnalyzeGraphConfig

        config = RuffAnalyzeGraphConfig(
            files=args.get("files"),
            direction=args.get("direction", "dependencies"),
            detect_string_imports=args.get("detect_string_imports", False),
            min_dots=args.get("min_dots"),
            preview=args.get("preview", False),
            target_version=args.get("target_version"),
            python=args.get("python"),
        )

        result = await self.ruff_runner.run_analyze_graph(config)
        return [self._format_command_result("Ruff analyze graph", result)]

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

    def _get_ruff_config_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-config tool."""
        return {
            "type": "object",
            "properties": {
                "option": {
                    "type": "string",
                    "description": "Specific config option to show (optional)",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format",
                    "default": "text",
                },
            },
            "required": [],
        }

    def _get_ruff_linter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-linter tool."""
        return {
            "type": "object",
            "properties": {
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format",
                    "default": "text",
                },
            },
            "required": [],
        }

    def _get_ruff_clean_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-clean tool."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def _get_ruff_analyze_graph_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ruff-analyze-graph tool."""
        return {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files or directories to include",
                    "default": ["."],
                },
                "direction": {
                    "type": "string",
                    "enum": ["dependencies", "dependents"],
                    "description": "Direction of the import map",
                    "default": "dependencies",
                },
                "detect_string_imports": {
                    "type": "boolean",
                    "description": "Attempt to detect imports from string literals",
                    "default": False,
                },
                "min_dots": {
                    "type": "integer",
                    "description": "Minimum number of dots in a string import",
                },
                "preview": {
                    "type": "boolean",
                    "description": "Enable preview mode",
                    "default": False,
                },
                "target_version": {
                    "type": "string",
                    "enum": ["py37", "py38", "py39", "py310", "py311", "py312", "py313", "py314"],
                    "description": "Minimum Python version that should be supported",
                },
                "python": {
                    "type": "string",
                    "description": "Path to a virtual environment",
                },
            },
            "required": [],
        }
