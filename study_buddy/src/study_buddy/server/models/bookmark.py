"""
Bookmark domain model for Study Buddy MCP Server.

This module defines the Bookmark entity representing user bookmarks for documents
and chunks in the system, following Clean Architecture Layer 4 principles as a
pure domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Bookmark:
    """
    Domain model representing a bookmark in the Study Buddy system.

    This class follows the Single Responsibility Principle (SRP) by representing
    only bookmark entities and their business rules. It provides:

    - Bookmark metadata and categorization
    - Validation of bookmark properties
    - Serialization and factory methods
    - Business rule enforcement

    Clean Architecture Layer 4: Domain Model
    - No dependencies on external frameworks or infrastructure
    - Pure domain logic with business rules
    - Immutable operations with validation
    """

    title: str
    document_id: int
    category: str = "General"
    id: Optional[int] = None
    chunk_id: Optional[int] = None  # Optional: bookmark specific chunk
    notes: Optional[str] = None
    page_number: Optional[int] = None  # For PDF/document page references
    position: Optional[str] = None  # For specific position within content
    tags: List[str] = field(default_factory=list)
    color: str = "#FFD700"  # Default bookmark color (gold)
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Bookmark after initialization."""
        self._validate()

        # Set timestamps if not provided
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def _validate(self) -> None:
        """
        Validate bookmark business rules.

        Raises:
            ValueError: If validation fails
        """
        if not self.title or not self.title.strip():
            raise ValueError("Bookmark title cannot be empty")

        if self.document_id is None or self.document_id <= 0:
            raise ValueError("Valid document_id is required")

        if not self.category or not self.category.strip():
            raise ValueError("Bookmark category cannot be empty")

        # Validate color format (hex color code)
        if not self._is_valid_hex_color(self.color):
            raise ValueError(f"Invalid color format: {self.color}")

        # Validate page number if provided
        if self.page_number is not None and self.page_number <= 0:
            raise ValueError("Page number must be positive")

    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format (#RRGGBB or #RGB)."""
        if not color.startswith('#'):
            return False

        hex_part = color[1:]
        if len(hex_part) not in [3, 6]:
            return False

        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False

    def update_notes(self, notes: str) -> None:
        """
        Update bookmark notes.

        Args:
            notes: New notes content
        """
        self.notes = notes
        self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """
        Add tag to bookmark.

        Args:
            tag: Tag to add
        """
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: str) -> None:
        """
        Remove tag from bookmark.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)

    def set_favorite(self, is_favorite: bool) -> None:
        """
        Set bookmark favorite status.

        Args:
            is_favorite: Whether bookmark is favorite
        """
        self.is_favorite = is_favorite
        self.updated_at = datetime.now(timezone.utc)

    def change_category(self, category: str) -> None:
        """
        Change bookmark category.

        Args:
            category: New category name

        Raises:
            ValueError: If category is empty
        """
        if not category or not category.strip():
            raise ValueError("Category cannot be empty")

        self.category = category.strip()
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert bookmark to dictionary representation.

        Returns:
            Dictionary containing all bookmark data
        """
        return {
            "id": self.id,
            "title": self.title,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "category": self.category,
            "notes": self.notes,
            "page_number": self.page_number,
            "position": self.position,
            "tags": self.tags.copy(),
            "color": self.color,
            "is_favorite": self.is_favorite,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bookmark':
        """
        Create bookmark from dictionary representation.

        Args:
            data: Dictionary containing bookmark data

        Returns:
            Bookmark instance
        """
        # Parse timestamps
        created_at = None
        updated_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data.get("id"),
            title=data["title"],
            document_id=data["document_id"],
            chunk_id=data.get("chunk_id"),
            category=data.get("category", "General"),
            notes=data.get("notes"),
            page_number=data.get("page_number"),
            position=data.get("position"),
            tags=data.get("tags", []).copy(),
            color=data.get("color", "#FFD700"),
            is_favorite=data.get("is_favorite", False),
            created_at=created_at,
            updated_at=updated_at
        )

    @classmethod
    def create_document_bookmark(
        cls,
        title: str,
        document_id: int,
        category: str = "General",
        **kwargs
    ) -> 'Bookmark':
        """
        Factory method for creating document-level bookmark.

        Args:
            title: Bookmark title
            document_id: ID of document to bookmark
            category: Bookmark category
            **kwargs: Additional bookmark properties

        Returns:
            New Bookmark instance
        """
        return cls(
            title=title,
            document_id=document_id,
            category=category,
            **kwargs
        )

    @classmethod
    def create_chunk_bookmark(
        cls,
        title: str,
        document_id: int,
        chunk_id: int,
        category: str = "General",
        **kwargs
    ) -> 'Bookmark':
        """
        Factory method for creating chunk-level bookmark.

        Args:
            title: Bookmark title
            document_id: ID of document containing chunk
            chunk_id: ID of specific chunk to bookmark
            category: Bookmark category
            **kwargs: Additional bookmark properties

        Returns:
            New Bookmark instance
        """
        return cls(
            title=title,
            document_id=document_id,
            chunk_id=chunk_id,
            category=category,
            **kwargs
        )

    def __str__(self) -> str:
        """String representation of bookmark."""
        chunk_info = f" (Chunk {self.chunk_id})" if self.chunk_id else ""
        return f"Bookmark: {self.title} - Doc {self.document_id}{chunk_info} [{self.category}]"

    def __repr__(self) -> str:
        """Developer representation of bookmark."""
        return (
            f"Bookmark(id={self.id}, title='{self.title}', "
            f"document_id={self.document_id}, chunk_id={self.chunk_id}, "
            f"category='{self.category}')"
        )
