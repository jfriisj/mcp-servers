"""
Domain Models for Import Testing
===============================

Core domain entities and value objects for import analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Set


class ImportType(Enum):
    """Type of import statement"""
    STANDARD_LIBRARY = "standard_library"
    THIRD_PARTY = "third_party" 
    LOCAL_RELATIVE = "local_relative"
    LOCAL_ABSOLUTE = "local_absolute"
    UNKNOWN = "unknown"


class ImportIssueType(Enum):
    """Types of import-related issues"""
    MISSING_MODULE = "missing_module"
    MISSING_ATTRIBUTE = "missing_attribute"
    CIRCULAR_IMPORT = "circular_import"
    UNUSED_IMPORT = "unused_import"
    WILDCARD_IMPORT = "wildcard_import"
    RELATIVE_IMPORT_BEYOND_PACKAGE = "relative_import_beyond_package"
    INCONSISTENT_IMPORT_STYLE = "inconsistent_import_style"
    IMPORT_ORDER_VIOLATION = "import_order_violation"
    SHADOWED_IMPORT = "shadowed_import"
    DEPRECATED_MODULE = "deprecated_module"


class Severity(Enum):
    """Severity levels for import issues"""
    ERROR = "error"
    WARNING = "warning" 
    INFO = "info"


@dataclass
class ImportStatement:
    """Represents a single import statement"""
    module: str
    names: List[str]  # Empty for 'import module', filled for 'from module import names'
    alias: Optional[str] = None
    level: int = 0  # Relative import level (0 for absolute)
    line_number: int = 0
    import_type: ImportType = ImportType.UNKNOWN
    is_valid: bool = False
    
    @property
    def is_relative(self) -> bool:
        """Check if this is a relative import"""
        return self.level > 0
    
    @property
    def is_wildcard(self) -> bool:
        """Check if this is a wildcard import"""
        return "*" in self.names
    
    @property
    def full_name(self) -> str:
        """Get full import name for display"""
        if self.names:
            names_str = ", ".join(self.names)
            return f"from {self.module} import {names_str}"
        return f"import {self.module}"


@dataclass
class ImportIssue:
    """Represents an issue with an import"""
    issue_type: ImportIssueType
    severity: Severity
    message: str
    line_number: int
    import_statement: ImportStatement
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Line {self.line_number}: [{self.severity.value.upper()}] {self.message}"


@dataclass
class ExportInfo:
    """Information about module exports"""
    module_path: Path
    explicit_exports: List[str] = field(default_factory=list)  # __all__ contents
    implicit_exports: List[str] = field(default_factory=list)  # All public names
    has_init_file: bool = False
    init_exports: List[str] = field(default_factory=list)  # __init__.py exports
    
    @property
    def all_exports(self) -> List[str]:
        """Get all available exports (explicit takes precedence)"""
        return self.explicit_exports if self.explicit_exports else self.implicit_exports


@dataclass
class DependencyInfo:
    """Information about project dependencies"""
    name: str
    version: Optional[str] = None
    is_installed: bool = False
    is_dev_dependency: bool = False
    source: str = ""  # requirements.txt, pyproject.toml, etc.
    
    def __str__(self) -> str:
        version_str = f"=={self.version}" if self.version else ""
        status = "✅" if self.is_installed else "❌"
        return f"{status} {self.name}{version_str}"


@dataclass
class CircularImportPath:
    """Represents a circular import cycle"""
    modules: List[str]
    severity: Severity = Severity.ERROR
    
    @property
    def cycle_description(self) -> str:
        """Get human-readable cycle description"""
        return " → ".join(self.modules + [self.modules[0]])
    
    def __str__(self) -> str:
        return f"Circular import: {self.cycle_description}"


@dataclass
class FileImportAnalysis:
    """Analysis result for a single file's imports"""
    file_path: Path
    imports: List[ImportStatement] = field(default_factory=list)
    issues: List[ImportIssue] = field(default_factory=list)
    exports: Optional[ExportInfo] = None
    
    @property
    def valid_imports_count(self) -> int:
        """Count of valid imports"""
        return len([imp for imp in self.imports if imp.is_valid])
    
    @property
    def invalid_imports_count(self) -> int:
        """Count of invalid imports"""
        return len(self.imports) - self.valid_imports_count
    
    @property
    def error_count(self) -> int:
        """Count of error-level issues"""
        return len([issue for issue in self.issues if issue.severity == Severity.ERROR])
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level issues"""
        return len([issue for issue in self.issues if issue.severity == Severity.WARNING])
    
    @property
    def health_score(self) -> float:
        """Calculate import health score (0-100)"""
        if not self.imports:
            return 100.0
        
        base_score = (self.valid_imports_count / len(self.imports)) * 100
        
        # Deduct points for issues
        error_penalty = self.error_count * 10
        warning_penalty = self.warning_count * 5
        
        final_score = max(0, base_score - error_penalty - warning_penalty)
        return round(final_score, 1)


@dataclass
class ProjectImportAnalysis:
    """Analysis result for entire project's imports"""
    project_root: Path
    file_analyses: List[FileImportAnalysis] = field(default_factory=list)
    circular_imports: List[CircularImportPath] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    unused_dependencies: List[str] = field(default_factory=list)
    dependency_info: Dict[str, DependencyInfo] = field(default_factory=dict)
    
    @property
    def total_files(self) -> int:
        """Total number of files analyzed"""
        return len(self.file_analyses)
    
    @property
    def total_imports(self) -> int:
        """Total number of imports across all files"""
        return sum(len(analysis.imports) for analysis in self.file_analyses)
    
    @property
    def total_valid_imports(self) -> int:
        """Total number of valid imports"""
        return sum(analysis.valid_imports_count for analysis in self.file_analyses)
    
    @property
    def total_issues(self) -> int:
        """Total number of issues found"""
        return sum(len(analysis.issues) for analysis in self.file_analyses)
    
    @property
    def overall_health_score(self) -> float:
        """Calculate overall project import health score"""
        if not self.file_analyses:
            return 100.0
        
        total_score = sum(analysis.health_score for analysis in self.file_analyses)
        average_score = total_score / len(self.file_analyses)
        
        # Apply penalties for project-level issues
        circular_penalty = len(self.circular_imports) * 5
        missing_deps_penalty = len(self.missing_dependencies) * 3
        
        final_score = max(0, average_score - circular_penalty - missing_deps_penalty)
        return round(final_score, 1)
    
    @property
    def success_rate(self) -> float:
        """Calculate import success rate percentage"""
        if self.total_imports == 0:
            return 100.0
        return round((self.total_valid_imports / self.total_imports) * 100, 1)


@dataclass
class ImportAnalysisOptions:
    """Configuration options for import analysis"""
    check_circular_imports: bool = True
    check_unused_imports: bool = True  
    check_import_order: bool = True
    check_wildcard_imports: bool = True
    check_relative_imports: bool = True
    include_test_files: bool = True
    max_files: int = 1000
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "node_modules"
    ])
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])


# Type aliases for better code readability
ImportMap = Dict[str, List[ImportStatement]]
ModulePath = str
CircularImportGraph = Dict[ModulePath, Set[ModulePath]]