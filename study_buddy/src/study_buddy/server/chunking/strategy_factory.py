"""Factory for selecting appropriate chunking strategy.

Implements the Factory pattern to automatically select the best
chunking strategy for a given document based on content analysis.
"""

from typing import List, Optional

from ..models.document import Document

from .base_strategy import BaseChunkingStrategy
from .chapter_strategy import ChapterStrategy
from .fixed_length_strategy import FixedLengthStrategy
from .heading_strategy import HeadingStrategy
from .section_strategy import SectionStrategy
from .slide_strategy import SlideStrategy


class ChunkingStrategyFactory:
    """Factory for selecting appropriate chunking strategy.

    Follows the Factory pattern and Open/Closed Principle:
    - New strategies can be registered without modifying existing code
    - Strategies are tried in priority order
    - Always falls back to FixedLengthStrategy

    Strategy priority (most specific first):
    1. SlideStrategy - Presentations and slide-based content
    2. ChapterStrategy - Books with clear chapter markers
    3. SectionStrategy - Academic papers with standard sections
    4. HeadingStrategy - Structured documents with headings
    5. FixedLengthStrategy - Fallback for any content
    """

    def __init__(self):
        """Initialize factory with default strategies."""
        self._strategies: List[BaseChunkingStrategy] = []
        self._fallback_strategy = FixedLengthStrategy()

        # Register default strategies in priority order
        self.register_strategy(SlideStrategy())
        self.register_strategy(ChapterStrategy())
        self.register_strategy(SectionStrategy())
        self.register_strategy(HeadingStrategy())

    def register_strategy(self, strategy: BaseChunkingStrategy) -> None:
        """Register a new chunking strategy.

        Args:
            strategy: The strategy to register

        Note:
            Strategies are tried in registration order, so register
            more specific strategies first.
        """
        if strategy not in self._strategies:
            self._strategies.append(strategy)

    def get_strategy(
        self, document: Document, content: str
    ) -> BaseChunkingStrategy:
        """Get the best chunking strategy for a document.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            Most appropriate chunking strategy

        Note:
            Always returns a strategy - uses fallback if no others match.
        """
        # Try registered strategies in order
        for strategy in self._strategies:
            if strategy.can_chunk(document, content):
                return strategy

        # Fallback strategy always works
        return self._fallback_strategy

    def get_available_strategies(self) -> List[str]:
        """Get names of all available strategies.

        Returns:
            List of strategy names
        """
        names = [strategy.get_strategy_name() for strategy in self._strategies]
        names.append(self._fallback_strategy.get_strategy_name())
        return names

    def get_strategy_by_name(
        self, name: str
    ) -> Optional[BaseChunkingStrategy]:
        """Get a specific strategy by name.

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

    def analyze_document(self, document: Document, content: str) -> dict:
        """Analyze which strategies can handle a document.

        Args:
            document: Document metadata
            content: Document text content

        Returns:
            Dictionary with analysis results
        """
        selected_strategy = self.get_strategy(document, content)
        results = {
            "selected_strategy": selected_strategy.get_strategy_name(),
            "compatible_strategies": [],
            "document_stats": {
                "word_count": len(content.split()) if content else 0,
                "line_count": len(content.split('\n')) if content else 0,
                "file_type": document.file_type
            }
        }

        # Check all strategies
        for strategy in self._strategies:
            if strategy.can_chunk(document, content):
                results["compatible_strategies"].append(
                    strategy.get_strategy_name()
                )

        # Fallback always compatible
        results["compatible_strategies"].append(
            self._fallback_strategy.get_strategy_name()
        )

        return results
