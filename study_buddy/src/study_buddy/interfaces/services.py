"""
Service Interfaces for Study Buddy Application

These interfaces define contracts for business logic services.
Services coordinate between repositories and implement business rules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path


class IDocumentService(ABC):
    """Interface for document-related business operations."""
    
    @abstractmethod
    async def upload_document(self, file_path: Path, title: Optional[str] = None, 
                            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Upload and process a new document."""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    async def list_documents(self, filters: Optional[Dict[str, Any]] = None, 
                           limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List documents with optional filters."""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: int) -> bool:
        """Delete a document and all related data."""
        pass
    
    @abstractmethod
    async def index_document(self, document_id: int, 
                           strategy: str = "auto", force: bool = False) -> Dict[str, Any]:
        """Index document for search and analysis."""
        pass


class ISearchService(ABC):
    """Interface for search operations."""
    
    @abstractmethod
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None,
                             limit: int = 20) -> Dict[str, Any]:
        """Search documents by query."""
        pass
    
    @abstractmethod
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on document content."""
        pass
    
    @abstractmethod
    async def get_similar_documents(self, document_id: int, 
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """Find documents similar to the given document."""
        pass


class ISummaryService(ABC):
    """Interface for summary operations."""
    
    @abstractmethod
    async def create_summary(self, content_id: int, content_type: str,
                           summary_type: str, model_name: str,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new summary."""
        pass
    
    @abstractmethod
    async def get_summary(self, summary_id: int) -> Optional[Dict[str, Any]]:
        """Get summary by ID."""
        pass
    
    @abstractmethod
    async def list_summaries(self, filters: Optional[Dict[str, Any]] = None,
                           limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List summaries with optional filters."""
        pass
    
    @abstractmethod
    async def export_summary(self, summary_id: int, file_path: Path,
                           include_metadata: bool = True) -> bool:
        """Export summary to file."""
        pass


class IAnalyticsService(ABC):
    """Interface for analytics operations."""
    
    @abstractmethod
    async def get_document_statistics(self, document_id: Optional[int] = None) -> Dict[str, Any]:
        """Get document statistics."""
        pass
    
    @abstractmethod
    async def get_usage_metrics(self, time_range: Optional[str] = None) -> Dict[str, Any]:
        """Get usage metrics for specified time range."""
        pass
    
    @abstractmethod
    async def generate_report(self, report_type: str, 
                            parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate analytical report."""
        pass