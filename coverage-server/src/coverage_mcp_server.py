#!/usr/bin/env python3
"""
Coverage MCP Server for Python Test Coverage Analysis
====================================================
Model Context Protocol server that provides comprehensive test coverage analysis using pytest-cov and coverage.py.
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


class CoverageMCPServer:
    """MCP server for Python test coverage analysis."""

    def __init__(self, project_root: Optional[Path] = None):
        self.server = Server("coverage-server", "1.0.0")
        self.project_root = project_root or Path.cwd()
        self.pyproject_toml = self._find_pyproject_toml()
        self.pytest_ini = self._find_pytest_config()

        # Setup MCP handlers
        self._setup_tools()

    def _find_pyproject_toml(self) -> Optional[Path]:
        """Find pyproject.toml configuration file."""
        for path in [self.project_root, *self.project_root.parents]:
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                return pyproject_path
        return None

    def _find_pytest_config(self) -> Optional[Path]:
        """Find pytest configuration file."""
        for config_file in ["pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"]:
            config_path = self.project_root / config_file
            if config_path.exists():
                return config_path
        return None

    def _setup_tools(self):
        """Set up MCP tools for coverage operations."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available coverage tools."""
            return [
                types.Tool(
                    name="run-tests-with-coverage",
                    description="Run tests with coverage measurement using pytest-cov",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_path": {
                                "type": "string",
                                "description": "Path to tests directory or specific test file",
                                "default": "tests/",
                            },
                            "source": {
                                "type": "string",
                                "description": "Source directory to measure coverage for",
                                "default": "src/",
                            },
                            "min_coverage": {
                                "type": "number",
                                "description": "Minimum coverage percentage required",
                                "default": 80.0,
                            },
                            "parallel": {
                                "type": "boolean",
                                "description": "Run tests in parallel using pytest-xdist",
                                "default": False,
                            },
                            "markers": {
                                "type": "string",
                                "description": "Pytest markers to select/deselect tests (e.g. 'not slow')",
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Verbose output",
                                "default": False,
                            },
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="generate-coverage-report",
                    description="Generate coverage reports in multiple formats (HTML, XML, JSON)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "formats": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "html",
                                        "xml",
                                        "json",
                                        "term",
                                        "term-missing",
                                    ],
                                },
                                "description": "Output formats for coverage report",
                                "default": ["html", "xml", "term-missing"],
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for reports",
                                "default": "test-reports",
                            },
                            "show_missing": {
                                "type": "boolean",
                                "description": "Show line numbers of missing coverage",
                                "default": True,
                            },
                            "skip_covered": {
                                "type": "boolean",
                                "description": "Skip files with 100% coverage",
                                "default": False,
                            },
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="check-coverage-threshold",
                    description="Check if coverage meets minimum threshold requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "threshold": {
                                "type": "number",
                                "description": "Minimum coverage percentage required",
                                "default": 80.0,
                            },
                            "per_file": {
                                "type": "boolean",
                                "description": "Check threshold per file",
                                "default": False,
                            },
                            "fail_under": {
                                "type": "boolean",
                                "description": "Fail if coverage is below threshold",
                                "default": True,
                            },
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="find-missing-coverage",
                    description="Identify specific lines and files with missing coverage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to analyze (glob pattern)",
                            },
                            "show_contexts": {
                                "type": "boolean",
                                "description": "Show test contexts that hit each line",
                                "default": False,
                            },
                            "min_coverage": {
                                "type": "number",
                                "description": "Show only files below this coverage percentage",
                                "default": 100.0,
                            },
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="coverage-diff",
                    description="Compare coverage between branches or commits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base": {
                                "type": "string",
                                "description": "Base branch/commit to compare against",
                                "default": "HEAD~1",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["text", "json"],
                                "description": "Output format",
                                "default": "text",
                            },
                        },
                        "required": [],
                    },
                ),
                types.Tool(
                    name="coverage-summary",
                    description="Get a quick coverage summary with key metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "show_files": {
                                "type": "boolean",
                                "description": "Include per-file coverage breakdown",
                                "default": True,
                            },
                            "sort_by": {
                                "type": "string",
                                "enum": ["coverage", "missing", "name"],
                                "description": "Sort files by coverage, missing lines, or name",
                                "default": "coverage",
                            },
                        },
                        "required": [],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "run-tests-with-coverage":
                    return await self._run_tests_with_coverage(arguments)
                elif name == "generate-coverage-report":
                    return await self._generate_coverage_report(arguments)
                elif name == "check-coverage-threshold":
                    return await self._check_coverage_threshold(arguments)
                elif name == "find-missing-coverage":
                    return await self._find_missing_coverage(arguments)
                elif name == "coverage-diff":
                    return await self._coverage_diff(arguments)
                elif name == "coverage-summary":
                    return await self._coverage_summary(arguments)
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

    async def _run_tests_with_coverage(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Run tests with coverage measurement."""
        test_path = args.get("test_path", "tests/")
        source = args.get("source", "src/")
        min_coverage = args.get("min_coverage", 80.0)
        parallel = args.get("parallel", False)
        markers = args.get("markers")
        verbose = args.get("verbose", False)

        cmd = ["python", "-m", "pytest"]

        # Add coverage options
        cmd.extend([f"--cov={source}", "--cov-report=term-missing"])
        cmd.extend([f"--cov-fail-under={min_coverage}"])

        # Add test path
        if Path(test_path).exists():
            cmd.append(test_path)

        # Add parallel execution if requested
        if parallel:
            cmd.extend(["-n", "auto"])

        # Add markers if specified
        if markers:
            cmd.extend(["-m", markers])

        # Add verbosity
        if verbose:
            cmd.append("-v")

        # Use configuration file if available
        if self.pytest_ini:
            cmd.extend(["-c", str(self.pytest_ini)])

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

            # Parse coverage from output
            coverage_line = None
            for line in output.split("\n"):
                if "TOTAL" in line and "%" in line:
                    coverage_line = line
                    break

            if result.returncode == 0:
                response = "✅ Tests passed with coverage requirements met!\n\n"
                response += (
                    f"📊 Coverage Summary:\n{coverage_line}\n\n"
                    if coverage_line
                    else ""
                )
                response += f"🎯 Required: {min_coverage}%\n\n"
                response += "Test Output:\n" + output
            else:
                response = f"❌ Tests failed or coverage below {min_coverage}%\n\n"
                response += (
                    f"📊 Coverage Summary:\n{coverage_line}\n\n"
                    if coverage_line
                    else ""
                )
                response += f"Test Output:\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ pytest or coverage not found. Install with: pip install pytest pytest-cov",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Test execution failed: {str(e)}"
                )
            ]

    async def _generate_coverage_report(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Generate coverage reports in multiple formats."""
        formats = args.get("formats", ["html", "xml", "term-missing"])
        output_dir = args.get("output_dir", "test-reports")
        show_missing = args.get("show_missing", True)
        skip_covered = args.get("skip_covered", False)

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []

        for format_type in formats:
            cmd = ["coverage", "report"]

            if format_type == "html":
                cmd = ["coverage", "html", f"--directory={output_dir}/coverage-html"]
            elif format_type == "xml":
                cmd = ["coverage", "xml", f"-o={output_dir}/coverage.xml"]
            elif format_type == "json":
                cmd = ["coverage", "json", f"-o={output_dir}/coverage.json"]
            elif format_type == "term-missing":
                cmd = ["coverage", "report", "--show-missing"]
            elif format_type == "term":
                cmd = ["coverage", "report"]

            if show_missing and format_type in ["term", "term-missing"]:
                if "--show-missing" not in cmd:
                    cmd.append("--show-missing")

            if skip_covered:
                cmd.append("--skip-covered")

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
                    if format_type in ["html", "xml", "json"]:
                        results.append(
                            f"✅ {format_type.upper()} report generated: {output_dir}/"
                        )
                    else:
                        results.append(
                            f"📊 {format_type.upper()} Coverage Report:\n{output}"
                        )
                else:
                    results.append(f"❌ {format_type.upper()} report failed:\n{output}")
                    if error:
                        results.append(f"Errors: {error}")

            except Exception as e:
                results.append(f"❌ {format_type.upper()} report failed: {str(e)}")

        return [types.TextContent(type="text", text="\n\n".join(results))]

    async def _check_coverage_threshold(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Check if coverage meets threshold requirements."""
        threshold = args.get("threshold", 80.0)
        per_file = args.get("per_file", False)
        fail_under = args.get("fail_under", True)

        cmd = ["coverage", "report"]

        if fail_under:
            cmd.extend([f"--fail-under={threshold}"])

        if per_file:
            cmd.append("--show-missing")

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

            # Parse total coverage
            total_coverage = None
            for line in output.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            total_coverage = float(part.replace("%", ""))
                            break
                    break

            if result.returncode == 0:
                response = f"✅ Coverage threshold met! ({total_coverage}% >= {threshold}%)\n\n"
                if per_file:
                    response += "📄 Per-file Coverage:\n" + output
            else:
                response = f"❌ Coverage below threshold! ({total_coverage}% < {threshold}%)\n\n"
                response += "📄 Coverage Report:\n" + output
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except FileNotFoundError:
            return [
                types.TextContent(
                    type="text",
                    text="❌ coverage not found. Install with: pip install coverage",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Coverage check failed: {str(e)}"
                )
            ]

    async def _find_missing_coverage(
        self, args: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Find specific lines and files with missing coverage."""
        file_pattern = args.get("file_pattern")
        show_contexts = args.get("show_contexts", False)
        min_coverage = args.get("min_coverage", 100.0)

        cmd = ["coverage", "report", "--show-missing"]

        if show_contexts:
            cmd.append("--show-contexts")

        if file_pattern:
            cmd.append(file_pattern)

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

            if result.returncode == 0 or output:
                # Parse output to find files below min_coverage
                lines = output.split("\n")
                missing_files = []

                for line in lines:
                    if "%" in line and "TOTAL" not in line and line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                coverage_str = next(p for p in parts if "%" in p)
                                coverage = float(coverage_str.replace("%", ""))
                                if coverage < min_coverage:
                                    missing_files.append(line)
                            except (ValueError, StopIteration):
                                continue

                response = f"🔍 Missing Coverage Analysis (< {min_coverage}%):\n\n"
                if missing_files:
                    response += "Files with missing coverage:\n"
                    response += "\n".join(missing_files)
                else:
                    response += "✅ All files meet the coverage requirement!"

                response += f"\n\n📊 Full Coverage Report:\n{output}"
            else:
                response = f"❌ Failed to analyze coverage:\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Missing coverage analysis failed: {str(e)}"
                )
            ]

    async def _coverage_diff(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Compare coverage between branches or commits."""
        base = args.get("base", "HEAD~1")
        format_type = args.get("format", "text")

        # This is a simplified implementation - in practice, you'd want to:
        # 1. Run coverage on current branch
        # 2. Checkout base branch, run coverage
        # 3. Compare the results
        # For now, we'll show current coverage and note the limitation

        try:
            # Get current coverage
            result = await asyncio.create_subprocess_exec(
                "coverage",
                "report",
                "--format=json" if format_type == "json" else "--show-missing",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if result.returncode == 0:
                response = f"📊 Current Coverage (vs {base}):\n\n"
                response += "⚠️ Note: Full diff comparison requires running tests on both branches.\n"
                response += "This shows current coverage only.\n\n"
                response += output
            else:
                response = f"❌ Coverage diff failed:\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Coverage diff failed: {str(e)}"
                )
            ]

    async def _coverage_summary(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get a quick coverage summary with key metrics."""
        show_files = args.get("show_files", True)
        # sort_by functionality would be implemented for future enhancement

        cmd = ["coverage", "report"]

        if show_files:
            cmd.append("--show-missing")

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

            if result.returncode == 0 or output:
                # Parse summary statistics
                lines = output.split("\n")
                total_line = None
                file_count = 0

                for line in lines:
                    if "TOTAL" in line:
                        total_line = line
                    elif "%" in line and line.strip() and "Name" not in line:
                        file_count += 1

                response = "📊 Coverage Summary\n" + "=" * 50 + "\n\n"

                if total_line:
                    parts = total_line.split()
                    if len(parts) >= 4:
                        response += (
                            f"📈 Total Coverage: {next(p for p in parts if '%' in p)}\n"
                        )
                        response += f"📁 Files Analyzed: {file_count}\n\n"

                if show_files:
                    response += "📄 Per-File Coverage:\n"
                    response += output
                else:
                    response += (
                        f"Overall Coverage:\n{total_line}" if total_line else output
                    )

            else:
                response = f"❌ Coverage summary failed:\n{output}"
                if error:
                    response += f"\n\nErrors:\n{error}"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"❌ Coverage summary failed: {str(e)}"
                )
            ]


async def main():
    """Main entry point for the Coverage MCP server."""
    try:
        # Get project root from command line arguments
        project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

        if not HAS_MCP:
            print("[ERROR] MCP package not available. Install with: pip install mcp")
            return

        # Create and run the service
        service = CoverageMCPServer(project_root)

        # Import the stdio transport
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await service.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="coverage-server",
                    server_version="1.0.0",
                    capabilities=service.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        print(f"[ERROR] Coverage MCP server failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
