"""Abstract base class for document chunking strategies.

Defines the interface that all chunking strategies must implement.
Follows the Strategy pattern for extensible document segmentation.
"""

from abc import ABC, abstractmethod
from typing import List

from ..models.chunk import Chunk
from ..models.document import Document


class BaseChunkingStrategy(ABC):
    """Abstract base class for document chunking strategies.

    All chunking strategies must implement this interface to ensure
    they can be used interchangeably (Liskov Substitution Principle).

    The strategy pattern allows adding new chunking methods without
    modifying existing code (Open/Closed Principle).
    """

    @abstractmethod
    def can_chunk(self, document: Document, content: str) -> bool:
        """Check if this strategy can handle the given document.

        Args:
            document: The document metadata
            content: The document's text content

        Returns:
            True if this strategy can chunk the document, False otherwise

        Note:
            This method should analyze the document's content and metadata
            to determine if this chunking strategy is appropriate.
        """
        pass

    @abstractmethod
    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """Create chunks from the document.

        Args:
            document: The document metadata
            content: The document's text content

        Returns:
            List of chunks created from the document

        Raises:
            ValueError: If the document cannot be chunked by this strategy

        Note:
            Each chunk should have:
            - document_id set to document.id
            - chunk_index set in order (0, 1, 2, ...)
            - appropriate chunk_type for the strategy
            - meaningful title extracted from content
            - calculated word_count
            - strategy-specific metadata
        """
        pass

    def get_strategy_name(self) -> str:
        """Get the name of this chunking strategy.

        Returns:
            Human-readable name of the strategy
        """
        return self.__class__.__name__.replace("Strategy", "").lower()

    def _calculate_word_count(self, text: str) -> int:
        """Calculate word count for a text chunk.

        Args:
            text: The text to count words in

        Returns:
            Number of words in the text
        """
        if not text or not text.strip():
            return 0
        return len(text.strip().split())

    def _clean_title(self, title: str) -> str:
        """Clean and format a chunk title.

        Args:
            title: Raw title text

        Returns:
            Cleaned title suitable for display
        """
        if not title:
            return "Untitled"

        # Remove extra whitespace and newlines
        title = " ".join(title.strip().split())

        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."

        return title
