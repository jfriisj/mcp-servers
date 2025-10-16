"""
Chunk Repository Interface

Defines the contract for academic chunk data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import AcademicChunk


class IChunkRepository(ABC):
    """
    Interface for academic chunk repository operations.
    
    Follows ISP by keeping chunk operations separate from paper operations.
    """
    
    @abstractmethod
    def create(self, chunk: AcademicChunk) -> AcademicChunk:
        """Create a new academic chunk."""
        pass
    
    @abstractmethod
    def get_by_id(self, chunk_id: int) -> Optional[AcademicChunk]:
        """Retrieve chunk by ID."""
        pass
    
    @abstractmethod
    def get_by_paper_id(self, paper_id: int) -> List[AcademicChunk]:
        """Get all chunks for a paper."""
        pass
    
    @abstractmethod
    def update(self, chunk: AcademicChunk) -> AcademicChunk:
        """Update existing chunk."""
        pass
    
    @abstractmethod
    def delete(self, chunk_id: int) -> bool:
        """Delete chunk by ID."""
        pass
    
    @abstractmethod
    def delete_by_paper_id(self, paper_id: int) -> int:
        """Delete all chunks for a paper. Returns count deleted."""
        pass
    
    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[AcademicChunk]:
        """List chunks with optional filters."""
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count chunks matching filters."""
        pass


class IChunkQueryRepository(ABC):
    """
    Interface for complex chunk query operations.
    Separated from basic CRUD following ISP.
    """
    
    @abstractmethod
    def get_statistics(self, paper_id: Optional[int] = None) -> Dict[str, Any]:
        """Get chunk statistics."""
        pass
    
    @abstractmethod
    def search_chunks(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[AcademicChunk]:
        """Search chunks by content."""
        pass
    
    @abstractmethod
    def get_chunks_by_section_type(self, section_type: str, paper_id: Optional[int] = None) -> List[AcademicChunk]:
        """Get chunks by section type."""
        pass