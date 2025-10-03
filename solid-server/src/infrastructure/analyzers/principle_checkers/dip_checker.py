"""
Dependency Inversion Principle Checker
======================================
Checks for DIP violations in Python code.
"""

import ast
from typing import List
from domain.interfaces import IPrincipleChecker
from domain.models import SolidPrinciple, SolidViolation


class DIPChecker(IPrincipleChecker):
    """
    Checks for Dependency Inversion Principle violations.
    Follows SRP - only checks for DIP violations.
    """

    def get_principle(self) -> SolidPrinciple:
        """Return the SOLID principle this checker validates."""
        return SolidPrinciple.DEPENDENCY_INVERSION

    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List[SolidViolation]:
        """
        Check for DIP violations in the AST.
        
        Checks for:
        - Classes creating their own dependencies in constructors
        - Direct instantiation instead of dependency injection
        - Tight coupling through hardcoded class instantiation
        
        Args:
            tree: AST of the Python file
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of DIP violations found
        """
        violations = []
        
        class DIPVisitor(ast.NodeVisitor):
            def __init__(self, checker, source_lines):
                self.checker = checker
                self.source_lines = source_lines
                
            def visit_ClassDef(self, node):
                # Check for direct instantiation in __init__
                init_method = None
                for item in node.body:
                    if (isinstance(item, ast.FunctionDef) and
                            item.name == '__init__'):
                        init_method = item
                        break
                
                if init_method:
                    self._check_constructor_dependencies(
                        init_method, node.name
                    )
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for hardcoded instantiations
                if (isinstance(node.func, ast.Name) and
                        node.func.id[0].isupper()):
                    
                    # Skip common built-ins
                    builtin_exceptions = [
                        'Exception', 'ValueError', 'TypeError',
                        'AttributeError', 'KeyError', 'IndexError',
                        'RuntimeError', 'NotImplementedError'
                    ]
                    
                    if node.func.id not in builtin_exceptions:
                        violations.append(SolidViolation(
                            principle=SolidPrinciple.DEPENDENCY_INVERSION,
                            severity="low",
                            line_number=node.lineno,
                            message=(
                                f"Direct instantiation of '{node.func.id}' "
                                f"creates tight coupling"
                            ),
                            suggestion=(
                                "Consider dependency injection or "
                                "factory pattern"
                            ),
                            code_snippet=self._get_code_snippet(
                                node.lineno
                            )
                        ))
                
                self.generic_visit(node)
            
            def _check_constructor_dependencies(
                self, init_method, class_name
            ):
                """Check constructor for DIP violations"""
                for stmt in init_method.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if (isinstance(target, ast.Attribute) and
                                isinstance(target.value, ast.Name) and
                                    target.value.id == 'self'):
                                
                                # Check if assigning direct instantiation
                                if (isinstance(stmt.value, ast.Call) and
                                    isinstance(stmt.value.func, ast.Name) and
                                        stmt.value.func.id[0].isupper()):
                                    
                                    violations.append(SolidViolation(
                                        principle=(
                                            SolidPrinciple.DEPENDENCY_INVERSION
                                        ),
                                        severity="medium",
                                        line_number=stmt.lineno,
                                        message=(
                                            f"'{class_name}' creates its own "
                                            f"dependencies in constructor"
                                        ),
                                        suggestion=(
                                            "Use dependency injection - pass "
                                            "dependencies as parameters"
                                        ),
                                        code_snippet=self._get_code_snippet(
                                            stmt.lineno
                                        )
                                    ))
            
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
        
        visitor = DIPVisitor(self, source_lines)
        visitor.visit(tree)
        return violations
