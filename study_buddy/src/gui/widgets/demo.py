"""
Demo script for the Base Widget System.

Demonstrates the widget system capabilities including loading indicators,
responsive layouts, accessibility features, and event handling.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

from ..widgets.base_widget import (
    BaseWidget, 
    WidgetFactory, 
    LayoutConstraints, 
    AccessibilityOptions,
    WidgetState
)
from ..events import EventBus, GlobalEvent


class DemoWidget(BaseWidget):
    """Demo widget showing base widget capabilities."""
    
    def create_ui(self):
        """Create demo UI components."""
        if not self.root_frame:
            return
        
        # Title
        title_label = ttk.Label(
            self.root_frame, 
            text=f"Demo Widget: {self.widget_id}",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack(pady=10)
        
        # Status display
        self.status_label = ttk.Label(
            self.root_frame,
            text=f"State: {self.state.value}"
        )
        self.status_label.pack()
        
        # Control buttons frame
        button_frame = ttk.Frame(self.root_frame)
        button_frame.pack(pady=20)
        
        # Load button
        self.load_button = ttk.Button(
            button_frame,
            text="Start Loading",
            command=self._start_loading_demo
        )
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        # Disable button
        self.disable_button = ttk.Button(
            button_frame,
            text="Toggle Enabled",
            command=self._toggle_enabled
        )
        self.disable_button.pack(side=tk.LEFT, padx=5)
        
        # Event button
        self.event_button = ttk.Button(
            button_frame,
            text="Send Event",
            command=self._send_test_event
        )
        self.event_button.pack(side=tk.LEFT, padx=5)
        
        # Progress display
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(
            self.root_frame,
            textvariable=self.progress_var
        )
        self.progress_label.pack(pady=10)
        
        # Subscribe to custom events
        self._subscribe_event("demo.test_event", self._on_test_event)
    
    def _start_loading_demo(self):
        """Demonstrate loading indicator."""
        def loading_task():
            # Show loading
            self.show_loading("Processing demo task...")
            self.progress_var.set("Loading started...")
            
            # Simulate work
            for i in range(5):
                time.sleep(1)
                progress = f"Step {i+1}/5 completed"
                # Schedule UI update on main thread
                if self.root_frame:
                    self.root_frame.winfo_toplevel().after(0, lambda p=progress: self.progress_var.set(p))
            
            # Hide loading
            if self.root_frame:
                self.root_frame.winfo_toplevel().after(0, self.hide_loading)
                self.root_frame.winfo_toplevel().after(0, lambda: self.progress_var.set("Loading completed!"))
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=loading_task, daemon=True)
        thread.start()
    
    def _toggle_enabled(self):
        """Toggle widget enabled state."""
        current_enabled = self.state == WidgetState.READY
        self.set_enabled(not current_enabled)
        self.status_label.config(text=f"State: {self.state.value}")
        
        state_msg = "disabled" if not current_enabled else "enabled"
        self.progress_var.set(f"Widget {state_msg}")
    
    def _send_test_event(self):
        """Send a test event via the event system."""
        self._publish_event("demo.test_event", {
            "sender": self.widget_id,
            "message": "Hello from demo widget!",
            "timestamp": time.time()
        })
    
    def _on_test_event(self, event: GlobalEvent):
        """Handle test events from other widgets."""
        sender = event.data.get("sender", "unknown")
        message = event.data.get("message", "no message")
        
        if sender != self.widget_id:  # Don't handle our own events
            self.progress_var.set(f"Received: {message} from {sender}")
    
    def _on_theme_changed(self, event: GlobalEvent):
        """Handle theme change events."""
        super()._on_theme_changed(event)
        self.progress_var.set("Theme changed!")


class WidgetSystemDemo:
    """Main demo application showcasing the widget system."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Widget System Demo - Study Buddy")
        self.root.geometry("800x600")
        
        # Create event bus
        self.event_bus = EventBus()
        
        # Create widget factory
        self.widget_factory = WidgetFactory(self.event_bus)
        
        # Set up demo constraints
        demo_constraints = LayoutConstraints(
            min_width=250,
            min_height=200,
            preferred_width=350,
            preferred_height=300
        )
        
        demo_accessibility = AccessibilityOptions(
            screen_reader_label="Demo Widget",
            keyboard_shortcuts={"Control-t": "test"},
            focus_indicators=True
        )
        
        self.widget_factory.set_default_constraints(demo_constraints)
        self.widget_factory.set_default_accessibility(demo_accessibility)
        
        # Create demo widgets
        self._create_demo_widgets()
        
        # Setup global controls
        self._create_global_controls()
    
    def _create_demo_widgets(self):
        """Create demonstration widgets."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Widget container with notebook for multiple widgets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create multiple demo widgets
        self.demo_widgets = []
        
        for i in range(3):
            # Create tab frame
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=f"Widget {i+1}")
            
            # Create demo widget
            widget = self.widget_factory.create_widget(
                widget_class=DemoWidget,
                parent=tab_frame,
                widget_id=f"demo_widget_{i+1}"
            )
            
            self.demo_widgets.append(widget)
    
    def _create_global_controls(self):
        """Create global control buttons."""
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Theme toggle button
        theme_button = ttk.Button(
            controls_frame,
            text="Toggle Theme",
            command=self._toggle_theme
        )
        theme_button.pack(side=tk.LEFT, padx=5)
        
        # Global event button
        event_button = ttk.Button(
            controls_frame,
            text="Broadcast Event",
            command=self._broadcast_event
        )
        event_button.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        exit_button = ttk.Button(
            controls_frame,
            text="Exit Demo",
            command=self._exit_demo
        )
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Info label
        info_label = ttk.Label(
            controls_frame,
            text="Demonstrating: Loading indicators, event system, responsive layouts, accessibility"
        )
        info_label.pack(side=tk.LEFT, padx=20)
    
    def _toggle_theme(self):
        """Simulate theme change event."""
        self.event_bus.publish(GlobalEvent(
            event_type="theme.changed",
            data={"theme": "toggled"},
            source="demo_app",
            timestamp=time.time()
        ))
    
    def _broadcast_event(self):
        """Broadcast a test event to all widgets."""
        self.event_bus.publish(GlobalEvent(
            event_type="demo.test_event",
            data={
                "sender": "global_control",
                "message": "Global broadcast message!",
                "timestamp": time.time()
            },
            source="demo_app",
            timestamp=time.time()
        ))
    
    def _exit_demo(self):
        """Clean up and exit demo."""
        # Destroy all widgets properly
        for widget in self.demo_widgets:
            widget.destroy()
        
        # Close application
        self.root.quit()
    
    def run(self):
        """Run the demo application."""
        print("Starting Widget System Demo...")
        print("\nFeatures demonstrated:")
        print("- Base widget system with lifecycle management")
        print("- Loading indicators for async operations")
        print("- Event system for inter-widget communication")
        print("- Responsive layout management")
        print("- Accessibility features")
        print("- Widget factory pattern")
        print("- Proper cleanup and resource management")
        print("\nTry the buttons to see the features in action!")
        
        self.root.mainloop()


if __name__ == "__main__":
    demo = WidgetSystemDemo()
    demo.run()