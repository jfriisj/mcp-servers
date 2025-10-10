"""
Summary Panel Widget for Study Buddy GUI Application.

This module implements SummaryPanelWidget, a concrete widget extending BaseWidget
to display and manage AI-generated document summaries. Provides summary viewing,
type selection, and integration with MCP for summary operations.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: BaseWidget (Layer 1), EventBus (Layer 2), MCP Client (Layer 3)

SOLID Principles Applied:
- SRP: Single responsibility for summary display and management  
- OCP: Extensible via SummaryDisplayOptions and new summary types
- LSP: Full BaseWidget substitutability and contract compliance
- ISP: Focused interface with only summary-related methods
- DIP: Dependency injection for EventBus and MCP client
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import base widget system
from ..widgets.base_widget import (
    BaseWidget,
    EventBus, 
    GlobalEvent,
    WidgetState,
    LayoutConstraints,
    AccessibilityOptions
)

# Import database adapter for direct summary access
try:
    from ..database_adapter import get_database_adapter
    DATABASE_ADAPTER_AVAILABLE = True
except ImportError:
    DATABASE_ADAPTER_AVAILABLE = False
    get_database_adapter = None


class SummaryType(Enum):
    """Types of summaries available."""
    BRIEF = "brief"           # 100-150 words
    STANDARD = "standard"     # 250-350 words  
    DETAILED = "detailed"     # 500-750 words
    CUSTOM = "custom"         # User-defined length


class SummaryStatus(Enum):
    """Summary generation status."""
    NOT_REQUESTED = "not_requested"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"
    OUTDATED = "outdated"     # Document changed since summary generated


@dataclass
class SummaryDisplayOptions:
    """Configuration options for summary display."""
    font_family: str = "Segoe UI"
    font_size: int = 11
    line_spacing: float = 1.3
    show_metadata: bool = True
    show_word_count: bool = True
    show_generation_time: bool = True
    auto_refresh: bool = False
    max_display_length: int = 10000  # Character limit for display


@dataclass
class SummaryMetadata:
    """Metadata for a generated summary."""
    model_name: Optional[str] = None
    generation_time: Optional[datetime] = None
    word_count: int = 0
    character_count: int = 0
    processing_time_ms: int = 0
    confidence_score: Optional[float] = None
    
    @property
    def display_info(self) -> str:
        """Get formatted metadata display string."""
        info_parts = []
        
        if self.word_count > 0:
            info_parts.append(f"Words: {self.word_count:,}")
        
        if self.character_count > 0:
            info_parts.append(f"Characters: {self.character_count:,}")
            
        if self.model_name:
            info_parts.append(f"Model: {self.model_name}")
            
        if self.generation_time:
            info_parts.append(f"Generated: {self.generation_time.strftime('%H:%M:%S')}")
            
        if self.processing_time_ms > 0:
            time_str = f"{self.processing_time_ms:,}ms" if self.processing_time_ms < 1000 else f"{self.processing_time_ms/1000:.1f}s"
            info_parts.append(f"Time: {time_str}")
            
        return " | ".join(info_parts) if info_parts else "No metadata available"


@dataclass
class Summary:
    """Container for summary content and metadata."""
    summary_id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    summary_type: SummaryType = SummaryType.STANDARD
    content: str = ""
    status: SummaryStatus = SummaryStatus.NOT_REQUESTED
    metadata: SummaryMetadata = field(default_factory=SummaryMetadata)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        """Check if summary is available for display."""
        return self.status == SummaryStatus.COMPLETED and bool(self.content.strip())
    
    @property
    def is_generating(self) -> bool:
        """Check if summary is currently being generated."""
        return self.status == SummaryStatus.GENERATING
    
    @property
    def has_error(self) -> bool:
        """Check if summary has an error."""
        return self.status == SummaryStatus.ERROR
    
    @property
    def display_title(self) -> str:
        """Get display-friendly title for summary."""
        type_names = {
            SummaryType.BRIEF: "Brief Summary",
            SummaryType.STANDARD: "Standard Summary", 
            SummaryType.DETAILED: "Detailed Summary",
            SummaryType.CUSTOM: "Custom Summary"
        }
        return type_names.get(self.summary_type, "Summary")


class SummaryPanelWidget(BaseWidget):
    """
    Summary panel widget for displaying and managing document summaries.
    
    Responsibilities:
    - Display summaries in different formats (brief, standard, detailed)
    - Handle summary type selection and switching
    - Show summary metadata and generation status
    - Request new summaries via MCP client
    - Respond to document selection events
    - Provide summary management actions
    
    Does NOT:
    - Generate summaries (delegates to MCP server)
    - Parse or modify document content  
    - Handle document upload/storage
    - Implement AI/ML logic
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: EventBus,
        widget_id: str,
        mcp_client: Optional[Any] = None,
        constraints: Optional[LayoutConstraints] = None,
        accessibility: Optional[AccessibilityOptions] = None,
        display_options: Optional[SummaryDisplayOptions] = None
    ):
        """
        Initialize summary panel widget.
        
        Args:
            parent: Parent tkinter widget
            event_bus: Event system for widget communication  
            widget_id: Unique identifier for this widget
            mcp_client: Optional MCP client for summary operations
            constraints: Optional layout constraints
            accessibility: Optional accessibility settings
            display_options: Optional display configuration
        """
        # Initialize display options
        self._display_options = display_options or SummaryDisplayOptions()
        
        # Initialize BaseWidget
        super().__init__(
            parent=parent,
            event_bus=event_bus, 
            widget_id=widget_id,
            constraints=constraints,
            accessibility=accessibility
        )
        
        # Store MCP client reference
        self.mcp_client = mcp_client
        
        # Internal state
        self._current_document_id: Optional[int] = None
        self._current_chunk_id: Optional[int] = None
        self._summaries: Dict[SummaryType, Summary] = {}
        self._selected_summary_type: SummaryType = SummaryType.STANDARD
        
        # UI Components (will be created in create_ui)
        self._type_selector: Optional[ttk.Combobox] = None
        self._summary_text: Optional[tk.Text] = None
        self._metadata_label: Optional[ttk.Label] = None
        self._status_label: Optional[ttk.Label] = None
        self._generate_button: Optional[ttk.Button] = None
        self._refresh_button: Optional[ttk.Button] = None
        self._clear_button: Optional[ttk.Button] = None
        self._scrollbar: Optional[ttk.Scrollbar] = None
        
        # Initialize UI
        self.create_ui()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Setup accessibility
        self._setup_accessibility()
        
        # Set initial state
        self._update_display()

    def create_ui(self) -> None:
        """Create the summary panel user interface."""
        try:
            self.show_loading("Setting up summary panel...")
            
            # Create main container
            if self.root_frame:
                self.root_frame.configure(relief="ridge", borderwidth=1)
            
            # Create components
            self._create_header()
            self._create_summary_display()
            self._create_action_buttons()
            self._create_status_bar()
            
            # Apply theme
            self._apply_theme()
            
            self.hide_loading()
            self._state = WidgetState.READY
            
        except Exception as e:
            self._handle_ui_error(f"Failed to create summary panel UI: {str(e)}")

    def _create_header(self) -> None:
        """Create header section with summary type selector."""
        header_frame = ttk.Frame(self.root_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Summary type label
        type_label = ttk.Label(header_frame, text="Summary Type:")
        type_label.pack(side="left", padx=(0, 10))
        
        # Summary type selector
        self._type_selector = ttk.Combobox(
            header_frame,
            values=[t.value.title() for t in SummaryType],
            state="readonly",
            width=15
        )
        self._type_selector.pack(side="left")
        
        # Set default value safely
        try:
            self._type_selector.set(self._selected_summary_type.value.title())
        except AttributeError:
            # Fallback if _selected_summary_type not initialized yet
            self._type_selector.set(SummaryType.STANDARD.value.title())
        
        self._type_selector.bind("<<ComboboxSelected>>", self._on_type_changed)
        
        # Generate button in header
        self._generate_button = ttk.Button(
            header_frame,
            text="Generate",
            command=self._on_generate_summary,
            state="disabled"
        )
        self._generate_button.pack(side="right", padx=(10, 0))

    def _create_summary_display(self) -> None:
        """Create summary content display area."""
        display_frame = ttk.Frame(self.root_frame)
        display_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Summary text widget
        self._summary_text = tk.Text(
            display_frame,
            wrap=tk.WORD,
            font=(self._display_options.font_family, self._display_options.font_size),
            state="disabled",
            bg="white",
            fg="black",
            selectbackground="#3399ff",
            selectforeground="white",
            spacing1=2,
            spacing2=1,
            spacing3=2
        )
        self._summary_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for text widget
        self._scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self._summary_text.yview)
        self._scrollbar.pack(side="right", fill="y")
        self._summary_text.configure(yscrollcommand=self._scrollbar.set)
        
        # Configure text widget tags for formatting
        self._configure_text_tags()

    def _create_action_buttons(self) -> None:
        """Create action buttons for summary management."""
        actions_frame = ttk.Frame(self.root_frame)
        actions_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Refresh button
        self._refresh_button = ttk.Button(
            actions_frame,
            text="Refresh",
            command=self._on_refresh_summary,
            state="disabled"
        )
        self._refresh_button.pack(side="left", padx=(0, 5))
        
        # Clear button
        self._clear_button = ttk.Button(
            actions_frame,
            text="Clear",
            command=self._on_clear_summary
        )
        self._clear_button.pack(side="left", padx=(0, 5))
        
        # Metadata display (right side)
        self._metadata_label = ttk.Label(
            actions_frame,
            text="No summary loaded",
            foreground="gray"
        )
        self._metadata_label.pack(side="right")

    def _create_status_bar(self) -> None:
        """Create status bar for displaying summary status."""
        status_frame = ttk.Frame(self.root_frame, relief="sunken", borderwidth=1)
        status_frame.pack(fill="x", padx=2, pady=2)
        
        self._status_label = ttk.Label(
            status_frame,
            text="Ready - Select a document to view summaries",
            anchor="w"
        )
        self._status_label.pack(side="left", padx=5, pady=2)

    def _configure_text_tags(self) -> None:
        """Configure text widget formatting tags."""
        if not self._summary_text:
            return
            
        # Configure different text styles
        self._summary_text.tag_configure("title", font=(self._display_options.font_family, self._display_options.font_size + 2, "bold"))
        self._summary_text.tag_configure("heading", font=(self._display_options.font_family, self._display_options.font_size + 1, "bold"))
        self._summary_text.tag_configure("emphasis", font=(self._display_options.font_family, self._display_options.font_size, "italic"))
        self._summary_text.tag_configure("code", font=("Consolas", self._display_options.font_size), background="#f5f5f5")
        self._summary_text.tag_configure("error", foreground="red")
        self._summary_text.tag_configure("generating", foreground="orange")

    def _setup_event_handlers(self) -> None:
        """Set up event subscriptions and handlers."""
        # Subscribe to document selection events
        self._subscribe_event('document.selected', self._on_document_selected)
        self._subscribe_event('document.content_updated', self._on_document_updated)
        self._subscribe_event('document.deleted', self._on_document_deleted)
        
        # Subscribe to summary events
        self._subscribe_event('summary.generated', self._on_summary_generated)
        self._subscribe_event('summary.error', self._on_summary_error)

    def _setup_accessibility(self) -> None:
        """Setup accessibility features."""
        # Set up keyboard shortcuts
        if self.root_frame:
            self.root_frame.bind("<Control-g>", lambda e: self._on_generate_summary())
            self.root_frame.bind("<F5>", lambda e: self.refresh_current_summary())
            
        # Screen reader support
        if self.accessibility.screen_reader_label:
            # Set accessible labels for screen readers
            pass

    # Event Handlers
    def _on_document_selected(self, event: GlobalEvent) -> None:
        """Handle document selection event from DocumentBrowserWidget."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            document = event_data.get('document', {})
            
            if document_id:
                self._current_document_id = document_id
                self._current_chunk_id = None  # Reset chunk selection
                
                # Load existing summaries for this document
                self._load_document_summaries(document_id)
                
                # Update UI state
                self._update_display()
                self._update_buttons()
                
                # Update status
                doc_title = document.get('title', f'Document {document_id}')
                self._update_status(f"Loaded summaries for: {doc_title}")
                
        except Exception as e:
            self._show_error(f"Error handling document selection: {str(e)}")

    def _on_document_updated(self, event: GlobalEvent) -> None:
        """Handle document content update event."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            
            if document_id == self._current_document_id:
                # Mark existing summaries as potentially outdated
                for summary in self._summaries.values():
                    if summary.status == SummaryStatus.COMPLETED:
                        summary.status = SummaryStatus.OUTDATED
                
                self._update_display()
                self._update_status("Document updated - summaries may be outdated")
                
        except Exception as e:
            self._show_error(f"Error handling document update: {str(e)}")

    def _on_document_deleted(self, event: GlobalEvent) -> None:
        """Handle document deletion event."""
        try:
            event_data = event.data
            document_id = event_data.get('document_id')
            
            if document_id == self._current_document_id:
                # Clear all summaries and reset state
                self.clear_summaries()
                self._current_document_id = None
                self._current_chunk_id = None
                
                self._update_display()
                self._update_buttons()
                self._update_status("Document deleted - summaries cleared")
                
        except Exception as e:
            self._show_error(f"Error handling document deletion: {str(e)}")

    def _on_summary_generated(self, event: GlobalEvent) -> None:
        """Handle summary generation completion event."""
        try:
            event_data = event.data
            summary_data = event_data.get('summary', {})
            
            # Create Summary object from event data
            summary = Summary(
                summary_id=summary_data.get('summary_id'),
                document_id=summary_data.get('document_id'),
                chunk_id=summary_data.get('chunk_id'),
                summary_type=SummaryType(summary_data.get('summary_type', 'standard')),
                content=summary_data.get('content', ''),
                status=SummaryStatus.COMPLETED,
                metadata=SummaryMetadata(
                    model_name=summary_data.get('model_name'),
                    word_count=len(summary_data.get('content', '').split()),
                    character_count=len(summary_data.get('content', '')),
                    processing_time_ms=summary_data.get('processing_time_ms', 0)
                )
            )
            
            # Store the summary
            self._summaries[summary.summary_type] = summary
            
            # Update display if this is the currently selected type
            if summary.summary_type == self._selected_summary_type:
                self._update_display()
            
            self._update_buttons()
            self._update_status(f"{summary.display_title} generated successfully")
            
        except Exception as e:
            self._show_error(f"Error handling summary generation: {str(e)}")

    def _on_summary_error(self, event: GlobalEvent) -> None:
        """Handle summary generation error event."""
        try:
            event_data = event.data
            error_message = event_data.get('error', 'Unknown error')
            summary_type_str = event_data.get('summary_type', 'standard')
            summary_type = SummaryType(summary_type_str)
            
            # Create error summary
            error_summary = Summary(
                summary_type=summary_type,
                status=SummaryStatus.ERROR,
                error_message=error_message
            )
            
            self._summaries[summary_type] = error_summary
            
            # Update display if this is the currently selected type
            if summary_type == self._selected_summary_type:
                self._update_display()
            
            self._update_buttons()
            self._show_error(f"Summary generation failed: {error_message}")
            
        except Exception as e:
            self._show_error(f"Error handling summary error: {str(e)}")

    # UI Event Handlers
    def _on_type_changed(self, event=None) -> None:
        """Handle summary type selection change."""
        if not self._type_selector:
            return
            
        try:
            selected_value = self._type_selector.get().lower()
            self._selected_summary_type = SummaryType(selected_value)
            
            # Update display for new type
            self._update_display()
            self._update_buttons()
            
            # Update status
            type_name = self._selected_summary_type.value.title()
            self._update_status(f"Switched to {type_name} summary view")
            
        except ValueError:
            self._show_error(f"Invalid summary type selected: {selected_value}")

    def _on_generate_summary(self) -> None:
        """Handle generate summary button click."""
        if not self._current_document_id:
            self._show_error("No document selected for summary generation")
            return
            
        try:
            # Update status to show generation in progress
            summary_type_name = self._selected_summary_type.value.title()
            self._update_status(f"Generating {summary_type_name} summary...")
            
            # Create generating summary placeholder
            generating_summary = Summary(
                document_id=self._current_document_id,
                chunk_id=self._current_chunk_id,
                summary_type=self._selected_summary_type,
                status=SummaryStatus.GENERATING
            )
            
            self._summaries[self._selected_summary_type] = generating_summary
            
            # Update display and buttons
            self._update_display()
            self._update_buttons()
            
            # Request summary generation via MCP (if available)
            if self.mcp_client:
                self._request_summary_generation()
            else:
                # No MCP client available - cannot generate AI summaries
                self._show_error("AI summary generation requires MCP server connection. Please start the MCP server or use manual summarization.")
                # Remove the generating placeholder
                if self._selected_summary_type in self._summaries:
                    del self._summaries[self._selected_summary_type]
                self._update_display()
                self._update_buttons()
                
        except Exception as e:
            self._show_error(f"Error initiating summary generation: {str(e)}")

    def _on_refresh_summary(self) -> None:
        """Handle refresh summary button click."""
        current_summary = self._summaries.get(self._selected_summary_type)
        
        if not current_summary or not current_summary.is_available:
            self._show_error("No summary to refresh")
            return
            
        try:
            # Re-request the summary
            self._on_generate_summary()
            
        except Exception as e:
            self._show_error(f"Error refreshing summary: {str(e)}")

    def _on_clear_summary(self) -> None:
        """Handle clear summary button click.""" 
        try:
            # Clear current summary type
            if self._selected_summary_type in self._summaries:
                del self._summaries[self._selected_summary_type]
            
            # Update display
            self._update_display()
            self._update_buttons()
            
            type_name = self._selected_summary_type.value.title()
            self._update_status(f"Cleared {type_name} summary")
            
        except Exception as e:
            self._show_error(f"Error clearing summary: {str(e)}")

    # Display Methods
    def _update_display(self) -> None:
        """Update the summary display area."""
        if not self._summary_text:
            return
            
        # Clear current content
        self._summary_text.configure(state="normal")
        self._summary_text.delete("1.0", tk.END)
        
        # Get current summary
        current_summary = self._summaries.get(self._selected_summary_type)
        
        if not current_summary:
            # No summary available
            self._display_no_summary()
        elif current_summary.is_generating:
            # Summary is being generated
            self._display_generating_status()
        elif current_summary.has_error:
            # Summary has error
            self._display_error(current_summary.error_message or "Unknown error")
        elif current_summary.is_available:
            # Display the summary
            self._display_summary_content(current_summary)
        else:
            # Unexpected state
            self._display_no_summary()
            
        # Update metadata display
        self._update_metadata_display(current_summary)
        
        # Make text read-only
        self._summary_text.configure(state="disabled")

    def _display_no_summary(self) -> None:
        """Display message when no summary is available."""
        message = f"No {self._selected_summary_type.value} summary available.\n\n"
        
        if self._current_document_id:
            message += "Click 'Generate' to create a new summary for the selected document."
        else:
            message += "Select a document from the Document Browser to generate summaries."
            
        if self._summary_text:
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert("1.0", message)

    def _display_generating_status(self) -> None:
        """Display status when summary is being generated."""
        message = f"Generating {self._selected_summary_type.value} summary...\n\n"
        message += "This may take a few moments depending on document length and complexity.\n"
        message += "Please wait while the AI processes the content."
        
        if self._summary_text:
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert("1.0", message, "generating")

    def _display_error(self, error_message: str) -> None:
        """Display error message."""
        message = f"Error generating {self._selected_summary_type.value} summary:\n\n"
        message += error_message + "\n\n"
        message += "Please try again or contact support if the issue persists."
        
        if self._summary_text:
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert("1.0", message, "error")

    def _display_summary_content(self, summary: Summary) -> None:
        """Display the actual summary content."""
        # Insert summary title
        title = f"{summary.display_title}\n"
        if self._summary_text:
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert("1.0", title, "title")
        
        # Add separator
        separator = "─" * 50 + "\n\n"
        if self._summary_text:
            self._summary_text.insert(tk.END, separator)
        
        # Insert summary content
        if summary.content:
            # Apply basic markdown-style formatting
            self._insert_formatted_content(summary.content)
        else:
            if self._summary_text:
                self._summary_text.insert(tk.END, "Summary content is empty.")
        
        # Add status indicator if outdated
        if summary.status == SummaryStatus.OUTDATED:
            outdated_note = "\n\n⚠️ This summary may be outdated as the document has been modified."
            if self._summary_text:
                self._summary_text.insert(tk.END, outdated_note, "emphasis")

    def _insert_formatted_content(self, content: str) -> None:
        """Insert content with basic formatting applied."""
        if not self._summary_text:
            return
            
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('# '):
                # Heading level 1
                self._summary_text.insert(tk.END, line + '\n', "heading")
            elif line.startswith('## '):
                # Heading level 2  
                self._summary_text.insert(tk.END, line + '\n', "heading")
            elif line.startswith('**') and line.endswith('**'):
                # Bold text (emphasis)
                self._summary_text.insert(tk.END, line[2:-2] + '\n', "emphasis")
            elif '`' in line:
                # Code snippets
                self._insert_line_with_code(line)
            else:
                # Regular text
                self._summary_text.insert(tk.END, line + '\n')

    def _insert_line_with_code(self, line: str) -> None:
        """Insert line with inline code formatting."""
        if not self._summary_text:
            return
            
        import re
        
        # Find code snippets in backticks
        code_pattern = r'`([^`]+)`'
        last_end = 0
        
        for match in re.finditer(code_pattern, line):
            # Insert text before code
            if match.start() > last_end:
                self._summary_text.insert(tk.END, line[last_end:match.start()])
            
            # Insert code with formatting
            code_text = match.group(1)
            self._summary_text.insert(tk.END, code_text, "code")
            
            last_end = match.end()
        
        # Insert remaining text
        if last_end < len(line):
            self._summary_text.insert(tk.END, line[last_end:])
            
        self._summary_text.insert(tk.END, '\n')

    def _update_metadata_display(self, summary: Optional[Summary]) -> None:
        """Update metadata label with summary information."""
        if not self._metadata_label:
            return
            
        if summary and summary.is_available and self._display_options.show_metadata:
            metadata_text = summary.metadata.display_info
            self._metadata_label.configure(text=metadata_text, foreground="black")
        else:
            self._metadata_label.configure(text="No metadata available", foreground="gray")

    def _update_buttons(self) -> None:
        """Update button states based on current state."""
        has_document = self._current_document_id is not None
        current_summary = self._summaries.get(self._selected_summary_type)
        is_generating = current_summary and current_summary.is_generating
        has_summary = current_summary and current_summary.is_available
        
        # Generate button
        if self._generate_button:
            self._generate_button.configure(
                state="disabled" if is_generating or not has_document else "normal",
                text="Generating..." if is_generating else "Generate"
            )
        
        # Refresh button
        if self._refresh_button:
            self._refresh_button.configure(
                state="normal" if has_summary and not is_generating else "disabled"
            )
        
        # Clear button (always enabled if there's something to clear)
        if self._clear_button:
            has_anything = self._selected_summary_type in self._summaries
            self._clear_button.configure(state="normal" if has_anything else "disabled")

    def _update_status(self, message: str) -> None:
        """Update status bar with message."""
        if self._status_label:
            self._status_label.configure(text=message)

    # MCP Integration Methods
    def _load_document_summaries(self, document_id: int) -> None:
        """Load existing summaries for a document."""
        try:
            # Try database first (faster, more reliable)
            if DATABASE_ADAPTER_AVAILABLE and get_database_adapter is not None:
                try:
                    db_adapter = get_database_adapter()
                    summaries_result = db_adapter.list_summaries(document_id=document_id)
                    summaries_data = summaries_result.get('summaries', [])
                    
                    # Convert to Summary objects
                    for summary_data in summaries_data:
                        try:
                            summary_type = SummaryType(summary_data.get('summary_type', 'standard'))
                            
                            # Parse generation_date if it's a string
                            generation_time = summary_data.get('generation_date')
                            if isinstance(generation_time, str):
                                try:
                                    generation_time = datetime.fromisoformat(generation_time.replace('Z', '+00:00'))
                                except ValueError:
                                    # Handle different date format from database
                                    generation_time = datetime.strptime(generation_time, '%Y-%m-%d %H:%M:%S')
                            elif generation_time is None:
                                generation_time = datetime.now()
                            
                            summary = Summary(
                                summary_id=summary_data.get('summary_id'),
                                document_id=summary_data.get('document_id') or document_id,  # Use document_id if not in data
                                chunk_id=summary_data.get('chunk_id'),  # Add chunk_id support
                                summary_type=summary_type,
                                content=summary_data.get('summary_content', ''),
                                status=SummaryStatus.COMPLETED,
                                metadata=SummaryMetadata(
                                    model_name=summary_data.get('model_name'),
                                    word_count=summary_data.get('word_count', 0),
                                    character_count=len(summary_data.get('summary_content', '')),
                                    generation_time=generation_time
                                )
                            )
                            
                            self._summaries[summary_type] = summary
                            
                        except (ValueError, TypeError) as e:
                            print(f"Error processing summary data: {e}")
                            continue
                    
                    return  # Successfully loaded from database
                    
                except Exception as e:
                    print(f"Database load failed, falling back to MCP: {e}")
            
            # Fallback to MCP client
            if self.mcp_client:
                response = self.mcp_client.get_document_summaries(document_id)
                
                if response.get('success', False):
                    summaries_data = response.get('summaries', [])
                    
                    # Convert to Summary objects
                    for summary_data in summaries_data:
                        try:
                            summary_type = SummaryType(summary_data.get('summary_type', 'standard'))
                            
                            summary = Summary(
                                summary_id=summary_data.get('summary_id'),
                                document_id=document_id,
                                chunk_id=summary_data.get('chunk_id'),
                                summary_type=summary_type,
                                content=summary_data.get('content', ''),
                                status=SummaryStatus.COMPLETED,
                                metadata=SummaryMetadata(
                                    model_name=summary_data.get('model_name'),
                                    word_count=summary_data.get('word_count', 0),
                                    character_count=summary_data.get('character_count', 0),
                                    generation_time=datetime.fromisoformat(summary_data.get('generation_time', datetime.now().isoformat()))
                                )
                            )
                            
                            self._summaries[summary_type] = summary
                            
                        except (ValueError, TypeError) as e:
                            print(f"Error processing MCP summary data: {e}")
                            continue
                    
        except Exception as e:
            self._show_error(f"Error loading summaries: {str(e)}")

    def _request_summary_generation(self) -> None:
        """Request summary generation via MCP client."""
        if not self.mcp_client or not self._current_document_id:
            return
            
        try:
            # Prepare request parameters
            request_params = {
                'document_id': self._current_document_id,
                'summary_type': self._selected_summary_type.value,
                'chunk_id': self._current_chunk_id  # None for full document
            }
            
            # Request generation (async operation)
            response = self.mcp_client.generate_summary(**request_params)
            
            if not response.get('success', False):
                error_message = response.get('error', 'Unknown error occurred')
                raise Exception(error_message)
                
        except Exception as e:
            # Remove generating placeholder and show error
            if self._selected_summary_type in self._summaries:
                del self._summaries[self._selected_summary_type]
                
            self._show_error(f"Error requesting summary: {str(e)}")
            self._update_display()
            self._update_buttons()



    # Utility Methods
    def _apply_theme(self) -> None:
        """Apply current theme to widget components."""
        # This would integrate with the theme system from base_widget
        # For now, we'll use default styling
        pass

    def _show_error(self, message: str) -> None:
        """Display error message to user."""
        try:
            self._update_status(f"Error: {message}")
        except AttributeError:
            # Status label not created yet, log error instead
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Summary panel error: {message}")
        # Could also show a popup dialog or other error indication

    def _handle_ui_error(self, message: str) -> None:
        """Handle UI creation errors."""
        self._state = WidgetState.ERROR
        self.hide_loading()
        self._show_error(message)

    # Public API Methods
    def get_current_summary(self) -> Optional[Summary]:
        """Get currently displayed summary."""
        return self._summaries.get(self._selected_summary_type)

    def get_summaries_for_document(self, document_id: int) -> Dict[SummaryType, Summary]:
        """Get all summaries for a specific document."""
        if document_id != self._current_document_id:
            return {}
        return self._summaries.copy()

    def request_summary(self, summary_type: SummaryType) -> bool:
        """Request generation of a specific summary type."""
        if not self._current_document_id:
            return False
            
        # Set the type and trigger generation
        self._selected_summary_type = summary_type
        if self._type_selector:
            self._type_selector.set(summary_type.value.title())
        
        self._on_generate_summary()
        return True

    def clear_summaries(self) -> None:
        """Clear all summaries."""
        self._summaries.clear()
        self._update_display()
        self._update_buttons()
        self._update_status("All summaries cleared")

    def set_summary_type(self, summary_type: SummaryType) -> None:
        """Set the active summary type."""
        self._selected_summary_type = summary_type
        if self._type_selector:
            self._type_selector.set(summary_type.value.title())
        self._update_display()
        self._update_buttons()

    def update_display_options(self, options: SummaryDisplayOptions) -> None:
        """Update display options and refresh view."""
        self._display_options = options
        
        # Apply new font settings
        if self._summary_text:
            self._summary_text.configure(
                font=(options.font_family, options.font_size)
            )
            self._configure_text_tags()
        
        # Refresh display
        self._update_display()

    def refresh_current_summary(self) -> None:
        """Refresh the currently displayed summary."""
        self._on_refresh_summary()

    def is_ready_for_generation(self) -> bool:
        """Check if widget is ready for summary generation."""
        return (
            self._current_document_id is not None and 
            self.get_state() == WidgetState.READY and
            not self._is_currently_generating()
        )

    def _is_currently_generating(self) -> bool:
        """Check if any summary is currently being generated."""
        return any(s.is_generating for s in self._summaries.values())