"""
MCP protocol handling for the Coverage MCP Server
"""
import logging
from typing import Dict, Any, List

from mcp.types import Tool, TextContent

from models import (
    TestRunConfig, ReportConfig,
    CoverageAnalysis, CoverageDiff, CoverageSummary
)
from coverage_runner import CoverageRunner
from coverage_reporter import CoverageReporter
from coverage_analyzer import CoverageAnalyzer

logger = logging.getLogger(__name__)


class MCPHandler:
    """Handles MCP protocol interactions for coverage operations"""

    def __init__(
        self,
        coverage_runner: CoverageRunner,
        coverage_reporter: CoverageReporter,
        coverage_analyzer: CoverageAnalyzer
    ):
        self.coverage_runner = coverage_runner
        self.coverage_reporter = coverage_reporter
        self.coverage_analyzer = coverage_analyzer

    def get_tools(self) -> List[Tool]:
        """List available coverage tools"""
        return [
            Tool(
                name="run-tests-with-coverage",
                description="Run tests with coverage measurement using "
                           "pytest-cov",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_path": {
                            "type": "string",
                            "description": "Path to tests directory or "
                                           "specific test file",
                            "default": "tests/",
                        },
                        "source": {
                            "type": "string",
                            "description": "Source directory to measure "
                                           "coverage for",
                            "default": "src/",
                        },
                        "min_coverage": {
                            "type": "number",
                            "description": "Minimum coverage percentage "
                                           "required",
                            "default": 80.0,
                        },
                        "parallel": {
                            "type": "boolean",
                            "description": "Run tests in parallel using "
                                           "pytest-xdist",
                            "default": False,
                        },
                        "markers": {
                            "type": "string",
                            "description": "Pytest markers to select/deselect "
                                           "tests",
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
            Tool(
                name="generate-coverage-report",
                description="Generate coverage reports in multiple formats",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "formats": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "html", "xml", "json",
                                    "term", "term-missing"
                                ],
                            },
                            "description": "Output formats for coverage "
                                           "report",
                            "default": ["html", "xml", "term-missing"],
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory for reports",
                            "default": "test-reports",
                        },
                        "show_missing": {
                            "type": "boolean",
                            "description": "Show line numbers of missing "
                                           "coverage",
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
            Tool(
                name="check-coverage-threshold",
                description="Check if coverage meets minimum threshold "
                           "requirements",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "threshold": {
                            "type": "number",
                            "description": "Minimum coverage percentage "
                                           "required",
                            "default": 80.0,
                        },
                        "per_file": {
                            "type": "boolean",
                            "description": "Check threshold per file",
                            "default": False,
                        },
                        "fail_under": {
                            "type": "boolean",
                            "description": "Fail if coverage below threshold",
                            "default": True,
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="find-missing-coverage",
                description="Identify specific lines and files with missing "
                           "coverage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to analyze",
                        },
                        "show_contexts": {
                            "type": "boolean",
                            "description": "Show test contexts that hit each "
                                           "line",
                            "default": False,
                        },
                        "min_coverage": {
                            "type": "number",
                            "description": "Show only files below this "
                                           "coverage %",
                            "default": 100.0,
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="coverage-diff",
                description="Compare coverage between branches or commits",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base": {
                            "type": "string",
                            "description": "Base branch/commit to compare "
                                           "against",
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
            Tool(
                name="coverage-summary",
                description="Get a quick coverage summary with key metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_files": {
                            "type": "boolean",
                            "description": "Include per-file coverage "
                                           "breakdown",
                            "default": True,
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["coverage", "missing", "name"],
                            "description": "Sort files by coverage, missing "
                                           "lines, or name",
                            "default": "coverage",
                        },
                    },
                    "required": [],
                },
            ),
        ]

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle tool calls for coverage operations"""
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
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error("Error calling tool %s: %s", name, e)
            return [TextContent(type="text", text=f"Error executing "
                                   f"{name}: {str(e)}")]

    async def _run_tests_with_coverage(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Run tests with coverage measurement"""
        config = TestRunConfig(
            test_path=args.get("test_path", "tests/"),
            source=args.get("source", "src/"),
            min_coverage=args.get("min_coverage", 80.0),
            parallel=args.get("parallel", False),
            markers=args.get("markers"),
            verbose=args.get("verbose", False),
        )

        output, error, returncode = await self.coverage_runner. \
            run_tests_with_coverage(config)

        # Parse coverage from output
        total_coverage = self.coverage_analyzer. \
            parse_coverage_percentage(output)

        if returncode == 0:
            response = "✅ Tests passed with coverage requirements met!\n\n"
            if total_coverage is not None:
                response += f"📊 Coverage Summary: {total_coverage:.1f}%\n"
                response += f"🎯 Required: {config.min_coverage:.1f}%\n\n"
            response += f"Test Output:\n{output}"
        else:
            response = f"❌ Tests failed or coverage below " \
                       f"{config.min_coverage:.1f}%\n\n"
            if total_coverage is not None:
                response += f"📊 Coverage Summary: {total_coverage:.1f}%\n"
            response += f"Test Output:\n{output}"
            if error:
                response += f"\n\nErrors:\n{error}"

        return [TextContent(type="text", text=response)]

    async def _generate_coverage_report(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Generate coverage reports in multiple formats"""
        config = ReportConfig(
            formats=args.get("formats"),
            output_dir=args.get("output_dir", "test-reports"),
            show_missing=args.get("show_missing", True),
            skip_covered=args.get("skip_covered", False),
        )

        result = await self.coverage_reporter.generate_reports(config)
        return [TextContent(type="text", text=result)]

    async def _check_coverage_threshold(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Check if coverage meets threshold requirements"""
        threshold = args.get("threshold", 80.0)
        per_file = args.get("per_file", False)

        result = await self.coverage_reporter. \
            check_threshold(threshold, per_file)
        return [TextContent(type="text", text=result)]

    async def _find_missing_coverage(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Find specific lines and files with missing coverage"""
        analysis = CoverageAnalysis(
            file_pattern=args.get("file_pattern"),
            show_contexts=args.get("show_contexts", False),
            min_coverage=args.get("min_coverage", 100.0),
        )

        # For now, return a simplified response
        # In a full implementation, this would analyze coverage data
        response = f"🔍 Missing Coverage Analysis (< " \
                   f"{analysis.min_coverage:.1f}%):\n\n"
        response += "⚠️ Full implementation requires coverage data parsing.\n"
        response += "This is a placeholder for the missing coverage analysis."

        return [TextContent(type="text", text=response)]

    async def _coverage_diff(self, args: Dict[str, Any]) -> List[TextContent]:
        """Compare coverage between branches or commits"""
        diff_config = CoverageDiff(
            base=args.get("base", "HEAD~1"),
            format=args.get("format", "text"),
        )

        # Simplified implementation - would need git operations
        response = f"📊 Current Coverage (vs {diff_config.base}):\n\n"
        response += "⚠️ Note: Full diff comparison requires running tests on " \
                    "both branches.\n"
        response += "This shows current coverage only.\n\n"

        # Get current coverage
        cmd = ["coverage", "report", "--show-missing"]
        output, error, returncode = await self.coverage_runner. \
            run_coverage_command(cmd)

        if returncode == 0:
            response += output
        else:
            response += f"❌ Failed to get coverage:\n{output}"
            if error:
                response += f"\n\nErrors:\n{error}"

        return [TextContent(type="text", text=response)]

    async def _coverage_summary(
        self, args: Dict[str, Any]
    ) -> List[TextContent]:
        """Get a quick coverage summary with key metrics"""
        summary_config = CoverageSummary(
            show_files=args.get("show_files", True),
            sort_by=args.get("sort_by", "coverage"),
        )

        # Get coverage report
        cmd = ["coverage", "report", "--show-missing"]
        output, error, returncode = await self.coverage_runner. \
            run_coverage_command(cmd)

        if returncode == 0 or output:
            total_coverage = self.coverage_analyzer. \
                parse_coverage_percentage(output)
            file_coverage = self.coverage_analyzer.parse_file_coverage(output)

            response = self.coverage_analyzer.format_coverage_summary(
                total_coverage, file_coverage, summary_config.show_files
            )
        else:
            response = f"❌ Coverage summary failed:\n{output}"
            if error:
                response += f"\n\nErrors:\n{error}"

        return [TextContent(type="text", text=response)]