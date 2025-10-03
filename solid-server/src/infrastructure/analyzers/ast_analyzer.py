"""
AST-Based Analyzer
==================
Analyzes Python files using Abstract Syntax Tree parsing.
Coordinates multiple principle checkers.
"""

import ast
from pathlib import Path
from typing import List
from domain.interfaces import IAnalyzer, IPrincipleChecker
from domain.models import SolidReport, SolidViolation, SolidPrinciple


class ASTAnalyzer(IAnalyzer):
    """
    AST-based implementation of IAnalyzer.
    Coordinates principle checkers to analyze Python files.
    
    Follows Open-Closed Principle - new checkers can be added
    without modifying this class.
    """

    def __init__(self, checkers: List[IPrincipleChecker]):
        """
        Initialize analyzer with principle checkers.
        
        Args:
            checkers: List of IPrincipleChecker implementations
        """
        self._checkers = checkers

    def analyze_file(self, file_path: Path) -> SolidReport:
        """
        Analyze a Python file for SOLID principle violations.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            SolidReport containing violations and score
            
        Raises:
            FileNotFoundError: If file doesn't exist
            SyntaxError: If file has syntax errors
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            source_lines = source_code.splitlines()
            
            # Parse the AST
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                # Return report with syntax error violation
                return SolidReport(
                    file_path=str(file_path),
                    violations=[SolidViolation(
                        principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                        severity="high",
                        line_number=e.lineno or 1,
                        message=f"Syntax error: {e.msg}",
                        suggestion="Fix syntax errors before SOLID analysis",
                        code_snippet=self._get_code_snippet(
                            source_lines, e.lineno or 1
                        )
                    )],
                    score=0.0,
                    summary={
                        principle: (
                            1 if principle ==
                            SolidPrinciple.SINGLE_RESPONSIBILITY
                            else 0
                        )
                        for principle in SolidPrinciple
                    }
                )
            
            # Run all principle checkers
            all_violations = []
            for checker in self._checkers:
                violations = checker.check(
                    tree,
                    source_lines,
                    str(file_path)
                )
                all_violations.extend(violations)
            
            # Calculate score and summary
            score = self._calculate_score(all_violations)
            summary = self._calculate_summary(all_violations)
            
            return SolidReport(
                file_path=str(file_path),
                violations=all_violations,
                score=score,
                summary=summary
            )
            
        except Exception as e:
            # Return report with analysis error
            return SolidReport(
                file_path=str(file_path),
                violations=[SolidViolation(
                    principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                    severity="high",
                    line_number=1,
                    message=f"Analysis error: {str(e)}",
                    suggestion="Check file accessibility and format",
                    code_snippet=""
                )],
                score=0.0,
                summary={
                    principle: (
                        1 if principle ==
                        SolidPrinciple.SINGLE_RESPONSIBILITY
                        else 0
                    )
                    for principle in SolidPrinciple
                }
            )

    def _calculate_score(
        self, violations: List[SolidViolation]
    ) -> float:
        """
        Calculate overall SOLID score (0-100).
        Higher is better.
        """
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {"high": 10, "medium": 5, "low": 2}
        total_penalty = sum(
            severity_weights.get(v.severity, 2)
            for v in violations
        )
        
        # Convert to score (higher is better)
        base_score = 100
        penalty_factor = min(total_penalty, 100)  # Cap penalty at 100
        
        return max(0.0, base_score - penalty_factor)

    def _calculate_summary(
        self, violations: List[SolidViolation]
    ) -> dict:
        """Calculate violation summary by principle"""
        summary = {principle: 0 for principle in SolidPrinciple}
        
        for violation in violations:
            summary[violation.principle] += 1
        
        return summary

    def _get_code_snippet(
        self, source_lines: List[str], line_number: int, context: int = 2
    ) -> str:
        """Get a code snippet around the given line number"""
        if not source_lines:
            return ""
        
        start = max(0, line_number - context - 1)
        end = min(len(source_lines), line_number + context)
        
        lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_number - 1 else "   "
            lines.append(
                f"{marker} {i+1:3d}: {source_lines[i]}"
            )
        
        return "\n".join(lines)
