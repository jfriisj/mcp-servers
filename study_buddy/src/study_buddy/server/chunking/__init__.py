"""Chunking strategies for document segmentation.

This package implements the Strategy pattern for different document chunking approaches.
Follows SOLID principles:
- SRP: Each strategy handles one chunking method
- OCP: New strategies can be added without modifying existing code
- LSP: All strategies are substitutable
- ISP: Focused chunking interface
- DIP: Depend on abstractions, not implementations
"""

from .base_strategy import BaseChunkingStrategy
from .chapter_strategy import ChapterStrategy
from .fixed_length_strategy import FixedLengthStrategy
from .heading_strategy import HeadingStrategy
from .section_strategy import SectionStrategy
from .slide_strategy import SlideStrategy
from .strategy_factory import ChunkingStrategyFactory

__all__ = [
    "BaseChunkingStrategy",
    "ChapterStrategy",
    "SectionStrategy",
    "HeadingStrategy",
    "FixedLengthStrategy", 
    "SlideStrategy",
    "ChunkingStrategyFactory",
]
