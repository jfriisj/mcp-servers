"""
Configuration Integration Module for Study Buddy GUI Application.

Provides unified configuration setup and initialization, integrating the
settings manager, theme system, and MCP client configuration. Acts as
the main entry point for configuration services.
"""

import logging
from pathlib import Path
from typing import Optional

from gui.config.settings_manager import (
    FileSettingsManager,
    ConfigurationService,
    Settings,
    ThemeConfig,
    MCPServerConfig
)
from gui.config.theme_system import ThemeManager, ThemeService
from gui.mcp_client import AsyncMCPClient, ConnectionConfig


class ConfigurationManager:
    """
    Central configuration manager coordinating all configuration services.
    
    Provides a unified interface for configuration initialization and
    management across the GUI application. Follows the Facade pattern
    to simplify configuration access for GUI components.
    """
    
    def __init__(
        self,
        config_dir: Optional[Path] = None,
        encryption_password: Optional[str] = None
    ):
        self.logger = logging.getLogger(__name__)
        
        # Initialize settings manager
        self.settings_manager = FileSettingsManager(
            config_dir=config_dir,
            encryption_password=encryption_password,
            auto_backup=True
        )
        
        # Initialize configuration service
        self.config_service = ConfigurationService(self.settings_manager)
        
        # Theme manager (initialized later with settings)
        self.theme_manager: Optional[ThemeManager] = None
        self.theme_service: Optional[ThemeService] = None
        
        # Current settings cache
        self._settings: Optional[Settings] = None
    
    def initialize(self) -> Settings:
        """
        Initialize all configuration services.
        
        Returns:
            Loaded application settings
        """
        try:
            # Load settings
            self._settings = self.config_service.initialize()
            
            # Initialize theme manager
            self.theme_manager = ThemeManager(self._settings.theme)
            self.theme_service = ThemeService(self.theme_manager)
            
            self.logger.info("Configuration manager initialized successfully")
            return self._settings
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration manager: {str(e)}")
            raise
    
    def get_settings(self) -> Settings:
        """Get current application settings."""
        if self._settings is None:
            self._settings = self.initialize()
        return self._settings
    
    def get_mcp_client(self) -> AsyncMCPClient:
        """
        Create MCP client with current configuration.
        
        Returns:
            Configured AsyncMCPClient instance
        """
        settings = self.get_settings()
        mcp_config = settings.mcp_server
        
        # Convert to ConnectionConfig
        connection_config = ConnectionConfig(
            host=mcp_config.host,
            port=mcp_config.port,
            timeout=mcp_config.timeout,
            max_retries=mcp_config.max_retries,
            retry_delay=mcp_config.retry_delay,
            max_retry_delay=mcp_config.max_retry_delay,
            connection_pool_size=mcp_config.connection_pool_size,
            keepalive_interval=mcp_config.keepalive_interval
        )
        
        return AsyncMCPClient(connection_config)
    
    def get_theme_service(self) -> ThemeService:
        """Get theme service for GUI styling."""
        if self.theme_service is None:
            settings = self.get_settings()
            self.theme_manager = ThemeManager(settings.theme)
            self.theme_service = ThemeService(self.theme_manager)
        
        return self.theme_service
    
    def update_mcp_server_config(self, **kwargs) -> None:
        """
        Update MCP server configuration.
        
        Args:
            **kwargs: MCP server configuration parameters
        """
        settings = self.get_settings()
        
        # Update MCP server config
        for key, value in kwargs.items():
            if hasattr(settings.mcp_server, key):
                setattr(settings.mcp_server, key, value)
        
        # Save updated settings
        self.config_service.update_settings(settings)
        self._settings = settings
        
        self.logger.info("MCP server configuration updated")
    
    def update_theme_config(self, **kwargs) -> None:
        """
        Update theme configuration.
        
        Args:
            **kwargs: Theme configuration parameters
        """
        settings = self.get_settings()
        
        # Update theme config
        for key, value in kwargs.items():
            if hasattr(settings.theme, key):
                setattr(settings.theme, key, value)
        
        # Save updated settings
        self.config_service.update_settings(settings)
        self._settings = settings
        
        # Update theme manager if initialized
        if self.theme_manager:
            self.theme_manager.config = settings.theme
        
        self.logger.info("Theme configuration updated")
    
    def save_window_state(self, width: int, height: int, x: int, y: int, state: str) -> None:
        """
        Save window state to configuration.
        
        Args:
            width: Window width
            height: Window height  
            x: Window x position
            y: Window y position
            state: Window state string
        """
        from gui.config.settings_manager import WindowState
        
        try:
            window_state = WindowState(state)
            self.config_service.update_window_state(width, height, x, y, window_state)
            self.logger.debug(f"Window state saved: {width}x{height} at ({x},{y}) - {state}")
        except Exception as e:
            self.logger.error(f"Failed to save window state: {str(e)}")


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager(
    config_dir: Optional[Path] = None,
    encryption_password: Optional[str] = None
) -> ConfigurationManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_dir: Optional config directory override
        encryption_password: Optional encryption password
        
    Returns:
        ConfigurationManager singleton instance
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager(
            config_dir=config_dir,
            encryption_password=encryption_password
        )
    
    return _config_manager


def initialize_configuration(
    config_dir: Optional[Path] = None,
    encryption_password: Optional[str] = None
) -> Settings:
    """
    Initialize global configuration system.
    
    Args:
        config_dir: Optional config directory override
        encryption_password: Optional encryption password
        
    Returns:
        Loaded application settings
    """
    manager = get_config_manager(config_dir, encryption_password)
    return manager.initialize()