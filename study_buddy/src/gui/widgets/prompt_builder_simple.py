"""
Study Buddy GUI - Prompt Builder Widget (Simplified)

Intelligent prompt generation widget for AI instructions.
Creates perfect prompts for Copilot Chat based on user selections.

Architecture: Clean Architecture Layer 1 (External Interface)  
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..events import EventBus, GlobalEvent
from ..mcp_client import AsyncMCPClient
from ..templates.base_template import (
    TemplateContext, 
    PromptStyle, 
    FocusArea
)
from ..templates.template_factory import template_factory
from ..utils import ClipboardManager

# Import database adapter for fallback data access
try:
    from ..database_adapter import get_database_adapter
    DATABASE_ADAPTER_AVAILABLE = True
except ImportError:
    DATABASE_ADAPTER_AVAILABLE = False
    get_database_adapter = None

# Import database adapter for fallback when MCP unavailable
try:
    from ..database_adapter import get_database_adapter
    DATABASE_ADAPTER_AVAILABLE = True
except ImportError:
    DATABASE_ADAPTER_AVAILABLE = False
    get_database_adapter = None


class PromptBuilderWidget(ttk.Frame):
    """
    Simplified Prompt Builder Widget for AI prompt generation.
    
    Provides essential functionality:
    - Document and chunk selection
    - Template-based prompt generation  
    - Style and focus area customization
    - Clipboard copy with metadata
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        event_bus: EventBus,
        mcp_client: Optional[AsyncMCPClient] = None,
        **kwargs
    ):
        """Initialize PromptBuilder widget."""
        super().__init__(parent, **kwargs)
        
        # Dependencies
        self.event_bus = event_bus
        self.mcp_client = mcp_client
        self.clipboard_manager = ClipboardManager(parent)
        self.logger = logging.getLogger(__name__)
        
        # State
        self.available_documents = []
        self.selected_document = None
        self.selected_chunk = None
        self.current_template = None
        
        # UI Variables
        self.template_var = tk.StringVar(value="summarization")
        self.document_var = tk.StringVar()
        self.chunk_var = tk.StringVar()
        self.style_var = tk.StringVar(value="standard")
        self.focus_vars = {}
        
        # Initialize
        self._create_ui()
        self._bind_events()
        self._load_initial_data()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Generation tab
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="Generate Prompt")
        
        # Template selection
        template_frame = ttk.LabelFrame(gen_frame, text="Template Type")
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(template_frame, text="Template:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.template_combo = ttk.Combobox(
            template_frame, textvariable=self.template_var, 
            state="readonly", width=40
        )
        self.template_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        template_frame.columnconfigure(1, weight=1)
        
        # Document selection
        doc_frame = ttk.LabelFrame(gen_frame, text="Document & Content")
        doc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(doc_frame, text="Document:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.document_combo = ttk.Combobox(
            doc_frame, textvariable=self.document_var, 
            state="readonly", width=40
        )
        self.document_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(doc_frame, text="Chunk:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.chunk_combo = ttk.Combobox(
            doc_frame, textvariable=self.chunk_var, 
            state="readonly", width=40
        )
        self.chunk_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        doc_frame.columnconfigure(1, weight=1)
        
        # Style selection
        style_frame = ttk.LabelFrame(gen_frame, text="Summary Style")
        style_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for i, style in enumerate(PromptStyle):
            desc = self._get_style_description(style)
            ttk.Radiobutton(
                style_frame,
                text=f"{style.value.title()} ({desc})",
                variable=self.style_var,
                value=style.value
            ).grid(row=i, column=0, sticky="w", padx=5, pady=2)
        
        # Focus areas
        focus_frame = ttk.LabelFrame(gen_frame, text="Focus Areas")
        focus_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize focus area checkboxes
        for i, focus_area in enumerate(FocusArea):
            self.focus_vars[focus_area] = tk.BooleanVar()
            cb = ttk.Checkbutton(
                focus_frame,
                text=focus_area.value.replace("_", " ").title(),
                variable=self.focus_vars[focus_area]
            )
            row = i % 4  # 4 rows
            col = i // 4  # Multiple columns
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        
        # Default selection
        self.focus_vars[FocusArea.KEY_CONCEPTS].set(True)
        
        # Preview area
        preview_frame = ttk.LabelFrame(gen_frame, text="Generated Prompt Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, height=15, width=80, wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(gen_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Generate Prompt",
            command=self._generate_prompt
        ).pack(side=tk.LEFT, padx=5)
        
        self.copy_button = ttk.Button(
            button_frame, text="Copy to Clipboard",
            command=self._copy_to_clipboard, state="disabled"
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
    
    def _bind_events(self):
        """Bind event handlers."""
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_changed)
        self.document_combo.bind("<<ComboboxSelected>>", self._on_document_changed)
        self.chunk_combo.bind("<<ComboboxSelected>>", self._on_selection_changed)
        
        # Style and focus changes
        self.style_var.trace_add("write", self._on_selection_changed)
        for var in self.focus_vars.values():
            var.trace_add("write", self._on_selection_changed)
    
    def _load_initial_data(self):
        """Load initial data."""
        # Load templates
        try:
            templates = template_factory.get_available_templates()
            template_names = [f"{t['name']}" for t in templates]
            self.template_combo['values'] = template_names
            if template_names:
                self.template_combo.set(template_names[0])
                self._on_template_changed()
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            messagebox.showerror("Error", f"Failed to load templates: {e}")
        
        # Load documents
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from database adapter or MCP server."""
        try:
            # Try database adapter first (faster and more reliable)
            if DATABASE_ADAPTER_AVAILABLE and get_database_adapter:
                db_adapter = get_database_adapter()
                docs_result = db_adapter.list_documents()
                documents_data = docs_result.get('documents', [])
                
                # Convert database format to expected format
                self.available_documents = []
                for doc_data in documents_data:
                    document = {
                        'id': doc_data.get('document_id'),
                        'title': doc_data.get('title', 'Untitled'),
                        'file_type': doc_data.get('file_type', 'unknown'),
                        'indexed': doc_data.get('indexed', False),
                        'total_pages': doc_data.get('total_pages'),
                        'total_words': doc_data.get('total_words')
                    }
                    self.available_documents.append(document)
                
                # Update UI
                doc_names = [f"{doc['title']} ({doc['file_type'].upper()})" for doc in self.available_documents]
                self.document_combo['values'] = doc_names
                
                if doc_names:
                    self.document_combo.set(doc_names[0])
                    self._on_document_changed()
                    
                return  # Successfully loaded from database
                
            # Fallback to MCP client if available
            if self.mcp_client:
                asyncio.create_task(self._load_documents_from_mcp())
            else:
                # No data source available
                self.document_combo['values'] = ["No documents available"]
                self.document_combo.set("No documents available")
        
        except Exception as e:
            self.logger.error(f"Failed to load documents: {e}")
            self.document_combo['values'] = ["Error loading documents"]
            self.document_combo.set("Error loading documents")
    
    async def _load_documents_from_mcp(self):
        """Load documents from MCP server (fallback method)."""
        try:
            if not self.mcp_client:
                return
                
            response = await self.mcp_client.call_tool("list_documents")
            
            if hasattr(response, 'data') and response.data.get("success"):
                documents = response.data.get("documents", [])
                self.available_documents = documents
                
                doc_names = [f"{doc['title']} ({doc['file_type'].upper()})" for doc in documents]
                self.document_combo['values'] = doc_names
                
                if doc_names:
                    self.document_combo.set(doc_names[0])
                    self._on_document_changed()
        
        except Exception as e:
            self.logger.error(f"Failed to load documents from MCP: {e}")
    
    def _on_template_changed(self, event=None):
        """Handle template change."""
        try:
            template_name = self.template_var.get()
            if template_name:
                self.current_template = template_factory.get_template_by_name(template_name)
                self._auto_generate()
        except Exception as e:
            self.logger.error(f"Template change error: {e}")
    
    def _on_document_changed(self, event=None):
        """Handle document change."""
        try:
            doc_index = self.document_combo.current()
            if 0 <= doc_index < len(self.available_documents):
                self.selected_document = self.available_documents[doc_index]
                self._load_chunks()
        except Exception as e:
            self.logger.error(f"Document change error: {e}")
    
    def _load_chunks(self):
        """Load chunks for selected document."""
        if not self.selected_document or not self.selected_document.get('indexed'):
            self.chunk_combo['values'] = ["Document not indexed"]
            self.chunk_combo.set("Document not indexed")
            self._on_selection_changed()
            return
        
        try:
            # Try database adapter first
            if DATABASE_ADAPTER_AVAILABLE and get_database_adapter:
                db_adapter = get_database_adapter()
                document_id = self.selected_document["id"]
                structure = db_adapter.get_document_structure(document_id)
                chunks = structure.get("chunks", [])
                
                if chunks:
                    # Format chunk names for display
                    chunk_names = []
                    for chunk in chunks:
                        title = chunk.get('title', f'Chunk {chunk.get("chunk_index", "?")}')
                        word_count = chunk.get('word_count', '?')
                        chunk_names.append(f"{title} ({word_count} words)")
                    
                    self.chunk_combo['values'] = chunk_names
                    self.chunk_combo.set(chunk_names[0])
                    
                    # Store chunks for reference
                    self.selected_document['chunks'] = chunks
                    self._on_selection_changed()
                    return
                else:
                    self.chunk_combo['values'] = ["No chunks available"]
                    self.chunk_combo.set("No chunks available")
                    self._on_selection_changed()
                    return
            
            # Fallback to MCP if available
            if self.mcp_client:
                asyncio.create_task(self._load_chunks_from_mcp())
            else:
                # No data source available
                self.chunk_combo['values'] = ["No chunks available"]
                self.chunk_combo.set("No chunks available")
                self._on_selection_changed()
        
        except Exception as e:
            self.logger.error(f"Failed to load chunks: {e}")
            self.chunk_combo['values'] = ["Error loading chunks"]
            self.chunk_combo.set("Error loading chunks")
    
    async def _load_chunks_from_mcp(self):
        """Load chunks from MCP server (fallback method)."""
        try:
            if not self.mcp_client or not self.selected_document:
                return
                
            response = await self.mcp_client.call_tool(
                "get_document_structure",
                {"document_id": self.selected_document["id"]}
            )
            
            if hasattr(response, 'data') and response.data.get("success"):
                chunks = response.data.get("chunks", [])
                
                if chunks:
                    chunk_names = [f"{chunk['title']} ({chunk['word_count']} words)" for chunk in chunks]
                    self.chunk_combo['values'] = chunk_names
                    self.chunk_combo.set(chunk_names[0])
                    
                    # Store chunks for reference
                    self.selected_document['chunks'] = chunks
                    self._on_selection_changed()
                else:
                    self.chunk_combo['values'] = ["No chunks available"]
                    self.chunk_combo.set("No chunks available")
        
        except Exception as e:
            self.logger.error(f"Failed to load chunks from MCP: {e}")
            self.chunk_combo['values'] = ["Error loading chunks"]
            self.chunk_combo.set("Error loading chunks")
    
    def _on_selection_changed(self, *args):
        """Handle any selection change."""
        self._auto_generate()
    
    def _auto_generate(self):
        """Auto-generate prompt if ready."""
        if self._has_required_data():
            self._generate_prompt()
    
    def _has_required_data(self):
        """Check if we have required data."""
        return (
            self.current_template and 
            self.selected_document and
            (
                "chunk_id" not in self.current_template.required_context or
                self._get_selected_chunk() is not None
            )
        )
    
    def _get_selected_chunk(self):
        """Get currently selected chunk."""
        if not self.selected_document or 'chunks' not in self.selected_document:
            return None
        
        chunk_index = self.chunk_combo.current()
        chunks = self.selected_document.get('chunks', [])
        
        if 0 <= chunk_index < len(chunks):
            return chunks[chunk_index]
        return None
    
    def _generate_prompt(self):
        """Generate AI prompt."""
        try:
            if not self._has_required_data():
                self._show_placeholder_prompt()
                return
            
            # Create context
            context = self._create_context()
            
            # Generate prompt
            if self.current_template and context:
                prompt = self.current_template.generate_prompt(context)
                
                # Update preview
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, prompt)
                
                # Enable copy
                self.copy_button.config(state="normal")
            else:
                self._show_placeholder_prompt()
            
        except Exception as e:
            self.logger.error(f"Prompt generation failed: {e}")
            self._show_placeholder_prompt()
    
    def _show_placeholder_prompt(self):
        """Show placeholder when prompt cannot be generated."""
        placeholder_text = """# AI Summary Prompt

Please select a document and template to generate a custom prompt.

Available when:
✅ Document is selected
✅ Template is chosen
✅ Document has content available

The generated prompt can then be copied and pasted into Copilot Chat for AI summarization."""
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, placeholder_text)
        self.copy_button.config(state="disabled")
    
    def _create_context(self):
        """Create template context from selections."""
        if not self.selected_document:
            return None
            
        selected_focus = [
            focus for focus, var in self.focus_vars.items() 
            if var.get()
        ]
        if not selected_focus:
            selected_focus = [FocusArea.KEY_CONCEPTS]
        
        chunk = self._get_selected_chunk()
        
        return TemplateContext(
            document_title=self.selected_document.get("title", "Unknown Document"),
            document_id=self.selected_document.get("id", 0),
            document_type=self.selected_document.get("file_type", "unknown"),
            chunk_title=chunk.get("title") if chunk else None,
            chunk_id=chunk.get("chunk_id") if chunk else None,
            chunk_type=chunk.get("chunk_type") if chunk else None,
            style=PromptStyle(self.style_var.get()),
            focus_areas=selected_focus
        )
    
    def _copy_to_clipboard(self):
        """Copy prompt to clipboard."""
        try:
            prompt_text = self.preview_text.get(1.0, tk.END).strip()
            if not prompt_text:
                messagebox.showwarning("No Content", "No prompt to copy.")
                return
            
            # Create metadata
            metadata = {
                "template": self.current_template.template_name if self.current_template else "Unknown",
                "document": self.selected_document["title"] if self.selected_document else "None",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Copy with metadata
            success = self.clipboard_manager.copy_prompt_with_metadata(
                prompt_text, metadata, show_notification=True
            )
            
            if success:
                self.logger.info("Prompt copied successfully")
                
        except Exception as e:
            self.logger.error(f"Copy failed: {e}")
            messagebox.showerror("Error", f"Failed to copy prompt: {e}")
    
    def _get_style_description(self, style):
        """Get style description."""
        descriptions = {
            PromptStyle.BRIEF: "100-150 words",
            PromptStyle.STANDARD: "250-350 words", 
            PromptStyle.DETAILED: "500-750 words"
        }
        return descriptions.get(style, "Standard")
    
    # Public interface methods
    
    def refresh(self):
        """Refresh widget data."""
        self._load_documents()
    
    def clear(self):
        """Clear widget content."""
        self.preview_text.delete(1.0, tk.END)
        self.copy_button.config(state="disabled")