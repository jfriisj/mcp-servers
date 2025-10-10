"""
Progress Panel Widget for Study Buddy MCP Server.

This module provides the ProgressPanelWidget class which displays reading progress
and allows users to update their progress through MCP tool interactions.
"""

from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add paths to import from other modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mcp-server', 'src'))

from ..sync_mcp_client import SyncMCPClient


class ProgressPanelWidget:
    """
    A GUI widget that displays reading progress and allows progress updates.
    
    This widget follows the Single Responsibility Principle by focusing solely
    on progress display and update functionality. It depends on abstractions
    (MCPClient) following the Dependency Inversion Principle.
    """
    
    def __init__(self, parent: tk.Widget, mcp_client: SyncMCPClient):
        """
        Initialize the ProgressPanelWidget.
        
        Args:
            parent: The parent tkinter widget
            mcp_client: The MCP client for backend interactions
        """
        self._mcp_client = mcp_client
        self._current_document_id: Optional[str] = None
        self._current_progress: Optional[Dict[str, Any]] = None
        
        # Create main frame
        self._frame = ttk.LabelFrame(parent, text="Reading Progress", padding="10")
        
        # Initialize UI components
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Document selection
        ttk.Label(self._frame, text="Document:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self._document_var = tk.StringVar()
        self._document_entry = ttk.Entry(self._frame, textvariable=self._document_var, width=40)
        self._document_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 5))
        
        # Load progress button
        self._load_button = ttk.Button(self._frame, text="Load Progress", command=self._load_progress)
        self._load_button.grid(row=0, column=3, padx=(5, 0), pady=(0, 5))
        
        # Progress display
        ttk.Label(self._frame, text="Progress:").grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        # Progress bar
        self._progress_var = tk.DoubleVar()
        self._progress_bar = ttk.Progressbar(
            self._frame, 
            variable=self._progress_var, 
            maximum=100,
            length=200
        )
        self._progress_bar.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(10, 5))
        
        # Progress percentage label
        self._percentage_label = ttk.Label(self._frame, text="0%")
        self._percentage_label.grid(row=1, column=2, padx=(5, 0), pady=(10, 5))
        
        # Pages input and update
        ttk.Label(self._frame, text="Pages Read:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        self._pages_var = tk.StringVar()
        self._pages_entry = ttk.Entry(self._frame, textvariable=self._pages_var, width=10)
        self._pages_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(5, 0))
        
        # Total pages label
        self._total_pages_label = ttk.Label(self._frame, text="/ 0 pages")
        self._total_pages_label.grid(row=2, column=2, sticky="w", padx=(5, 0), pady=(5, 0))
        
        # Update button
        self._update_button = ttk.Button(self._frame, text="Update Progress", command=self._update_progress)
        self._update_button.grid(row=2, column=3, padx=(5, 0), pady=(5, 0))
        
        # Status label
        self._status_label = ttk.Label(self._frame, text="Enter document ID to load progress")
        self._status_label.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        # Configure column weights for resizing
        self._frame.columnconfigure(1, weight=1)
        
        # Initially disable controls until progress is loaded
        self._set_controls_state(tk.DISABLED)
    
    def _set_controls_state(self, state: str) -> None:
        """Enable or disable progress update controls."""
        self._pages_entry.config(state=state)
        self._update_button.config(state=state)
    
    def _load_progress(self) -> None:
        """Load progress for the specified document."""
        document_id = self._document_var.get().strip()
        if not document_id:
            messagebox.showerror("Error", "Please enter a document ID")
            return
        
        try:
            self._status_label.config(text="Loading progress...")
            self._frame.update()
            
            # Call MCP tool to get reading progress
            result = self._mcp_client.get_reading_progress(document_id)
            
            if result.success:
                progress_data = result.data
                if progress_data and "progress" in progress_data:
                    self._current_document_id = document_id
                    self._current_progress = progress_data["progress"]
                    self._display_progress()
                    self._set_controls_state(tk.NORMAL)
                    self._status_label.config(text="Progress loaded successfully")
                else:
                    # No existing progress, create new
                    self._current_document_id = document_id
                    self._current_progress = None
                    self._display_no_progress()
                    self._set_controls_state(tk.NORMAL)
                    self._status_label.config(text="No progress found. Enter total pages and current progress.")
            else:
                error_msg = result.error or "Failed to load progress"
                messagebox.showerror("Error", error_msg)
                self._status_label.config(text=f"Error: {error_msg}")
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self._status_label.config(text=error_msg)
    
    def _display_progress(self) -> None:
        """Display the current progress in the UI."""
        if not self._current_progress:
            return
        
        progress = self._current_progress
        pages_read = progress.get("pages_read", 0)
        total_pages = progress.get("total_pages", 0)
        percentage = (pages_read / total_pages * 100) if total_pages > 0 else 0
        
        self._progress_var.set(percentage)
        self._percentage_label.config(text=f"{percentage:.1f}%")
        self._pages_var.set(str(pages_read))
        self._total_pages_label.config(text=f"/ {total_pages} pages")
    
    def _display_no_progress(self) -> None:
        """Display UI state when no progress exists."""
        self._progress_var.set(0)
        self._percentage_label.config(text="0%")
        self._pages_var.set("0")
        self._total_pages_label.config(text="/ 0 pages")
    
    def _update_progress(self) -> None:
        """Update reading progress via MCP tool."""
        if not self._current_document_id:
            messagebox.showerror("Error", "No document loaded")
            return
        
        try:
            pages_read = int(self._pages_var.get())
            if pages_read < 0:
                raise ValueError("Pages read cannot be negative")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of pages read")
            return
        
        try:
            self._status_label.config(text="Updating progress...")
            self._frame.update()
            
            # Call MCP tool to update reading progress
            result = self._mcp_client.update_reading_progress(
                self._current_document_id,
                pages_read
            )
            
            if result.success:
                # Reload progress to get updated data
                self._load_progress()
                messagebox.showinfo("Success", "Progress updated successfully")
            else:
                error_msg = result.error or "Failed to update progress"
                messagebox.showerror("Error", error_msg)
                self._status_label.config(text=f"Error: {error_msg}")
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self._status_label.config(text=error_msg)
    
    def get_frame(self) -> ttk.LabelFrame:
        """Get the main frame widget for embedding in parent containers."""
        return self._frame
    
    def refresh(self) -> None:
        """Refresh the progress display by reloading current document."""
        if self._current_document_id:
            self._load_progress()
    
    def set_document(self, document_id: str) -> None:
        """Set the document ID and load its progress."""
        self._document_var.set(document_id)
        self._load_progress()