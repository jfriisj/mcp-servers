"""Slide-based chunking strategy for presentation documents.

This strategy is designed for slide presentations, lectures, and similar documents
where content is structured as individual slides rather than continuous text.
"""

import re
from typing import List, Dict, Any
from .base_strategy import BaseChunkingStrategy
from ..models.chunk import Chunk
from ..models.document import Document


class SlideStrategy(BaseChunkingStrategy):
    """
    Chunks documents by detecting slide boundaries.
    
    Designed for PowerPoint exports, lecture slides, and presentation PDFs
    where content is organized as discrete slides with headers, bullets, etc.
    
    Detection patterns:
    - Slide numbers (1/50, Slide 2, etc.)
    - Repeated header patterns
    - Page breaks with title patterns
    - Bullet-heavy short-line content
    """
    
    def __init__(self):
        # Patterns for detecting slide boundaries
        self.slide_patterns = [
            # Slide numbering patterns
            r'(?:Slide\s+|Page\s+)?(\d+)(?:\s*[/|]\s*\d+)?',
            # Numbered slides at start of line
            r'^\s*(\d+)(?:\.|:|\s)\s*[A-Z][^a-z]*$',
            # Title patterns (short lines, often capitalized)
            r'^[A-Z][A-Z\s]{3,30}$',
            # Section headers
            r'^[^\w]*([A-Z][^a-z]{3,40})[^\w]*$',
            # Agenda/outline patterns
            r'(?:Agenda|Outline|Overview|Contents?):\s*',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
                                for pattern in self.slide_patterns]
    
    def can_chunk(self, document: Document, content: str) -> bool:
        """
        Check if document appears to be slide-based content.
        
        Args:
            document: Document metadata
            content: Document text content
            
        Returns:
            True if content appears to be slide-based
        """
        if not content:
            return False
        
        lines = content.split('\n')
        total_lines_with_content = sum(1 for line in lines if len(line.strip()) > 0)
        
        if total_lines_with_content == 0:
            return False
        
        # Check short line ratio (indicator of slide content)
        short_lines = sum(1 for line in lines if 0 < len(line.strip()) < 50)
        short_line_ratio = short_lines / total_lines_with_content
        
        # Check words per page (low ratio indicates slide content)
        pages = document.total_pages or 1
        words = len(content.split())
        words_per_page = words / pages if pages > 0 else 0
        
        # Check for slide-specific patterns
        slide_indicators = (
            content.count("•") + content.count("*") + content.count("-") +  # Bullets
            content.lower().count("slide ") +  # Slide references
            len([line for line in lines if line.strip().startswith(tuple("123456789"))])  # Numbered lists
        )
        
        # Decision logic: consider it slide content if:
        # - High ratio of short lines (>70%) OR
        # - Low words per page (<50) AND slide indicators present
        return (
            short_line_ratio > 0.7 or
            (words_per_page < 50 and slide_indicators > 10)
        )
    
    def chunk(self, document: Document, content: str) -> List[Chunk]:
        """
        Split document into slide-based chunks.
        
        Args:
            document: Document to chunk
            content: Raw text content of the document
            
        Returns:
            List of chunks, each representing a slide or slide group
        """
        lines = content.split('\n')
        
        # Detect slide boundaries
        slide_breaks = self._find_slide_boundaries(lines)
        
        # If no clear slides detected, fall back to content-based splitting
        if len(slide_breaks) < 2:
            return self._fallback_chunk_by_content(document, lines)
        
        chunks = []
        
        for i, (start_line, title) in enumerate(slide_breaks):
            # Determine end line (next slide start or end of document)
            end_line = slide_breaks[i + 1][0] if i + 1 < len(slide_breaks) else len(lines)
            
            # Extract slide content
            slide_lines = lines[start_line:end_line]
            slide_content = '\n'.join(slide_lines).strip()
            
            if not slide_content:
                continue
            
            # Generate meaningful title
            chunk_title = title or f"Slide {i + 1}"
            
            # Create chunk
            chunk = Chunk(
                document_id=document.id or 0,
                chunk_index=i,
                chunk_type="slide",
                title=chunk_title,
                content=slide_content,
                word_count=len(slide_content.split()),
                metadata={
                    "slide_number": i + 1,
                    "start_line": start_line,
                    "end_line": end_line,
                    "detection_method": "slide_pattern"
                }
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _find_slide_boundaries(self, lines: List[str]) -> List[tuple]:
        """
        Find potential slide boundary lines.
        
        Returns:
            List of (line_number, title) tuples for slide starts
        """
        slide_breaks = [(0, "Introduction")]  # Always start with first line
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Check for slide number patterns
            for pattern in self.compiled_patterns:
                match = pattern.search(line_stripped)
                if match:
                    # Potential slide boundary detected
                    title = self._extract_slide_title(lines, i)
                    slide_breaks.append((i, title))
                    break
        
        # Remove duplicates and sort by line number
        slide_breaks = list(set(slide_breaks))
        slide_breaks.sort(key=lambda x: x[0])
        
        # Filter out slides that are too close together (< 5 lines)
        filtered_breaks = [slide_breaks[0]]
        
        for current_break in slide_breaks[1:]:
            last_break = filtered_breaks[-1]
            if current_break[0] - last_break[0] >= 5:  # Minimum 5 lines per slide
                filtered_breaks.append(current_break)
        
        return filtered_breaks
    
    def _extract_slide_title(self, lines: List[str], start_line: int) -> str:
        """
        Extract a meaningful title for the slide starting at start_line.
        
        Looks for the first substantial line that could serve as a title.
        """
        # Check current line and next few lines for title
        for i in range(start_line, min(start_line + 5, len(lines))):
            line = lines[i].strip()
            
            # Skip empty lines and pure numbers
            if not line or line.isdigit() or len(line) < 3:
                continue
            
            # Skip lines with only special characters
            if not any(c.isalpha() for c in line):
                continue
            
            # Good candidate for title
            if 5 <= len(line) <= 50:
                # Clean up title
                title = re.sub(r'[^\w\s-]', ' ', line)  # Remove special chars except hyphens
                title = ' '.join(title.split())  # Normalize whitespace
                return title[:40]  # Limit length
        
        # Fallback
        return f"Slide {start_line + 1}"
    
    def _fallback_chunk_by_content(self, document: Document, lines: List[str]) -> List[Chunk]:
        """
        Fallback method when slide detection fails.
        
        Groups content by logical sections based on line patterns.
        """
        chunks = []
        current_chunk_lines = []
        current_title = "Content Section 1"
        chunk_count = 0
        
        target_lines_per_chunk = max(10, len(lines) // 6)  # Aim for ~6 chunks
        
        for i, line in enumerate(lines):
            current_chunk_lines.append(line)
            
            # Check if we should start a new chunk
            should_break = (
                len(current_chunk_lines) >= target_lines_per_chunk and
                (line.strip() == '' or  # Empty line
                 (len(line.strip()) < 30 and line.strip().isupper()) or  # Potential header
                 any(line.strip().startswith(prefix) for prefix in ['•', '*', '-', str(j)]) for j in range(1, 10))  # List item
            )
            
            if should_break and len(current_chunk_lines) > 5:
                # Create chunk from accumulated lines
                content = '\n'.join(current_chunk_lines[:-1]).strip()  # Exclude break line
                
                if content:
                    chunk = Chunk(
                        document_id=document.id or 0,
                        chunk_index=chunk_count,
                        chunk_type="slide",
                        title=current_title,
                        content=content,
                        word_count=len(content.split()),
                        metadata={
                            "detection_method": "content_fallback",
                            "chunk_number": chunk_count + 1
                        }
                    )
                    chunks.append(chunk)
                    chunk_count += 1
                
                # Start new chunk
                current_chunk_lines = [line] if line.strip() else []
                current_title = f"Content Section {chunk_count + 1}"
        
        # Add final chunk
        if current_chunk_lines:
            content = '\n'.join(current_chunk_lines).strip()
            if content:
                chunk = Chunk(
                    document_id=document.id or 0,
                    chunk_index=chunk_count,
                    chunk_type="slide",
                    title=current_title,
                    content=content,
                    word_count=len(content.split()),
                    metadata={
                        "detection_method": "content_fallback",
                        "chunk_number": chunk_count + 1
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Return information about this chunking strategy."""
        return {
            "name": "slide",
            "description": "Chunks documents by slide boundaries and presentation structure",
            "best_for": ["presentations", "lecture_slides", "slide_pdfs", "bullet_heavy_content"],
            "chunk_type": "slide",
            "patterns_count": len(self.slide_patterns)
        }