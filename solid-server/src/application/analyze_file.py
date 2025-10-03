"""
Analyze File Use Case
====================
Single responsibility: Coordinate the analysis of a single Python file.
"""

from pathlib import Path
from domain.interfaces import IAnalyzer
from domain.models import SolidReport


class AnalyzeFileUseCase:
    """
    Use case for analyzing a single file.
    Depends on IAnalyzer abstraction (Dependency Inversion Principle).
    """

    def __init__(self, analyzer: IAnalyzer):
        """
        Initialize with analyzer dependency.
        
        Args:
            analyzer: Implementation of IAnalyzer interface
        """
        self._analyzer = analyzer

    def execute(self, file_path: Path) -> SolidReport:
        """
        Execute the use case: analyze a single file.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            SolidReport containing analysis results
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a Python file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix != '.py':
            raise ValueError(
                f"Only Python files supported. Got: {file_path.suffix}"
            )
        
        return self._analyzer.analyze_file(file_path)
