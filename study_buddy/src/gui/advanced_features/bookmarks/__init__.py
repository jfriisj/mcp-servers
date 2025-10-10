"""
Bookmarks Module for Study Buddy GUI Application.

This module provides comprehensive bookmark management functionality including:

- BookmarkManager: High-level coordination of bookmark operations
- BookmarkWidget: GUI interface for bookmark display and management  
- BookmarkDialog: Dialog for adding/editing bookmark information

Features:
- Position tracking and navigation within documents
- Bookmark organization with tags and colors
- Search and filtering capabilities
- Export functionality for bookmark data
- Integration with content viewer for automatic position updates
- Reading position management for seamless document navigation

The module follows the Facade pattern with BookmarkManager providing a clean
interface for GUI components, while maintaining separation between business
logic and presentation layers.
"""

from .bookmark_manager import BookmarkManager
from .bookmark_widget import BookmarkWidget, BookmarkDialog

__all__ = [
    "BookmarkManager",
    "BookmarkWidget", 
    "BookmarkDialog"
]