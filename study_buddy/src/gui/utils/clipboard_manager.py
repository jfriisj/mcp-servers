"""
Study Buddy GUI - Clipboard Manager

Cross-platform clipboard operations for copying AI prompts and other text content.
Provides robust clipboard handling with multiple format support and error recovery.

Architecture: Clean Architecture Layer 4 (Infrastructure - Utilities)
SOLID: Single Responsibility (clipboard operations only)
"""

import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional, Dict, Any
from enum import Enum
import sys
import subprocess
import os


class ClipboardFormat(Enum):
    """Supported clipboard formats."""
    PLAIN_TEXT = "text/plain"
    RICH_TEXT = "text/rtf"
    MARKDOWN = "text/markdown"


class ClipboardError(Exception):
    """Exception raised when clipboard operations fail."""
    pass


class ClipboardManager:
    """
    Cross-platform clipboard operations manager.
    
    Provides reliable clipboard functionality with multiple format support,
    error handling, and fallback mechanisms for different platforms.
    
    Responsibilities:
    - Copy text to system clipboard
    - Handle multiple text formats
    - Provide user feedback for operations
    - Handle platform-specific clipboard quirks
    
    Does NOT:
    - Store clipboard history (could be added as extension)
    - Handle non-text clipboard content
    - Provide clipboard monitoring (outside scope)
    """
    
    def __init__(self, parent_widget: Optional[tk.Widget] = None):
        """
        Initialize clipboard manager.
        
        Args:
            parent_widget: Parent tkinter widget for clipboard operations
                          If None, will create temporary root when needed
        """
        self.parent_widget = parent_widget
        self.logger = logging.getLogger(__name__)
        
        # Detect platform for platform-specific handling
        self.platform = sys.platform.lower()
        
    def copy_to_clipboard(
        self, 
        text: str, 
        format_type: ClipboardFormat = ClipboardFormat.PLAIN_TEXT,
        show_notification: bool = True
    ) -> bool:
        """
        Copy text to system clipboard with specified format.
        
        Args:
            text: Text content to copy
            format_type: Clipboard format (plain text, rich text, markdown)
            show_notification: Whether to show success/error notifications
            
        Returns:
            True if copy was successful, False otherwise
        """
        if not text or not text.strip():
            if show_notification:
                messagebox.showwarning("Clipboard", "No content to copy to clipboard.")
            return False
        
        try:
            # Get or create tkinter root for clipboard operations
            root = self._get_tkinter_root()
            
            # Clear clipboard first
            root.clipboard_clear()
            
            # Copy text to clipboard
            root.clipboard_append(text)
            
            # Update clipboard (platform-specific)
            root.update_idletasks()
            
            # Verify copy was successful (when possible)
            if self._verify_clipboard_content(text):
                if show_notification:
                    self._show_copy_success_notification(len(text))
                self.logger.info(f"Successfully copied {len(text)} characters to clipboard")
                return True
            else:
                # Verification failed, try fallback methods
                return self._try_fallback_copy(text, show_notification)
                
        except Exception as e:
            self.logger.error(f"Clipboard copy failed: {str(e)}")
            if show_notification:
                messagebox.showerror(
                    "Clipboard Error", 
                    f"Failed to copy to clipboard: {str(e)}"
                )
            return False
    
    def copy_prompt_with_metadata(
        self, 
        prompt: str, 
        metadata: Dict[str, Any],
        show_notification: bool = True
    ) -> bool:
        """
        Copy AI prompt to clipboard with formatted metadata header.
        
        Adds helpful metadata as comments at the top of the prompt
        for user reference and debugging.
        
        Args:
            prompt: The generated AI prompt
            metadata: Dictionary with prompt metadata (template, style, etc.)
            show_notification: Whether to show notifications
            
        Returns:
            True if copy was successful, False otherwise
        """
        # Build formatted content with metadata
        formatted_content = self._format_prompt_with_metadata(prompt, metadata)
        
        return self.copy_to_clipboard(
            formatted_content,
            ClipboardFormat.PLAIN_TEXT,
            show_notification
        )
    
    def _format_prompt_with_metadata(self, prompt: str, metadata: Dict[str, Any]) -> str:
        """Format prompt with metadata header."""
        header_lines = [
            "<!-- Study Buddy AI Prompt -->",
            "<!-- Generated by Study Buddy GUI -->"
        ]
        
        # Add metadata as comments
        if "template" in metadata:
            header_lines.append(f"<!-- Template: {metadata['template']} -->")
        if "document" in metadata:
            header_lines.append(f"<!-- Document: {metadata['document']} -->")
        if "chunk" in metadata:
            header_lines.append(f"<!-- Chunk: {metadata['chunk']} -->")
        if "style" in metadata:
            header_lines.append(f"<!-- Style: {metadata['style']} -->")
        if "timestamp" in metadata:
            header_lines.append(f"<!-- Generated: {metadata['timestamp']} -->")
        
        header_lines.append("<!-- Copy this entire prompt to Copilot Chat -->")
        header_lines.append("")  # Blank line before prompt
        
        return "\n".join(header_lines) + "\n" + prompt
    
    def _get_tkinter_root(self) -> tk.Tk:
        """Get tkinter root for clipboard operations."""
        if self.parent_widget and hasattr(self.parent_widget, 'tk'):
            return self.parent_widget.tk
        elif self.parent_widget:
            # Try to get root from parent widget
            widget = self.parent_widget
            while widget.master:
                widget = widget.master
            return widget.tk
        else:
            # Create temporary root
            root = tk.Tk()
            root.withdraw()  # Hide the window
            return root
    
    def _verify_clipboard_content(self, expected_text: str) -> bool:
        """
        Verify that clipboard contains the expected text.
        
        Args:
            expected_text: Text that should be in clipboard
            
        Returns:
            True if clipboard matches expected text
        """
        try:
            root = self._get_tkinter_root()
            clipboard_content = root.clipboard_get()
            
            # Simple verification - check if our text is contained
            # (clipboard might have additional formatting)
            return expected_text.strip() in clipboard_content
            
        except Exception:
            # Verification failed, but copy might still have worked
            return False
    
    def _try_fallback_copy(self, text: str, show_notification: bool) -> bool:
        """
        Try platform-specific fallback clipboard methods.
        
        Args:
            text: Text to copy
            show_notification: Whether to show notifications
            
        Returns:
            True if fallback copy succeeded
        """
        try:
            if self.platform.startswith("win"):
                return self._windows_fallback_copy(text)
            elif self.platform.startswith("darwin"):
                return self._macos_fallback_copy(text)
            elif self.platform.startswith("linux"):
                return self._linux_fallback_copy(text)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Fallback clipboard copy failed: {str(e)}")
            if show_notification:
                messagebox.showerror(
                    "Clipboard Error",
                    "Unable to copy to clipboard. Please copy the text manually."
                )
            return False
    
    def _windows_fallback_copy(self, text: str) -> bool:
        """Windows-specific clipboard fallback."""
        try:
            # Use Windows clip.exe command
            process = subprocess.Popen(
                ["clip"], 
                stdin=subprocess.PIPE, 
                shell=True
            )
            process.communicate(input=text.encode('utf-8'))
            return process.returncode == 0
        except Exception:
            return False
    
    def _macos_fallback_copy(self, text: str) -> bool:
        """macOS-specific clipboard fallback."""
        try:
            # Use macOS pbcopy command
            process = subprocess.Popen(
                ["pbcopy"], 
                stdin=subprocess.PIPE
            )
            process.communicate(input=text.encode('utf-8'))
            return process.returncode == 0
        except Exception:
            return False
    
    def _linux_fallback_copy(self, text: str) -> bool:
        """Linux-specific clipboard fallback."""
        try:
            # Try xclip first, then xsel
            for command in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.PIPE
                    )
                    process.communicate(input=text.encode('utf-8'))
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
        except Exception:
            return False
    
    def _show_copy_success_notification(self, char_count: int) -> None:
        """Show success notification for clipboard copy."""
        messagebox.showinfo(
            "Copied to Clipboard",
            f"AI prompt ({char_count:,} characters) copied to clipboard.\n\n"
            f"You can now paste it into Copilot Chat or your preferred AI assistant."
        )
    
    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content.
        
        Returns:
            Clipboard text content, or None if unavailable
        """
        try:
            root = self._get_tkinter_root()
            return root.clipboard_get()
        except Exception as e:
            self.logger.debug(f"Unable to get clipboard content: {str(e)}")
            return None
    
    def clear_clipboard(self) -> bool:
        """
        Clear the system clipboard.
        
        Returns:
            True if clear was successful, False otherwise
        """
        try:
            root = self._get_tkinter_root()
            root.clipboard_clear()
            root.update_idletasks()
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear clipboard: {str(e)}")
            return False