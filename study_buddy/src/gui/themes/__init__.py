"""
Enhanced Theme System for Study Buddy GUI Application.

Provides comprehensive theme management with JSON configuration, responsive design,
accessibility features, and custom theme creation capabilities.

This module completes Task 13: UI Theme and Styling System by extending the
existing theme system with enhanced features while maintaining SOLID principles.
"""

# Core theme management components
from gui.themes.theme_manager import (
    JSONThemeLoader,
    ResponsiveManager,
    AccessibilityManager,
    CustomThemeManager,
    ScreenSize,
    AccessibilityLevel,
    ThemeMetadata,
    ResponsiveConfig,
    AccessibilityConfig,
)

# Integrated theme system
from gui.themes.enhanced_theme_system import (
    EnhancedThemeSystem,
    create_enhanced_theme_system,
    apply_theme_to_widget,
    get_theme_color,
)

# Demo and integration utilities
from gui.themes.theme_demo import (
    ThemeDemo,
    CustomThemeDialog,
    integrate_theme_system_with_app,
)

__all__ = [
    # Core Components
    "JSONThemeLoader",
    "ResponsiveManager", 
    "AccessibilityManager",
    "CustomThemeManager",
    
    # Data Classes and Enums
    "ScreenSize",
    "AccessibilityLevel",
    "ThemeMetadata",
    "ResponsiveConfig",
    "AccessibilityConfig",
    
    # Integrated System
    "EnhancedThemeSystem",
    "create_enhanced_theme_system",
    
    # Utility Functions
    "apply_theme_to_widget",
    "get_theme_color",
    
    # Demo and Integration
    "ThemeDemo",
    "CustomThemeDialog", 
    "integrate_theme_system_with_app",
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "Study Buddy Development Team"
__description__ = "Enhanced theme system with JSON configuration, responsive design, and accessibility"

# Quick start guide in docstring
__doc__ = """
Enhanced Theme System - Quick Start Guide

1. Basic Setup:
   ```python
   from gui.themes import create_enhanced_theme_system
   
   theme_system = create_enhanced_theme_system(root, settings_manager)
   theme_system.load_theme("light")
   ```

2. Apply Theme to Widgets:
   ```python
   from gui.themes import apply_theme_to_widget
   
   apply_theme_to_widget(my_label, theme_system)
   ```

3. Get Theme Colors:
   ```python
   from gui.themes import get_theme_color
   
   bg_color = get_theme_color(theme_system, "primary_bg", "#FFFFFF")
   ```

4. Create Custom Theme:
   ```python
   theme_system.create_custom_theme(
       base_theme="light",
       theme_name="My Theme", 
       description="Custom theme",
       color_customizations={"primary_bg": "#F0F8FF"}
   )
   ```

5. Accessibility Features:
   ```python
   # Font scaling
   theme_system.set_accessibility_font_scaling(1.2)
   
   # High contrast mode
   theme_system.toggle_high_contrast_mode()
   ```

6. Responsive Design:
   ```python
   # Get responsive font size
   font_size = theme_system.get_responsive_font_size(12)
   
   # Get responsive padding
   padding = theme_system.get_responsive_padding(8)
   ```

Features:
- JSON-based theme configuration
- Light, dark, and high-contrast themes included
- Responsive design for different screen sizes
- Accessibility compliance (WCAG AA/AAA)
- Custom theme creation and import/export
- Integration with existing theme system
- SOLID principles compliance
- Clean Architecture alignment
"""