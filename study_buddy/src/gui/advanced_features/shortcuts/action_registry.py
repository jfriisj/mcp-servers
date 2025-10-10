"""
Action Registry for Study Buddy GUI Application.

Provides a centralized registry of all available actions that can be bound to keyboard
shortcuts, menu items, or toolbar buttons. Follows the Command pattern for extensible
action management and supports dynamic action registration.
"""

import logging
from typing import Dict, List, Callable, Any, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import messagebox


class ActionCategory(Enum):
    """Categories for organizing actions."""
    FILE = "file"
    EDIT = "edit"
    VIEW = "view"
    NAVIGATION = "navigation"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    ANNOTATION = "annotation"
    WINDOW = "window"
    HELP = "help"


class ActionScope(Enum):
    """Scope where actions can be executed."""
    GLOBAL = "global"  # Available everywhere
    DOCUMENT = "document"  # Only when document is active
    EDITOR = "editor"  # Only in text editing contexts
    BROWSER = "browser"  # Only in document browser
    VIEWER = "viewer"  # Only in content viewer


@dataclass
class ActionContext:
    """Context information for action execution."""
    active_widget: Optional[tk.Widget] = None
    selected_text: Optional[str] = None
    current_document_id: Optional[int] = None
    cursor_position: Optional[int] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None


class IAction(ABC):
    """
    Abstract base class for all actions.
    
    Follows Command pattern - each action encapsulates a request as an object,
    allowing for parameterization, queuing, and undoable operations.
    """
    
    @abstractmethod
    def execute(self, context: ActionContext) -> bool:
        """
        Execute the action.
        
        Args:
            context: Current application context
            
        Returns:
            True if action executed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def can_execute(self, context: ActionContext) -> bool:
        """
        Check if action can be executed in current context.
        
        Args:
            context: Current application context
            
        Returns:
            True if action is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable action description."""
        pass


@dataclass
class ActionDefinition:
    """Definition of a registered action."""
    action_id: str
    name: str
    description: str
    category: ActionCategory
    scope: ActionScope
    action: IAction
    default_shortcut: Optional[str] = None
    icon: Optional[str] = None
    tooltip: Optional[str] = None
    enabled: bool = True


class ActionRegistry:
    """
    Central registry for all available actions.
    
    Responsibilities:
    - Register and manage available actions
    - Provide action lookup by ID or category
    - Handle action execution with context
    - Support dynamic action registration
    
    SOLID Compliance:
    - SRP: Only manages action registration and lookup
    - OCP: New actions can be registered without modification
    - LSP: All actions follow IAction interface
    - ISP: Focused interface for action management
    - DIP: Depends on IAction abstraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._actions: Dict[str, ActionDefinition] = {}
        self._categories: Dict[ActionCategory, Set[str]] = {
            category: set() for category in ActionCategory
        }
        
        # Register built-in actions
        self._register_builtin_actions()
    
    def register_action(
        self,
        action_id: str,
        name: str,
        description: str,
        category: ActionCategory,
        scope: ActionScope,
        action: IAction,
        default_shortcut: Optional[str] = None,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None
    ) -> bool:
        """
        Register a new action.
        
        Args:
            action_id: Unique identifier for the action
            name: Display name for the action
            description: Detailed description
            category: Action category for organization
            scope: Scope where action is available
            action: Action implementation
            default_shortcut: Default keyboard shortcut
            icon: Optional icon identifier
            tooltip: Optional tooltip text
            
        Returns:
            True if registered successfully, False if ID already exists
        """
        if action_id in self._actions:
            self.logger.warning(f"Action ID already exists: {action_id}")
            return False
        
        try:
            action_def = ActionDefinition(
                action_id=action_id,
                name=name,
                description=description,
                category=category,
                scope=scope,
                action=action,
                default_shortcut=default_shortcut,
                icon=icon,
                tooltip=tooltip or description
            )
            
            self._actions[action_id] = action_def
            self._categories[category].add(action_id)
            
            self.logger.info(f"Registered action: {action_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register action {action_id}: {str(e)}")
            return False
    
    def unregister_action(self, action_id: str) -> bool:
        """
        Unregister an action.
        
        Args:
            action_id: ID of action to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if action_id not in self._actions:
            return False
        
        try:
            action_def = self._actions[action_id]
            self._categories[action_def.category].discard(action_id)
            del self._actions[action_id]
            
            self.logger.info(f"Unregistered action: {action_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister action {action_id}: {str(e)}")
            return False
    
    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """Get action definition by ID."""
        return self._actions.get(action_id)
    
    def get_actions_by_category(self, category: ActionCategory) -> List[ActionDefinition]:
        """Get all actions in a category."""
        action_ids = self._categories.get(category, set())
        return [self._actions[action_id] for action_id in action_ids if action_id in self._actions]
    
    def get_actions_by_scope(self, scope: ActionScope) -> List[ActionDefinition]:
        """Get all actions available in a scope."""
        return [action for action in self._actions.values() if action.scope == scope or action.scope == ActionScope.GLOBAL]
    
    def execute_action(self, action_id: str, context: ActionContext) -> bool:
        """
        Execute an action by ID.
        
        Args:
            action_id: ID of action to execute
            context: Current application context
            
        Returns:
            True if executed successfully, False otherwise
        """
        action_def = self.get_action(action_id)
        if not action_def:
            self.logger.warning(f"Action not found: {action_id}")
            return False
        
        if not action_def.enabled:
            self.logger.debug(f"Action disabled: {action_id}")
            return False
        
        try:
            if not action_def.action.can_execute(context):
                self.logger.debug(f"Action not available in current context: {action_id}")
                return False
            
            success = action_def.action.execute(context)
            if success:
                self.logger.debug(f"Executed action: {action_id}")
            else:
                self.logger.warning(f"Action execution failed: {action_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing action {action_id}: {str(e)}")
            return False
    
    def get_all_actions(self) -> List[ActionDefinition]:
        """Get all registered actions."""
        return list(self._actions.values())
    
    def enable_action(self, action_id: str, enabled: bool = True) -> bool:
        """Enable or disable an action."""
        action_def = self.get_action(action_id)
        if action_def:
            action_def.enabled = enabled
            return True
        return False
    
    def _register_builtin_actions(self) -> None:
        """Register built-in application actions."""
        
        # File actions
        self.register_action(
            "file.open",
            "Open Document",
            "Open a document file for viewing",
            ActionCategory.FILE,
            ActionScope.GLOBAL,
            OpenDocumentAction(),
            "Ctrl+O"
        )
        
        self.register_action(
            "file.close",
            "Close Document", 
            "Close the current document",
            ActionCategory.FILE,
            ActionScope.DOCUMENT,
            CloseDocumentAction(),
            "Ctrl+W"
        )
        
        # View actions
        self.register_action(
            "view.zoom_in",
            "Zoom In",
            "Increase text size",
            ActionCategory.VIEW,
            ActionScope.VIEWER,
            ZoomInAction(),
            "Ctrl+Plus"
        )
        
        self.register_action(
            "view.zoom_out",
            "Zoom Out", 
            "Decrease text size",
            ActionCategory.VIEW,
            ActionScope.VIEWER,
            ZoomOutAction(),
            "Ctrl+Minus"
        )
        
        self.register_action(
            "view.zoom_reset",
            "Reset Zoom",
            "Reset text size to default",
            ActionCategory.VIEW,
            ActionScope.VIEWER,
            ZoomResetAction(),
            "Ctrl+0"
        )
        
        # Navigation actions
        self.register_action(
            "nav.next_document",
            "Next Document",
            "Open next document in list",
            ActionCategory.NAVIGATION,
            ActionScope.GLOBAL,
            NextDocumentAction(),
            "Ctrl+Tab"
        )
        
        self.register_action(
            "nav.prev_document", 
            "Previous Document",
            "Open previous document in list",
            ActionCategory.NAVIGATION,
            ActionScope.GLOBAL,
            PrevDocumentAction(),
            "Ctrl+Shift+Tab"
        )
        
        # Search actions
        self.register_action(
            "search.find",
            "Find",
            "Open find dialog",
            ActionCategory.SEARCH,
            ActionScope.GLOBAL,
            FindAction(),
            "Ctrl+F"
        )
        
        self.register_action(
            "search.find_next",
            "Find Next",
            "Find next search result", 
            ActionCategory.SEARCH,
            ActionScope.GLOBAL,
            FindNextAction(),
            "F3"
        )
        
        # Bookmark actions (will be implemented in bookmark system)
        self.register_action(
            "bookmark.add",
            "Add Bookmark",
            "Add bookmark at current position",
            ActionCategory.BOOKMARK,
            ActionScope.DOCUMENT,
            AddBookmarkAction(),
            "Ctrl+B"
        )
        
        self.register_action(
            "bookmark.list",
            "Show Bookmarks",
            "Show bookmarks list",
            ActionCategory.BOOKMARK,
            ActionScope.GLOBAL,
            ShowBookmarksAction(),
            "Ctrl+Shift+B"
        )


# Built-in Action Implementations
class OpenDocumentAction(IAction):
    """Action to open a document."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with document browser
        messagebox.showinfo("Action", "Open Document - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Open a document file for viewing"


class CloseDocumentAction(IAction):
    """Action to close current document."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with content viewer
        messagebox.showinfo("Action", "Close Document - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return context.current_document_id is not None
    
    def get_description(self) -> str:
        return "Close the current document"


class ZoomInAction(IAction):
    """Action to zoom in content."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with content viewer
        messagebox.showinfo("Action", "Zoom In - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return context.active_widget is not None
    
    def get_description(self) -> str:
        return "Increase text size"


class ZoomOutAction(IAction):
    """Action to zoom out content."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with content viewer
        messagebox.showinfo("Action", "Zoom Out - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return context.active_widget is not None
    
    def get_description(self) -> str:
        return "Decrease text size"


class ZoomResetAction(IAction):
    """Action to reset zoom level."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with content viewer
        messagebox.showinfo("Action", "Reset Zoom - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return context.active_widget is not None
    
    def get_description(self) -> str:
        return "Reset text size to default"


class NextDocumentAction(IAction):
    """Action to navigate to next document."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with document browser
        messagebox.showinfo("Action", "Next Document - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Open next document in list"


class PrevDocumentAction(IAction):
    """Action to navigate to previous document."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with document browser
        messagebox.showinfo("Action", "Previous Document - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Open previous document in list"


class FindAction(IAction):
    """Action to open find dialog."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with search system
        messagebox.showinfo("Action", "Find - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Open find dialog"


class FindNextAction(IAction):
    """Action to find next search result."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with search system
        messagebox.showinfo("Action", "Find Next - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Find next search result"


class AddBookmarkAction(IAction):
    """Action to add bookmark at current position."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with bookmark system
        messagebox.showinfo("Action", "Add Bookmark - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return context.current_document_id is not None
    
    def get_description(self) -> str:
        return "Add bookmark at current position"


class ShowBookmarksAction(IAction):
    """Action to show bookmarks list."""
    
    def execute(self, context: ActionContext) -> bool:
        # This will be implemented when integrated with bookmark system
        messagebox.showinfo("Action", "Show Bookmarks - To be implemented")
        return True
    
    def can_execute(self, context: ActionContext) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Show bookmarks list"


# Singleton instance
_action_registry: Optional[ActionRegistry] = None


def get_action_registry() -> ActionRegistry:
    """Get the global action registry instance."""
    global _action_registry
    if _action_registry is None:
        _action_registry = ActionRegistry()
    return _action_registry