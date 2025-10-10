"""
Repository Interfaces for Study Buddy Application

These interfaces define contracts for data access operations.
Repositories handle all database interactions and data persistence.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class IDocumentRepository(ABC):
    """Interface for document data access operations."""
    
    @abstractmethod
    async def create(self, document_data: Dict[str, Any]) -> int:
        """Create a new document record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    async def list_all(self, filters: Optional[Dict[str, Any]] = None,
                      limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """List documents with optional filters. Returns (items, total_count)."""
        pass
    
    @abstractmethod
    async def update(self, document_id: int, updates: Dict[str, Any]) -> bool:
        """Update document record."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: int) -> bool:
        """Delete document record."""
        pass
    
    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None,
                    limit: int = 20) -> List[Dict[str, Any]]:
        """Search documents by text query."""
        pass


class IChunkRepository(ABC):
    """Interface for chunk data access operations."""
    
    @abstractmethod
    async def create(self, chunk_data: Dict[str, Any]) -> int:
        """Create a new chunk record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk by ID."""
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        pass
    
    @abstractmethod
    async def update(self, chunk_id: int, updates: Dict[str, Any]) -> bool:
        """Update chunk record."""
        pass
    
    @abstractmethod
    async def delete(self, chunk_id: int) -> bool:
        """Delete chunk record."""
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: int) -> int:
        """Delete all chunks for a document. Returns count of deleted chunks."""
        pass


class ISummaryRepository(ABC):
    """Interface for summary data access operations."""
    
    @abstractmethod
    async def create(self, summary_data: Dict[str, Any]) -> int:
        """Create a new summary record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, summary_id: int) -> Optional[Dict[str, Any]]:
        """Get summary by ID."""
        pass
    
    @abstractmethod
    async def get_by_content(self, content_id: int, content_type: str,
                           summary_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get summaries for specific content."""
        pass
    
    @abstractmethod
    async def list_all(self, filters: Optional[Dict[str, Any]] = None,
                      limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """List summaries with optional filters. Returns (items, total_count)."""
        pass
    
    @abstractmethod
    async def update(self, summary_id: int, updates: Dict[str, Any]) -> bool:
        """Update summary record."""
        pass
    
    @abstractmethod
    async def delete(self, summary_id: int) -> bool:
        """Delete summary record."""
        pass


class IUserRepository(ABC):
    """Interface for user data access operations."""
    
    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> int:
        """Create a new user record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def update(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user record."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user record."""
        pass
    
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials."""
        pass