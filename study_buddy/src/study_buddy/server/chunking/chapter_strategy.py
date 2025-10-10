"""Chapter-based chunking strategy for books and structured documents.

Detects chapter markers using common patterns and creates chunks
for each chapter. Ideal for books, manuals, and long-form content.
"""

import re
from typing import List, Optional, Tuple

from ..models.chunk import Chunk
from ..models.document import Document

from .base_strategy import BaseChunkingStrategy


class ChapterStrategy(BaseChunkingStrategy):
    """Chunks documents by detecting chapter boundaries.

    This strategy looks for common chapter patterns like:
    - "Chapter 1", "Chapter One", "CH 1"
    - "1.", "2.", "3." at start of lines
    - "CHAPTER I", "CHAPTER II" (Roman numerals)
    - Numbered headings in structured documents

    Follows Single Responsibility Principle - only handles chapter detection.
    """

    # Chapter detection patterns (in priority order)
    CHAPTER_PATTERNS = [
        # "Chapter 1", "Chapter One", "Chapter I"
        (r'^\s*(?:Chapter|CHAPTER|Ch\.|CH\.?)\s+'
         r'([IVXivx0-9]+|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|'
         r'[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en)\s*[:\-\.]?\s*(.+)?$'),

        # "1.", "2.", "3." at start of line with title
        r'^\s*([0-9]+)\.\s+(.+)$',

        # "I.", "II.", "III." Roman numerals
        r'^\s*([IVX]+)\.\s+(.+)$',

        # Markdown-style headers that look like chapters
        (r'^#{1,2}\s+(?:Chapter|Ch\.?)\s*([0-9]+|[IVX]+)\s*'
         r'[:\-\.]?\s*(.+)?$'),
    ]

    def can_chunk(self, document: Document, content: str) -> bool:
        """Check if document contains chapter markers.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            True if chapter patterns are found
        """
        if not content:
            return False

        # Look for at least 2 chapter markers
        chapter_count = 0
        for pattern in self.CHAPTER_PATTERNS:
            matches = re.findall(
                pattern, content, re.MULTILINE | re.IGNORECASE
            )
            chapter_count += len(matches)
            if chapter_count >= 2:
                return True

        return False

    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """Create chunks by splitting on chapter boundaries.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            List of chapter chunks

        Raises:
            ValueError: If no chapters found
        """
        if not content:
            raise ValueError("Document has no content")

        chapters = self._find_chapters(content)

        if not chapters:
            raise ValueError("No chapters found in document")

        chunks = []
        for i, chapter_data in enumerate(chapters):
            title, chap_content, chapter_num, start_pos = chapter_data
            chunk = Chunk(
                document_id=document.id or 0,
                chunk_index=i,
                chunk_type="chapter",
                title=self._clean_title(
                    title or f"Chapter {chapter_num or i+1}"
                ),
                content=chap_content.strip(),
                word_count=self._calculate_word_count(chap_content),
                metadata={
                    "chapter_number": chapter_num or i + 1,
                    "strategy": "chapter",
                    "start_position": start_pos,
                    "detection_pattern": "chapter_markers"
                }
            )
            chunks.append(chunk)

        return chunks

    def _find_chapters(
        self, content: str
    ) -> List[Tuple[Optional[str], str, Optional[int], int]]:
        """Find chapter boundaries and extract content.

        Args:
            content: Full document content

        Returns:
            List of (title, content, chapter_number, start_position) tuples
        """
        chapters = []
        lines = content.split('\n')

        # Find all chapter markers
        chapter_markers = []
        for i, line in enumerate(lines):
            for pattern in self.CHAPTER_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    chapter_num = self._extract_chapter_number(match.group(1))
                    # Use the entire line as the title for better preservation
                    title = line.strip()
                    chapter_markers.append((i, title, chapter_num, line))
                    break

        if not chapter_markers:
            return []

        # Extract content between markers
        for i, marker_data in enumerate(chapter_markers):
            line_num, title, chapter_num, header_line = marker_data
            start_line = line_num

            # Find end line (next chapter or end of document)
            if i + 1 < len(chapter_markers):
                end_line = chapter_markers[i + 1][0]
            else:
                end_line = len(lines)

            # Extract chapter content (excluding the header line)
            chapter_lines = lines[start_line + 1:end_line]
            chapter_content = '\n'.join(chapter_lines).strip()

            # Include header if title is part of it
            if title:
                chapter_content = header_line + '\n' + chapter_content

            # Calculate start position in original text
            start_pos = sum(len(line) + 1 for line in lines[:start_line])

            chapters.append((title, chapter_content, chapter_num, start_pos))

        return chapters

    def _extract_chapter_number(self, num_str: str) -> Optional[int]:
        """Extract numeric chapter number from string.

        Args:
            num_str: String containing chapter number

        Returns:
            Integer chapter number or None if cannot parse
        """
        if not num_str:
            return None

        # Try direct integer conversion
        try:
            return int(num_str)
        except ValueError:
            pass

        # Try Roman numeral conversion
        roman_map = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
            'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20
        }

        num_upper = num_str.upper()
        if num_upper in roman_map:
            return roman_map[num_upper]

        # Try word numbers
        word_map = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        num_lower = num_str.lower()
        if num_lower in word_map:
            return word_map[num_lower]

        return None
