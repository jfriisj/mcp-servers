"""
Data models for the Coverage MCP Server
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class CoverageResult:
    """Result of a coverage run"""

    total_coverage: float
    covered_lines: int
    total_lines: int
    missing_lines: List[int]
    file_coverage: Dict[str, Dict[str, Any]]
    output: str
    error: Optional[str] = None


@dataclass
class TestRunConfig:
    """Configuration for test execution"""

    test_path: str = "tests/"
    source: str = "src/"
    min_coverage: float = 80.0
    parallel: bool = False
    markers: Optional[str] = None
    verbose: bool = False


@dataclass
class ReportConfig:
    """Configuration for coverage reports"""

    formats: Optional[List[str]] = None
    output_dir: str = "test-reports"
    show_missing: bool = True
    skip_covered: bool = False

    def __post_init__(self):
        if self.formats is None:
            self.formats = ["html", "xml", "term-missing"]


@dataclass
class ThresholdConfig:
    """Configuration for coverage thresholds"""

    threshold: float = 80.0
    per_file: bool = False
    fail_under: bool = True


@dataclass
class CoverageAnalysis:
    """Analysis of coverage data"""

    file_pattern: Optional[str] = None
    show_contexts: bool = False
    min_coverage: float = 100.0


@dataclass
class CoverageDiff:
    """Configuration for coverage comparison"""

    base: str = "HEAD~1"
    format: str = "text"


@dataclass
class CoverageSummary:
    """Configuration for coverage summary"""

    show_files: bool = True
    sort_by: str = "coverage"
