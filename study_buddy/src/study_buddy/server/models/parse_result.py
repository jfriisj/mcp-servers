"""
ParseResult domain model for Study Buddy MCP Server.

This module defines the ParseResult entity representing the output of document
parsing operations, following Clean Architecture Layer 4 principles as a pure
domain model with no external dependencies.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ParseResult:
    """
    Domain model representing the result of document parsing operations.

    This class follows the Single Responsibility Principle (SRP) by representing
    only the parsed content and metadata from document processing. It provides:

    - Content storage with metadata
    - Validation of parsing results
    - Serialization capabilities
    - Factory methods for creation

    Clean Architecture Layer 4: Domain Model
    - No dependencies on external frameworks or infrastructure
    - Pure domain logic with business rules
    - Immutable data structure with validation
    """

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate ParseResult after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate ParseResult business rules.

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(self.content, str):
            raise ValueError("Content must be a string")

        if not self.content.strip():
            raise ValueError("Content cannot be empty or whitespace only")

        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # Validate required metadata fields
        if "file_type" not in self.metadata:
            raise ValueError("Metadata must include 'file_type'")

        valid_file_types = {"pdf", "docx", "pptx", "md", "txt"}
        if self.metadata["file_type"] not in valid_file_types:
            raise ValueError(
                f"Invalid file_type: {self.metadata['file_type']}. "
                f"Must be one of: {valid_file_types}"
            )

    @property
    def word_count(self) -> int:
        """Get word count of parsed content."""
        return len(self.content.split())

    @property
    def file_type(self) -> str:
        """Get file type from metadata."""
        return self.metadata["file_type"]

    @property
    def title(self) -> Optional[str]:
        """Get document title from metadata if available."""
        return self.metadata.get("title")

    @property
    def total_pages(self) -> Optional[int]:
        """Get total pages from metadata if available."""
        return self.metadata.get("total_pages")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ParseResult to dictionary for serialization.

        Returns:
            Dictionary representation of ParseResult
        """
        return {
            "content": self.content,
            "metadata": self.metadata.copy(),
            "word_count": self.word_count,
        }

    def to_json(self) -> str:
        """
        Convert ParseResult to JSON string.

        Returns:
            JSON representation of ParseResult
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParseResult":
        """
        Create ParseResult from dictionary.

        Args:
            data: Dictionary containing ParseResult data

        Returns:
            ParseResult instance

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        if "content" not in data:
            raise ValueError("Data must contain 'content' field")

        if "metadata" not in data:
            raise ValueError("Data must contain 'metadata' field")

        return cls(content=data["content"], metadata=data["metadata"])

    @classmethod
    def from_json(cls, json_str: str) -> "ParseResult":
        """
        Create ParseResult from JSON string.

        Args:
            json_str: JSON string containing ParseResult data

        Returns:
            ParseResult instance

        Raises:
            ValueError: If JSON is invalid
            json.JSONDecodeError: If JSON parsing fails
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def add_metadata(self, key: str, value: Any) -> "ParseResult":
        """
        Create new ParseResult with additional metadata.

        This maintains immutability by returning a new instance.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            New ParseResult with added metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value

        return ParseResult(content=self.content, metadata=new_metadata)

    def with_content(self, content: str) -> "ParseResult":
        """
        Create new ParseResult with different content.

        Args:
            content: New content string

        Returns:
            New ParseResult with updated content
        """
        return ParseResult(content=content, metadata=self.metadata.copy())

    def __str__(self) -> str:
        """String representation of ParseResult."""
        return (
            f"ParseResult(file_type={self.file_type}, "
            f"word_count={self.word_count}, "
            f"title={self.title or 'N/A'})"
        )

    def __repr__(self) -> str:
        """Developer representation of ParseResult."""
        return (
            f"ParseResult(content='{self.content[:50]}...', "
            f"metadata={self.metadata})"
        )
