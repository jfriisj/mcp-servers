"""
Study Buddy Main Application

This module implements the MainApplication class that serves as the central
orchestrator for the GUI application following Clean Architecture principles.

Architecture: Clean Architecture Layer 2 (Application Layer)
Responsibilities:
- Application lifecycle management (startup, shutdown)
- Global event handling and coordination
- Theme and UI consistency management
- MCP client coordination
- Widget lifecycle management

Dependencies: 
- Layer 1 (External): tkinter, asyncio
- Layer 3 (Domain): gui.config, gui.mcp_client
"""

import asyncio
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Dict, Any, Callable
import threading
import signal
import sys
from enum import Enum

from gui.config import ConfigurationManager
from gui.mcp_client import AsyncMCPClient, MCPConnectionError
from gui.events import EventBus, GlobalEvent
from gui.widgets.document_browser import DocumentBrowserWidget
from gui.widgets.content_viewer import ContentViewerWidget
from gui.widgets.summary_panel import SummaryPanelWidget
from gui.widgets.prompt_builder_simple import PromptBuilderWidget


class ApplicationState(Enum):
    """Application lifecycle states."""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"





class KeyboardShortcuts:
    """
    Manages global keyboard shortcuts for the application.
    
    Follows Single Responsibility Principle for keyboard handling.
    """
    
    def __init__(self, root: tk.Tk, event_bus: EventBus):
        self.root = root
        self.event_bus = event_bus
        self.shortcuts: Dict[str, Callable] = {}
        self._logger = logging.getLogger(f"{__name__}.KeyboardShortcuts")
        
        self._setup_default_shortcuts()
    
    def _setup_default_shortcuts(self) -> None:
        """Setup default application shortcuts."""
        self.register("Control-q", self._quit_application)
        self.register("Control-o", self._open_document)
        self.register("Control-comma", self._open_preferences)
        self.register("F11", self._toggle_fullscreen)
        self.register("Control-t", self._toggle_theme)
    
    def register(self, sequence: str, callback: Callable) -> None:
        """
        Register a keyboard shortcut.
        
        Args:
            sequence: Key sequence (e.g., "Control-o")
            callback: Function to call when shortcut is pressed
        """
        self.root.bind_all(f"<{sequence}>", lambda event: callback())
        self.shortcuts[sequence] = callback
        self._logger.debug(f"Registered shortcut: {sequence}")
    
    def unregister(self, sequence: str) -> None:
        """Unregister a keyboard shortcut."""
        if sequence in self.shortcuts:
            self.root.unbind_all(f"<{sequence}>")
            del self.shortcuts[sequence]
    
    def _quit_application(self) -> None:
        """Handle Ctrl+Q shortcut."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="app.quit_requested",
            data={},
            source="keyboard_shortcuts",
            timestamp=time.time()
        ))
    
    def _open_document(self) -> None:
        """Handle Ctrl+O shortcut."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="document.open_requested",
            data={},
            source="keyboard_shortcuts",
            timestamp=time.time()
        ))
    
    def _open_preferences(self) -> None:
        """Handle Ctrl+, shortcut."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="preferences.open_requested",
            data={},
            source="keyboard_shortcuts",
            timestamp=time.time()
        ))
    
    def _toggle_fullscreen(self) -> None:
        """Handle F11 shortcut."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="ui.fullscreen_toggle_requested",
            data={},
            source="keyboard_shortcuts",
            timestamp=time.time()
        ))
    
    def _toggle_theme(self) -> None:
        """Handle Ctrl+T shortcut."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="theme.toggle_requested",
            data={},
            source="keyboard_shortcuts",
            timestamp=time.time()
        ))


class MainApplication:
    """
    Main application class orchestrating the GUI application.
    
    Responsibilities (Single Responsibility Principle):
    - Application lifecycle management
    - Global event coordination
    - MCP client management
    - Theme and UI consistency
    - Error handling and recovery
    
    Does NOT:
    - Implement specific widgets (delegation to specialized classes)
    - Handle document parsing (delegation to MCP server)
    - Manage file I/O (delegation to configuration system)
    """
    
    def __init__(
        self, 
        config_manager: ConfigurationManager,
        auto_connect: bool = True,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize the main application.
        
        Args:
            config_manager: Configuration management system
            auto_connect: Whether to auto-connect to MCP server
            event_bus: Event bus for component communication (optional, creates default if None)
        """
        self.config_manager = config_manager
        self.auto_connect = auto_connect
        
        # Application state
        self.state = ApplicationState.INITIALIZING
        self._logger = logging.getLogger(f"{__name__}.MainApplication")
        
        # Core components (dependency injection)
        self.root: Optional[tk.Tk] = None
        self.event_bus = event_bus or EventBus()  # Allow injection, fallback to default
        self.keyboard_shortcuts: Optional[KeyboardShortcuts] = None
        self.mcp_client: Optional[AsyncMCPClient] = None
        
        # Threading
        self._asyncio_thread: Optional[threading.Thread] = None
        self._asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event = threading.Event()
        
        # Widgets (will be populated by widget system)
        self.widgets: Dict[str, Any] = {}
        
        # UI Components
        self.main_container: Optional[tk.Frame] = None
        self.horizontal_paned: Optional[tk.PanedWindow] = None
        self.vertical_paned: Optional[tk.PanedWindow] = None
        self.menu_bar: Optional[tk.Menu] = None
        self.status_bar: Optional[tk.Frame] = None
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup internal event handlers."""
        self.event_bus.subscribe("app.quit_requested", self._handle_quit_request)
        self.event_bus.subscribe("theme.toggle_requested", self._handle_theme_toggle)
        self.event_bus.subscribe("mcp.connection_status_changed", self._handle_mcp_status_change)
    
    async def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            self.state = ApplicationState.STARTING
            self._logger.info("Starting Study Buddy GUI Application")
            
            # Initialize Tkinter on main thread
            await self._initialize_gui()
            
            # Setup main application layout
            await self._setup_main_layout()
            
            # Create and integrate widgets
            self._create_widgets()
            
            # Setup inter-widget event coordination
            self._setup_widget_events()
            
            # Create menu and status bars
            self._create_menu_bar()
            self._create_status_bar()
            
            # Initialize MCP client
            if self.auto_connect:
                await self._initialize_mcp_client()
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            self.state = ApplicationState.RUNNING
            self._logger.info("Application started successfully")
            
            # Run the main event loop
            await self._run_main_loop()
            
            return 0
            
        except Exception as e:
            self.state = ApplicationState.ERROR
            self._logger.critical(f"Application error: {e}", exc_info=True)
            await self._show_error_dialog(f"Application Error: {e}")
            return 1
            
        finally:
            await self._shutdown()
    
    async def _initialize_gui(self) -> None:
        """Initialize the Tkinter GUI."""
        # Create root window on main thread
        def create_root():
            self.root = tk.Tk()
            self.root.title("Study Buddy")
            self.root.geometry("1200x800")
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
            
            # Apply theme
            self._apply_theme()
            
            # Setup keyboard shortcuts
            self.keyboard_shortcuts = KeyboardShortcuts(self.root, self.event_bus)
            
            # Hide window initially (will show after full initialization)
            self.root.withdraw()
        
        # Run on main thread
        if threading.current_thread() == threading.main_thread():
            create_root()
        else:
            # If not on main thread, schedule on main thread
            await asyncio.get_event_loop().run_in_executor(None, create_root)
    
    async def _initialize_mcp_client(self) -> None:
        """Initialize MCP client connection."""
        try:
            self.mcp_client = self.config_manager.get_mcp_client()
            
            await self.mcp_client.connect()
            self._logger.info("MCP client connected successfully")
            
            # Publish connection event
            import time
            self.event_bus.publish(GlobalEvent(
                event_type="mcp.connection_status_changed",
                data={"connected": True},
                source="main_application",
                timestamp=time.time()
            ))
            
        except MCPConnectionError as e:
            self._logger.error(f"Failed to connect to MCP server: {e}")
            # Continue without MCP connection - user can retry manually
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self._logger.info(f"Received signal {signum}")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, signal_handler)
    
    async def _run_main_loop(self) -> None:
        """Run the main application event loop."""
        # Show the main window
        if self.root:
            self.root.deiconify()
        
        # Run until shutdown is requested
        while not self._shutdown_event.is_set() and self.state == ApplicationState.RUNNING:
            try:
                # Process Tkinter events
                if self.root:
                    self.root.update()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except tk.TclError:
                # Window was closed
                break
            except Exception as e:
                self._logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)  # Prevent error spam
    
    async def _shutdown(self) -> None:
        """Shutdown the application gracefully."""
        if self.state == ApplicationState.SHUTTING_DOWN:
            return
        
        self.state = ApplicationState.SHUTTING_DOWN
        self._logger.info("Shutting down application")
        
        try:
            # Disconnect MCP client
            if self.mcp_client:
                await self.mcp_client.disconnect()
                self._logger.info("MCP client disconnected")
            
            # Save configuration
            settings = self.config_manager.get_settings()
            self.config_manager.config_service.update_settings(settings)
            self._logger.info("Configuration saved")
            
            # Cleanup Tkinter
            if self.root:
                self.root.quit()
                self.root.destroy()
                self._logger.info("GUI cleaned up")
            
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}", exc_info=True)
        
        finally:
            self.state = ApplicationState.STOPPED
            self._logger.info("Application shutdown complete")
    
    def _apply_theme(self) -> None:
        """Apply the current theme to the application."""
        if not self.root:
            return
        
        theme_service = self.config_manager.get_theme_service()
        theme = theme_service.theme_manager.get_current_theme()
        colors = theme.get_color_scheme()
        
        # Configure tkinter colors
        self.root.configure(bg=colors.primary_bg)
        
        # Configure ttk style
        style = ttk.Style(self.root)
        style.theme_use('clam')  # Use clam as base theme
        
        # Apply theme colors to ttk widgets
        style.configure('TFrame', background=colors.primary_bg)
        style.configure('TLabel', background=colors.primary_bg, foreground=colors.primary_fg)
        style.configure('TButton', background=colors.accent_fg, foreground=colors.primary_bg)
        style.map('TButton', background=[('active', colors.accent_bg)])
        
        self._logger.info(f"Applied theme: {theme.get_name()}")
    
    def _on_window_close(self) -> None:
        """Handle window close event."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="app.quit_requested",
            data={},
            source="window_close",
            timestamp=time.time()
        ))
    
    def _handle_quit_request(self, event: GlobalEvent) -> None:
        """Handle application quit request."""
        self._logger.info("Quit requested")
        self._shutdown_event.set()
    
    def _handle_theme_toggle(self, event: GlobalEvent) -> None:
        """Handle theme toggle request."""
        settings = self.config_manager.get_settings()
        current_mode = settings.theme.mode
        
        # Toggle between light and dark mode
        from gui.config.settings_manager import ThemeMode
        if current_mode == ThemeMode.LIGHT:
            new_mode = ThemeMode.DARK
        elif current_mode == ThemeMode.DARK:
            new_mode = ThemeMode.LIGHT
        else:  # AUTO mode
            # For AUTO mode, switch to explicit light/dark
            theme_service = self.config_manager.get_theme_service()
            current_theme = theme_service.theme_manager.get_current_theme()
            if "dark" in current_theme.get_name().lower():
                new_mode = ThemeMode.LIGHT
            else:
                new_mode = ThemeMode.DARK
        
        # Update theme configuration
        self.config_manager.update_theme_config(mode=new_mode)
        self._apply_theme()
        
        self._logger.info(f"Theme toggled to: {new_mode}")
    
    def _handle_mcp_status_change(self, event: GlobalEvent) -> None:
        """Handle MCP connection status change."""
        connected = event.data.get("connected", False)
        self._logger.info(f"MCP connection status changed: {connected}")
        
        # Update UI to reflect connection status
        # This will be handled by specific widgets in later tasks
    
    async def _show_error_dialog(self, message: str) -> None:
        """Show error dialog to user."""
        def show_dialog():
            messagebox.showerror("Application Error", message)
        
        if self.root:
            self.root.after(0, show_dialog)
        else:
            self._logger.error(f"Cannot show error dialog (no root): {message}")
    
    # Public API for widget registration (used by widget system)
    def register_widget(self, name: str, widget: Any) -> None:
        """
        Register a widget with the application.
        
        Args:
            name: Widget identifier
            widget: Widget instance
        """
        self.widgets[name] = widget
        self._logger.debug(f"Registered widget: {name}")
    
    def unregister_widget(self, name: str) -> None:
        """Unregister a widget."""
        if name in self.widgets:
            del self.widgets[name]
            self._logger.debug(f"Unregistered widget: {name}")
    
    def get_widget(self, name: str) -> Optional[Any]:
        """Get a registered widget by name."""
        return self.widgets.get(name)
    
    async def _setup_main_layout(self) -> None:
        """
        Create the three-panel main layout.
        
        Layout structure:
        - Horizontal split: Document Browser (left) | Content Area (right)
        - Content area vertical split: Content Viewer (top) | Summary Panel (bottom)
        """
        if not self.root:
            raise RuntimeError("Root window not initialized")
        
        try:
            # Create main container frame
            self.main_container = tk.Frame(self.root)
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Create horizontal paned window for left/right split
            self.horizontal_paned = tk.PanedWindow(
                self.main_container,
                orient=tk.HORIZONTAL,
                sashwidth=4,
                sashrelief=tk.RAISED,
                sashpad=2
            )
            self.horizontal_paned.pack(fill=tk.BOTH, expand=True)
            
            # Create vertical paned window for content/summary split (right side)
            self.vertical_paned = tk.PanedWindow(
                self.horizontal_paned,
                orient=tk.VERTICAL,
                sashwidth=4,
                sashrelief=tk.RAISED,
                sashpad=2
            )
            
            # Add vertical paned window to horizontal (it will contain content + summary)
            self.horizontal_paned.add(self.vertical_paned, width=900)  # Right side gets more space
            
            self._logger.info("Main layout created successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to setup main layout: {e}", exc_info=True)
            raise
    
    def _create_widgets(self) -> None:
        """
        Create and configure all application widgets with dependency injection.
        
        Each widget receives:
        - parent: Container widget for UI placement
        - event_bus: Global event communication
        - config_manager: Configuration access
        - mcp_client: MCP server communication (optional)
        """
        try:
            # Create Document Browser Widget (left panel)
            browser_container = tk.Frame(self.horizontal_paned)
            if self.horizontal_paned:
                self.horizontal_paned.add(browser_container, width=300, minsize=250)  # Left panel
            
            document_browser = DocumentBrowserWidget(
                parent=browser_container,
                event_bus=self.event_bus,
                widget_id="document_browser",
                mcp_client=self.mcp_client
            )
            
            # Create Content Viewer Widget (top-right panel) 
            content_container = tk.Frame(self.vertical_paned)
            if self.vertical_paned:
                self.vertical_paned.add(content_container, height=400, minsize=300)  # Top of right side
            
            content_viewer = ContentViewerWidget(
                parent=content_container,
                event_bus=self.event_bus,
                widget_id="content_viewer",
                mcp_client=self.mcp_client
            )
            
            # Create Summary & Prompt Panel (bottom-right panel) with tabs
            bottom_container = tk.Frame(self.vertical_paned) 
            if self.vertical_paned:
                self.vertical_paned.add(bottom_container, height=250, minsize=180)  # Bottom of right side
            
            # Create notebook for Summary and Prompt Builder tabs
            bottom_notebook = ttk.Notebook(bottom_container)
            bottom_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Summary Panel tab
            summary_tab = tk.Frame(bottom_notebook)
            bottom_notebook.add(summary_tab, text="Summaries")
            
            summary_panel = SummaryPanelWidget(
                parent=summary_tab,
                event_bus=self.event_bus,
                widget_id="summary_panel",
                mcp_client=self.mcp_client
            )
            
            # Prompt Builder tab  
            prompt_tab = tk.Frame(bottom_notebook)
            bottom_notebook.add(prompt_tab, text="Prompt Builder")
            
            # Create Prompt Builder (works with or without MCP client)
            prompt_builder = PromptBuilderWidget(
                parent=prompt_tab,
                event_bus=self.event_bus,
                mcp_client=self.mcp_client  # Can be None, PromptBuilder will adapt
            )
            # Register prompt builder widget
            self.register_widget("prompt_builder", prompt_builder)
            
            # Register widgets for lifecycle management
            self.register_widget("document_browser", document_browser)
            self.register_widget("content_viewer", content_viewer)
            self.register_widget("summary_panel", summary_panel)
            
            # Note: Widgets auto-initialize via BaseWidget.show() when first shown
            
            self._logger.info("All widgets created and initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to create widgets: {e}", exc_info=True)
            # Continue with partial initialization rather than crash
            import time
            self.event_bus.publish(GlobalEvent(
                event_type="app.widget_initialization_error",
                data={"error": str(e)},
                source="main_application",
                timestamp=time.time()
            ))
    
    def _setup_widget_events(self) -> None:
        """
        Configure inter-widget event communication for the Browse → View → Summarize workflow.
        
        Event Flow:
        1. DocumentBrowser publishes "document.selected" → ContentViewer loads document
        2. ContentViewer publishes "content.loaded" → SummaryPanel enables summarization
        3. SummaryPanel publishes "summary.generated" → All widgets can respond
        """
        try:
            # Subscribe to workflow events for coordination
            self.event_bus.subscribe("document.selected", self._handle_document_selected)
            self.event_bus.subscribe("content.loaded", self._handle_content_loaded) 
            self.event_bus.subscribe("summary.generated", self._handle_summary_generated)
            
            # Subscribe to widget lifecycle events
            self.event_bus.subscribe("widget.error", self._handle_widget_error)
            
            self._logger.info("Widget event coordination setup complete")
            
        except Exception as e:
            self._logger.error(f"Failed to setup widget events: {e}", exc_info=True)
    
    def _create_menu_bar(self) -> None:
        """Create professional application menu bar."""
        try:
            if not self.root:
                return
            
            self.menu_bar = tk.Menu(self.root)
            self.root.config(menu=self.menu_bar)
            
            # File Menu
            file_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Open Document...", accelerator="Ctrl+O", 
                                command=self._menu_open_document)
            file_menu.add_separator()
            file_menu.add_command(label="Preferences...", accelerator="Ctrl+,", 
                                command=self._menu_open_preferences)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", accelerator="Ctrl+Q", 
                                command=self._menu_quit)
            
            # View Menu
            view_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="View", menu=view_menu)
            view_menu.add_command(label="Toggle Theme", accelerator="Ctrl+T",
                                command=self._menu_toggle_theme)
            view_menu.add_command(label="Toggle Fullscreen", accelerator="F11",
                                command=self._menu_toggle_fullscreen)
            view_menu.add_separator()
            view_menu.add_command(label="Reset Layout", command=self._menu_reset_layout)
            
            # Tools Menu
            tools_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
            tools_menu.add_command(label="Connect to MCP Server", 
                                 command=self._menu_connect_mcp)
            tools_menu.add_command(label="Disconnect MCP Server", 
                                 command=self._menu_disconnect_mcp)
            
            # Help Menu
            help_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Help", menu=help_menu)
            help_menu.add_command(label="About Study Buddy", command=self._menu_about)
            
            self._logger.info("Menu bar created successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to create menu bar: {e}", exc_info=True)
    
    def _create_status_bar(self) -> None:
        """Create status bar showing connection status and document info."""
        try:
            if not self.root:
                return
            
            self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # MCP connection status
            self.status_mcp_label = tk.Label(
                self.status_bar, 
                text="MCP: Disconnected", 
                anchor=tk.W
            )
            self.status_mcp_label.pack(side=tk.LEFT, padx=5)
            
            # Current document info
            self.status_doc_label = tk.Label(
                self.status_bar, 
                text="No document loaded", 
                anchor=tk.W
            )
            self.status_doc_label.pack(side=tk.LEFT, padx=20)
            
            # Application status
            self.status_app_label = tk.Label(
                self.status_bar, 
                text="Ready", 
                anchor=tk.E
            )
            self.status_app_label.pack(side=tk.RIGHT, padx=5)
            
            self._logger.info("Status bar created successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to create status bar: {e}", exc_info=True)
    
    # Event Handlers for Widget Coordination
    def _handle_document_selected(self, event: GlobalEvent) -> None:
        """Handle document selection from DocumentBrowser."""
        document_title = event.data.get("title", "Unknown Document")
        
        self._logger.info(f"Document selected: {document_title}")
        
        # Update status bar
        if hasattr(self, 'status_doc_label'):
            self.status_doc_label.config(text=f"Document: {document_title}")
    
    def _handle_content_loaded(self, event: GlobalEvent) -> None:
        """Handle content loading completion from ContentViewer."""
        document_id = event.data.get("document_id")
        word_count = event.data.get("word_count", 0)
        
        self._logger.info(f"Content loaded for document {document_id}, {word_count} words")
        
        # Update status bar
        if hasattr(self, 'status_app_label'):
            self.status_app_label.config(text=f"Loaded ({word_count} words)")
    
    def _handle_summary_generated(self, event: GlobalEvent) -> None:
        """Handle summary generation completion."""
        summary_type = event.data.get("summary_type", "unknown")
        
        self._logger.info(f"Summary generated: {summary_type}")
        
        # Update status bar
        if hasattr(self, 'status_app_label'):
            self.status_app_label.config(text=f"Summary ready ({summary_type})")
    
    def _handle_widget_error(self, event: GlobalEvent) -> None:
        """Handle widget-level errors."""
        error_message = event.data.get("error", "Unknown widget error")
        widget_name = event.data.get("widget", "Unknown widget")
        
        self._logger.error(f"Widget error in {widget_name}: {error_message}")
        
        # Update status bar to show error
        if hasattr(self, 'status_app_label'):
            self.status_app_label.config(text=f"Error in {widget_name}")
    
    # Menu Handlers
    def _menu_open_document(self) -> None:
        """Handle File → Open Document menu."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="document.open_requested",
            data={},
            source="menu",
            timestamp=time.time()
        ))
    
    def _menu_open_preferences(self) -> None:
        """Handle File → Preferences menu."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="preferences.open_requested",
            data={},
            source="menu",
            timestamp=time.time()
        ))
    
    def _menu_quit(self) -> None:
        """Handle File → Exit menu."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="app.quit_requested",
            data={},
            source="menu",
            timestamp=time.time()
        ))
    
    def _menu_toggle_theme(self) -> None:
        """Handle View → Toggle Theme menu."""
        import time
        self.event_bus.publish(GlobalEvent(
            event_type="theme.toggle_requested",
            data={},
            source="menu",
            timestamp=time.time()
        ))
    
    def _menu_toggle_fullscreen(self) -> None:
        """Handle View → Toggle Fullscreen menu."""
        if self.root:
            current_state = self.root.attributes('-fullscreen')
            self.root.attributes('-fullscreen', not current_state)
    
    def _menu_reset_layout(self) -> None:
        """Handle View → Reset Layout menu."""
        try:
            if self.horizontal_paned:
                # Reset to default proportions: 25% browser, 75% content area
                total_width = self.root.winfo_width() if self.root else 1200
                self.horizontal_paned.sash_place(0, int(total_width * 0.25), 0)
            
            if self.vertical_paned:
                # Reset to default proportions: 70% content, 30% summary
                total_height = self.root.winfo_height() - 100 if self.root else 600  # Account for menu/status
                self.vertical_paned.sash_place(0, 0, int(total_height * 0.70))
            
            self._logger.info("Layout reset to defaults")
            
        except Exception as e:
            self._logger.error(f"Failed to reset layout: {e}", exc_info=True)
    
    def _menu_connect_mcp(self) -> None:
        """Handle Tools → Connect to MCP Server menu."""
        asyncio.create_task(self._connect_mcp_async())
    
    def _menu_disconnect_mcp(self) -> None:
        """Handle Tools → Disconnect MCP Server menu."""
        asyncio.create_task(self._disconnect_mcp_async())
    
    async def _connect_mcp_async(self) -> None:
        """Async helper for MCP connection."""
        try:
            if not self.mcp_client:
                self.mcp_client = self.config_manager.get_mcp_client()
            
            await self.mcp_client.connect()
            
            if hasattr(self, 'status_mcp_label'):
                self.status_mcp_label.config(text="MCP: Connected")
            
            self._logger.info("MCP client connected via menu")
            
        except Exception as e:
            self._logger.error(f"Failed to connect MCP client: {e}")
            if hasattr(self, 'status_mcp_label'):
                self.status_mcp_label.config(text="MCP: Connection failed")
    
    async def _disconnect_mcp_async(self) -> None:
        """Async helper for MCP disconnection."""
        try:
            if self.mcp_client:
                await self.mcp_client.disconnect()
            
            if hasattr(self, 'status_mcp_label'):
                self.status_mcp_label.config(text="MCP: Disconnected")
            
            self._logger.info("MCP client disconnected via menu")
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect MCP client: {e}")
    
    def _menu_about(self) -> None:
        """Handle Help → About menu."""
        about_text = """Study Buddy v1.0.0

Document Processing and Summarization Tool

Built with Clean Architecture principles
and SOLID design patterns.

© 2024 Study Buddy Development Team"""
        
        messagebox.showinfo("About Study Buddy", about_text)