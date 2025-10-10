"""
Bookmark Manager Dialog for Study Buddy GUI Application.

This module implements BookmarkManagerDialog, providing a comprehensive interface
for creating and editing bookmarks with validation, category management,
and color selection for Task 14 Phase 2.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: tkinter (external framework), MCP Client (Layer 3)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class BookmarkData:
    """
    Data structure for bookmark creation/editing.
    
    Contains all fields needed for bookmark management with validation
    and display formatting. Follows single responsibility principle.
    """
    title: str = ""
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    category: str = "General"
    notes: str = ""
    page_number: Optional[int] = None
    position: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    color: str = "#FFD700"
    is_favorite: bool = False
    
    # Display properties
    document_title: str = ""
    chunk_title: str = ""
    
    def validate(self) -> List[str]:
        """
        Validate bookmark data and return error messages.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Title validation
        if not self.title or not self.title.strip():
            errors.append("Title is required")
        elif len(self.title.strip()) > 200:
            errors.append("Title must be 200 characters or less")
        
        # Document validation
        if self.document_id is None:
            errors.append("Document selection is required")
        elif self.document_id <= 0:
            errors.append("Invalid document selection")
        
        # Category validation
        if not self.category or not self.category.strip():
            errors.append("Category is required")
        elif len(self.category.strip()) > 50:
            errors.append("Category must be 50 characters or less")
        
        # Notes validation
        if self.notes and len(self.notes) > 2000:
            errors.append("Notes must be 2000 characters or less")
        
        # Page number validation
        if self.page_number is not None and self.page_number <= 0:
            errors.append("Page number must be positive")
        
        # Position validation
        if self.position and len(self.position) > 100:
            errors.append("Position must be 100 characters or less")
        
        # Tags validation
        for tag in self.tags:
            if not tag.strip():
                errors.append("Empty tags are not allowed")
            elif len(tag) > 30:
                errors.append(f"Tag '{tag}' is too long (max 30 characters)")
        
        if len(self.tags) > 10:
            errors.append("Maximum 10 tags allowed")
        
        # Color validation
        if not self._is_valid_color(self.color):
            errors.append("Invalid color format")
        
        return errors
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate hex color format."""
        if not color:
            return False
        if not color.startswith("#"):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP calls."""
        data = {
            "title": self.title.strip(),
            "document_id": self.document_id,
            "category": self.category.strip(),
            "color": self.color,
            "is_favorite": self.is_favorite
        }
        
        # Optional fields
        if self.chunk_id is not None:
            data["chunk_id"] = self.chunk_id
        if self.notes.strip():
            data["notes"] = self.notes.strip()
        if self.page_number is not None:
            data["page_number"] = self.page_number
        if self.position and self.position.strip():
            data["position"] = self.position.strip()
        if self.tags:
            data["tags"] = [tag.strip() for tag in self.tags if tag.strip()]
        
        return data


def show_bookmark_dialog(
    parent: tk.Widget,
    mcp_client,
    bookmark_id: Optional[int] = None,
    initial_document_id: Optional[int] = None,
    initial_chunk_id: Optional[int] = None
) -> Optional[BookmarkData]:
    """
    Show bookmark creation/editing dialog.
    
    Factory function for simple bookmark dialog creation.
    
    Args:
        parent: Parent widget for dialog
        mcp_client: MCP client for backend communication
        bookmark_id: ID of bookmark to edit (None for new)
        initial_document_id: Pre-select document
        initial_chunk_id: Pre-select chunk
    
    Returns:
        BookmarkData if saved, None if cancelled
    """
    messagebox.showinfo(
        "Bookmark Dialog", 
        f"Bookmark dialog not yet fully implemented.\n\n"
        f"Action: {'Edit' if bookmark_id else 'Create'}\n"
        f"Document ID: {initial_document_id}\n"
        f"Chunk ID: {initial_chunk_id}"
    )
    return None