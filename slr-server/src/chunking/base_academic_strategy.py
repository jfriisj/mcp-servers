"""
Abstract base class for academic document chunking strategies.

Defines the interface that all academic chunking strategies must implement.
Extends the basic chunking concept with academic-specific features.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple

from ..models import AcademicChunk, ResearchPaper


class BaseAcademicStrategy(ABC):
    """
    Abstract base class for academic document chunking strategies.

    This class extends basic chunking with academic research-specific features:
    - Academic section detection and classification
    - Citation counting and analysis
    - Figure and table reference extraction
    - Research element identification
    - Semantic tagging for research concepts

    Follows Strategy pattern for extensible academic document segmentation.
    """

    @abstractmethod
    def can_chunk(self, paper: ResearchPaper, content: str) -> bool:
        """
        Check if this strategy can handle the given research paper.

        Args:
            paper: The research paper metadata
            content: The paper's text content

        Returns:
            True if this strategy can chunk the paper, False otherwise
        """
        pass

    @abstractmethod
    def chunk(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """
        Create academic chunks from the research paper.

        Args:
            paper: The research paper metadata
            content: The paper's text content

        Returns:
            List of academic chunks created from the paper

        Raises:
            ValueError: If the paper cannot be chunked by this strategy
        """
        pass

    def get_strategy_name(self) -> str:
        """Get the name of this academic chunking strategy."""
        return self.__class__.__name__.replace("Strategy", "").lower()

    # Academic-specific utility methods

    def _detect_section_type(self, title: str, content: str, position_ratio: float) -> str:
        """
        Detect the type of academic section based on title and content.

        Args:
            title: Section title or heading
            content: Section content
            position_ratio: Position in document (0.0 = start, 1.0 = end)

        Returns:
            Detected section type (abstract, introduction, methods, etc.)
        """
        if not title:
            title = ""
        
        title_lower = title.lower().strip()
        content_lower = content.lower() if content else ""

        # Abstract detection
        if re.search(r'\babstract\b', title_lower) or position_ratio < 0.1:
            if any(keyword in content_lower for keyword in ['purpose', 'objective', 'method', 'result', 'conclusion']):
                return "abstract"

        # Introduction detection
        if re.search(r'\b(introduction|background|overview)\b', title_lower) or position_ratio < 0.3:
            if any(keyword in content_lower for keyword in ['background', 'motivation', 'previous', 'literature']):
                return "introduction"

        # Methods/Methodology detection
        if re.search(r'\b(method|methodology|approach|procedure|design)\b', title_lower):
            return "methods"
        if any(keyword in content_lower for keyword in ['participants', 'sample', 'procedure', 'analysis', 'statistical']):
            return "methods"

        # Results detection
        if re.search(r'\b(result|finding|outcome|analysis)\b', title_lower):
            return "results"
        if any(keyword in content_lower for keyword in ['figure', 'table', 'significant', 'correlation']):
            return "results"

        # Discussion detection
        if re.search(r'\b(discussion|interpretation|implication)\b', title_lower):
            return "discussion"
        if any(keyword in content_lower for keyword in ['interpret', 'suggest', 'implication', 'limitation']):
            return "discussion"

        # Conclusion detection
        if re.search(r'\b(conclusion|summary|final)\b', title_lower) or position_ratio > 0.8:
            if any(keyword in content_lower for keyword in ['conclude', 'summary', 'future work', 'recommendation']):
                return "conclusion"

        # References detection
        if re.search(r'\b(reference|bibliography|citation)\b', title_lower) or position_ratio > 0.9:
            return "references"

        # Default to body section
        return "body"

    def _count_citations(self, content: str) -> int:
        """
        Count the number of citations in the content.

        Args:
            content: Text content to analyze

        Returns:
            Number of citations found
        """
        if not content:
            return 0

        # Citation patterns (various formats)
        citation_patterns = [
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2023) or (Author et al., 2023)
            r'\[\d+\]',              # [1] or [1,2,3]
            r'\[\d+[-–]\d+\]',       # [1-5] or [1–5]
            r'\b[A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\)',  # Author et al. (2023)
            r'\b[A-Z][a-z]+\s+\(\d{4}\)',  # Author (2023)
        ]

        citation_count = 0
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            citation_count += len(matches)

        return citation_count

    def _count_figures_tables(self, content: str) -> Tuple[int, int]:
        """
        Count figure and table references in the content.

        Args:
            content: Text content to analyze

        Returns:
            Tuple of (figure_count, table_count)
        """
        if not content:
            return 0, 0

        # Figure patterns
        figure_patterns = [
            r'\bfigure\s+\d+\b',
            r'\bfig\.\s+\d+\b',
            r'\bfig\s+\d+\b',
        ]

        # Table patterns
        table_patterns = [
            r'\btable\s+\d+\b',
            r'\btab\.\s+\d+\b',
        ]

        figure_count = 0
        for pattern in figure_patterns:
            matches = re.findall(pattern, content.lower())
            figure_count += len(matches)

        table_count = 0
        for pattern in table_patterns:
            matches = re.findall(pattern, content.lower())
            table_count += len(matches)

        return figure_count, table_count

    def _extract_research_elements(self, content: str, section_type: str) -> List[str]:
        """
        Extract research elements based on section type and content.

        Args:
            content: Text content to analyze
            section_type: Type of academic section

        Returns:
            List of research elements found
        """
        if not content:
            return []

        elements = []
        content_lower = content.lower()

        # Hypothesis detection
        if any(keyword in content_lower for keyword in ['hypothesis', 'hypothesize', 'predict', 'expect']):
            elements.append('hypothesis')

        # Methodology elements
        if section_type == "methods":
            if any(keyword in content_lower for keyword in ['survey', 'questionnaire', 'interview']):
                elements.append('survey_method')
            if any(keyword in content_lower for keyword in ['experiment', 'trial', 'treatment']):
                elements.append('experimental_method')
            if any(keyword in content_lower for keyword in ['statistical', 'regression', 'anova']):
                elements.append('statistical_analysis')

        # Results elements
        if section_type == "results":
            if any(keyword in content_lower for keyword in ['significant', 'p <', 'p=', 'p-value']):
                elements.append('statistical_results')
            if any(keyword in content_lower for keyword in ['correlation', 'association', 'relationship']):
                elements.append('correlation_analysis')

        # Discussion elements
        if section_type == "discussion":
            if any(keyword in content_lower for keyword in ['limitation', 'limit', 'constraint']):
                elements.append('limitations')
            if any(keyword in content_lower for keyword in ['future', 'recommend', 'suggestion']):
                elements.append('future_work')

        return elements

    def _generate_semantic_tags(self, content: str, section_type: str) -> List[str]:
        """
        Generate semantic tags for content based on academic concepts.

        Args:
            content: Text content to analyze
            section_type: Type of academic section

        Returns:
            List of semantic tags
        """
        if not content:
            return []

        tags = []
        content_lower = content.lower()

        # Research methodology tags
        if any(keyword in content_lower for keyword in ['qualitative', 'ethnographic', 'phenomenological']):
            tags.append('qualitative_research')
        if any(keyword in content_lower for keyword in ['quantitative', 'statistical', 'numerical']):
            tags.append('quantitative_research')
        if any(keyword in content_lower for keyword in ['mixed method', 'mixed-method', 'triangulation']):
            tags.append('mixed_methods')

        # Study design tags
        if any(keyword in content_lower for keyword in ['randomized', 'rct', 'controlled trial']):
            tags.append('randomized_trial')
        if any(keyword in content_lower for keyword in ['longitudinal', 'follow-up', 'over time']):
            tags.append('longitudinal_study')
        if any(keyword in content_lower for keyword in ['cross-sectional', 'cross sectional', 'snapshot']):
            tags.append('cross_sectional')

        # Domain-specific tags
        if any(keyword in content_lower for keyword in ['machine learning', 'artificial intelligence', 'neural network']):
            tags.append('ai_ml')
        if any(keyword in content_lower for keyword in ['clinical', 'patient', 'medical', 'healthcare']):
            tags.append('clinical_research')
        if any(keyword in content_lower for keyword in ['software', 'programming', 'algorithm', 'system']):
            tags.append('computer_science')

        return list(set(tags))  # Remove duplicates

    def _calculate_confidence_score(self, chunk: AcademicChunk) -> float:
        """
        Calculate confidence score for the chunk's section classification.

        Args:
            chunk: Academic chunk to evaluate

        Returns:
            Confidence score between 0 and 1
        """
        score = 0.5  # Base confidence

        # Increase confidence based on various factors
        if chunk.title and chunk.title.strip():
            score += 0.2

        if chunk.section_type in ['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']:
            score += 0.2

        if hasattr(chunk, 'citation_count') and chunk.citation_count and chunk.citation_count > 0:
            score += 0.1

        if hasattr(chunk, 'research_elements') and chunk.research_elements:
            score += 0.1 * min(len(chunk.research_elements), 3) / 3

        if hasattr(chunk, 'semantic_tags') and chunk.semantic_tags:
            score += 0.1 * min(len(chunk.semantic_tags), 2) / 2

        return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1

    def _calculate_word_count(self, text: str) -> int:
        """Calculate word count for a text chunk."""
        if not text or not text.strip():
            return 0
        return len(text.strip().split())

    def _clean_title(self, title: str) -> str:
        """Clean and format a chunk title."""
        if not title:
            return "Untitled"

        # Remove extra whitespace and newlines
        title = " ".join(title.strip().split())

        # Remove common section numbering
        title = re.sub(r'^\d+\.?\s*', '', title)
        title = re.sub(r'^[IVX]+\.?\s*', '', title, flags=re.IGNORECASE)

        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."

        return title.strip() or "Untitled"