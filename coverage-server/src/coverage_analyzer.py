"""
Coverage data parsing and analysis for the Coverage MCP Server
"""

import re
from typing import Dict, List, Optional, Any


class CoverageAnalyzer:
    """Analyzes coverage output and extracts meaningful data"""

    @staticmethod
    def parse_coverage_percentage(output: str) -> Optional[float]:
        """Extract total coverage percentage from output"""
        # Look for patterns like "TOTAL 85.2%" or "85.2%"
        total_pattern = r"TOTAL\s+(\d+(?:\.\d+)?)%"
        match = re.search(total_pattern, output, re.IGNORECASE)

        if match:
            return float(match.group(1))

        # Fallback: look for any percentage at the end of lines
        lines = output.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if "%" in line:
                # Extract the last percentage found
                percentages = re.findall(r"(\d+(?:\.\d+)?)%", line)
                if percentages:
                    return float(percentages[-1])

        return None

    @staticmethod
    def parse_file_coverage(output: str) -> Dict[str, Dict[str, Any]]:
        """Parse per-file coverage information"""
        file_coverage = {}
        lines = output.split("\n")

        for line in lines:
            line = line.strip()
            if not line or "Name" in line or "TOTAL" in line or "---" in line:
                continue

            # Parse lines like: "src/module.py    15     10    67%   5-8, 12"
            parts = re.split(r"\s+", line)
            if len(parts) >= 4 and "%" in parts[-2]:
                try:
                    filename = parts[0]
                    statements = int(parts[-4])
                    missing = int(parts[-3])
                    coverage_str = parts[-2]
                    coverage_pct = float(coverage_str.replace("%", ""))

                    # Extract missing lines if present
                    missing_lines: List[int] = []
                    if len(parts) > 4:
                        missing_part = " ".join(parts[4:])
                        if missing_part and missing_part != "100%":
                            # Parse line numbers like "5-8, 12"
                            line_matches = re.findall(r"(\d+)(?:-(\d+))?", missing_part)
                            for start, end in line_matches:
                                start_num = int(start)
                                if end:
                                    end_num = int(end)
                                    missing_lines.extend(range(start_num, end_num + 1))
                                else:
                                    missing_lines.append(start_num)

                    file_coverage[filename] = {
                        "statements": statements,
                        "missing": missing,
                        "coverage": coverage_pct,
                        "missing_lines": missing_lines,
                    }
                except (ValueError, IndexError):
                    continue

        return file_coverage

    @staticmethod
    def find_files_below_threshold(
        file_coverage: Dict[str, Dict[str, Any]], threshold: float
    ) -> List[str]:
        """Find files with coverage below the specified threshold"""
        below_threshold = []

        for filename, data in file_coverage.items():
            if data["coverage"] < threshold:
                below_threshold.append(filename)

        return below_threshold

    @staticmethod
    def calculate_overall_stats(
        file_coverage: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate overall coverage statistics"""
        if not file_coverage:
            return {
                "total_files": 0,
                "average_coverage": 0.0,
                "files_below_80": 0,
                "files_below_90": 0,
            }

        total_coverage = 0.0
        files_below_80 = 0
        files_below_90 = 0

        for data in file_coverage.values():
            coverage = data["coverage"]
            total_coverage += coverage
            if coverage < 80:
                files_below_80 += 1
            if coverage < 90:
                files_below_90 += 1

        return {
            "total_files": len(file_coverage),
            "average_coverage": total_coverage / len(file_coverage),
            "files_below_80": files_below_80,
            "files_below_90": files_below_90,
        }

    @staticmethod
    def format_coverage_summary(
        total_coverage: Optional[float],
        file_coverage: Dict[str, Dict[str, Any]],
        show_files: bool = True,
    ) -> str:
        """Format coverage data into a readable summary"""
        summary = "📊 Coverage Summary\n" + "=" * 50 + "\n\n"

        if total_coverage is not None:
            summary += f"📈 Total Coverage: {total_coverage:.1f}%\n"

        stats = CoverageAnalyzer.calculate_overall_stats(file_coverage)
        summary += f"📁 Files Analyzed: {stats['total_files']}\n"
        summary += f"📊 Average Coverage: {stats['average_coverage']:.1f}%\n"

        if stats["files_below_80"] > 0:
            summary += f"⚠️ Files below 80%: {stats['files_below_80']}\n"
        if stats["files_below_90"] > 0:
            summary += f"⚠️ Files below 90%: {stats['files_below_90']}\n"

        if show_files and file_coverage:
            summary += "\n📄 Per-File Coverage:\n"
            for filename, data in sorted(file_coverage.items()):
                status = "✅" if data["coverage"] >= 80 else "❌"
                summary += f"{status} {filename}: {data['coverage']:.1f}%\n"

        return summary
