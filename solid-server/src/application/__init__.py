"""
Application Layer - Use Cases
=============================
Each use case represents a single business operation.
Following Single Responsibility Principle.
"""

from .analyze_file import AnalyzeFileUseCase
from .analyze_directory import AnalyzeDirectoryUseCase
from .generate_report import GenerateReportUseCase
from .suggest_refactoring import SuggestRefactoringUseCase

__all__ = [
    'AnalyzeFileUseCase',
    'AnalyzeDirectoryUseCase',
    'GenerateReportUseCase',
    'SuggestRefactoringUseCase',
]
