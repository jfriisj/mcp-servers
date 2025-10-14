"""
Factory for selecting appropriate academic chunking strategy.

Implements the Factory pattern to automatically select the best
chunking strategy for a given research paper based on content analysis.
"""

import re
from typing import List, Optional

from ..models import ResearchPaper
from .academic_section_strategy import AcademicSectionStrategy
from .base_academic_strategy import BaseAcademicStrategy
from .citation_aware_strategy import CitationAwareStrategy
from .topic_based_strategy import TopicBasedStrategy


class AcademicChunkingStrategyFactory:
    """
    Factory for selecting appropriate academic chunking strategy.

    Follows the Factory pattern and Open/Closed Principle:
    - New strategies can be registered without modifying existing code
    - Strategies are tried in priority order based on paper characteristics
    - Always falls back to AcademicSectionStrategy for structured papers

    Strategy priority (most specific first):
    1. CitationAwareStrategy - Papers with extensive citation networks
    2. AcademicSectionStrategy - Papers with clear academic structure
    3. TopicBasedStrategy - Papers with diverse thematic content
    4. AcademicSectionStrategy - Fallback for any academic content

    Each strategy is optimized for different systematic literature review needs:
    - Citation-aware: Citation network analysis, reference pattern detection
    - Academic section: Standard academic analysis, quality assessment
    - Topic-based: Thematic analysis, concept clustering
    """

    def __init__(self):
        """Initialize factory with default academic strategies."""
        self._strategies: List[BaseAcademicStrategy] = []
        self._fallback_strategy = AcademicSectionStrategy()

        # Register default strategies in priority order
        self.register_strategy(CitationAwareStrategy())
        self.register_strategy(AcademicSectionStrategy())
        self.register_strategy(TopicBasedStrategy())

    def register_strategy(self, strategy: BaseAcademicStrategy) -> None:
        """
        Register a new academic chunking strategy.

        Args:
            strategy: The strategy to register

        Note:
            Strategies are tried in registration order, so register
            more specific strategies first.
        """
        if strategy not in self._strategies:
            self._strategies.append(strategy)

    def get_strategy(
        self, paper: ResearchPaper, content: str
    ) -> BaseAcademicStrategy:
        """
        Get the best chunking strategy for a research paper.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            Most appropriate academic chunking strategy

        Note:
            Always returns a strategy - uses fallback if no others match.
        """
        # Try registered strategies in order
        for strategy in self._strategies:
            try:
                if strategy.can_chunk(paper, content):
                    return strategy
            except Exception:
                # Continue to next strategy if current one fails
                continue

        # Fallback strategy should always work for academic content
        return self._fallback_strategy

    def get_best_strategy_with_analysis(
        self, paper: ResearchPaper, content: str
    ) -> tuple[BaseAcademicStrategy, dict]:
        """
        Get the best strategy along with detailed analysis.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            Tuple of (selected_strategy, analysis_results)
        """
        selected_strategy = self.get_strategy(paper, content)
        analysis = self.analyze_paper(paper, content)
        
        return selected_strategy, analysis

    def get_available_strategies(self) -> List[str]:
        """
        Get names of all available strategies.

        Returns:
            List of strategy names
        """
        names = [strategy.get_strategy_name() for strategy in self._strategies]
        names.append(self._fallback_strategy.get_strategy_name())
        return list(set(names))  # Remove duplicates

    def get_strategy_by_name(
        self, name: str
    ) -> Optional[BaseAcademicStrategy]:
        """
        Get a specific strategy by name.

        Args:
            name: Name of the strategy

        Returns:
            Strategy instance or None if not found
        """
        # Check registered strategies
        for strategy in self._strategies:
            if strategy.get_strategy_name() == name:
                return strategy

        # Check fallback
        if self._fallback_strategy.get_strategy_name() == name:
            return self._fallback_strategy

        return None

    def analyze_paper(self, paper: ResearchPaper, content: str) -> dict:
        """
        Analyze which strategies can handle a research paper.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            Dictionary with analysis results
        """
        if not content:
            return {
                "error": "No content provided",
                "selected_strategy": self._fallback_strategy.get_strategy_name(),
                "compatible_strategies": [self._fallback_strategy.get_strategy_name()],
                "paper_stats": {"word_count": 0, "has_content": False}
            }

        selected_strategy = self.get_strategy(paper, content)
        
        # Basic paper statistics
        word_count = len(content.split()) if content else 0
        line_count = len(content.split('\n')) if content else 0
        
        results = {
            "selected_strategy": selected_strategy.get_strategy_name(),
            "compatible_strategies": [],
            "strategy_analysis": {},
            "paper_stats": {
                "word_count": word_count,
                "line_count": line_count,
                "file_type": paper.file_type,
                "has_content": bool(content and content.strip()),
                "estimated_pages": word_count // 250,  # Rough estimate
                "title": paper.title,
                "authors": paper.author_names,
                "publication_year": paper.publication_year
            },
            "academic_features": self._analyze_academic_features(content),
            "content_complexity": self._assess_content_complexity(content)
        }

        # Check compatibility with all strategies
        for strategy in self._strategies:
            strategy_name = strategy.get_strategy_name()
            try:
                can_handle = strategy.can_chunk(paper, content)
                
                if can_handle:
                    results["compatible_strategies"].append(strategy_name)
                
                # Store detailed analysis for each strategy
                results["strategy_analysis"][strategy_name] = {
                    "can_handle": can_handle,
                    "suitability_score": self._calculate_suitability_score(strategy, paper, content),
                    "reasons": self._get_strategy_selection_reasons(strategy, paper, content)
                }
                
            except Exception as e:
                results["strategy_analysis"][strategy_name] = {
                    "can_handle": False,
                    "error": str(e),
                    "suitability_score": 0.0,
                    "reasons": ["Strategy evaluation failed"]
                }

        # Fallback always compatible
        fallback_name = self._fallback_strategy.get_strategy_name()
        if fallback_name not in results["compatible_strategies"]:
            results["compatible_strategies"].append(fallback_name)

        # Add recommendation
        results["recommendation"] = self._generate_recommendation(results)

        return results

    def _analyze_academic_features(self, content: str) -> dict:
        """Analyze academic features of the content."""
        if not content:
            return {}

        content_lower = content.lower()
        
        # Count citations (basic patterns)
        citation_patterns = [
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2023)
            r'\[\d+\]',              # [1]
            r'\b[A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\)',  # Author et al. (2023)
        ]
        
        citation_count = 0
        for pattern in citation_patterns:
            import re
            matches = re.findall(pattern, content)
            citation_count += len(matches)

        # Detect academic sections
        academic_sections = []
        section_patterns = [
            ('abstract', r'\babstract\b'),
            ('introduction', r'\bintroduction\b'),
            ('methods', r'\b(method|methodology)\b'),
            ('results', r'\b(result|finding)\b'),
            ('discussion', r'\bdiscussion\b'),
            ('conclusion', r'\bconclusion\b'),
            ('references', r'\breference\b')
        ]
        
        for section_name, pattern in section_patterns:
            if re.search(pattern, content_lower):
                academic_sections.append(section_name)

        # Count figures and tables
        figure_count = len(re.findall(r'\bfigure\s+\d+\b', content_lower))
        table_count = len(re.findall(r'\btable\s+\d+\b', content_lower))

        # Research keywords
        research_keywords = [
            'study', 'research', 'analysis', 'investigation', 'experiment',
            'hypothesis', 'method', 'data', 'result', 'conclusion'
        ]
        
        keyword_count = sum(
            len(re.findall(rf'\b{keyword}\b', content_lower))
            for keyword in research_keywords
        )

        return {
            "citation_count": citation_count,
            "citations_per_1000_words": (citation_count / max(1, len(content.split()))) * 1000,
            "academic_sections": academic_sections,
            "section_count": len(academic_sections),
            "has_structured_sections": len(academic_sections) >= 4,
            "figure_count": figure_count,
            "table_count": table_count,
            "research_keyword_count": keyword_count,
            "keyword_density": keyword_count / max(1, len(content.split()))
        }

    def _assess_content_complexity(self, content: str) -> dict:
        """Assess the complexity and characteristics of content."""
        if not content:
            return {"complexity_score": 0.0}

        words = content.split()
        sentences = re.split(r'[.!?]+\s+', content)
        
        # Calculate complexity metrics
        avg_sentence_length = len(words) / max(1, len(sentences))
        
        # Count complex words (longer than 6 characters, rough heuristic)
        complex_words = [word for word in words if len(word) > 6]
        complex_word_ratio = len(complex_words) / max(1, len(words))
        
        # Topic diversity (rough estimate based on unique longer words)
        unique_complex_words = set(word.lower() for word in complex_words)
        topic_diversity = len(unique_complex_words) / max(1, len(complex_words))
        
        # Overall complexity score (0-1)
        complexity_score = (
            min(avg_sentence_length / 30, 1.0) * 0.4 +  # Sentence complexity
            min(complex_word_ratio * 2, 1.0) * 0.3 +      # Vocabulary complexity
            min(topic_diversity * 2, 1.0) * 0.3            # Topic diversity
        )

        return {
            "complexity_score": complexity_score,
            "avg_sentence_length": avg_sentence_length,
            "complex_word_ratio": complex_word_ratio,
            "topic_diversity": topic_diversity,
            "readability": "high" if complexity_score < 0.4 else "medium" if complexity_score < 0.7 else "low"
        }

    def _calculate_suitability_score(self, strategy: BaseAcademicStrategy, paper: ResearchPaper, content: str) -> float:
        """Calculate how suitable a strategy is for the given paper."""
        if not strategy.can_chunk(paper, content):
            return 0.0

        strategy_name = strategy.get_strategy_name()
        academic_features = self._analyze_academic_features(content)
        
        # Strategy-specific scoring
        if strategy_name == "citation_aware":
            # High score for papers with many citations
            citation_density = academic_features.get("citations_per_1000_words", 0)
            return min(1.0, citation_density / 50)  # Normalize around 50 citations per 1000 words
        
        elif strategy_name == "academic_section":
            # High score for well-structured academic papers
            structure_score = academic_features.get("section_count", 0) / 7  # Max 7 typical sections
            return min(1.0, structure_score)
        
        elif strategy_name == "topic_based":
            # High score for papers with diverse topics
            complexity = self._assess_content_complexity(content)
            return complexity.get("topic_diversity", 0.5)
        
        return 0.5  # Default moderate suitability

    def _get_strategy_selection_reasons(self, strategy: BaseAcademicStrategy, paper: ResearchPaper, content: str) -> List[str]:
        """Get reasons why a strategy was or wasn't selected."""
        reasons = []
        strategy_name = strategy.get_strategy_name()
        academic_features = self._analyze_academic_features(content)
        
        if strategy_name == "citation_aware":
            citation_count = academic_features.get("citation_count", 0)
            if citation_count >= 10:
                reasons.append(f"High citation density ({citation_count} citations found)")
            else:
                reasons.append(f"Low citation count ({citation_count} citations)")
        
        elif strategy_name == "academic_section":
            section_count = academic_features.get("section_count", 0)
            if section_count >= 4:
                reasons.append(f"Well-structured academic format ({section_count} sections detected)")
            else:
                reasons.append(f"Limited academic structure ({section_count} sections)")
        
        elif strategy_name == "topic_based":
            keyword_count = academic_features.get("research_keyword_count", 0)
            if keyword_count >= 20:
                reasons.append(f"Rich topical content ({keyword_count} research keywords)")
            else:
                reasons.append(f"Limited topical diversity ({keyword_count} research keywords)")
        
        return reasons

    def _generate_recommendation(self, analysis: dict) -> dict:
        """Generate recommendations based on analysis."""
        selected = analysis.get("selected_strategy", "unknown")
        compatible = analysis.get("compatible_strategies", [])
        academic_features = analysis.get("academic_features", {})
        
        recommendation = {
            "primary_strategy": selected,
            "confidence": "high" if len(compatible) >= 2 else "medium" if len(compatible) == 1 else "low",
            "alternative_strategies": [s for s in compatible if s != selected][:2],
            "optimization_suggestions": []
        }
        
        # Add optimization suggestions
        if academic_features.get("citation_count", 0) > 20:
            recommendation["optimization_suggestions"].append("Consider citation network analysis")
        
        if academic_features.get("section_count", 0) >= 5:
            recommendation["optimization_suggestions"].append("Leverage structured academic format")
        
        if academic_features.get("keyword_density", 0) > 0.05:
            recommendation["optimization_suggestions"].append("Perform thematic content analysis")
        
        return recommendation

    def create_chunking_plan(self, paper: ResearchPaper, content: str) -> dict:
        """
        Create a comprehensive chunking plan for the research paper.

        Args:
            paper: Research paper metadata
            content: Paper text content

        Returns:
            Detailed chunking plan with strategy selection and parameters
        """
        strategy, analysis = self.get_best_strategy_with_analysis(paper, content)
        
        return {
            "paper_info": {
                "title": paper.title,
                "authors": paper.author_names,
                "file_type": paper.file_type,
                "word_count": analysis["paper_stats"]["word_count"]
            },
            "selected_strategy": {
                "name": strategy.get_strategy_name(),
                "confidence": analysis["recommendation"]["confidence"],
                "suitability_score": analysis["strategy_analysis"].get(
                    strategy.get_strategy_name(), {}
                ).get("suitability_score", 0.5)
            },
            "analysis": analysis,
            "expected_outcomes": {
                "estimated_chunks": self._estimate_chunk_count(content, strategy),
                "chunk_characteristics": self._describe_expected_chunks(strategy),
                "processing_time": "fast" if len(content.split()) < 5000 else "medium" if len(content.split()) < 15000 else "slow"
            },
            "alternatives": analysis["recommendation"]["alternative_strategies"]
        }

    def _estimate_chunk_count(self, content: str, strategy: BaseAcademicStrategy) -> int:
        """Estimate number of chunks that will be produced."""
        if not content:
            return 0
        
        word_count = len(content.split())
        strategy_name = strategy.get_strategy_name()
        
        if strategy_name == "citation_aware":
            # Estimate based on citation density
            citation_count = len(re.findall(r'\([^)]*\d{4}[^)]*\)', content))
            return max(3, min(citation_count // 3, word_count // 300))
        
        elif strategy_name == "academic_section":
            # Estimate based on typical academic sections
            return min(8, max(4, word_count // 800))
        
        elif strategy_name == "topic_based":
            # Estimate based on content diversity
            return max(4, min(12, word_count // 400))
        
        return max(3, word_count // 500)  # Default estimate

    def _describe_expected_chunks(self, strategy: BaseAcademicStrategy) -> List[str]:
        """Describe the characteristics of expected chunks."""
        strategy_name = strategy.get_strategy_name()
        
        descriptions = {
            "citation_aware": [
                "Citation-rich content sections",
                "Preserved reference contexts",
                "Grouped related citations",
                "Optimal for citation network analysis"
            ],
            "academic_section": [
                "Standard academic sections (Abstract, Methods, etc.)",
                "Logical paper structure preserved",
                "Section-specific content analysis",
                "Ideal for quality assessment"
            ],
            "topic_based": [
                "Thematically coherent content groups",
                "Semantic topic boundaries",
                "Concept clustering optimization",
                "Perfect for thematic analysis"
            ]
        }
        
        return descriptions.get(strategy_name, ["Content-based chunks", "Balanced size distribution"])


# Utility function for easy access
def create_chunking_strategy_factory() -> AcademicChunkingStrategyFactory:
    """Create a configured academic chunking strategy factory."""
    return AcademicChunkingStrategyFactory()