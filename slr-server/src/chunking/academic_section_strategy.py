"""
Academic section-based chunking strategy for research papers.

Detects and segments academic papers by their structural sections like
Abstract, Introduction, Methods, Results, Discussion, and Conclusion.
Optimized for systematic literature review processing.
"""

import re
from typing import List, Tuple

from ..domain.models import AcademicChunk, ResearchPaper
from .base_academic_strategy import BaseAcademicStrategy


class AcademicSectionStrategy(BaseAcademicStrategy):
    """
    Chunks research papers by detecting academic section boundaries.

    This strategy identifies standard academic sections and creates chunks
    that preserve the logical structure of research papers:
    - Abstract: Paper summary and key findings
    - Introduction: Background and motivation
    - Methods/Methodology: Research approach and procedures
    - Results/Findings: Research outcomes and data
    - Discussion: Interpretation and implications
    - Conclusion: Summary and future work
    - References: Citation list

    Optimized for systematic literature review where section-level analysis
    is crucial for quality assessment and evidence extraction.
    """

    # Enhanced academic section patterns with better detection
    ACADEMIC_SECTION_PATTERNS = [
        # Abstract variations
        (r'^\s*(?:Abstract|ABSTRACT)\s*$', 'abstract'),
        (r'^\s*(?:Abstract|ABSTRACT)\s*[—–:-]', 'abstract'),
        (r'^\s*(?:Executive\s+Summary|EXECUTIVE\s+SUMMARY)', 'abstract'),

        # Introduction variations
        (r'^\s*(?:Introduction|INTRODUCTION)\s*$', 'introduction'),
        (r'^\s*(?:I|1)\.\s*(?:Introduction|INTRODUCTION)', 'introduction'),
        (r'^\s*(?:Background|BACKGROUND)\s*$', 'introduction'),
        (r'^\s*(?:Overview|OVERVIEW)\s*$', 'introduction'),

        # Literature Review (can be separate or part of introduction)
        (r'^\s*(?:Literature\s+Review|LITERATURE\s+REVIEW)', 'background'),
        (r'^\s*(?:Related\s+Work|RELATED\s+WORK)', 'background'),
        (r'^\s*(?:Previous\s+Studies|PREVIOUS\s+STUDIES)', 'background'),

        # Methods variations
        (r'^\s*(?:Methods?|METHODS?)\s*$', 'methods'),
        (r'^\s*(?:Methodology|METHODOLOGY)\s*$', 'methods'),
        (r'^\s*(?:Materials?\s+and\s+Methods?|MATERIALS?\s+AND\s+METHODS?)', 'methods'),
        (r'^\s*(?:Experimental\s+Design|EXPERIMENTAL\s+DESIGN)', 'methods'),
        (r'^\s*(?:Study\s+Design|STUDY\s+DESIGN)', 'methods'),
        (r'^\s*(?:II|III|2|3)\.\s*(?:Methods?|Methodology)', 'methods'),

        # Results variations
        (r'^\s*(?:Results?|RESULTS?)\s*$', 'results'),
        (r'^\s*(?:Findings?|FINDINGS?)\s*$', 'results'),
        (r'^\s*(?:Outcomes?|OUTCOMES?)\s*$', 'results'),
        (r'^\s*(?:Analysis|ANALYSIS)\s*$', 'results'),
        (r'^\s*(?:III|IV|V|3|4|5)\.\s*(?:Results?|Findings?)', 'results'),

        # Discussion variations
        (r'^\s*(?:Discussion|DISCUSSION)\s*$', 'discussion'),
        (r'^\s*(?:Analysis\s+and\s+Discussion|ANALYSIS\s+AND\s+DISCUSSION)', 'discussion'),
        (r'^\s*(?:Interpretation|INTERPRETATION)', 'discussion'),
        (r'^\s*(?:IV|V|VI|4|5|6)\.\s*(?:Discussion)', 'discussion'),

        # Conclusion variations
        (r'^\s*(?:Conclusion|CONCLUSION)\s*$', 'conclusion'),
        (r'^\s*(?:Conclusions|CONCLUSIONS)\s*$', 'conclusion'),
        (r'^\s*(?:Summary|SUMMARY)\s*$', 'conclusion'),
        (r'^\s*(?:Final\s+Remarks|FINAL\s+REMARKS)', 'conclusion'),
        (r'^\s*(?:V|VI|VII|5|6|7)\.\s*(?:Conclusion)', 'conclusion'),

        # Limitations (can be separate section or part of discussion)
        (r'^\s*(?:Limitations?|LIMITATIONS?)\s*$', 'discussion'),
        (r'^\s*(?:Study\s+Limitations?|STUDY\s+LIMITATIONS?)', 'discussion'),

        # Future Work
        (r'^\s*(?:Future\s+Work|FUTURE\s+WORK)', 'conclusion'),
        (r'^\s*(?:Future\s+Research|FUTURE\s+RESEARCH)', 'conclusion'),
        (r'^\s*(?:Recommendations?|RECOMMENDATIONS?)', 'conclusion'),

        # References
        (r'^\s*(?:References?|REFERENCES?)\s*$', 'references'),
        (r'^\s*(?:Bibliography|BIBLIOGRAPHY)\s*$', 'references'),
        (r'^\s*(?:Citations?|CITATIONS?)\s*$', 'references'),

        # Appendix
        (r'^\s*(?:Appendix|APPENDIX)', 'appendix'),
        (r'^\s*(?:Supplementary|SUPPLEMENTARY)', 'appendix'),

        # Generic numbered sections (lower priority)
        (r'^\s*([1-9]\d?)\.\s+[A-Z][A-Z\s\-]*$', 'numbered'),
        (r'^\s*([IVX]+)\.\s+[A-Z][A-Z\s\-]*$', 'numbered'),
    ]

    def can_chunk(self, paper: ResearchPaper, content: str) -> bool:
        """
        Check if paper contains academic section markers.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            True if academic sections are found
        """
        if not content:
            return False

        # Look for at least 3 different academic section types
        found_sections = set()
        for pattern, section_type in self.ACADEMIC_SECTION_PATTERNS:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                found_sections.add(section_type)
                
        # Must find core academic sections
        core_sections = {'introduction', 'methods', 'results', 'discussion'}
        core_found = len(found_sections & core_sections)
        
        # Require at least 3 total sections with at least 2 core sections
        return len(found_sections) >= 3 and core_found >= 2

    def chunk(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """
        Create chunks by splitting on academic section boundaries.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            List of academic section chunks

        Raises:
            ValueError: If no academic sections found
        """
        if not content:
            raise ValueError("Paper has no content")

        sections = self._find_academic_sections(content)

        if not sections:
            raise ValueError("No academic sections found in paper")

        chunks = []
        total_length = len(content)

        for i, section_data in enumerate(sections):
            title, section_content, section_type, start_pos = section_data
            
            # Calculate position ratio for section type detection refinement
            position_ratio = start_pos / total_length if total_length > 0 else 0.0
            
            # Refine section type based on content and position
            refined_section_type = self._detect_section_type(title, section_content, position_ratio)
            if refined_section_type != 'body':
                section_type = refined_section_type

            # Count citations, figures, and tables
            citation_count = self._count_citations(section_content)
            figure_count, table_count = self._count_figures_tables(section_content)

            # Extract research elements and semantic tags
            research_elements = self._extract_research_elements(section_content, section_type)
            semantic_tags = self._generate_semantic_tags(section_content, section_type)

            # Create academic chunk
            chunk = AcademicChunk(
                paper_id=paper.id or 0,
                chunk_index=i,
                content=section_content.strip(),
                section_type=section_type,
                title=self._clean_title(title),
                word_count=self._calculate_word_count(section_content),
                citation_count=citation_count,
                figure_count=figure_count,
                table_count=table_count,
                research_elements=research_elements,
                semantic_tags=semantic_tags,
                metadata={
                    "strategy": "academic_section",
                    "start_position": start_pos,
                    "position_ratio": position_ratio,
                    "original_section_type": section_type,
                    "refined_section_type": refined_section_type,
                    "has_citations": citation_count > 0,
                    "has_figures": figure_count > 0,
                    "has_tables": table_count > 0,
                    "research_element_count": len(research_elements),
                    "semantic_tag_count": len(semantic_tags)
                }
            )

            # Calculate and set confidence score
            confidence_score = self._calculate_confidence_score(chunk)
            chunk.confidence_score = max(0.0, min(1.0, confidence_score))  # Ensure within valid range
            
            chunks.append(chunk)

        return chunks

    def _find_academic_sections(self, content: str) -> List[Tuple[str, str, str, int]]:
        """
        Find academic section boundaries and extract content.

        Args:
            content: Full paper content

        Returns:
            List of (title, content, section_type, start_position) tuples
        """
        sections = []
        lines = content.split('\n')

        # Find all section markers
        section_markers = []
        for i, line in enumerate(lines):
            for pattern, section_type in self.ACADEMIC_SECTION_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    title = line.strip()
                    section_markers.append((i, title, section_type))
                    break

        if not section_markers:
            return []

        # Remove duplicate markers (prefer earlier matches)
        unique_markers = []
        used_lines = set()
        for line_num, title, section_type in section_markers:
            if line_num not in used_lines:
                unique_markers.append((line_num, title, section_type))
                used_lines.add(line_num)

        # Sort by line number
        unique_markers.sort()

        # Extract content between markers
        for i, (line_num, title, section_type) in enumerate(unique_markers):
            start_line = line_num

            # Find end line (next section or end of document)
            if i + 1 < len(unique_markers):
                end_line = unique_markers[i + 1][0]
            else:
                end_line = len(lines)

            # Extract section content (excluding the header line)
            section_lines = lines[start_line + 1:end_line]
            section_content = '\n'.join(section_lines).strip()

            # Include header in content
            if section_content:
                full_content = title + '\n' + section_content
            else:
                full_content = title

            # Calculate start position in original text
            start_pos = sum(len(line) + 1 for line in lines[:start_line])

            # Only include sections with substantial content
            word_count = self._calculate_word_count(section_content)
            if word_count >= 10 or section_type in ['abstract', 'references']:
                sections.append((title, full_content, section_type, start_pos))

        return sections

    def get_strategy_name(self) -> str:
        """Get the name of this chunking strategy."""
        return "academic_section"