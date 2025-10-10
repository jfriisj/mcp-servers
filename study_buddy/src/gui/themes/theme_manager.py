"""
Enhanced Theme Management System for Study Buddy GUI Application.

Extends the existing theme system with JSON-based theme loading, responsive design,
accessibility features, and custom theme management. Follows Clean Architecture
and SOLID principles for maintainable and extensible theme management.
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os

from gui.config.settings_manager import SettingsManager


class ScreenSize(Enum):
    """Screen size categories for responsive design."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class AccessibilityLevel(Enum):
    """Accessibility compliance levels."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    WCAG_AA = "wcag_aa"
    WCAG_AAA = "wcag_aaa"


@dataclass
class ThemeMetadata:
    """Theme metadata for identification and management."""
    name: str
    version: str
    description: str
    author: str
    tags: List[str]
    created_date: Optional[str] = None
    modified_date: Optional[str] = None


@dataclass
class ResponsiveConfig:
    """Responsive design configuration."""
    breakpoints: Dict[str, int]
    font_scale: Dict[str, float]
    padding_scale: Dict[str, float]


@dataclass
class AccessibilityConfig:
    """Accessibility configuration settings."""
    high_contrast: bool
    font_scaling: float
    focus_highlight: bool
    keyboard_navigation: bool
    screen_reader_support: bool
    minimum_contrast_ratio: float = 4.5


class JSONThemeLoader:
    """
    Loads and validates themes from JSON files.
    
    Responsibilities:
    - Load theme configurations from JSON files
    - Validate theme structure and values
    - Handle loading errors gracefully
    - Support theme file discovery
    
    SOLID Compliance:
    - SRP: Only handles JSON theme loading
    - OCP: Extensible for new theme file formats
    - DIP: Depends on abstractions, not file system directly
    """
    
    def __init__(self, themes_directory: Path):
        self.themes_directory = Path(themes_directory)
        self.logger = logging.getLogger(__name__)
        
        # Ensure themes directory exists
        self.themes_directory.mkdir(parents=True, exist_ok=True)
    
    def load_theme(self, theme_file: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Load theme from JSON file.
        
        Args:
            theme_file: Path to theme JSON file
            
        Returns:
            Theme configuration dictionary or None if failed
        """
        try:
            theme_path = Path(theme_file)
            if not theme_path.is_absolute():
                theme_path = self.themes_directory / theme_path
            
            if not theme_path.exists():
                self.logger.error(f"Theme file not found: {theme_path}")
                return None
            
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # Validate theme structure
            if self._validate_theme_structure(theme_data):
                self.logger.info(f"Successfully loaded theme: {theme_path.name}")
                return theme_data
            else:
                self.logger.error(f"Invalid theme structure: {theme_path.name}")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error in {theme_file}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load theme {theme_file}: {str(e)}")
            return None
    
    def save_theme(self, theme_data: Dict[str, Any], theme_file: Union[str, Path]) -> bool:
        """
        Save theme to JSON file.
        
        Args:
            theme_data: Theme configuration dictionary
            theme_file: Path to save theme file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            theme_path = Path(theme_file)
            if not theme_path.is_absolute():
                theme_path = self.themes_directory / theme_path
            
            # Validate before saving
            if not self._validate_theme_structure(theme_data):
                self.logger.error("Cannot save invalid theme structure")
                return False
            
            # Ensure directory exists
            theme_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved theme: {theme_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save theme {theme_file}: {str(e)}")
            return False
    
    def discover_themes(self) -> List[Path]:
        """
        Discover all theme files in themes directory.
        
        Returns:
            List of theme file paths
        """
        theme_files = []
        try:
            for file_path in self.themes_directory.glob("*.json"):
                if file_path.is_file():
                    theme_files.append(file_path)
            
            self.logger.info(f"Discovered {len(theme_files)} theme files")
            return sorted(theme_files)
            
        except Exception as e:
            self.logger.error(f"Failed to discover themes: {str(e)}")
            return []
    
    def _validate_theme_structure(self, theme_data: Dict[str, Any]) -> bool:
        """
        Validate theme JSON structure.
        
        Args:
            theme_data: Theme configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ['theme_info', 'colors', 'fonts', 'dimensions']
        
        try:
            # Check required sections exist
            for section in required_sections:
                if section not in theme_data:
                    self.logger.error(f"Missing required section: {section}")
                    return False
            
            # Validate theme_info
            theme_info = theme_data['theme_info']
            required_info_fields = ['name', 'version', 'description']
            for field in required_info_fields:
                if field not in theme_info:
                    self.logger.error(f"Missing theme_info field: {field}")
                    return False
            
            # Validate colors section
            colors = theme_data['colors']
            required_colors = ['primary_bg', 'primary_fg', 'secondary_bg', 'secondary_fg']
            for color in required_colors:
                if color not in colors:
                    self.logger.error(f"Missing required color: {color}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Theme validation error: {str(e)}")
            return False


class ResponsiveManager:
    """
    Manages responsive design for different screen sizes.
    
    Responsibilities:
    - Detect current screen size and resolution
    - Calculate responsive scaling factors
    - Apply responsive adjustments to widgets
    - Handle window resize events
    
    SOLID Compliance:
    - SRP: Only handles responsive design logic
    - OCP: Extensible for new screen size categories
    - LSP: Consistent interface for all responsive operations
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = logging.getLogger(__name__)
        self._current_size = ScreenSize.MEDIUM
        self._scale_factor = 1.0
        self._listeners = []
        
        # Bind to window configuration changes
        self.root.bind('<Configure>', self._on_window_configure)
        
        # Initial size detection
        self._detect_screen_size()
    
    def get_current_screen_size(self) -> ScreenSize:
        """Get current screen size category."""
        return self._current_size
    
    def get_scale_factor(self) -> float:
        """Get current scaling factor."""
        return self._scale_factor
    
    def calculate_responsive_value(
        self, 
        base_value: Union[int, float], 
        responsive_config: ResponsiveConfig,
        value_type: str = "font"
    ) -> Union[int, float]:
        """
        Calculate responsive value based on current screen size.
        
        Args:
            base_value: Base value to scale
            responsive_config: Responsive configuration
            value_type: Type of value (font, padding, etc.)
            
        Returns:
            Scaled value for current screen size
        """
        try:
            size_key = self._current_size.value
            
            if value_type == "font":
                scale = responsive_config.font_scale.get(size_key, 1.0)
            elif value_type == "padding":
                scale = responsive_config.padding_scale.get(size_key, 1.0)
            else:
                scale = 1.0
            
            result = base_value * scale
            
            # Ensure minimum values
            if value_type == "font" and result < 8:
                result = 8
            elif value_type == "padding" and result < 2:
                result = 2
            
            return int(result) if isinstance(base_value, int) else result
            
        except Exception as e:
            self.logger.error(f"Failed to calculate responsive value: {str(e)}")
            return base_value
    
    def add_resize_listener(self, callback):
        """Add listener for screen size changes."""
        self._listeners.append(callback)
    
    def _detect_screen_size(self) -> None:
        """Detect current screen size category."""
        try:
            window_width = self.root.winfo_width()
            
            # If window not realized yet, use screen dimensions
            if window_width <= 1:
                window_width = self.root.winfo_screenwidth()
            
            old_size = self._current_size
            
            if window_width < 800:
                self._current_size = ScreenSize.SMALL
                self._scale_factor = 0.9
            elif window_width < 1200:
                self._current_size = ScreenSize.MEDIUM
                self._scale_factor = 1.0
            else:
                self._current_size = ScreenSize.LARGE
                self._scale_factor = 1.1
            
            # Notify listeners if size changed
            if old_size != self._current_size:
                self.logger.info(f"Screen size changed: {self._current_size.value}")
                for listener in self._listeners:
                    try:
                        listener(self._current_size, self._scale_factor)
                    except Exception as e:
                        self.logger.error(f"Resize listener error: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Failed to detect screen size: {str(e)}")
    
    def _on_window_configure(self, event) -> None:
        """Handle window configuration changes."""
        # Only handle main window resize events
        if event.widget == self.root:
            self._detect_screen_size()


class AccessibilityManager:
    """
    Manages accessibility features and compliance.
    
    Responsibilities:
    - Handle accessibility settings and preferences
    - Apply accessibility enhancements to widgets
    - Validate color contrast ratios
    - Manage keyboard navigation and focus
    
    SOLID Compliance:
    - SRP: Only handles accessibility features
    - OCP: Extensible for new accessibility standards
    - DIP: Depends on accessibility configuration interface
    """
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)
        self._accessibility_config = AccessibilityConfig(
            high_contrast=False,
            font_scaling=1.0,
            focus_highlight=True,
            keyboard_navigation=True,
            screen_reader_support=True
        )
    
    def get_accessibility_config(self) -> AccessibilityConfig:
        """Get current accessibility configuration."""
        return self._accessibility_config
    
    def set_font_scaling(self, scale_factor: float) -> None:
        """
        Set font scaling factor for accessibility.
        
        Args:
            scale_factor: Font scaling factor (0.8-2.0)
        """
        # Clamp scaling factor to reasonable range
        scale_factor = max(0.8, min(2.0, scale_factor))
        self._accessibility_config.font_scaling = scale_factor
        
        # Save to settings
        self.settings_manager.set_setting('accessibility.font_scaling', scale_factor)
        self.logger.info(f"Font scaling set to {scale_factor}")
    
    def enable_high_contrast(self, enabled: bool) -> None:
        """
        Enable or disable high contrast mode.
        
        Args:
            enabled: True to enable high contrast mode
        """
        self._accessibility_config.high_contrast = enabled
        self.settings_manager.set_setting('accessibility.high_contrast', enabled)
        self.logger.info(f"High contrast mode {'enabled' if enabled else 'disabled'}")
    
    def calculate_accessible_font_size(self, base_size: int) -> int:
        """
        Calculate accessible font size with scaling applied.
        
        Args:
            base_size: Base font size
            
        Returns:
            Scaled font size for accessibility
        """
        scaled_size = int(base_size * self._accessibility_config.font_scaling)
        return max(8, scaled_size)  # Minimum readable size
    
    def validate_color_contrast(
        self, 
        foreground: str, 
        background: str,
        level: AccessibilityLevel = AccessibilityLevel.WCAG_AA
    ) -> bool:
        """
        Validate color contrast ratio for accessibility compliance.
        
        Args:
            foreground: Foreground color (hex format)
            background: Background color (hex format)
            level: Accessibility compliance level
            
        Returns:
            True if contrast ratio meets requirements
        """
        try:
            # Calculate contrast ratio (simplified implementation)
            fg_luminance = self._calculate_luminance(foreground)
            bg_luminance = self._calculate_luminance(background)
            
            # Calculate contrast ratio
            if fg_luminance > bg_luminance:
                contrast_ratio = (fg_luminance + 0.05) / (bg_luminance + 0.05)
            else:
                contrast_ratio = (bg_luminance + 0.05) / (fg_luminance + 0.05)
            
            # Check against requirements
            if level == AccessibilityLevel.WCAG_AAA:
                return contrast_ratio >= 7.0
            elif level == AccessibilityLevel.WCAG_AA:
                return contrast_ratio >= 4.5
            else:
                return contrast_ratio >= 3.0
                
        except Exception as e:
            self.logger.error(f"Failed to validate color contrast: {str(e)}")
            return False
    
    def _calculate_luminance(self, color: str) -> float:
        """
        Calculate relative luminance of a color.
        
        Args:
            color: Color in hex format (#RRGGBB)
            
        Returns:
            Relative luminance value (0.0-1.0)
        """
        try:
            # Remove # prefix if present
            color = color.lstrip('#')
            
            # Convert to RGB values
            r = int(color[0:2], 16) / 255.0
            g = int(color[2:4], 16) / 255.0
            b = int(color[4:6], 16) / 255.0
            
            # Apply gamma correction
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            
            # Calculate luminance
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
        except Exception as e:
            self.logger.error(f"Failed to calculate luminance for {color}: {str(e)}")
            return 0.5  # Default mid-range value


class CustomThemeManager:
    """
    Manages custom theme creation, import, and export.
    
    Responsibilities:
    - Create new themes from templates
    - Import themes from external files
    - Export themes to shareable files
    - Manage user theme library
    
    SOLID Compliance:
    - SRP: Only handles custom theme management
    - OCP: Extensible for new theme formats
    - DIP: Uses theme loader abstraction
    """
    
    def __init__(self, theme_loader: JSONThemeLoader):
        self.theme_loader = theme_loader
        self.logger = logging.getLogger(__name__)
    
    def create_theme_from_template(
        self, 
        template_name: str, 
        new_theme_info: ThemeMetadata,
        color_overrides: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create new theme from existing template.
        
        Args:
            template_name: Name of template theme file
            new_theme_info: Metadata for new theme
            color_overrides: Optional color customizations
            
        Returns:
            New theme configuration or None if failed
        """
        try:
            # Load template theme
            template_path = f"{template_name}.json"
            template_data = self.theme_loader.load_theme(template_path)
            
            if not template_data:
                self.logger.error(f"Failed to load template: {template_name}")
                return None
            
            # Create new theme from template
            new_theme = template_data.copy()
            
            # Update theme info
            new_theme['theme_info'] = asdict(new_theme_info)
            
            # Apply color overrides if provided
            if color_overrides:
                new_theme['colors'].update(color_overrides)
            
            self.logger.info(f"Created new theme: {new_theme_info.name}")
            return new_theme
            
        except Exception as e:
            self.logger.error(f"Failed to create theme from template: {str(e)}")
            return None
    
    def import_theme(self, source_file: Path) -> bool:
        """
        Import theme from external file.
        
        Args:
            source_file: Path to theme file to import
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load theme from source file
            theme_data = self.theme_loader.load_theme(source_file)
            
            if not theme_data:
                return False
            
            # Generate destination filename
            theme_name = theme_data.get('theme_info', {}).get('name', 'imported_theme')
            safe_name = "".join(c for c in theme_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            dest_file = f"{safe_name.lower().replace(' ', '_')}.json"
            
            # Save to themes directory
            success = self.theme_loader.save_theme(theme_data, dest_file)
            
            if success:
                self.logger.info(f"Successfully imported theme: {theme_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to import theme: {str(e)}")
            return False
    
    def export_theme(self, theme_name: str, destination: Path) -> bool:
        """
        Export theme to external file.
        
        Args:
            theme_name: Name of theme to export
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load theme
            theme_file = f"{theme_name}.json"
            theme_data = self.theme_loader.load_theme(theme_file)
            
            if not theme_data:
                return False
            
            # Save to destination
            with open(destination, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully exported theme: {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export theme: {str(e)}")
            return False
    
    def get_user_themes(self) -> List[Dict[str, Any]]:
        """
        Get list of available user themes.
        
        Returns:
            List of theme metadata dictionaries
        """
        user_themes = []
        
        try:
            theme_files = self.theme_loader.discover_themes()
            
            for theme_file in theme_files:
                theme_data = self.theme_loader.load_theme(theme_file)
                if theme_data and 'theme_info' in theme_data:
                    theme_info = theme_data['theme_info'].copy()
                    theme_info['file_path'] = str(theme_file)
                    user_themes.append(theme_info)
            
            self.logger.info(f"Found {len(user_themes)} user themes")
            return user_themes
            
        except Exception as e:
            self.logger.error(f"Failed to get user themes: {str(e)}")
            return []