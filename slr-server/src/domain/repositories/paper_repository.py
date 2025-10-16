"""
Paper Repository Interface

Defines the contract for paper data access operations following DIP.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import ResearchPaper


class IPaperRepository(ABC):
    """
    Interface for paper repository operations.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles paper data access
    - Interface Segregation: Focused interface for paper operations
    - Dependency Inversion: Abstract interface, not concrete implementation
    """
    
    @abstractmethod
    def create(self, paper: ResearchPaper) -> ResearchPaper:
        """Create a new research paper."""
        pass
    
    @abstractmethod
    def get_by_id(self, paper_id: int) -> Optional[ResearchPaper]:
        """Retrieve paper by ID."""
        pass
    
    @abstractmethod
    def update(self, paper: ResearchPaper) -> ResearchPaper:
        """Update existing paper."""
        pass
    
    @abstractmethod
    def delete(self, paper_id: int) -> bool:
        """Delete paper by ID."""
        pass
    
    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[ResearchPaper]:
        """List papers with optional filters."""
        pass
    
    @abstractmethod
    def search_papers(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[ResearchPaper]:
        """Search papers by query."""
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count papers matching filters."""
        pass
    
    @abstractmethod
    def exists(self, paper_id: int) -> bool:
        """Check if paper exists."""
        pass


class IPaperQueryRepository(ABC):
    """
    Separate interface for complex paper queries following ISP.
    This separates basic CRUD from complex search operations.
    """
    
    @abstractmethod
    def get_papers_paginated(self, offset: int, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[ResearchPaper]:
        """Get papers with pagination."""
        pass
    
    @abstractmethod
    def get_corpus_statistics(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        pass
    
    @abstractmethod
    def detect_duplicates(self, similarity_threshold: float = 0.85) -> List[List[ResearchPaper]]:
        """Detect duplicate papers."""
        pass