"""
Study Buddy Main Application Demo

This demo script shows the completed Task 8: Main Application Integration.
It demonstrates the three-panel layout with Browse → View → Summarize workflow.

Usage: python demo_main_app.py

Features demonstrated:
- Professional three-panel layout (Document Browser | Content Viewer | Summary Panel)
- Menu bar with File, View, Tools, Help menus  
- Status bar showing MCP connection and document status
- Keyboard shortcuts (Ctrl+O, Ctrl+Q, F11, etc.)
- Event-driven inter-widget communication
- Error handling and recovery
- Theme support and toggling

Architecture: Clean Architecture demonstration
Layer 1: MainApplication orchestrating three concrete widgets
Layer 2: EventBus coordinating component communication  
Layer 3: Mock services for demonstration without full backend
"""

import asyncio
import logging
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.app import MainApplication
from gui.events import EventBus, GlobalEvent


class MockConfigurationManager:
    """
    Mock configuration manager for demonstration.
    
    In production, this would connect to actual configuration services,
    but for demo purposes we provide reasonable defaults.
    """
    
    def __init__(self):
        self.settings = self._create_mock_settings()
        self.theme_service = self._create_mock_theme_service()
        
    def _create_mock_settings(self):
        """Create mock settings object."""
        settings = Mock()
        settings.theme = Mock()
        settings.theme.mode = "LIGHT"  # Default to light mode
        return settings
    
    def _create_mock_theme_service(self):
        """Create mock theme service."""
        theme_service = Mock()
        theme_manager = Mock()
        
        # Mock theme with color scheme
        theme = Mock()
        color_scheme = Mock()
        color_scheme.primary_bg = "#FFFFFF"
        color_scheme.primary_fg = "#000000"
        color_scheme.accent_bg = "#E0E0E0"
        color_scheme.accent_fg = "#0078D4"
        
        theme.get_color_scheme.return_value = color_scheme
        theme.get_name.return_value = "Light Theme"
        
        theme_manager.get_current_theme.return_value = theme
        theme_service.theme_manager = theme_manager
        
        return theme_service
    
    def get_mcp_client(self):
        """Return mock MCP client for demo."""
        mcp_client = Mock()
        
        # Mock async methods
        async def mock_connect():
            print("Demo: MCP client connected (simulated)")
            return True
            
        async def mock_disconnect():
            print("Demo: MCP client disconnected (simulated)")
            return True
        
        mcp_client.connect = mock_connect
        mcp_client.disconnect = mock_disconnect
        
        return mcp_client
    
    def get_theme_service(self):
        """Return theme service."""
        return self.theme_service
    
    def get_settings(self):
        """Return settings."""
        return self.settings
    
    def update_theme_config(self, **kwargs):
        """Mock theme config update."""
        mode = kwargs.get('mode')
        if mode:
            self.settings.theme.mode = str(mode)
            print(f"Demo: Theme mode updated to {mode}")
    
    def update_mcp_server_config(self, **kwargs):
        """Mock MCP server config update."""
        server_path = kwargs.get('server_path')
        if server_path:
            print(f"Demo: MCP server path updated to {server_path}")


class DemoEventMonitor:
    """
    Demo event monitor that logs all events for demonstration purposes.
    
    This shows how the EventBus facilitates loose coupling between components.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.setup_monitoring()
    
    def setup_monitoring(self):
        """Subscribe to all common events for logging."""
        event_types = [
            "document.selected",
            "document.open_requested", 
            "content.loaded",
            "summary.generated",
            "app.quit_requested",
            "theme.toggle_requested",
            "preferences.open_requested",
            "widget.error"
        ]
        
        for event_type in event_types:
            self.event_bus.subscribe(event_type, self.log_event)
    
    def log_event(self, event: GlobalEvent):
        """Log event details for demo purposes."""
        print(f"🔔 Event: {event.event_type}")
        print(f"   Source: {event.source}")
        if event.data:
            print(f"   Data: {event.data}")
        print()


class StudyBuddyDemo:
    """
    Demo application showing Task 8: Main Application Integration.
    
    This demonstrates the complete three-panel application with all
    functionality integrated properly following Clean Architecture.
    """
    
    def __init__(self):
        self.config_manager = MockConfigurationManager()
        self.event_monitor = None
        
        # Setup logging for demo
        logging.basicConfig(
            level=logging.INFO,
            format='%(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_demo(self):
        """Run the complete application demo."""
        print("="*60)
        print("🎯 STUDY BUDDY - TASK 8 DEMO")
        print("Main Application Integration")
        print("="*60)
        print()
        
        print("📋 Features Demonstrated:")
        print("  ✅ Three-panel layout (Browse | View | Summarize)")
        print("  ✅ Menu bar (File, View, Tools, Help)")
        print("  ✅ Status bar (MCP status, document info)")
        print("  ✅ Keyboard shortcuts (Ctrl+O, Ctrl+Q, F11, Ctrl+T)")
        print("  ✅ Event-driven widget communication")
        print("  ✅ Clean Architecture compliance")
        print("  ✅ SOLID principles implementation")
        print("  ✅ Error handling and recovery")
        print()
        
        print("🚀 Starting application...")
        print()
        
        try:
            # Create MainApplication with demo configuration
            app = MainApplication(
                config_manager=self.config_manager,
                auto_connect=False  # Don't auto-connect for demo
            )
            
            # Setup event monitoring for demonstration
            self.event_monitor = DemoEventMonitor(app.event_bus)
            
            print("📱 Application created successfully!")
            print("   - Event monitoring active")
            print("   - Mock services configured")
            print()
            
            # Subscribe to demo-specific events
            app.event_bus.subscribe("app.quit_requested", self.handle_quit_demo)
            
            # Publish a demo startup event
            import time
            startup_event = GlobalEvent(
                event_type="app.demo_started",
                data={"version": "1.0.0", "task": "Task 8 Integration"},
                source="demo",
                timestamp=time.time()
            )
            app.event_bus.publish(startup_event)
            
            print("🎮 DEMO CONTROLS:")
            print("   - Try File → Open Document (Ctrl+O)")
            print("   - Try View → Toggle Theme (Ctrl+T)")
            print("   - Try View → Toggle Fullscreen (F11)")
            print("   - Try Tools → Connect/Disconnect MCP Server")
            print("   - Try Help → About")
            print("   - Close window or press Ctrl+Q to exit")
            print()
            
            print("📊 Watch the console for event notifications!")
            print("="*60)
            print()
            
            # Run the application
            exit_code = await app.run()
            
            print()
            print("="*60) 
            print("✅ DEMO COMPLETED SUCCESSFULLY!")
            print(f"   Exit code: {exit_code}")
            print("   Task 8: Main Application Integration - COMPLETE")
            print("="*60)
            
            return exit_code
            
        except Exception as e:
            print()
            print("❌ Demo Error:")
            print(f"   {e}")
            print("   This might be due to missing tkinter or display issues")
            return 1
    
    def handle_quit_demo(self, event: GlobalEvent):
        """Handle demo quit event."""
        print("👋 Demo quit requested - shutting down gracefully...")


async def main():
    """Main demo entry point."""
    demo = StudyBuddyDemo()
    return await demo.run_demo()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)