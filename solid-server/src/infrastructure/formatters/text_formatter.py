"""
Text Formatter
==============
Formats SOLID analysis reports as plain text.
"""

from pathlib import Path
from typing import List, Dict, Any
from domain.interfaces import IFormatter
from domain.models import SolidReport


class TextFormatter(IFormatter):
    """
    Plain text formatter for SOLID reports.
    Follows Single Responsibility Principle - only formats to text.
    """

    def format_file_report(self, report: SolidReport) -> str:
        """
        Format a single file analysis report.
        
        Args:
            report: SolidReport to format
            
        Returns:
            Formatted text string
        """
        output = f"""
SOLID Analysis Report: {Path(report.file_path).name}
{'=' * 60}

Score: {report.score:.1f}/100

Violations by Principle:
"""
        
        for principle, count in report.summary.items():
            if count > 0:
                output += f"  {principle.value}: {count} violations\n"
        
        if report.violations:
            output += "\nDetailed Violations:\n"
            for violation in report.violations:
                output += f"""
[{violation.principle.value}] {violation.severity.upper()}
Line {violation.line_number}: {violation.message}
💡 {violation.suggestion}

{violation.code_snippet}
{'─' * 60}
"""
        else:
            output += "\n✅ No violations found!\n"
        
        return output.strip()

    def format_directory_report(
        self,
        reports: List[SolidReport],
        summary: Dict[str, Any]
    ) -> str:
        """
        Format a directory analysis report.
        
        Args:
            reports: List of SolidReports
            summary: Summary statistics
            
        Returns:
            Formatted text string
        """
        output = f"""
SOLID PRINCIPLES ANALYSIS REPORT
{'=' * 60}

SUMMARY:
Average Score: {summary.get('average_score', 0):.1f}/100
Files Analyzed: {summary.get('total_files', 0)}
Files with Violations: {summary.get('files_with_violations', 0)}
Total Violations: {summary.get('total_violations', 0)}

VIOLATIONS BY PRINCIPLE:
"""
        
        for principle, count in summary.get(
            'violations_by_principle', {}
        ).items():
            output += f"{principle}: {count} violations\n"
        
        # Most problematic files
        worst_files = summary.get('worst_files', [])
        if worst_files:
            output += f"\nMOST PROBLEMATIC FILES:\n"
            for i, report in enumerate(worst_files[:5], 1):
                file_name = Path(report.file_path).name
                output += (
                    f"{i}. {file_name}: {report.score:.1f}/100 "
                    f"({len(report.violations)} violations)\n"
                )
        
        # Detailed file reports (only files with violations)
        output += "\n" + "=" * 60
        output += "\nDETAILED RESULTS\n"
        output += "=" * 60 + "\n"
        
        for report in reports:
            if report.violations:
                file_name = Path(report.file_path).name
                output += f"\n📄 {file_name}\n"
                output += f"Score: {report.score:.1f}/100\n\n"
                
                for violation in report.violations:
                    output += (
                        f"  📍 Line {violation.line_number} "
                        f"[{violation.principle.value}] "
                        f"{violation.severity.upper()}\n"
                    )
                    output += f"     {violation.message}\n"
                    output += f"     💡 {violation.suggestion}\n\n"
        
        return output.strip()

    def format_suggestions(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """
        Format refactoring suggestions.
        
        Args:
            suggestions: List of suggestion dictionaries
            
        Returns:
            Formatted text string
        """
        if not suggestions:
            return "✅ No refactoring suggestions needed!"
        
        output = f"""
🔧 REFACTORING SUGGESTIONS (Top {len(suggestions)})
{'=' * 60}

Priority Score Calculation:
- High severity: +10 points
- Medium severity: +5 points
- Low severity: +2 points

"""
        
        for i, sugg in enumerate(suggestions, 1):
            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(sugg['severity'], '⚪')
            
            output += f"""
{i}. {severity_emoji} Priority Score: {sugg['priority_score']}
   File: {sugg['file']} (line {sugg['line']})
   Principle: {sugg['principle']} - {sugg['severity'].upper()}
   
   Problem: {sugg['message']}
   
   💡 Suggestion: {sugg['suggestion']}
   
   Code Context:
{sugg['code']}
{'─' * 60}
"""
        
        return output.strip()
