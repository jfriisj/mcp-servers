"""Fixed-length chunking strategy as fallback for any document.

Splits documents into chunks of approximately equal word count,
breaking at sentence or paragraph boundaries when possible.
"""

import re
from typing import List

from ..models.chunk import Chunk
from ..models.document import Document

from .base_strategy import BaseChunkingStrategy


class FixedLengthStrategy(BaseChunkingStrategy):
    """Chunks documents by fixed word count with smart boundaries.

    This strategy provides reliable chunking for any document type:
    - Target chunk size: 750 words
    - Minimum chunk size: 100 words
    - Maximum chunk size: 1000 words
    - Breaks at paragraph boundaries when possible
    - Falls back to sentence boundaries
    - Last resort: word boundaries

    Follows Single Responsibility Principle - handles fixed-length chunking.
    """

    def __init__(
        self,
        target_words: int = 750,
        min_words: int = 100,
        max_words: int = 1000
    ):
        """Initialize with configurable chunk sizes.

        Args:
            target_words: Target number of words per chunk
            min_words: Minimum acceptable chunk size
            max_words: Maximum acceptable chunk size
        """
        self.target_words = target_words
        self.min_words = min_words
        self.max_words = max_words

    def can_chunk(self, document: Document, content: str) -> bool:
        """Always returns True - this strategy works on any document.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            True (always can chunk any document)
        """
        return content is not None and len(content.strip()) > 0

    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """Create fixed-length chunks from document.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            List of fixed-length chunks

        Raises:
            ValueError: If document has no content
        """
        if not content or not content.strip():
            raise ValueError("Document has no content")

        content = content.strip()
        words = content.split()

        if len(words) < self.min_words:
            # Document is too short, return as single chunk
            return [Chunk(
                document_id=document.id or 0,
                chunk_index=0,
                chunk_type="paragraph",
                title=f"Document Content ({len(words)} words)",
                content=content,
                word_count=len(words),
                metadata={
                    "strategy": "fixed_length",
                    "target_words": self.target_words,
                    "actual_words": len(words),
                    "is_complete_document": True
                }
            )]

        chunks = []
        chunk_start = 0
        chunk_index = 0

        while chunk_start < len(words):
            # Determine chunk end position
            chunk_end = min(chunk_start + self.target_words, len(words))

            # Try to find a good break point
            chunk_end = self._find_break_point(
                words, chunk_start, chunk_end, len(words)
            )

            # Extract chunk words and reconstruct text
            chunk_words = words[chunk_start:chunk_end]
            chunk_text = ' '.join(chunk_words)

            # Find original text boundaries for better formatting
            chunk_content = self._reconstruct_formatting(content, chunk_text)

            # Create chunk
            chunk = Chunk(
                document_id=document.id or 0,
                chunk_index=chunk_index,
                chunk_type="paragraph",
                title=self._generate_title(chunk_content, chunk_index),
                content=chunk_content,
                word_count=len(chunk_words),
                metadata={
                    "strategy": "fixed_length",
                    "target_words": self.target_words,
                    "actual_words": len(chunk_words),
                    "start_word": chunk_start,
                    "end_word": chunk_end,
                    "is_final_chunk": chunk_end >= len(words)
                }
            )

            chunks.append(chunk)
            chunk_start = chunk_end
            chunk_index += 1

        return chunks

    def _find_break_point(
        self, words: List[str], start: int, target_end: int, total_words: int
    ) -> int:
        """Find the best break point near the target end position.

        Args:
            words: List of all words
            start: Start position
            target_end: Target end position
            total_words: Total number of words

        Returns:
            Optimal break point position
        """
        # If we're at the end, take everything
        if target_end >= total_words:
            return total_words

        # Don't create chunks that are too small
        min_end = start + self.min_words
        if target_end < min_end:
            target_end = min_end

        # Don't create chunks that are too large
        max_end = start + self.max_words
        if target_end > max_end:
            target_end = max_end

        # Look for paragraph break (double newline) within reasonable range
        search_start = max(start, target_end - 50)
        search_end = min(total_words, target_end + 50)

        for i in range(target_end, search_start - 1, -1):
            if i < len(words) and '\n\n' in words[i]:
                return i + 1

        # Look for sentence endings
        for i in range(target_end, search_start - 1, -1):
            if i < len(words) and re.search(r'[.!?]$', words[i]):
                return i + 1

        # Look forward for sentence endings (within limits)
        for i in range(target_end, search_end):
            if i < len(words) and re.search(r'[.!?]$', words[i]):
                return i + 1

        # No good break point found, use target
        return min(target_end, total_words)

    def _reconstruct_formatting(
        self, original_content: str, chunk_text: str
    ) -> str:
        """Attempt to preserve original formatting in chunk.

        Args:
            original_content: Original document content (unused for now)
            chunk_text: Space-separated chunk text

        Returns:
            Chunk text with preserved formatting
        """
        # This is a simplified approach - in practice, you might want
        # to maintain a mapping of word positions to original positions
        # For now, we'll use the chunk_text as-is but could enhance later
        _ = original_content  # Acknowledge unused parameter
        return chunk_text.strip()

    def _generate_title(self, content: str, chunk_index: int) -> str:
        """Generate a meaningful title for the chunk.

        Args:
            content: Chunk content
            chunk_index: Zero-based chunk index

        Returns:
            Generated title
        """
        # Try to extract first sentence or line as title
        lines = content.split('\n')
        first_line = lines[0].strip() if lines else ""

        if first_line and len(first_line) <= 80:
            # Use first line if it's reasonable length
            return self._clean_title(first_line)

        # Extract first few words
        words = content.split()
        if len(words) > 0:
            title_words = words[:8]  # First 8 words
            title = ' '.join(title_words)
            if len(words) > 8:
                title += "..."
            return self._clean_title(title)

        # Fallback
        return f"Section {chunk_index + 1}"
