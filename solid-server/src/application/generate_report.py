"""
Generate Report Use Case
========================
Single responsibility: Generate formatted reports from analysis results.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from domain.interfaces import IFormatter
from domain.models import SolidReport, SolidPrinciple


@dataclass
class ReportOptions:
    """Options for report generation"""
    include_suggestions: bool = True
    output_format: str = "text"  # "text", "json", "markdown"
    severity_filter: str = "all"  # "all", "high", "medium", "low"


class GenerateReportUseCase:
    """
    Use case for generating formatted reports.
    Depends on IFormatter abstraction (Dependency Inversion Principle).
    """

    def __init__(self, formatter: IFormatter):
        """
        Initialize with formatter dependency.
        
        Args:
            formatter: Implementation of IFormatter interface
        """
        self._formatter = formatter

    def execute(
        self,
        reports: List[SolidReport],
        options: ReportOptions = None
    ) -> str:
        """
        Execute the use case: generate formatted report.
        
        Args:
            reports: List of analysis reports
            options: Optional report generation options
            
        Returns:
            Formatted report as string
        """
        if options is None:
            options = ReportOptions()
        
        # Filter by severity if needed
        if options.severity_filter != "all":
            reports = self._filter_by_severity(
                reports, options.severity_filter
            )
        
        # Calculate summary statistics
        summary = self._calculate_summary(reports)
        
        # Format using the formatter
        return self._formatter.format_directory_report(reports, summary)

    def _filter_by_severity(
        self,
        reports: List[SolidReport],
        severity: str
    ) -> List[SolidReport]:
        """Filter reports to only include specific severity."""
        filtered_reports = []
        
        for report in reports:
            filtered_violations = [
                v for v in report.violations
                if v.severity == severity
            ]
            
            if filtered_violations:
                # Create new report with filtered violations
                from domain.models import SolidReport
                filtered_report = SolidReport(
                    file_path=report.file_path,
                    violations=filtered_violations,
                    score=report.score,
                    summary=report.summary
                )
                filtered_reports.append(filtered_report)
        
        return filtered_reports

    def _calculate_summary(
        self,
        reports: List[SolidReport]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for reports."""
        if not reports:
            return {
                'total_files': 0,
                'files_with_violations': 0,
                'total_violations': 0,
                'average_score': 0.0,
                'violations_by_principle': {},
                'worst_files': []
            }
        
        total_files = len(reports)
        files_with_violations = sum(
            1 for r in reports if r.violations
        )
        total_violations = sum(len(r.violations) for r in reports)
        average_score = sum(r.score for r in reports) / total_files
        
        # Count violations by principle
        violations_by_principle = {}
        for principle in SolidPrinciple:
            violations_by_principle[principle.value] = sum(
                r.summary.get(principle, 0) for r in reports
            )
        
        # Find worst files (lowest scores)
        worst_files = sorted(reports, key=lambda r: r.score)[:5]
        
        return {
            'total_files': total_files,
            'files_with_violations': files_with_violations,
            'total_violations': total_violations,
            'average_score': average_score,
            'violations_by_principle': violations_by_principle,
            'worst_files': worst_files
        }
