#!/usr/bin/env python3
"""
Ruff MCP Server for Python Code Quality
=======================================
Model Context Protocol server that provides fast Python linting and formatting using Ruff.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP imports (these would be installed as dependencies)
try:
    from mcp import types
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions

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
    """MCP server for Ruff Python linting and formatting."""

    def __init__(self, project_root: Optional[Path] = None):
        self.server = Server("ruff-server", "1.0.0")
        self.project_root = project_root or Path.cwd()
        self.pyproject_toml = self._find_pyproject_toml()

        # Setup MCP handlers
        self._setup_tools()

    def _find_pyproject_toml(self) -> Optional[Path]:
        """Find pyproject.toml configuration file."""
        for path in [self.project_root, *self.project_root.parents]:
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                return pyproject_path
        return None

    def _setup_tools(self):
        """Set up MCP tools for Ruff operations."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available Ruff tools."""
            return [
                types.Tool(
                    name="ruff-check",
                    description="Run Ruff linter to identify code issues",
                    inputSchema={
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
                                "description": "Comma-separated list of rule codes to select (e.g., 'E,W,F')",
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
                    },
                ),
                types.Tool(
                    name="ruff-format",
                    description="Format Python code using Ruff (Black-compatible)",
                    inputSchema={
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
                    },
                ),
                types.Tool(
                    name="ruff-check-diff",
                    description="Check Ruff issues on changed files only (git diff)",
                    inputSchema={
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
                    },
                ),
                types.Tool(
                    name="ruff-show-settings",
                    description="Show active Ruff configuration settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to show settings for",
                                "default": ".",
                            }
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="ruff-explain-rule",
                    description="Explain a specific Ruff rule",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "rule": {
                                "type": "string",
                                "description": "Rule code to explain (e.g., 'E501', 'F401')",
                            }
                        },
                        "required": ["rule"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "ruff-check":
                    return await self._ruff_check(arguments)
                elif name == "ruff-format":
                    return await self._ruff_format(arguments)
                elif name == "ruff-check-diff":
                    return await self._ruff_check_diff(arguments)
                elif name == "ruff-show-settings":
                    return await self._ruff_show_settings(arguments)
                elif name == "ruff-explain-rule":
                    return await self._ruff_explain_rule(arguments)
                else:
                    return [
                        types.TextContent(type="text", text=f"Unknown tool: {name}")
                    ]
            except Exception as e:
                return [
                    types.TextContent(
                        type="text", text=f"Error executing tool {name}: {str(e)}"
                    )
                ]

    async def _ruff_check(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Run Ruff linter."""
        path = args.get("path", ".")
        fix = args.get("fix", False)
        format_type = args.get("format", "text")
        select = args.get("select")
        ignore = args.get("ignore")
        show_fixes = args.get("show_fixes", False)

        cmd = ["ruff", "check", path]

        if fix:
            cmd.append("--fix")

        if format_type != "text":
            cmd.extend(["--format", format_type])

        if select:
            cmd.extend(["--select", select])

        if ignore:
            cmd.extend(["--ignore", ignore])

        if show_fixes:
            cmd.append("--show-fixes")

        # Add config file if available
        if self.pyproject_toml:
            cmd.extend(["--config", str(self.pyproject_toml)])

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if result.returncode == 0:
                response = "✅ Ruff check passed - no issues found!"
                if output:
                    response += f"\n\n{output}"
            else:
                response = f"❌ Ruff check found issues:\n\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Ruff not found. Install with: pip install ruff",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(type="text", text=f"❌ Ruff check failed: {str(e)}")
            ]

    async def _ruff_format(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Format code using Ruff."""
        path = args.get("path", ".")
        check = args.get("check", False)
        diff = args.get("diff", False)

        cmd = ["ruff", "format", path]

        if check:
            cmd.append("--check")

        if diff:
            cmd.append("--diff")

        # Add config file if available
        if self.pyproject_toml:
            cmd.extend(["--config", str(self.pyproject_toml)])

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if result.returncode == 0:
                if check:
                    response = "✅ Code formatting is correct!"
                elif diff:
                    response = "📝 Formatting diff:\n\n" + (
                        output or "No changes needed"
                    )
                else:
                    response = "✅ Code formatted successfully!"
                    if output:
                        response += f"\n\nFiles formatted:\n{output}"
            else:
                response = f"❌ Ruff format failed:\n\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Ruff not found. Install with: pip install ruff",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(type="text", text=f"❌ Ruff format failed: {str(e)}")
            ]

    async def _ruff_check_diff(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Check Ruff issues on changed files only."""
        base = args.get("base", "HEAD~1")
        format_type = args.get("format", "text")

        try:
            # Get changed files
            git_result = await asyncio.create_subprocess_exec(
                "git",
                "diff",
                "--name-only",
                base,
                "--",
                "*.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            git_stdout, git_stderr = await git_result.communicate()

            if git_result.returncode != 0:
                return [
                    types.TextContent(
                        type="text", text=f"❌ Git diff failed: {git_stderr.decode()}"
                    )
                ]

            changed_files = [
                f.strip() for f in git_stdout.decode().split("\n") if f.strip()
            ]

            if not changed_files:
                return [
                    types.TextContent(type="text", text="ℹ️ No Python files changed")
                ]

            # Run Ruff on changed files
            cmd = ["ruff", "check"] + changed_files

            if format_type != "text":
                cmd.extend(["--format", format_type])

            if self.pyproject_toml:
                cmd.extend(["--config", str(self.pyproject_toml)])

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            response = f"📊 Ruff check on {len(changed_files)} changed file(s):\n"
            response += f"Files: {', '.join(changed_files[:5])}"
            if len(changed_files) > 5:
                response += f" (and {len(changed_files) - 5} more)"
            response += "\n\n"

            if result.returncode == 0:
                response += "✅ No issues found in changed files!"
            else:
                response += f"❌ Issues found:\n\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Ruff diff check failed: {str(e)}"
                )
            ]

    async def _ruff_show_settings(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Show active Ruff configuration."""
        path = args.get("path", ".")

        cmd = ["ruff", "check", "--show-settings", path]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if result.returncode == 0:
                response = "⚙️ Active Ruff Configuration:\n\n" + output
            else:
                response = f"❌ Failed to show settings:\n\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Ruff not found. Install with: pip install ruff",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Failed to show settings: {str(e)}"
                )
            ]

    async def _ruff_explain_rule(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Explain a specific Ruff rule."""
        rule = args.get("rule")

        if not rule:
            return [
                types.TextContent(
                    type="text", text="❌ Rule code is required (e.g., 'E501', 'F401')"
                )
            ]

        cmd = ["ruff", "rule", rule]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if result.returncode == 0:
                response = f"📖 Rule {rule} explanation:\n\n{output}"
            else:
                response = f"❌ Rule {rule} not found or error:\n\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Ruff not found. Install with: pip install ruff",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Failed to explain rule: {str(e)}"
                )
            ]


async def main():
    """Main entry point for the Ruff MCP server."""
    try:
        # Get project root from command line arguments
        project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

        if not HAS_MCP:
            print("[ERROR] MCP package not available. Install with: pip install mcp")
            return

        # Create and run the service
        service = RuffMCPServer(project_root)

        # Import the stdio transport
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await service.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ruff-server",
                    server_version="1.0.0",
                    capabilities=service.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        print(f"[ERROR] Ruff MCP server failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
