"""Heading-based chunking strategy for structured documents.

Splits documents on Markdown headings (#, ##, ###) or HTML headings.
Ideal for Markdown documents, documentation, and structured content.
"""

import re
from typing import List, Tuple

from ..models.chunk import Chunk
from ..models.document import Document

from .base_strategy import BaseChunkingStrategy


class HeadingStrategy(BaseChunkingStrategy):
    """Chunks documents by splitting on heading markers.

    This strategy detects:
    - Markdown headings: #, ##, ###, ####
    - HTML headings: <h1>, <h2>, <h3>, <h4>
    - Underlined headings (=== and ---)

    Maintains heading hierarchy and creates meaningful chunk titles.
    Follows Single Responsibility Principle - only handles heading detection.
    """

    # Heading detection patterns
    HEADING_PATTERNS = [
        # Markdown headings: # Title (allow leading whitespace)
        (r'^\s*(#{1,6})\s+(.+)$', 'markdown'),

        # HTML headings: <h1>Title</h1>, <h2>Title</h2>
        (r'^\s*<(h[1-6])>(.+?)</h[1-6]>\s*$', 'html'),

        # Underlined headings (Setext style)
        (r'^(.+)\n={3,}\s*$', 'setext_h1'),
        (r'^(.+)\n-{3,}\s*$', 'setext_h2'),
    ]

    def can_chunk(self, document: Document, content: str) -> bool:
        """Check if document contains heading markers."""
        if not content:
            return False

        # Look for at least 3 headings
        heading_count = 0
        for pattern, _ in self.HEADING_PATTERNS:
            matches = re.findall(
                pattern, content, re.MULTILINE | re.IGNORECASE
            )
            heading_count += len(matches)
            if heading_count >= 3:
                return True

        return False

    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """Create chunks by splitting on heading boundaries."""
        if not content:
            raise ValueError("Document has no content")

        headings = self._find_headings(content)

        if not headings:
            raise ValueError("No headings found in document")

        chunks = []
        for i, heading_data in enumerate(headings):
            title, heading_content, level, heading_type, start_pos = heading_data
            chunk = Chunk(
                document_id=document.id or 0,
                chunk_index=i,
                chunk_type="heading",
                title=self._clean_title(title),
                content=heading_content.strip(),
                word_count=self._calculate_word_count(heading_content),
                metadata={
                    "heading_level": level,
                    "heading_type": heading_type,
                    "strategy": "heading",
                    "start_position": start_pos,
                    "detection_pattern": "heading_markers"
                }
            )
            chunks.append(chunk)

        return chunks

    def _find_headings(self, content: str) -> List[Tuple[str, str, int, str, int]]:
        """Find heading boundaries and extract content."""
        headings = []
        lines = content.split('\n')

        # Find all heading markers
        heading_markers = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for markdown headings (allow leading whitespace)
            match = re.match(r'^\s*(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                heading_markers.append((i, title, level, 'markdown'))
                i += 1
                continue

            i += 1

        if not heading_markers:
            return []

        # Extract content between markers
        for i, marker_data in enumerate(heading_markers):
            line_num, title, level, heading_type = marker_data
            start_line = line_num + 1

            # Find end line
            end_line = len(lines)
            for j in range(i + 1, len(heading_markers)):
                next_line_num, _, next_level, _ = heading_markers[j]
                if next_level <= level:
                    end_line = next_line_num
                    break

            # Extract section content
            section_lines = lines[start_line:end_line]
            section_content = '\n'.join(section_lines).strip()

            # Include the heading line
            heading_line = lines[line_num]
            full_content = heading_line
            if section_content:
                full_content += '\n' + section_content

            # Calculate start position
            start_pos = sum(len(line) + 1 for line in lines[:line_num])

            headings.append((title, full_content, level, heading_type, start_pos))

        return headings
