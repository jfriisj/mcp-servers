"""
Advanced Search Components for Study Buddy GUI Application.

This package implements Task 14, Phase 1: Advanced Search Enhancement
with syntax highlighting, intelligent suggestions, and enhanced result display.

Components:
- SearchHighlighter: Syntax highlighting for search results
- SearchSuggestionEngine: Intelligent search suggestions and autocomplete  
- SearchHistoryManager: Search history persistence and management
- SearchResultRenderer: Enhanced result display with context highlighting
"""

from .search_highlighter import SearchHighlighter
from .search_suggestions import SearchSuggestionEngine  
from .search_history import SearchHistoryManager
from .search_results import SearchResultRenderer

__all__ = [
    "SearchHighlighter",
    "SearchSuggestionEngine", 
    "SearchHistoryManager",
    "SearchResultRenderer"
]