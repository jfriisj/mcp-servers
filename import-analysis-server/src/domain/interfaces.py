"""
Domain Interfaces for Import Testing
===================================

Abstract interfaces defining the contracts for import analysis components.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional

from domain.models import (
    ImportStatement, ImportIssue, FileImportAnalysis, 
    ProjectImportAnalysis, CircularImportPath, DependencyInfo,
    ImportAnalysisOptions, ExportInfo
)


class ImportAnalyzerInterface(ABC):
    """Interface for analyzing imports in Python files"""
    
    @abstractmethod
    def analyze_file(self, file_path: Path) -> FileImportAnalysis:
        """Analyze imports in a single Python file"""
        pass
    
    @abstractmethod
    def analyze_project(self, project_root: Path, options: ImportAnalysisOptions) -> ProjectImportAnalysis:
        """Analyze imports across an entire project"""
        pass
    
    @abstractmethod
    def find_circular_imports(self, files: List[Path]) -> List[CircularImportPath]:
        """Find circular import dependencies between files"""
        pass


class DependencyResolverInterface(ABC):
    """Interface for resolving and validating dependencies"""
    
    @abstractmethod
    def resolve_import(self, import_stmt: ImportStatement, from_file: Path) -> bool:
        """Check if an import can be resolved"""
        pass
    
    @abstractmethod
    def get_module_path(self, module_name: str, from_file: Path) -> Optional[Path]:
        """Get the file path for a module"""
        pass
    
    @abstractmethod
    def is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of Python standard library"""
        pass
    
    @abstractmethod
    def is_third_party(self, module_name: str) -> bool:
        """Check if module is a third-party package"""
        pass
    
    @abstractmethod
    def get_installed_packages(self) -> Dict[str, DependencyInfo]:
        """Get information about installed packages"""
        pass


class ExportAnalyzerInterface(ABC):
    """Interface for analyzing module exports"""
    
    @abstractmethod
    def analyze_exports(self, file_path: Path) -> ExportInfo:
        """Analyze what a module exports"""
        pass
    
    @abstractmethod
    def check_export_availability(self, module_path: Path, export_name: str) -> bool:
        """Check if a specific export is available from a module"""
        pass


class ImportFormatterInterface(ABC):
    """Interface for formatting import analysis results"""
    
    @abstractmethod
    def format_file_analysis(self, analysis: FileImportAnalysis) -> str:
        """Format single file analysis result"""
        pass
    
    @abstractmethod
    def format_project_analysis(self, analysis: ProjectImportAnalysis) -> str:
        """Format project-wide analysis result"""
        pass
    
    @abstractmethod
    def format_issues_report(self, issues: List[ImportIssue]) -> str:
        """Format a list of import issues"""
        pass
    
    @abstractmethod
    def format_circular_imports(self, circular_imports: List[CircularImportPath]) -> str:
        """Format circular import report"""
        pass


class ImportFixerInterface(ABC):
    """Interface for automatically fixing import issues"""
    
    @abstractmethod
    def fix_unused_imports(self, file_path: Path) -> List[str]:
        """Remove unused imports from a file"""
        pass
    
    @abstractmethod
    def fix_import_order(self, file_path: Path) -> bool:
        """Fix import ordering in a file"""
        pass
    
    @abstractmethod
    def suggest_fixes(self, issues: List[ImportIssue]) -> Dict[str, str]:
        """Suggest fixes for import issues"""
        pass