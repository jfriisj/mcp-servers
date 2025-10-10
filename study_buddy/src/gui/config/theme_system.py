"""
Theme System for Study Buddy GUI Application.

Provides customizable visual styling with light/dark mode support, custom colors,
and dynamic theme switching. Follows the Strategy pattern for extensible themes
and integrates with the configuration system for persistence.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, Protocol, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

from gui.config.settings_manager import ThemeConfig, ThemeMode


class StyleProperty(Enum):
    """Theme style properties."""
    # Colors
    PRIMARY_BG = "primary_bg"
    SECONDARY_BG = "secondary_bg"
    ACCENT_BG = "accent_bg"
    PRIMARY_FG = "primary_fg"
    SECONDARY_FG = "secondary_fg"
    ACCENT_FG = "accent_fg"
    BORDER_COLOR = "border_color"
    SELECTION_BG = "selection_bg"
    SELECTION_FG = "selection_fg"
    ERROR_COLOR = "error_color"
    WARNING_COLOR = "warning_color"
    SUCCESS_COLOR = "success_color"
    
    # Fonts
    DEFAULT_FONT = "default_font"
    HEADING_FONT = "heading_font"
    MONO_FONT = "mono_font"
    
    # Dimensions
    PADDING = "padding"
    BORDER_WIDTH = "border_width"
    RELIEF = "relief"


@dataclass
class ColorScheme:
    """Color scheme definition for themes."""
    primary_bg: str
    secondary_bg: str
    accent_bg: str
    primary_fg: str
    secondary_fg: str
    accent_fg: str
    border_color: str
    selection_bg: str
    selection_fg: str
    error_color: str = "#dc3545"
    warning_color: str = "#ffc107"
    success_color: str = "#28a745"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "primary_bg": self.primary_bg,
            "secondary_bg": self.secondary_bg,
            "accent_bg": self.accent_bg,
            "primary_fg": self.primary_fg,
            "secondary_fg": self.secondary_fg,
            "accent_fg": self.accent_fg,
            "border_color": self.border_color,
            "selection_bg": self.selection_bg,
            "selection_fg": self.selection_fg,
            "error_color": self.error_color,
            "warning_color": self.warning_color,
            "success_color": self.success_color
        }


class ThemeProvider(Protocol):
    """Protocol for theme detection (system theme, etc.)."""
    
    def get_system_theme(self) -> ThemeMode:
        """Get current system theme mode."""
        ...


class Theme(ABC):
    """
    Abstract theme base class.
    
    Defines the interface for theme implementations following the Strategy
    pattern. Each theme provides a complete style specification for the GUI.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Get theme name."""
        pass
    
    @abstractmethod
    def get_color_scheme(self) -> ColorScheme:
        """Get theme color scheme."""
        pass
    
    @abstractmethod
    def get_style_properties(self) -> Dict[StyleProperty, Any]:
        """Get complete style property mapping."""
        pass
    
    @abstractmethod
    def configure_ttk_styles(self, style: ttk.Style) -> None:
        """Configure ttk widget styles for this theme."""
        pass


class LightTheme(Theme):
    """Light theme implementation."""
    
    def get_name(self) -> str:
        return "Light"
    
    def get_color_scheme(self) -> ColorScheme:
        return ColorScheme(
            primary_bg="#ffffff",
            secondary_bg="#f8f9fa",
            accent_bg="#e9ecef",
            primary_fg="#212529",
            secondary_fg="#6c757d",
            accent_fg="#0078d4",
            border_color="#dee2e6",
            selection_bg="#0078d4",
            selection_fg="#ffffff"
        )
    
    def get_style_properties(self) -> Dict[StyleProperty, Any]:
        colors = self.get_color_scheme()
        return {
            StyleProperty.PRIMARY_BG: colors.primary_bg,
            StyleProperty.SECONDARY_BG: colors.secondary_bg,
            StyleProperty.ACCENT_BG: colors.accent_bg,
            StyleProperty.PRIMARY_FG: colors.primary_fg,
            StyleProperty.SECONDARY_FG: colors.secondary_fg,
            StyleProperty.ACCENT_FG: colors.accent_fg,
            StyleProperty.BORDER_COLOR: colors.border_color,
            StyleProperty.SELECTION_BG: colors.selection_bg,
            StyleProperty.SELECTION_FG: colors.selection_fg,
            StyleProperty.ERROR_COLOR: colors.error_color,
            StyleProperty.WARNING_COLOR: colors.warning_color,
            StyleProperty.SUCCESS_COLOR: colors.success_color,
            StyleProperty.DEFAULT_FONT: ("Segoe UI", 9),
            StyleProperty.HEADING_FONT: ("Segoe UI", 11, "bold"),
            StyleProperty.MONO_FONT: ("Consolas", 9),
            StyleProperty.PADDING: 8,
            StyleProperty.BORDER_WIDTH: 1,
            StyleProperty.RELIEF: tk.FLAT
        }
    
    def configure_ttk_styles(self, style: ttk.Style) -> None:
        """Configure ttk widget styles for light theme."""
        colors = self.get_color_scheme()
        
        # Configure main styles
        style.configure(".", 
                       background=colors.primary_bg,
                       foreground=colors.primary_fg,
                       fieldbackground=colors.primary_bg,
                       selectbackground=colors.selection_bg,
                       selectforeground=colors.selection_fg,
                       font=("Segoe UI", 9))
        
        # Button styles
        style.configure("Accent.TButton",
                       background=colors.accent_fg,
                       foreground=colors.selection_fg,
                       focuscolor=colors.accent_fg,
                       borderwidth=0,
                       relief=tk.FLAT)
        
        style.map("Accent.TButton",
                 background=[("active", colors.accent_bg),
                           ("pressed", colors.accent_fg)])
        
        # Frame styles
        style.configure("Card.TFrame",
                       background=colors.primary_bg,
                       borderwidth=1,
                       relief=tk.SOLID)
        
        style.configure("Sidebar.TFrame",
                       background=colors.secondary_bg)
        
        # Entry styles
        style.configure("Search.TEntry",
                       fieldbackground=colors.accent_bg,
                       borderwidth=1,
                       relief=tk.FLAT)
        
        # Treeview styles
        style.configure("DocumentList.Treeview",
                       background=colors.primary_bg,
                       foreground=colors.primary_fg,
                       fieldbackground=colors.primary_bg,
                       borderwidth=0,
                       font=("Segoe UI", 9))
        
        style.configure("DocumentList.Treeview.Heading",
                       background=colors.secondary_bg,
                       foreground=colors.primary_fg,
                       borderwidth=1,
                       relief=tk.FLAT)
        
        # Text widget styles (handled separately as it's not ttk)
        style.configure("Content.Text",
                       background=colors.primary_bg,
                       foreground=colors.primary_fg,
                       insertbackground=colors.primary_fg,
                       selectbackground=colors.selection_bg,
                       selectforeground=colors.selection_fg,
                       borderwidth=0,
                       relief=tk.FLAT)


class DarkTheme(Theme):
    """Dark theme implementation."""
    
    def get_name(self) -> str:
        return "Dark"
    
    def get_color_scheme(self) -> ColorScheme:
        return ColorScheme(
            primary_bg="#1e1e1e",
            secondary_bg="#2d2d30",
            accent_bg="#3e3e42",
            primary_fg="#ffffff",
            secondary_fg="#cccccc",
            accent_fg="#0078d4",
            border_color="#464647",
            selection_bg="#0078d4",
            selection_fg="#ffffff"
        )
    
    def get_style_properties(self) -> Dict[StyleProperty, Any]:
        colors = self.get_color_scheme()
        return {
            StyleProperty.PRIMARY_BG: colors.primary_bg,
            StyleProperty.SECONDARY_BG: colors.secondary_bg,
            StyleProperty.ACCENT_BG: colors.accent_bg,
            StyleProperty.PRIMARY_FG: colors.primary_fg,
            StyleProperty.SECONDARY_FG: colors.secondary_fg,
            StyleProperty.ACCENT_FG: colors.accent_fg,
            StyleProperty.BORDER_COLOR: colors.border_color,
            StyleProperty.SELECTION_BG: colors.selection_bg,
            StyleProperty.SELECTION_FG: colors.selection_fg,
            StyleProperty.ERROR_COLOR: colors.error_color,
            StyleProperty.WARNING_COLOR: colors.warning_color,
            StyleProperty.SUCCESS_COLOR: colors.success_color,
            StyleProperty.DEFAULT_FONT: ("Segoe UI", 9),
            StyleProperty.HEADING_FONT: ("Segoe UI", 11, "bold"),
            StyleProperty.MONO_FONT: ("Consolas", 9),
            StyleProperty.PADDING: 8,
            StyleProperty.BORDER_WIDTH: 1,
            StyleProperty.RELIEF: tk.FLAT
        }
    
    def configure_ttk_styles(self, style: ttk.Style) -> None:
        """Configure ttk widget styles for dark theme."""
        colors = self.get_color_scheme()
        
        # Configure main styles
        style.configure(".", 
                       background=colors.primary_bg,
                       foreground=colors.primary_fg,
                       fieldbackground=colors.primary_bg,
                       selectbackground=colors.selection_bg,
                       selectforeground=colors.selection_fg,
                       font=("Segoe UI", 9))
        
        # Button styles
        style.configure("Accent.TButton",
                       background=colors.accent_fg,
                       foreground=colors.selection_fg,
                       focuscolor=colors.accent_fg,
                       borderwidth=0,
                       relief=tk.FLAT)
        
        style.map("Accent.TButton",
                 background=[("active", colors.accent_bg),
                           ("pressed", colors.accent_fg)])
        
        # Frame styles
        style.configure("Card.TFrame",
                       background=colors.primary_bg,
                       borderwidth=1,
                       relief=tk.SOLID)
        
        style.configure("Sidebar.TFrame",
                       background=colors.secondary_bg)
        
        # Entry styles
        style.configure("Search.TEntry",
                       fieldbackground=colors.accent_bg,
                       borderwidth=1,
                       relief=tk.FLAT)
        
        # Treeview styles
        style.configure("DocumentList.Treeview",
                       background=colors.primary_bg,
                       foreground=colors.primary_fg,
                       fieldbackground=colors.primary_bg,
                       borderwidth=0,
                       font=("Segoe UI", 9))
        
        style.configure("DocumentList.Treeview.Heading",
                       background=colors.secondary_bg,
                       foreground=colors.primary_fg,
                       borderwidth=1,
                       relief=tk.FLAT)


class SystemThemeProvider:
    """Provides system theme detection for auto mode."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_system_theme(self) -> ThemeMode:
        """
        Detect system theme mode.
        
        On Windows, reads registry for system theme preference.
        On other systems, defaults to light mode.
        """
        try:
            import sys
            if sys.platform == "win32":
                return self._get_windows_theme()
            else:
                # For now, default to light on non-Windows systems
                # Could be extended to read system themes on Linux/Mac
                return ThemeMode.LIGHT
        except Exception as e:
            self.logger.warning(f"Failed to detect system theme: {str(e)}")
            return ThemeMode.LIGHT
    
    def _get_windows_theme(self) -> ThemeMode:
        """Get Windows system theme from registry."""
        try:
            import winreg
            
            # Read Windows theme setting from registry
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return ThemeMode.LIGHT if value == 1 else ThemeMode.DARK
                
        except Exception as e:
            self.logger.debug(f"Could not read Windows theme registry: {str(e)}")
            return ThemeMode.LIGHT


class ThemeManager:
    """
    Central theme management system.
    
    Handles theme switching, persistence, and widget updates following
    the Observer pattern for theme change notifications. Integrates with
    the configuration system for theme persistence.
    """
    
    def __init__(self, theme_config: ThemeConfig):
        self.config = theme_config
        self.logger = logging.getLogger(__name__)
        
        # Available themes
        self._themes: Dict[str, Theme] = {
            "light": LightTheme(),
            "dark": DarkTheme()
        }
        
        # Current theme state
        self._current_theme: Optional[Theme] = None
        self._ttk_style: Optional[ttk.Style] = None
        
        # System theme provider
        self._system_provider = SystemThemeProvider()
        
        # Theme change listeners
        self._listeners: List[Callable[[Theme], None]] = []
        
        # Initialize theme
        self._update_current_theme()
    
    def initialize(self, root_widget: tk.Tk) -> None:
        """Initialize theme manager with root widget."""
        try:
            # Create ttk style object
            self._ttk_style = ttk.Style(root_widget)
            
            # Apply current theme
            self._apply_theme()
            
            if self._current_theme:
                self.logger.info(f"Theme manager initialized with {self._current_theme.get_name()} theme")
            else:
                self.logger.warning("Theme manager initialized but no current theme set")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize theme manager: {str(e)}")
            raise
    
    def get_current_theme(self) -> Theme:
        """Get currently active theme."""
        if self._current_theme is None:
            self._update_current_theme()
        
        if self._current_theme is None:
            # Fallback to light theme if something went wrong
            self._current_theme = self._themes["light"]
        
        return self._current_theme
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available theme names and display names."""
        return {key: theme.get_name() for key, theme in self._themes.items()}
    
    def set_theme_mode(self, mode: ThemeMode) -> None:
        """Set theme mode and update configuration."""
        try:
            old_mode = self.config.mode
            self.config.mode = mode
            
            self._update_current_theme()
            self._apply_theme()
            
            self.logger.info(f"Theme mode changed from {old_mode} to {mode}")
            
        except Exception as e:
            self.logger.error(f"Failed to set theme mode: {str(e)}")
            raise
    
    def update_custom_colors(self, colors: Dict[str, str]) -> None:
        """Update custom color overrides."""
        try:
            self.config.custom_colors.update(colors)
            self._apply_theme()
            
            self.logger.info("Custom colors updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update custom colors: {str(e)}")
            raise
    
    def get_style_property(self, prop: StyleProperty) -> Any:
        """Get current theme style property."""
        theme = self.get_current_theme()
        properties = theme.get_style_properties()
        
        # Apply custom color overrides
        if prop in [StyleProperty.PRIMARY_BG, StyleProperty.ACCENT_FG] and self.config.custom_colors:
            prop_name = prop.value
            if prop_name in self.config.custom_colors:
                return self.config.custom_colors[prop_name]
        
        return properties.get(prop)
    
    def get_color_scheme(self) -> ColorScheme:
        """Get current color scheme with custom overrides."""
        theme = self.get_current_theme()
        scheme = theme.get_color_scheme()
        
        # Apply custom colors
        if self.config.custom_colors:
            scheme_dict = scheme.to_dict()
            scheme_dict.update(self.config.custom_colors)
            # Would need a ColorScheme.from_dict method for this
        
        return scheme
    
    def add_theme_listener(self, callback: Callable[[Theme], None]) -> None:
        """Add callback for theme changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_theme_listener(self, callback: Callable[[Theme], None]) -> None:
        """Remove theme change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def configure_widget(self, widget: tk.Widget, style_name: str) -> None:
        """Configure widget with current theme styles."""
        try:
            theme = self.get_current_theme()
            properties = theme.get_style_properties()
            
            # Apply common properties based on widget type
            if isinstance(widget, (tk.Frame, tk.Toplevel)):
                widget.configure(
                    bg=properties[StyleProperty.PRIMARY_BG],
                    relief=properties[StyleProperty.RELIEF],
                    borderwidth=properties[StyleProperty.BORDER_WIDTH]
                )
            elif isinstance(widget, (tk.Label, tk.Button)):
                widget.configure(
                    bg=properties[StyleProperty.PRIMARY_BG],
                    fg=properties[StyleProperty.PRIMARY_FG],
                    font=properties[StyleProperty.DEFAULT_FONT],
                    relief=properties[StyleProperty.RELIEF]
                )
            elif isinstance(widget, tk.Text):
                widget.configure(
                    bg=properties[StyleProperty.PRIMARY_BG],
                    fg=properties[StyleProperty.PRIMARY_FG],
                    insertbackground=properties[StyleProperty.PRIMARY_FG],
                    selectbackground=properties[StyleProperty.SELECTION_BG],
                    selectforeground=properties[StyleProperty.SELECTION_FG],
                    font=properties[StyleProperty.DEFAULT_FONT],
                    borderwidth=0,
                    relief=tk.FLAT
                )
            
            self.logger.debug(f"Configured widget {widget} with {style_name} style")
            
        except Exception as e:
            self.logger.warning(f"Failed to configure widget {widget}: {str(e)}")
    
    def _update_current_theme(self) -> None:
        """Update current theme based on configuration."""
        if self.config.mode == ThemeMode.AUTO:
            # Use system theme detection
            system_mode = self._system_provider.get_system_theme()
            theme_key = "dark" if system_mode == ThemeMode.DARK else "light"
        elif self.config.mode == ThemeMode.DARK:
            theme_key = "dark"
        else:
            theme_key = "light"
        
        old_theme = self._current_theme
        self._current_theme = self._themes[theme_key]
        
        # Notify listeners if theme changed
        if old_theme != self._current_theme:
            for listener in self._listeners:
                try:
                    listener(self._current_theme)
                except Exception as e:
                    self.logger.error(f"Theme listener error: {str(e)}")
    
    def _apply_theme(self) -> None:
        """Apply current theme to ttk styles."""
        if self._ttk_style and self._current_theme:
            try:
                self._current_theme.configure_ttk_styles(self._ttk_style)
                self.logger.debug(f"Applied {self._current_theme.get_name()} theme styles")
            except Exception as e:
                self.logger.error(f"Failed to apply theme styles: {str(e)}")


class ThemeService:
    """
    High-level theme service for GUI components.
    
    Provides a clean interface for theme operations following Clean Architecture
    principles. Acts as a facade over the theme manager and configuration system.
    """
    
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        self.logger = logging.getLogger(__name__)
    
    def get_current_colors(self) -> ColorScheme:
        """Get current color scheme."""
        return self.theme_manager.get_color_scheme()
    
    def get_style_value(self, property_name: StyleProperty) -> Any:
        """Get style property value."""
        return self.theme_manager.get_style_property(property_name)
    
    def apply_to_widget(self, widget: tk.Widget, style_name: str = "default") -> None:
        """Apply current theme to widget."""
        self.theme_manager.configure_widget(widget, style_name)
    
    def switch_theme_mode(self, mode: ThemeMode) -> None:
        """Switch to different theme mode."""
        self.theme_manager.set_theme_mode(mode)
    
    def add_change_listener(self, callback: Callable[[Theme], None]) -> None:
        """Add theme change listener."""
        self.theme_manager.add_theme_listener(callback)