"""
Suggest Refactoring Use Case
============================
Single responsibility: Generate prioritized refactoring suggestions.
"""

from typing import List, Dict, Any
from domain.models import SolidReport, SolidPrinciple, SolidViolation


class RefactoringOptions:
    """Options for refactoring suggestions"""
    
    def __init__(self, max_suggestions=10, priority_filter="all"):
        # Ensure max_suggestions is always an integer
        if isinstance(max_suggestions, str):
            try:
                self.max_suggestions = int(max_suggestions)
            except (ValueError, TypeError):
                self.max_suggestions = 10
        else:
            self.max_suggestions = max_suggestions
            
        self.priority_filter = priority_filter


class SuggestRefactoringUseCase:
    """
    Use case for generating refactoring suggestions.
    Single responsibility: analyze violations and prioritize fixes.
    """

    def execute(
        self,
        reports: List[SolidReport],
        options: RefactoringOptions = None
    ) -> List[Dict[str, Any]]:
        """
        Execute the use case: generate refactoring suggestions.
        
        Args:
            reports: List of analysis reports
            options: Optional refactoring options
            
        Returns:
            List of prioritized suggestions
        """
        if options is None:
            options = RefactoringOptions()
        
        # Collect all violations with context
        suggestions = []
        for report in reports:
            for violation in report.violations:
                suggestion = {
                    'file': Path(report.file_path).name,
                    'full_path': report.file_path,
                    'line': violation.line_number,
                    'principle': violation.principle.value,
                    'severity': violation.severity,
                    'message': violation.message,
                    'suggestion': violation.suggestion,
                    'code': violation.code_snippet,
                    'priority_score': self._calculate_priority_score(
                        violation
                    ),
                }
                suggestions.append(suggestion)
        
        # Filter by priority if specified
        if options.priority_filter != "all":
            suggestions = [
                s for s in suggestions
                if s['severity'] == options.priority_filter
            ]
        
        # Sort by priority score (high to low)
        suggestions.sort(
            key=lambda x: x['priority_score'],
            reverse=True
        )
        
        # Limit suggestions
        return suggestions[:options.max_suggestions]

    def _calculate_priority_score(
        self,
        violation: SolidViolation
    ) -> int:
        """
        Calculate priority score for a violation.
        Higher scores = more important to fix.
        """
        # Base score by severity
        severity_scores = {"high": 10, "medium": 5, "low": 2}
        score = severity_scores.get(violation.severity, 0)

        # Boost foundation principles (SRP and DIP)
        if violation.principle in [
            SolidPrinciple.SINGLE_RESPONSIBILITY,
            SolidPrinciple.DEPENDENCY_INVERSION
        ]:
            score += 2

        # Boost violations with specific high-impact keywords
        high_impact_keywords = [
            'constructor', 'dependency', 'inheritance',
            'signature', 'coupling'
        ]
        if any(
            kw in violation.message.lower()
            for kw in high_impact_keywords
        ):
            score += 1

        return score


# Import Path for use in execute method
from pathlib import Path
