"""
Domain Interfaces
================
Core abstractions that define contracts for the domain.
Following Interface Segregation Principle - each interface is focused.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import ast


class IAnalyzer(ABC):
    """
    Abstract analyzer interface.
    Follows Liskov Substitution Principle - all implementations must
    be substitutable.
    """

    @abstractmethod
    def analyze_file(self, file_path: Path) -> 'SolidReport':
        """
        Analyze a Python file for SOLID principle violations.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            SolidReport containing violations and score
        """
        pass


class IPrincipleChecker(ABC):
    """
    Abstract principle checker interface.
    Enables Open-Closed Principle - new checkers can be added
    without modifying existing code.
    """

    @abstractmethod
    def check(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str
    ) -> List['SolidViolation']:
        """
        Check for violations of a specific SOLID principle.
        
        Args:
            tree: AST of the Python file
            source_lines: Source code lines for context
            file_path: Path to file being analyzed
            
        Returns:
            List of violations found
        """
        pass

    @abstractmethod
    def get_principle(self) -> 'SolidPrinciple':
        """Return the SOLID principle this checker validates."""
        pass


class IFormatter(ABC):
    """
    Abstract formatter interface.
    Supports multiple output formats following Open-Closed Principle.
    """

    @abstractmethod
    def format_file_report(
        self,
        report: 'SolidReport'
    ) -> str:
        """Format a single file report."""
        pass

    @abstractmethod
    def format_directory_report(
        self,
        reports: List['SolidReport'],
        summary: Dict[str, Any]
    ) -> str:
        """Format a directory analysis report."""
        pass

    @abstractmethod
    def format_suggestions(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Format refactoring suggestions."""
        pass
