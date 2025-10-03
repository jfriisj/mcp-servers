"""
Analyze Directory Use Case
==========================
Single responsibility: Coordinate analysis of all Python files in a directory.
"""

from pathlib import Path
from typing import List
from dataclasses import dataclass
from domain.interfaces import IAnalyzer
from domain.models import SolidReport


@dataclass
class DirectoryFilters:
    """Filters for directory analysis"""
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_files: int = 100

    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = ["*.py"]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "__pycache__", ".git", ".venv", "venv", "test_*"
            ]


class AnalyzeDirectoryUseCase:
    """
    Use case for analyzing a directory of Python files.
    Depends on IAnalyzer abstraction (Dependency Inversion Principle).
    """

    def __init__(self, analyzer: IAnalyzer):
        """
        Initialize with analyzer dependency.
        
        Args:
            analyzer: Implementation of IAnalyzer interface
        """
        self._analyzer = analyzer

    def execute(
        self,
        directory_path: Path,
        filters: DirectoryFilters = None
    ) -> List[SolidReport]:
        """
        Execute the use case: analyze all Python files in directory.
        
        Args:
            directory_path: Path to directory to analyze
            filters: Optional filters for file selection
            
        Returns:
            List of SolidReports, one per analyzed file
            
        Raises:
            NotADirectoryError: If path is not a directory
        """
        if not directory_path.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {directory_path}"
            )
        
        if filters is None:
            filters = DirectoryFilters()
        
        # Find Python files
        files = self._find_python_files(directory_path, filters)
        
        # Analyze each file
        reports = []
        for file_path in files:
            try:
                report = self._analyzer.analyze_file(file_path)
                reports.append(report)
            except Exception:
                # Skip files that can't be analyzed
                continue
        
        return reports

    def _find_python_files(
        self,
        directory: Path,
        filters: DirectoryFilters
    ) -> List[Path]:
        """
        Find Python files in directory applying filters.
        
        Args:
            directory: Directory to search
            filters: Filters to apply
            
        Returns:
            List of Path objects to Python files
        """
        files = []
        
        for pattern in filters.include_patterns:
            for file_path in directory.rglob(pattern):
                # Check exclusions
                if any(
                    excl in str(file_path)
                    for excl in filters.exclude_patterns
                ):
                    continue
                
                files.append(file_path)
                
                # Respect max files limit
                if len(files) >= filters.max_files:
                    break
            
            if len(files) >= filters.max_files:
                break
        
        return files
