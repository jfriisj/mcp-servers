"""
Document domain model for Study Buddy MCP Server.

This module defines the Document entity representing uploaded documents in the
system, following Clean Architecture Layer 4 principles as a pure domain model.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Document:
    """
    Domain model representing a document in the Study Buddy system.

    This class follows the Single Responsibility Principle (SRP) by representing
    only document entities and their business rules. It provides:

    - Document metadata and state management
    - Validation of document properties
    - Serialization and factory methods
    - Business rule enforcement

    Clean Architecture Layer 4: Domain Model
    - No dependencies on external frameworks or infrastructure
    - Pure domain logic with business rules
    - Immutable operations with validation
    """

    title: str
    file_path: str
    file_type: str
    id: Optional[int] = None
    upload_date: Optional[datetime] = None
    file_size: Optional[int] = None
    total_pages: Optional[int] = None
    total_words: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    indexed: bool = False
    summarized: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Document after initialization."""
        self._validate()

        # Set timestamps if not provided
        if self.upload_date is None:
            self.upload_date = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """
        Validate Document business rules.

        Raises:
            ValueError: If validation fails
        """
        if not self.title or not self.title.strip():
            raise ValueError("Document title cannot be empty")

        if not self.file_path or not self.file_path.strip():
            raise ValueError("Document file_path cannot be empty")

        valid_file_types = {"pdf", "docx", "pptx", "md", "txt"}
        if self.file_type not in valid_file_types:
            raise ValueError(
                f"Invalid file_type: {self.file_type}. "
                f"Must be one of: {valid_file_types}"
            )

        if self.file_size is not None and self.file_size < 0:
            raise ValueError("File size cannot be negative")

        if self.total_pages is not None and self.total_pages < 0:
            raise ValueError("Total pages cannot be negative")

        if self.total_words is not None and self.total_words < 0:
            raise ValueError("Total words cannot be negative")

        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")

        # Validate tags are strings
        for tag in self.tags:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")

    @property
    def is_text_document(self) -> bool:
        """Check if document is text-based (md, txt)."""
        return self.file_type in {"md", "txt"}

    @property
    def is_binary_document(self) -> bool:
        """Check if document is binary (pdf, docx, pptx)."""
        return self.file_type in {"pdf", "docx", "pptx"}

    @property
    def processing_status(self) -> str:
        """Get current processing status."""
        if self.summarized:
            return "fully_processed"
        elif self.indexed:
            return "indexed"
        else:
            return "uploaded"

    @property
    def file_extension(self) -> str:
        """Get file extension from file_path."""
        return self.file_path.split(".")[-1].lower()

    def add_tag(self, tag: str) -> "Document":
        """
        Add a tag to the document.

        Args:
            tag: Tag to add

        Returns:
            New Document instance with added tag
        """
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError("Tag must be a non-empty string")

        tag = tag.strip().lower()
        new_tags = self.tags.copy()

        if tag not in new_tags:
            new_tags.append(tag)

        return self._copy_with(tags=new_tags)

    def remove_tag(self, tag: str) -> "Document":
        """
        Remove a tag from the document.

        Args:
            tag: Tag to remove

        Returns:
            New Document instance with removed tag
        """
        tag = tag.strip().lower()
        new_tags = [t for t in self.tags if t != tag]
        return self._copy_with(tags=new_tags)

    def mark_indexed(self) -> "Document":
        """
        Mark document as indexed.

        Returns:
            New Document instance marked as indexed
        """
        return self._copy_with(indexed=True, updated_at=datetime.now(timezone.utc))

    def mark_summarized(self) -> "Document":
        """
        Mark document as summarized.

        Returns:
            New Document instance marked as summarized
        """
        return self._copy_with(summarized=True, updated_at=datetime.now(timezone.utc))

    def update_notes(self, notes: str) -> "Document":
        """
        Update document notes.

        Args:
            notes: New notes content

        Returns:
            New Document instance with updated notes
        """
        return self._copy_with(notes=notes, updated_at=datetime.now(datetime.UTC))

    def _copy_with(self, **kwargs) -> "Document":
        """
        Create a copy of this document with specified changes.

        Args:
            **kwargs: Fields to update

        Returns:
            New Document instance with changes
        """
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return Document.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Document to dictionary for serialization.

        Returns:
            Dictionary representation of Document
        """
        return {
            "id": self.id,
            "title": self.title,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "upload_date": self.upload_date.isoformat()
            if self.upload_date
            else None,
            "file_size": self.file_size,
            "total_pages": self.total_pages,
            "total_words": self.total_words,
            "tags": self.tags.copy(),
            "notes": self.notes,
            "indexed": self.indexed,
            "summarized": self.summarized,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at
            else None,
            "processing_status": self.processing_status,
        }

    def to_json(self) -> str:
        """
        Convert Document to JSON string.

        Returns:
            JSON representation of Document
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """
        Create Document from dictionary.

        Args:
            data: Dictionary containing Document data

        Returns:
            Document instance

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Parse datetime fields
        upload_date = None
        upload_date_raw = data.get("upload_date")
        if upload_date_raw:
            if isinstance(upload_date_raw, str):
                upload_date = datetime.fromisoformat(upload_date_raw)
            elif isinstance(upload_date_raw, datetime):
                upload_date = upload_date_raw

        created_at = None
        created_at_raw = data.get("created_at")
        if created_at_raw:
            if isinstance(created_at_raw, str):
                created_at = datetime.fromisoformat(created_at_raw)
            elif isinstance(created_at_raw, datetime):
                created_at = created_at_raw

        updated_at = None
        updated_at_raw = data.get("updated_at")
        if updated_at_raw:
            if isinstance(updated_at_raw, str):
                updated_at = datetime.fromisoformat(updated_at_raw)
            elif isinstance(updated_at_raw, datetime):
                updated_at = updated_at_raw

        return cls(
            id=data.get("id"),
            title=data["title"],
            file_path=data["file_path"],
            file_type=data["file_type"],
            upload_date=upload_date,
            file_size=data.get("file_size"),
            total_pages=data.get("total_pages"),
            total_words=data.get("total_words"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            indexed=data.get("indexed", False),
            summarized=data.get("summarized", False),
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def from_db_row(cls, row: Tuple) -> "Document":
        """
        Create Document from database row tuple.

        Args:
            row: Database row tuple

        Returns:
            Document instance

        Raises:
            ValueError: If row format is invalid
        """
        if not row or len(row) < 14:
            raise ValueError("Invalid database row format")

        # Parse JSON fields
        tags = json.loads(row[7]) if row[7] else []

        # Parse datetime fields
        upload_date = datetime.fromisoformat(row[4]) if row[4] else None
        created_at = datetime.fromisoformat(row[12]) if row[12] else None
        updated_at = datetime.fromisoformat(row[13]) if row[13] else None

        return cls(
            id=row[0],
            title=row[1],
            file_path=row[2],
            file_type=row[3],
            upload_date=upload_date,
            file_size=row[5],
            total_pages=row[6],
            total_words=row[7] if len(row) > 7 else None,
            tags=tags,
            notes=row[8] if len(row) > 8 else None,
            indexed=bool(row[9]) if len(row) > 9 else False,
            summarized=bool(row[10]) if len(row) > 10 else False,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def from_parse_result(
        cls, parse_result, file_path: str, title: Optional[str] = None
    ) -> "Document":
        """
        Create Document from ParseResult.

        Args:
            parse_result: ParseResult instance
            file_path: Path to the document file
            title: Optional title override

        Returns:
            Document instance
        """
        return cls(
            title=title or parse_result.title or "Untitled Document",
            file_path=file_path,
            file_type=parse_result.file_type,
            total_pages=parse_result.total_pages,
            total_words=parse_result.word_count,
            file_size=parse_result.metadata.get("file_size"),
        )

    def __str__(self) -> str:
        """String representation of Document."""
        return (
            f"Document(id={self.id}, title='{self.title}', "
            f"type={self.file_type}, status={self.processing_status})"
        )

    def __repr__(self) -> str:
        """Developer representation of Document."""
        return (
            f"Document(id={self.id}, title='{self.title}', "
            f"file_path='{self.file_path}', file_type='{self.file_type}')"
        )
