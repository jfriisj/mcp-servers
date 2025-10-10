"""
Base Widget System for Study Buddy GUI Application.

Provides foundational classes and utilities for all GUI widgets following
Clean Architecture principles. Implements common functionality like event handling,
loading indicators, responsive layouts, and accessibility features.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: tkinter (external framework), gui.app (Layer 2 - Application)
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

from ..events import EventBus, GlobalEvent


class WidgetState(Enum):
    """Widget lifecycle states."""
    INITIALIZING = "initializing"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"
    DESTROYED = "destroyed"


class LoadingState(Enum):
    """Loading operation states."""
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class LayoutConstraints:
    """Responsive layout constraints for widgets."""
    min_width: int = 200
    min_height: int = 100
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    preferred_width: int = 400
    preferred_height: int = 300
    grow_horizontal: bool = True
    grow_vertical: bool = True


@dataclass
class AccessibilityOptions:
    """Accessibility configuration for widgets."""
    tab_order: int = 0
    screen_reader_label: Optional[str] = None
    keyboard_shortcuts: Dict[str, str] = field(default_factory=dict)
    high_contrast_support: bool = True
    focus_indicators: bool = True


class LoadingIndicator:
    """
    Loading indicator widget with progress tracking.
    
    Provides visual feedback during async operations following SRP.
    """
    
    def __init__(self, parent: tk.Widget, message: str = "Loading..."):
        self.parent = parent
        self.message = message
        self._logger = logging.getLogger(f"{__name__}.LoadingIndicator")
        
        # UI components
        self.frame: Optional[ttk.Frame] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.label: Optional[ttk.Label] = None
        
        # State
        self.is_visible = False
        self._animation_after_id: Optional[str] = None
    
    def show(self, message: Optional[str] = None) -> None:
        """Show the loading indicator."""
        if self.is_visible:
            return
        
        try:
            # Update message if provided
            if message:
                self.message = message
            
            # Create UI if not exists
            if self.frame is None:
                self._create_ui()
            
            # Show the frame
            if self.frame:
                self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.is_visible = True
            
            # Start animation
            self._start_animation()
            
            self._logger.debug(f"Loading indicator shown: {self.message}")
            
        except Exception as e:
            self._logger.error(f"Failed to show loading indicator: {e}", exc_info=True)
    
    def hide(self) -> None:
        """Hide the loading indicator."""
        if not self.is_visible:
            return
        
        try:
            # Stop animation
            self._stop_animation()
            
            # Hide the frame
            if self.frame:
                self.frame.pack_forget()
            
            self.is_visible = False
            self._logger.debug("Loading indicator hidden")
            
        except Exception as e:
            self._logger.error(f"Failed to hide loading indicator: {e}", exc_info=True)
    
    def update_message(self, message: str) -> None:
        """Update the loading message."""
        self.message = message
        if self.label and self.is_visible:
            self.label.config(text=message)
    
    def _create_ui(self) -> None:
        """Create the loading UI components."""
        # Main frame with border
        self.frame = ttk.Frame(self.parent, relief=tk.RAISED, borderwidth=1)
        
        # Progress bar (indeterminate mode)
        self.progress_bar = ttk.Progressbar(
            self.frame, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(pady=(20, 10))
        
        # Message label
        self.label = ttk.Label(
            self.frame,
            text=self.message,
            font=('TkDefaultFont', 9)
        )
        self.label.pack(pady=(0, 20))
    
    def _start_animation(self) -> None:
        """Start the progress bar animation."""
        if self.progress_bar:
            self.progress_bar.start(10)  # 10ms interval
    
    def _stop_animation(self) -> None:
        """Stop the progress bar animation."""
        if self.progress_bar:
            self.progress_bar.stop()


class ResponsiveLayout:
    """
    Responsive layout manager for widgets.
    
    Handles window resizing and adaptive layouts following SRP.
    """
    
    def __init__(self, widget: tk.Widget, constraints: LayoutConstraints):
        self.widget = widget
        self.constraints = constraints
        self._logger = logging.getLogger(f"{__name__}.ResponsiveLayout")
        
        # Bind resize events
        self.widget.bind('<Configure>', self._on_configure)
        
        # Track last size for debouncing
        self._last_width = 0
        self._last_height = 0
        self._resize_after_id: Optional[str] = None
    
    def _on_configure(self, event) -> None:
        """Handle widget resize events with debouncing."""
        if event.widget != self.widget:
            return
        
        # Cancel previous resize callback
        if self._resize_after_id:
            self.widget.after_cancel(self._resize_after_id)
        
        # Schedule resize handling with debounce delay
        self._resize_after_id = self.widget.after(100, self._handle_resize)
    
    def _handle_resize(self) -> None:
        """Handle widget resize with constraints."""
        try:
            current_width = self.widget.winfo_width()
            current_height = self.widget.winfo_height()
            
            # Skip if size hasn't changed
            if (current_width == self._last_width and 
                current_height == self._last_height):
                return
            
            self._last_width = current_width
            self._last_height = current_height
            
            # Apply constraints
            self._apply_constraints(current_width, current_height)
            
            # Notify about layout change
            self._notify_layout_change(current_width, current_height)
            
        except Exception as e:
            self._logger.error(f"Error handling resize: {e}", exc_info=True)
    
    def _apply_constraints(self, width: int, height: int) -> None:
        """Apply layout constraints to widget."""
        # Check minimum constraints
        new_width = max(width, self.constraints.min_width)
        new_height = max(height, self.constraints.min_height)
        
        # Check maximum constraints
        if self.constraints.max_width:
            new_width = min(new_width, self.constraints.max_width)
        if self.constraints.max_height:
            new_height = min(new_height, self.constraints.max_height)
        
        # Update geometry if needed (only for toplevel widgets)
        if new_width != width or new_height != height:
            if hasattr(self.widget, 'geometry'):
                try:
                    self.widget.geometry(f"{new_width}x{new_height}")  # type: ignore
                except tk.TclError:
                    # Widget may not support geometry management
                    pass
    
    def _notify_layout_change(self, width: int, height: int) -> None:
        """Notify about layout changes via event system."""
        # This could be used by child widgets to adjust their layout
        self._logger.debug(f"Layout changed: {width}x{height}")


class AccessibilityManager:
    """
    Accessibility support for widgets.
    
    Handles keyboard navigation, screen reader support, and high contrast.
    """
    
    def __init__(self, widget: tk.Widget, options: AccessibilityOptions):
        self.widget = widget
        self.options = options
        self._logger = logging.getLogger(f"{__name__}.AccessibilityManager")
        
        # Setup accessibility features
        self._setup_keyboard_navigation()
        self._setup_screen_reader_support()
        self._setup_focus_indicators()
    
    def _setup_keyboard_navigation(self) -> None:
        """Setup keyboard navigation for the widget."""
        # Note: We don't override tk_focusNext/tk_focusPrev to avoid recursion
        # Individual widgets should handle focus navigation as needed
        
        # Bind keyboard shortcuts
        for key_sequence, action in self.options.keyboard_shortcuts.items():
            self.widget.bind(f"<{key_sequence}>", lambda e, a=action: self._handle_shortcut(a))
    
    def _setup_screen_reader_support(self) -> None:
        """Setup screen reader accessibility."""
        if self.options.screen_reader_label:
            # Set accessible name for screen readers
            try:
                if hasattr(self.widget, 'configure'):
                    # Try to set accessible properties
                    self.widget.configure(takefocus=True)  # type: ignore
            except (tk.TclError, TypeError):
                # Some widgets don't support these configurations
                pass
    
    def _setup_focus_indicators(self) -> None:
        """Setup visual focus indicators."""
        if self.options.focus_indicators:
            self.widget.bind('<FocusIn>', self._on_focus_in)
            self.widget.bind('<FocusOut>', self._on_focus_out)
    
    def _navigate_focus(self, direction: int) -> None:
        """Navigate focus between widgets."""
        try:
            if direction > 0 and hasattr(self.widget, 'tk_focusNext'):
                next_widget = self.widget.tk_focusNext()
                if next_widget and hasattr(next_widget, 'focus_set'):
                    next_widget.focus_set()
            elif direction < 0 and hasattr(self.widget, 'tk_focusPrev'):
                prev_widget = self.widget.tk_focusPrev()
                if prev_widget and hasattr(prev_widget, 'focus_set'):
                    prev_widget.focus_set()
        except (AttributeError, tk.TclError):
            # Fallback focus navigation
            pass
    
    def _handle_shortcut(self, action: str) -> None:
        """Handle keyboard shortcut actions."""
        self._logger.debug(f"Keyboard shortcut activated: {action}")
        # Action handling would be implemented by specific widgets
    
    def _on_focus_in(self, event) -> None:
        """Handle widget focus in."""
        if hasattr(self.widget, 'configure'):
            try:
                # Try to set focus indicators if supported
                self.widget.configure(relief=tk.SOLID, borderwidth=2)  # type: ignore
            except (tk.TclError, TypeError):
                # Widget may not support these configurations
                pass
    
    def _on_focus_out(self, event) -> None:
        """Handle widget focus out."""
        if hasattr(self.widget, 'configure'):
            try:
                # Reset focus indicators if supported
                self.widget.configure(relief=tk.FLAT, borderwidth=1)  # type: ignore
            except (tk.TclError, TypeError):
                # Widget may not support these configurations
                pass


class BaseWidget(ABC):
    """
    Abstract base class for all GUI widgets.
    
    Provides common functionality following SOLID principles:
    - Single Responsibility: Each widget handles one UI concern
    - Open/Closed: Extensible via inheritance, closed for modification
    - Liskov Substitution: All widgets can be used interchangeably
    - Interface Segregation: Minimal required interface
    - Dependency Inversion: Depends on EventBus abstraction
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: EventBus,
        widget_id: str,
        constraints: Optional[LayoutConstraints] = None,
        accessibility: Optional[AccessibilityOptions] = None
    ):
        """
        Initialize base widget.
        
        Args:
            parent: Parent tkinter widget
            event_bus: Global event bus for communication
            widget_id: Unique identifier for this widget
            constraints: Layout constraints
            accessibility: Accessibility options
        """
        self.parent = parent
        self.event_bus = event_bus
        self.widget_id = widget_id
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State management
        self.state = WidgetState.INITIALIZING
        self._last_error: Optional[Exception] = None
        
        # UI components
        self.root_frame: Optional[ttk.Frame] = None
        self.loading_indicator: Optional[LoadingIndicator] = None
        
        # Layout and accessibility
        self.constraints = constraints or LayoutConstraints()
        self.accessibility = accessibility or AccessibilityOptions()
        self._responsive_layout: Optional[ResponsiveLayout] = None
        self._accessibility_manager: Optional[AccessibilityManager] = None
        
        # Event subscriptions (use weak references to prevent memory leaks)
        self._event_subscriptions: List[str] = []
        
        # Initialize the widget
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize widget components."""
        try:
            # Create root frame
            self._create_root_frame()
            
            # Setup layout management
            self._setup_responsive_layout()
            
            # Setup accessibility
            self._setup_accessibility()
            
            # Create loading indicator
            self._create_loading_indicator()
            
            # Create widget-specific UI
            self.create_ui()
            
            # Setup event handlers
            self._setup_event_handlers()
            
            # Mark as ready
            self.state = WidgetState.READY
            self._publish_event("widget.ready", {"widget_id": self.widget_id})
            
            self._logger.info(f"Widget {self.widget_id} initialized successfully")
            
        except Exception as e:
            self.state = WidgetState.ERROR
            self._last_error = e
            self._logger.error(f"Widget {self.widget_id} initialization failed: {e}", exc_info=True)
            self._publish_event("widget.error", {
                "widget_id": self.widget_id,
                "error": str(e)
            })
    
    def _create_root_frame(self) -> None:
        """Create the root frame for this widget."""
        self.root_frame = ttk.Frame(self.parent)
        self.root_frame.pack(fill=tk.BOTH, expand=True)
    
    def _setup_responsive_layout(self) -> None:
        """Setup responsive layout management."""
        if self.root_frame:
            self._responsive_layout = ResponsiveLayout(self.root_frame, self.constraints)
    
    def _setup_accessibility(self) -> None:
        """Setup accessibility features."""
        if self.root_frame:
            self._accessibility_manager = AccessibilityManager(self.root_frame, self.accessibility)
    
    def _create_loading_indicator(self) -> None:
        """Create loading indicator for async operations."""
        if self.root_frame:
            self.loading_indicator = LoadingIndicator(self.root_frame)
    
    def _setup_event_handlers(self) -> None:
        """Setup event subscriptions for this widget."""
        # Subscribe to global events that all widgets should handle
        self._subscribe_event("theme.changed", self._on_theme_changed)
        self._subscribe_event("app.shutdown", self._on_app_shutdown)
    
    @abstractmethod
    def create_ui(self) -> None:
        """
        Create the widget-specific UI components.
        
        Must be implemented by concrete widget classes.
        """
        pass
    
    def destroy(self) -> None:
        """Destroy the widget and clean up resources."""
        try:
            self.state = WidgetState.DESTROYED
            
            # Unsubscribe from events
            self._unsubscribe_all_events()
            
            # Destroy UI components
            if self.root_frame:
                self.root_frame.destroy()
            
            # Publish destroyed event
            self._publish_event("widget.destroyed", {"widget_id": self.widget_id})
            
            self._logger.info(f"Widget {self.widget_id} destroyed")
            
        except Exception as e:
            self._logger.error(f"Error destroying widget {self.widget_id}: {e}", exc_info=True)
    
    def show_loading(self, message: str = "Loading...") -> None:
        """Show loading indicator with message."""
        if self.loading_indicator:
            self.loading_indicator.show(message)
        self.state = WidgetState.LOADING
    
    def hide_loading(self) -> None:
        """Hide loading indicator."""
        if self.loading_indicator:
            self.loading_indicator.hide()
        if self.state == WidgetState.LOADING:
            self.state = WidgetState.READY
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the widget."""
        self.state = WidgetState.READY if enabled else WidgetState.DISABLED
        
        # Enable/disable all child widgets
        if self.root_frame:
            self._set_children_enabled(self.root_frame, enabled)
    
    def _set_children_enabled(self, widget: tk.Widget, enabled: bool) -> None:
        """Recursively enable/disable child widgets."""
        try:
            if hasattr(widget, 'configure'):
                try:
                    # Try to set state if the widget supports it
                    widget.configure(state='normal' if enabled else 'disabled')  # type: ignore
                except (tk.TclError, TypeError):
                    # Widget may not support state configuration
                    pass
            
            # Recursively handle children
            for child in widget.winfo_children():
                self._set_children_enabled(child, enabled)
                
        except Exception as e:
            self._logger.debug(f"Could not set enabled state for widget: {e}")
    
    def _subscribe_event(self, event_type: str, handler: Callable[[GlobalEvent], None]) -> None:
        """Subscribe to an event type."""
        self.event_bus.subscribe(event_type, handler)
        self._event_subscriptions.append(event_type)
    
    def _unsubscribe_all_events(self) -> None:
        """Unsubscribe from all event types."""
        for event_type in self._event_subscriptions:
            self.event_bus.unsubscribe_all(event_type)
        self._event_subscriptions.clear()
    
    def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to the global event bus."""
        event = GlobalEvent(
            event_type=event_type,
            data=data,
            source=self.widget_id,
            timestamp=time.time()
        )
        self.event_bus.publish(event)
    
    def _on_theme_changed(self, event: GlobalEvent) -> None:
        """Handle theme change events."""
        self._logger.debug(f"Theme changed event received in {self.widget_id}")
        # Concrete widgets should override this to apply theme changes
    
    def _on_app_shutdown(self, event: GlobalEvent) -> None:
        """Handle application shutdown events."""
        self._logger.debug(f"App shutdown event received in {self.widget_id}")
        self.destroy()
    
    # Public API for concrete widgets
    def get_state(self) -> WidgetState:
        """Get current widget state."""
        return self.state
    
    def get_last_error(self) -> Optional[Exception]:
        """Get the last error that occurred."""
        return self._last_error
    
    def is_ready(self) -> bool:
        """Check if widget is ready for interaction."""
        return self.state == WidgetState.READY


class WidgetFactory:
    """
    Factory for creating widgets with consistent configuration.
    
    Follows Factory pattern for widget creation and configuration.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._logger = logging.getLogger(f"{__name__}.WidgetFactory")
        
        # Default configurations
        self._default_constraints = LayoutConstraints()
        self._default_accessibility = AccessibilityOptions()
    
    def create_widget(
        self,
        widget_class: type,
        parent: tk.Widget,
        widget_id: str,
        constraints: Optional[LayoutConstraints] = None,
        accessibility: Optional[AccessibilityOptions] = None,
        **kwargs
    ) -> BaseWidget:
        """
        Create a widget instance with default configuration.
        
        Args:
            widget_class: Widget class to instantiate
            parent: Parent tkinter widget
            widget_id: Unique widget identifier
            constraints: Layout constraints (uses defaults if None)
            accessibility: Accessibility options (uses defaults if None)
            **kwargs: Additional arguments for widget constructor
            
        Returns:
            Configured widget instance
        """
        try:
            # Use defaults if not provided
            final_constraints = constraints or self._default_constraints
            final_accessibility = accessibility or self._default_accessibility
            
            # Create widget instance
            widget = widget_class(
                parent=parent,
                event_bus=self.event_bus,
                widget_id=widget_id,
                constraints=final_constraints,
                accessibility=final_accessibility,
                **kwargs
            )
            
            self._logger.info(f"Created widget: {widget_id} ({widget_class.__name__})")
            return widget
            
        except Exception as e:
            self._logger.error(f"Failed to create widget {widget_id}: {e}", exc_info=True)
            raise
    
    def set_default_constraints(self, constraints: LayoutConstraints) -> None:
        """Set default layout constraints for new widgets."""
        self._default_constraints = constraints
    
    def set_default_accessibility(self, accessibility: AccessibilityOptions) -> None:
        """Set default accessibility options for new widgets."""
        self._default_accessibility = accessibility