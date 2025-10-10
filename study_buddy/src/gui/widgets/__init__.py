"""
GUI Widgets Module for Study Buddy Application.

This module provides the widget system foundation including base classes,
layout management, accessibility support, and loading indicators following
Clean Architecture and SOLID principles.

Architecture: Clean Architecture Layer 1 (External Interface)
"""

from .base_widget import (
    # Core widget classes
    BaseWidget,
    WidgetFactory,
    
    # State management
    WidgetState,
    LoadingState,
    
    # Layout and accessibility
    LayoutConstraints,
    AccessibilityOptions,
    ResponsiveLayout,
    AccessibilityManager,
    
    # UI components
    LoadingIndicator,
)

from .document_browser import (
    # Document browsing widget
    DocumentBrowserWidget,
    DocumentItem,
)

__all__ = [
    # Core classes
    "BaseWidget",
    "WidgetFactory",
    
    # Enums
    "WidgetState", 
    "LoadingState",
    
    # Configuration classes
    "LayoutConstraints",
    "AccessibilityOptions",
    
    # Utility classes
    "ResponsiveLayout",
    "AccessibilityManager", 
    "LoadingIndicator",
    
    # Concrete widgets
    "DocumentBrowserWidget",
    "DocumentItem",
]