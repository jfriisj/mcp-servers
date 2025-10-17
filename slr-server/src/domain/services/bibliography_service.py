"""
Bibliography Service Interface

Defines the contract for bibliography processing operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..domain.models import ResearchPaper


class IBibliographyService(ABC):
    """
    Interface for bibliography processing operations.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles bibliography processing
    - Interface Segregation: Focused interface for bibliography operations  
    - Dependency Inversion: Abstract interface, not concrete implementation
    """
    
    @abstractmethod
    def parse_bibtex(self, file_path: str) -> List[ResearchPaper]:
        """Parse BibTeX file and extract papers."""
        pass
    
    @abstractmethod
    def parse_ris(self, file_path: str) -> List[ResearchPaper]:
        """Parse RIS file and extract papers."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from bibliography file."""
        pass
    
    @abstractmethod
    def validate_bibliography(self, file_path: str) -> Dict[str, Any]:
        """Validate bibliography file format and content."""
        pass