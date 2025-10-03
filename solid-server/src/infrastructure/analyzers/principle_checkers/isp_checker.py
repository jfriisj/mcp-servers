"""
Interface Segregation Principle Checker

Detects violations of the Interface Segregation Principle:
- Fat interfaces (too many public methods)
- Empty method implementations (unused interface methods)
"""

import ast
from typing import List
from domain.interfaces import IPrincipleChecker
from domain.models import SolidPrinciple, SolidViolation


class ISPChecker(IPrincipleChecker):
    """Checker for Interface Segregation Principle violations"""
    
    def get_principle(self) -> SolidPrinciple:
        """Return the principle this checker validates"""
        return SolidPrinciple.INTERFACE_SEGREGATION
    
    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List[SolidViolation]:
        """
        Analyze AST for ISP violations
        
        Args:
            tree: Python AST to analyze
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of detected violations
        """
        self.source_lines = source_lines
        violations: List[SolidViolation] = []
        
        visitor = ISPVisitor(self, violations)
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


class ISPVisitor(ast.NodeVisitor):
    """AST visitor for detecting ISP violations"""
    
    def __init__(self, checker: ISPChecker, violations: List[SolidViolation]):
        self.checker = checker
        self.violations = violations
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check for fat interfaces and empty methods"""
        # Count public methods (interface)
        public_methods = [
            m for m in node.body 
            if isinstance(m, ast.FunctionDef) and not m.name.startswith('_')
        ]
        
        # Check for fat interface (>10 public methods)
        if len(public_methods) > 10:
            self.violations.append(SolidViolation(
                principle=SolidPrinciple.INTERFACE_SEGREGATION,
                severity="medium",
                line_number=node.lineno,
                message=f"Class '{node.name}' has {len(public_methods)} public methods",
                suggestion="Consider splitting into smaller, more focused interfaces",
                code_snippet=self.checker._get_code_snippet(node.lineno)
            ))
        
        # Check for empty method implementations (unused interface methods)
        for method in public_methods:
            if self._is_empty_method(method):
                self.violations.append(SolidViolation(
                    principle=SolidPrinciple.INTERFACE_SEGREGATION,
                    severity="low",
                    line_number=method.lineno,
                    message=f"Empty method '{method.name}' suggests interface bloat",
                    suggestion="Remove unused methods or split interface",
                    code_snippet=self.checker._get_code_snippet(method.lineno)
                ))
        
        self.generic_visit(node)
    
    def _is_empty_method(self, method: ast.FunctionDef) -> bool:
        """Check if method is effectively empty (pass or docstring only)"""
        if len(method.body) == 1:
            stmt = method.body[0]
            # Check for pass statement
            if isinstance(stmt, ast.Pass):
                return True
            # Check for docstring only (Expr with Constant)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                return True
        return False
