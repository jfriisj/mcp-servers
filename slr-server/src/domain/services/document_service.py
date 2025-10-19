"""
Document Service Interface

Defines the contract for research document operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import ResearchPaper


class IDocumentService(ABC):
    """
    Interface for document service operations.
    
    Follows SRP by handling only document-related business logic.
    """
    
    @abstractmethod
    def upload_paper(self, file_path: str, title: Optional[str] = None, 
                    authors: Optional[List[str]] = None, doi: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> ResearchPaper:
        """Upload and process a research paper."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a document file."""
        pass
    
    @abstractmethod
    def process_document(self, paper: ResearchPaper) -> Dict[str, Any]:
        """Process document content and extract information."""
        pass
    
    @abstractmethod
    def classify_paper(self, paper: ResearchPaper) -> Dict[str, Any]:
        """Classify paper by type, methodology, etc."""
        pass


class IBibliographyService(ABC):
    """
    Interface for bibliography operations.
    Separated from document service following ISP.
    """
    
    @abstractmethod
    def upload_bibliography_batch(self, file_path: str, tags: Optional[List[str]] = None) -> List[ResearchPaper]:
        """Upload papers from bibliography file (BibTeX, RIS)."""
        pass
    
    @abstractmethod
    def parse_bibliography_entry(self, entry: str, format_type: str) -> Dict[str, Any]:
        """Parse a single bibliography entry."""
        pass


class IDuplicateDetectionService(ABC):
    """
    Interface for duplicate detection operations.
    Separated following ISP principle.
    """
    
    @abstractmethod
    def detect_duplicates(self, similarity_threshold: float = 0.85) -> List[List[ResearchPaper]]:
        """Detect duplicate papers."""
        pass
    
    @abstractmethod
    def remove_duplicates(self, duplicate_groups: List[List[ResearchPaper]], dry_run: bool = True) -> Dict[str, Any]:
        """Remove duplicate papers."""
        pass