"""
Bookmark Widget for Study Buddy GUI Application.

Provides a comprehensive bookmark management interface with list display,
search/filtering, and bookmark operations. Integrates with the bookmark
manager for coordinated bookmark operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Optional, Dict, Any, Callable, cast
import logging
from datetime import datetime

from gui.widgets.base_widget import BaseWidget


class BookmarkDialog(tk.Toplevel):
    """Dialog for adding/editing bookmarks."""
    
    def __init__(
        self, 
        parent: tk.Widget, 
        bookmark_data: Optional[Dict[str, Any]] = None,
        title: str = "Add Bookmark"
    ):
        super().__init__(parent)
        self.parent = parent
        self.bookmark_data = bookmark_data or {}
        self.result = None
        
        self.title(title)
        self.geometry("400x350")
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        
        self._create_widgets()
        self._populate_fields()
        self._center_on_parent()
        
        # Focus on title entry
        self.title_entry.focus_set()
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        ttk.Label(main_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=2)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        
        # Notes
        ttk.Label(main_frame, text="Notes:").grid(row=1, column=0, sticky="nw", pady=2)
        self.notes_text = tk.Text(main_frame, height=8, width=40, wrap=tk.WORD)
        notes_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scroll.set)
        self.notes_text.grid(row=1, column=1, sticky="ew", pady=2)
        notes_scroll.grid(row=1, column=2, sticky="ns", pady=2)
        
        # Tags
        ttk.Label(main_frame, text="Tags:").grid(row=2, column=0, sticky="w", pady=2)
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk.Entry(main_frame, textvariable=self.tags_var, width=40)
        self.tags_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2)
        ttk.Label(
            main_frame, 
            text="(comma-separated)", 
            font=("TkDefaultFont", 8)
        ).grid(row=3, column=1, sticky="w")
        
        # Color
        ttk.Label(main_frame, text="Color:").grid(row=4, column=0, sticky="w", pady=2)
        self.color_var = tk.StringVar(value="blue")
        color_frame = ttk.Frame(main_frame)
        color_frame.grid(row=4, column=1, columnspan=2, sticky="ew", pady=2)
        
        colors = ["blue", "red", "green", "yellow", "purple", "orange", "gray"]
        for i, color in enumerate(colors):
            ttk.Radiobutton(
                color_frame,
                text=color.title(),
                variable=self.color_var,
                value=color
            ).grid(row=0, column=i, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._ok_clicked
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_clicked
        ).pack(side="right")
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def _populate_fields(self) -> None:
        """Populate fields with existing bookmark data."""
        if self.bookmark_data:
            self.title_var.set(self.bookmark_data.get("title", ""))
            
            notes = self.bookmark_data.get("notes", "")
            if notes:
                self.notes_text.insert("1.0", notes)
            
            tags = self.bookmark_data.get("tags", [])
            if tags:
                self.tags_var.set(", ".join(tags))
            
            color = self.bookmark_data.get("color", "blue")
            self.color_var.set(color)
    
    def _center_on_parent(self) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - self.winfo_width()) // 2
        y = parent_y + (parent_height - self.winfo_height()) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _ok_clicked(self) -> None:
        """Handle OK button click."""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required", parent=self)
            return
        
        # Get notes
        notes = self.notes_text.get("1.0", tk.END).strip()
        notes = notes if notes else None
        
        # Parse tags
        tags_text = self.tags_var.get().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()] if tags_text else []
        
        # Get color
        color = self.color_var.get()
        
        self.result = {
            "title": title,
            "notes": notes,
            "tags": tags,
            "color": color
        }
        
        self.destroy()
    
    def _cancel_clicked(self) -> None:
        """Handle Cancel button click."""
        self.result = None
        self.destroy()


class BookmarkWidget(BaseWidget):
    """
    Widget for displaying and managing bookmarks.
    
    Features:
    - List all bookmarks with filtering and search
    - Add, edit, delete bookmark operations
    - Navigate to bookmarks
    - Export bookmark data
    - Integration with bookmark manager
    """
    
    def __init__(self, parent: tk.Widget, bookmark_manager: Any = None):
        # Create mock event bus for BaseWidget
        class MockEventBus:
            def emit(self, event_name: str, data=None): pass
            def subscribe(self, event_name: str, callback): pass
        
        super().__init__(parent, MockEventBus(), "bookmark_widget")  # type: ignore
        self.bookmark_manager = bookmark_manager
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self._bookmarks_data: List[Any] = []
        self._filtered_bookmarks: List[Any] = []
        
        self._create_widgets()
        self._setup_event_handlers()
        self._load_bookmarks()
    
    def _create_widgets(self) -> None:
        """Create the bookmark widget interface."""
        # Main container
        main_frame = ttk.Frame(cast(tk.Misc, self))
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 5))
        
        # Search
        ttk.Label(toolbar_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side="left", padx=(0, 10))
        
        # Filter by document
        ttk.Label(toolbar_frame, text="Document:").pack(side="left", padx=(5, 5))
        self.document_filter_var = tk.StringVar(value="All Documents")
        self.document_combo = ttk.Combobox(
            toolbar_frame,
            textvariable=self.document_filter_var,
            values=["All Documents", "Current Document"],
            state="readonly",
            width=15
        )
        self.document_combo.pack(side="left", padx=(0, 10))
        self.document_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Buttons
        button_frame = ttk.Frame(toolbar_frame)
        button_frame.pack(side="right")
        
        ttk.Button(
            button_frame,
            text="Add",
            command=self._add_bookmark
        ).pack(side="left", padx=2)
        
        ttk.Button(
            button_frame,
            text="Edit",
            command=self._edit_bookmark
        ).pack(side="left", padx=2)
        
        ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_bookmark
        ).pack(side="left", padx=2)
        
        ttk.Button(
            button_frame,
            text="Export",
            command=self._export_bookmarks
        ).pack(side="left", padx=2)
        
        # Bookmarks list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # Treeview for bookmarks
        columns = ("Title", "Position", "Document", "Tags", "Created", "Accessed")
        self.bookmarks_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Configure columns
        column_configs = {
            "Title": {"width": 200, "minwidth": 150},
            "Position": {"width": 100, "minwidth": 80},
            "Document": {"width": 150, "minwidth": 100},
            "Tags": {"width": 120, "minwidth": 80},
            "Created": {"width": 100, "minwidth": 80},
            "Accessed": {"width": 100, "minwidth": 80}
        }
        
        for col, config in column_configs.items():
            self.bookmarks_tree.heading(col, text=col)
            self.bookmarks_tree.column(col, width=config["width"], minwidth=config["minwidth"])
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bookmarks_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.bookmarks_tree.xview)
        self.bookmarks_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.bookmarks_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click for navigation
        self.bookmarks_tree.bind("<Double-1>", self._on_bookmark_double_click)
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self) -> None:
        """Create context menu for bookmarks."""
        self.context_menu = tk.Menu(cast(tk.Misc, self), tearoff=0)
        self.context_menu.add_command(label="Navigate to Bookmark", command=self._navigate_to_bookmark)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Bookmark", command=self._edit_bookmark)
        self.context_menu.add_command(label="Delete Bookmark", command=self._delete_bookmark)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Title", command=self._copy_bookmark_title)
        
        # Bind right-click
        self.bookmarks_tree.bind("<Button-3>", self._show_context_menu)
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for bookmark manager."""
        if self.bookmark_manager:
            self.bookmark_manager.on_bookmark_created = self._on_bookmark_created
            self.bookmark_manager.on_bookmark_updated = self._on_bookmark_updated
            self.bookmark_manager.on_bookmark_deleted = self._on_bookmark_deleted
    
    def _load_bookmarks(self) -> None:
        """Load bookmarks from bookmark manager."""
        if not self.bookmark_manager:
            return
        
        try:
            # For now, load all bookmarks (could be optimized for large datasets)
            self._bookmarks_data = []  # Would call bookmark_manager.get_all_bookmarks()
            self._apply_filters()
            self._update_display()
        except Exception as e:
            self.logger.error(f"Failed to load bookmarks: {str(e)}")
    
    def _apply_filters(self) -> None:
        """Apply current search and filter criteria."""
        search_text = self.search_var.get().lower()
        document_filter = self.document_filter_var.get()
        
        self._filtered_bookmarks = []
        
        for bookmark in self._bookmarks_data:
            # Apply search filter
            if search_text:
                # Mock search (would use bookmark.matches_search in real implementation)
                title = getattr(bookmark, 'title', str(bookmark)).lower()
                if search_text not in title:
                    continue
            
            # Apply document filter
            if document_filter == "Current Document":
                current_doc_id = getattr(self.bookmark_manager, 'current_document_id', None)
                bookmark_doc_id = getattr(bookmark, 'document_id', None)
                if current_doc_id and bookmark_doc_id != current_doc_id:
                    continue
            
            self._filtered_bookmarks.append(bookmark)
    
    def _update_display(self) -> None:
        """Update the bookmarks tree display."""
        # Clear existing items
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)
        
        # Add filtered bookmarks
        for bookmark in self._filtered_bookmarks:
            # Mock display data (would use bookmark.get_display_info() in real implementation)
            display_data = (
                getattr(bookmark, 'title', 'Unnamed Bookmark'),
                getattr(bookmark, 'position', 'Unknown Position'),
                f"Document {getattr(bookmark, 'document_id', '?')}",
                ", ".join(getattr(bookmark, 'tags', [])),
                getattr(bookmark, 'created_date', datetime.now()).strftime("%Y-%m-%d"),
                getattr(bookmark, 'last_accessed', 'Never')
            )
            
            item_id = self.bookmarks_tree.insert("", "end", values=display_data)
            
            # Store bookmark reference
            self.bookmarks_tree.set(item_id, "#0", getattr(bookmark, 'bookmark_id', 0))
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes."""
        self._apply_filters()
        self._update_display()
    
    def _on_filter_changed(self, event=None) -> None:
        """Handle filter changes."""
        self._apply_filters()
        self._update_display()
    
    def _on_bookmark_double_click(self, event: tk.Event) -> None:
        """Handle double-click on bookmark item."""
        self._navigate_to_bookmark()
    
    def _show_context_menu(self, event: tk.Event) -> None:
        """Show context menu at cursor position."""
        item = self.bookmarks_tree.identify("item", event.x, event.y)
        if item:
            self.bookmarks_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_bookmark_id(self) -> Optional[int]:
        """Get the ID of the currently selected bookmark."""
        selection = self.bookmarks_tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        bookmark_id = self.bookmarks_tree.set(item, "#0")
        
        try:
            return int(bookmark_id) if bookmark_id else None
        except (ValueError, TypeError):
            return None
    
    def _add_bookmark(self) -> None:
        """Show dialog to add new bookmark."""
        dialog = BookmarkDialog(cast(tk.Widget, self), title="Add Bookmark")
        cast(tk.Misc, self).wait_window(dialog)
        
        if dialog.result:
            if self.bookmark_manager:
                result = self.bookmark_manager.create_bookmark_at_current_position(
                    title=dialog.result["title"],
                    notes=dialog.result["notes"],
                    tags=dialog.result["tags"],
                    color=dialog.result["color"]
                )
                
                if result["success"]:
                    messagebox.showinfo("Success", result["message"], parent=cast(tk.Misc, self))
                    self._load_bookmarks()  # Refresh display
                else:
                    messagebox.showerror("Error", result["error"], parent=cast(tk.Misc, self))
    
    def _edit_bookmark(self) -> None:
        """Show dialog to edit selected bookmark."""
        bookmark_id = self._get_selected_bookmark_id()
        if not bookmark_id:
            messagebox.showwarning("No Selection", "Please select a bookmark to edit", parent=cast(tk.Misc, self))
            return
        
        # Get current bookmark data (mock for now)
        current_data = {
            "title": "Sample Bookmark",
            "notes": "Sample notes",
            "tags": ["tag1", "tag2"],
            "color": "blue"
        }
        
        dialog = BookmarkDialog(cast(tk.Widget, self), current_data, "Edit Bookmark")
        cast(tk.Misc, self).wait_window(dialog)
        
        if dialog.result:
            if self.bookmark_manager:
                result = self.bookmark_manager.update_bookmark(
                    bookmark_id=bookmark_id,
                    title=dialog.result["title"],
                    notes=dialog.result["notes"],
                    tags=dialog.result["tags"],
                    color=dialog.result["color"]
                )
                
                if result["success"]:
                    messagebox.showinfo("Success", result["message"], parent=cast(tk.Misc, self))
                    self._load_bookmarks()  # Refresh display
                else:
                    messagebox.showerror("Error", result["error"], parent=cast(tk.Misc, self))
    
    def _delete_bookmark(self) -> None:
        """Delete selected bookmark."""
        bookmark_id = self._get_selected_bookmark_id()
        if not bookmark_id:
            messagebox.showwarning("No Selection", "Please select a bookmark to delete", parent=cast(tk.Misc, self))
            return
        
        response = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this bookmark?",
            parent=cast(tk.Misc, self)
        )
        
        if response and self.bookmark_manager:
            result = self.bookmark_manager.delete_bookmark(bookmark_id)
            
            if result["success"]:
                messagebox.showinfo("Success", result["message"], parent=cast(tk.Misc, self))
                self._load_bookmarks()  # Refresh display
            else:
                messagebox.showerror("Error", result["error"], parent=cast(tk.Misc, self))
    
    def _navigate_to_bookmark(self) -> None:
        """Navigate to selected bookmark."""
        bookmark_id = self._get_selected_bookmark_id()
        if not bookmark_id:
            messagebox.showwarning("No Selection", "Please select a bookmark to navigate to", parent=cast(tk.Misc, self))
            return
        
        if self.bookmark_manager:
            result = self.bookmark_manager.navigate_to_bookmark(bookmark_id)
            
            if not result["success"]:
                messagebox.showerror("Error", result["error"], parent=cast(tk.Misc, self))
    
    def _copy_bookmark_title(self) -> None:
        """Copy selected bookmark title to clipboard."""
        selection = self.bookmarks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        title = self.bookmarks_tree.item(item, "values")[0]
        
        try:
            cast(tk.Misc, self).clipboard_clear()
            cast(tk.Misc, self).clipboard_append(title)
            messagebox.showinfo("Copied", f"Title copied to clipboard: {title}", parent=cast(tk.Misc, self))
        except Exception as e:
            self.logger.error(f"Failed to copy to clipboard: {str(e)}")
    
    def _export_bookmarks(self) -> None:
        """Export bookmarks to file."""
        if not self.bookmark_manager:
            messagebox.showerror("Error", "Bookmark manager not available", parent=cast(tk.Misc, self))
            return
        
        # Simple format selection for now
        format_type = simpledialog.askstring(
            "Export Format",
            "Enter export format (json, csv, txt):",
            initialvalue="json",
            parent=cast(tk.Misc, self)
        )
        
        if format_type:
            current_only = messagebox.askyesno(
                "Export Scope",
                "Export only current document bookmarks?",
                parent=cast(tk.Misc, self)
            )
            
            result = self.bookmark_manager.export_bookmarks(format_type, current_only)
            
            if result["success"]:
                messagebox.showinfo(
                    "Export Complete",
                    f"Bookmarks exported in {format_type} format",
                    parent=cast(tk.Misc, self)
                )
                # In real implementation, would save to file or show save dialog
            else:
                messagebox.showerror("Error", result["error"], parent=cast(tk.Misc, self))
    
    def _on_bookmark_created(self, bookmark: Any) -> None:
        """Handle bookmark creation event."""
        self._load_bookmarks()
    
    def _on_bookmark_updated(self, bookmark: Any) -> None:
        """Handle bookmark update event."""
        self._load_bookmarks()
    
    def _on_bookmark_deleted(self, bookmark_id: int) -> None:
        """Handle bookmark deletion event."""
        self._load_bookmarks()
    
    def refresh_bookmarks(self) -> None:
        """Public method to refresh bookmark display."""
        self._load_bookmarks()
    
    def set_document_filter(self, document_id: Optional[int]) -> None:
        """Set document filter programmatically."""
        if document_id:
            self.document_filter_var.set("Current Document")
        else:
            self.document_filter_var.set("All Documents")
        
        self._on_filter_changed()