"""
Keyboard Shortcuts Module for Study Buddy GUI Application.

This module provides a comprehensive keyboard shortcut system with the following components:

- ActionRegistry: Command pattern implementation for managing available actions
- ShortcutManager: Manages keyboard shortcut bindings and conflict resolution
- ShortcutEditor: GUI widget for customizing keyboard shortcuts
- ShortcutBinding: Data model for shortcut configuration
- ShortcutConflict: Conflict detection and resolution

Features:
- Customizable keyboard shortcuts
- Conflict detection and resolution
- Scope-based shortcut management (global vs context-specific)
- Import/export of shortcut configurations
- User-friendly shortcut customization interface
"""

from .action_registry import (
    ActionRegistry,
    IAction,
    ActionDefinition,
    ActionCategory,
    ActionScope
)

from .shortcut_manager import (
    ShortcutManager,
    ShortcutBinding,
    ShortcutModifier,
    ShortcutConflict
)

from .shortcut_editor import (
    ShortcutEditor,
    ShortcutCaptureDialog
)

__all__ = [
    # Action Registry
    "ActionRegistry",
    "IAction", 
    "ActionDefinition",
    "ActionCategory",
    "ActionScope",
    
    # Shortcut Manager
    "ShortcutManager",
    "ShortcutBinding",
    "ShortcutModifier", 
    "ShortcutConflict",
    
    # Shortcut Editor
    "ShortcutEditor",
    "ShortcutCaptureDialog"
]