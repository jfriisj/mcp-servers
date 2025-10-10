"""
Bookmark Panel Widget for Study Buddy GUI Application.

This module implements BookmarkPanelWidget, providing bookmark management
capabilities including listing, searching, filtering, and bookmark operations
with MCP integration for Task 14 Phase 2.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: BaseWidget (Layer 1), EventBus (Layer 2), MCP Client (Layer 3)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

# Import base widget system
from ..widgets.base_widget import (
    BaseWidget, 
    WidgetState, 
    LayoutConstraints, 
    AccessibilityOptions
)
from ..events import EventBus, GlobalEvent

logger = logging.getLogger(__name__)


@dataclass
class BookmarkItem:
    """
    Bookmark metadata for display in panel.
    
    Represents a bookmark with all necessary information for UI display
    and user operations. Follows single responsibility principle.
    """
    id: int
    title: str
    document_id: int
    chunk_id: Optional[int] = None
    category: str = "General"
    notes: Optional[str] = None
    page_number: Optional[int] = None
    position: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    color: str = "#FFD700"
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Display properties
    document_title: str = ""
    chunk_title: str = ""

    @property
    def display_title(self) -> str:
        """Get display title for bookmark."""
        return self.title[:50] + "..." if len(self.title) > 50 else self.title
    
    @property
    def location_text(self) -> str:
        """Get location description."""
        if self.chunk_id:
            return f"{self.document_title} → {self.chunk_title}"
        else:
            return self.document_title
    
    @property
    def tags_display(self) -> str:
        """Get formatted tags for display."""
        if not self.tags:
            return ""
        return ", ".join(self.tags[:3]) + ("..." if len(self.tags) > 3 else "")


class BookmarkPanelWidget(BaseWidget):
    """
    Bookmark management panel widget.
    
    Provides comprehensive bookmark management interface:
    - List bookmarks with filtering and sorting
    - Search bookmarks by title, notes, tags
    - Create, edit, delete bookmarks
    - Manage categories and favorites
    - Export bookmark collections
    
    Follows Clean Architecture Layer 1 principles:
    - External interface for bookmark management
    - Delegates business logic to MCP backend
    - Event-driven communication with other widgets
    - Framework-agnostic widget structure
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        mcp_client,
        event_bus: EventBus,
        widget_id: str = "bookmark_panel",
        **kwargs
    ):
        """
        Initialize bookmark panel widget.
        
        Args:
            parent: Parent tkinter widget
            mcp_client: MCP client for backend communication
            event_bus: Event system for widget communication
            widget_id: Unique widget identifier
            **kwargs: Additional widget arguments
        """
        super().__init__(
            parent=parent,
            event_bus=event_bus,
            widget_id=widget_id,
            **kwargs
        )
        
        self.mcp_client = mcp_client
        self.event_bus = event_bus
        
        # Widget state
        self.bookmarks: List[BookmarkItem] = []
        self.filtered_bookmarks: List[BookmarkItem] = []
        self.categories: List[str] = []
        self.selected_bookmark: Optional[BookmarkItem] = None
        
        # Filter state
        self.current_filters = {
            "category": "All",
            "document_id": None,
            "is_favorite": None,
            "search_query": ""
        }
        
        # Setup custom styles and event handlers after base widget creation
        self._setup_styles()
        self._setup_bookmark_event_handlers()
        self._load_initial_data()
        
        logger.info(f"BookmarkPanelWidget initialized: {widget_id}")

    def create_ui(self) -> None:
        """Create the widget-specific UI components (BaseWidget requirement)."""
        if not self.root_frame:
            return
        
        # Configure main layout
        self.root_frame.grid_columnconfigure(0, weight=1)
        self.root_frame.grid_rowconfigure(1, weight=1)
        
        # Create widget content
        self._create_widget_content()

    def _setup_styles(self) -> None:
        """Configure custom styles for bookmark panel."""
        style = ttk.Style()
        
        # Bookmark list styles
        style.configure(
            "Bookmark.Treeview",
            rowheight=30,
            font=("Arial", 10)
        )
        
        style.configure(
            "Bookmark.Treeview.Heading",
            font=("Arial", 10, "bold")
        )
        
        # Favorite button style
        style.configure(
            "Favorite.TButton",
            font=("Arial", 8),
            padding=(2, 1)
        )
        
        # Category label style
        style.configure(
            "Category.TLabel",
            font=("Arial", 8, "bold"),
            padding=(2, 1)
        )

    def _create_widget_content(self) -> None:
        """Create the main widget interface."""
        if not self.root_frame:
            return
        self.root_frame.grid_columnconfigure(0, weight=1)
        self.root_frame.grid_rowconfigure(1, weight=1)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        self._create_main_content()
        
        # Create status bar
        self._create_status_bar()

    def _create_toolbar(self) -> None:
        """Create bookmark management toolbar."""
        if not self.root_frame:
            return
        toolbar = ttk.Frame(self.root_frame)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(1, weight=1)
        
        # Left side - actions
        actions_frame = ttk.Frame(toolbar)
        actions_frame.pack(side="left")
        
        # New bookmark button
        self.new_btn = ttk.Button(
            actions_frame,
            text="+ New",
            command=self._create_new_bookmark,
            width=8
        )
        self.new_btn.pack(side="left", padx=(0, 5))
        
        # Edit bookmark button
        self.edit_btn = ttk.Button(
            actions_frame,
            text="Edit",
            command=self._edit_bookmark,
            state="disabled",
            width=8
        )
        self.edit_btn.pack(side="left", padx=(0, 5))
        
        # Delete bookmark button
        self.delete_btn = ttk.Button(
            actions_frame,
            text="Delete",
            command=self._delete_bookmark,
            state="disabled",
            width=8
        )
        self.delete_btn.pack(side="left", padx=(0, 5))
        
        # Separator
        ttk.Separator(actions_frame, orient="vertical").pack(side="left", padx=5, fill="y")
        
        # Export button
        self.export_btn = ttk.Button(
            actions_frame,
            text="Export",
            command=self._export_bookmarks,
            width=8
        )
        self.export_btn.pack(side="left", padx=(0, 5))
        
        # Right side - search and filters
        filters_frame = ttk.Frame(toolbar)
        filters_frame.pack(side="right")
        
        # Search
        ttk.Label(filters_frame, text="Search:").pack(side="left", padx=(0, 2))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            filters_frame,
            textvariable=self.search_var,
            width=20,
            font=("Arial", 10)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        
        # Category filter
        ttk.Label(filters_frame, text="Category:").pack(side="left", padx=(0, 2))
        
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.category_var,
            width=15,
            state="readonly"
        )
        self.category_combo.pack(side="left", padx=(0, 5))
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_filter)
        
        # Favorites filter
        self.favorites_var = tk.BooleanVar()
        self.favorites_cb = ttk.Checkbutton(
            filters_frame,
            text="Favorites only",
            variable=self.favorites_var,
            command=self._on_favorites_filter
        )
        self.favorites_cb.pack(side="left")

    def _create_main_content(self) -> None:
        """Create main bookmark list and details."""
        if not self.root_frame:
            return
        main_frame = ttk.Frame(self.root_frame)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create paned window for list and details
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew")
        
        # Left pane - bookmark list
        list_frame = ttk.LabelFrame(paned, text="Bookmarks", padding=5)
        paned.add(list_frame, weight=2)
        
        self._create_bookmark_list(list_frame)
        
        # Right pane - bookmark details
        details_frame = ttk.LabelFrame(paned, text="Details", padding=5)
        paned.add(details_frame, weight=1)
        
        self._create_bookmark_details(details_frame)

    def _create_bookmark_list(self, parent: tk.Widget) -> None:
        """Create bookmark list with treeview."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview columns
        columns = ("title", "category", "location", "tags", "created")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            style="Bookmark.Treeview",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("#0", text="★", anchor="center")
        self.tree.column("#0", width=30, minwidth=30, stretch=False)
        
        self.tree.heading("title", text="Title", anchor="w")
        self.tree.column("title", width=200, minwidth=150)
        
        self.tree.heading("category", text="Category", anchor="w")
        self.tree.column("category", width=100, minwidth=80)
        
        self.tree.heading("location", text="Location", anchor="w")
        self.tree.column("location", width=250, minwidth=200)
        
        self.tree.heading("tags", text="Tags", anchor="w")
        self.tree.column("tags", width=150, minwidth=100)
        
        self.tree.heading("created", text="Created", anchor="w")
        self.tree.column("created", width=100, minwidth=80)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scroll.set)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_bookmark_select)
        self.tree.bind("<Double-Button-1>", self._on_bookmark_double_click)

    def _create_bookmark_details(self, parent: tk.Widget) -> None:
        """Create bookmark details panel."""
        parent.grid_columnconfigure(0, weight=1)
        
        # Details display
        details_scroll = ttk.Scrollbar(parent, orient="vertical")
        details_scroll.grid(row=0, column=1, sticky="ns")
        
        self.details_text = tk.Text(
            parent,
            wrap="word",
            height=10,
            font=("Arial", 10),
            yscrollcommand=details_scroll.set,
            state="disabled"
        )
        self.details_text.grid(row=0, column=0, sticky="nsew")
        details_scroll.configure(command=self.details_text.yview)
        
        parent.grid_rowconfigure(0, weight=1)

    def _create_status_bar(self) -> None:
        """Create status bar showing bookmark count and filters."""
        if not self.root_frame:
            return
        status_frame = ttk.Frame(self.root_frame)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Arial", 9)
        )
        self.status_label.pack(side="left")
        
        # Refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="↻",
            command=self._refresh_bookmarks,
            width=3
        )
        refresh_btn.pack(side="right")

    def _setup_bookmark_event_handlers(self) -> None:
        """Setup event handlers for widget communication."""
        # Listen for document selection events
        self.event_bus.subscribe(
            "document_selected", 
            self._on_document_selected
        )
        
        # Listen for chunk selection events
        self.event_bus.subscribe(
            "chunk_selected", 
            self._on_chunk_selected
        )

    def _load_initial_data(self) -> None:
        """Load initial bookmark data and categories."""
        asyncio.create_task(self._async_load_data())

    async def _async_load_data(self) -> None:
        """Asynchronously load bookmark data."""
        try:
            # Load categories
            await self._load_categories()
            
            # Load bookmarks
            await self._load_bookmarks()
            
            self._update_status("Ready")
            
        except Exception as e:
            logger.error(f"Failed to load bookmark data: {e}")
            messagebox.showerror("Error", f"Failed to load bookmarks: {str(e)}")

    async def _load_categories(self) -> None:
        """Load bookmark categories from backend."""
        try:
            result = await self.mcp_client.call_tool(
                "get_bookmark_categories", {}
            )
            
            if result.get("success"):
                data = result.get("data", {})
                categories = data.get("categories", [])
                
                # Update category filter
                self.categories = ["All"] + categories
                self.category_combo["values"] = self.categories
                
            else:
                logger.error(f"Failed to load categories: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            # Fallback to default categories
            self.categories = ["All", "General", "Important", "Research", "References"]
            self.category_combo["values"] = self.categories

    async def _load_bookmarks(self) -> None:
        """Load bookmarks from backend."""
        try:
            self._update_status("Loading bookmarks...")
            
            # Build filters for backend call
            filters = {}
            if self.current_filters["category"] != "All":
                filters["category"] = self.current_filters["category"]
            if self.current_filters["document_id"] is not None:
                filters["document_id"] = self.current_filters["document_id"]
            if self.current_filters["is_favorite"] is not None:
                filters["is_favorite"] = self.current_filters["is_favorite"]
            
            # Call appropriate backend method
            if self.current_filters["search_query"]:
                # Use search if query present
                result = await self.mcp_client.call_tool(
                    "search_bookmarks",
                    {
                        "query": self.current_filters["search_query"],
                        **filters
                    }
                )
            else:
                # Use list with filters
                result = await self.mcp_client.call_tool(
                    "list_bookmarks",
                    filters
                )
            
            if result.get("success"):
                data = result.get("data", {})
                bookmark_data = data.get("bookmarks", [])
                
                # Convert to BookmarkItem objects
                self.bookmarks = []
                for bm_data in bookmark_data:
                    bookmark = BookmarkItem(
                        id=bm_data["id"],
                        title=bm_data["title"],
                        document_id=bm_data["document_id"],
                        chunk_id=bm_data.get("chunk_id"),
                        category=bm_data["category"],
                        notes=bm_data.get("notes"),
                        page_number=bm_data.get("page_number"),
                        position=bm_data.get("position"),
                        tags=bm_data.get("tags", []),
                        color=bm_data["color"],
                        is_favorite=bm_data["is_favorite"],
                        created_at=datetime.fromisoformat(bm_data["created_at"]) if bm_data.get("created_at") else None,
                        updated_at=datetime.fromisoformat(bm_data["updated_at"]) if bm_data.get("updated_at") else None,
                        document_title=bm_data.get("document_title", f"Document {bm_data['document_id']}"),
                        chunk_title=bm_data.get("chunk_title", "")
                    )
                    self.bookmarks.append(bookmark)
                
                self._update_bookmark_list()
                
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Failed to load bookmarks: {error_msg}")
                messagebox.showerror("Error", f"Failed to load bookmarks: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error loading bookmarks: {e}")
            messagebox.showerror("Error", f"Failed to load bookmarks: {str(e)}")

    def _update_bookmark_list(self) -> None:
        """Update the bookmark list display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add bookmarks
        for bookmark in self.bookmarks:
            # Determine favorite display
            favorite_icon = "★" if bookmark.is_favorite else ""
            
            # Format created date
            created_str = ""
            if bookmark.created_at:
                created_str = bookmark.created_at.strftime("%Y-%m-%d")
            
            # Insert bookmark
            item_id = self.tree.insert(
                "",
                "end",
                text=favorite_icon,
                values=(
                    bookmark.display_title,
                    bookmark.category,
                    bookmark.location_text,
                    bookmark.tags_display,
                    created_str
                ),
                tags=(f"bookmark_{bookmark.id}",)
            )
            
            # Set row color based on bookmark color (light tint)
            try:
                # Convert hex color to lighter version for row background
                color = bookmark.color
                if color.startswith("#") and len(color) == 7:
                    # Make color lighter for background
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    
                    # Blend with white to make lighter
                    r = int(r + (255 - r) * 0.8)
                    g = int(g + (255 - g) * 0.8)
                    b = int(b + (255 - b) * 0.8)
                    
                    light_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    self.tree.set(item_id, "title", f"⬤ {bookmark.display_title}")
                    
            except ValueError:
                pass  # Use default colors if color parsing fails
        
        # Update status
        count = len(self.bookmarks)
        filter_text = ""
        if self.current_filters["search_query"]:
            filter_text = f" (search: '{self.current_filters['search_query']}')"
        elif self.current_filters["category"] != "All":
            filter_text = f" (category: {self.current_filters['category']})"
        
        self._update_status(f"{count} bookmark{'s' if count != 1 else ''}{filter_text}")

    def _on_bookmark_select(self, event) -> None:
        """Handle bookmark selection."""
        selection = self.tree.selection()
        if not selection:
            self.selected_bookmark = None
            self._update_bookmark_details(None)
            self._update_buttons()
            return
        
        item_id = selection[0]
        bookmark_id = None
        
        # Extract bookmark ID from tags
        for tag in self.tree.item(item_id, "tags"):
            if tag.startswith("bookmark_"):
                bookmark_id = int(tag.replace("bookmark_", ""))
                break
        
        if bookmark_id:
            # Find bookmark
            self.selected_bookmark = next(
                (bm for bm in self.bookmarks if bm.id == bookmark_id),
                None
            )
            
            self._update_bookmark_details(self.selected_bookmark)
            self._update_buttons()

    def _update_bookmark_details(self, bookmark: Optional[BookmarkItem]) -> None:
        """Update bookmark details panel."""
        self.details_text.configure(state="normal")
        self.details_text.delete(1.0, "end")
        
        if bookmark:
            details = f"Title: {bookmark.title}\n\n"
            details += f"Category: {bookmark.category}\n"
            details += f"Location: {bookmark.location_text}\n"
            
            if bookmark.page_number:
                details += f"Page: {bookmark.page_number}\n"
            
            if bookmark.tags:
                details += f"Tags: {', '.join(bookmark.tags)}\n"
            
            details += f"Favorite: {'Yes' if bookmark.is_favorite else 'No'}\n"
            details += f"Color: {bookmark.color}\n"
            
            if bookmark.created_at:
                details += f"Created: {bookmark.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            if bookmark.notes:
                details += f"\nNotes:\n{bookmark.notes}"
            
            self.details_text.insert(1.0, details)
        
        self.details_text.configure(state="disabled")

    def _update_buttons(self) -> None:
        """Update button states based on selection."""
        has_selection = self.selected_bookmark is not None
        
        self.edit_btn.configure(state="normal" if has_selection else "disabled")
        self.delete_btn.configure(state="normal" if has_selection else "disabled")

    def _on_search_change(self, event) -> None:
        """Handle search query change."""
        query = self.search_var.get().strip()
        self.current_filters["search_query"] = query
        
        # Debounced search - could implement timer here
        asyncio.create_task(self._load_bookmarks())

    def _on_category_filter(self, event) -> None:
        """Handle category filter change."""
        category = self.category_var.get()
        self.current_filters["category"] = category
        asyncio.create_task(self._load_bookmarks())

    def _on_favorites_filter(self) -> None:
        """Handle favorites filter change."""
        show_favorites = self.favorites_var.get()
        self.current_filters["is_favorite"] = show_favorites if show_favorites else None
        asyncio.create_task(self._load_bookmarks())

    def _on_bookmark_double_click(self, event) -> None:
        """Handle double-click on bookmark."""
        if self.selected_bookmark:
            # Emit navigation event using _publish_event method
            self._publish_event("bookmark_navigate", {
                "document_id": self.selected_bookmark.document_id,
                "chunk_id": self.selected_bookmark.chunk_id,
                "page_number": self.selected_bookmark.page_number
            })

    def _create_new_bookmark(self) -> None:
        """Create new bookmark."""
        if not self.root_frame:
            return
        
        from ..widgets.bookmark_manager import show_bookmark_dialog
        
        result = show_bookmark_dialog(
            parent=self.root_frame,
            mcp_client=self.mcp_client
        )
        
        if result:
            # Refresh bookmark list after creation
            asyncio.create_task(self._load_bookmarks())

    def _edit_bookmark(self) -> None:
        """Edit selected bookmark."""
        if not self.selected_bookmark or not self.root_frame:
            return
        
        from ..widgets.bookmark_manager import show_bookmark_dialog
        
        result = show_bookmark_dialog(
            parent=self.root_frame,
            mcp_client=self.mcp_client,
            bookmark_id=self.selected_bookmark.id
        )
        
        if result:
            # Refresh bookmark list after editing
            asyncio.create_task(self._load_bookmarks())

    def _delete_bookmark(self) -> None:
        """Delete selected bookmark."""
        if not self.selected_bookmark:
            return
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete bookmark '{self.selected_bookmark.title}'?"
        )
        
        if result:
            asyncio.create_task(self._async_delete_bookmark())

    async def _async_delete_bookmark(self) -> None:
        """Asynchronously delete bookmark."""
        if not self.selected_bookmark:
            return
        
        try:
            self._update_status("Deleting bookmark...")
            
            result = await self.mcp_client.call_tool(
                "delete_bookmark",
                {"bookmark_id": self.selected_bookmark.id}
            )
            
            if result.get("success"):
                messagebox.showinfo("Success", "Bookmark deleted successfully")
                self.selected_bookmark = None
                await self._load_bookmarks()
            else:
                error_msg = result.get("message", "Unknown error")
                messagebox.showerror("Error", f"Failed to delete bookmark: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error deleting bookmark: {e}")
            messagebox.showerror("Error", f"Failed to delete bookmark: {str(e)}")

    def _export_bookmarks(self) -> None:
        """Export bookmarks to file."""
        # This would open export dialog
        # For now, show placeholder message
        messagebox.showinfo("Info", "Export bookmarks not yet implemented")

    def _refresh_bookmarks(self) -> None:
        """Refresh bookmark list."""
        asyncio.create_task(self._load_bookmarks())

    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_label.configure(text=message)
        if self.root_frame:
            self.root_frame.update_idletasks()

    def _on_document_selected(self, event: GlobalEvent) -> None:
        """Handle document selection from other widgets."""
        document_id = event.data.get("document_id")
        if document_id:
            self.current_filters["document_id"] = document_id
            self.current_filters["category"] = "All"
            self.category_var.set("All")
            asyncio.create_task(self._load_bookmarks())

    def _on_chunk_selected(self, event: GlobalEvent) -> None:
        """Handle chunk selection from other widgets."""
        # Could filter by chunk or show chunk bookmarks
        pass

    # Public interface methods
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current widget state.
        
        Returns:
            Dictionary containing widget state
        """
        return {
            "filters": self.current_filters.copy(),
            "selected_bookmark_id": self.selected_bookmark.id if self.selected_bookmark else None,
            "bookmark_count": len(self.bookmarks)
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """
        Restore widget state.
        
        Args:
            state: State dictionary to restore
        """
        if "filters" in state:
            self.current_filters.update(state["filters"])
            
            # Update UI to match filters
            if "category" in state["filters"]:
                self.category_var.set(state["filters"]["category"])
            if "search_query" in state["filters"]:
                self.search_var.set(state["filters"]["search_query"])
            if "is_favorite" in state["filters"]:
                self.favorites_var.set(bool(state["filters"]["is_favorite"]))
        
        asyncio.create_task(self._load_bookmarks())

    def clear_filters(self) -> None:
        """Clear all filters and refresh."""
        self.current_filters = {
            "category": "All",
            "document_id": None,
            "is_favorite": None,
            "search_query": ""
        }
        
        # Update UI
        self.category_var.set("All")
        self.search_var.set("")
        self.favorites_var.set(False)
        
        asyncio.create_task(self._load_bookmarks())

    def filter_by_document(self, document_id: int) -> None:
        """Filter bookmarks by specific document."""
        self.current_filters["document_id"] = document_id
        self.current_filters["category"] = "All"
        self.category_var.set("All")
        asyncio.create_task(self._load_bookmarks())