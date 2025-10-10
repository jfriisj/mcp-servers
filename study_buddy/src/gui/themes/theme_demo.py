"""
Theme System Integration Demo for Study Buddy GUI Application.

Demonstrates how to integrate the enhanced theme system with existing GUI components
and provides examples of theme usage throughout the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from gui.config.settings_manager import SettingsManager
from gui.themes.enhanced_theme_system import (
    EnhancedThemeSystem,
    apply_theme_to_widget,
    get_theme_color,
    create_enhanced_theme_system
)


class ThemeDemo(tk.Frame):
    """
    Demonstration of the enhanced theme system capabilities.
    
    Shows how to:
    - Load and switch between themes
    - Create custom themes
    - Import/export themes
    - Use responsive design features
    - Apply accessibility settings
    """
    
    def __init__(self, parent: tk.Misc, theme_system: EnhancedThemeSystem):
        super().__init__(parent)
        self.theme_system = theme_system
        self.logger = logging.getLogger(__name__)
        
        # Add theme change listener
        self.theme_system.add_theme_change_listener(self._on_theme_changed)
        
        self._create_widgets()
        self._layout_widgets()
        
        # Apply initial theme
        self._apply_theme()
    
    def _create_widgets(self) -> None:
        """Create demo widgets."""
        # Theme selection frame
        self.theme_frame = ttk.LabelFrame(self, text="Theme Selection")
        
        # Available themes
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(
            self.theme_frame,
            textvariable=self.theme_var,
            state="readonly"
        )
        self.theme_combo.bind('<<ComboboxSelected>>', self._on_theme_selected)
        
        # Load themes button
        self.load_themes_btn = ttk.Button(
            self.theme_frame,
            text="Refresh Themes",
            command=self._load_available_themes
        )
        
        # Theme management frame
        self.management_frame = ttk.LabelFrame(self, text="Theme Management")
        
        # Create custom theme
        self.create_theme_btn = ttk.Button(
            self.management_frame,
            text="Create Custom Theme",
            command=self._create_custom_theme
        )
        
        # Import theme
        self.import_theme_btn = ttk.Button(
            self.management_frame,
            text="Import Theme",
            command=self.theme_system.import_theme_file
        )
        
        # Export theme
        self.export_theme_btn = ttk.Button(
            self.management_frame,
            text="Export Current Theme",
            command=self._export_current_theme
        )
        
        # Accessibility frame
        self.accessibility_frame = ttk.LabelFrame(self, text="Accessibility Settings")
        
        # Font scaling
        ttk.Label(self.accessibility_frame, text="Font Scaling:").grid(row=0, column=0, sticky="w")
        self.font_scale_var = tk.DoubleVar(value=1.0)
        self.font_scale_slider = ttk.Scale(
            self.accessibility_frame,
            from_=0.8,
            to=2.0,
            variable=self.font_scale_var,
            orient="horizontal",
            command=self._on_font_scale_changed
        )
        
        # High contrast toggle
        self.high_contrast_var = tk.BooleanVar()
        self.high_contrast_check = ttk.Checkbutton(
            self.accessibility_frame,
            text="High Contrast Mode",
            variable=self.high_contrast_var,
            command=self._on_high_contrast_toggled
        )
        
        # Demo content frame
        self.demo_frame = ttk.LabelFrame(self, text="Theme Preview")
        
        # Various widgets to demonstrate theming
        self.demo_label = tk.Label(
            self.demo_frame,
            text="Sample Label Text",
            font=("Arial", 12)
        )
        
        self.demo_button = tk.Button(
            self.demo_frame,
            text="Sample Button",
            command=lambda: messagebox.showinfo("Demo", "Button clicked!")
        )
        
        self.demo_entry = tk.Entry(
            self.demo_frame,
            font=("Arial", 10)
        )
        self.demo_entry.insert(0, "Sample text input")
        
        self.demo_text = tk.Text(
            self.demo_frame,
            height=4,
            width=40,
            font=("Consolas", 9)
        )
        self.demo_text.insert("1.0", "Sample text area content\\nWith multiple lines\\nTo show theming effects")
        
        # Responsive info
        self.responsive_frame = ttk.LabelFrame(self, text="Responsive Information")
        self.screen_info_label = tk.Label(
            self.responsive_frame,
            text="Screen size info will appear here",
            font=("Arial", 10)
        )
        
        # Update screen info
        self._update_screen_info()
    
    def _layout_widgets(self) -> None:
        """Layout demo widgets."""
        # Theme selection
        self.theme_frame.pack(fill="x", padx=5, pady=5)
        self.theme_combo.pack(side="left", padx=5, pady=5)
        self.load_themes_btn.pack(side="right", padx=5, pady=5)
        
        # Theme management
        self.management_frame.pack(fill="x", padx=5, pady=5)
        self.create_theme_btn.pack(side="left", padx=5, pady=5)
        self.import_theme_btn.pack(side="left", padx=5, pady=5)
        self.export_theme_btn.pack(side="left", padx=5, pady=5)
        
        # Accessibility
        self.accessibility_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(self.accessibility_frame, text="Font Scaling:").grid(row=0, column=0, sticky="w", padx=5)
        self.font_scale_slider.grid(row=0, column=1, sticky="ew", padx=5)
        self.high_contrast_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        self.accessibility_frame.grid_columnconfigure(1, weight=1)
        
        # Demo content
        self.demo_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.demo_label.pack(pady=5)
        self.demo_button.pack(pady=5)
        self.demo_entry.pack(pady=5)
        self.demo_text.pack(pady=5, fill="both", expand=True)
        
        # Responsive info
        self.responsive_frame.pack(fill="x", padx=5, pady=5)
        self.screen_info_label.pack(padx=5, pady=5)
        
        # Load initial themes
        self._load_available_themes()
    
    def _load_available_themes(self) -> None:
        """Load and display available themes."""
        try:
            themes = self.theme_system.get_available_themes()
            theme_names = [theme['name'] for theme in themes]
            
            self.theme_combo['values'] = theme_names
            
            if theme_names and not self.theme_var.get():
                self.theme_var.set(theme_names[0])
            
            self.logger.info(f"Loaded {len(theme_names)} themes")
            
        except Exception as e:
            self.logger.error(f"Failed to load themes: {str(e)}")
            messagebox.showerror("Error", f"Failed to load themes: {str(e)}")
    
    def _on_theme_selected(self, event=None) -> None:
        """Handle theme selection."""
        theme_name = self.theme_var.get()
        if theme_name:
            # Convert display name to file name
            safe_name = theme_name.lower().replace(' ', '_').replace('study_buddy_', '')
            if safe_name == "study_buddy_light":
                safe_name = "light"
            elif safe_name == "study_buddy_dark":
                safe_name = "dark"
            elif safe_name == "study_buddy_high_contrast":
                safe_name = "high-contrast"
            
            success = self.theme_system.load_theme(safe_name)
            if not success:
                messagebox.showerror("Error", f"Failed to load theme: {theme_name}")
    
    def _create_custom_theme(self) -> None:
        """Create a custom theme."""
        try:
            # Simple dialog for custom theme creation
            dialog = CustomThemeDialog(self, self.theme_system)
            self.wait_window(dialog)
            
            # Refresh theme list
            self._load_available_themes()
            
        except Exception as e:
            self.logger.error(f"Failed to create custom theme: {str(e)}")
            messagebox.showerror("Error", f"Failed to create custom theme: {str(e)}")
    
    def _export_current_theme(self) -> None:
        """Export the current theme."""
        current_theme = self.theme_var.get()
        if current_theme:
            # Convert display name to file name
            safe_name = current_theme.lower().replace(' ', '_').replace('study_buddy_', '')
            self.theme_system.export_theme(safe_name)
        else:
            messagebox.showwarning("Warning", "No theme selected to export.")
    
    def _on_font_scale_changed(self, value) -> None:
        """Handle font scaling changes."""
        scale_factor = float(value)
        self.theme_system.set_accessibility_font_scaling(scale_factor)
    
    def _on_high_contrast_toggled(self) -> None:
        """Handle high contrast mode toggle."""
        self.theme_system.toggle_high_contrast_mode()
    
    def _on_theme_changed(self, theme_data: Dict[str, Any]) -> None:
        """Handle theme changes."""
        self._apply_theme()
        self._update_screen_info()
    
    def _apply_theme(self) -> None:
        """Apply current theme to demo widgets."""
        # Apply theme to demo widgets
        demo_widgets = [
            self.demo_label,
            self.demo_button,
            self.demo_entry,
            self.demo_text,
            self.screen_info_label
        ]
        
        for widget in demo_widgets:
            apply_theme_to_widget(widget, self.theme_system)
    
    def _update_screen_info(self) -> None:
        """Update responsive design information."""
        screen_size = self.theme_system.responsive_manager.get_current_screen_size()
        scale_factor = self.theme_system.responsive_manager.get_scale_factor()
        
        # Sample font size calculation
        base_font_size = 12
        responsive_font_size = self.theme_system.get_responsive_font_size(base_font_size)
        
        # Sample padding calculation
        base_padding = 8
        responsive_padding = self.theme_system.get_responsive_padding(base_padding)
        
        info_text = (
            f"Screen Size: {screen_size.value.title()}\\n"
            f"Scale Factor: {scale_factor:.1f}\\n"
            f"Font Size: {base_font_size} → {responsive_font_size}\\n"
            f"Padding: {base_padding} → {responsive_padding}"
        )
        
        self.screen_info_label.configure(text=info_text)


class CustomThemeDialog(tk.Toplevel):
    """Dialog for creating custom themes."""
    
    def __init__(self, parent: tk.Widget, theme_system: EnhancedThemeSystem):
        super().__init__(parent)
        self.theme_system = theme_system
        self.result = None
        
        self.title("Create Custom Theme")
        self.geometry("400x300")
        self.resizable(False, False)
        if hasattr(parent, 'winfo_toplevel'):
            self.transient(parent.winfo_toplevel())
        self.grab_set()
        
        self._create_widgets()
        self._layout_widgets()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Theme name
        ttk.Label(self, text="Theme Name:").pack(anchor="w", padx=10, pady=(10, 5))
        self.name_var = tk.StringVar(value="My Custom Theme")
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, width=40)
        
        # Description
        ttk.Label(self, text="Description:").pack(anchor="w", padx=10, pady=(10, 5))
        self.desc_var = tk.StringVar(value="Custom theme created by user")
        self.desc_entry = ttk.Entry(self, textvariable=self.desc_var, width=40)
        
        # Base theme
        ttk.Label(self, text="Base Theme:").pack(anchor="w", padx=10, pady=(10, 5))
        self.base_var = tk.StringVar(value="light")
        self.base_combo = ttk.Combobox(
            self,
            textvariable=self.base_var,
            values=["light", "dark", "high-contrast"],
            state="readonly",
            width=37
        )
        
        # Color customization (simplified)
        ttk.Label(self, text="Primary Background Color:").pack(anchor="w", padx=10, pady=(10, 5))
        self.bg_color_var = tk.StringVar(value="#FFFFFF")
        self.bg_color_entry = ttk.Entry(self, textvariable=self.bg_color_var, width=40)
        
        ttk.Label(self, text="Primary Text Color:").pack(anchor="w", padx=10, pady=(10, 5))
        self.fg_color_var = tk.StringVar(value="#000000")
        self.fg_color_entry = ttk.Entry(self, textvariable=self.fg_color_var, width=40)
        
        # Buttons
        self.button_frame = ttk.Frame(self)
        self.create_btn = ttk.Button(
            self.button_frame,
            text="Create Theme",
            command=self._create_theme
        )
        self.cancel_btn = ttk.Button(
            self.button_frame,
            text="Cancel",
            command=self.destroy
        )
    
    def _layout_widgets(self) -> None:
        """Layout dialog widgets."""
        self.name_entry.pack(padx=10, pady=(0, 5), fill="x")
        self.desc_entry.pack(padx=10, pady=(0, 5), fill="x")
        self.base_combo.pack(padx=10, pady=(0, 5), fill="x")
        self.bg_color_entry.pack(padx=10, pady=(0, 5), fill="x")
        self.fg_color_entry.pack(padx=10, pady=(0, 15), fill="x")
        
        self.button_frame.pack(fill="x", padx=10, pady=10)
        self.cancel_btn.pack(side="right", padx=(5, 0))
        self.create_btn.pack(side="right")
    
    def _create_theme(self) -> None:
        """Create the custom theme."""
        try:
            theme_name = self.name_var.get().strip()
            description = self.desc_var.get().strip()
            base_theme = self.base_var.get()
            
            if not theme_name:
                messagebox.showerror("Error", "Please enter a theme name.")
                return
            
            # Color customizations
            color_overrides = {
                "primary_bg": self.bg_color_var.get(),
                "primary_fg": self.fg_color_var.get()
            }
            
            success = self.theme_system.create_custom_theme(
                base_theme,
                theme_name,
                description,
                color_overrides
            )
            
            if success:
                messagebox.showinfo("Success", f"Theme '{theme_name}' created successfully!")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to create theme.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create theme: {str(e)}")


# Example integration with main application
def integrate_theme_system_with_app(app_root: tk.Tk) -> EnhancedThemeSystem:
    """
    Example of how to integrate the enhanced theme system with the main application.
    
    Args:
        app_root: Main application window
        
    Returns:
        Configured theme system instance
    """
    # Initialize settings manager with concrete implementation
    from gui.config.settings_manager import FileSettingsManager
    settings_manager = FileSettingsManager()
    
    # Create enhanced theme system
    theme_system = create_enhanced_theme_system(
        app_root,
        settings_manager,
        Path(__file__).parent  # Use themes directory
    )
    
    # Load default theme
    theme_system.load_theme("light")
    
    return theme_system


# Demo application
def main():
    """Run theme system demo application."""
    root = tk.Tk()
    root.title("Study Buddy - Theme System Demo")
    root.geometry("800x600")
    
    try:
        # Initialize theme system
        theme_system = integrate_theme_system_with_app(root)
        
        # Create demo interface
        demo = ThemeDemo(root, theme_system)
        demo.pack(fill="both", expand=True)
        
        # Start application
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Failed to start theme demo: {str(e)}")
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")


if __name__ == "__main__":
    main()