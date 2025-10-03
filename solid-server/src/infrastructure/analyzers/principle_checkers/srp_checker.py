"""
Single Responsibility Principle Checker
========================================
Checks for SRP violations in Python code.
"""

import ast
from typing import List
from domain.interfaces import IPrincipleChecker
from domain.models import SolidPrinciple, SolidViolation


class SRPChecker(IPrincipleChecker):
    """
    Checks for Single Responsibility Principle violations.
    Follows SRP itself - only checks for SRP violations.
    """

    def get_principle(self) -> SolidPrinciple:
        """Return the SOLID principle this checker validates."""
        return SolidPrinciple.SINGLE_RESPONSIBILITY

    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List[SolidViolation]:
        """
        Check for SRP violations in the AST.
        
        Checks for:
        - Classes with too many distinct responsibilities
        - Methods that are too long (possible mixed concerns)
        
        Args:
            tree: AST of the Python file
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of SRP violations found
        """
        violations = []
        
        class SRPVisitor(ast.NodeVisitor):
            def __init__(self, checker, source_lines):
                self.checker = checker
                self.source_lines = source_lines
                
            def visit_ClassDef(self, node):
                # Check for classes with too many responsibilities
                methods = [
                    n for n in node.body
                    if isinstance(n, ast.FunctionDef)
                ]
                responsibilities = self._analyze_class_responsibilities(
                    node, methods
                )
                
                if len(responsibilities) > 3:
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                        severity="medium",
                        line_number=node.lineno,
                        message=(
                            f"Class '{node.name}' has "
                            f"{len(responsibilities)} distinct "
                            f"responsibilities"
                        ),
                        suggestion=(
                            f"Consider splitting into separate classes: "
                            f"{', '.join(responsibilities)}"
                        ),
                        code_snippet=self._get_code_snippet(node.lineno)
                    ))
                
                # Check for methods that are too long
                for method in methods:
                    if method.name.startswith('_'):
                        continue  # Skip private methods
                        
                    method_lines = (
                        method.end_lineno - method.lineno
                        if hasattr(method, 'end_lineno')
                        else 10
                    )
                    if method_lines > 30:  # Long method threshold
                        violations.append(SolidViolation(
                            principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                            severity="low",
                            line_number=method.lineno,
                            message=(
                                f"Method '{method.name}' is too long "
                                f"({method_lines} lines)"
                            ),
                            suggestion=(
                                "Consider breaking down into smaller methods"
                            ),
                            code_snippet=self._get_code_snippet(
                                method.lineno
                            )
                        ))
                
                self.generic_visit(node)
            
            def _analyze_class_responsibilities(self, class_node, methods):
                """Identify different responsibilities in a class"""
                responsibilities = set()
                
                for method in methods:
                    method_name = method.name.lower()
                    
                    # Data access patterns
                    if any(
                        pattern in method_name
                        for pattern in [
                            'load', 'save', 'read',
                            'write', 'fetch'
                        ]
                    ):
                        responsibilities.add("Data Access")
                    
                    # Business logic patterns
                    if any(
                        pattern in method_name
                        for pattern in [
                            'calculate', 'compute',
                            'process', 'validate'
                        ]
                    ):
                        responsibilities.add("Business Logic")
                    
                    # UI/Presentation patterns
                    if any(
                        pattern in method_name
                        for pattern in [
                            'display', 'show',
                            'render', 'format'
                        ]
                    ):
                        responsibilities.add("Presentation")
                    
                    # Communication patterns
                    if any(
                        pattern in method_name
                        for pattern in [
                            'send', 'receive',
                            'notify', 'emit'
                        ]
                    ):
                        responsibilities.add("Communication")
                
                return list(responsibilities)
            
            def _get_code_snippet(
                self, line_number: int, context: int = 2
            ) -> str:
                """Get a code snippet around the given line number"""
                if not self.source_lines:
                    return ""
                
                start = max(0, line_number - context - 1)
                end = min(
                    len(self.source_lines),
                    line_number + context
                )
                
                lines = []
                for i in range(start, end):
                    marker = ">>>" if i == line_number - 1 else "   "
                    lines.append(
                        f"{marker} {i+1:3d}: {self.source_lines[i]}"
                    )
                
                return "\n".join(lines)
        
        visitor = SRPVisitor(self, source_lines)
        visitor.visit(tree)
        return violations
