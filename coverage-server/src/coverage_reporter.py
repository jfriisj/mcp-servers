"""
Coverage report generation and formatting for the Coverage MCP Server
"""
import logging
from pathlib import Path

from models import ReportConfig
from coverage_runner import CoverageRunner

logger = logging.getLogger(__name__)


class CoverageReporter:
    """Handles generation of coverage reports in various formats"""

    def __init__(self, coverage_runner: CoverageRunner, project_root: Path):
        self.coverage_runner = coverage_runner
        self.project_root = project_root

    async def generate_reports(self, config: ReportConfig) -> str:
        """Generate coverage reports in specified formats"""
        results = []

        for format_type in config.formats or []:
            result = await self._generate_single_report(format_type, config)
            results.append(result)

        return "\n\n".join(results)

    async def _generate_single_report(
        self, format_type: str, config: ReportConfig
    ) -> str:
        """Generate a single report in the specified format"""
        cmd = ["coverage", "report"]

        if format_type == "html":
            output_dir = Path(config.output_dir) / "coverage-html"
            output_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["coverage", "html", f"--directory={output_dir}"]
        elif format_type == "xml":
            output_file = Path(config.output_dir) / "coverage.xml"
            Path(config.output_dir).mkdir(parents=True, exist_ok=True)
            cmd = ["coverage", "xml", f"-o={output_file}"]
        elif format_type == "json":
            output_file = Path(config.output_dir) / "coverage.json"
            Path(config.output_dir).mkdir(parents=True, exist_ok=True)
            cmd = ["coverage", "json", f"-o={output_file}"]
        elif format_type == "term-missing":
            cmd = ["coverage", "report", "--show-missing"]
        elif format_type == "term":
            cmd = ["coverage", "report"]

        if config.show_missing and format_type in ["term", "term-missing"]:
            if "--show-missing" not in cmd:
                cmd.append("--show-missing")

        if config.skip_covered:
            cmd.append("--skip-covered")

        output, error, returncode = await self.coverage_runner.run_coverage_command(
            cmd
        )

        if returncode == 0:
            if format_type in ["html", "xml", "json"]:
                output_path = self._get_output_path(format_type, config)
                result = (
                    f"✅ {format_type.upper()} report generated: {output_path}"
                )
                return result
            else:
                return f"📊 {format_type.upper()} Coverage Report:\n{output}"
        else:
            error_msg = f"❌ {format_type.upper()} report failed:\n{output}"
            if error:
                error_msg += f"\nErrors: {error}"
            return error_msg

    def _get_output_path(self, format_type: str, config: ReportConfig) -> str:
        """Get the output path for a report format"""
        if format_type == "html":
            return f"{config.output_dir}/coverage-html/index.html"
        elif format_type == "xml":
            return f"{config.output_dir}/coverage.xml"
        elif format_type == "json":
            return f"{config.output_dir}/coverage.json"
        return config.output_dir

    async def check_threshold(
        self, threshold: float, per_file: bool = False
    ) -> str:
        """Check if coverage meets threshold requirements"""
        cmd = ["coverage", "report"]

        if per_file:
            cmd.append("--show-missing")

        output, error, returncode = await self.coverage_runner.run_coverage_command(
            cmd
        )

        if returncode == 0 or output:
            # Parse total coverage
            total_coverage = self._parse_total_coverage(output)

            if total_coverage is not None:
                if total_coverage >= threshold:
                    response = (
                        f"✅ Coverage threshold met! "
                        f"({total_coverage:.1f}% >= {threshold:.1f}%)\n\n"
                    )
                else:
                    response = (
                        f"❌ Coverage below threshold! "
                        f"({total_coverage:.1f}% < {threshold:.1f}%)\n\n"
                    )
            else:
                response = (
                    "⚠️ Could not parse coverage percentage from output.\n\n"
                )

            if per_file:
                response += "📄 Coverage Report:\n" + output
            else:
                response += f"Coverage Report:\n{output}"

            if error:
                response += f"\n\nErrors:\n{error}"

            return response
        else:
            error_msg = f"❌ Coverage check failed:\n{output}"
            if error:
                error_msg += f"\n\nErrors:\n{error}"
            return error_msg

    def _parse_total_coverage(self, output: str) -> float | None:
        """Parse total coverage percentage from output"""
        lines = output.split("\n")
        for line in lines:
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        try:
                            return float(part.replace("%", ""))
                        except ValueError:
                            continue
        return None
