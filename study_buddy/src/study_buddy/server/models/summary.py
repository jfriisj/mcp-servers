"""
Summary domain model for Study Buddy MCP Server.

This module defines the Summary entity representing AI-generated summaries in
the system, following Clean Architecture Layer 4 principles as a pure domain
model.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass
class Summary:
    """
    Domain model representing an AI-generated summary in Study Buddy system.

    This class follows the Single Responsibility Principle (SRP) by representing
    only summary entities and their business rules. It provides:

    - Summary content and metadata management
    - Validation of summary properties
    - Serialization and factory methods
    - Business rule enforcement

    Clean Architecture Layer 4: Domain Model
    - No dependencies on external frameworks or infrastructure
    - Pure domain logic with business rules
    - Immutable operations with validation
    """

    summary_content: str
    summary_type: str
    id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    word_count: Optional[int] = None
    model_name: Optional[str] = None
    generation_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate Summary after initialization."""
        self._validate()

        # Set defaults
        if self.word_count is None:
            self.word_count = len(self.summary_content.split())

        if self.generation_date is None:
            self.generation_date = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """
        Validate Summary business rules.

        Raises:
            ValueError: If validation fails
        """
        if not self.summary_content or not self.summary_content.strip():
            raise ValueError("Summary content cannot be empty")

        valid_summary_types = {"brief", "standard", "detailed", "custom"}
        if self.summary_type not in valid_summary_types:
            raise ValueError(
                f"Invalid summary_type: {self.summary_type}. "
                f"Must be one of: {valid_summary_types}"
            )

        # Ensure either document_id or chunk_id is set, but not both
        if self.document_id is not None and self.chunk_id is not None:
            raise ValueError(
                "Cannot set both document_id and chunk_id. "
                "Summary must be for either document or chunk, not both."
            )

        if self.document_id is None and self.chunk_id is None:
            raise ValueError(
                "Must set either document_id or chunk_id. "
                "Summary must be associated with document or chunk."
            )

        if self.document_id is not None and self.document_id <= 0:
            raise ValueError("document_id must be a positive integer")

        if self.chunk_id is not None and self.chunk_id <= 0:
            raise ValueError("chunk_id must be a positive integer")

        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # Validate word count ranges for summary types
        self._validate_word_count_ranges()

    def _validate_word_count_ranges(self) -> None:
        """Validate word count is appropriate for summary type."""
        if self.word_count is None:
            return

        # Recommended word count ranges
        ranges = {
            "brief": (50, 150),
            "standard": (200, 400),
            "detailed": (400, 800),
            "custom": (1, 10000),  # No strict limits for custom
        }

        min_words, max_words = ranges[self.summary_type]

        if self.word_count < min_words:
            # This is a warning, not an error - log but don't fail
            pass

        if self.word_count > max_words and self.summary_type != "custom":
            # This is a warning, not an error - log but don't fail
            pass

    @property
    def is_document_summary(self) -> bool:
        """Check if this is a document-level summary."""
        return self.document_id is not None and self.chunk_id is None

    @property
    def is_chunk_summary(self) -> bool:
        """Check if this is a chunk-level summary."""
        return self.chunk_id is not None and self.document_id is None

    @property
    def target_id(self) -> int:
        """Get the ID of the target (document or chunk)."""
        return self.document_id or self.chunk_id

    @property
    def target_type(self) -> str:
        """Get the type of target (document or chunk)."""
        return "document" if self.is_document_summary else "chunk"

    @property
    def word_count_category(self) -> str:
        """Get word count category based on actual count."""
        if self.word_count is None:
            return "unknown"

        if self.word_count <= 150:
            return "brief"
        elif self.word_count <= 400:
            return "standard"
        elif self.word_count <= 800:
            return "detailed"
        else:
            return "extensive"

    def with_metadata(self, key: str, value: Any) -> "Summary":
        """
        Create new summary with additional metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            New Summary instance with added metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return self._copy_with(metadata=new_metadata)

    def with_model_info(self, model_name: str) -> "Summary":
        """
        Create new summary with model information.

        Args:
            model_name: Name of AI model used

        Returns:
            New Summary instance with model info
        """
        return self._copy_with(model_name=model_name)

    def _copy_with(self, **kwargs) -> "Summary":
        """
        Create a copy of this summary with specified changes.

        Args:
            **kwargs: Fields to update

        Returns:
            New Summary instance with changes
        """
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return Summary.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Summary to dictionary for serialization.

        Returns:
            Dictionary representation of Summary
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "summary_type": self.summary_type,
            "summary_content": self.summary_content,
            "word_count": self.word_count,
            "model_name": self.model_name,
            "generation_date": self.generation_date.isoformat()
            if self.generation_date
            else None,
            "metadata": self.metadata.copy(),
            "target_type": self.target_type,
            "target_id": self.target_id,
            "word_count_category": self.word_count_category,
        }

    def to_json(self) -> str:
        """
        Convert Summary to JSON string.

        Returns:
            JSON representation of Summary
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Summary":
        """
        Create Summary from dictionary.

        Args:
            data: Dictionary containing Summary data

        Returns:
            Summary instance

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Parse datetime fields
        generation_date = None
        generation_date_raw = data.get("generation_date")
        if generation_date_raw:
            if isinstance(generation_date_raw, str):
                generation_date = datetime.fromisoformat(generation_date_raw)
            elif isinstance(generation_date_raw, datetime):
                generation_date = generation_date_raw

        return cls(
            id=data.get("id"),
            document_id=data.get("document_id"),
            chunk_id=data.get("chunk_id"),
            summary_type=data["summary_type"],
            summary_content=data["summary_content"],
            word_count=data.get("word_count"),
            model_name=data.get("model_name"),
            generation_date=generation_date,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_db_row(cls, row: Tuple) -> "Summary":
        """
        Create Summary from database row tuple.

        Args:
            row: Database row tuple

        Returns:
            Summary instance

        Raises:
            ValueError: If row format is invalid
        """
        if not row or len(row) < 9:
            raise ValueError("Invalid database row format")

        # Parse JSON metadata
        metadata = json.loads(row[8]) if row[8] else {}

        # Parse datetime
        generation_date = datetime.fromisoformat(row[7]) if row[7] else None

        return cls(
            id=row[0],
            document_id=row[1],
            chunk_id=row[2],
            summary_type=row[3],
            summary_content=row[4],
            word_count=row[5],
            model_name=row[6],
            generation_date=generation_date,
            metadata=metadata,
        )

    @classmethod
    def create_document_summary(
        cls,
        document_id: int,
        summary_content: str,
        summary_type: str = "standard",
        model_name: Optional[str] = None,
    ) -> "Summary":
        """
        Factory method to create document-level summary.

        Args:
            document_id: ID of document to summarize
            summary_content: Summary text content
            summary_type: Type of summary
            model_name: AI model used for generation

        Returns:
            New Summary instance for document
        """
        return cls(
            document_id=document_id,
            summary_content=summary_content,
            summary_type=summary_type,
            model_name=model_name,
        )

    @classmethod
    def create_chunk_summary(
        cls,
        chunk_id: int,
        summary_content: str,
        summary_type: str = "standard",
        model_name: Optional[str] = None,
    ) -> "Summary":
        """
        Factory method to create chunk-level summary.

        Args:
            chunk_id: ID of chunk to summarize
            summary_content: Summary text content
            summary_type: Type of summary
            model_name: AI model used for generation

        Returns:
            New Summary instance for chunk
        """
        return cls(
            chunk_id=chunk_id,
            summary_content=summary_content,
            summary_type=summary_type,
            model_name=model_name,
        )

    def __str__(self) -> str:
        """String representation of Summary."""
        return (
            f"Summary(id={self.id}, type={self.summary_type}, "
            f"target={self.target_type}:{self.target_id}, "
            f"words={self.word_count})"
        )

    def __repr__(self) -> str:
        """Developer representation of Summary."""
        return (
            f"Summary(id={self.id}, {self.target_type}_id={self.target_id}, "
            f"type={self.summary_type}, content='{self.summary_content[:50]}...')"
        )
