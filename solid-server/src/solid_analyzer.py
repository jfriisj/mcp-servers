"""
SOLID Principles Analyzer
========================
Analyzes Python code files for adherence to SOLID principles.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum


class SolidPrinciple(Enum):
    """SOLID principles enumeration"""
    SINGLE_RESPONSIBILITY = "SRP"
    OPEN_CLOSED = "OCP" 
    LISKOV_SUBSTITUTION = "LSP"
    INTERFACE_SEGREGATION = "ISP"
    DEPENDENCY_INVERSION = "DIP"


@dataclass
class SolidViolation:
    """Represents a violation of a SOLID principle"""
    principle: SolidPrinciple
    severity: str  # "high", "medium", "low"
    line_number: int
    message: str
    suggestion: str
    code_snippet: str


@dataclass
class SolidReport:
    """Complete SOLID analysis report for a file"""
    file_path: str
    violations: List[SolidViolation]
    score: float  # 0-100, higher is better
    summary: Dict[SolidPrinciple, int]  # violation count per principle


class SolidAnalyzer:
    """Main analyzer for SOLID principles"""
    
    def __init__(self):
        self.current_file_path = ""
        self.current_source_lines = []
    
    def analyze_file(self, file_path: Path) -> SolidReport:
        """Analyze a Python file for SOLID principles violations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            self.current_file_path = str(file_path)
            self.current_source_lines = source_code.splitlines()
            
            # Parse the AST
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return SolidReport(
                    file_path=str(file_path),
                    violations=[SolidViolation(
                        principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                        severity="high",
                        line_number=e.lineno or 1,
                        message=f"Syntax error: {e.msg}",
                        suggestion="Fix syntax errors before SOLID analysis",
                        code_snippet=self._get_code_snippet(e.lineno or 1)
                    )],
                    score=0.0,
                    summary={principle: 1 if principle == SolidPrinciple.SINGLE_RESPONSIBILITY else 0 
                            for principle in SolidPrinciple}
                )
            
            violations = []
            
            # Analyze each SOLID principle
            violations.extend(self._analyze_single_responsibility(tree))
            violations.extend(self._analyze_open_closed(tree))
            violations.extend(self._analyze_liskov_substitution(tree))
            violations.extend(self._analyze_interface_segregation(tree))
            violations.extend(self._analyze_dependency_inversion(tree))
            
            # Calculate score and summary
            score = self._calculate_score(violations)
            summary = self._calculate_summary(violations)
            
            return SolidReport(
                file_path=str(file_path),
                violations=violations,
                score=score,
                summary=summary
            )
            
        except Exception as e:
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
                summary={principle: 1 if principle == SolidPrinciple.SINGLE_RESPONSIBILITY else 0 
                        for principle in SolidPrinciple}
            )
    
    def _analyze_single_responsibility(self, tree: ast.AST) -> List[SolidViolation]:
        """Analyze Single Responsibility Principle violations"""
        violations = []
        
        class SRPVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_ClassDef(self, node):
                # Check for classes with too many responsibilities
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                responsibilities = self._analyze_class_responsibilities(node, methods)
                
                if len(responsibilities) > 3:  # Threshold for multiple responsibilities
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                        severity="medium",
                        line_number=node.lineno,
                        message=f"Class '{node.name}' has {len(responsibilities)} distinct responsibilities",
                        suggestion=f"Consider splitting into separate classes: {', '.join(responsibilities)}",
                        code_snippet=self.analyzer._get_code_snippet(node.lineno)
                    ))
                
                # Check for methods that are too long (possible SRP violation)
                for method in methods:
                    if method.name.startswith('_'):
                        continue  # Skip private methods
                        
                    method_lines = method.end_lineno - method.lineno if hasattr(method, 'end_lineno') else 10
                    if method_lines > 30:  # Long method threshold
                        violations.append(SolidViolation(
                            principle=SolidPrinciple.SINGLE_RESPONSIBILITY,
                            severity="low",
                            line_number=method.lineno,
                            message=f"Method '{method.name}' is too long ({method_lines} lines)",
                            suggestion="Consider breaking down into smaller methods",
                            code_snippet=self.analyzer._get_code_snippet(method.lineno)
                        ))
                
                self.generic_visit(node)
            
            def _analyze_class_responsibilities(self, class_node, methods):
                """Identify different responsibilities in a class"""
                responsibilities = set()
                
                # Analyze method names for different responsibility patterns
                for method in methods:
                    method_name = method.name.lower()
                    
                    # Data access patterns
                    if any(pattern in method_name for pattern in ['load', 'save', 'read', 'write', 'fetch']):
                        responsibilities.add("Data Access")
                    
                    # Business logic patterns
                    if any(pattern in method_name for pattern in ['calculate', 'compute', 'process', 'validate']):
                        responsibilities.add("Business Logic")
                    
                    # UI/Presentation patterns
                    if any(pattern in method_name for pattern in ['display', 'show', 'render', 'format']):
                        responsibilities.add("Presentation")
                    
                    # Communication patterns
                    if any(pattern in method_name for pattern in ['send', 'receive', 'notify', 'emit']):
                        responsibilities.add("Communication")
                
                return list(responsibilities)
        
        visitor = SRPVisitor(self)
        visitor.visit(tree)
        return violations
    
    def _analyze_open_closed(self, tree: ast.AST) -> List[SolidViolation]:
        """Analyze Open-Closed Principle violations"""
        violations = []
        
        class OCPVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_If(self, node):
                # Look for type checking that suggests OCP violation
                if self._is_type_checking_if(node):
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.OPEN_CLOSED,
                        severity="medium",
                        line_number=node.lineno,
                        message="Type checking detected - consider using polymorphism",
                        suggestion="Replace type checks with polymorphic method calls or strategy pattern",
                        code_snippet=self.analyzer._get_code_snippet(node.lineno)
                    ))
                
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                # Check for long elif chains that suggest OCP violation
                if_count = self._count_elif_chains(node)
                if if_count > 5:
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.OPEN_CLOSED,
                        severity="low",
                        line_number=node.lineno,
                        message=f"Function '{node.name}' has {if_count} conditional branches",
                        suggestion="Consider using strategy pattern or polymorphism",
                        code_snippet=self.analyzer._get_code_snippet(node.lineno)
                    ))
                
                self.generic_visit(node)
            
            def _is_type_checking_if(self, node):
                """Check if this is a type-checking if statement"""
                if isinstance(node.test, ast.Call):
                    if isinstance(node.test.func, ast.Name) and node.test.func.id in ['isinstance', 'type']:
                        return True
                    if isinstance(node.test.func, ast.Attribute) and node.test.func.attr == '__class__':
                        return True
                return False
            
            def _count_elif_chains(self, node):
                """Count the number of elif/if chains in a function"""
                count = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        count += 1
                return count
        
        visitor = OCPVisitor(self)
        visitor.visit(tree)
        return violations
    
    def _analyze_liskov_substitution(self, tree: ast.AST) -> List[SolidViolation]:
        """Analyze Liskov Substitution Principle violations"""
        violations = []
        
        class LSPVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.classes = {}
                
            def visit_ClassDef(self, node):
                # Store class information
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
                
            def visit_Raise(self, node):
                # Check for NotImplementedError in overridden methods
                if (isinstance(node.exc, ast.Call) and 
                    isinstance(node.exc.func, ast.Name) and 
                    node.exc.func.id == 'NotImplementedError'):
                    
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.LISKOV_SUBSTITUTION,
                        severity="high",
                        line_number=node.lineno,
                        message="NotImplementedError suggests LSP violation",
                        suggestion="Reconsider inheritance hierarchy - child should be substitutable for parent",
                        code_snippet=self.analyzer._get_code_snippet(node.lineno)
                    ))
                
                self.generic_visit(node)
        
        visitor = LSPVisitor(self)
        visitor.visit(tree)
        
        # Additional LSP checks after collecting all class info
        self._check_method_signature_compatibility(visitor.classes, violations)
        
        return violations
    
    def _analyze_interface_segregation(self, tree: ast.AST) -> List[SolidViolation]:
        """Analyze Interface Segregation Principle violations"""
        violations = []
        
        class ISPVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_ClassDef(self, node):
                # Count public methods (interface)
                public_methods = [m for m in node.body 
                                if isinstance(m, ast.FunctionDef) and not m.name.startswith('_')]
                
                if len(public_methods) > 10:  # Large interface threshold
                    violations.append(SolidViolation(
                        principle=SolidPrinciple.INTERFACE_SEGREGATION,
                        severity="medium",
                        line_number=node.lineno,
                        message=f"Class '{node.name}' has {len(public_methods)} public methods",
                        suggestion="Consider splitting into smaller, more focused interfaces",
                        code_snippet=self.analyzer._get_code_snippet(node.lineno)
                    ))
                
                # Check for empty method implementations (unused interface methods)
                for method in public_methods:
                    if self._is_empty_method(method):
                        violations.append(SolidViolation(
                            principle=SolidPrinciple.INTERFACE_SEGREGATION,
                            severity="low",
                            line_number=method.lineno,
                            message=f"Empty method '{method.name}' suggests interface bloat",
                            suggestion="Remove unused methods or split interface",
                            code_snippet=self.analyzer._get_code_snippet(method.lineno)
                        ))
                
                self.generic_visit(node)
            
            def _is_empty_method(self, method):
                """Check if method is effectively empty"""
                if len(method.body) == 1:
                    stmt = method.body[0]
                    return (isinstance(stmt, ast.Pass) or 
                           (isinstance(stmt, ast.Expr) and 
                            isinstance(stmt.value, ast.Constant)))
                return False
        
        visitor = ISPVisitor(self)
        visitor.visit(tree)
        return violations
    
    def _analyze_dependency_inversion(self, tree: ast.AST) -> List[SolidViolation]:
        """Analyze Dependency Inversion Principle violations"""
        violations = []
        
        class DIPVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_ClassDef(self, node):
                # Check for direct instantiation of concrete classes in __init__
                init_method = None
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        init_method = item
                        break
                
                if init_method:
                    self._check_constructor_dependencies(init_method, node.name, violations)
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for hardcoded instantiations
                if (isinstance(node.func, ast.Name) and 
                    node.func.id[0].isupper()):  # Likely a class name
                    
                    # Skip common built-ins that are acceptable
                    if node.func.id not in ['Exception', 'ValueError', 'TypeError', 'AttributeError']:
                        violations.append(SolidViolation(
                            principle=SolidPrinciple.DEPENDENCY_INVERSION,
                            severity="low",
                            line_number=node.lineno,
                            message=f"Direct instantiation of '{node.func.id}' creates tight coupling",
                            suggestion="Consider dependency injection or factory pattern",
                            code_snippet=self.analyzer._get_code_snippet(node.lineno)
                        ))
                
                self.generic_visit(node)
            
            def _check_constructor_dependencies(self, init_method, class_name, violations):
                """Check constructor for DIP violations"""
                for stmt in init_method.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if (isinstance(target, ast.Attribute) and 
                                isinstance(target.value, ast.Name) and 
                                target.value.id == 'self'):
                                
                                # Check if assigning a direct instantiation
                                if (isinstance(stmt.value, ast.Call) and 
                                    isinstance(stmt.value.func, ast.Name) and
                                    stmt.value.func.id[0].isupper()):
                                    
                                    violations.append(SolidViolation(
                                        principle=SolidPrinciple.DEPENDENCY_INVERSION,
                                        severity="medium",
                                        line_number=stmt.lineno,
                                        message=f"'{class_name}' creates its own dependencies in constructor",
                                        suggestion="Use dependency injection - pass dependencies as parameters",
                                        code_snippet=self.analyzer._get_code_snippet(stmt.lineno)
                                    ))
        
        visitor = DIPVisitor(self)
        visitor.visit(tree)
        return violations
    
    def _check_method_signature_compatibility(self, classes: Dict, violations: List[SolidViolation]):
        """Check for LSP violations in method signatures"""
        for class_name, class_info in classes.items():
            for base_class in class_info['bases']:
                if base_class in classes:
                    # Compare method signatures
                    base_methods = classes[base_class]['methods']
                    child_methods = class_info['methods']
                    
                    for method_name, base_method_info in base_methods.items():
                        if method_name in child_methods:
                            child_method_info = child_methods[method_name]
                            
                            # Check parameter count
                            if len(child_method_info['args']) != len(base_method_info['args']):
                                violations.append(SolidViolation(
                                    principle=SolidPrinciple.LISKOV_SUBSTITUTION,
                                    severity="high",
                                    line_number=child_method_info['node'].lineno,
                                    message=f"Method '{method_name}' signature differs from base class",
                                    suggestion="Ensure method signatures match parent class for substitutability",
                                    code_snippet=self._get_code_snippet(child_method_info['node'].lineno)
                                ))
    
    def _get_code_snippet(self, line_number: int, context: int = 2) -> str:
        """Get a code snippet around the given line number"""
        if not self.current_source_lines:
            return ""
        
        start = max(0, line_number - context - 1)
        end = min(len(self.current_source_lines), line_number + context)
        
        lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_number - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.current_source_lines[i]}")
        
        return "\n".join(lines)
    
    def _calculate_score(self, violations: List[SolidViolation]) -> float:
        """Calculate overall SOLID score (0-100)"""
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {"high": 10, "medium": 5, "low": 2}
        total_penalty = sum(severity_weights.get(v.severity, 2) for v in violations)
        
        # Convert to score (higher is better)
        base_score = 100
        penalty_factor = min(total_penalty, 100)  # Cap penalty at 100
        
        return max(0.0, base_score - penalty_factor)
    
    def _calculate_summary(self, violations: List[SolidViolation]) -> Dict[SolidPrinciple, int]:
        """Calculate violation summary by principle"""
        summary = {principle: 0 for principle in SolidPrinciple}
        
        for violation in violations:
            summary[violation.principle] += 1
        
        return summary


class SolidBatchAnalyzer:
    """Batch analyzer for multiple files"""
    
    def __init__(self):
        self.analyzer = SolidAnalyzer()
    
    def analyze_directory(self, directory_path: Path, 
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None) -> List[SolidReport]:
        """Analyze all Python files in a directory"""
        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", ".git", ".venv", "venv", "test_*"]
        
        reports = []
        
        # Find all Python files
        for pattern in include_patterns:
            for file_path in directory_path.rglob(pattern):
                # Check exclusions
                if any(exclude in str(file_path) for exclude in exclude_patterns):
                    continue
                
                if file_path.is_file():
                    report = self.analyzer.analyze_file(file_path)
                    reports.append(report)
        
        return reports
    
    def generate_summary_report(self, reports: List[SolidReport]) -> Dict[str, Any]:
        """Generate a summary report from multiple file reports"""
        if not reports:
            return {
                "total_files": 0,
                "average_score": 0.0,
                "total_violations": 0,
                "violations_by_principle": {p.value: 0 for p in SolidPrinciple},
                "files_with_violations": 0
            }
        
        total_violations = sum(len(r.violations) for r in reports)
        average_score = sum(r.score for r in reports) / len(reports)
        files_with_violations = sum(1 for r in reports if r.violations)
        
        violations_by_principle = {p.value: 0 for p in SolidPrinciple}
        for report in reports:
            for principle, count in report.summary.items():
                violations_by_principle[principle.value] += count
        
        return {
            "total_files": len(reports),
            "average_score": round(average_score, 1),
            "total_violations": total_violations,
            "violations_by_principle": violations_by_principle,
            "files_with_violations": files_with_violations,
            "worst_files": sorted(reports, key=lambda r: r.score)[:5],
            "best_files": sorted(reports, key=lambda r: r.score, reverse=True)[:5]
        }