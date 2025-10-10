"""
MCP Handler Interface Definitions.

This module defines interfaces for specialized MCP handlers following the
Interface Segregation Principle. Each interface focuses on a specific domain
of functionality rather than having one monolithic handler interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IDocumentMCPHandler(ABC):
    """Interface for document-related MCP operations."""

    @abstractmethod
    async def upload_document(self, **kwargs) -> Dict[str, Any]:
        """Upload and parse a document."""
        pass

    @abstractmethod
    async def get_document(self, **kwargs) -> Dict[str, Any]:
        """Retrieve document by ID."""
        pass

    @abstractmethod
    async def list_documents(self, **kwargs) -> Dict[str, Any]:
        """List documents with optional filtering."""
        pass

    @abstractmethod
    async def delete_document(self, **kwargs) -> Dict[str, Any]:
        """Delete document and associated data."""
        pass

    @abstractmethod
    async def search_documents(self, **kwargs) -> Dict[str, Any]:
        """Search documents by content."""
        pass


class IChunkingMCPHandler(ABC):
    """Interface for chunking and indexing-related MCP operations."""

    @abstractmethod
    async def index_document(self, **kwargs) -> Dict[str, Any]:
        """Index document into chunks."""
        pass

    @abstractmethod
    async def get_document_structure(self, **kwargs) -> Dict[str, Any]:
        """Get document structure and chunks."""
        pass

    @abstractmethod
    async def get_chunk_content(self, **kwargs) -> Dict[str, Any]:
        """Get content of specific chunk."""
        pass

    @abstractmethod
    async def list_chunks(self, **kwargs) -> Dict[str, Any]:
        """List chunks with optional filtering."""
        pass


class ISummaryMCPHandler(ABC):
    """Interface for summary-related MCP operations."""

    @abstractmethod
    async def save_summary(self, **kwargs) -> Dict[str, Any]:
        """Save AI-generated summary."""
        pass

    @abstractmethod
    async def get_summary(self, **kwargs) -> Dict[str, Any]:
        """Get summary by type and target."""
        pass

    @abstractmethod
    async def list_summaries(self, **kwargs) -> Dict[str, Any]:
        """List summaries with optional filtering."""
        pass

    @abstractmethod
    async def get_summary_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get summary statistics."""
        pass


class IBookmarkMCPHandler(ABC):
    """Interface for bookmark-related MCP operations."""

    @abstractmethod
    async def create_document_bookmark(self, **kwargs) -> Dict[str, Any]:
        """Create bookmark for document."""
        pass

    @abstractmethod
    async def create_chunk_bookmark(self, **kwargs) -> Dict[str, Any]:
        """Create bookmark for chunk."""
        pass

    @abstractmethod
    async def get_bookmark(self, **kwargs) -> Dict[str, Any]:
        """Get bookmark by ID."""
        pass

    @abstractmethod
    async def list_bookmarks(self, **kwargs) -> Dict[str, Any]:
        """List bookmarks with optional filtering."""
        pass

    @abstractmethod
    async def search_bookmarks(self, **kwargs) -> Dict[str, Any]:
        """Search bookmarks by content."""
        pass

    @abstractmethod
    async def update_bookmark(self, **kwargs) -> Dict[str, Any]:
        """Update bookmark."""
        pass

    @abstractmethod
    async def delete_bookmark(self, **kwargs) -> Dict[str, Any]:
        """Delete bookmark."""
        pass

    @abstractmethod
    async def export_bookmarks(self, **kwargs) -> Dict[str, Any]:
        """Export bookmarks to file."""
        pass


class IProgressMCPHandler(ABC):
    """Interface for progress tracking and study session MCP operations."""

    @abstractmethod
    async def track_reading_progress(self, **kwargs) -> Dict[str, Any]:
        """Track reading progress."""
        pass

    @abstractmethod
    async def mark_content_completed(self, **kwargs) -> Dict[str, Any]:
        """Mark content as completed."""
        pass

    @abstractmethod
    async def get_reading_progress(self, **kwargs) -> Dict[str, Any]:
        """Get reading progress."""
        pass

    @abstractmethod
    async def start_study_session(self, **kwargs) -> Dict[str, Any]:
        """Start study session."""
        pass

    @abstractmethod
    async def pause_study_session(self, **kwargs) -> Dict[str, Any]:
        """Pause study session."""
        pass

    @abstractmethod
    async def end_study_session(self, **kwargs) -> Dict[str, Any]:
        """End study session."""
        pass

    @abstractmethod
    async def get_session_history(self, **kwargs) -> Dict[str, Any]:
        """Get session history."""
        pass

    @abstractmethod
    async def get_daily_summary(self, **kwargs) -> Dict[str, Any]:
        """Get daily summary."""
        pass


class IPromptMCPHandler(ABC):
    """Interface for prompt generation MCP operations."""

    @abstractmethod
    async def generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """Generate AI prompt from targets."""
        pass

    @abstractmethod
    async def get_available_prompt_types(self, **kwargs) -> Dict[str, Any]:
        """Get available prompt types."""
        pass

    @abstractmethod
    async def validate_prompt_targets(self, **kwargs) -> Dict[str, Any]:
        """Validate prompt targets."""
        pass

    @abstractmethod
    async def get_prompt_preview(self, **kwargs) -> Dict[str, Any]:
        """Get prompt preview."""
        pass


class IFileMCPHandler(ABC):
    """Interface for file export MCP operations."""

    @abstractmethod
    async def create_markdown_file(self, **kwargs) -> Dict[str, Any]:
        """Create markdown file."""
        pass

    @abstractmethod
    async def export_summary_to_file(self, **kwargs) -> Dict[str, Any]:
        """Export summary to file."""
        pass

    @abstractmethod
    async def export_document_structure_to_file(self, **kwargs) -> Dict[str, Any]:
        """Export document structure to file."""
        pass


class IMCPHandler(ABC):
    """
    Composite interface for MCP handler that delegates to specialized handlers.
    
    This interface follows the Composite pattern, providing a unified interface
    while delegating to specialized handlers internally.
    """

    @property
    @abstractmethod
    def document_handler(self) -> IDocumentMCPHandler:
        """Get document handler."""
        pass

    @property
    @abstractmethod
    def chunking_handler(self) -> IChunkingMCPHandler:
        """Get chunking handler."""
        pass

    @property
    @abstractmethod
    def summary_handler(self) -> ISummaryMCPHandler:
        """Get summary handler."""
        pass

    @property
    @abstractmethod
    def bookmark_handler(self) -> IBookmarkMCPHandler:
        """Get bookmark handler."""
        pass

    @property
    @abstractmethod
    def progress_handler(self) -> IProgressMCPHandler:
        """Get progress handler."""
        pass

    @property
    @abstractmethod
    def prompt_handler(self) -> IPromptMCPHandler:
        """Get prompt handler."""
        pass

    @property
    @abstractmethod
    def file_handler(self) -> IFileMCPHandler:
        """Get file handler."""
        pass