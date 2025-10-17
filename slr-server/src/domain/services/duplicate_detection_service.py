"""
Duplicate Detection Service Interface

Defines the contract for duplicate paper detection operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ..domain.models import ResearchPaper


class IDuplicateDetectionService(ABC):
    """
    Interface for duplicate detection operations.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles duplicate detection
    - Interface Segregation: Focused interface for duplicate operations
    - Dependency Inversion: Abstract interface, not concrete implementation
    """
    
    @abstractmethod
    def detect_duplicates(self, papers: List[ResearchPaper], 
                         similarity_threshold: float = 0.85) -> List[List[ResearchPaper]]:
        """Detect duplicate papers based on similarity."""
        pass
    
    @abstractmethod
    def calculate_similarity(self, paper1: ResearchPaper, 
                           paper2: ResearchPaper) -> float:
        """Calculate similarity score between two papers."""
        pass
    
    @abstractmethod
    def find_potential_duplicates(self, target_paper: ResearchPaper, 
                                 corpus: List[ResearchPaper]) -> List[Tuple[ResearchPaper, float]]:
        """Find potential duplicates for a target paper in a corpus."""
        pass
    
    @abstractmethod
    def remove_duplicates(self, papers: List[ResearchPaper], 
                         similarity_threshold: float = 0.85) -> List[ResearchPaper]:
        """Remove duplicates from a list of papers."""
        pass