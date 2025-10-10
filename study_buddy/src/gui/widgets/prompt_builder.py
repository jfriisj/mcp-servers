"""
Study Buddy GUI - Prompt Builder Widget

Intelligent prompt generation widget that creates AI instructions for document processing.
This is the core interface that enables users to generate perfect prompts for AI agents.

Architecture: Clean Architecture Layer 1 (External Interface)
Pattern: Strategy Pattern (templates), Observer Pattern (events), Factory Pattern (template creation)
SOLID: Single Responsibility (prompt generation UI), Dependency Inversion (template abstractions)
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass

from ..widgets.base_widget import BaseWidget, WidgetState
from ..events import EventBus, GlobalEvent
from ..mcp_client import AsyncMCPClient, MCPConnectionError
from ..templates.base_template import (
    BasePromptTemplate, 
    TemplateContext, 
    PromptStyle, 
    FocusArea
)
from ..templates.template_factory import (
    PromptTemplateFactory,
    template_factory
)
from ..utils import ClipboardManager


@dataclass
class DocumentInfo:
    """Information about a document for prompt generation."""
    document_id: int
    title: str
    file_type: str
    indexed: bool = False
    chunks: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []


@dataclass
class PromptHistory:
    """Historical prompt for reuse and favorites."""
    timestamp: datetime
    template_name: str
    document_title: str
    chunk_title: Optional[str]
    style: str
    focus_areas: List[str]
    prompt_content: str
    is_favorite: bool = False


class PromptBuilderWidget(ttk.Frame):
    """
    Intelligent AI Prompt Builder Widget.
    
    Provides a sophisticated interface for generating AI prompts that instruct
    agents to execute MCP tools for document processing. This is the key component
    that enables the AI workflow described in the implementation guide.
    
    Features:
    - Document and chunk selection with real-time updates
    - Template-based prompt generation (Strategy pattern)
    - Style and focus area customization
    - Live prompt preview with syntax highlighting
    - One-click clipboard copy with metadata
    - Prompt history and favorites management
    - Integration with document browser events
    
    Responsibilities:
    - Render prompt generation interface
    - Coordinate template system for prompt creation
    - Handle clipboard operations
    - Manage prompt history and favorites
    - Respond to document/chunk selection events
    
    Does NOT:
    - Execute AI operations (handled by AI agents)
    - Directly access MCP server (uses events and client)
    - Contain prompt templates (delegated to template system)
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        event_bus: EventBus,
        mcp_client: AsyncMCPClient,
        **kwargs
    ):
        """Initialize PromptBuilder widget with dependencies."""
        super().__init__(parent, **kwargs)
        
        # Store dependencies
        self.event_bus = event_bus
        
        self.mcp_client = mcp_client
        self.clipboard_manager = ClipboardManager(parent)
        self.template_factory = template_factory
        self.logger = logging.getLogger(__name__)
        
        # State management
        self.available_documents: List[DocumentInfo] = []
        self.selected_document: Optional[DocumentInfo] = None
        self.selected_chunk: Optional[Dict[str, Any]] = None
        self.current_template: Optional[BasePromptTemplate] = None
        self.prompt_history: List[PromptHistory] = []
        
        # UI components (will be created in _create_widgets)
        self.template_var = tk.StringVar(value="summarization")
        self.document_var = tk.StringVar()
        self.chunk_var = tk.StringVar()
        self.style_var = tk.StringVar(value="standard")
        self.focus_vars: Dict[FocusArea, tk.BooleanVar] = {}
        
        # UI widgets (will be initialized in _create_widgets)
        self.template_combo: Optional[ttk.Combobox] = None
        self.document_combo: Optional[ttk.Combobox] = None
        self.chunk_combo: Optional[ttk.Combobox] = None
        self.style_frame: Optional[ttk.LabelFrame] = None
        self.focus_frame: Optional[ttk.LabelFrame] = None
        self.preview_text: Optional[scrolledtext.ScrolledText] = None
        self.copy_button: Optional[ttk.Button] = None
        self.generate_button: Optional[ttk.Button] = None
        self.history_tree: Optional[ttk.Treeview] = None
        
        # Initialize widget
        self._setup_widget()
    
    def _setup_widget(self) -> None:
        """Initialize the prompt builder interface."""
        try:
            self.set_state(WidgetState.LOADING)
            self._create_widgets()
            self._setup_layout()
            self._bind_events()
            self._initialize_focus_areas()
            self._load_initial_data()
            self.set_state(WidgetState.READY)
            
        except Exception as e:
            self.logger.error(f"Failed to setup PromptBuilder widget: {str(e)}")
            self.set_state(WidgetState.ERROR)
            self.show_error("Widget Setup Error", f"Failed to initialize Prompt Builder: {str(e)}")
    
    def _create_widgets(self) -> None:
        """Create all UI components."""
        # Main container with notebook for organization
        self.notebook = ttk.Notebook(self)
        
        # Tab 1: Prompt Generation
        self.generation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.generation_frame, text="Generate Prompt")
        
        # Tab 2: History & Favorites
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History & Favorites")
        
        # === Generation Tab Components ===
        
        # Template Selection
        template_frame = ttk.LabelFrame(self.generation_frame, text="Template Type")
        ttk.Label(template_frame, text="Prompt Template:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            state="readonly",
            width=40
        )
        self.template_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        template_frame.columnconfigure(1, weight=1)
        
        # Document Selection
        document_frame = ttk.LabelFrame(self.generation_frame, text="Document & Content")
        ttk.Label(document_frame, text="Document:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.document_combo = ttk.Combobox(
            document_frame,
            textvariable=self.document_var,
            state="readonly",
            width=40
        )
        self.document_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(document_frame, text="Chunk/Section:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.chunk_combo = ttk.Combobox(
            document_frame,
            textvariable=self.chunk_var,
            state="readonly",
            width=40
        )
        self.chunk_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        document_frame.columnconfigure(1, weight=1)
        
        # Style Selection
        self.style_frame = ttk.LabelFrame(self.generation_frame, text="Summary Style")
        
        for i, style in enumerate(PromptStyle):
            rb = ttk.Radiobutton(
                self.style_frame,
                text=f"{style.value.title()} ({self._get_style_description(style)})",
                variable=self.style_var,
                value=style.value
            )
            rb.grid(row=i, column=0, sticky="w", padx=5, pady=2)
        
        # Focus Areas
        self.focus_frame = ttk.LabelFrame(self.generation_frame, text="Focus Areas")
        
        # Initialize focus area variables
        for focus_area in FocusArea:
            self.focus_vars[focus_area] = tk.BooleanVar()
        
        # Create checkboxes in two columns
        focus_areas = list(FocusArea)
        for i, focus_area in enumerate(focus_areas):
            cb = ttk.Checkbutton(
                self.focus_frame,
                text=focus_area.value.replace("_", " ").title(),
                variable=self.focus_vars[focus_area]
            )
            row = i % ((len(focus_areas) + 1) // 2)
            col = 0 if i < (len(focus_areas) + 1) // 2 else 1
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        
        # Prompt Preview
        preview_frame = ttk.LabelFrame(self.generation_frame, text="Generated Prompt Preview")
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=15,
            width=80,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Action Buttons
        button_frame = ttk.Frame(self.generation_frame)
        
        self.generate_button = ttk.Button(
            button_frame,
            text="Generate Prompt",
            command=self._generate_prompt
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        self.copy_button = ttk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=self._copy_to_clipboard,
            state="disabled"
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        favorite_button = ttk.Button(
            button_frame,
            text="Add to Favorites",
            command=self._add_to_favorites
        )
        favorite_button.pack(side=tk.LEFT, padx=5)
        
        # === History Tab Components ===
        
        # History tree
        history_columns = ("timestamp", "template", "document", "style")
        self.history_tree = ttk.Treeview(
            self.history_frame,
            columns=history_columns,
            show="tree headings",
            height=10
        )
        
        # Configure columns
        self.history_tree.heading("#0", text="Type")
        self.history_tree.heading("timestamp", text="Time")
        self.history_tree.heading("template", text="Template")
        self.history_tree.heading("document", text="Document")
        self.history_tree.heading("style", text="Style")
        
        self.history_tree.column("#0", width=100)
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("template", width=120)
        self.history_tree.column("document", width=200)
        self.history_tree.column("style", width=100)
        
        # History scrollbar
        history_scroll = ttk.Scrollbar(self.history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        # History buttons
        history_button_frame = ttk.Frame(self.history_frame)
        
        ttk.Button(
            history_button_frame,
            text="Load Selected",
            command=self._load_from_history
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            history_button_frame,
            text="Delete Selected",
            command=self._delete_from_history
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            history_button_frame,
            text="Clear History",
            command=self._clear_history
        ).pack(side=tk.LEFT, padx=5)
    
    def _setup_layout(self) -> None:
        """Arrange all UI components."""
        # Main notebook
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Generation tab layout
        template_frame = self.generation_frame.winfo_children()[0]
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        document_frame = self.generation_frame.winfo_children()[1]
        document_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.style_frame.pack(fill=tk.X, padx=5, pady=5)
        self.focus_frame.pack(fill=tk.X, padx=5, pady=5)
        
        preview_frame = self.generation_frame.winfo_children()[4]
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        button_frame = self.generation_frame.winfo_children()[5]
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # History tab layout
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)
        history_scroll = self.history_frame.winfo_children()[1]
        history_scroll.pack(fill=tk.Y, side=tk.RIGHT, pady=5)
        
        history_button_frame = self.history_frame.winfo_children()[2]
        history_button_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        # Template selection
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_changed)
        
        # Document/chunk selection
        self.document_combo.bind("<<ComboboxSelected>>", self._on_document_changed)
        self.chunk_combo.bind("<<ComboboxSelected>>", self._on_chunk_changed)
        
        # Style and focus changes
        self.style_var.trace_add("write", self._on_settings_changed)
        for focus_var in self.focus_vars.values():
            focus_var.trace_add("write", self._on_settings_changed)
        
        # History selection
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_selected)
        self.history_tree.bind("<Double-1>", lambda e: self._load_from_history())
        
        # Global events
        self.event_bus.subscribe("document_selected", self._on_external_document_selected)
        self.event_bus.subscribe("chunk_selected", self._on_external_chunk_selected)
        self.event_bus.subscribe("documents_updated", self._refresh_document_list)
    
    def _initialize_focus_areas(self) -> None:
        """Set default focus areas."""
        # Default to key concepts
        self.focus_vars[FocusArea.KEY_CONCEPTS].set(True)
    
    def _load_initial_data(self) -> None:
        """Load initial data for dropdowns."""
        # Load templates
        self._load_templates()
        
        # Load documents
        asyncio.create_task(self._load_documents_async())
    
    def _load_templates(self) -> None:
        """Load available templates into dropdown."""
        try:
            templates = self.template_factory.get_available_templates()
            template_names = [f"{t['name']} - {t['description']}" for t in templates]
            self.template_combo['values'] = template_names
            
            if templates:
                self.template_combo.set(template_names[0])  # Select first template
                self._on_template_changed()
                
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            self.show_error("Template Error", f"Failed to load prompt templates: {str(e)}")
    
    async def _load_documents_async(self) -> None:
        """Load available documents from MCP server."""
        try:
            self.set_state(WidgetState.LOADING)
            
            # Get document list
            response = await self.mcp_client.call_tool("list_documents")
            
            if response.get("success"):
                documents_data = response.get("documents", [])
                self.available_documents = [
                    DocumentInfo(
                        document_id=doc["id"],
                        title=doc["title"],
                        file_type=doc["file_type"],
                        indexed=doc.get("indexed", False)
                    )
                    for doc in documents_data
                ]
                
                # Update document dropdown
                doc_names = [f"{doc.title} ({doc.file_type.upper()})" for doc in self.available_documents]
                self.document_combo['values'] = doc_names
                
                if doc_names:
                    self.document_combo.set(doc_names[0])
                    self._on_document_changed()
            
            self.set_state(WidgetState.READY)
            
        except Exception as e:
            self.logger.error(f"Failed to load documents: {str(e)}")
            self.set_state(WidgetState.ERROR)
            self.show_error("Document Loading Error", f"Failed to load documents: {str(e)}")
    
    def _on_template_changed(self, event=None) -> None:
        """Handle template selection change."""
        try:
            template_text = self.template_var.get()
            if not template_text:
                return
            
            # Extract template name (before " - ")
            template_name = template_text.split(" - ")[0]
            self.current_template = self.template_factory.get_template_by_name(template_name)
            
            # Update UI based on template requirements
            self._update_ui_for_template()
            
            # Auto-generate if we have all required data
            self._auto_generate_if_ready()
            
        except Exception as e:
            self.logger.error(f"Template change error: {str(e)}")
            self.show_error("Template Error", f"Failed to change template: {str(e)}")
    
    def _on_document_changed(self, event=None) -> None:
        """Handle document selection change."""
        try:
            doc_text = self.document_var.get()
            if not doc_text:
                return
            
            # Find selected document
            doc_index = self.document_combo.current()
            if 0 <= doc_index < len(self.available_documents):
                self.selected_document = self.available_documents[doc_index]
                
                # Load chunks for this document
                asyncio.create_task(self._load_chunks_async())
            
        except Exception as e:
            self.logger.error(f"Document change error: {str(e)}")
    
    async def _load_chunks_async(self) -> None:
        """Load chunks for selected document."""
        if not self.selected_document or not self.selected_document.indexed:
            self.chunk_combo['values'] = ["Document not indexed"]
            self.chunk_combo.set("Document not indexed")
            return
        
        try:
            # Get document structure
            response = await self.mcp_client.call_tool(
                "get_document_structure", 
                {"document_id": self.selected_document.document_id}
            )
            
            if response.get("success"):
                chunks = response.get("chunks", [])
                self.selected_document.chunks = chunks
                
                # Update chunk dropdown
                if chunks:
                    chunk_names = [f"{chunk['title']} ({chunk['word_count']} words)" for chunk in chunks]
                    self.chunk_combo['values'] = chunk_names
                    self.chunk_combo.set(chunk_names[0])
                    self._on_chunk_changed()
                else:
                    self.chunk_combo['values'] = ["No chunks available"]
                    self.chunk_combo.set("No chunks available")
            
        except Exception as e:
            self.logger.error(f"Failed to load chunks: {str(e)}")
            self.chunk_combo['values'] = ["Error loading chunks"]
            self.chunk_combo.set("Error loading chunks")
    
    def _on_chunk_changed(self, event=None) -> None:
        """Handle chunk selection change."""
        try:
            if not self.selected_document or not self.selected_document.chunks:
                return
            
            chunk_index = self.chunk_combo.current()
            if 0 <= chunk_index < len(self.selected_document.chunks):
                self.selected_chunk = self.selected_document.chunks[chunk_index]
                
                # Auto-generate if ready
                self._auto_generate_if_ready()
            
        except Exception as e:
            self.logger.error(f"Chunk change error: {str(e)}")
    
    def _on_settings_changed(self, *args) -> None:
        """Handle style or focus area changes."""
        # Auto-generate if ready
        self._auto_generate_if_ready()
    
    def _auto_generate_if_ready(self) -> None:
        """Auto-generate prompt if all required data is available."""
        if self._has_required_data():
            self._generate_prompt()
    
    def _has_required_data(self) -> bool:
        """Check if we have all data needed for prompt generation."""
        return (
            self.current_template is not None and
            self.selected_document is not None and
            (
                "chunk_id" not in self.current_template.required_context or
                self.selected_chunk is not None
            )
        )
    
    def _generate_prompt(self) -> None:
        """Generate AI prompt based on current selections."""
        try:
            if not self._has_required_data():
                messagebox.showwarning(
                    "Incomplete Selection", 
                    "Please select template, document, and chunk (if required) before generating prompt."
                )
                return
            
            # Create template context
            context = self._create_template_context()
            
            # Generate prompt
            prompt = self.current_template.generate_prompt(context)
            
            # Update preview
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, prompt)
            
            # Enable copy button
            self.copy_button.config(state="normal")
            
            # Add to history
            self._add_to_prompt_history(context, prompt)
            
        except Exception as e:
            self.logger.error(f"Prompt generation failed: {str(e)}")
            self.show_error("Generation Error", f"Failed to generate prompt: {str(e)}")
    
    def _create_template_context(self) -> TemplateContext:
        """Create TemplateContext from current UI selections."""
        # Get selected focus areas
        selected_focus = [
            focus_area for focus_area, var in self.focus_vars.items()
            if var.get()
        ]
        
        if not selected_focus:
            selected_focus = [FocusArea.KEY_CONCEPTS]  # Default
        
        return TemplateContext(
            document_title=self.selected_document.title,
            document_id=self.selected_document.document_id,
            document_type=self.selected_document.file_type,
            chunk_title=self.selected_chunk.get("title") if self.selected_chunk else None,
            chunk_id=self.selected_chunk.get("chunk_id") if self.selected_chunk else None,
            chunk_type=self.selected_chunk.get("chunk_type") if self.selected_chunk else None,
            style=PromptStyle(self.style_var.get()),
            focus_areas=selected_focus
        )
    
    def _copy_to_clipboard(self) -> None:
        """Copy generated prompt to clipboard."""
        try:
            prompt_text = self.preview_text.get(1.0, tk.END).strip()
            if not prompt_text:
                messagebox.showwarning("No Content", "No prompt to copy.")
                return
            
            # Create metadata for clipboard
            metadata = {
                "template": self.current_template.template_name,
                "document": self.selected_document.title,
                "chunk": self.selected_chunk.get("title") if self.selected_chunk else None,
                "style": self.style_var.get(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Copy with metadata
            success = self.clipboard_manager.copy_prompt_with_metadata(
                prompt_text,
                metadata,
                show_notification=True
            )
            
            if success:
                self.logger.info("Prompt copied to clipboard successfully")
            
        except Exception as e:
            self.logger.error(f"Clipboard copy failed: {str(e)}")
            messagebox.showerror("Copy Error", f"Failed to copy prompt: {str(e)}")
    
    def _add_to_prompt_history(self, context: TemplateContext, prompt: str) -> None:
        """Add generated prompt to history."""
        try:
            history_entry = PromptHistory(
                timestamp=datetime.now(),
                template_name=self.current_template.template_name,
                document_title=context.document_title,
                chunk_title=context.chunk_title,
                style=context.style.value,
                focus_areas=[area.value for area in context.focus_areas],
                prompt_content=prompt
            )
            
            self.prompt_history.insert(0, history_entry)  # Add to beginning
            
            # Limit history size
            if len(self.prompt_history) > 100:
                self.prompt_history = self.prompt_history[:100]
            
            # Update history tree
            self._refresh_history_tree()
            
        except Exception as e:
            self.logger.error(f"Failed to add to history: {str(e)}")
    
    def _refresh_history_tree(self) -> None:
        """Refresh the history tree display."""
        try:
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Add history entries
            for i, entry in enumerate(self.prompt_history):
                item_text = "★ Favorite" if entry.is_favorite else "Recent"
                
                self.history_tree.insert(
                    "",
                    tk.END,
                    text=item_text,
                    values=(
                        entry.timestamp.strftime("%m/%d %H:%M"),
                        entry.template_name,
                        entry.document_title[:30] + "..." if len(entry.document_title) > 30 else entry.document_title,
                        entry.style.title()
                    ),
                    tags=("favorite",) if entry.is_favorite else ()
                )
            
            # Configure tags
            self.history_tree.tag_configure("favorite", background="#fff3cd")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh history tree: {str(e)}")
    
    def _add_to_favorites(self) -> None:
        """Add current prompt to favorites."""
        if not self.prompt_history:
            messagebox.showinfo("No History", "Generate a prompt first to add it to favorites.")
            return
        
        # Mark most recent as favorite
        self.prompt_history[0].is_favorite = True
        self._refresh_history_tree()
        
        messagebox.showinfo("Added to Favorites", "Current prompt added to favorites.")
    
    def _load_from_history(self) -> None:
        """Load selected history entry."""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a history entry to load.")
            return
        
        try:
            # Get selected index
            item = selection[0]
            index = self.history_tree.index(item)
            
            if 0 <= index < len(self.prompt_history):
                entry = self.prompt_history[index]
                
                # Load settings
                # Note: This is a simplified version - full implementation would
                # restore all selections including document/chunk
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, entry.prompt_content)
                self.copy_button.config(state="normal")
                
                messagebox.showinfo("Loaded", f"Loaded prompt from {entry.timestamp.strftime('%m/%d %H:%M')}")
            
        except Exception as e:
            self.logger.error(f"Failed to load from history: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load history entry: {str(e)}")
    
    def _delete_from_history(self) -> None:
        """Delete selected history entry."""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a history entry to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Delete selected history entry?"):
            try:
                item = selection[0]
                index = self.history_tree.index(item)
                
                if 0 <= index < len(self.prompt_history):
                    del self.prompt_history[index]
                    self._refresh_history_tree()
                
            except Exception as e:
                self.logger.error(f"Failed to delete history entry: {str(e)}")
    
    def _clear_history(self) -> None:
        """Clear all history."""
        if messagebox.askyesno("Confirm Clear", "Clear all prompt history? This cannot be undone."):
            self.prompt_history.clear()
            self._refresh_history_tree()
    
    def _on_external_document_selected(self, event: GlobalEvent) -> None:
        """Handle external document selection event."""
        try:
            document_id = event.data.get("document_id")
            if document_id:
                # Find and select document
                for i, doc in enumerate(self.available_documents):
                    if doc.document_id == document_id:
                        self.document_combo.current(i)
                        self._on_document_changed()
                        break
        except Exception as e:
            self.logger.error(f"Error handling external document selection: {str(e)}")
    
    def _on_external_chunk_selected(self, event: GlobalEvent) -> None:
        """Handle external chunk selection event."""
        try:
            chunk_id = event.data.get("chunk_id")
            if chunk_id and self.selected_document and self.selected_document.chunks:
                # Find and select chunk
                for i, chunk in enumerate(self.selected_document.chunks):
                    if chunk.get("chunk_id") == chunk_id:
                        self.chunk_combo.current(i)
                        self._on_chunk_changed()
                        break
        except Exception as e:
            self.logger.error(f"Error handling external chunk selection: {str(e)}")
    
    def _refresh_document_list(self, event: GlobalEvent) -> None:
        """Refresh document list when documents are updated."""
        asyncio.create_task(self._load_documents_async())
    
    def _update_ui_for_template(self) -> None:
        """Update UI visibility based on template requirements."""
        if not self.current_template:
            return
        
        # Show/hide chunk selection based on template requirements
        chunk_required = "chunk_id" in self.current_template.required_context
        chunk_state = "readonly" if chunk_required else "disabled"
        self.chunk_combo.config(state=chunk_state)
    
    def _on_history_selected(self, event) -> None:
        """Handle history tree selection."""
        # Could show preview of selected history entry
        pass
    
    def _get_style_description(self, style: PromptStyle) -> str:
        """Get human-readable description for style."""
        descriptions = {
            PromptStyle.BRIEF: "100-150 words",
            PromptStyle.STANDARD: "250-350 words", 
            PromptStyle.DETAILED: "500-750 words"
        }
        return descriptions.get(style, "Standard length")
    
    # Required BaseWidget method implementations
    
    def refresh_content(self) -> None:
        """Refresh widget content."""
        asyncio.create_task(self._load_documents_async())
    
    def clear_content(self) -> None:
        """Clear widget content."""
        self.preview_text.delete(1.0, tk.END)
        self.copy_button.config(state="disabled")
        self.selected_document = None
        self.selected_chunk = None
    
    def get_selection(self) -> Optional[Dict[str, Any]]:
        """Get current selection state."""
        return {
            "template": self.template_var.get(),
            "document": self.selected_document.document_id if self.selected_document else None,
            "chunk": self.selected_chunk.get("chunk_id") if self.selected_chunk else None,
            "style": self.style_var.get(),
            "focus_areas": [
                area.value for area, var in self.focus_vars.items() if var.get()
            ]
        }
    
    def set_selection(self, selection_data: Dict[str, Any]) -> None:
        """Set selection from external data."""
        # Implementation would restore UI state from selection data
        pass