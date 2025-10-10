"""Section-based chunking strategy for academic papers and reports.

Detects standard academic sections like Abstract, Introduction, Methods,
Results, Discussion, and Conclusion. Ideal for research papers.
"""

import re
from typing import List, Tuple

from ..models.chunk import Chunk
from ..models.document import Document

from .base_strategy import BaseChunkingStrategy


class SectionStrategy(BaseChunkingStrategy):
    """Chunks documents by detecting academic paper sections.

    This strategy looks for standard academic sections:
    - Abstract
    - Introduction
    - Methods/Methodology
    - Results/Findings
    - Discussion
    - Conclusion
    - References/Bibliography

    Follows Single Responsibility Principle - only handles section detection.
    """

    # Standard academic sections (in typical order)
    SECTION_PATTERNS = [
        # Abstract variations
        (r'^\s*(?:Abstract|ABSTRACT)\s*$', 'abstract'),
        (r'^\s*(?:Abstract|ABSTRACT)\s*[—–-]', 'abstract'),  # With em-dash or dash
        
        # Introduction variations  
        (r'^\s*(?:Introduction|INTRODUCTION)\s*$', 'introduction'),
        (r'^\s*(?:I|1)\.\s*(?:Introduction|INTRODUCTION)\s*$', 'introduction'),
        
        # Methods variations
        (r'^\s*(?:Methods?|METHODS?|Methodology|METHODOLOGY)\s*$', 'methods'),
        (r'^\s*(?:II|III|2|3)\.\s*(?:Methods?|METHODS?|Methodology|METHODOLOGY)', 'methods'),
        
        # Results variations
        (r'^\s*(?:Results?|RESULTS?|Findings?|FINDINGS?)\s*$', 'results'),
        (r'^\s*(?:III|IV|V|3|4|5)\.\s*(?:Results?|RESULTS?|Findings?|FINDINGS?)', 'results'),
        
        # Discussion variations
        (r'^\s*(?:Discussion|DISCUSSION)\s*$', 'discussion'),
        (r'^\s*(?:IV|V|VI|4|5|6)\.\s*(?:Discussion|DISCUSSION)', 'discussion'),
        
        # Conclusion variations
        (r'^\s*(?:Conclusion|CONCLUSION|Conclusions|CONCLUSIONS)\s*$', 'conclusion'),
        (r'^\s*(?:V|VI|VII|5|6|7)\.\s*(?:Conclusion|CONCLUSION)', 'conclusion'),
        
        # References
        (r'^\s*(?:References?|REFERENCES?|Bibliography|BIBLIOGRAPHY)\s*$', 'references'),
        
        # Roman numeral sections (catch-all for other sections)
        (r'^\s*(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+[A-Z][A-Z\s\-]*$', 'numbered'),
        
        # Regular numbered sections
        (r'^\s*([1-9][0-9]?)\.\s+[A-Z][A-Z\s\-]*$', 'numbered'),
    ]

    def can_chunk(self, document: Document, content: str) -> bool:
        """Check if document contains academic section markers.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            True if academic sections are found
        """
        if not content:
            return False

        # Look for at least 3 different section types
        found_sections = set()
        for pattern, section_type in self.SECTION_PATTERNS:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                found_sections.add(section_type)

        return len(found_sections) >= 3

    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """Create chunks by splitting on section boundaries.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            List of section chunks

        Raises:
            ValueError: If no sections found
        """
        if not content:
            raise ValueError("Document has no content")

        sections = self._find_sections(content)

        if not sections:
            raise ValueError("No academic sections found in document")

        chunks = []
        for i, section_data in enumerate(sections):
            title, section_content, section_type, start_pos = section_data
            chunk = Chunk(
                document_id=document.id or 0,
                chunk_index=i,
                chunk_type="section",
                title=self._clean_title(title),
                content=section_content.strip(),
                word_count=self._calculate_word_count(section_content),
                metadata={
                    "section_type": section_type,
                    "strategy": "section",
                    "start_position": start_pos,
                    "detection_pattern": "academic_sections"
                }
            )
            chunks.append(chunk)

        return chunks

    def _find_sections(self, content: str) -> List[Tuple[str, str, str, int]]:
        """Find section boundaries and extract content.

        Args:
            content: Full document content

        Returns:
            List of (title, content, section_type, start_position) tuples
        """
        sections = []
        lines = content.split('\n')

        # Find all section markers
        section_markers = []
        for i, line in enumerate(lines):
            for pattern, section_type in self.SECTION_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    title = line.strip()
                    section_markers.append((i, title, section_type))
                    break

        if not section_markers:
            return []

        # Extract content between markers
        for i, (line_num, title, section_type) in enumerate(section_markers):
            start_line = line_num

            # Find end line (next section or end of document)
            if i + 1 < len(section_markers):
                end_line = section_markers[i + 1][0]
            else:
                end_line = len(lines)

            # Extract section content (excluding the header line)
            section_lines = lines[start_line + 1:end_line]
            section_content = '\n'.join(section_lines).strip()

            # Include header
            if section_content:
                section_content = title + '\n' + section_content
            else:
                section_content = title

            # Calculate start position in original text
            start_pos = sum(len(line) + 1 for line in lines[:start_line])

            sections.append((title, section_content, section_type, start_pos))

        return sections
