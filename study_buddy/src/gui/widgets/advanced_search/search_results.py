"""
Enhanced Search Result Rendering for Study Buddy GUI Application.

Provides advanced search result display with context highlighting,
snippet extraction, and rich formatting for improved user experience.

Part of Task 14, Phase 1: Advanced Search Enhancement
Architecture: Clean Architecture Layer 1 (External Interface)
SOLID Compliance: Single Responsibility, Strategy Pattern for rendering types
"""

import tkinter as tk
from tkinter import ttk, font
import re
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result with metadata."""
    id: str
    title: str
    content: str
    result_type: str  # "document", "chunk", "bookmark", etc.
    relevance_score: float
    metadata: Dict[str, Any]
    highlight_positions: Optional[List[Tuple[int, int]]] = None  # Start, end positions of matches
    snippet: str = ""  # Extracted context snippet
    
    def __post_init__(self):
        if self.highlight_positions is None:
            self.highlight_positions = []


@dataclass
class RenderContext:
    """Context information for result rendering."""
    query: str
    max_snippet_length: int = 300
    highlight_color: str = "yellow"
    font_family: str = "Arial"
    font_size: int = 10
    show_metadata: bool = True
    show_relevance: bool = False
    compact_mode: bool = False


class ResultRenderer(ABC):
    """Abstract renderer for different result types."""
    
    @abstractmethod
    def can_render(self, result: SearchResult) -> bool:
        """Check if this renderer can handle the result type."""
        pass
    
    @abstractmethod
    def render(
        self, 
        result: SearchResult, 
        parent: tk.Widget, 
        context: RenderContext
    ) -> tk.Widget:
        """Render the search result as a widget."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get renderer priority (higher = more specific)."""
        pass


class DocumentResultRenderer(ResultRenderer):
    """Renderer for document search results."""
    
    def can_render(self, result: SearchResult) -> bool:
        return result.result_type == "document"
    
    def render(self, result: SearchResult, parent: tk.Widget, context: RenderContext) -> tk.Widget:
        """Render document search result."""
        # Create main container
        container = ttk.Frame(parent, padding=(10, 5))
        container.grid_columnconfigure(1, weight=1)
        
        # Document icon
        icon_label = ttk.Label(container, text="📄", font=(context.font_family, context.font_size + 2))
        icon_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))
        
        # Content area
        content_frame = ttk.Frame(container)
        content_frame.grid(row=0, column=1, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Title with highlighting
        title_label = tk.Label(
            content_frame,
            text=result.title,
            font=(context.font_family, context.font_size + 1, "bold"),
            fg="blue",
            cursor="hand2",
            anchor="w",
            justify="left"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Snippet with highlighting
        if result.snippet:
            snippet_text = self._create_snippet_widget(content_frame, result, context)
            snippet_text.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Metadata row
        if context.show_metadata:
            metadata_frame = ttk.Frame(content_frame)
            metadata_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
            
            # File info
            file_type = result.metadata.get("file_type", "unknown").upper()
            pages = result.metadata.get("total_pages", 0)
            words = result.metadata.get("total_words", 0)
            
            info_text = f"{file_type}"
            if pages > 0:
                info_text += f" • {pages} pages"
            if words > 0:
                info_text += f" • {words:,} words"
            
            ttk.Label(
                metadata_frame,
                text=info_text,
                font=(context.font_family, context.font_size - 1),
                foreground="gray"
            ).pack(side="left")
            
            # Upload date
            upload_date = result.metadata.get("upload_date")
            if upload_date:
                try:
                    date_obj = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%b %d, %Y")
                    ttk.Label(
                        metadata_frame,
                        text=f" • Uploaded {date_str}",
                        font=(context.font_family, context.font_size - 1),
                        foreground="gray"
                    ).pack(side="left")
                except:
                    pass
            
            # Relevance score (if enabled)
            if context.show_relevance:
                relevance_pct = int(result.relevance_score * 100)
                ttk.Label(
                    metadata_frame,
                    text=f" • {relevance_pct}% match",
                    font=(context.font_family, context.font_size - 1),
                    foreground="darkgreen"
                ).pack(side="right")
        
        return container
    
    def _create_snippet_widget(self, parent: tk.Widget, result: SearchResult, context: RenderContext) -> tk.Text:
        """Create text widget with highlighted snippet."""
        text_widget = tk.Text(
            parent,
            height=3,
            width=80,
            wrap="word",
            font=(context.font_family, context.font_size),
            relief="flat",
            state="disabled",
            cursor="arrow",
            bg=parent.cget("bg") if hasattr(parent, 'cget') else "white"
        )
        
        # Configure highlight tag
        text_widget.tag_configure(
            "highlight",
            background=context.highlight_color,
            foreground="black",
            font=(context.font_family, context.font_size, "bold")
        )
        
        # Insert snippet with highlights
        text_widget.config(state="normal")
        self._insert_highlighted_text(text_widget, result.snippet, context.query)
        text_widget.config(state="disabled")
        
        return text_widget
    
    def _insert_highlighted_text(self, text_widget: tk.Text, text: str, query: str) -> None:
        """Insert text with query terms highlighted."""
        if not query.strip():
            text_widget.insert("end", text)
            return
        
        # Create regex pattern for all query words
        query_words = [re.escape(word) for word in query.strip().split() if len(word) > 1]
        if not query_words:
            text_widget.insert("end", text)
            return
        
        pattern = r'\b(' + '|'.join(query_words) + r')\b'
        regex = re.compile(pattern, re.IGNORECASE)
        
        last_end = 0
        for match in regex.finditer(text):
            # Insert text before match
            text_widget.insert("end", text[last_end:match.start()])
            
            # Insert highlighted match
            text_widget.insert("end", match.group(), "highlight")
            
            last_end = match.end()
        
        # Insert remaining text
        text_widget.insert("end", text[last_end:])
    
    def get_priority(self) -> int:
        return 80


class ChunkResultRenderer(ResultRenderer):
    """Renderer for chunk/section search results."""
    
    def can_render(self, result: SearchResult) -> bool:
        return result.result_type in ["chunk", "section"]
    
    def render(self, result: SearchResult, parent: tk.Widget, context: RenderContext) -> tk.Widget:
        """Render chunk search result."""
        container = ttk.Frame(parent, padding=(10, 5))
        container.grid_columnconfigure(1, weight=1)
        
        # Chunk icon
        icon_label = ttk.Label(container, text="📑", font=(context.font_family, context.font_size + 2))
        icon_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))
        
        # Content area
        content_frame = ttk.Frame(container)
        content_frame.grid(row=0, column=1, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Document and chunk title
        doc_title = result.metadata.get("document_title", "Unknown Document")
        chunk_title = result.title
        
        # Document name (smaller, gray)
        doc_label = ttk.Label(
            content_frame,
            text=f"📄 {doc_title}",
            font=(context.font_family, context.font_size - 1),
            foreground="gray"
        )
        doc_label.grid(row=0, column=0, sticky="w")
        
        # Chunk title (main title)
        title_label = tk.Label(
            content_frame,
            text=chunk_title,
            font=(context.font_family, context.font_size, "bold"),
            fg="darkblue",
            cursor="hand2",
            anchor="w",
            justify="left"
        )
        title_label.grid(row=1, column=0, sticky="ew")
        
        # Snippet
        if result.snippet:
            snippet_text = self._create_snippet_widget(content_frame, result, context)
            snippet_text.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        
        # Metadata
        if context.show_metadata:
            metadata_frame = ttk.Frame(content_frame)
            metadata_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))
            
            # Chunk info
            chunk_index = result.metadata.get("chunk_index", 0)
            word_count = result.metadata.get("word_count", 0)
            chunk_type = result.metadata.get("chunk_type", "section")
            
            info_text = f"{chunk_type.title()} {chunk_index + 1}"
            if word_count > 0:
                info_text += f" • {word_count:,} words"
            
            ttk.Label(
                metadata_frame,
                text=info_text,
                font=(context.font_family, context.font_size - 1),
                foreground="gray"
            ).pack(side="left")
            
            # Relevance
            if context.show_relevance:
                relevance_pct = int(result.relevance_score * 100)
                ttk.Label(
                    metadata_frame,
                    text=f" • {relevance_pct}% match",
                    font=(context.font_family, context.font_size - 1),
                    foreground="darkgreen"
                ).pack(side="right")
        
        return container
    
    def _create_snippet_widget(self, parent: tk.Widget, result: SearchResult, context: RenderContext) -> tk.Text:
        """Create highlighted snippet widget."""
        # Similar to DocumentResultRenderer but shorter
        text_widget = tk.Text(
            parent,
            height=2,
            width=80,
            wrap="word",
            font=(context.font_family, context.font_size),
            relief="flat",
            state="disabled",
            cursor="arrow",
            bg=parent.cget("bg") if hasattr(parent, 'cget') else "white"
        )
        
        # Configure highlight tag
        text_widget.tag_configure(
            "highlight",
            background=context.highlight_color,
            foreground="black",
            font=(context.font_family, context.font_size, "bold")
        )
        
        # Insert snippet with highlights
        text_widget.config(state="normal")
        self._insert_highlighted_text(text_widget, result.snippet, context.query)
        text_widget.config(state="disabled")
        
        return text_widget
    
    def _insert_highlighted_text(self, text_widget: tk.Text, text: str, query: str) -> None:
        """Insert highlighted text (same as DocumentResultRenderer)."""
        if not query.strip():
            text_widget.insert("end", text)
            return
        
        query_words = [re.escape(word) for word in query.strip().split() if len(word) > 1]
        if not query_words:
            text_widget.insert("end", text)
            return
        
        pattern = r'\b(' + '|'.join(query_words) + r')\b'
        regex = re.compile(pattern, re.IGNORECASE)
        
        last_end = 0
        for match in regex.finditer(text):
            text_widget.insert("end", text[last_end:match.start()])
            text_widget.insert("end", match.group(), "highlight")
            last_end = match.end()
        
        text_widget.insert("end", text[last_end:])
    
    def get_priority(self) -> int:
        return 85


class BookmarkResultRenderer(ResultRenderer):
    """Renderer for bookmark search results."""
    
    def can_render(self, result: SearchResult) -> bool:
        return result.result_type == "bookmark"
    
    def render(self, result: SearchResult, parent: tk.Widget, context: RenderContext) -> tk.Widget:
        """Render bookmark search result."""
        container = ttk.Frame(parent, padding=(10, 5))
        container.grid_columnconfigure(1, weight=1)
        
        # Bookmark icon
        icon_label = ttk.Label(container, text="🔖", font=(context.font_family, context.font_size + 2))
        icon_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))
        
        # Content area
        content_frame = ttk.Frame(container)
        content_frame.grid(row=0, column=1, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Bookmark title
        title_label = tk.Label(
            content_frame,
            text=result.title,
            font=(context.font_family, context.font_size, "bold"),
            fg="darkorange",
            cursor="hand2",
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Document context
        doc_title = result.metadata.get("document_title", "Unknown Document")
        position = result.metadata.get("position", "")
        
        context_text = f"📄 {doc_title}"
        if position:
            context_text += f" • {position}"
        
        ttk.Label(
            content_frame,
            text=context_text,
            font=(context.font_family, context.font_size - 1),
            foreground="gray"
        ).grid(row=1, column=0, sticky="w")
        
        # Bookmark notes/snippet
        notes = result.metadata.get("notes", result.snippet)
        if notes:
            notes_widget = tk.Text(
                content_frame,
                height=2,
                width=80,
                wrap="word",
                font=(context.font_family, context.font_size),
                relief="flat",
                state="disabled",
                cursor="arrow",
                bg=parent.cget("bg") if hasattr(parent, 'cget') else "white"
            )
            
            notes_widget.config(state="normal")
            notes_widget.insert("end", notes)
            notes_widget.config(state="disabled")
            
            notes_widget.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        
        return container
    
    def get_priority(self) -> int:
        return 75


class DefaultResultRenderer(ResultRenderer):
    """Fallback renderer for unknown result types."""
    
    def can_render(self, result: SearchResult) -> bool:
        return True  # Can render any result type
    
    def render(self, result: SearchResult, parent: tk.Widget, context: RenderContext) -> tk.Widget:
        """Render generic search result."""
        container = ttk.Frame(parent, padding=(10, 5))
        container.grid_columnconfigure(1, weight=1)
        
        # Generic icon
        icon_label = ttk.Label(container, text="📋", font=(context.font_family, context.font_size + 2))
        icon_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))
        
        # Content area
        content_frame = ttk.Frame(container)
        content_frame.grid(row=0, column=1, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = tk.Label(
            content_frame,
            text=result.title,
            font=(context.font_family, context.font_size, "bold"),
            cursor="hand2",
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Type and snippet
        type_text = f"Type: {result.result_type}"
        ttk.Label(
            content_frame,
            text=type_text,
            font=(context.font_family, context.font_size - 1),
            foreground="gray"
        ).grid(row=1, column=0, sticky="w")
        
        if result.snippet:
            snippet_label = ttk.Label(
                content_frame,
                text=result.snippet[:200] + ("..." if len(result.snippet) > 200 else ""),
                font=(context.font_family, context.font_size),
                wraplength=600,
                justify="left"
            )
            snippet_label.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        
        return container
    
    def get_priority(self) -> int:
        return 1  # Lowest priority (fallback)


class SearchResultRenderer:
    """
    Advanced search result rendering system with context-aware highlighting.
    
    Responsibilities:
    - Render different types of search results with appropriate formatting
    - Apply intelligent highlighting based on search query
    - Extract and display relevant content snippets
    - Provide configurable rendering options through context
    
    Architecture:
    - Uses Strategy pattern for different result types
    - Supports extensible renderer registration
    - Provides consistent formatting with theme integration
    - Follows Single Responsibility and Open/Closed principles
    """
    
    def __init__(self, theme_config: Optional[Dict[str, Any]] = None):
        """
        Initialize result renderer.
        
        Args:
            theme_config: Optional theme configuration for rendering
        """
        self.theme_config = theme_config or {}
        self.renderers: List[ResultRenderer] = []
        self.result_click_handlers: Dict[str, Callable] = {}
        
        # Initialize default renderers
        self._initialize_renderers()
        
        logger.info("SearchResultRenderer initialized with %d renderers", len(self.renderers))
    
    def _initialize_renderers(self) -> None:
        """Initialize default result renderers."""
        self.renderers = [
            ChunkResultRenderer(),
            DocumentResultRenderer(), 
            BookmarkResultRenderer(),
            DefaultResultRenderer()  # Fallback
        ]
        
        # Sort by priority (highest first)
        self.renderers.sort(key=lambda r: r.get_priority(), reverse=True)
    
    def render_results(
        self,
        results: List[SearchResult],
        parent: tk.Widget,
        query: str = "",
        max_results: Optional[int] = None,
        render_options: Optional[Dict[str, Any]] = None
    ) -> List[tk.Widget]:
        """
        Render list of search results as widgets.
        
        Args:
            results: Search results to render
            parent: Parent widget container
            query: Original search query for highlighting
            max_results: Maximum number of results to render
            render_options: Optional rendering configuration
            
        Returns:
            List of rendered result widgets
        """
        if max_results:
            results = results[:max_results]
        
        # Create render context
        context = self._create_render_context(query, render_options)
        
        rendered_widgets = []
        
        for i, result in enumerate(results):
            try:
                # Generate snippet if not provided
                if not result.snippet and result.content:
                    result.snippet = self._extract_snippet(result.content, query, context.max_snippet_length)
                
                # Find appropriate renderer
                renderer = self._select_renderer(result)
                if not renderer:
                    logger.warning("No renderer available for result type: %s", result.result_type)
                    continue
                
                # Render result
                result_widget = renderer.render(result, parent, context)
                
                # Add hover effect
                self._add_hover_effect(result_widget)
                
                # Add click handler if configured
                if result.result_type in self.result_click_handlers:
                    self._add_click_handler(result_widget, result, self.result_click_handlers[result.result_type])
                
                rendered_widgets.append(result_widget)
                
                logger.debug("Rendered result %d: %s", i + 1, result.title[:50])
                
            except Exception as e:
                logger.error("Failed to render result %d: %s", i + 1, e)
        
        return rendered_widgets
    
    def _create_render_context(self, query: str, options: Optional[Dict[str, Any]]) -> RenderContext:
        """Create render context from options and theme config."""
        # Default options
        context_options = {
            "max_snippet_length": 300,
            "highlight_color": "yellow",
            "font_family": "Arial",
            "font_size": 10,
            "show_metadata": True,
            "show_relevance": False,
            "compact_mode": False
        }
        
        # Apply theme config
        theme_search = self.theme_config.get("search_results", {})
        context_options.update(theme_search)
        
        # Apply user options
        if options:
            context_options.update(options)
        
        return RenderContext(
            query=query,
            **context_options
        )
    
    def _select_renderer(self, result: SearchResult) -> Optional[ResultRenderer]:
        """Select most appropriate renderer for result."""
        for renderer in self.renderers:
            if renderer.can_render(result):
                return renderer
        return None
    
    def _extract_snippet(self, content: str, query: str, max_length: int) -> str:
        """Extract relevant snippet from content based on query."""
        if not query.strip() or not content:
            return content[:max_length] + ("..." if len(content) > max_length else "")
        
        # Find best match position
        query_words = [word.lower() for word in query.strip().split() if len(word) > 1]
        if not query_words:
            return content[:max_length] + ("..." if len(content) > max_length else "")
        
        content_lower = content.lower()
        best_position = 0
        best_score = 0
        
        # Find position with most query word matches
        for i in range(0, len(content) - max_length + 1, 50):  # Check every 50 chars
            snippet = content_lower[i:i + max_length]
            score = sum(1 for word in query_words if word in snippet)
            
            if score > best_score:
                best_score = score
                best_position = i
        
        # Extract snippet around best position
        start = max(0, best_position)
        end = min(len(content), start + max_length)
        
        snippet = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _add_hover_effect(self, widget: tk.Widget) -> None:
        """Add hover effect to result widget."""
        def on_enter(event):
            try:
                # Only apply to Frame widgets that support these options
                if isinstance(widget, (tk.Frame, ttk.Frame)):
                    widget.configure(relief="solid", borderwidth=1)
            except (tk.TclError, AttributeError):
                pass  # Some widgets don't support these options
        
        def on_leave(event):
            try:
                if isinstance(widget, (tk.Frame, ttk.Frame)):
                    widget.configure(relief="flat", borderwidth=0)
            except (tk.TclError, AttributeError):
                pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        # Apply to all child widgets too
        for child in widget.winfo_children():
            if isinstance(child, (tk.Widget, ttk.Widget)):
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)
    
    def _add_click_handler(self, widget: tk.Widget, result: SearchResult, handler: Callable) -> None:
        """Add click handler to result widget."""
        def on_click(event):
            try:
                handler(result)
            except Exception as e:
                logger.error("Error in result click handler: %s", e)
        
        widget.bind("<Button-1>", on_click)
        # Set cursor to indicate clickable (suppress type checker warnings)
        try:
            widget.configure(cursor="hand2")  # type: ignore
        except Exception:
            pass
        
        # Apply to all child widgets too
        for child in widget.winfo_children():
            if isinstance(child, (tk.Widget, ttk.Widget)):
                child.bind("<Button-1>", on_click)
                try:
                    child.configure(cursor="hand2")  # type: ignore
                except Exception:
                    pass
    
    def register_click_handler(self, result_type: str, handler: Callable[[SearchResult], None]) -> None:
        """
        Register click handler for specific result type.
        
        Args:
            result_type: Type of result to handle clicks for
            handler: Function to call when result is clicked
        """
        self.result_click_handlers[result_type] = handler
        logger.info("Registered click handler for result type: %s", result_type)
    
    def add_custom_renderer(self, renderer: ResultRenderer) -> None:
        """
        Add custom result renderer.
        
        Args:
            renderer: Custom renderer implementation
        """
        self.renderers.append(renderer)
        self.renderers.sort(key=lambda r: r.get_priority(), reverse=True)
        logger.info("Added custom result renderer: %s", type(renderer).__name__)
    
    def update_theme(self, theme_config: Dict[str, Any]) -> None:
        """
        Update theme configuration for rendering.
        
        Args:
            theme_config: New theme configuration
        """
        self.theme_config = theme_config
        logger.info("Updated result renderer theme configuration")
    
    def create_pagination_widget(
        self,
        parent: tk.Widget,
        current_page: int,
        total_pages: int,
        page_size: int,
        on_page_change: Callable[[int], None]
    ) -> tk.Widget:
        """
        Create pagination controls for search results.
        
        Args:
            parent: Parent widget
            current_page: Current page number (1-based)
            total_pages: Total number of pages
            page_size: Results per page
            on_page_change: Callback for page changes
            
        Returns:
            Pagination widget
        """
        if total_pages <= 1:
            return ttk.Frame(parent)  # Empty frame if no pagination needed
        
        pagination_frame = ttk.Frame(parent, padding=(5, 10))
        
        # Previous button
        prev_btn = ttk.Button(
            pagination_frame,
            text="← Previous",
            command=lambda: on_page_change(current_page - 1),
            state="normal" if current_page > 1 else "disabled"
        )
        prev_btn.pack(side="left", padx=(0, 5))
        
        # Page info
        info_label = ttk.Label(
            pagination_frame,
            text=f"Page {current_page} of {total_pages}"
        )
        info_label.pack(side="left", padx=(5, 5))
        
        # Next button
        next_btn = ttk.Button(
            pagination_frame,
            text="Next →",
            command=lambda: on_page_change(current_page + 1),
            state="normal" if current_page < total_pages else "disabled"
        )
        next_btn.pack(side="left", padx=(5, 0))
        
        # Jump to page (if many pages)
        if total_pages > 5:
            ttk.Label(pagination_frame, text="Go to:").pack(side="right", padx=(10, 2))
            
            page_var = tk.StringVar(value=str(current_page))
            page_entry = ttk.Entry(pagination_frame, textvariable=page_var, width=5)
            page_entry.pack(side="right", padx=(0, 2))
            
            def go_to_page():
                try:
                    page = int(page_var.get())
                    if 1 <= page <= total_pages:
                        on_page_change(page)
                except ValueError:
                    pass
            
            go_btn = ttk.Button(pagination_frame, text="Go", command=go_to_page)
            go_btn.pack(side="right")
        
        return pagination_frame