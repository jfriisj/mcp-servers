"""
Study Buddy GUI - Prompt Builder Widget (Clean Version)

Intelligent prompt generation widget following Clean Architecture and SOLID principles.
This is the core interface that enables the AI workflow described in the implementation guide.

Architecture: Clean Architecture Layer 1 (External Interface)
Pattern: Strategy Pattern (templates), Factory Pattern (template creation)
SOLID: All principles followed with proper dependency injection
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from ..widgets.base_widget import BaseWidget, WidgetState, LayoutConstraints
from ..events import EventBus, GlobalEvent
from ..mcp_client import AsyncMCPClient
from ..templates.base_template import (
    BasePromptTemplate, 
    TemplateContext, 
    PromptStyle, 
    FocusArea
)
from ..templates.template_factory import template_factory
from ..utils.clipboard_manager import ClipboardManager


@dataclass
class DocumentInfo:
    """Information about a document for prompt generation."""
    document_id: int
    title: str
    file_type: str
    indexed: bool = False
    chunks: Optional[List[Dict[str, Any]]] = None


class PromptBuilderWidget(BaseWidget):
    """
    Intelligent Prompt Builder Widget.
    
    Creates AI instructions for document processing following the workflow:
    GUI Selection -> Template Strategy -> Generated Prompt -> Clipboard -> AI Agent
    
    Responsibilities (SRP):
    - Present document/chunk selection interface
    - Generate AI prompts using template strategies
    - Manage clipboard operations with metadata
    - Provide prompt preview and customization
    
    Design Patterns:
    - Strategy Pattern: Template selection and generation
    - Factory Pattern: Template creation
    - Observer Pattern: Event-driven updates
    - Dependency Injection: All dependencies injected via constructor
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        event_bus: EventBus,
        mcp_client: AsyncMCPClient,
        widget_id: str = "prompt_builder",
        constraints: Optional[LayoutConstraints] = None,
        **kwargs
    ):
        """
        Initialize PromptBuilder widget.
        
        Args:
            parent: Parent tkinter widget
            event_bus: Global event bus for communication  
            mcp_client: MCP client for data operations
            widget_id: Unique identifier for this widget
            constraints: Layout constraints
        """
        # Set default constraints for prompt builder
        if constraints is None:
            constraints = LayoutConstraints(
                min_width=800,
                min_height=600,
                preferred_width=1000,
                preferred_height=700
            )
        
        # Initialize BaseWidget with proper parameters
        super().__init__(
            parent=parent,
            event_bus=event_bus,
            widget_id=widget_id,
            constraints=constraints
        )
        
        # Injected dependencies (DIP)
        self.mcp_client = mcp_client
        self.clipboard_manager = ClipboardManager(parent)
        self.template_factory = template_factory
        
        # State management
        self.available_documents: List[DocumentInfo] = []
        self.selected_document: Optional[DocumentInfo] = None
        self.current_template: Optional[BasePromptTemplate] = None
        
        # UI variables
        self.template_var = tk.StringVar(value="summarization")
        self.document_var = tk.StringVar()
        self.chunk_var = tk.StringVar()
        self.style_var = tk.StringVar(value="standard")
        self.focus_vars: Dict[FocusArea, tk.BooleanVar] = {}
        
        # UI components (will be created in create_widgets)
        self.template_combo: Optional[ttk.Combobox] = None
        self.document_combo: Optional[ttk.Combobox] = None
        self.chunk_combo: Optional[ttk.Combobox] = None
        self.preview_text: Optional[scrolledtext.ScrolledText] = None
        self.copy_button: Optional[ttk.Button] = None
        
        # Initialize widget
        self._initialize_widget()
    
    def _initialize_widget(self) -> None:
        """Initialize the widget following BaseWidget lifecycle."""
        try:
            self.set_state(WidgetState.LOADING)
            
            # Create UI
            self.create_widgets()
            
            # Load initial data
            asyncio.create_task(self._load_initial_data())
            
            self.set_state(WidgetState.READY)
            
        except Exception as e:
            self._logger.error(f"Widget initialization failed: {e}", exc_info=True)
            self.show_error(f"Failed to initialize prompt builder: {e}")
            self.set_state(WidgetState.ERROR)
    
    def create_widgets(self) -> None:
        """Create the UI components (required by BaseWidget)."""
        # Main container
        self.root_frame = ttk.Frame(self.parent)
        self.root_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for organization
        notebook = ttk.Notebook(self.root_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Generation tab
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="Generate Prompt")
        self._create_generation_tab(gen_frame)
        
        # History tab  
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="History")
        self._create_history_tab(history_frame)
    
    def _create_generation_tab(self, parent: ttk.Frame) -> None:
        """Create the prompt generation interface."""
        # Template selection
        template_frame = ttk.LabelFrame(parent, text="Template Type")
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(template_frame, text="Template:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var, 
            state="readonly",
            width=40
        )
        self.template_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        template_frame.columnconfigure(1, weight=1)
        
        # Document selection
        doc_frame = ttk.LabelFrame(parent, text="Document & Content")
        doc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(doc_frame, text="Document:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.document_combo = ttk.Combobox(
            doc_frame, 
            textvariable=self.document_var, 
            state="readonly",
            width=40
        )
        self.document_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(doc_frame, text="Chunk:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.chunk_combo = ttk.Combobox(
            doc_frame, 
            textvariable=self.chunk_var, 
            state="readonly",
            width=40
        )
        self.chunk_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        doc_frame.columnconfigure(1, weight=1)
        
        # Style selection
        self._create_style_selection(parent)
        
        # Focus areas  
        self._create_focus_areas(parent)
        
        # Preview area
        preview_frame = ttk.LabelFrame(parent, text="Generated Prompt Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, 
            height=15, 
            width=80, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Generate Prompt",
            command=self._generate_prompt
        ).pack(side=tk.LEFT, padx=5)
        
        self.copy_button = ttk.Button(
            button_frame, 
            text="Copy to Clipboard",
            command=self._copy_to_clipboard,
            state="disabled"
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        # Bind events
        self._bind_events()
    
    def _create_style_selection(self, parent: ttk.Frame) -> None:
        """Create style selection controls."""
        style_frame = ttk.LabelFrame(parent, text="Summary Style")
        style_frame.pack(fill=tk.X, padx=5, pady=5)
        
        styles = [
            ("Brief (100-150 words)", PromptStyle.BRIEF.value),
            ("Standard (250-350 words)", PromptStyle.STANDARD.value),
            ("Detailed (500-750 words)", PromptStyle.DETAILED.value)
        ]
        
        for i, (text, value) in enumerate(styles):
            ttk.Radiobutton(
                style_frame,
                text=text,
                variable=self.style_var,
                value=value
            ).grid(row=i, column=0, sticky="w", padx=5, pady=2)
    
    def _create_focus_areas(self, parent: ttk.Frame) -> None:
        """Create focus area checkboxes."""
        focus_frame = ttk.LabelFrame(parent, text="Focus Areas")
        focus_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize focus area variables
        for focus_area in FocusArea:
            self.focus_vars[focus_area] = tk.BooleanVar()
        
        # Default selections
        self.focus_vars[FocusArea.KEY_CONCEPTS].set(True)
        
        # Create checkboxes in grid
        for i, focus_area in enumerate(FocusArea):
            text = focus_area.value.replace("_", " ").title()
            cb = ttk.Checkbutton(
                focus_frame,
                text=text,
                variable=self.focus_vars[focus_area]
            )
            row = i % 4  # 4 rows
            col = i // 4  # Multiple columns
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
    
    def _create_history_tab(self, parent: ttk.Frame) -> None:
        """Create prompt history interface."""
        ttk.Label(parent, text="Prompt History (Future Feature)").pack(pady=20)
        # TODO: Implement history tracking and display
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        if self.template_combo:
            self.template_combo.bind("<<ComboboxSelected>>", self._on_template_changed)
        if self.document_combo:
            self.document_combo.bind("<<ComboboxSelected>>", self._on_document_changed)
        if self.chunk_combo:
            self.chunk_combo.bind("<<ComboboxSelected>>", self._on_selection_changed)
        
        # Style and focus changes
        self.style_var.trace_add("write", self._on_selection_changed)
        for var in self.focus_vars.values():
            var.trace_add("write", self._on_selection_changed)
    
    async def _load_initial_data(self) -> None:
        """Load initial data from MCP server."""
        try:
            # Load templates
            await self._load_templates()
            
            # Load documents
            await self._load_documents()
            
        except Exception as e:
            self._logger.error(f"Failed to load initial data: {e}", exc_info=True)
            self.show_error(f"Failed to load data: {e}")
    
    async def _load_templates(self) -> None:
        """Load available templates."""
        try:
            templates = self.template_factory.get_available_templates()
            template_names = [t['name'] for t in templates]
            
            if self.template_combo:
                self.template_combo['values'] = template_names
                if template_names:
                    self.template_combo.set(template_names[0])
                    self._on_template_changed()
                    
        except Exception as e:
            self._logger.error(f"Failed to load templates: {e}", exc_info=True)
            raise
    
    async def _load_documents(self) -> None:
        """Load documents from MCP server."""
        try:
            response = await self.mcp_client.call_tool("list_documents")
            
            if hasattr(response, 'data') and response.data.get("success"):
                documents = response.data.get("documents", [])
                
                # Convert to DocumentInfo objects
                self.available_documents = [
                    DocumentInfo(
                        document_id=doc["id"],
                        title=doc["title"],
                        file_type=doc["file_type"],
                        indexed=doc.get("indexed", False)
                    )
                    for doc in documents
                ]
                
                # Update UI
                doc_names = [f"{doc.title} ({doc.file_type.upper()})" for doc in self.available_documents]
                if self.document_combo:
                    self.document_combo['values'] = doc_names
                    if doc_names:
                        self.document_combo.set(doc_names[0])
                        self._on_document_changed()
            
        except Exception as e:
            self._logger.error(f"Failed to load documents: {e}", exc_info=True)
            raise
    
    def _on_template_changed(self, event=None) -> None:
        """Handle template selection change."""
        try:
            template_name = self.template_var.get()
            if template_name:
                self.current_template = self.template_factory.get_template_by_name(template_name)
                self._auto_generate_if_ready()
        except Exception as e:
            self._logger.error(f"Template change error: {e}")
            self.show_error(f"Template error: {e}")
    
    def _on_document_changed(self, event=None) -> None:
        """Handle document selection change."""
        try:
            doc_index = self.document_combo.current() if self.document_combo else -1
            if 0 <= doc_index < len(self.available_documents):
                self.selected_document = self.available_documents[doc_index]
                asyncio.create_task(self._load_chunks_for_document())
        except Exception as e:
            self._logger.error(f"Document change error: {e}")
            self.show_error(f"Document error: {e}")
    
    def _on_selection_changed(self, *args) -> None:
        """Handle any selection change."""
        self._auto_generate_if_ready()
    
    async def _load_chunks_for_document(self) -> None:
        """Load chunks for the selected document."""
        if not self.selected_document:
            return
            
        if not self.selected_document.indexed:
            if self.chunk_combo:
                self.chunk_combo['values'] = ["Document not indexed"]
                self.chunk_combo.set("Document not indexed")
            return
        
        try:
            response = await self.mcp_client.call_tool(
                "get_document_structure",
                {"document_id": self.selected_document.document_id}
            )
            
            if hasattr(response, 'data') and response.data.get("success"):
                chunks = response.data.get("chunks", [])
                self.selected_document.chunks = chunks
                
                if chunks and self.chunk_combo:
                    chunk_names = [f"{chunk['title']} ({chunk['word_count']} words)" for chunk in chunks]
                    self.chunk_combo['values'] = chunk_names
                    self.chunk_combo.set(chunk_names[0])
                    self._auto_generate_if_ready()
                else:
                    self.chunk_combo['values'] = ["No chunks available"]
                    self.chunk_combo.set("No chunks available")
        
        except Exception as e:
            self._logger.error(f"Failed to load chunks: {e}", exc_info=True)
            self.show_error(f"Failed to load chunks: {e}")
    
    def _auto_generate_if_ready(self) -> None:
        """Auto-generate prompt if all required data is available."""
        if self._can_generate_prompt():
            self._generate_prompt()
    
    def _can_generate_prompt(self) -> bool:
        """Check if we have all required data for prompt generation."""
        return (
            self.current_template is not None and
            self.selected_document is not None and
            (
                not hasattr(self.current_template, 'requires_chunk') or
                not self.current_template.requires_chunk or
                self._get_selected_chunk() is not None
            )
        )
    
    def _get_selected_chunk(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected chunk."""
        if not self.selected_document or not self.selected_document.chunks:
            return None
        
        chunk_index = self.chunk_combo.current() if self.chunk_combo else -1
        if 0 <= chunk_index < len(self.selected_document.chunks):
            return self.selected_document.chunks[chunk_index]
        return None
    
    def _generate_prompt(self) -> None:
        """Generate AI prompt using current selections."""
        try:
            if not self._can_generate_prompt():
                return
            
            # Create context
            context = self._create_template_context()
            
            # Generate prompt using template strategy
            prompt = self.current_template.generate_prompt(context)
            
            # Update preview
            if self.preview_text:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, prompt)
            
            # Enable copy button
            if self.copy_button:
                self.copy_button.config(state="normal")
                
        except Exception as e:
            self._logger.error(f"Prompt generation failed: {e}", exc_info=True)
            self.show_error(f"Failed to generate prompt: {e}")
    
    def _create_template_context(self) -> TemplateContext:
        """Create template context from current selections."""
        selected_focus = [
            focus for focus, var in self.focus_vars.items() 
            if var.get()
        ]
        if not selected_focus:
            selected_focus = [FocusArea.KEY_CONCEPTS]
        
        chunk = self._get_selected_chunk()
        
        return TemplateContext(
            document_title=self.selected_document.title,
            document_id=self.selected_document.document_id,
            document_type=self.selected_document.file_type,
            chunk_title=chunk.get("title") if chunk else None,
            chunk_id=chunk.get("chunk_id") if chunk else None,
            chunk_type=chunk.get("chunk_type") if chunk else None,
            style=PromptStyle(self.style_var.get()),
            focus_areas=selected_focus
        )
    
    def _copy_to_clipboard(self) -> None:
        """Copy generated prompt to clipboard."""
        try:
            if not self.preview_text:
                return
                
            prompt_text = self.preview_text.get(1.0, tk.END).strip()
            if not prompt_text:
                messagebox.showwarning("No Content", "No prompt to copy.")
                return
            
            # Create metadata
            metadata = {
                "template": self.current_template.template_name if self.current_template else "Unknown",
                "document": self.selected_document.title if self.selected_document else "None",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Copy to clipboard with metadata
            success = self.clipboard_manager.copy_prompt_with_metadata(
                prompt_text, metadata, show_notification=True
            )
            
            if success:
                self._logger.info("Prompt copied to clipboard successfully")
                # TODO: Add to history
                
        except Exception as e:
            self._logger.error(f"Copy to clipboard failed: {e}", exc_info=True)
            self.show_error(f"Failed to copy prompt: {e}")
    
    # Public interface methods (BaseWidget contract)
    
    def refresh(self) -> None:
        """Refresh widget data."""
        asyncio.create_task(self._load_initial_data())
    
    def clear(self) -> None:
        """Clear widget content."""
        if self.preview_text:
            self.preview_text.delete(1.0, tk.END)
        if self.copy_button:
            self.copy_button.config(state="disabled")
    
    def get_widget_data(self) -> Dict[str, Any]:
        """Get widget data for persistence."""
        return {
            "selected_template": self.template_var.get(),
            "selected_style": self.style_var.get(),
            "focus_areas": {
                focus.value: var.get() 
                for focus, var in self.focus_vars.items()
            }
        }
    
    def set_widget_data(self, data: Dict[str, Any]) -> None:
        """Set widget data from persistence."""
        try:
            if "selected_template" in data:
                self.template_var.set(data["selected_template"])
            if "selected_style" in data:
                self.style_var.set(data["selected_style"])
            if "focus_areas" in data:
                for focus, value in data["focus_areas"].items():
                    focus_area = FocusArea(focus)
                    if focus_area in self.focus_vars:
                        self.focus_vars[focus_area].set(value)
        except Exception as e:
            self._logger.error(f"Failed to set widget data: {e}")