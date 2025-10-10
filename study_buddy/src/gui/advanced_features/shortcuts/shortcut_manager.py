"""
Keyboard Shortcut Manager for Study Buddy GUI Application.

Manages keyboard shortcuts and their bindings to actions. Provides customizable
shortcut configuration, conflict detection, and integration with the action registry.
Supports context-aware shortcut handling and user customization.
"""

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Set, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from gui.config.settings_manager import SettingsManager
from gui.advanced_features.shortcuts.action_registry import (
    ActionRegistry, ActionContext, ActionScope, get_action_registry
)


class ShortcutModifier(Enum):
    """Keyboard modifiers for shortcuts."""
    CTRL = "Control"
    SHIFT = "Shift"
    ALT = "Alt"
    CMD = "Command"  # For macOS compatibility
    META = "Meta"


@dataclass
class ShortcutBinding:
    """Represents a keyboard shortcut binding."""
    key: str
    modifiers: Set[ShortcutModifier] = field(default_factory=set)
    action_id: str = ""
    description: str = ""
    scope: ActionScope = ActionScope.GLOBAL
    
    def to_tkinter_sequence(self) -> str:
        """Convert to Tkinter key sequence format."""
        parts = []
        
        # Add modifiers
        for modifier in self.modifiers:
            parts.append(modifier.value)
        
        # Add key
        parts.append(self.key)
        
        return f"<{'-'.join(parts)}>"
    
    def to_display_string(self) -> str:
        """Convert to human-readable display string."""
        parts = []
        
        # Add modifiers in standard order
        for modifier in [ShortcutModifier.CTRL, ShortcutModifier.SHIFT, ShortcutModifier.ALT]:
            if modifier in self.modifiers:
                if modifier == ShortcutModifier.CTRL:
                    parts.append("Ctrl")
                elif modifier == ShortcutModifier.SHIFT:
                    parts.append("Shift")
                elif modifier == ShortcutModifier.ALT:
                    parts.append("Alt")
        
        # Add key
        key_display = self.key
        if key_display.lower() == "plus":
            key_display = "+"
        elif key_display.lower() == "minus":
            key_display = "-"
        elif len(key_display) == 1:
            key_display = key_display.upper()
        
        parts.append(key_display)
        
        return "+".join(parts)
    
    @classmethod
    def from_string(cls, shortcut_str: str, action_id: str = "", description: str = "") -> 'ShortcutBinding':
        """
        Create ShortcutBinding from string format like 'Ctrl+Shift+F'.
        
        Args:
            shortcut_str: String representation of shortcut
            action_id: Associated action ID
            description: Shortcut description
            
        Returns:
            ShortcutBinding instance
        """
        parts = shortcut_str.replace(" ", "").split("+")
        
        modifiers = set()
        key = ""
        
        for part in parts:
            part_lower = part.lower()
            if part_lower in ["ctrl", "control"]:
                modifiers.add(ShortcutModifier.CTRL)
            elif part_lower == "shift":
                modifiers.add(ShortcutModifier.SHIFT)
            elif part_lower == "alt":
                modifiers.add(ShortcutModifier.ALT)
            else:
                key = part
        
        return cls(
            key=key,
            modifiers=modifiers,
            action_id=action_id,
            description=description
        )


class ShortcutConflict:
    """Represents a shortcut conflict between bindings."""
    
    def __init__(self, shortcut: ShortcutBinding, existing_binding: ShortcutBinding):
        self.shortcut = shortcut
        self.existing_binding = existing_binding
    
    def __str__(self) -> str:
        return (f"Shortcut conflict: {self.shortcut.to_display_string()} "
                f"already bound to {self.existing_binding.action_id}")


class ShortcutManager:
    """
    Manages keyboard shortcuts and their bindings to actions.
    
    Responsibilities:
    - Store and manage shortcut bindings
    - Handle shortcut conflicts and validation
    - Provide shortcut customization interface
    - Integration with Tkinter event system
    - Persistence of user customizations
    
    SOLID Compliance:
    - SRP: Only handles shortcut management and binding
    - OCP: New shortcuts can be added without modification
    - LSP: Consistent shortcut handling interface
    - ISP: Focused interface for shortcut operations
    - DIP: Depends on ActionRegistry abstraction
    """
    
    def __init__(self, action_registry: ActionRegistry, settings_manager: SettingsManager):
        self.action_registry = action_registry
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)
        
        # Shortcut storage
        self._shortcuts: Dict[str, ShortcutBinding] = {}  # key_sequence -> binding
        self._action_shortcuts: Dict[str, str] = {}  # action_id -> key_sequence
        self._bound_widgets: Set[tk.Widget] = set()
        
        # Context tracking
        self._current_context = ActionContext()
        self._context_callbacks: List[Callable[[ActionContext], None]] = []
        
        # Load shortcuts from configuration
        self._load_shortcuts()
        
        # Initialize default shortcuts from action registry
        self._initialize_default_shortcuts()
    
    def bind_shortcut(
        self, 
        shortcut: ShortcutBinding, 
        force: bool = False
    ) -> Tuple[bool, Optional[ShortcutConflict]]:
        """
        Bind a keyboard shortcut to an action.
        
        Args:
            shortcut: Shortcut binding to add
            force: If True, replace existing binding
            
        Returns:
            Tuple of (success, conflict_info)
        """
        key_sequence = shortcut.to_tkinter_sequence()
        
        # Check for conflicts
        if key_sequence in self._shortcuts and not force:
            existing = self._shortcuts[key_sequence]
            conflict = ShortcutConflict(shortcut, existing)
            return False, conflict
        
        # Verify action exists
        action_def = self.action_registry.get_action(shortcut.action_id)
        if not action_def:
            self.logger.error(f"Cannot bind shortcut to unknown action: {shortcut.action_id}")
            return False, None
        
        # Remove existing binding for this action if any
        old_sequence = self._action_shortcuts.get(shortcut.action_id)
        if old_sequence and old_sequence in self._shortcuts:
            del self._shortcuts[old_sequence]
        
        # Add new binding
        self._shortcuts[key_sequence] = shortcut
        self._action_shortcuts[shortcut.action_id] = key_sequence
        
        # Update widget bindings
        self._update_widget_bindings()
        
        self.logger.info(f"Bound shortcut {shortcut.to_display_string()} to {shortcut.action_id}")
        return True, None
    
    def unbind_shortcut(self, key_sequence: str) -> bool:
        """
        Remove a shortcut binding.
        
        Args:
            key_sequence: Tkinter key sequence to remove
            
        Returns:
            True if removed, False if not found
        """
        if key_sequence not in self._shortcuts:
            return False
        
        binding = self._shortcuts[key_sequence]
        del self._shortcuts[key_sequence]
        
        if binding.action_id in self._action_shortcuts:
            del self._action_shortcuts[binding.action_id]
        
        self._update_widget_bindings()
        
        self.logger.info(f"Unbound shortcut {binding.to_display_string()}")
        return True
    
    def get_shortcut_for_action(self, action_id: str) -> Optional[ShortcutBinding]:
        """Get shortcut binding for an action."""
        key_sequence = self._action_shortcuts.get(action_id)
        if key_sequence:
            return self._shortcuts.get(key_sequence)
        return None
    
    def get_all_shortcuts(self) -> List[ShortcutBinding]:
        """Get all current shortcut bindings."""
        return list(self._shortcuts.values())
    
    def get_shortcuts_by_scope(self, scope: ActionScope) -> List[ShortcutBinding]:
        """Get shortcuts available in a specific scope."""
        return [binding for binding in self._shortcuts.values() 
                if binding.scope == scope or binding.scope == ActionScope.GLOBAL]
    
    def register_widget(self, widget: tk.Widget) -> None:
        """
        Register a widget to receive shortcut events.
        
        Args:
            widget: Widget to bind shortcuts to
        """
        if widget in self._bound_widgets:
            return
        
        self._bound_widgets.add(widget)
        self._bind_shortcuts_to_widget(widget)
        
        # Bind focus events for context tracking
        widget.bind("<FocusIn>", lambda e: self._update_context(e.widget))
        widget.bind("<Button-1>", lambda e: self._update_context(e.widget))
        
        self.logger.debug(f"Registered widget for shortcuts: {widget}")
    
    def unregister_widget(self, widget: tk.Widget) -> None:
        """
        Unregister a widget from shortcut events.
        
        Args:
            widget: Widget to unbind shortcuts from
        """
        if widget not in self._bound_widgets:
            return
        
        self._bound_widgets.discard(widget)
        self._unbind_shortcuts_from_widget(widget)
        
        self.logger.debug(f"Unregistered widget from shortcuts: {widget}")
    
    def update_context(self, context: ActionContext) -> None:
        """
        Update current context for shortcut execution.
        
        Args:
            context: New action context
        """
        self._current_context = context
        
        # Notify context change listeners
        for callback in self._context_callbacks:
            try:
                callback(context)
            except Exception as e:
                self.logger.error(f"Error in context callback: {str(e)}")
    
    def add_context_listener(self, callback: Callable[[ActionContext], None]) -> None:
        """Add listener for context changes."""
        self._context_callbacks.append(callback)
    
    def save_shortcuts(self) -> bool:
        """
        Save current shortcuts to configuration.
        
        Returns:
            True if saved successfully
        """
        try:
            # Convert shortcuts to serializable format
            shortcuts_data = {}
            for key_sequence, binding in self._shortcuts.items():
                shortcuts_data[binding.action_id] = {
                    "key": binding.key,
                    "modifiers": [mod.value for mod in binding.modifiers],
                    "description": binding.description,
                    "scope": binding.scope.value
                }
            
            # Save to settings
            self.settings_manager.set_setting("shortcuts.bindings", shortcuts_data)
            
            self.logger.info("Saved shortcut configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save shortcuts: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all shortcuts to default values."""
        self._shortcuts.clear()
        self._action_shortcuts.clear()
        self._initialize_default_shortcuts()
        self._update_widget_bindings()
        self.logger.info("Reset shortcuts to defaults")
    
    def _load_shortcuts(self) -> None:
        """Load shortcuts from configuration."""
        try:
            # Get shortcuts data with fallback
            try:
                shortcuts_data = self.settings_manager.get_setting("shortcuts.bindings")
            except:
                shortcuts_data = {}
            
            if not shortcuts_data:
                shortcuts_data = {}
            
            for action_id, shortcut_data in shortcuts_data.items():
                # Convert modifiers back to enum
                modifiers = set()
                for mod_name in shortcut_data.get("modifiers", []):
                    for modifier in ShortcutModifier:
                        if modifier.value == mod_name:
                            modifiers.add(modifier)
                            break
                
                binding = ShortcutBinding(
                    key=shortcut_data["key"],
                    modifiers=modifiers,
                    action_id=action_id,
                    description=shortcut_data.get("description", ""),
                    scope=ActionScope(shortcut_data.get("scope", "global"))
                )
                
                key_sequence = binding.to_tkinter_sequence()
                self._shortcuts[key_sequence] = binding
                self._action_shortcuts[action_id] = key_sequence
            
            self.logger.info(f"Loaded {len(self._shortcuts)} shortcuts from configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load shortcuts: {str(e)}")
    
    def _initialize_default_shortcuts(self) -> None:
        """Initialize default shortcuts from action registry."""
        for action_def in self.action_registry.get_all_actions():
            if action_def.default_shortcut and action_def.action_id not in self._action_shortcuts:
                binding = ShortcutBinding.from_string(
                    action_def.default_shortcut,
                    action_def.action_id,
                    action_def.description
                )
                binding.scope = action_def.scope
                
                success, conflict = self.bind_shortcut(binding, force=False)
                if not success and conflict:
                    self.logger.warning(f"Default shortcut conflict: {conflict}")
    
    def _update_widget_bindings(self) -> None:
        """Update shortcut bindings on all registered widgets."""
        for widget in self._bound_widgets:
            self._unbind_shortcuts_from_widget(widget)
            self._bind_shortcuts_to_widget(widget)
    
    def _bind_shortcuts_to_widget(self, widget: tk.Widget) -> None:
        """Bind all shortcuts to a specific widget."""
        for key_sequence, binding in self._shortcuts.items():
            try:
                widget.bind(key_sequence, lambda e, b=binding: self._handle_shortcut(e, b))
            except tk.TclError as e:
                self.logger.warning(f"Failed to bind {key_sequence}: {str(e)}")
    
    def _unbind_shortcuts_from_widget(self, widget: tk.Widget) -> None:
        """Unbind all shortcuts from a specific widget."""
        for key_sequence in self._shortcuts.keys():
            try:
                widget.unbind(key_sequence)
            except tk.TclError:
                pass  # Binding might not exist
    
    def _handle_shortcut(self, event: tk.Event, binding: ShortcutBinding) -> str:
        """
        Handle shortcut key press.
        
        Args:
            event: Tkinter event
            binding: Shortcut binding that was triggered
            
        Returns:
            "break" to prevent further event processing
        """
        try:
            # Update context with current widget
            if hasattr(event, 'widget'):
                self._update_context(event.widget)
            
            # Check if action is available in current scope
            action_def = self.action_registry.get_action(binding.action_id)
            if not action_def:
                return "break"
            
            # Check scope compatibility
            current_scope = ActionScope.GLOBAL
            if hasattr(event, 'widget'):
                current_scope = self._determine_current_scope(event.widget)
            if not self._is_scope_compatible(action_def.scope, current_scope):
                return "break"
            
            # Execute action
            success = self.action_registry.execute_action(binding.action_id, self._current_context)
            
            if success:
                self.logger.debug(f"Executed shortcut: {binding.to_display_string()} -> {binding.action_id}")
            
            return "break"  # Prevent further processing
            
        except Exception as e:
            self.logger.error(f"Error handling shortcut {binding.to_display_string()}: {str(e)}")
            return "break"
    
    def _update_context(self, widget: tk.Misc) -> None:
        """Update action context based on current widget."""
        context = ActionContext()
        # Cast to Widget for context if it's a proper widget
        if isinstance(widget, tk.Widget):
            context.active_widget = widget
        
        # Extract additional context information with safe attribute access
        try:
            # Check for text widget methods
            if hasattr(widget, 'tag_ranges') and callable(getattr(widget, 'tag_ranges')):
                if widget.tag_ranges(tk.SEL):  # type: ignore
                    context.selected_text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)  # type: ignore
                    context.selection_start = widget.index(tk.SEL_FIRST)  # type: ignore
                    context.selection_end = widget.index(tk.SEL_LAST)  # type: ignore
            
            if hasattr(widget, 'index') and callable(getattr(widget, 'index')):
                context.cursor_position = widget.index(tk.INSERT)  # type: ignore
                
        except (tk.TclError, AttributeError, TypeError):
            pass
        
        # Add document context if available
        if hasattr(widget, 'document_id'):
            context.current_document_id = getattr(widget, 'document_id')
        
        self.update_context(context)
    
    def _determine_current_scope(self, widget: tk.Misc) -> ActionScope:
        """Determine appropriate scope for current widget."""
        widget_name = widget.__class__.__name__.lower()
        
        if 'text' in widget_name or 'entry' in widget_name:
            return ActionScope.EDITOR
        elif 'browser' in widget_name or 'list' in widget_name:
            return ActionScope.BROWSER
        elif 'viewer' in widget_name or 'content' in widget_name:
            return ActionScope.VIEWER
        else:
            return ActionScope.GLOBAL
    
    def _is_scope_compatible(self, action_scope: ActionScope, current_scope: ActionScope) -> bool:
        """Check if action scope is compatible with current scope."""
        if action_scope == ActionScope.GLOBAL:
            return True
        return action_scope == current_scope


# Factory function for easy initialization
def create_shortcut_manager(
    action_registry: Optional[ActionRegistry] = None,
    settings_manager: Optional[SettingsManager] = None
) -> ShortcutManager:
    """
    Factory function to create shortcut manager with dependencies.
    
    Args:
        action_registry: Optional action registry (uses global if not provided)
        settings_manager: Optional settings manager
        
    Returns:
        Configured ShortcutManager instance
    """
    if action_registry is None:
        action_registry = get_action_registry()
    
    if settings_manager is None:
        # This would need to be provided by the calling code
        from gui.config.settings_manager import FileSettingsManager
        settings_manager = FileSettingsManager()
    
    return ShortcutManager(action_registry, settings_manager)