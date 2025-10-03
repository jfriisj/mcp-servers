"""
Liskov Substitution Principle Checker

Detects violations of the Liskov Substitution Principle:
- NotImplementedError in overridden methods
- Method signature mismatches between parent and child classes
"""

import ast
from typing import List, Dict, Any
from domain.interfaces import IPrincipleChecker
from domain.models import SolidPrinciple, SolidViolation


class LSPChecker(IPrincipleChecker):
    """Checker for Liskov Substitution Principle violations"""
    
    def get_principle(self) -> SolidPrinciple:
        """Return the principle this checker validates"""
        return SolidPrinciple.LISKOV_SUBSTITUTION
    
    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List[SolidViolation]:
        """
        Analyze AST for LSP violations
        
        Args:
            tree: Python AST to analyze
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of detected violations
        """
        self.source_lines = source_lines
        violations: List[SolidViolation] = []
        
        visitor = LSPVisitor(self, violations)
        visitor.visit(tree)
        
        # Check method signature compatibility after collecting all classes
        self._check_method_signature_compatibility(visitor.classes, violations)
        
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
    
    def _check_method_signature_compatibility(
        self, 
        classes: Dict[str, Dict[str, Any]], 
        violations: List[SolidViolation]
    ) -> None:
        """Check for LSP violations in method signatures between parent/child classes"""
        for class_name, class_info in classes.items():
            for base_class in class_info['bases']:
                if base_class in classes:
                    # Compare method signatures
                    base_methods = classes[base_class]['methods']
                    child_methods = class_info['methods']
                    
                    for method_name, base_method_info in base_methods.items():
                        if method_name in child_methods:
                            child_method_info = child_methods[method_name]
                            
                            # Check parameter count (different signature = LSP violation)
                            if len(child_method_info['args']) != len(base_method_info['args']):
                                violations.append(SolidViolation(
                                    principle=SolidPrinciple.LISKOV_SUBSTITUTION,
                                    severity="high",
                                    line_number=child_method_info['node'].lineno,
                                    message=f"Method '{method_name}' signature differs from base class",
                                    suggestion="Ensure method signatures match parent class for substitutability",
                                    code_snippet=self._get_code_snippet(child_method_info['node'].lineno)
                                ))


class LSPVisitor(ast.NodeVisitor):
    """AST visitor for detecting LSP violations"""
    
    def __init__(self, checker: LSPChecker, violations: List[SolidViolation]):
        self.checker = checker
        self.violations = violations
        self.classes: Dict[str, Dict[str, Any]] = {}
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect class hierarchy information"""
        # Store class information for later analysis
        base_classes = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.classes[node.name] = {
            'bases': base_classes,
            'methods': {},
            'node': node
        }
        
        # Collect method signatures
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.classes[node.name]['methods'][item.name] = {
                    'args': [arg.arg for arg in item.args.args],
                    'node': item
                }
        
        self.generic_visit(node)
    
    def visit_Raise(self, node: ast.Raise) -> None:
        """Check for NotImplementedError (LSP violation indicator)"""
        if (isinstance(node.exc, ast.Call) and 
            isinstance(node.exc.func, ast.Name) and 
            node.exc.func.id == 'NotImplementedError'):
            
            self.violations.append(SolidViolation(
                principle=SolidPrinciple.LISKOV_SUBSTITUTION,
                severity="high",
                line_number=node.lineno,
                message="NotImplementedError suggests LSP violation",
                suggestion="Reconsider inheritance hierarchy - child should be substitutable for parent",
                code_snippet=self.checker._get_code_snippet(node.lineno)
            ))
        
        self.generic_visit(node)
