#!/usr/bin/env python3
"""
Study Buddy GUI Application Entry Point

This module serves as the entry point for the Study Buddy desktop application.
It handles command-line arguments, environment setup, and application initialization.

Architecture: Clean Architecture Layer 1 (External Interface)
Dependencies: gui.app.MainApplication (Layer 2 - Application)
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add the parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.app import MainApplication
from gui.config import get_config_manager, initialize_configuration


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('study_buddy_gui.log')
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Study Buddy - Document Processing and Summarization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start GUI with default settings
  python main.py --theme dark       # Start with dark theme
  python main.py --debug            # Enable debug logging
  python main.py --config custom.json  # Use custom configuration file
        """
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file (default: auto-discover)"
    )
    
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "auto"],
        help="UI theme (overrides saved preference)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (equivalent to --log-level DEBUG)"
    )
    
    parser.add_argument(
        "--mcp-server-path",
        type=str,
        help="Path to MCP server executable (overrides configuration)"
    )
    
    parser.add_argument(
        "--no-auto-connect",
        action="store_true",
        help="Don't automatically connect to MCP server on startup"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Study Buddy GUI v1.0.0"
    )
    
    return parser.parse_args()


def validate_environment() -> bool:
    """
    Validate the runtime environment and dependencies.
    
    Returns:
        True if environment is valid, False otherwise
    """
    try:
        import tkinter
        
        # Test tkinter availability
        root = tkinter.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        
        return True
        
    except ImportError:
        logging.error("Tkinter is not available. Please install python3-tk package.")
        return False
    except Exception as e:
        logging.error(f"Environment validation failed: {e}")
        return False


async def async_main(args: argparse.Namespace) -> int:
    """
    Async entry point for the application.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Initialize configuration
        config_manager = get_config_manager()
        config_manager.initialize()
        
        # Override configuration with command-line arguments
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                logging.error(f"Configuration file not found: {config_path}")
                return 1
            # TODO: Load custom configuration file
        
        if args.theme:
            from gui.config.settings_manager import ThemeMode
            theme_mode = ThemeMode.LIGHT if args.theme == "light" else ThemeMode.DARK if args.theme == "dark" else ThemeMode.AUTO
            config_manager.update_theme_config(mode=theme_mode)
        
        if args.mcp_server_path:
            config_manager.update_mcp_server_config(server_path=args.mcp_server_path)
        
        # auto_connect is handled by MainApplication, not stored in config
        
        # Create and run main application
        app = MainApplication(
            config_manager=config_manager,
            auto_connect=not args.no_auto_connect
        )
        
        # Run the application
        exit_code = await app.run()
        
        logging.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point for the Study Buddy GUI application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Setup logging
        log_level = "DEBUG" if args.debug else args.log_level
        setup_logging(log_level)
        
        logging.info("Starting Study Buddy GUI Application")
        logging.debug(f"Command-line arguments: {args}")
        
        # Validate environment
        if not validate_environment():
            logging.critical("Environment validation failed")
            return 1
        
        # Check Python version
        if sys.version_info < (3, 8):
            logging.critical("Python 3.8 or higher is required")
            return 1
        
        # Run async application
        if sys.platform == "win32":
            # On Windows, use ProactorEventLoop for better subprocess support
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        return asyncio.run(async_main(args))
        
    except Exception as e:
        # Fallback error handling if logging isn't set up
        print(f"Critical error during startup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)