"""
Content Viewer Widget for Study Buddy GUI Application.

This module implements ContentViewerWidget, a concrete widget extending BaseWidget
to display document content in a readable format. Provides content viewing,
text formatting, and document navigation capabilities with MCP integration.

Architecture: Clean Architecture Layer 1 (External Interface)  
Dependencies: BaseWidget (Layer 1), EventBus (Layer 2), MCP Client (Layer 3)
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

# Import base widget system
from ..widgets.base_widget import (
    BaseWidget, 
    WidgetState, 
    LayoutConstraints, 
    AccessibilityOptions
)
from ..events import EventBus, GlobalEvent

# Import database adapter for direct content access
try:
    from ..database_adapter import get_database_adapter
    DATABASE_ADAPTER_AVAILABLE = True
except ImportError:
    DATABASE_ADAPTER_AVAILABLE = False
    get_database_adapter = None


@dataclass
class ContentDisplayOptions:
    """Configuration options for content display."""
    font_family: str = "Segoe UI"
    font_size: int = 11
    line_spacing: float = 1.2
    wrap_text: bool = True
    show_line_numbers: bool = False
    syntax_highlighting: bool = True
    max_content_length: int = 1000000  # 1MB text limit


@dataclass
class DocumentContent:
    """Container for document content and metadata."""
    document_id: int
    title: str
    content: str
    file_type: str
    word_count: int
    character_count: int
    load_time: datetime
    is_truncated: bool = False
    
    @property
    def display_info(self) -> str:
        """Get formatted display information."""
        info_parts = [
            f"Words: {self.word_count:,}",
            f"Characters: {self.character_count:,}",
            f"Type: {self.file_type.upper()}"
        ]
        if self.is_truncated:
            info_parts.append("(Truncated)")
        return " | ".join(info_parts)


class ContentViewerWidget(BaseWidget):
    """
    Content viewer widget for displaying document content.
    
    Responsibilities:
    - Display document content in readable format
    - Handle document selection events  
    - Provide text formatting and navigation
    - Integrate with MCP client for content retrieval
    - Support different document types
    
    Does NOT:
    - Edit or modify document content
    - Handle document upload/deletion
    - Manage document metadata
    - Implement document parsing (delegates to MCP)
    """
    
    # Type annotations for timer attributes
    _search_timer: Optional[str] = None
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: EventBus,
        widget_id: str,
        mcp_client: Optional[Any] = None,
        constraints: Optional[LayoutConstraints] = None,
        accessibility: Optional[AccessibilityOptions] = None,
        display_options: Optional[ContentDisplayOptions] = None
    ):
        """
        Initialize content viewer widget.
        
        Args:
            parent: Parent tkinter widget
            event_bus: Global event bus for communication
            widget_id: Unique identifier for this widget instance
            mcp_client: MCP client for content retrieval operations
            constraints: Layout constraints for responsive design  
            accessibility: Accessibility options
            display_options: Content display configuration
        """
        # Initialize attributes BEFORE calling super().__init__()
        # because BaseWidget constructor will call create_ui()
        
        # MCP integration
        self.mcp_client = mcp_client
        
        # Display configuration
        self.display_options = display_options or ContentDisplayOptions()
        
        # Current document state
        self._current_document: Optional[DocumentContent] = None
        self._loading_content: bool = False
        
        # Text formatting state
        self._font_size: int = self.display_options.font_size
        self._wrap_mode: bool = self.display_options.wrap_text
        
        # Search state
        self._search_query: str = ""
        self._search_results: List[Tuple[str, str]] = []  # (start_index, end_index)
        self._current_search_index: int = -1
        
        # UI components (will be created in create_ui)
        self._main_frame: Optional[ttk.Frame] = None
        self._toolbar_frame: Optional[ttk.Frame] = None
        self._content_frame: Optional[ttk.Frame] = None
        self._status_frame: Optional[ttk.Frame] = None
        
        # Toolbar components
        self._font_size_var: Optional[tk.StringVar] = None
        self._wrap_var: Optional[tk.BooleanVar] = None
        self._search_entry: Optional[tk.Entry] = None
        
        # Content display components
        self._text_widget: Optional[tk.Text] = None
        self._v_scrollbar: Optional[ttk.Scrollbar] = None
        self._h_scrollbar: Optional[ttk.Scrollbar] = None
        
        # Status components
        self._status_label: Optional[tk.Label] = None
        self._document_info_label: Optional[tk.Label] = None
        
        # NOW call parent constructor (which will call create_ui)
        super().__init__(parent, event_bus, widget_id, constraints, accessibility)

    def create_ui(self) -> None:
        """
        Create the content viewer UI components.
        
        Layout:
        - Toolbar (font controls, search, view options)
        - Content area (scrollable text widget)
        - Status bar (document info, position)
        """
        try:
            self._logger.info(f"Creating content viewer UI for widget {self.widget_id}")
            
            # Create main frame
            self._main_frame = ttk.Frame(self.root_frame)
            self._main_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Create UI sections
            self._create_toolbar()
            self._create_content_area()
            self._create_status_bar()
            
            # Setup event handlers
            self._setup_event_handlers()
            
            # Setup accessibility
            self._setup_accessibility()
            
            # Set initial state
            self._update_display("No document selected")
            
            self._logger.info("Content viewer UI created successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to create content viewer UI: {e}", exc_info=True)
            self.state = WidgetState.ERROR
            self._last_error = e

    def _create_toolbar(self) -> None:
        """Create toolbar with font controls, search, and view options."""
        self._toolbar_frame = ttk.Frame(self._main_frame)
        self._toolbar_frame.pack(fill="x", pady=(0, 5))
        
        # Font size control
        ttk.Label(self._toolbar_frame, text="Font Size:").pack(side="left", padx=(0, 5))
        
        self._font_size_var = tk.StringVar(value=str(self._font_size))
        font_combo = ttk.Combobox(
            self._toolbar_frame,
            textvariable=self._font_size_var,
            values=["8", "9", "10", "11", "12", "14", "16", "18", "20"],
            width=5,
            state="readonly"
        )
        font_combo.pack(side="left", padx=(0, 10))
        font_combo.bind("<<ComboboxSelected>>", self._on_font_size_changed)
        
        # Separator
        ttk.Separator(self._toolbar_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Text wrap toggle
        self._wrap_var = tk.BooleanVar(value=self._wrap_mode)
        wrap_check = ttk.Checkbutton(
            self._toolbar_frame,
            text="Wrap Text",
            variable=self._wrap_var,
            command=self._on_wrap_changed
        )
        wrap_check.pack(side="left", padx=(0, 10))
        
        # Separator
        ttk.Separator(self._toolbar_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Search controls
        ttk.Label(self._toolbar_frame, text="Search:").pack(side="left", padx=(0, 5))
        
        self._search_entry = tk.Entry(self._toolbar_frame, width=20)
        self._search_entry.pack(side="left", padx=(0, 5))
        self._search_entry.bind("<Return>", self._on_search_activate)
        self._search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # Search navigation buttons
        search_prev_btn = ttk.Button(
            self._toolbar_frame,
            text="◀",
            width=3,
            command=self._search_previous
        )
        search_prev_btn.pack(side="left", padx=(0, 2))
        
        search_next_btn = ttk.Button(
            self._toolbar_frame,
            text="▶",
            width=3,
            command=self._search_next
        )
        search_next_btn.pack(side="left", padx=(0, 10))
        
        # Spacer to push refresh button to right
        spacer_frame = ttk.Frame(self._toolbar_frame)
        spacer_frame.pack(side="left", fill="x", expand=True)
        
        # Refresh button
        refresh_btn = ttk.Button(
            self._toolbar_frame,
            text="🔄 Refresh",
            command=self._refresh_content
        )
        refresh_btn.pack(side="right")

    def _create_content_area(self) -> None:
        """Create scrollable text content area."""
        self._content_frame = ttk.Frame(self._main_frame)
        self._content_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Create text widget with scrollbars
        text_frame = ttk.Frame(self._content_frame)
        text_frame.pack(fill="both", expand=True)
        
        # Configure grid weights for proper expansion
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        # Text widget
        self._text_widget = tk.Text(
            text_frame,
            wrap="word" if self._wrap_mode else "none",
            state="disabled",
            bg="white",
            fg="black",
            font=(self.display_options.font_family, self._font_size),
            spacing1=int(self._font_size * 0.2),  # Line spacing
            spacing2=int(self._font_size * 0.1),
            spacing3=int(self._font_size * 0.2),
            padx=10,
            pady=10,
            selectbackground="#316AC5",
            selectforeground="white"
        )
        self._text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Vertical scrollbar
        self._v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self._text_widget.yview)
        self._v_scrollbar.grid(row=0, column=1, sticky="ns")
        self._text_widget.config(yscrollcommand=self._v_scrollbar.set)
        
        # Horizontal scrollbar (shown when text wrapping is off)
        self._h_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=self._text_widget.xview)
        if not self._wrap_mode:
            self._h_scrollbar.grid(row=1, column=0, sticky="ew")
            self._text_widget.config(xscrollcommand=self._h_scrollbar.set)
        
        # Text widget event bindings
        self._text_widget.bind("<Button-1>", self._on_text_clicked)
        self._text_widget.bind("<Control-f>", lambda e: self._search_entry.focus_set() if self._search_entry else None)
        self._text_widget.bind("<Control-plus>", lambda e: self._change_font_size(1))
        self._text_widget.bind("<Control-minus>", lambda e: self._change_font_size(-1))

    def _create_status_bar(self) -> None:
        """Create status bar with document information."""
        self._status_frame = ttk.Frame(self._main_frame)
        self._status_frame.pack(fill="x", pady=(5, 0))
        
        # Document info label (left side)
        self._document_info_label = tk.Label(
            self._status_frame,
            text="No document loaded",
            font=("Segoe UI", 9),
            fg="gray",
            anchor="w"
        )
        self._document_info_label.pack(side="left", fill="x", expand=True)
        
        # Status label (right side)  
        self._status_label = tk.Label(
            self._status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            fg="gray",
            anchor="e"
        )
        self._status_label.pack(side="right")

    def _setup_event_handlers(self) -> None:
        """Setup event subscriptions for document-related events."""
        # Call parent to setup base event handlers
        super()._setup_event_handlers()
        
        # Subscribe to document selection events
        self._subscribe_event('document.selected', self._on_document_selected)
        self._subscribe_event('document.content_updated', self._on_document_updated)
        self._subscribe_event('document.deleted', self._on_document_deleted)

    def _setup_accessibility(self) -> None:
        """Setup accessibility features for keyboard navigation."""
        # Check if UI components exist before setting up accessibility
        if hasattr(self, '_text_widget') and self._text_widget:
            # Keyboard shortcuts
            self._text_widget.bind("<F3>", lambda e: self._search_next())
            self._text_widget.bind("<Shift-F3>", lambda e: self._search_previous())
            
        if hasattr(self, '_search_entry') and self._search_entry:
            # Search entry keyboard navigation
            self._search_entry.bind("<Escape>", lambda e: self._clear_search())
            self._search_entry.bind("<Tab>", lambda e: self._text_widget.focus_set() if self._text_widget else None)
            
        # Screen reader support
        if self.accessibility.screen_reader_label:
            # Would set aria-label equivalent for screen readers
            pass

    # Event Handlers
    def _on_document_selected(self, event: GlobalEvent) -> None:
        """Handle document selection event from DocumentBrowserWidget."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            document = event_data.get('document')
            
            if not document_id:
                self._logger.warning("Received document_selected event without document_id")
                return
                
            self._logger.info(f"Document selected: ID {document_id}")
            
            # Load document content asynchronously
            self._load_document_content(document_id, document)
            
        except Exception as e:
            self._logger.error(f"Error handling document selection: {e}", exc_info=True)
            self._update_status(f"Error: {str(e)}")

    def _on_document_updated(self, event: GlobalEvent) -> None:
        """Handle document content update event."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            if self._current_document and self._current_document.document_id == document_id:
                # Refresh current document content
                self._refresh_content()
        except Exception as e:
            self._logger.error(f"Error handling document update: {e}", exc_info=True)

    def _on_document_deleted(self, event: GlobalEvent) -> None:
        """Handle document deletion event."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            if self._current_document and self._current_document.document_id == document_id:
                # Clear content if current document was deleted
                self._clear_content()
                self._update_status("Document was deleted")
        except Exception as e:
            self._logger.error(f"Error handling document deletion: {e}", exc_info=True)

    def _on_font_size_changed(self, event) -> None:
        """Handle font size selection change."""
        try:
            if self._font_size_var:
                new_size = int(self._font_size_var.get())
                self._change_font_size(new_size - self._font_size)
        except (ValueError, TypeError):
            pass  # Invalid font size, ignore

    def _on_wrap_changed(self) -> None:
        """Handle text wrapping toggle."""
        if not self._text_widget or not self._wrap_var:
            return
            
        self._wrap_mode = self._wrap_var.get()
        
        # Update text widget wrap mode
        self._text_widget.config(wrap="word" if self._wrap_mode else "none")
        
        # Show/hide horizontal scrollbar based on wrap mode
        if self._wrap_mode:
            if self._h_scrollbar:
                self._h_scrollbar.grid_remove()
            if self._text_widget:
                self._text_widget.config(xscrollcommand="")
        else:
            if self._h_scrollbar:
                self._h_scrollbar.grid(row=1, column=0, sticky="ew")
            if self._text_widget and self._h_scrollbar:
                self._text_widget.config(xscrollcommand=self._h_scrollbar.set)

    def _on_search_activate(self, event) -> None:
        """Handle search entry activation (Enter key)."""
        self._perform_search()

    def _on_search_changed(self, event) -> None:
        """Handle search query change.""" 
        # Debounce search to avoid excessive updates
        if hasattr(self, '_search_timer') and self._search_timer and self.root_frame:
            self.root_frame.after_cancel(self._search_timer)
        
        if self.root_frame:
            self._search_timer = self.root_frame.after(300, self._perform_search)

    def _on_text_clicked(self, event) -> None:
        """Handle text widget click for cursor positioning."""
        if self._text_widget and self._current_document:
            # Update status with cursor position
            cursor_pos = self._text_widget.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self._update_status(f"Line {line}, Column {col}")

    # Content Management
    def _load_document_content(self, document_id: int, document_metadata: Optional[Any] = None) -> None:
        """Load document content from database adapter or MCP client."""
        if self._loading_content:
            return
            
        self._loading_content = True
        self.show_loading("Loading document content...")
        
        try:
            # Clear current search
            self._clear_search()
            
            # Try database adapter first (direct access when MCP not available)
            content = None
            if DATABASE_ADAPTER_AVAILABLE and get_database_adapter is not None:
                try:
                    db_adapter = get_database_adapter()
                    
                    # Get document info
                    doc_data = db_adapter.get_document(document_id)
                    if doc_data:
                        
                        # Get document structure (chunks)
                        structure_result = db_adapter.get_document_structure(document_id)
                        if structure_result and 'chunks' in structure_result:
                            # Combine all chunk content to show full document
                            full_content = ""
                            chunks = structure_result['chunks']
                            
                            for chunk in chunks:
                                chunk_result = db_adapter.get_chunk_content(chunk['chunk_id'])
                                if chunk_result and 'content' in chunk_result:
                                    chunk_content = chunk_result['content']
                                    full_content += f"\n\n## {chunk.get('title', f'Chunk {chunk['chunk_index'] + 1}')}\n\n"
                                    full_content += chunk_content + "\n"
                            
                            if full_content:
                                # Create DocumentContent object
                                content = DocumentContent(
                                    document_id=document_id,
                                    title=doc_data.get('title', 'Unknown Document'),
                                    content=full_content.strip(),
                                    file_type=doc_data.get('file_type', 'unknown'),
                                    word_count=len(full_content.split()),
                                    character_count=len(full_content),
                                    load_time=datetime.now()
                                )
                                self._logger.info(f"Loaded document content from database: {len(chunks)} chunks, {len(full_content)} characters")
                        else:
                            # No chunks, try to show document metadata
                            content = DocumentContent(
                                document_id=document_id,
                                title=doc_data.get('title', 'Unknown Document'),
                                content=f"Document: {doc_data.get('title', 'Unknown')}\n\nThis document has not been indexed yet. Use the MCP server to index it into chunks.",
                                file_type=doc_data.get('file_type', 'unknown'),
                                word_count=doc_data.get('total_words', 0),
                                character_count=0,
                                load_time=datetime.now()
                            )
                    
                except Exception as e:
                    self._logger.warning(f"Database adapter failed, falling back to MCP: {e}")
            
            # Fallback to MCP client if database didn't work
            if content is None:
                if self.mcp_client and hasattr(self.mcp_client, 'call_tool'):
                    # TODO: Call MCP to get document content when MCP server is available
                    # self.mcp_client.call_tool("get_document_content", {"document_id": document_id})
                    self._logger.warning("MCP document content loading not yet implemented")
                    content = DocumentContent(
                        document_id=document_id,
                        title="Unknown Document",
                        content="No content available. Please ensure the document is properly indexed.",
                        file_type="unknown",
                        word_count=0,
                        character_count=0,
                        load_time=datetime.now()
                    )
                else:
                    # No MCP client and database failed
                    self._logger.error("Cannot load document content - no MCP client and database failed")
                    content = DocumentContent(
                        document_id=document_id,
                        title="Error Loading Document",
                        content="Error: Cannot load document content. Please check the database connection.",
                        file_type="unknown",
                        word_count=0,
                        character_count=0,
                        load_time=datetime.now()
                    )
            
            # Update display
            self._current_document = content
            self._display_content(content)
            self._update_document_info(content)
            self._update_status("Document loaded successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to load document content: {e}", exc_info=True)
            self._update_display(f"Error loading document: {str(e)}")
            self._update_status(f"Error: {str(e)}")
        finally:
            self._loading_content = False
            self.hide_loading()



    def _display_content(self, content: DocumentContent) -> None:
        """Display document content in the text widget."""
        if not self._text_widget:
            return
            
        # Enable text widget for editing
        self._text_widget.config(state="normal")
        
        # Clear existing content
        self._text_widget.delete("1.0", tk.END)
        
        # Insert new content
        display_text = content.content
        if content.is_truncated:
            display_text = display_text[:self.display_options.max_content_length] + "\n\n[Content truncated...]"
        
        self._text_widget.insert("1.0", display_text)
        
        # Apply syntax highlighting based on file type
        self._apply_syntax_highlighting(content.file_type)
        
        # Disable text widget (read-only)
        self._text_widget.config(state="disabled")
        
        # Scroll to top
        self._text_widget.see("1.0")

    def _apply_syntax_highlighting(self, file_type: str) -> None:
        """Apply basic syntax highlighting based on file type."""
        if not self._text_widget or not self.display_options.syntax_highlighting:
            return
            
        try:
            # Configure text tags for highlighting
            self._text_widget.tag_configure("heading", font=(self.display_options.font_family, self._font_size + 2, "bold"), foreground="#2E5090")
            self._text_widget.tag_configure("code", font=("Consolas", self._font_size), background="#f5f5f5", foreground="#d73a49")
            self._text_widget.tag_configure("link", foreground="#0366d6", underline=True)
            
            content = self._text_widget.get("1.0", tk.END)
            
            if file_type in ["md", "markdown"]:
                self._highlight_markdown(content)
            elif file_type in ["py", "python"]:
                self._highlight_python(content)
            
        except Exception as e:
            self._logger.error(f"Error applying syntax highlighting: {e}")

    def _highlight_markdown(self, content: str) -> None:
        """Apply markdown syntax highlighting."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            
            # Headings
            if line.startswith('#') and self._text_widget:
                line_end = f"{i+1}.end"
                self._text_widget.tag_add("heading", line_start, line_end)
            
            # Code blocks (inline)
            if self._text_widget:
                code_pattern = r'`([^`]+)`'
                for match in re.finditer(code_pattern, line):
                    start_idx = f"{i+1}.{match.start()}"
                    end_idx = f"{i+1}.{match.end()}"
                    self._text_widget.tag_add("code", start_idx, end_idx)
    
    def _highlight_python(self, content: str) -> None:
        """Apply basic Python syntax highlighting."""
        # This is a simplified implementation
        # In a real application, you'd use a proper syntax highlighter
        keywords = ["def", "class", "import", "from", "if", "else", "elif", "for", "while", "try", "except"]
        
        if not self._text_widget:
            return
            
        for keyword in keywords:
            start = "1.0"
            while True:
                pos = self._text_widget.search(f"\\m{keyword}\\M", start, tk.END, regexp=True)
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self._text_widget.tag_add("code", pos, end)
                start = end

    def _update_document_info(self, content: DocumentContent) -> None:
        """Update document information display."""
        if self._document_info_label:
            info_text = f"{content.title} | {content.display_info}"
            self._document_info_label.config(text=info_text)

    def _update_display(self, message: str) -> None:
        """Update content display with a message."""
        if not self._text_widget:
            return
            
        self._text_widget.config(state="normal")
        self._text_widget.delete("1.0", tk.END)
        self._text_widget.insert("1.0", message)
        self._text_widget.config(state="disabled")
        
        if self._document_info_label:
            self._document_info_label.config(text="No document loaded")

    def _update_status(self, message: str) -> None:
        """Update status bar message.""" 
        if self._status_label:
            self._status_label.config(text=message)

    def _clear_content(self) -> None:
        """Clear current document content."""
        self._current_document = None
        self._update_display("No document selected")
        self._clear_search()

    def _refresh_content(self) -> None:
        """Refresh current document content."""
        if self._current_document:
            self._load_document_content(self._current_document.document_id)
        else:
            self._update_status("No document to refresh")

    # Font and Display Controls
    def _change_font_size(self, delta: int) -> None:
        """Change font size by delta amount."""
        new_size = max(8, min(24, self._font_size + delta))
        if new_size != self._font_size:
            self._font_size = new_size
            
            # Update font size variable
            if self._font_size_var:
                self._font_size_var.set(str(new_size))
            
            # Update text widget font
            if self._text_widget:
                current_font = self._text_widget.cget("font")
                if isinstance(current_font, tuple):
                    new_font = (current_font[0], new_size)
                else:
                    new_font = (self.display_options.font_family, new_size)
                self._text_widget.config(font=new_font)
            
            # Re-apply syntax highlighting with new font size
            if self._current_document:
                self._apply_syntax_highlighting(self._current_document.file_type)

    # Search Functionality
    def _perform_search(self) -> None:
        """Perform search in document content."""
        if not self._text_widget or not self._search_entry:
            return
            
        query = self._search_entry.get().strip()
        if not query:
            self._clear_search()
            return
            
        self._search_query = query
        self._search_results = []
        self._current_search_index = -1
        
        # Clear previous search highlighting
        self._text_widget.tag_remove("search_highlight", "1.0", tk.END)
        
        # Find all occurrences
        start = "1.0"
        while True:
            pos = self._text_widget.search(query, start, tk.END, nocase=True)
            if not pos:
                break
                
            end_pos = f"{pos}+{len(query)}c"
            self._search_results.append((pos, end_pos))
            start = end_pos
        
        # Highlight search results
        if self._search_results:
            self._text_widget.tag_configure("search_highlight", background="#ffeb3b", foreground="black")
            for start_pos, end_pos in self._search_results:
                self._text_widget.tag_add("search_highlight", start_pos, end_pos)
            
            # Navigate to first result
            self._current_search_index = 0
            self._highlight_current_search_result()
            self._update_status(f"Found {len(self._search_results)} matches")
        else:
            self._update_status("No matches found")

    def _search_next(self) -> None:
        """Navigate to next search result."""
        if not self._search_results:
            return
            
        self._current_search_index = (self._current_search_index + 1) % len(self._search_results)
        self._highlight_current_search_result()

    def _search_previous(self) -> None:
        """Navigate to previous search result."""
        if not self._search_results:
            return
            
        self._current_search_index = (self._current_search_index - 1) % len(self._search_results)
        self._highlight_current_search_result()

    def _highlight_current_search_result(self) -> None:
        """Highlight current search result."""
        if not self._search_results or self._current_search_index < 0:
            return
            
        if not self._text_widget:
            return
            
        # Clear previous current highlight
        self._text_widget.tag_remove("current_search", "1.0", tk.END)
        
        # Highlight current result
        start_pos, end_pos = self._search_results[self._current_search_index]
        self._text_widget.tag_configure("current_search", background="#ff5722", foreground="white")
        self._text_widget.tag_add("current_search", start_pos, end_pos)
        
        # Scroll to current result
        self._text_widget.see(start_pos)
        
        # Update status
        current = self._current_search_index + 1
        total = len(self._search_results)
        self._update_status(f"Match {current} of {total}")

    def _clear_search(self) -> None:
        """Clear search results and highlighting."""
        if self._text_widget:
            self._text_widget.tag_remove("search_highlight", "1.0", tk.END)
            self._text_widget.tag_remove("current_search", "1.0", tk.END)
        
        if self._search_entry:
            self._search_entry.delete(0, tk.END)
        
        self._search_query = ""
        self._search_results = []
        self._current_search_index = -1

    # Public API Methods
    def load_document(self, document_id: int) -> None:
        """Public method to load a specific document."""
        self._load_document_content(document_id)

    def get_current_document(self) -> Optional[DocumentContent]:
        """Get currently displayed document."""
        return self._current_document

    def set_font_size(self, size: int) -> None:
        """Public method to set font size."""
        self._change_font_size(size - self._font_size)

    def search(self, query: str) -> None:
        """Public method to search within content."""
        if self._search_entry:
            self._search_entry.delete(0, tk.END)
            self._search_entry.insert(0, query)
            self._perform_search()

    def clear_content(self) -> None:
        """Public method to clear displayed content."""
        self._clear_content()
    
    def update_display_options(self, options: ContentDisplayOptions) -> None:
        """Update display options and refresh view."""
        self._display_options = options
        
        # Apply new options if content is loaded
        if self._current_document and self._text_widget:
            # Update font
            self._text_widget.config(
                font=(options.font_family, options.font_size)
            )
            
            # Update wrap mode
            if options.wrap_text != self._wrap_mode:
                self._wrap_mode = options.wrap_text
                self._on_wrap_changed()
            
            # Re-apply syntax highlighting if enabled
            if options.syntax_highlighting:
                self._apply_syntax_highlighting(self._current_document.file_type)
    
    def next_search_result(self) -> None:
        """Navigate to next search result."""
        if not self._search_results:
            return
            
        self._current_search_index = (self._current_search_index + 1) % len(self._search_results)
        self._highlight_current_search_result()
    
    def previous_search_result(self) -> None:
        """Navigate to previous search result."""
        if not self._search_results:
            return
            
        self._current_search_index = (self._current_search_index - 1) % len(self._search_results)
        self._highlight_current_search_result()
    
    def _show_error(self, message: str) -> None:
        """Display error message to user."""
        if self._status_label:
            self._status_label.config(text=f"Error: {message}", fg="red")
    
    def _update_status_bar(self) -> None:
        """Update status bar with current document information."""
        if not self._status_label:
            return
            
        if self._current_document:
            status_text = self._current_document.display_info
            if self._search_results:
                current_idx = self._current_search_index + 1 if self._current_search_index >= 0 else 0
                status_text += f" | Search: {current_idx}/{len(self._search_results)}"
            
            self._status_label.config(text=status_text, fg="black")
        else:
            self._status_label.config(text="No document loaded", fg="gray")
    
    def _create_ui(self) -> None:
        """Alias for create_ui method expected by tests."""
        self.create_ui()