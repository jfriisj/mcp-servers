"""
Open-Closed Principle Checker

Detects violations of the Open-Closed Principle:
- Type checking (isinstance, type) instead of polymorphism
- Long elif chains that suggest missing abstraction
"""

import ast
from typing import List
from domain.interfaces import IPrincipleChecker
from domain.models import SolidPrinciple, SolidViolation


class OCPChecker(IPrincipleChecker):
    """Checker for Open-Closed Principle violations"""
    
    def get_principle(self) -> SolidPrinciple:
        """Return the principle this checker validates"""
        return SolidPrinciple.OPEN_CLOSED
    
    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List[SolidViolation]:
        """
        Analyze AST for OCP violations
        
        Args:
            tree: Python AST to analyze
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of detected violations
        """
        self.source_lines = source_lines
        violations: List[SolidViolation] = []
        
        visitor = OCPVisitor(self, violations)
        visitor.visit(tree)
        
        return violations
    
    def _get_code_snippet(self, line_number: int, context: int = 2) -> str:
        """Get code snippet around the given line number"""
        if not self.source_lines:
            return ""
        
        start = max(0, line_number - context - 1)
        end = min(len(self.source_lines), line_number + context)
        
        snippet_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_number - 1 else "   "
            snippet_lines.append(f"{marker} {i+1:4d}: {self.source_lines[i]}")
        
        return "\n".join(snippet_lines)


class OCPVisitor(ast.NodeVisitor):
    """AST visitor for detecting OCP violations"""
    
    def __init__(self, checker: OCPChecker, violations: List[SolidViolation]):
        self.checker = checker
        self.violations = violations
    
    def visit_If(self, node: ast.If) -> None:
        """Check if statements for type checking"""
        if self._is_type_checking_if(node):
            self.violations.append(SolidViolation(
                principle=SolidPrinciple.OPEN_CLOSED,
                severity="medium",
                line_number=node.lineno,
                message="Type checking detected - consider using polymorphism",
                suggestion="Replace type checks with polymorphic method calls or strategy pattern",
                code_snippet=self.checker._get_code_snippet(node.lineno)
            ))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check for long elif chains"""
        if_count = self._count_conditional_branches(node)
        if if_count > 5:
            self.violations.append(SolidViolation(
                principle=SolidPrinciple.OPEN_CLOSED,
                severity="low",
                line_number=node.lineno,
                message=f"Function '{node.name}' has {if_count} conditional branches",
                suggestion="Consider using strategy pattern or polymorphism",
                code_snippet=self.checker._get_code_snippet(node.lineno)
            ))
        
        self.generic_visit(node)
    
    def _is_type_checking_if(self, node: ast.If) -> bool:
        """Detect if this is a type-checking if statement"""
        if isinstance(node.test, ast.Call):
            # Check for isinstance() or type() calls
            if isinstance(node.test.func, ast.Name):
                if node.test.func.id in ['isinstance', 'type']:
                    return True
            # Check for __class__ attribute access
            if isinstance(node.test.func, ast.Attribute):
                if node.test.func.attr == '__class__':
                    return True
        return False
    
    def _count_conditional_branches(self, node: ast.FunctionDef) -> int:
        """Count the number of if/elif chains in a function"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                count += 1
        return count
