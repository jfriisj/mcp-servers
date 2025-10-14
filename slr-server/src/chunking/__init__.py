"""
Academic chunking strategies for systematic literature review processing.

This package provides specialized chunking strategies for academic research papers,
optimizing content segmentation for AI processing while preserving academic structure.
"""

from .academic_section_strategy import AcademicSectionStrategy
from .citation_aware_strategy import CitationAwareStrategy
from .topic_based_strategy import TopicBasedStrategy
from .strategy_factory import AcademicChunkingStrategyFactory

__all__ = [
    "AcademicSectionStrategy",
    "CitationAwareStrategy", 
    "TopicBasedStrategy",
    "AcademicChunkingStrategyFactory"
]