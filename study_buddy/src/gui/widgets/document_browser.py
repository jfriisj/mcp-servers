"""
Document Browser Widget for Study Buddy GUI Application.

This module implements DocumentBrowserWidget, the first concrete widget extending
our BaseWidget foundation. Provides document listing, search, filtering, and 
selection capabilities with MCP integration.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: BaseWidget (Layer 1), EventBus (Layer 2), MCP Client (Layer 3)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Import base widget system
from ..widgets.base_widget import (
    BaseWidget, 
    WidgetState, 
    LayoutConstraints, 
    AccessibilityOptions
)
from ..events import EventBus, GlobalEvent

# Import database adapter for direct access
try:
    from ..database_adapter import get_database_adapter
    DATABASE_ADAPTER_AVAILABLE = True
except ImportError:
    DATABASE_ADAPTER_AVAILABLE = False


@dataclass
class DocumentItem:
    """
    Document metadata for display in browser.
    
    Represents a document with all necessary information for UI display
    and user operations. Follows single responsibility principle.
    """
    id: int
    title: str
    file_path: str
    file_type: str  # "pdf", "docx", "pptx", "md"
    file_size: int  # bytes
    upload_date: datetime
    total_pages: Optional[int] = None
    total_words: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    indexed: bool = False
    summarized: bool = False
    notes: str = ""

    @property
    def display_title(self) -> str:
        """Get display-friendly title."""
        return self.title or Path(self.file_path).stem

    @property
    def file_size_display(self) -> str:
        """Get human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size // 1024} KB"
        else:
            return f"{self.file_size // (1024 * 1024)} MB"

    @property
    def status_display(self) -> str:
        """Get document processing status."""
        statuses = []
        if self.indexed:
            statuses.append("Indexed")
        if self.summarized:
            statuses.append("Summarized")
        return ", ".join(statuses) if statuses else "Not processed"


class DocumentBrowserWidget(BaseWidget):
    """
    Document browser widget with search, filter, and selection capabilities.
    
    First concrete implementation of BaseWidget, demonstrating:
    - Proper inheritance and abstract method implementation
    - MCP integration for document operations
    - Event-driven communication with other components
    - Responsive layout and accessibility features
    - Search and filtering functionality
    
    Follows SOLID principles:
    - SRP: Only handles document browsing UI functionality
    - OCP: Extensible for new view modes without modification
    - LSP: Can substitute BaseWidget in any context
    - ISP: Only depends on necessary BaseWidget interface
    - DIP: Depends on EventBus and MCP client abstractions
    """

    def __init__(
        self,
        parent: tk.Widget,
        event_bus: EventBus,
        widget_id: str,
        mcp_client: Optional[Any] = None,
        constraints: Optional[LayoutConstraints] = None,
        accessibility: Optional[AccessibilityOptions] = None
    ):
        """
        Initialize document browser widget.
        
        Args:
            parent: Parent tkinter widget
            event_bus: Global event bus for communication
            widget_id: Unique identifier for this widget instance
            mcp_client: MCP client for document operations (optional for testing)
            constraints: Layout constraints for responsive design
            accessibility: Accessibility options
        """
        # Initialize attributes BEFORE calling super().__init__()
        # because BaseWidget constructor will call create_ui()
        
        # MCP integration
        self.mcp_client = mcp_client
        
        # Document data management
        self._documents: List[DocumentItem] = []
        self._filtered_documents: List[DocumentItem] = []
        self._selected_document: Optional[DocumentItem] = None
        
        # UI state
        self._search_query: str = ""
        self._file_type_filter: str = "All"
        self._sort_column: str = "title"
        self._sort_reverse: bool = False
        
        # UI components (will be created in create_ui)
        self._search_frame: Optional[ttk.Frame] = None
        self._search_entry: Optional[tk.Entry] = None
        self._filter_combo: Optional[ttk.Combobox] = None
        self._refresh_button: Optional[ttk.Button] = None
        self._document_tree: Optional[ttk.Treeview] = None
        self._scrollbar: Optional[ttk.Scrollbar] = None
        self._status_frame: Optional[ttk.Frame] = None
        self._status_label: Optional[tk.Label] = None
        self._context_menu: Optional[tk.Menu] = None
        
        # Mapping for tree item to document ID
        self._item_to_doc_id: Dict[str, int] = {}
        
        # NOW call parent constructor (which will call create_ui)
        super().__init__(parent, event_bus, widget_id, constraints, accessibility)

    def create_ui(self) -> None:
        """
        Create the document browser UI components.
        
        Implements the abstract method from BaseWidget.
        Creates a comprehensive document browser interface with:
        - Search and filter controls
        - Document list with sortable columns
        - Status bar with document count
        - Context menu for operations
        """
        if not self.root_frame:
            self._logger.error("Cannot create UI: root_frame is None")
            return

        try:
            # Create main layout
            self._create_search_controls()
            self._create_document_list()
            self._create_status_bar()
            self._create_context_menu()
            
            # Apply accessibility features
            self._setup_accessibility()
            
            # Load initial documents
            self._load_initial_documents()
            
            self._logger.info(f"Document browser UI created successfully: {self.widget_id}")

        except Exception as e:
            self._logger.error(f"Failed to create document browser UI: {e}", exc_info=True)
            self.state = WidgetState.ERROR
            self._last_error = e

    def _load_initial_documents(self) -> None:
        """Load initial set of documents."""
        # Try to load documents from database adapter or MCP client
        if DATABASE_ADAPTER_AVAILABLE:
            try:
                db_adapter = get_database_adapter()
                docs_result = db_adapter.list_documents(limit=100)
                
                documents = []
                for doc_data in docs_result.get('documents', []):
                    # Convert database result to DocumentItem
                    doc_item = DocumentItem(
                        id=doc_data['document_id'],
                        title=doc_data['title'],
                        file_path=doc_data.get('file_path', ''),
                        file_type=doc_data['file_type'],
                        file_size=0,  # Not stored in current schema
                        upload_date=datetime.fromisoformat(doc_data['upload_date'].replace('Z', '+00:00')) if doc_data.get('upload_date') else datetime.now(),
                        total_pages=doc_data.get('total_pages'),
                        total_words=doc_data.get('total_words'),
                        tags=doc_data.get('tags', []),
                        indexed=doc_data.get('indexed', False),
                        summarized=doc_data.get('summarized', False),
                        notes=""
                    )
                    documents.append(doc_item)
                
                self._documents = documents
                self._logger.info(f"Loaded {len(documents)} documents from database adapter")
                
            except Exception as e:
                self._logger.warning(f"Failed to load documents from database: {e}")
                self._documents = []
        
        else:
            # No database adapter available - start with empty list
            # In production, documents should be loaded from MCP server or database
            self._documents = []
        
        self._filter_and_display_documents()

    def _create_search_controls(self) -> None:
        """Create search and filter control panel."""
        # Search and filter frame
        self._search_frame = ttk.Frame(self.root_frame)
        self._search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search label and entry
        search_label = ttk.Label(self._search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self._search_entry = tk.Entry(self._search_frame, width=30)
        self._search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self._search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        # Filter label and combobox
        filter_label = ttk.Label(self._search_frame, text="Filter:")
        filter_label.pack(side=tk.LEFT, padx=(10, 5))
        
        filter_options = ["All", "PDF", "DOCX", "PPTX", "Markdown"]
        self._filter_combo = ttk.Combobox(
            self._search_frame, 
            values=filter_options, 
            state="readonly",
            width=15
        )
        self._filter_combo.set("All")
        self._filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self._filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Refresh button
        self._refresh_button = ttk.Button(
            self._search_frame,
            text="Refresh",
            command=self._refresh_documents
        )
        self._refresh_button.pack(side=tk.RIGHT, padx=(10, 0))

    def _create_document_list(self) -> None:
        """Create the main document list with columns."""
        # Frame for treeview and scrollbar
        list_frame = ttk.Frame(self.root_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Define columns
        columns = ("title", "type", "size", "date", "status", "tags")
        
        # Create treeview
        self._document_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure column headings and sorting
        column_config = {
            "title": ("Document Title", 300, tk.W),
            "type": ("Type", 80, tk.CENTER), 
            "size": ("Size", 80, tk.E),
            "date": ("Upload Date", 120, tk.CENTER),
            "status": ("Status", 120, tk.CENTER),
            "tags": ("Tags", 150, tk.W)
        }
        
        for col_id, (heading, width, anchor) in column_config.items():
            self._document_tree.heading(
                col_id, 
                text=heading,
                command=lambda c=col_id: self._sort_documents(c)
            )
            self._document_tree.column(col_id, width=width, anchor=anchor)  # type: ignore
        
        # Bind selection events
        self._document_tree.bind('<<TreeviewSelect>>', self._on_document_selected)
        self._document_tree.bind('<Double-1>', self._on_document_double_clicked)
        self._document_tree.bind('<Button-3>', self._on_document_right_clicked)
        
        # Add scrollbar
        self._scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._document_tree.yview)
        self._document_tree.configure(yscrollcommand=self._scrollbar.set)
        
        # Pack components
        self._document_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_status_bar(self) -> None:
        """Create status bar showing document count and other info."""
        self._status_frame = ttk.Frame(self.root_frame)
        self._status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self._status_label = tk.Label(
            self._status_frame,
            text="No documents loaded",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=5
        )
        self._status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_context_menu(self) -> None:
        """Create context menu for document operations."""
        self._context_menu = tk.Menu(self.root_frame, tearoff=0)
        self._context_menu.add_command(label="Open Document", command=self._open_selected_document)
        self._context_menu.add_command(label="View Details", command=self._view_document_details)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Index Document", command=self._index_selected_document)
        self._context_menu.add_command(label="Generate Summary", command=self._summarize_selected_document)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Delete Document", command=self._delete_selected_document)

    def _setup_accessibility(self) -> None:
        """Setup accessibility features for keyboard navigation."""
        # Check if UI components exist before setting up accessibility
        if hasattr(self, '_search_entry') and self._search_entry:
            # Add keyboard shortcuts
            self._search_entry.bind('<Return>', lambda e: self._search_entry.focus_set() if self._search_entry else None)
            
        if hasattr(self, '_document_tree') and self._document_tree:
            # Keyboard navigation
            self._document_tree.bind('<Return>', self._on_document_double_clicked)
            self._document_tree.bind('<Menu>', self._on_document_right_clicked)
            
            # Screen reader support
            if self.accessibility.screen_reader_label:
                # Would set aria-label equivalent for screen readers
                pass

    def _setup_event_handlers(self) -> None:
        """
        Setup event subscriptions for document-related events.
        
        Overrides BaseWidget method to add document-specific event handling.
        """
        # Call parent to setup base event handlers
        super()._setup_event_handlers()
        
        # Subscribe to document events for real-time updates
        self._subscribe_event('document.uploaded', self._on_document_uploaded)
        self._subscribe_event('document.deleted', self._on_document_deleted) 
        self._subscribe_event('document.updated', self._on_document_updated)
        self._subscribe_event('document.indexed', self._on_document_indexed)
        self._subscribe_event('document.summarized', self._on_document_summarized)

    # Event handlers for document operations
    def _on_search_changed(self, event) -> None:
        """Handle search query changes with real-time filtering."""
        if self._search_entry:
            self._search_query = self._search_entry.get().strip().lower()
            self._filter_and_display_documents()

    def _on_filter_changed(self, event) -> None:
        """Handle file type filter changes."""
        if self._filter_combo:
            self._file_type_filter = self._filter_combo.get()
            self._filter_and_display_documents()

    def _on_document_selected(self, event) -> None:
        """Handle document selection in the tree view."""
        if not self._document_tree:
            return
            
        selection = self._document_tree.selection()
        if selection:
            item_id = selection[0]
            # Get document from item data
            self._selected_document = self._get_document_by_tree_item(item_id)
            
            if self._selected_document:
                # Publish selection event for other components
                self._publish_event('document.selected', {
                    'document_id': self._selected_document.id,
                    'title': self._selected_document.title,
                    'file_type': self._selected_document.file_type,
                    'file_path': self._selected_document.file_path
                })
                
                self._logger.debug(f"Document selected: {self._selected_document.title}")

    def _on_document_double_clicked(self, event) -> None:
        """Handle double-click to open document."""
        if self._selected_document:
            self._open_selected_document()

    def _on_document_right_clicked(self, event) -> None:
        """Handle right-click to show context menu."""
        if self._document_tree and self._context_menu:
            # Select item under cursor
            item = self._document_tree.identify_row(event.y)
            if item:
                self._document_tree.selection_set(item)
                self._on_document_selected(event)  # Update selection
                
                # Show context menu
                try:
                    self._context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self._context_menu.grab_release()

    def _refresh_documents(self) -> None:
        """Refresh document list from MCP server."""
        self._load_initial_documents()  # Use the same logic as initial load

    # Document data management methods will be continued in the next part...
    
    def _load_documents_async(self) -> None:
        """Load documents from MCP server asynchronously."""
        # This would implement async MCP call
        # For now, we'll add placeholder implementation
        self._logger.info("Loading documents from MCP server...")
        # TODO: Implement actual MCP integration
        self._update_status("Loading documents...")

    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        if self._status_label:
            self._status_label.config(text=message)

    def _sort_documents(self, column: str) -> None:
        """Sort documents by the specified column."""
        if column == self._sort_column:
            # Toggle sort direction if same column
            self._sort_reverse = not self._sort_reverse
        else:
            # New column, default to ascending
            self._sort_column = column
            self._sort_reverse = False
        
        self._filter_and_display_documents()

    def _filter_and_display_documents(self) -> None:
        """Apply search and filter criteria and update the display."""
        # Start with all documents
        filtered = self._documents.copy()
        
        # Apply search filter
        if self._search_query:
            filtered = [doc for doc in filtered 
                       if self._search_query in doc.display_title.lower() 
                       or self._search_query in ' '.join(doc.tags).lower()]
        
        # Apply file type filter
        if self._file_type_filter != "All":
            file_type_map = {
                "PDF": "pdf",
                "DOCX": "docx", 
                "PPTX": "pptx",
                "Markdown": "md"
            }
            target_type = file_type_map.get(self._file_type_filter)
            if target_type:
                filtered = [doc for doc in filtered if doc.file_type == target_type]
        
        # Apply sorting
        sort_key_map = {
            "title": lambda d: d.display_title.lower(),
            "type": lambda d: d.file_type,
            "size": lambda d: d.file_size,
            "date": lambda d: d.upload_date,
            "status": lambda d: d.status_display,
            "tags": lambda d: ' '.join(d.tags).lower()
        }
        
        if self._sort_column in sort_key_map:
            filtered.sort(key=sort_key_map[self._sort_column], reverse=self._sort_reverse)
        
        # Store filtered results
        self._filtered_documents = filtered
        
        # Update display
        self._populate_document_tree()
        self._update_status_count()

    def _populate_document_tree(self) -> None:
        """Populate the treeview with filtered documents."""
        if not self._document_tree:
            return
            
        # Clear existing items
        for item in self._document_tree.get_children():
            self._document_tree.delete(item)
        
        # Add filtered documents
        for doc in self._filtered_documents:
            item_id = self._document_tree.insert("", "end", values=(
                doc.display_title,
                doc.file_type.upper(),
                doc.file_size_display,
                doc.upload_date.strftime("%Y-%m-%d"),
                doc.status_display,
                ', '.join(doc.tags[:3])  # Show first 3 tags
            ))
            # Store document ID using item mapping (avoid #0 column issue)
            if not hasattr(self, '_item_to_doc_id'):
                self._item_to_doc_id = {}
            self._item_to_doc_id[item_id] = doc.id

    def _update_status_count(self) -> None:
        """Update status bar with document count."""
        total = len(self._documents)
        filtered = len(self._filtered_documents)
        
        if total == 0:
            message = "No documents loaded"
        elif total == filtered:
            message = f"Showing {total} document{'s' if total != 1 else ''}"
        else:
            message = f"Showing {filtered} of {total} documents"
            
        self._update_status(message)

    def _get_document_by_tree_item(self, item_id: str) -> Optional[DocumentItem]:
        """Get document object from treeview item."""
        if not self._document_tree:
            return None
            
        try:
            # Get document ID from item mapping
            if not hasattr(self, '_item_to_doc_id') or item_id not in self._item_to_doc_id:
                return None
            doc_id = self._item_to_doc_id[item_id]
            
            # Find document in filtered list
            for doc in self._filtered_documents:
                if doc.id == doc_id:
                    return doc
        except (ValueError, tk.TclError):
            pass
        
        return None

    # Document operation methods
    def _open_selected_document(self) -> None:
        """Open the selected document."""
        if self._selected_document:
            # Publish document open event
            self._publish_event('document.opened', {
                'document_id': self._selected_document.id,
                'title': self._selected_document.title,
                'file_path': self._selected_document.file_path
            })
            
            self._logger.info(f"Opening document: {self._selected_document.title}")

    def _view_document_details(self) -> None:
        """Show detailed information about the selected document."""
        if self._selected_document:
            # Show document details dialog
            details = (
                f"Title: {self._selected_document.title}\n"
                f"Type: {self._selected_document.file_type.upper()}\n" 
                f"Size: {self._selected_document.file_size_display}\n"
                f"Upload Date: {self._selected_document.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Pages: {self._selected_document.total_pages or 'Unknown'}\n"
                f"Words: {self._selected_document.total_words or 'Unknown'}\n"
                f"Status: {self._selected_document.status_display}\n"
                f"Tags: {', '.join(self._selected_document.tags) or 'None'}\n"
                f"Notes: {self._selected_document.notes or 'None'}"
            )
            
            messagebox.showinfo("Document Details", details)

    def _index_selected_document(self) -> None:
        """Request indexing of the selected document."""
        if self._selected_document:
            # Publish index request event
            self._publish_event('document.index_requested', {
                'document_id': self._selected_document.id,
                'title': self._selected_document.title
            })
            
            messagebox.showinfo("Index Request", 
                              f"Indexing requested for: {self._selected_document.title}")

    def _summarize_selected_document(self) -> None:
        """Request summarization of the selected document."""
        if self._selected_document:
            # Publish summarize request event
            self._publish_event('document.summarize_requested', {
                'document_id': self._selected_document.id, 
                'title': self._selected_document.title
            })
            
            messagebox.showinfo("Summary Request",
                              f"Summarization requested for: {self._selected_document.title}")

    def _delete_selected_document(self) -> None:
        """Delete the selected document after confirmation."""
        if self._selected_document:
            # Confirm deletion
            response = messagebox.askyesno(
                "Delete Document",
                f"Are you sure you want to delete '{self._selected_document.title}'?\n\n"
                "This action cannot be undone."
            )
            
            if response:
                # Publish delete request event
                self._publish_event('document.delete_requested', {
                    'document_id': self._selected_document.id,
                    'title': self._selected_document.title
                })

    # Event handlers for document lifecycle events
    def _on_document_uploaded(self, event: GlobalEvent) -> None:
        """Handle document uploaded event."""
        self._logger.info(f"Document uploaded: {event.data}")
        # Refresh the document list to include new document
        self._refresh_documents()

    def _on_document_deleted(self, event: GlobalEvent) -> None:
        """Handle document deleted event."""
        doc_id = event.data.get('document_id')
        if doc_id:
            # Remove from local cache
            self._documents = [doc for doc in self._documents if doc.id != doc_id]
            self._filter_and_display_documents()
            
            # Clear selection if deleted document was selected
            if self._selected_document and self._selected_document.id == doc_id:
                self._selected_document = None

    def _on_document_updated(self, event: GlobalEvent) -> None:
        """Handle document updated event."""
        doc_id = event.data.get('document_id')
        if doc_id:
            # Refresh document list to get updated information
            self._refresh_documents()

    def _on_document_indexed(self, event: GlobalEvent) -> None:
        """Handle document indexed event."""
        doc_id = event.data.get('document_id')
        if doc_id:
            # Update document status in local cache
            for doc in self._documents:
                if doc.id == doc_id:
                    doc.indexed = True
                    break
            
            self._filter_and_display_documents()

    def _on_document_summarized(self, event: GlobalEvent) -> None:
        """Handle document summarized event."""
        doc_id = event.data.get('document_id')
        if doc_id:
            # Update document status in local cache  
            for doc in self._documents:
                if doc.id == doc_id:
                    doc.summarized = True
                    break
            
            self._filter_and_display_documents()

    # MCP integration methods (placeholder implementations)
    async def _load_documents_from_mcp(self) -> List[DocumentItem]:
        """Load documents from MCP server or database adapter."""
        # Try database adapter first (direct access when MCP not available)
        if DATABASE_ADAPTER_AVAILABLE:
            try:
                db_adapter = get_database_adapter()
                docs_result = db_adapter.list_documents(limit=100)  # Load more documents
                
                documents = []
                for doc_data in docs_result.get('documents', []):
                    # Convert database result to DocumentItem
                    doc_item = DocumentItem(
                        id=doc_data['document_id'],
                        title=doc_data['title'],
                        file_path=doc_data.get('file_path', ''),
                        file_type=doc_data['file_type'],
                        file_size=0,  # Not stored in current schema
                        upload_date=datetime.fromisoformat(doc_data['upload_date'].replace('Z', '+00:00')) if doc_data.get('upload_date') else datetime.now(),
                        total_pages=doc_data.get('total_pages'),
                        total_words=doc_data.get('total_words'),
                        tags=doc_data.get('tags', []),
                        indexed=doc_data.get('indexed', False),
                        summarized=doc_data.get('summarized', False),
                        notes=""
                    )
                    documents.append(doc_item)
                
                self._logger.info(f"Loaded {len(documents)} documents from database")
                return documents
                
            except Exception as e:
                self._logger.warning(f"Database adapter failed, falling back to MCP: {e}")
        
        # Fallback to MCP client
        if not self.mcp_client:
            self._logger.warning("No MCP client available and database adapter failed")
            return []
        
        try:
            # TODO: Implement actual MCP call when MCP server is available
            # response = await self.mcp_client.call_tool('list_documents')
            # return self._parse_mcp_response(response)
            
            # For now, return empty list - MCP integration not yet implemented
            self._logger.info("MCP document loading not yet implemented")
            return []
            
        except Exception as e:
            self._logger.error(f"Failed to load documents from MCP: {e}")
            return []



    def load_documents(self) -> None:
        """Public method to load documents (for external calls)."""
        self._load_documents_async()

    def get_selected_document(self) -> Optional[DocumentItem]:
        """Get currently selected document."""
        return self._selected_document

    def refresh(self) -> None:
        """Public method to refresh the document list."""
        self._refresh_documents()

    def search(self, query: str) -> None:
        """Public method to set search query."""
        if self._search_entry:
            self._search_entry.delete(0, tk.END)
            self._search_entry.insert(0, query)
            self._search_query = query.lower()
            self._filter_and_display_documents()