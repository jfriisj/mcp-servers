"""
Search Panel GUI Component for Study Buddy Application.

Provides comprehensive search interface with advanced filtering,
result display, and saved search management. Integrates with
SearchService via MCP client for all search operations.

Enhanced with advanced search capabilities:
- Syntax highlighting for search results
- Intelligent search suggestions with autocomplete
- Persistent search history with analytics
- Rich result rendering with pagination
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date, timedelta
import logging

# Advanced search components
from .advanced_search import (
    SearchHighlighter,
    SearchSuggestionEngine,
    SearchHistoryManager,
    SearchResultRenderer
)


# MCP client placeholder for development
class MCPClient:
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": False, "error": "MCP client not available"}


logger = logging.getLogger(__name__)


class SearchPanel(ttk.Frame):
    """
    Comprehensive search interface for Study Buddy application.
    
    Provides search functionality including:
    - Full-text search across all entity types  
    - Advanced filtering and sorting options
    - Saved search management and quick access
    - Result preview and navigation
    - Real-time search suggestions
    - Pagination support for large result sets
    
    Integrates with SearchService via MCP client using async operations.
    """
    
    def __init__(self, parent, mcp_client: Optional[Any] = None, **kwargs):
        """
        Initialize search panel with GUI components.
        
        Args:
            parent: Parent tkinter widget
            mcp_client: MCP client for service communication
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.mcp_client = mcp_client or MCPClient()
        self.parent = parent
        
        # Search state
        self.current_results: List[Any] = []
        self.current_page = 1
        self.results_per_page = 20
        self.total_results = 0
        self.current_query = None
        self.selected_result_item = None
        
        # GUI state
        self.filters_visible = True
        self.loading = False
        
        # Saved searches cache
        self.saved_searches_cache: List[Any] = []
        self.last_cache_update = None
        
        # Advanced search components
        self.highlighter = SearchHighlighter()
        self.suggestion_engine = SearchSuggestionEngine()
        # Initialize history manager with SQLite storage
        from .advanced_search.search_history import SQLiteHistoryStorage
        import os
        history_db_path = os.path.join(os.path.expanduser("~"), ".study_buddy", "search_history.db")
        history_storage = SQLiteHistoryStorage(history_db_path)
        self.history_manager = SearchHistoryManager(history_storage)
        self.result_renderer = SearchResultRenderer()
        
        # Setup GUI components
        self._setup_styles()
        self._setup_gui()
        self._setup_bindings()
        
        # Load initial data
        self._load_saved_searches()
        
        logger.info("SearchPanel initialized successfully")
    
    def _setup_styles(self) -> None:
        """Configure custom styles for the search panel."""
        style = ttk.Style()
        
        # Search button style
        style.configure(
            "Search.TButton",
            font=("Arial", 10, "bold")
        )
        
        # Filter section style
        style.configure(
            "Filter.TLabelframe",
            padding=5
        )
        
        # Results treeview style  
        style.configure(
            "Results.Treeview",
            rowheight=25
        )
        
        style.configure(
            "Results.Treeview.Heading",
            font=("Arial", 9, "bold")
        )
    
    def _setup_gui(self) -> None:
        """Setup the complete GUI layout."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Results area gets most space
        
        # Create main sections
        self._setup_search_input()      # Row 0
        self._setup_filters_panel()     # Row 1  
        self._setup_results_area()      # Row 2
        self._setup_status_bar()        # Row 3
    
    def _setup_search_input(self) -> None:
        """Setup search input and controls section."""
        input_frame = ttk.Frame(self)
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Saved searches dropdown
        ttk.Label(input_frame, text="Quick Search:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.saved_searches_var = tk.StringVar(value="Select saved search...")
        self.saved_searches_combo = ttk.Combobox(
            input_frame,
            textvariable=self.saved_searches_var,
            state="readonly",
            width=25
        )
        self.saved_searches_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.saved_searches_combo.bind("<<ComboboxSelected>>", self._on_saved_search_selected)
        
        # New search section
        ttk.Label(input_frame, text="Search:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        
        search_controls = ttk.Frame(input_frame)
        search_controls.grid(row=1, column=1, sticky="ew", pady=(5, 0))
        search_controls.grid_columnconfigure(0, weight=1)
        
        # Search entry with suggestions
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_controls,
            textvariable=self.search_var,
            font=("Arial", 11)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self._on_search_text_change)
        self.search_entry.bind("<Return>", lambda e: self._execute_search())
        
        # Search button
        self.search_button = ttk.Button(
            search_controls,
            text="Search",
            command=self._execute_search,
            style="Search.TButton"
        )
        self.search_button.grid(row=0, column=1, padx=(0, 5))
        
        # Advanced search button
        self.advanced_button = ttk.Button(
            search_controls,
            text="Advanced...",
            command=self._open_advanced_search
        )
        self.advanced_button.grid(row=0, column=2, padx=(0, 5))
        
        # Save search button
        self.save_button = ttk.Button(
            search_controls,
            text="Save",
            command=self._save_current_search,
            state="disabled"
        )
        self.save_button.grid(row=0, column=3)
        
        # Suggestions listbox (initially hidden)
        self.suggestions_frame = ttk.Frame(search_controls)
        
        self.suggestions_listbox = tk.Listbox(
            self.suggestions_frame,
            height=5,
            font=("Arial", 9)
        )
        self.suggestions_listbox.pack(fill="both", expand=True)
        self.suggestions_listbox.bind("<Double-Button-1>", self._on_suggestion_select)
        self.suggestions_listbox.bind("<Return>", self._on_suggestion_select)
        
        # Hide suggestions initially
        self.suggestions_visible = False
    
    def _setup_filters_panel(self) -> None:
        """Setup collapsible filters panel."""
        # Filter toggle button
        filter_header = ttk.Frame(self)
        filter_header.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        self.filter_toggle_btn = ttk.Button(
            filter_header,
            text="▼ Filters",
            command=self._toggle_filters,
            width=15
        )
        self.filter_toggle_btn.pack(side="left")
        
        # Clear filters button
        clear_btn = ttk.Button(
            filter_header,
            text="Clear All",
            command=self._clear_filters
        )
        clear_btn.pack(side="left", padx=(10, 0))
        
        # Filters panel (collapsible)
        self.filters_frame = ttk.LabelFrame(
            self,
            text="Search Filters",
            style="Filter.TLabelframe"
        )
        self.filters_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.filters_frame.grid_columnconfigure(1, weight=1)
        
        # Entity type filters
        entity_frame = ttk.Frame(self.filters_frame)
        entity_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=2)
        
        ttk.Label(entity_frame, text="Entity Types:").pack(side="left", padx=(0, 10))
        
        self.entity_filters = {}
        entity_types = [("Documents", "document"), ("Bookmarks", "bookmark"), 
                       ("Sessions", "session"), ("Goals", "goal")]
        
        for i, (label, value) in enumerate(entity_types):
            var = tk.BooleanVar(value=True)
            self.entity_filters[value] = var
            cb = ttk.Checkbutton(entity_frame, text=label, variable=var)
            cb.pack(side="left", padx=(0, 15))
        
        # Date range filters
        date_frame = ttk.Frame(self.filters_frame)
        date_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(date_frame, text="Date Range:").pack(side="left", padx=(0, 10))
        
        ttk.Label(date_frame, text="From:").pack(side="left", padx=(0, 5))
        self.date_from_var = tk.StringVar()
        self.date_from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12)
        self.date_from_entry.pack(side="left", padx=(0, 10))
        
        ttk.Label(date_frame, text="To:").pack(side="left", padx=(0, 5))
        self.date_to_var = tk.StringVar()
        self.date_to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12)
        self.date_to_entry.pack(side="left", padx=(0, 10))
        
        # Helper date buttons
        ttk.Button(date_frame, text="Today", command=self._set_date_today).pack(side="left", padx=2)
        ttk.Button(date_frame, text="Week", command=self._set_date_week).pack(side="left", padx=2)
        ttk.Button(date_frame, text="Month", command=self._set_date_month).pack(side="left", padx=2)
        
        # Results limit
        limit_frame = ttk.Frame(self.filters_frame)
        limit_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=2)
        
        ttk.Label(limit_frame, text="Max Results:").pack(side="left", padx=(0, 10))
        
        self.results_limit_var = tk.IntVar(value=self.results_per_page)
        self.results_limit_scale = ttk.Scale(
            limit_frame,
            from_=10,
            to=100,
            variable=self.results_limit_var,
            orient="horizontal",
            length=200
        )
        self.results_limit_scale.pack(side="left", padx=(0, 10))
        
        self.results_limit_label = ttk.Label(limit_frame, text=str(self.results_per_page))
        self.results_limit_label.pack(side="left")
        
        # Update label when scale changes
        self.results_limit_var.trace("w", self._on_results_limit_change)
    
    def _setup_results_area(self) -> None:
        """Setup results display area with preview pane."""
        results_paned = ttk.PanedWindow(self, orient="horizontal")
        results_paned.grid(row=2, column=0, sticky="nsew", padx=5, pady=2)
        
        # Results list (left pane)
        results_frame = ttk.Frame(results_paned)
        results_paned.add(results_frame, weight=2)
        
        # Results treeview with scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configure treeview columns
        columns = ("title", "type", "relevance", "date")
        self.results_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Results.Treeview"
        )
        
        # Column headers and widths
        self.results_tree.heading("title", text="Title")
        self.results_tree.heading("type", text="Type")
        self.results_tree.heading("relevance", text="Relevance %")
        self.results_tree.heading("date", text="Modified")
        
        self.results_tree.column("title", width=300, anchor="w")
        self.results_tree.column("type", width=80, anchor="center")
        self.results_tree.column("relevance", width=80, anchor="center")
        self.results_tree.column("date", width=100, anchor="center")
        
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars for treeview
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.results_tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.results_tree.configure(xscrollcommand=h_scroll.set)
        
        # Pagination controls
        pagination_frame = ttk.Frame(results_frame)
        pagination_frame.pack(fill="x", pady=(5, 0))
        
        self.prev_button = ttk.Button(
            pagination_frame,
            text="◀ Previous",
            command=self._previous_page,
            state="disabled"
        )
        self.prev_button.pack(side="left")
        
        self.page_label = ttk.Label(pagination_frame, text="Page 1 of 1")
        self.page_label.pack(side="left", padx=10)
        
        self.next_button = ttk.Button(
            pagination_frame,
            text="Next ▶",
            command=self._next_page,
            state="disabled"
        )
        self.next_button.pack(side="left")
        
        # Results count label
        self.results_count_label = ttk.Label(pagination_frame, text="No results")
        self.results_count_label.pack(side="right")
        
        # Preview pane (right pane)
        preview_frame = ttk.LabelFrame(results_paned, text="Preview")
        results_paned.add(preview_frame, weight=1)
        
        # Preview text widget with scrollbar
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        
        self.preview_text = tk.Text(
            preview_container,
            wrap="word",
            font=("Arial", 10),
            state="disabled",
            bg="#f8f8f8"
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        
        preview_scroll = ttk.Scrollbar(
            preview_container,
            orient="vertical",
            command=self.preview_text.yview
        )
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        
        # Preview action buttons
        preview_buttons = ttk.Frame(preview_frame)
        preview_buttons.pack(fill="x", padx=5, pady=(0, 5))
        
        self.open_button = ttk.Button(
            preview_buttons,
            text="Open",
            command=self._open_selected_result,
            state="disabled"
        )
        self.open_button.pack(side="left", padx=(0, 5))
        
        self.bookmark_button = ttk.Button(
            preview_buttons,
            text="Bookmark",
            command=self._bookmark_selected_result,
            state="disabled"
        )
        self.bookmark_button.pack(side="left")
    
    def _setup_status_bar(self) -> None:
        """Setup status bar at bottom."""
        self.status_bar = ttk.Frame(self)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side="left")
        
        # Loading indicator (progress bar)
        self.loading_progress = ttk.Progressbar(
            self.status_bar,
            mode="indeterminate",
            length=100
        )
        # Initially hidden
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        # Result selection
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_selection)
        self.results_tree.bind("<Double-Button-1>", lambda e: self._open_selected_result())
        
        # Keyboard shortcuts
        self.bind_all("<Control-f>", lambda e: self.search_entry.focus())
        self.bind_all("<Control-Shift-F>", lambda e: self._open_advanced_search())
        self.bind_all("<F5>", lambda e: self._refresh_saved_searches())
        
        # Filter change notifications
        for var in self.entity_filters.values():
            var.trace("w", self._on_filter_change)
    
    def _execute_search(self) -> None:
        """Execute search with current parameters."""
        query_text = self.search_var.get().strip()
        
        if not query_text:
            messagebox.showwarning("Search", "Please enter search text")
            return
        
        # Build search query
        search_query = self._build_search_query(query_text)
        
        # Save to search history for analytics
        try:
            search_entry = {
                "query": query_text,
                "filters": search_query.get("filters", {}),
                "timestamp": datetime.now().isoformat()
            }
            self.history_manager.save_search(search_entry)
            
            # Update suggestion engine with the search
            self.suggestion_engine.add_search_term(query_text)
            
        except Exception as e:
            logger.error(f"Error saving search to history: {e}")
        
        # Execute search asynchronously
        asyncio.create_task(self._async_execute_search(search_query))
    
    async def _async_execute_search(self, search_query: Dict[str, Any]) -> None:
        """Execute search asynchronously via MCP client."""
        try:
            self._set_loading(True)
            self._update_status("Searching...")
            
            # Call SearchService via MCP
            result = await self.mcp_client.call_tool(
                "search_service.execute_search",
                search_query
            )
            
            if result.get("success"):
                search_result = result.get("data", {})
                self._display_search_results(search_result)
                
                # Enable save button for successful searches
                self.save_button.configure(state="normal")
                
                result_count = len(search_result.get("items", []))
                self._update_status(f"Found {result_count} results")
            else:
                error_msg = result.get("error", "Search failed")
                messagebox.showerror("Search Error", f"Search failed: {error_msg}")
                self._update_status("Search failed")
                
        except Exception as e:
            logger.error(f"Search execution failed: {str(e)}")
            messagebox.showerror("Search Error", f"Search failed: {str(e)}")
            self._update_status("Search failed")
            
        finally:
            self._set_loading(False)
    
    def _build_search_query(self, query_text: str) -> Dict[str, Any]:
        """Build search query from current GUI state."""
        # Get selected entity types
        entity_types = [
            entity_type for entity_type, var in self.entity_filters.items()
            if var.get()
        ]
        
        # Build query dictionary
        search_query = {
            "query_text": query_text,
            "query_type": "basic",  # Default to basic search
            "entity_type_filters": entity_types,
            "max_results": self.results_limit_var.get(),
            "boost_recent_results": True
        }
        
        # Add date range if specified
        date_from = self.date_from_var.get().strip()
        date_to = self.date_to_var.get().strip()
        
        if date_from or date_to:
            date_range = {}
            if date_from:
                try:
                    date_range["start_date"] = datetime.strptime(date_from, "%Y-%m-%d").isoformat()
                except ValueError:
                    pass  # Ignore invalid dates
            
            if date_to:
                try:
                    date_range["end_date"] = datetime.strptime(date_to, "%Y-%m-%d").isoformat()
                except ValueError:
                    pass  # Ignore invalid dates
            
            if date_range:
                search_query["date_range"] = date_range
        
        return search_query
    
    def _display_search_results(self, search_result: Dict[str, Any]) -> None:
        """Display search results with enhanced rendering and highlighting."""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.current_results = search_result.get("items", [])
        self.total_results = search_result.get("total_results", 0)
        
        # Convert results to SearchResult objects for enhanced renderer
        try:
            from .advanced_search.search_results import SearchResult
            
            search_results = []
            query = self.search_var.get().strip()
            
            for item in self.current_results:
                search_results.append(SearchResult(
                    title=item.get("title", "Untitled"),
                    content=item.get("content", ""),
                    result_type=item.get("entity_type", "unknown"),
                    relevance=item.get("relevance_score", 0.0),
                    metadata={
                        "created_date": item.get("created_date"),
                        "entry_id": item.get("entry_id"),
                        "file_path": item.get("file_path"),
                        "word_count": item.get("word_count", 0)
                    }
                ))
            
            # Use enhanced result renderer if we have a container for rich rendering
            # For now, keep TreeView but enhance the data
            for i, result in enumerate(search_results):
                # Get highlighted title using our highlighter
                highlighted_title = self.highlighter.highlight_text(
                    text=result.title,
                    query=query,
                    content_type="text"
                )
                
                # Format relevance as percentage
                relevance_pct = f"{result.relevance * 100:.1f}%"
                
                # Format date
                created_date = result.metadata.get("created_date")
                if created_date:
                    try:
                        date_obj = datetime.fromisoformat(created_date)
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except:
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"
                
                # Insert into treeview (use original title since TreeView doesn't support rich text)
                self.results_tree.insert(
                    "",
                    "end",
                    values=(
                        result.title,  # Original title
                        result.result_type.title(),
                        relevance_pct,
                        date_str
                    ),
                    tags=(result.metadata.get("entry_id", ""),)
                )
                
        except Exception as e:
            logger.error(f"Error in enhanced result rendering: {e}")
            
            # Fallback to original simple rendering
            for item in self.current_results:
                # Format relevance as percentage
                relevance = item.get("relevance_score", 0)
                relevance_pct = f"{relevance * 100:.1f}%"
                
                # Format date
                created_date = item.get("created_date")
                if created_date:
                    try:
                        date_obj = datetime.fromisoformat(created_date)
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except:
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"
                
                # Insert into treeview
                self.results_tree.insert(
                    "",
                    "end",
                    values=(
                        item.get("title", "Untitled"),
                        item.get("entity_type", "Unknown").title(),
                        relevance_pct,
                        date_str
                    ),
                    tags=(item.get("entry_id", ""),)
                )
        
        # Update pagination controls
        self._update_pagination_controls()
        
        # Update results count
        count_text = f"Showing {len(self.current_results)} of {self.total_results} results"
        self.results_count_label.configure(text=count_text)
        
        # Clear preview pane
        self._clear_preview()
    
    def _on_result_selection(self, event) -> None:
        """Handle result selection in treeview."""
        selection = self.results_tree.selection()
        
        if selection:
            item_id = selection[0]
            item_values = self.results_tree.item(item_id, "values")
            
            if item_values:
                # Find corresponding result item
                title = item_values[0]
                self.selected_result_item = next(
                    (item for item in self.current_results if item.get("title") == title),
                    None
                )
                
                if self.selected_result_item:
                    self._show_result_preview(self.selected_result_item)
                    
                    # Enable action buttons
                    self.open_button.configure(state="normal")
                    self.bookmark_button.configure(state="normal")
        else:
            self.selected_result_item = None
            self._clear_preview()
            
            # Disable action buttons
            self.open_button.configure(state="disabled")
            self.bookmark_button.configure(state="disabled")
    
    def _show_result_preview(self, result_item: Dict[str, Any]) -> None:
        """Show preview of selected result."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete(1.0, "end")
        
        # Build preview content
        preview_lines = []
        
        # Title and type
        title = result_item.get("title", "Untitled")
        entity_type = result_item.get("entity_type", "Unknown").title()
        preview_lines.append(f"Title: {title}")
        preview_lines.append(f"Type: {entity_type}")
        preview_lines.append("")
        
        # Metadata
        metadata = result_item.get("metadata", {})
        if metadata:
            preview_lines.append("Metadata:")
            for key, value in metadata.items():
                preview_lines.append(f"  {key}: {value}")
            preview_lines.append("")
        
        # Content preview
        content_preview = result_item.get("content_preview", "")
        if content_preview:
            preview_lines.append("Content Preview:")
            preview_lines.append(content_preview)
        
        # Insert preview text
        preview_text = "\n".join(preview_lines)
        self.preview_text.insert(1.0, preview_text)
        
        self.preview_text.configure(state="disabled")
    
    def _clear_preview(self) -> None:
        """Clear the preview pane."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete(1.0, "end")
        self.preview_text.insert(1.0, "Select a search result to view preview")
        self.preview_text.configure(state="disabled")
    
    def _open_selected_result(self) -> None:
        """Open the currently selected result."""
        if not self.selected_result_item:
            return
        
        try:
            entity_type = self.selected_result_item.get("entity_type")
            entity_id = self.selected_result_item.get("entity_id")
            
            # Trigger navigation to the selected entity
            # This would integrate with the main application's navigation system
            if hasattr(self.parent, 'navigate_to_entity'):
                self.parent.navigate_to_entity(entity_type, entity_id)
            else:
                # Fallback: show information dialog
                title = self.selected_result_item.get("title", "Unknown")
                messagebox.showinfo(
                    "Open Result",
                    f"Would navigate to {entity_type}: {title} (ID: {entity_id})"
                )
                
        except Exception as e:
            logger.error(f"Failed to open result: {str(e)}")
            messagebox.showerror("Error", f"Failed to open result: {str(e)}")
    
    def _bookmark_selected_result(self) -> None:
        """Create bookmark for selected result."""
        if not self.selected_result_item:
            return
        
        # This would integrate with the bookmark system
        title = self.selected_result_item.get("title", "Unknown")
        messagebox.showinfo(
            "Bookmark Created",
            f"Bookmark created for: {title}"
        )
    
    def _save_current_search(self) -> None:
        """Save current search for later reuse."""
        if not self.search_var.get().strip():
            messagebox.showwarning("Save Search", "No search to save")
            return
        
        # Get search name from user
        search_name = simpledialog.askstring(
            "Save Search",
            "Enter name for this search:",
            initialvalue=f"Search: {self.search_var.get()[:30]}..."
        )
        
        if search_name:
            asyncio.create_task(self._async_save_search(search_name.strip()))
    
    async def _async_save_search(self, search_name: str) -> None:
        """Save search asynchronously."""
        try:
            # Build saved search object
            search_query = self._build_search_query(self.search_var.get())
            
            saved_search = {
                "name": search_name,
                "search_query": search_query,
                "created_date": datetime.now().isoformat()
            }
            
            # Call SearchService to save
            result = await self.mcp_client.call_tool(
                "search_service.save_search",
                saved_search
            )
            
            if result.get("success"):
                messagebox.showinfo("Success", f"Search '{search_name}' saved successfully")
                self._refresh_saved_searches()
            else:
                error_msg = result.get("error", "Failed to save search")
                messagebox.showerror("Save Error", error_msg)
                
        except Exception as e:
            logger.error(f"Failed to save search: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save search: {str(e)}")
    
    def _load_saved_searches(self) -> None:
        """Load saved searches asynchronously."""
        asyncio.create_task(self._async_load_saved_searches())
    
    async def _async_load_saved_searches(self) -> None:
        """Load saved searches from SearchService."""
        try:
            result = await self.mcp_client.call_tool(
                "search_service.get_saved_searches",
                {"sort_by": "last_used_date", "sort_desc": True}
            )
            
            if result.get("success"):
                self.saved_searches_cache = result.get("data", [])
                self._update_saved_searches_combo()
                self.last_cache_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to load saved searches: {str(e)}")
    
    def _update_saved_searches_combo(self) -> None:
        """Update the saved searches combobox."""
        if not self.saved_searches_cache:
            self.saved_searches_combo.configure(values=["No saved searches"])
            return
        
        # Build display values
        values = ["Select saved search..."]
        for search in self.saved_searches_cache:
            name = search.get("name", "Unnamed")
            values.append(name)
        
        self.saved_searches_combo.configure(values=values)
    
    def _on_saved_search_selected(self, event) -> None:
        """Handle saved search selection."""
        selected_name = self.saved_searches_var.get()
        
        if selected_name == "Select saved search..." or selected_name == "No saved searches":
            return
        
        # Find the selected search
        selected_search = next(
            (search for search in self.saved_searches_cache 
             if search.get("name") == selected_name),
            None
        )
        
        if selected_search:
            search_id = selected_search.get("search_id")
            if search_id:
                asyncio.create_task(self._async_execute_saved_search(search_id))
    
    async def _async_execute_saved_search(self, search_id: int) -> None:
        """Execute saved search by ID."""
        try:
            self._set_loading(True)
            self._update_status("Executing saved search...")
            
            result = await self.mcp_client.call_tool(
                "search_service.execute_saved_search",
                {"search_id": search_id}
            )
            
            if result.get("success"):
                search_result = result.get("data", {})
                self._display_search_results(search_result)
                self._update_status(f"Saved search executed: {len(search_result.get('items', []))} results")
            else:
                error_msg = result.get("error", "Failed to execute saved search")
                messagebox.showerror("Search Error", error_msg)
                
        except Exception as e:
            logger.error(f"Failed to execute saved search: {str(e)}")
            messagebox.showerror("Search Error", f"Failed to execute saved search: {str(e)}")
            
        finally:
            self._set_loading(False)
    
    def _refresh_saved_searches(self) -> None:
        """Refresh saved searches cache."""
        self._load_saved_searches()
    
    def _open_advanced_search(self) -> None:
        """Open advanced search dialog."""
        # Placeholder for advanced search dialog
        messagebox.showinfo("Advanced Search", "Advanced search dialog not yet implemented")
    
    def _toggle_filters(self) -> None:
        """Toggle visibility of filters panel."""
        if self.filters_visible:
            self.filters_frame.grid_remove()
            self.filter_toggle_btn.configure(text="▶ Filters")
            self.filters_visible = False
        else:
            self.filters_frame.grid()
            self.filter_toggle_btn.configure(text="▼ Filters")
            self.filters_visible = True
    
    def _clear_filters(self) -> None:
        """Reset all filters to default values."""
        # Reset entity type filters
        for var in self.entity_filters.values():
            var.set(True)
        
        # Clear date range
        self.date_from_var.set("")
        self.date_to_var.set("")
        
        # Reset results limit
        self.results_limit_var.set(20)
    
    def _on_filter_change(self, *args) -> None:
        """Handle filter changes."""
        # Auto-search could be implemented here if desired
        pass
    
    def _on_results_limit_change(self, *args) -> None:
        """Handle results limit scale changes."""
        limit = self.results_limit_var.get()
        self.results_limit_label.configure(text=str(int(limit)))
        self.results_per_page = int(limit)
    
    def _on_search_text_change(self, event) -> None:
        """Handle search text changes for intelligent suggestions."""
        query = self.search_var.get().strip()
        
        if len(query) >= 2:  # Start suggesting after 2 characters
            try:
                # Get intelligent suggestions from our advanced engine
                suggestions = self.suggestion_engine.get_suggestions(
                    query=query,
                    max_suggestions=8
                )
                
                if suggestions:
                    suggestion_texts = [s.text for s in suggestions]
                    self._show_suggestions(suggestion_texts)
                else:
                    self._hide_suggestions()
                    
            except Exception as e:
                logger.error(f"Error getting suggestions: {e}")
                self._hide_suggestions()
        else:
            self._hide_suggestions()
    
    def _on_suggestion_select(self, event) -> None:
        """Handle suggestion selection."""
        if self.suggestions_visible:
            selection = self.suggestions_listbox.curselection()
            if selection:
                suggestion = self.suggestions_listbox.get(selection[0])
                self.search_var.set(suggestion)
                self._hide_suggestions()
                self._execute_search()
    
    def _show_suggestions(self, suggestions: List[str]) -> None:
        """Show search suggestions."""
        if suggestions:
            self.suggestions_listbox.delete(0, "end")
            for suggestion in suggestions:
                self.suggestions_listbox.insert("end", suggestion)
            
            if not self.suggestions_visible:
                self.suggestions_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(2, 0))
                self.suggestions_visible = True
    
    def _hide_suggestions(self) -> None:
        """Hide search suggestions."""
        if self.suggestions_visible:
            self.suggestions_frame.grid_remove()
            self.suggestions_visible = False
    
    def _set_date_today(self) -> None:
        """Set date range to today."""
        today = date.today().strftime("%Y-%m-%d")
        self.date_from_var.set(today)
        self.date_to_var.set(today)
    
    def _set_date_week(self) -> None:
        """Set date range to past week."""
        today = date.today()
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        self.date_from_var.set(week_ago)
        self.date_to_var.set(today_str)
    
    def _set_date_month(self) -> None:
        """Set date range to past month."""
        today = date.today()
        month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        self.date_from_var.set(month_ago)
        self.date_to_var.set(today_str)
    
    def _update_pagination_controls(self) -> None:
        """Update pagination button states."""
        has_results = len(self.current_results) > 0
        
        if has_results:
            total_pages = max(1, (self.total_results + self.results_per_page - 1) // self.results_per_page)
            self.page_label.configure(text=f"Page {self.current_page} of {total_pages}")
            
            # Enable/disable pagination buttons
            self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_button.configure(state="normal" if self.current_page < total_pages else "disabled")
        else:
            self.page_label.configure(text="Page 1 of 1")
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
    
    def _previous_page(self) -> None:
        """Navigate to previous results page."""
        if self.current_page > 1:
            self.current_page -= 1
            # Re-execute search with new page
            # This would need pagination support in SearchService
            self._update_pagination_controls()
    
    def _next_page(self) -> None:
        """Navigate to next results page."""
        total_pages = max(1, (self.total_results + self.results_per_page - 1) // self.results_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            # Re-execute search with new page
            # This would need pagination support in SearchService
            self._update_pagination_controls()
    
    def _set_loading(self, loading: bool) -> None:
        """Set loading state and update UI accordingly."""
        self.loading = loading
        
        if loading:
            self.search_button.configure(state="disabled")
            self.advanced_button.configure(state="disabled")
            self.loading_progress.pack(side="right", padx=(10, 0))
            self.loading_progress.start()
        else:
            self.search_button.configure(state="normal")
            self.advanced_button.configure(state="normal")
            self.loading_progress.stop()
            self.loading_progress.pack_forget()
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_label.configure(text=message)
        self.update_idletasks()