"""
Analyze Imports Use Case
=======================

Use case for analyzing imports in Python files.
"""

from pathlib import Path
from typing import Optional

from domain.models import FileImportAnalysis, ImportAnalysisOptions
from infrastructure.import_analyzer import ImportAnalyzer


class AnalyzeImportsUseCase:
    """Use case for analyzing imports in files"""
    
    def __init__(self, import_analyzer: ImportAnalyzer):
        self.import_analyzer = import_analyzer
    
    def execute(self, file_path: Path, options: Optional[ImportAnalysisOptions] = None) -> FileImportAnalysis:
        """Execute import analysis for a single file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix == '.py':
            raise ValueError(f"Only Python files are supported: {file_path}")
        
        return self.import_analyzer.analyze_file(file_path)