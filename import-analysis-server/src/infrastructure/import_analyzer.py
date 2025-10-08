"""
Import Analyzer Implementation
=============================

Concrete implementation of import analysis using AST parsing.
"""

import ast
from pathlib import Path
from typing import List, Dict
import importlib.util

from domain.interfaces import ImportAnalyzerInterface
from domain.models import (
    ImportStatement, ImportIssue, ImportType, ImportIssueType,
    Severity, FileImportAnalysis, ProjectImportAnalysis, 
    CircularImportPath, ImportAnalysisOptions
)
from .dependency_resolver import DependencyResolver


class ImportAnalyzer(ImportAnalyzerInterface):
    """Concrete implementation of import analysis using AST"""
    
    def __init__(self, dependency_resolver: DependencyResolver):
        self.dependency_resolver = dependency_resolver
    
    def analyze_file(self, file_path: Path) -> FileImportAnalysis:
        """Analyze imports in a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = self._extract_imports(tree)
            issues = []
            
            # Validate each import
            for import_stmt in imports:
                import_stmt.is_valid = self.dependency_resolver.resolve_import(import_stmt, file_path)
                import_stmt.import_type = self._classify_import(import_stmt, file_path)
                
                # Check for various issues
                file_issues = self._check_import_issues(import_stmt, content, file_path)
                issues.extend(file_issues)
            
            # Check for unused imports
            unused_issues = self._check_unused_imports(imports, content)
            issues.extend(unused_issues)
            
            return FileImportAnalysis(
                file_path=file_path,
                imports=imports,
                issues=issues
            )
            
        except Exception as e:
            # Return analysis with error
            error_issue = ImportIssue(
                issue_type=ImportIssueType.MISSING_MODULE,
                severity=Severity.ERROR,
                message=f"Failed to parse file: {str(e)}",
                line_number=1,
                import_statement=ImportStatement(module="", names=[])
            )
            return FileImportAnalysis(
                file_path=file_path,
                imports=[],
                issues=[error_issue]
            )
    
    def analyze_project(self, project_root: Path, options: ImportAnalysisOptions) -> ProjectImportAnalysis:
        """Analyze imports across an entire project"""
        file_analyses = []
        
        # Find all Python files
        python_files = self._find_python_files(project_root, options)
        
        # Analyze each file
        for file_path in python_files[:options.max_files]:
            analysis = self.analyze_file(file_path)
            file_analyses.append(analysis)
        
        # Find circular imports
        circular_imports = []
        if options.check_circular_imports:
            circular_imports = self.find_circular_imports(python_files)
        
        # Check dependencies
        missing_deps, unused_deps = self._check_project_dependencies(
            file_analyses, project_root
        )
        
        return ProjectImportAnalysis(
            project_root=project_root,
            file_analyses=file_analyses,
            circular_imports=circular_imports,
            missing_dependencies=missing_deps,
            unused_dependencies=unused_deps
        )
    
    def find_circular_imports(self, files: List[Path]) -> List[CircularImportPath]:
        """Find circular import dependencies between files"""
        # Build dependency graph
        graph = {}
        
        for file_path in files:
            try:
                analysis = self.analyze_file(file_path)
                module_name = self._get_module_name(file_path)
                graph[module_name] = set()
                
                for import_stmt in analysis.imports:
                    if import_stmt.import_type in [ImportType.LOCAL_ABSOLUTE, ImportType.LOCAL_RELATIVE]:
                        graph[module_name].add(import_stmt.module)
                        
            except Exception:
                continue
        
        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle_modules = path[cycle_start:]
                cycles.append(CircularImportPath(modules=cycle_modules))
                return
            
            if node in visited or node not in graph:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for module in graph:
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportStatement]:
        """Extract import statements from AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportStatement(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        line_number=node.lineno
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                
                imports.append(ImportStatement(
                    module=module,
                    names=names,
                    level=node.level,
                    line_number=node.lineno
                ))
        
        return imports
    
    def _classify_import(self, import_stmt: ImportStatement, from_file: Path) -> ImportType:
        """Classify the type of import"""
        module = import_stmt.module
        
        if import_stmt.is_relative:
            return ImportType.LOCAL_RELATIVE
        
        if self.dependency_resolver.is_standard_library(module):
            return ImportType.STANDARD_LIBRARY
        
        if self.dependency_resolver.is_third_party(module):
            return ImportType.THIRD_PARTY
        
        # Check if it's a local module
        if self.dependency_resolver.get_module_path(module, from_file):
            return ImportType.LOCAL_ABSOLUTE
        
        return ImportType.UNKNOWN
    
    def _check_import_issues(self, import_stmt: ImportStatement, file_content: str, file_path: Path) -> List[ImportIssue]:
        """Check for various import-related issues"""
        issues = []
        
        # Check if import is invalid
        if not import_stmt.is_valid:
            if import_stmt.module:
                issue = ImportIssue(
                    issue_type=ImportIssueType.MISSING_MODULE,
                    severity=Severity.ERROR,
                    message=f"Cannot resolve import '{import_stmt.module}'",
                    line_number=import_stmt.line_number,
                    import_statement=import_stmt,
                    suggestion=f"Check if '{import_stmt.module}' is installed or spelled correctly"
                )
                issues.append(issue)
        
        # Check for wildcard imports
        if import_stmt.is_wildcard:
            issue = ImportIssue(
                issue_type=ImportIssueType.WILDCARD_IMPORT,
                severity=Severity.WARNING,
                message=f"Wildcard import from '{import_stmt.module}' should be avoided",
                line_number=import_stmt.line_number,
                import_statement=import_stmt,
                suggestion="Import specific names instead of using '*'"
            )
            issues.append(issue)
        
        # Check relative imports beyond package
        if import_stmt.is_relative and import_stmt.level > 1:
            package_depth = len([p for p in file_path.parts if not p.endswith('.py')])
            if import_stmt.level > package_depth:
                issue = ImportIssue(
                    issue_type=ImportIssueType.RELATIVE_IMPORT_BEYOND_PACKAGE,
                    severity=Severity.ERROR,
                    message=f"Relative import level {import_stmt.level} exceeds package depth",
                    line_number=import_stmt.line_number,
                    import_statement=import_stmt,
                    suggestion="Use absolute imports or reduce relative import level"
                )
                issues.append(issue)
        
        return issues
    
    def _check_unused_imports(self, imports: List[ImportStatement], file_content: str) -> List[ImportIssue]:
        """Check for unused imports"""
        issues = []
        
        for import_stmt in imports:
            if import_stmt.is_wildcard:
                continue  # Can't easily check wildcard imports
            
            # Check if import is used in the file
            names_to_check = []
            
            if import_stmt.names:
                # from module import name1, name2
                names_to_check = import_stmt.names
            else:
                # import module
                module_name = import_stmt.alias or import_stmt.module.split('.')[0]
                names_to_check = [module_name]
            
            for name in names_to_check:
                if not self._is_name_used(name, file_content):
                    issue = ImportIssue(
                        issue_type=ImportIssueType.UNUSED_IMPORT,
                        severity=Severity.WARNING,
                        message=f"Unused import '{name}'",
                        line_number=import_stmt.line_number,
                        import_statement=import_stmt,
                        suggestion=f"Remove unused import '{name}'"
                    )
                    issues.append(issue)
        
        return issues
    
    def _is_name_used(self, name: str, content: str) -> bool:
        """Check if a name is used in the file content"""
        # Simple heuristic - check if name appears in content
        # This is not perfect but works for most cases
        import re
        
        # Look for the name as a word boundary (not part of another word)
        pattern = r'\b' + re.escape(name) + r'\b'
        matches = re.findall(pattern, content)
        
        # Exclude the import line itself
        return len(matches) > 1
    
    def _find_python_files(self, root: Path, options: ImportAnalysisOptions) -> List[Path]:
        """Find Python files matching the criteria"""
        files = []
        
        for pattern in options.include_patterns:
            files.extend(root.rglob(pattern))
        
        # Filter out excluded patterns
        filtered_files = []
        for file_path in files:
            if any(excl in str(file_path) for excl in options.exclude_patterns):
                continue
            
            # Skip test files if requested
            if not options.include_test_files and 'test' in file_path.name.lower():
                continue
            
            filtered_files.append(file_path)
        
        return filtered_files
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        if file_path.name == "__init__.py":
            return str(file_path.parent).replace('/', '.').replace('\\', '.')
        else:
            return str(file_path.with_suffix('')).replace('/', '.').replace('\\', '.')
    
    def _check_project_dependencies(self, file_analyses: List[FileImportAnalysis], project_root: Path) -> tuple[List[str], List[str]]:
        """Check for missing and unused dependencies"""
        # Collect all third-party imports
        used_packages = set()
        for analysis in file_analyses:
            for import_stmt in analysis.imports:
                if import_stmt.import_type == ImportType.THIRD_PARTY:
                    # Get top-level package name
                    package = import_stmt.module.split('.')[0]
                    used_packages.add(package)
        
        # Get declared dependencies
        declared_deps = self._get_declared_dependencies(project_root)
        
        # Find missing and unused
        missing = list(used_packages - set(declared_deps.keys()))
        unused = [pkg for pkg in declared_deps if pkg not in used_packages]
        
        return missing, unused
    
    def _get_declared_dependencies(self, project_root: Path) -> Dict[str, str]:
        """Get declared dependencies from requirements files"""
        dependencies = {}
        
        # Check requirements.txt
        req_file = project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse package name (handle version specifiers)
                            import re
                            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                            if match:
                                dependencies[match.group(1)] = line
            except Exception:
                pass
        
        return dependencies