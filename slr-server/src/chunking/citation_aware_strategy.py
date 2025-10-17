"""
Citation-aware chunking strategy for research papers.

Creates chunks that preserve citation contexts and reference relationships,
ensuring that citations are not split from their surrounding context.
Optimized for citation analysis and reference network building.
"""

import re
from typing import List, Tuple, Set

from ..domain.models import AcademicChunk, ResearchPaper
from .base_academic_strategy import BaseAcademicStrategy


class CitationAwareStrategy(BaseAcademicStrategy):
    """
    Chunks research papers while preserving citation contexts.

    This strategy ensures that citations are never split from their
    surrounding context, creating chunks that are optimal for:
    - Citation network analysis
    - Reference pattern detection
    - Context-aware citation extraction
    - Bibliography analysis

    Features:
    - Detects various citation formats (APA, IEEE, Nature, etc.)
    - Preserves citation context (surrounding sentences)
    - Groups related citations together
    - Maintains reference integrity across chunks
    - Identifies citation-dense regions for special handling
    """

    # Various citation patterns found in academic papers
    CITATION_PATTERNS = [
        # Author-year citations: (Smith, 2023), (Jones et al., 2022)
        r'\([A-Z][a-zA-Z\s,&]+,?\s+\d{4}[a-z]?\)',
        r'\([A-Z][a-zA-Z\s,&]+\s+et\s+al\.,?\s+\d{4}[a-z]?\)',
        
        # Multiple author-year citations: (Smith, 2023; Jones, 2022)
        r'\([A-Z][a-zA-Z\s,&]+,?\s+\d{4}[a-z]?(?:;\s*[A-Z][a-zA-Z\s,&]+,?\s+\d{4}[a-z]?)+\)',
        
        # Numbered citations: [1], [1,2,3], [1-5]
        r'\[\d+\]',
        r'\[\d+(?:\s*,\s*\d+)+\]',
        r'\[\d+\s*[-–]\s*\d+\]',
        
        # Superscript-style citations: Smith^1^, method^1,2,3^
        r'\w+\^\d+(?:\s*,\s*\d+)*\^',
        
        # In-text author citations: Smith (2023) showed that...
        r'\b[A-Z][a-zA-Z]+\s+\(\d{4}[a-z]?\)\s+(?:showed|demonstrated|found|reported|argued|suggested)',
        r'\b[A-Z][a-zA-Z]+\s+et\s+al\.\s+\(\d{4}[a-z]?\)\s+(?:showed|demonstrated|found|reported|argued|suggested)',
        
        # DOI and URL citations
        r'doi:\s*10\.\d+/[^\s]+',
        r'https?://[^\s]+',
    ]

    # Sentence boundary patterns
    SENTENCE_ENDINGS = r'[.!?]\s+'
    
    # Minimum and maximum chunk sizes
    MIN_CHUNK_WORDS = 50
    MAX_CHUNK_WORDS = 500
    CITATION_CONTEXT_SENTENCES = 2  # Sentences before and after citation

    def can_chunk(self, paper: ResearchPaper, content: str) -> bool:
        """
        Check if paper contains sufficient citations for citation-aware chunking.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            True if paper has substantial citations
        """
        if not content:
            return False

        # Count total citations in document
        total_citations = self._count_citations(content)
        
        # Require at least 10 citations for citation-aware strategy
        if total_citations < 10:
            return False

        # Check for citation distribution (not all in references section)
        # Split into rough thirds and check middle section has citations
        content_length = len(content)
        middle_section = content[content_length//3:2*content_length//3]
        middle_citations = self._count_citations(middle_section)
        
        # At least 30% of citations should be in the middle section
        return middle_citations >= (total_citations * 0.3)

    def chunk(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """
        Create citation-aware chunks from the research paper.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            List of citation-aware academic chunks

        Raises:
            ValueError: If paper cannot be chunked by this strategy
        """
        if not content:
            raise ValueError("Paper has no content")

        # Find all citations and their positions
        citations = self._find_citations_with_context(content)
        
        if not citations:
            raise ValueError("No citations found for citation-aware chunking")

        # Create chunks based on citation boundaries and contexts
        chunks = self._create_citation_aware_chunks(content, citations)
        
        if not chunks:
            raise ValueError("Could not create citation-aware chunks")

        # Process chunks and add academic metadata
        processed_chunks = []
        for i, chunk_data in enumerate(chunks):
            content_text, start_pos, citations_in_chunk = chunk_data
            
            # Calculate position ratio
            position_ratio = start_pos / len(content) if len(content) > 0 else 0.0
            
            # Extract title (first line or sentence)
            title = self._extract_chunk_title(content_text)
            
            # Detect section type
            section_type = self._detect_section_type(title, content_text, position_ratio)
            
            # Count figures, tables, and other elements
            citation_count = len(citations_in_chunk)
            figure_count, table_count = self._count_figures_tables(content_text)
            research_elements = self._extract_research_elements(content_text, section_type)
            semantic_tags = self._generate_semantic_tags(content_text, section_type)
            
            # Add citation-specific semantic tags
            semantic_tags.extend(self._extract_citation_semantic_tags(citations_in_chunk))

            # Create academic chunk
            chunk = AcademicChunk(
                paper_id=paper.id or 0,
                chunk_index=i,
                content=content_text.strip(),
                section_type=section_type,
                title=self._clean_title(title),
                word_count=self._calculate_word_count(content_text),
                citation_count=citation_count,
                figure_count=figure_count,
                table_count=table_count,
                research_elements=research_elements,
                semantic_tags=list(set(semantic_tags)),  # Remove duplicates
                metadata={
                    "strategy": "citation_aware",
                    "start_position": start_pos,
                    "position_ratio": position_ratio,
                    "citation_density": citation_count / max(1, self._calculate_word_count(content_text)),
                    "citations": [self._extract_citation_info(cit) for cit in citations_in_chunk],
                    "citation_types": list(set(self._classify_citations(citations_in_chunk))),
                    "has_multiple_citations": citation_count > 1,
                    "context_preserved": True
                }
            )

            # Calculate confidence score
            chunk.confidence_score = self._calculate_confidence_score(chunk)
            
            processed_chunks.append(chunk)

        return processed_chunks

    def _find_citations_with_context(self, content: str) -> List[Tuple[int, int, str, str]]:
        """
        Find all citations with their positions and surrounding context.

        Args:
            content: Full paper content

        Returns:
            List of (start_pos, end_pos, citation_text, context) tuples
        """
        citations = []
        
        for pattern in self.CITATION_PATTERNS:
            for match in re.finditer(pattern, content):
                start_pos = match.start()
                end_pos = match.end()
                citation_text = match.group()
                
                # Extract surrounding context
                context = self._extract_citation_context(content, start_pos, end_pos)
                
                citations.append((start_pos, end_pos, citation_text, context))
        
        # Sort by position and remove overlapping citations
        citations.sort()
        return self._remove_overlapping_citations(citations)

    def _extract_citation_context(self, content: str, start_pos: int, end_pos: int) -> str:
        """
        Extract context around a citation (surrounding sentences).

        Args:
            content: Full content
            start_pos: Citation start position
            end_pos: Citation end position

        Returns:
            Context string containing citation and surrounding text
        """
        # Find sentence boundaries before and after citation
        before_text = content[:start_pos]
        after_text = content[end_pos:]
        
        # Find sentences before citation
        before_sentences = re.split(self.SENTENCE_ENDINGS, before_text)
        before_context = ' '.join(before_sentences[-self.CITATION_CONTEXT_SENTENCES:])
        
        # Find sentences after citation
        after_sentences = re.split(self.SENTENCE_ENDINGS, after_text)
        after_context = ' '.join(after_sentences[:self.CITATION_CONTEXT_SENTENCES])
        
        # Combine context with citation
        citation_text = content[start_pos:end_pos]
        full_context = f"{before_context.strip()} {citation_text} {after_context.strip()}"
        
        return full_context.strip()

    def _remove_overlapping_citations(self, citations: List[Tuple[int, int, str, str]]) -> List[Tuple[int, int, str, str]]:
        """Remove overlapping citations, keeping the longest ones."""
        if not citations:
            return []
        
        filtered_citations = []
        last_end = -1
        
        for start_pos, end_pos, citation_text, context in citations:
            if start_pos >= last_end:  # No overlap
                filtered_citations.append((start_pos, end_pos, citation_text, context))
                last_end = end_pos
        
        return filtered_citations

    def _create_citation_aware_chunks(self, content: str, citations: List[Tuple[int, int, str, str]]) -> List[Tuple[str, int, List[Tuple]]]:
        """
        Create chunks that preserve citation contexts.

        Args:
            content: Full content
            citations: List of citation data

        Returns:
            List of (chunk_content, start_position, citations_in_chunk) tuples
        """
        if not citations:
            return []

        chunks = []
        current_start = 0
        current_citations = []
        
        for i, (cit_start, cit_end, cit_text, context) in enumerate(citations):
            # Calculate context boundaries
            context_start = max(current_start, cit_start - len(context) // 2)
            context_end = min(len(content), cit_end + len(context) // 2)
            
            # Check if we should start a new chunk
            if (self._should_start_new_chunk(current_start, context_start, content) or
                len(current_citations) >= 5):  # Max citations per chunk
                
                # Finalize current chunk if we have content
                if current_start < cit_start:
                    chunk_end = context_start
                    chunk_content = content[current_start:chunk_end]
                    
                    if self._calculate_word_count(chunk_content) >= self.MIN_CHUNK_WORDS:
                        chunks.append((chunk_content, current_start, current_citations.copy()))
                
                # Start new chunk
                current_start = context_start
                current_citations = []
            
            # Add citation to current chunk
            current_citations.append((cit_start, cit_end, cit_text, context))
            
            # If this is the last citation or chunk is getting too large
            if (i == len(citations) - 1 or 
                self._calculate_word_count(content[current_start:context_end]) >= self.MAX_CHUNK_WORDS):
                
                # Finalize chunk
                chunk_end = min(len(content), context_end)
                chunk_content = content[current_start:chunk_end]
                
                if self._calculate_word_count(chunk_content) >= self.MIN_CHUNK_WORDS:
                    chunks.append((chunk_content, current_start, current_citations.copy()))
                
                # Reset for next chunk
                current_start = chunk_end
                current_citations = []

        # Handle any remaining content
        if current_start < len(content):
            remaining_content = content[current_start:]
            if self._calculate_word_count(remaining_content) >= self.MIN_CHUNK_WORDS:
                chunks.append((remaining_content, current_start, []))

        return chunks

    def _should_start_new_chunk(self, current_start: int, next_citation_start: int, content: str) -> bool:
        """Determine if a new chunk should be started."""
        current_content = content[current_start:next_citation_start]
        word_count = self._calculate_word_count(current_content)
        
        # Start new chunk if current one is getting too large
        return word_count >= self.MAX_CHUNK_WORDS

    def _extract_chunk_title(self, content: str) -> str:
        """Extract a meaningful title from chunk content."""
        lines = content.split('\n')
        
        # Look for section headers or first substantial line
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not line.lower().startswith(('the', 'this', 'a ', 'an ')):
                # If line looks like a header, use it
                if (len(line.split()) <= 10 and 
                    any(char.isupper() for char in line) and
                    not line.endswith('.')):
                    return line
        
        # Fallback: use first sentence
        sentences = re.split(r'[.!?]\s+', content)
        first_sentence = sentences[0].strip() if sentences else content[:100]
        return first_sentence[:100] + "..." if len(first_sentence) > 100 else first_sentence

    def _extract_citation_info(self, citation_data: Tuple[int, int, str, str]) -> dict:
        """Extract structured information from citation."""
        start_pos, end_pos, citation_text, context = citation_data
        
        return {
            "text": citation_text,
            "start_position": start_pos,
            "end_position": end_pos,
            "type": self._classify_single_citation(citation_text),
            "context_snippet": context[:100] + "..." if len(context) > 100 else context
        }

    def _classify_citations(self, citations: List[Tuple]) -> List[str]:
        """Classify citation types in the chunk."""
        types = []
        for citation_data in citations:
            citation_text = citation_data[2]  # citation_text is at index 2
            citation_type = self._classify_single_citation(citation_text)
            types.append(citation_type)
        return types

    def _classify_single_citation(self, citation_text: str) -> str:
        """Classify a single citation by its format."""
        if re.match(r'\[\d+\]', citation_text):
            return "numbered"
        elif re.match(r'\([A-Z].*\d{4}.*\)', citation_text):
            return "author_year"
        elif re.match(r'\w+\^\d+', citation_text):
            return "superscript"
        elif "doi:" in citation_text.lower():
            return "doi"
        elif citation_text.startswith(('http', 'www')):
            return "url"
        else:
            return "other"

    def _extract_citation_semantic_tags(self, citations: List[Tuple]) -> List[str]:
        """Extract semantic tags based on citation characteristics."""
        tags = []
        
        if len(citations) > 3:
            tags.append("citation_rich")
        
        citation_types = self._classify_citations(citations)
        if "author_year" in citation_types:
            tags.append("apa_style")
        if "numbered" in citation_types:
            tags.append("ieee_style")
        if "doi" in citation_types:
            tags.append("doi_citations")
        
        # Check for citation clusters (multiple citations close together)
        if len(citations) > 1:
            positions = [cit[0] for cit in citations]  # start positions
            gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else float('inf')
            
            if avg_gap < 200:  # Characters - close citations
                tags.append("citation_cluster")
        
        return tags

    def get_strategy_name(self) -> str:
        """Get the name of this chunking strategy."""
        return "citation_aware"