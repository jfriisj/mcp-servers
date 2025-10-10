"""
Chunk domain model for Study Buddy MCP Server.

This module defines the Chunk entity representing document segments in the
system, following Clean Architecture Layer 4 principles as a pure domain model.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass
class Chunk:
    """
    Domain model representing a document chunk in the Study Buddy system.

    This class follows the Single Responsibility Principle (SRP) by representing
    only chunk entities and their business rules. It provides:

    - Chunk content and metadata management
    - Validation of chunk properties
    - Serialization and factory methods
    - Business rule enforcement

    Clean Architecture Layer 4: Domain Model
    - No dependencies on external frameworks or infrastructure
    - Pure domain logic with business rules
    - Immutable operations with validation
    """

    document_id: int
    chunk_index: int
    content: str
    id: Optional[int] = None
    chunk_type: str = "auto"
    title: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    word_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Chunk after initialization."""
        self._validate()

        # Set defaults
        if self.word_count is None:
            self.word_count = len(self.content.split())

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """
        Validate Chunk business rules.

        Raises:
            ValueError: If validation fails
        """
        if self.document_id is None or self.document_id <= 0:
            raise ValueError("document_id must be a positive integer")

        if self.chunk_index < 0:
            raise ValueError("chunk_index cannot be negative")

        if not self.content or not self.content.strip():
            raise ValueError("Chunk content cannot be empty")

        valid_chunk_types = {
            "chapter",
            "section",
            "heading",
            "slide",
            "paragraph",
            "auto",
            "fixed_length",
        }
        if self.chunk_type not in valid_chunk_types:
            raise ValueError(
                f"Invalid chunk_type: {self.chunk_type}. "
                f"Must be one of: {valid_chunk_types}"
            )

        if self.start_page is not None and self.start_page < 1:
            raise ValueError("start_page must be >= 1")

        if self.end_page is not None and self.end_page < 1:
            raise ValueError("end_page must be >= 1")

        if (
            self.start_page is not None
            and self.end_page is not None
            and self.start_page > self.end_page
        ):
            raise ValueError("start_page cannot be greater than end_page")

        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

    @property
    def page_range(self) -> Optional[str]:
        """Get formatted page range string."""
        if self.start_page is None:
            return None

        if self.end_page is None or self.start_page == self.end_page:
            return f"p. {self.start_page}"

        return f"pp. {self.start_page}-{self.end_page}"

    @property
    def is_multi_page(self) -> bool:
        """Check if chunk spans multiple pages."""
        return (
            self.start_page is not None
            and self.end_page is not None
            and self.start_page != self.end_page
        )

    @property
    def has_title(self) -> bool:
        """Check if chunk has a title."""
        return bool(self.title and self.title.strip())

    @property
    def display_title(self) -> str:
        """Get display title with fallback."""
        if self.has_title:
            return self.title or ""

        if self.chunk_type == "auto":
            return f"Chunk {self.chunk_index + 1}"

        return f"{self.chunk_type.title()} {self.chunk_index + 1}"

    def with_title(self, title: str) -> "Chunk":
        """
        Create new chunk with updated title.

        Args:
            title: New title

        Returns:
            New Chunk instance with updated title
        """
        return self._copy_with(title=title.strip() if title else None)

    def with_metadata(self, key: str, value: Any) -> "Chunk":
        """
        Create new chunk with additional metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            New Chunk instance with added metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return self._copy_with(metadata=new_metadata)

    def with_page_range(
        self, start_page: int, end_page: int = None
    ) -> "Chunk":
        """
        Create new chunk with page range information.

        Args:
            start_page: Starting page number
            end_page: Ending page number (optional)

        Returns:
            New Chunk instance with page range
        """
        if start_page < 1:
            raise ValueError("start_page must be >= 1")

        if end_page is not None and end_page < start_page:
            raise ValueError("end_page cannot be less than start_page")

        return self._copy_with(
            start_page=start_page, end_page=end_page or start_page
        )

    def _copy_with(self, **kwargs) -> "Chunk":
        """
        Create a copy of this chunk with specified changes.

        Args:
            **kwargs: Fields to update

        Returns:
            New Chunk instance with changes
        """
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return Chunk.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Chunk to dictionary for serialization.

        Returns:
            Dictionary representation of Chunk
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_type": self.chunk_type,
            "title": self.title,
            "content": self.content,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "word_count": self.word_count,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "page_range": self.page_range,
            "display_title": self.display_title,
        }

    def to_json(self) -> str:
        """
        Convert Chunk to JSON string.

        Returns:
            JSON representation of Chunk
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """
        Create Chunk from dictionary.

        Args:
            data: Dictionary containing Chunk data

        Returns:
            Chunk instance

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Parse datetime fields
        created_at = None
        created_at_raw = data.get("created_at")
        if created_at_raw:
            if isinstance(created_at_raw, str):
                created_at = datetime.fromisoformat(created_at_raw)
            elif isinstance(created_at_raw, datetime):
                created_at = created_at_raw

        return cls(
            id=data.get("id"),
            document_id=data["document_id"],
            chunk_index=data["chunk_index"],
            chunk_type=data.get("chunk_type", "auto"),
            title=data.get("title"),
            content=data["content"],
            start_page=data.get("start_page"),
            end_page=data.get("end_page"),
            word_count=data.get("word_count"),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )

    @classmethod
    def from_db_row(cls, row: Tuple) -> "Chunk":
        """
        Create Chunk from database row tuple.

        Args:
            row: Database row tuple

        Returns:
            Chunk instance

        Raises:
            ValueError: If row format is invalid
        """
        if not row or len(row) < 11:
            raise ValueError("Invalid database row format")

        # Parse JSON metadata
        metadata = json.loads(row[9]) if row[9] else {}

        # Parse datetime
        created_at = datetime.fromisoformat(row[10]) if row[10] else None

        return cls(
            id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            chunk_type=row[3] or "auto",
            title=row[4],
            content=row[5],
            start_page=row[6],
            end_page=row[7],
            word_count=row[8],
            metadata=metadata,
            created_at=created_at,
        )

    @classmethod
    def create_from_content(
        cls,
        document_id: int,
        chunk_index: int,
        content: str,
        chunk_type: str = "auto",
        title: Optional[str] = None,
        **kwargs,
    ) -> "Chunk":
        """
        Factory method to create chunk from content.

        Args:
            document_id: ID of parent document
            chunk_index: Index of chunk in document
            content: Chunk content
            chunk_type: Type of chunk
            title: Optional title
            **kwargs: Additional chunk properties

        Returns:
            New Chunk instance
        """
        return cls(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            chunk_type=chunk_type,
            title=title,
            **kwargs,
        )

    def __str__(self) -> str:
        """String representation of Chunk."""
        return (
            f"Chunk(id={self.id}, doc_id={self.document_id}, "
            f"index={self.chunk_index}, type={self.chunk_type}, "
            f"words={self.word_count})"
        )

    def __repr__(self) -> str:
        """Developer representation of Chunk."""
        return (
            f"Chunk(id={self.id}, document_id={self.document_id}, "
            f"chunk_index={self.chunk_index}, content='{self.content[:50]}...')"
        )
