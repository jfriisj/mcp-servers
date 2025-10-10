"""
Search Result Highlighting Component for Study Buddy GUI Application.

Implements advanced syntax highlighting for search results with configurable
colors, pattern matching, and context-aware highlighting strategies.

Part of Task 14, Phase 1: Advanced Search Enhancement
Architecture: Clean Architecture Layer 1 (External Interface)
SOLID Compliance: Single Responsibility, Open/Closed via Strategy Pattern
"""

import tkinter as tk
from tkinter import ttk
import re
from typing import Dict, List, Tuple, Optional, Any, Pattern
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HighlightType(Enum):
    """Enumeration of different highlight types for search results."""
    SEARCH_TERM = "search_term"
    KEYWORD = "keyword" 
    FILENAME = "filename"
    DATE = "date"
    NUMBER = "number"
    QUOTE = "quote"
    CODE = "code"
    HEADING = "heading"
    LINK = "link"
    EMPHASIS = "emphasis"


@dataclass
class HighlightStyle:
    """Configuration for highlight appearance and behavior."""
    foreground: str
    background: str
    font_style: str = "normal"  # normal, bold, italic
    underline: bool = False
    relief: str = "flat"  # flat, raised, sunken
    borderwidth: int = 0


@dataclass
class HighlightPattern:
    """Pattern definition for content matching and highlighting."""
    pattern: Pattern[str]
    highlight_type: HighlightType
    priority: int = 0  # Higher priority patterns applied last
    case_sensitive: bool = False
    whole_word_only: bool = False


class HighlightStrategy(ABC):
    """Abstract strategy for different highlighting approaches."""
    
    @abstractmethod
    def get_patterns(self, search_query: str) -> List[HighlightPattern]:
        """Generate highlight patterns based on search query and content type."""
        pass
    
    @abstractmethod
    def should_apply(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Determine if this strategy should be applied to the content."""
        pass


class TextHighlightStrategy(HighlightStrategy):
    """Highlighting strategy for plain text content."""
    
    def get_patterns(self, search_query: str) -> List[HighlightPattern]:
        """Generate patterns for plain text highlighting."""
        patterns = []
        
        if not search_query.strip():
            return patterns
        
        # Search term highlighting (highest priority)
        query_words = search_query.strip().split()
        for word in query_words:
            if len(word) >= 2:  # Only highlight meaningful words
                escaped_word = re.escape(word)
                pattern = re.compile(f"\\b{escaped_word}\\b", re.IGNORECASE)
                patterns.append(HighlightPattern(
                    pattern=pattern,
                    highlight_type=HighlightType.SEARCH_TERM,
                    priority=100,
                    case_sensitive=False,
                    whole_word_only=True
                ))
        
        # Common keywords and phrases
        keyword_patterns = [
            (r"\b(chapter|section|part|appendix)\s+\d+\b", HighlightType.HEADING),
            (r"\b(figure|table|diagram)\s+\d+", HighlightType.KEYWORD),
            (r"\b(note|important|warning|tip)\b", HighlightType.EMPHASIS),
            (r"\b\d{4}-\d{2}-\d{2}\b", HighlightType.DATE),  # Date format
            (r"\b\d+(\.\d+)?%?\b", HighlightType.NUMBER),     # Numbers/percentages
        ]
        
        for pattern_str, highlight_type in keyword_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            patterns.append(HighlightPattern(
                pattern=pattern,
                highlight_type=highlight_type,
                priority=50
            ))
        
        return patterns
    
    def should_apply(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Apply to all text content."""
        return True


class MarkdownHighlightStrategy(HighlightStrategy):
    """Highlighting strategy for Markdown content."""
    
    def get_patterns(self, search_query: str) -> List[HighlightPattern]:
        """Generate patterns for Markdown content highlighting."""
        patterns = []
        
        # Include base text patterns
        text_strategy = TextHighlightStrategy()
        patterns.extend(text_strategy.get_patterns(search_query))
        
        # Markdown-specific patterns
        markdown_patterns = [
            (r"^#{1,6}\s+.+$", HighlightType.HEADING),        # Headers
            (r"`[^`]+`", HighlightType.CODE),                  # Inline code
            (r"```[\s\S]*?```", HighlightType.CODE),           # Code blocks
            (r"\*\*[^*]+\*\*", HighlightType.EMPHASIS),       # Bold
            (r"\*[^*]+\*", HighlightType.EMPHASIS),           # Italic
            (r"\[([^\]]+)\]\([^)]+\)", HighlightType.LINK),   # Links
            (r">\s+.+", HighlightType.QUOTE),                 # Blockquotes
        ]
        
        for pattern_str, highlight_type in markdown_patterns:
            pattern = re.compile(pattern_str, re.MULTILINE)
            patterns.append(HighlightPattern(
                pattern=pattern,
                highlight_type=highlight_type,
                priority=25
            ))
        
        return patterns
    
    def should_apply(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Apply to Markdown content."""
        file_type = metadata.get("file_type", "").lower()
        return file_type in ["md", "markdown"] or "markdown" in content[:200].lower()


class CodeHighlightStrategy(HighlightStrategy):
    """Highlighting strategy for source code content."""
    
    def get_patterns(self, search_query: str) -> List[HighlightPattern]:
        """Generate patterns for source code highlighting."""
        patterns = []
        
        # Include base text patterns
        text_strategy = TextHighlightStrategy()
        patterns.extend(text_strategy.get_patterns(search_query))
        
        # Programming language keywords (simplified)
        keyword_patterns = [
            (r"\b(class|function|def|var|let|const|import|export)\b", HighlightType.KEYWORD),
            (r"\b(if|else|for|while|return|try|catch|finally)\b", HighlightType.KEYWORD),
            (r"//.*$", HighlightType.QUOTE),                    # Comments
            (r"/\*[\s\S]*?\*/", HighlightType.QUOTE),          # Block comments
            (r'"[^"]*"', HighlightType.QUOTE),                 # String literals
            (r"'[^']*'", HighlightType.QUOTE),                 # String literals
        ]
        
        for pattern_str, highlight_type in keyword_patterns:
            pattern = re.compile(pattern_str, re.MULTILINE)
            patterns.append(HighlightPattern(
                pattern=pattern,
                highlight_type=highlight_type,
                priority=30
            ))
        
        return patterns
    
    def should_apply(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Apply to source code files."""
        file_type = metadata.get("file_type", "").lower()
        code_extensions = ["py", "js", "ts", "java", "cpp", "c", "cs", "php", "rb", "go"]
        return file_type in code_extensions or any(ext in content[:100].lower() for ext in ["def ", "class ", "function ", "import "])


class SearchHighlighter:
    """
    Advanced search result highlighter with syntax-aware highlighting.
    
    Responsibilities:
    - Apply intelligent highlighting to search results
    - Support multiple content types (text, markdown, code)
    - Provide configurable highlight styles and themes
    - Manage highlight patterns and strategies
    
    Architecture:
    - Uses Strategy pattern for different content types
    - Configurable through theme system integration
    - Follows Single Responsibility and Open/Closed principles
    """
    
    def __init__(self, theme_config: Optional[Dict[str, Any]] = None):
        """
        Initialize highlighter with theme configuration.
        
        Args:
            theme_config: Theme configuration for highlight styles
        """
        self.theme_config = theme_config or {}
        self.strategies: List[HighlightStrategy] = [
            CodeHighlightStrategy(),
            MarkdownHighlightStrategy(), 
            TextHighlightStrategy()  # Fallback strategy
        ]
        
        # Default highlight styles
        self.highlight_styles = self._create_default_styles()
        self._apply_theme_config()
        
        logger.debug("SearchHighlighter initialized with %d strategies", len(self.strategies))
    
    def _create_default_styles(self) -> Dict[HighlightType, HighlightStyle]:
        """Create default highlight styles for different content types."""
        return {
            HighlightType.SEARCH_TERM: HighlightStyle(
                foreground="black",
                background="yellow", 
                font_style="bold"
            ),
            HighlightType.KEYWORD: HighlightStyle(
                foreground="blue",
                background="lightblue",
                font_style="bold"
            ),
            HighlightType.FILENAME: HighlightStyle(
                foreground="darkgreen",
                background="lightgreen"
            ),
            HighlightType.DATE: HighlightStyle(
                foreground="purple",
                background="lavender"
            ),
            HighlightType.NUMBER: HighlightStyle(
                foreground="red",
                background="mistyrose"
            ),
            HighlightType.QUOTE: HighlightStyle(
                foreground="gray",
                background="lightgray",
                font_style="italic"
            ),
            HighlightType.CODE: HighlightStyle(
                foreground="darkblue",
                background="aliceblue",
                font_style="normal"
            ),
            HighlightType.HEADING: HighlightStyle(
                foreground="darkred",
                background="pink",
                font_style="bold"
            ),
            HighlightType.LINK: HighlightStyle(
                foreground="blue",
                background="white",
                underline=True
            ),
            HighlightType.EMPHASIS: HighlightStyle(
                foreground="darkorange", 
                background="peachpuff",
                font_style="italic"
            )
        }
    
    def _apply_theme_config(self) -> None:
        """Apply theme configuration to highlight styles."""
        theme_highlights = self.theme_config.get("search_highlights", {})
        
        for highlight_type_str, style_config in theme_highlights.items():
            try:
                highlight_type = HighlightType(highlight_type_str)
                if highlight_type in self.highlight_styles:
                    style = self.highlight_styles[highlight_type]
                    
                    # Update style properties from theme config
                    if "foreground" in style_config:
                        style.foreground = style_config["foreground"]
                    if "background" in style_config:
                        style.background = style_config["background"]
                    if "font_style" in style_config:
                        style.font_style = style_config["font_style"]
                    if "underline" in style_config:
                        style.underline = style_config["underline"]
                        
            except ValueError:
                logger.warning("Unknown highlight type in theme config: %s", highlight_type_str)
    
    def highlight_text_widget(
        self, 
        text_widget: tk.Text, 
        search_query: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Apply highlighting to text widget content.
        
        Args:
            text_widget: Tkinter Text widget to highlight
            search_query: Current search query
            content: Text content to analyze  
            metadata: Optional metadata about the content
        """
        if not search_query.strip():
            return
        
        metadata = metadata or {}
        
        # Select appropriate strategy
        strategy = self._select_strategy(content, metadata)
        if not strategy:
            logger.warning("No highlighting strategy available for content")
            return
        
        # Get highlight patterns
        patterns = strategy.get_patterns(search_query)
        if not patterns:
            return
        
        # Configure text widget tags for highlighting
        self._configure_text_tags(text_widget)
        
        # Apply highlighting patterns
        self._apply_highlighting_patterns(text_widget, content, patterns)
        
        logger.debug("Applied %d highlight patterns to text widget", len(patterns))
    
    def _select_strategy(self, content: str, metadata: Dict[str, Any]) -> Optional[HighlightStrategy]:
        """Select the most appropriate highlighting strategy."""
        for strategy in self.strategies:
            if strategy.should_apply(content, metadata):
                return strategy
        return None
    
    def _configure_text_tags(self, text_widget: tk.Text) -> None:
        """Configure text widget tags for each highlight type."""
        for highlight_type, style in self.highlight_styles.items():
            tag_name = f"highlight_{highlight_type.value}"
            
            # Configure tag with style properties
            tag_config = {
                "foreground": style.foreground,
                "background": style.background,
                "underline": style.underline,
                "relief": style.relief,
                "borderwidth": style.borderwidth
            }
            
            # Handle font style
            if style.font_style != "normal":
                current_font = text_widget.cget("font")
                if isinstance(current_font, str):
                    # Parse font string and add style
                    font_parts = current_font.split()
                    if len(font_parts) >= 2:
                        font_family = font_parts[0]
                        font_size = font_parts[1]
                        if style.font_style == "bold":
                            tag_config["font"] = (font_family, font_size, "bold")
                        elif style.font_style == "italic":
                            tag_config["font"] = (font_family, font_size, "italic")
            
            text_widget.tag_configure(tag_name, **tag_config)
    
    def _apply_highlighting_patterns(
        self, 
        text_widget: tk.Text, 
        content: str, 
        patterns: List[HighlightPattern]
    ) -> None:
        """Apply highlighting patterns to text widget content."""
        # Sort patterns by priority (lower priority first)
        sorted_patterns = sorted(patterns, key=lambda p: p.priority)
        
        for pattern_info in sorted_patterns:
            tag_name = f"highlight_{pattern_info.highlight_type.value}"
            
            # Find all matches for this pattern
            for match in pattern_info.pattern.finditer(content):
                start_pos = match.start()
                end_pos = match.end()
                
                # Convert to tkinter text indices
                start_line = content[:start_pos].count('\n') + 1
                start_col = start_pos - content.rfind('\n', 0, start_pos) - 1
                end_line = content[:end_pos].count('\n') + 1
                end_col = end_pos - content.rfind('\n', 0, end_pos) - 1
                
                start_index = f"{start_line}.{start_col}"
                end_index = f"{end_line}.{end_col}"
                
                # Apply highlight tag
                text_widget.tag_add(tag_name, start_index, end_index)
    
    def get_highlight_summary(self, content: str, search_query: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Get summary of highlights that would be applied to content.
        
        Args:
            content: Text content to analyze
            search_query: Current search query 
            metadata: Optional content metadata
            
        Returns:
            Dictionary with highlight type counts
        """
        metadata = metadata or {}
        summary = {}
        
        strategy = self._select_strategy(content, metadata)
        if not strategy:
            return summary
        
        patterns = strategy.get_patterns(search_query)
        
        for pattern_info in patterns:
            highlight_type = pattern_info.highlight_type.value
            match_count = len(pattern_info.pattern.findall(content))
            
            if match_count > 0:
                summary[highlight_type] = summary.get(highlight_type, 0) + match_count
        
        return summary
    
    def update_theme(self, theme_config: Dict[str, Any]) -> None:
        """
        Update highlight styles with new theme configuration.
        
        Args:
            theme_config: New theme configuration
        """
        self.theme_config = theme_config
        self._apply_theme_config()
        logger.info("Updated highlighter theme configuration")
    
    def add_custom_strategy(self, strategy: HighlightStrategy) -> None:
        """
        Add custom highlighting strategy.
        
        Args:
            strategy: Custom highlighting strategy
        """
        self.strategies.insert(0, strategy)  # Add at beginning for priority
        logger.info("Added custom highlighting strategy: %s", type(strategy).__name__)
    
    def clear_highlights(self, text_widget: tk.Text) -> None:
        """
        Clear all highlights from text widget.
        
        Args:
            text_widget: Text widget to clear
        """
        for highlight_type in HighlightType:
            tag_name = f"highlight_{highlight_type.value}"
            text_widget.tag_delete(tag_name)