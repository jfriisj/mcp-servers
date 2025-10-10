"""
Study Buddy GUI - Prompt Builder Widget (Final Version)

The core AI workflow interface for Study Buddy. This widget enables users to generate
intelligent prompts for AI agents, following the workflow described in the implementation guide.

Architecture: Clean Architecture Layer 1 (External Interface)
Patterns: Strategy (templates), Factory (template creation), Observer (events)
SOLID: All principles followed with proper dependency injection and abstractions
"""

import asyncio
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, List, Optional

from ..events import EventBus
from ..mcp_client import AsyncMCPClient
from ..templates.base_template import (BasePromptTemplate, FocusArea,
                                         PromptStyle, TemplateContext)
from ..templates.template_factory import template_factory
from ..utils.clipboard_manager import ClipboardManager
from ..widgets.base_widget import BaseWidget, LayoutConstraints


@dataclass
class DocumentInfo:
    """Document information for prompt generation."""

    document_id: int
    title: str
    file_type: str
    indexed: bool = False
    chunks: Optional[List[Dict[str, Any]]] = None


class PromptBuilderWidget(BaseWidget):
    """
    Intelligent Prompt Builder Widget.

    The centerpiece of Study Buddy's AI workflow:
    User Selection -> Template Strategy -> Generated Prompt -> Clipboard -> AI Agent

    This widget creates perfect instructions that AI agents can execute using MCP tools.
    """

    def __init__(
        self,
        parent: tk.Widget,
        event_bus: EventBus,
        mcp_client: AsyncMCPClient,
        widget_id: str = "prompt_builder",
        constraints: Optional[LayoutConstraints] = None,
        **kwargs,
    ):
        """Initialize the PromptBuilder widget."""
        # Set constraints for prompt builder
        if constraints is None:
            constraints = LayoutConstraints(
                min_width=800,
                min_height=600,
                preferred_width=1000,
                preferred_height=700,
            )

        # Initialize BaseWidget
        super().__init__(
            parent=parent,
            event_bus=event_bus,
            widget_id=widget_id,
            constraints=constraints,
        )

        # Dependencies (injected following DIP)
        self.mcp_client = mcp_client
        self.clipboard_manager = ClipboardManager(parent)

        # State
        self.available_documents: List[DocumentInfo] = []
        self.selected_document: Optional[DocumentInfo] = None
        self.current_template: Optional[BasePromptTemplate] = None

        # UI variables
        self.template_var = tk.StringVar(value="summarization")
        self.document_var = tk.StringVar()
        self.chunk_var = tk.StringVar()
        self.style_var = tk.StringVar(value="standard")
        self.focus_vars: Dict[FocusArea, tk.BooleanVar] = {}

        # UI components
        self.template_combo: Optional[ttk.Combobox] = None
        self.document_combo: Optional[ttk.Combobox] = None
        self.chunk_combo: Optional[ttk.Combobox] = None
        self.preview_text: Optional[scrolledtext.ScrolledText] = None
        self.copy_button: Optional[ttk.Button] = None

        # Load initial data
        self._schedule_initial_load()

    def create_ui(self) -> None:
        """Create the UI components (BaseWidget interface requirement)."""
        if not self.root_frame:
            return

        # Create notebook for organization
        notebook = ttk.Notebook(self.root_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Generation tab
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="Generate Prompt")
        self._create_generation_tab(gen_frame)

        # History tab (placeholder)
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="History")
        ttk.Label(history_frame, text="Prompt History (Future Feature)").pack(pady=20)

    def _create_generation_tab(self, parent: ttk.Frame) -> None:
        """Create the prompt generation interface."""
        # Template selection
        template_frame = ttk.LabelFrame(parent, text="AI Template")
        template_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(template_frame, text="Template:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.template_combo = ttk.Combobox(
            template_frame, textvariable=self.template_var, state="readonly", width=50
        )
        self.template_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        template_frame.columnconfigure(1, weight=1)

        # Document selection
        doc_frame = ttk.LabelFrame(parent, text="Document & Content")
        doc_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(doc_frame, text="Document:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.document_combo = ttk.Combobox(
            doc_frame, textvariable=self.document_var, state="readonly", width=50
        )
        self.document_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(doc_frame, text="Chunk/Chapter:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.chunk_combo = ttk.Combobox(
            doc_frame, textvariable=self.chunk_var, state="readonly", width=50
        )
        self.chunk_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        doc_frame.columnconfigure(1, weight=1)

        # Style selection
        style_frame = ttk.LabelFrame(parent, text="Summary Style")
        style_frame.pack(fill=tk.X, padx=5, pady=5)

        styles = [
            ("Brief (100-150 words)", "brief"),
            ("Standard (250-350 words)", "standard"),
            ("Detailed (500-750 words)", "detailed"),
        ]

        for i, (text, value) in enumerate(styles):
            ttk.Radiobutton(
                style_frame, text=text, variable=self.style_var, value=value
            ).grid(row=i, column=0, sticky="w", padx=5, pady=2)

        # Focus areas
        focus_frame = ttk.LabelFrame(parent, text="Focus Areas")
        focus_frame.pack(fill=tk.X, padx=5, pady=5)

        # Initialize focus variables
        for focus_area in FocusArea:
            self.focus_vars[focus_area] = tk.BooleanVar()

        # Default selection
        self.focus_vars[FocusArea.KEY_CONCEPTS].set(True)

        # Create checkboxes in grid
        for i, focus_area in enumerate(FocusArea):
            text = focus_area.value.replace("_", " ").title()
            cb = ttk.Checkbutton(
                focus_frame, text=text, variable=self.focus_vars[focus_area]
            )
            row = i % 3  # 3 rows
            col = i // 3  # Multiple columns
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)

        # Preview area
        preview_frame = ttk.LabelFrame(parent, text="Generated Prompt Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=15,
            width=80,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled",
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            button_frame, text="Generate Prompt", command=self._generate_prompt
        ).pack(side=tk.LEFT, padx=5)

        self.copy_button = ttk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=self._copy_to_clipboard,
            state="disabled",
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)

        # Bind events
        self._bind_events()

    def _bind_events(self) -> None:
        """Bind event handlers."""
        if self.template_combo:
            self.template_combo.bind("<<ComboboxSelected>>", self._on_template_changed)
        if self.document_combo:
            self.document_combo.bind("<<ComboboxSelected>>", self._on_document_changed)
        if self.chunk_combo:
            self.chunk_combo.bind("<<ComboboxSelected>>", self._on_selection_changed)

        # Variable traces
        self.style_var.trace_add("write", self._on_selection_changed)
        for var in self.focus_vars.values():
            var.trace_add("write", self._on_selection_changed)

    def _schedule_initial_load(self) -> None:
        """Schedule initial data loading."""
        # Use after_idle to ensure UI is created first
        if self.root_frame:
            self.root_frame.after_idle(
                lambda: asyncio.create_task(self._load_initial_data())
            )

    async def _load_initial_data(self) -> None:
        """Load initial data from MCP server."""
        try:
            self.show_loading("Loading templates and documents...")

            # Load templates
            await self._load_templates()

            # Load documents
            await self._load_documents()

            self.hide_loading()
            self._logger.info("Initial data loaded successfully")

        except Exception as e:
            self.hide_loading()
            self._logger.error(f"Failed to load initial data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load data: {e}")

    async def _load_templates(self) -> None:
        """Load available templates."""
        try:
            templates = template_factory.get_available_templates()
            template_names = [f"{t['name']}" for t in templates]

            if self.template_combo and template_names:
                self.template_combo["values"] = template_names
                self.template_combo.set(template_names[0])
                self._on_template_changed()

        except Exception as e:
            self._logger.error(f"Failed to load templates: {e}")
            raise

    async def _load_documents(self) -> None:
        """Load documents from MCP server."""
        try:
            response = await self.mcp_client.call_tool("list_documents")

            if response and hasattr(response, "data") and response.data:
                data = response.data
                if isinstance(data, dict) and data.get("success"):
                    documents = data.get("documents", [])

                    # Convert to DocumentInfo objects
                    self.available_documents = [
                        DocumentInfo(
                            document_id=doc["id"],
                            title=doc["title"],
                            file_type=doc["file_type"],
                            indexed=doc.get("indexed", False),
                        )
                        for doc in documents
                    ]

                    # Update UI
                    if self.document_combo and self.available_documents:
                        doc_names = [
                            f"{doc.title} ({doc.file_type.upper()})"
                            for doc in self.available_documents
                        ]
                        self.document_combo["values"] = doc_names
                        self.document_combo.set(doc_names[0])
                        self._on_document_changed()
                else:
                    self._logger.warning("MCP call failed or returned error")

        except Exception as e:
            self._logger.error(f"Failed to load documents: {e}")
            raise

    def _on_template_changed(self, event=None) -> None:
        """Handle template selection change."""
        try:
            template_name = self.template_var.get()
            if template_name:
                self.current_template = template_factory.get_template_by_name(
                    template_name
                )
                self._auto_generate_if_ready()
        except Exception as e:
            self._logger.error(f"Template change error: {e}")
            messagebox.showerror("Error", f"Template error: {e}")

    def _on_document_changed(self, event=None) -> None:
        """Handle document selection change."""
        try:
            if not self.document_combo:
                return

            doc_index = self.document_combo.current()
            if 0 <= doc_index < len(self.available_documents):
                self.selected_document = self.available_documents[doc_index]
                asyncio.create_task(self._load_chunks_for_document())
        except Exception as e:
            self._logger.error(f"Document change error: {e}")
            messagebox.showerror("Error", f"Document error: {e}")

    def _on_selection_changed(self, *args) -> None:
        """Handle any selection change."""
        self._auto_generate_if_ready()

    async def _load_chunks_for_document(self) -> None:
        """Load chunks for the selected document."""
        if not self.selected_document or not self.chunk_combo:
            return

        if not self.selected_document.indexed:
            self.chunk_combo["values"] = ["Document not indexed"]
            self.chunk_combo.set("Document not indexed")
            return

        try:
            response = await self.mcp_client.call_tool(
                "get_document_structure",
                {"document_id": self.selected_document.document_id},
            )

            if response and hasattr(response, "data") and response.data:
                data = response.data
                if isinstance(data, dict) and data.get("success"):
                    chunks = data.get("chunks", [])
                    self.selected_document.chunks = chunks

                    if chunks:
                        chunk_names = [
                            f"{chunk['title']} ({chunk['word_count']} words)"
                            for chunk in chunks
                        ]
                        self.chunk_combo["values"] = chunk_names
                        self.chunk_combo.set(chunk_names[0])
                        self._auto_generate_if_ready()
                    else:
                        self.chunk_combo["values"] = ["No chunks available"]
                        self.chunk_combo.set("No chunks available")

        except Exception as e:
            self._logger.error(f"Failed to load chunks: {e}")
            if self.chunk_combo:
                self.chunk_combo["values"] = [f"Error: {str(e)[:50]}"]
                self.chunk_combo.set(f"Error: {str(e)[:50]}")

    def _auto_generate_if_ready(self) -> None:
        """Auto-generate prompt if all required data is available."""
        if self._can_generate_prompt():
            self._generate_prompt()

    def _can_generate_prompt(self) -> bool:
        """Check if we have all required data for prompt generation."""
        return (
            self.current_template is not None
            and self.selected_document is not None
            and (
                not self._template_requires_chunk()
                or self._get_selected_chunk() is not None
            )
        )

    def _template_requires_chunk(self) -> bool:
        """Check if current template requires chunk selection."""
        # Most templates require chunks, but some work at document level
        return True  # For now, assume all templates need chunks

    def _get_selected_chunk(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected chunk."""
        if (
            not self.selected_document
            or not self.selected_document.chunks
            or not self.chunk_combo
        ):
            return None

        chunk_index = self.chunk_combo.current()
        if 0 <= chunk_index < len(self.selected_document.chunks):
            return self.selected_document.chunks[chunk_index]
        return None

    def _generate_prompt(self) -> None:
        """Generate AI prompt using current selections."""
        try:
            if (
                not self._can_generate_prompt()
                or not self.current_template
                or not self.selected_document
            ):
                return

            # Create context
            context = self._create_template_context()

            # Generate prompt using template strategy
            prompt = self.current_template.generate_prompt(context)

            # Update preview
            if self.preview_text:
                self.preview_text.config(state="normal")
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, prompt)
                self.preview_text.config(state="disabled")

            # Enable copy button
            if self.copy_button:
                self.copy_button.config(state="normal")

        except Exception as e:
            self._logger.error(f"Prompt generation failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate prompt: {e}")

    def _create_template_context(self) -> TemplateContext:
        """Create template context from current selections."""
        if not self.selected_document:
            raise ValueError("No document selected")

        selected_focus = [focus for focus, var in self.focus_vars.items() if var.get()]
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
            focus_areas=selected_focus,
        )

    def _copy_to_clipboard(self) -> None:
        """Copy generated prompt to clipboard."""
        try:
            if not self.preview_text:
                return

            # Get prompt text
            self.preview_text.config(state="normal")
            prompt_text = self.preview_text.get(1.0, tk.END).strip()
            self.preview_text.config(state="disabled")

            if not prompt_text:
                messagebox.showwarning("No Content", "No prompt to copy.")
                return

            # Create metadata
            metadata = {
                "template": (
                    self.current_template.template_name
                    if self.current_template
                    else "Unknown"
                ),
                "document": (
                    self.selected_document.title if self.selected_document else "None"
                ),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Copy to clipboard
            success = self.clipboard_manager.copy_prompt_with_metadata(
                prompt_text, metadata, show_notification=True
            )

            if success:
                self._logger.info("Prompt copied to clipboard successfully")
                messagebox.showinfo("Success", "Prompt copied to clipboard!")

        except Exception as e:
            self._logger.error(f"Copy to clipboard failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to copy prompt: {e}")

    # Public interface methods

    def refresh(self) -> None:
        """Refresh widget data."""
        asyncio.create_task(self._load_initial_data())

    def clear(self) -> None:
        """Clear widget content."""
        if self.preview_text:
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.config(state="disabled")
        if self.copy_button:
            self.copy_button.config(state="disabled")
