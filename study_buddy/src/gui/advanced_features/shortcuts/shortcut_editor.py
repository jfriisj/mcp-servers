"""
Keyboard Shortcut Customization Widget for Study Buddy GUI Application.

Provides a user interface for customizing keyboard shortcuts, viewing current bindings,
and managing shortcut conflicts. Integrates with the shortcut manager for real-time
shortcut management and validation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Set, Tuple, cast
import logging

from gui.advanced_features.shortcuts.shortcut_manager import (
    ShortcutManager, ShortcutBinding, ShortcutConflict, ActionScope
)
from gui.advanced_features.shortcuts.action_registry import ActionRegistry, ActionCategory
from gui.widgets.base_widget import BaseWidget


class ShortcutCaptureDialog(tk.Toplevel):
    """Dialog for capturing keyboard shortcuts from user input."""
    
    def __init__(self, parent: tk.Widget, current_shortcut: Optional[ShortcutBinding] = None):
        super().__init__(parent)
        self.parent = parent
        self.current_shortcut = current_shortcut
        self.result = None
        self.captured_keys = set()
        self.captured_modifiers = set()
        
        self.title("Capture Keyboard Shortcut")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        
        self._create_widgets()
        self._center_on_parent()
        
        # Focus on capture area
        self.capture_frame.focus_set()
        
        # Bind key events
        self.bind('<KeyPress>', self._on_key_press)
        self.bind('<KeyRelease>', self._on_key_release)
        self.capture_frame.bind('<KeyPress>', self._on_key_press)
        self.capture_frame.bind('<KeyRelease>', self._on_key_release)
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Instructions
        instructions = tk.Label(
            self,
            text="Press the key combination you want to use as a shortcut.\\n"
                 "Use Escape to cancel or Delete to clear the shortcut.",
            wraplength=350,
            justify="center"
        )
        instructions.pack(pady=20)
        
        # Current shortcut display
        current_text = "No shortcut"
        if self.current_shortcut:
            current_text = self.current_shortcut.to_display_string()
        
        tk.Label(self, text=f"Current: {current_text}").pack(pady=5)
        
        # Capture area
        self.capture_frame = tk.Frame(self, relief="sunken", bd=2, height=40)
        self.capture_frame.pack(fill="x", padx=20, pady=10)
        
        self.capture_label = tk.Label(
            self.capture_frame,
            text="Press keys here...",
            bg="white",
            relief="flat"
        )
        self.capture_label.pack(expand=True, fill="both")
        
        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Clear",
            command=self._clear_shortcut
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="OK",
            command=self._accept
        ).pack(side="left", padx=5)
    
    def _center_on_parent(self) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - self.winfo_width()) // 2
        y = parent_y + (parent_height - self.winfo_height()) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _on_key_press(self, event: tk.Event) -> str:
        """Handle key press events."""
        key = event.keysym
        
        # Handle special keys
        if key == "Escape":
            self._cancel()
            return "break"
        elif key == "Delete":
            self._clear_shortcut()
            return "break"
        elif key == "Return":
            self._accept()
            return "break"
        
        # Capture modifiers
        if key in ["Control_L", "Control_R"]:
            self.captured_modifiers.add("Control")
        elif key in ["Shift_L", "Shift_R"]:
            self.captured_modifiers.add("Shift")
        elif key in ["Alt_L", "Alt_R"]:
            self.captured_modifiers.add("Alt")
        else:
            # Regular key
            self.captured_keys.add(key)
        
        self._update_display()
        return "break"
    
    def _on_key_release(self, event: tk.Event) -> str:
        """Handle key release events."""
        # Don't need to handle releases for capture
        return "break"
    
    def _update_display(self) -> None:
        """Update the capture display."""
        parts = []
        
        # Add modifiers
        for modifier in ["Control", "Shift", "Alt"]:
            if modifier in self.captured_modifiers:
                if modifier == "Control":
                    parts.append("Ctrl")
                else:
                    parts.append(modifier)
        
        # Add keys
        for key in sorted(self.captured_keys):
            if key not in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]:
                parts.append(key)
        
        if parts:
            display_text = "+".join(parts)
        else:
            display_text = "Press keys..."
        
        self.capture_label.configure(text=display_text)
    
    def _clear_shortcut(self) -> None:
        """Clear the current shortcut."""
        self.captured_keys.clear()
        self.captured_modifiers.clear()
        self._update_display()
    
    def _accept(self) -> None:
        """Accept the captured shortcut."""
        if self.captured_keys:
            # Create shortcut from captured input
            key = next(iter(self.captured_keys))  # Take first key
            modifiers = set()
            
            from gui.advanced_features.shortcuts.shortcut_manager import ShortcutModifier
            if "Control" in self.captured_modifiers:
                modifiers.add(ShortcutModifier.CTRL)
            if "Shift" in self.captured_modifiers:
                modifiers.add(ShortcutModifier.SHIFT)
            if "Alt" in self.captured_modifiers:
                modifiers.add(ShortcutModifier.ALT)
            
            self.result = ShortcutBinding(key=key, modifiers=modifiers)
        else:
            self.result = None  # Clear shortcut
        
        self.destroy()
    
    def _cancel(self) -> None:
        """Cancel shortcut capture."""
        self.result = None
        self.destroy()


class ShortcutEditor(BaseWidget):
    """
    Widget for editing and customizing keyboard shortcuts.
    
    Features:
    - Display all current shortcuts organized by category
    - Edit individual shortcuts with conflict detection
    - Search and filter shortcuts
    - Reset to defaults
    - Import/export shortcut configurations
    """
    
    def __init__(self, parent: tk.Widget, shortcut_manager: ShortcutManager, action_registry: ActionRegistry):
        # Create mock event bus for now (will be replaced when event system is implemented)
        class MockEventBus:
            def emit(self, event_name: str, data=None): pass
            def subscribe(self, event_name: str, callback): pass
        
        super().__init__(parent, MockEventBus(), "shortcut_editor")  # type: ignore
        self.shortcut_manager = shortcut_manager
        self.action_registry = action_registry
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self._shortcuts_data: Dict[str, ShortcutBinding] = {}
        self._filtered_actions: List[str] = []
        
        self._create_widgets()
        self._load_shortcuts()
    
    def _create_widgets(self) -> None:
        """Create the shortcut editor interface."""
        # Main container
        main_frame = ttk.Frame(cast(tk.Misc, self))
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 5))
        
        # Search
        ttk.Label(toolbar_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side="left", padx=(0, 10))
        
        # Category filter
        ttk.Label(toolbar_frame, text="Category:").pack(side="left", padx=(10, 5))
        self.category_var = tk.StringVar(value="All")
        categories = ["All"] + [cat.value.title() for cat in ActionCategory]
        self.category_combo = ttk.Combobox(
            toolbar_frame,
            textvariable=self.category_var,
            values=categories,
            state="readonly",
            width=15
        )
        self.category_combo.pack(side="left", padx=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Buttons
        ttk.Button(
            toolbar_frame,
            text="Reset All",
            command=self._reset_to_defaults
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            toolbar_frame,
            text="Save",
            command=self._save_shortcuts
        ).pack(side="right")
        
        # Shortcuts list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # Treeview for shortcuts
        columns = ("Action", "Shortcut", "Description", "Scope")
        self.shortcuts_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            height=20
        )
        
        # Configure columns
        self.shortcuts_tree.heading("#0", text="Category")
        self.shortcuts_tree.column("#0", width=100, minwidth=80)
        
        for col in columns:
            self.shortcuts_tree.heading(col, text=col)
            if col == "Action":
                self.shortcuts_tree.column(col, width=200, minwidth=150)
            elif col == "Shortcut":
                self.shortcuts_tree.column(col, width=120, minwidth=80)
            elif col == "Description":
                self.shortcuts_tree.column(col, width=300, minwidth=200)
            else:  # Scope
                self.shortcuts_tree.column(col, width=80, minwidth=60)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.shortcuts_tree.yview)
        self.shortcuts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.shortcuts_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click for editing
        self.shortcuts_tree.bind("<Double-1>", self._on_shortcut_double_click)
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self) -> None:
        """Create context menu for shortcuts."""
        self.context_menu = tk.Menu(cast(tk.Misc, self), tearoff=0)
        self.context_menu.add_command(label="Edit Shortcut", command=self._edit_selected_shortcut)
        self.context_menu.add_command(label="Clear Shortcut", command=self._clear_selected_shortcut)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reset to Default", command=self._reset_selected_shortcut)
        
        # Bind right-click
        self.shortcuts_tree.bind("<Button-3>", self._show_context_menu)
    
    def _load_shortcuts(self) -> None:
        """Load and display current shortcuts."""
        try:
            # Get all shortcuts
            shortcuts = self.shortcut_manager.get_all_shortcuts()
            
            # Get all actions to include those without shortcuts
            all_actions = self.action_registry.get_all_actions()
            
            # Build shortcuts data
            self._shortcuts_data = {}
            for shortcut in shortcuts:
                self._shortcuts_data[shortcut.action_id] = shortcut
            
            # Add actions without shortcuts
            for action_def in all_actions:
                if action_def.action_id not in self._shortcuts_data:
                    self._shortcuts_data[action_def.action_id] = ShortcutBinding(
                        key="",
                        action_id=action_def.action_id,
                        description=action_def.description,
                        scope=action_def.scope
                    )
            
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Failed to load shortcuts: {str(e)}")
            messagebox.showerror("Error", f"Failed to load shortcuts: {str(e)}", parent=cast(tk.Misc, self))
    
    def _update_display(self) -> None:
        """Update the shortcuts tree display."""
        # Clear existing items
        for item in self.shortcuts_tree.get_children():
            self.shortcuts_tree.delete(item)
        
        # Group by category
        categories: Dict[ActionCategory, List[str]] = {}
        
        for action_id, shortcut in self._shortcuts_data.items():
            action_def = self.action_registry.get_action(action_id)
            if action_def:
                category = action_def.category
                if category not in categories:
                    categories[category] = []
                categories[category].append(action_id)
        
        # Apply filters
        filtered_categories = self._apply_filters(categories)
        
        # Add category nodes and shortcuts
        for category, action_ids in filtered_categories.items():
            if not action_ids:
                continue
                
            category_node = self.shortcuts_tree.insert(
                "",
                "end",
                text=category.value.title(),
                values=("", "", f"{len(action_ids)} actions", ""),
                open=True
            )
            
            # Add shortcuts for this category
            for action_id in sorted(action_ids):
                shortcut = self._shortcuts_data[action_id]
                action_def = self.action_registry.get_action(action_id)
                
                if action_def:
                    shortcut_text = shortcut.to_display_string() if shortcut.key else "(None)"
                    
                    self.shortcuts_tree.insert(
                        category_node,
                        "end",
                        text="",
                        values=(
                            action_def.name,
                            shortcut_text,
                            action_def.description,
                            action_def.scope.value
                        ),
                        tags=(action_id,)
                    )
    
    def _apply_filters(self, categories: Dict[ActionCategory, List[str]]) -> Dict[ActionCategory, List[str]]:
        """Apply search and category filters."""
        filtered = {}
        
        search_text = self.search_var.get().lower()
        selected_category = self.category_var.get()
        
        for category, action_ids in categories.items():
            # Category filter
            if selected_category != "All" and category.value.title() != selected_category:
                continue
            
            # Search filter
            if search_text:
                filtered_actions = []
                for action_id in action_ids:
                    action_def = self.action_registry.get_action(action_id)
                    shortcut = self._shortcuts_data.get(action_id)
                    
                    if action_def and (
                        search_text in action_def.name.lower() or
                        search_text in action_def.description.lower() or
                        (shortcut and search_text in shortcut.to_display_string().lower())
                    ):
                        filtered_actions.append(action_id)
                
                filtered[category] = filtered_actions
            else:
                filtered[category] = action_ids
        
        return filtered
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes."""
        self._update_display()
    
    def _on_filter_changed(self, event=None) -> None:
        """Handle category filter changes."""
        self._update_display()
    
    def _on_shortcut_double_click(self, event: tk.Event) -> None:
        """Handle double-click on shortcut item."""
        self._edit_selected_shortcut()
    
    def _show_context_menu(self, event: tk.Event) -> None:
        """Show context menu at cursor position."""
        item = self.shortcuts_tree.identify("item", event.x, event.y)
        if item and self.shortcuts_tree.set(item, "Action"):  # Not a category
            self.shortcuts_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_action_id(self) -> Optional[str]:
        """Get action ID of selected item."""
        selection = self.shortcuts_tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.shortcuts_tree.item(item, "tags")
        
        return tags[0] if tags else None
    
    def _edit_selected_shortcut(self) -> None:
        """Edit the selected shortcut."""
        action_id = self._get_selected_action_id()
        if not action_id:
            return
        
        current_shortcut = self._shortcuts_data.get(action_id)
        action_def = self.action_registry.get_action(action_id)
        
        if not action_def:
            return
        
        # Open capture dialog
        dialog = ShortcutCaptureDialog(cast(tk.Widget, self), current_shortcut)
        cast(tk.Misc, self).wait_window(dialog)
        
        if dialog.result is not None:
            new_shortcut = dialog.result
            new_shortcut.action_id = action_id
            new_shortcut.description = action_def.description
            new_shortcut.scope = action_def.scope
            
            # Check for conflicts
            if new_shortcut.key:
                success, conflict = self.shortcut_manager.bind_shortcut(new_shortcut, force=False)
                
                if not success and conflict:
                    # Ask user about conflict
                    response = messagebox.askyesno(
                        "Shortcut Conflict",
                        f"The shortcut {new_shortcut.to_display_string()} is already used by "
                        f"{conflict.existing_binding.action_id}.\\n\\nReplace the existing shortcut?",
                        parent=cast(tk.Misc, self)
                    )
                    
                    if response:
                        self.shortcut_manager.bind_shortcut(new_shortcut, force=True)
                        self._shortcuts_data[action_id] = new_shortcut
                        self._update_display()
                else:
                    self._shortcuts_data[action_id] = new_shortcut
                    self._update_display()
            else:
                # Clear shortcut
                old_shortcut = self.shortcut_manager.get_shortcut_for_action(action_id)
                if old_shortcut:
                    self.shortcut_manager.unbind_shortcut(old_shortcut.to_tkinter_sequence())
                
                self._shortcuts_data[action_id] = ShortcutBinding(
                    key="",
                    action_id=action_id,
                    description=action_def.description,
                    scope=action_def.scope
                )
                self._update_display()
    
    def _clear_selected_shortcut(self) -> None:
        """Clear the selected shortcut."""
        action_id = self._get_selected_action_id()
        if not action_id:
            return
        
        old_shortcut = self.shortcut_manager.get_shortcut_for_action(action_id)
        if old_shortcut:
            self.shortcut_manager.unbind_shortcut(old_shortcut.to_tkinter_sequence())
        
        action_def = self.action_registry.get_action(action_id)
        if action_def:
            self._shortcuts_data[action_id] = ShortcutBinding(
                key="",
                action_id=action_id,
                description=action_def.description,
                scope=action_def.scope
            )
            self._update_display()
    
    def _reset_selected_shortcut(self) -> None:
        """Reset selected shortcut to default."""
        action_id = self._get_selected_action_id()
        if not action_id:
            return
        
        action_def = self.action_registry.get_action(action_id)
        if action_def and action_def.default_shortcut:
            default_shortcut = ShortcutBinding.from_string(
                action_def.default_shortcut,
                action_id,
                action_def.description
            )
            default_shortcut.scope = action_def.scope
            
            success, conflict = self.shortcut_manager.bind_shortcut(default_shortcut, force=False)
            
            if not success and conflict:
                    response = messagebox.askyesno(
                        "Shortcut Conflict",
                        f"The default shortcut {default_shortcut.to_display_string()} conflicts with "
                        f"{conflict.existing_binding.action_id}.\\n\\nReplace the existing shortcut?",
                        parent=cast(tk.Misc, self)
                    )
                    
                    if response:
                        self.shortcut_manager.bind_shortcut(default_shortcut, force=True)
                        self._shortcuts_data[action_id] = default_shortcut
                        self._update_display()
            else:
                self._shortcuts_data[action_id] = default_shortcut
                self._update_display()
    
    def _reset_to_defaults(self) -> None:
        """Reset all shortcuts to defaults."""
        response = messagebox.askyesno(
            "Reset Shortcuts",
            "Reset all shortcuts to default values?\\n\\nThis will remove all customizations.",
            parent=cast(tk.Misc, self)
        )
        
        if response:
            self.shortcut_manager.reset_to_defaults()
            self._load_shortcuts()
    
    def _save_shortcuts(self) -> None:
        """Save current shortcut configuration."""
        try:
            success = self.shortcut_manager.save_shortcuts()
            
            if success:
                messagebox.showinfo("Success", "Shortcut configuration saved.", parent=cast(tk.Misc, self))
            else:
                messagebox.showerror("Error", "Failed to save shortcut configuration.", parent=cast(tk.Misc, self))
                
        except Exception as e:
            self.logger.error(f"Failed to save shortcuts: {str(e)}")
            messagebox.showerror("Error", f"Failed to save shortcuts: {str(e)}", parent=cast(tk.Misc, self))