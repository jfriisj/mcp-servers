"""
Configuration Management System for Study Buddy GUI Application.

This module provides secure configuration storage, theme management, and application
state persistence following Clean Architecture principles. It handles sensitive
data encryption and configuration validation with migration support.
"""

import json
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from enum import Enum
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class ThemeMode(Enum):
    """GUI theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system theme


class WindowState(Enum):
    """Window state options."""
    NORMAL = "normal"
    MAXIMIZED = "maximized"
    MINIMIZED = "minimized"
    FULLSCREEN = "fullscreen"


@dataclass
class MCPServerConfig:
    """MCP server connection configuration."""
    host: str = "localhost"
    port: int = 3000
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 10.0
    connection_pool_size: int = 5
    keepalive_interval: float = 30.0
    use_tls: bool = False
    verify_ssl: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServerConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ThemeConfig:
    """GUI theme configuration."""
    mode: ThemeMode = ThemeMode.AUTO
    custom_colors: Dict[str, str] = field(default_factory=dict)
    font_family: str = "Segoe UI"
    font_size: int = 9
    accent_color: str = "#0078d4"
    use_transparency: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["mode"] = self.mode.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeConfig':
        """Create from dictionary."""
        if "mode" in data and isinstance(data["mode"], str):
            data["mode"] = ThemeMode(data["mode"])
        return cls(**data)


@dataclass
class WindowConfig:
    """Window configuration and state."""
    width: int = 1200
    height: int = 800
    x: int = 100
    y: int = 100
    state: WindowState = WindowState.NORMAL
    remember_position: bool = True
    remember_size: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["state"] = self.state.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowConfig':
        """Create from dictionary."""
        if "state" in data and isinstance(data["state"], str):
            data["state"] = WindowState(data["state"])
        return cls(**data)


@dataclass
class ApplicationConfig:
    """Application-wide configuration."""
    auto_save_interval: int = 300  # seconds
    max_recent_documents: int = 10
    default_chunk_strategy: str = "auto"
    default_summary_type: str = "standard"
    enable_analytics: bool = False
    check_updates: bool = True
    startup_check_server: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Settings:
    """Complete application settings container."""
    mcp_server: MCPServerConfig = field(default_factory=MCPServerConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mcp_server": self.mcp_server.to_dict(),
            "theme": self.theme.to_dict(),
            "window": self.window.to_dict(),
            "application": self.application.to_dict(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create from dictionary."""
        return cls(
            mcp_server=MCPServerConfig.from_dict(data.get("mcp_server", {})),
            theme=ThemeConfig.from_dict(data.get("theme", {})),
            window=WindowConfig.from_dict(data.get("window", {})),
            application=ApplicationConfig.from_dict(data.get("application", {})),
            version=data.get("version", "1.0.0")
        )


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class EncryptionManager:
    """
    Handles encryption/decryption of sensitive configuration data.
    
    Uses Fernet symmetric encryption with PBKDF2 key derivation for secure
    storage of MCP server credentials and other sensitive settings.
    """
    
    def __init__(self, password: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._fernet: Optional[Fernet] = None
        
        if password:
            self._setup_encryption(password)
    
    def _setup_encryption(self, password: str) -> None:
        """Setup encryption with password-derived key."""
        try:
            # Use a fixed salt for consistency (in production, should be random and stored)
            salt = b"study_buddy_salt_2025"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._fernet = Fernet(key)
        except Exception as e:
            raise ConfigurationError(f"Failed to setup encryption: {str(e)}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not self._fernet:
            raise ConfigurationError("Encryption not initialized")
        
        try:
            encrypted_bytes = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise ConfigurationError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not self._fernet:
            raise ConfigurationError("Encryption not initialized")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise ConfigurationError(f"Decryption failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if encryption is available."""
        return self._fernet is not None


class ConfigValidator:
    """
    Validates configuration data and handles migrations between versions.
    
    Ensures configuration integrity and provides backward compatibility
    when configuration schema changes between application versions.
    """
    
    CURRENT_VERSION = "1.0.0"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._migration_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "0.9.0": self._migrate_from_0_9_0,
        }
    
    def validate_settings(self, settings: Settings) -> List[str]:
        """
        Validate settings configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate MCP server config
        mcp = settings.mcp_server
        if not mcp.host:
            errors.append("MCP server host cannot be empty")
        if mcp.port <= 0 or mcp.port > 65535:
            errors.append("MCP server port must be between 1 and 65535")
        if mcp.timeout <= 0:
            errors.append("MCP server timeout must be positive")
        if mcp.max_retries < 0:
            errors.append("MCP server max retries must be non-negative")
        
        # Validate theme config
        theme = settings.theme
        if theme.font_size <= 0:
            errors.append("Font size must be positive")
        if not self._is_valid_color(theme.accent_color):
            errors.append("Invalid accent color format")
        
        # Validate window config
        window = settings.window
        if window.width <= 0 or window.height <= 0:
            errors.append("Window dimensions must be positive")
        
        # Validate application config
        app = settings.application
        if app.auto_save_interval <= 0:
            errors.append("Auto-save interval must be positive")
        if app.max_recent_documents <= 0:
            errors.append("Max recent documents must be positive")
        
        return errors
    
    def migrate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate configuration data from older versions.
        
        Args:
            config_data: Raw configuration dictionary
            
        Returns:
            Migrated configuration dictionary
        """
        version = config_data.get("version", "0.9.0")
        
        if version == self.CURRENT_VERSION:
            return config_data
        
        self.logger.info(f"Migrating configuration from version {version} to {self.CURRENT_VERSION}")
        
        # Apply migration handlers in sequence
        for migration_version in sorted(self._migration_handlers.keys()):
            if version <= migration_version:
                handler = self._migration_handlers[migration_version]
                config_data = handler(config_data)
        
        config_data["version"] = self.CURRENT_VERSION
        return config_data
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format (hex)."""
        if not color.startswith("#"):
            return False
        try:
            int(color[1:], 16)
            return len(color) == 7  # #RRGGBB format
        except ValueError:
            return False
    
    def _migrate_from_0_9_0(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration from version 0.9.0."""
        # Example migration: rename old settings
        if "server" in config_data:
            config_data["mcp_server"] = config_data.pop("server")
        
        # Add new settings with defaults
        if "application" not in config_data:
            config_data["application"] = ApplicationConfig().to_dict()
        
        return config_data


class SettingsManager(ABC):
    """
    Abstract settings manager interface.
    
    Defines the contract for configuration persistence, following
    Dependency Inversion Principle for testability and flexibility.
    """
    
    @abstractmethod
    def load_settings(self) -> Settings:
        """Load settings from storage."""
        pass
    
    @abstractmethod
    def save_settings(self, settings: Settings) -> None:
        """Save settings to storage."""
        pass
    
    @abstractmethod
    def get_setting(self, key_path: str) -> Any:
        """Get specific setting by dot-notation path."""
        pass
    
    @abstractmethod
    def set_setting(self, key_path: str, value: Any) -> None:
        """Set specific setting by dot-notation path."""
        pass
    
    @abstractmethod
    def add_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Add callback for setting changes."""
        pass
    
    @abstractmethod
    def remove_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Remove setting change callback."""
        pass


class FileSettingsManager(SettingsManager):
    """
    File-based settings manager implementation.
    
    Provides persistent configuration storage with encryption support,
    automatic backups, and validation. Handles configuration files in
    a platform-appropriate user data directory.
    """
    
    def __init__(
        self,
        config_dir: Optional[Path] = None,
        encryption_password: Optional[str] = None,
        auto_backup: bool = True
    ):
        self.logger = logging.getLogger(__name__)
        
        # Setup configuration directory
        if config_dir is None:
            config_dir = self._get_default_config_dir()
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "settings.json"
        self.backup_dir = self.config_dir / "backups"
        self.auto_backup = auto_backup
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.auto_backup:
            self.backup_dir.mkdir(exist_ok=True)
        
        # Setup encryption
        self.encryption = EncryptionManager(encryption_password)
        
        # Setup validation
        self.validator = ConfigValidator()
        
        # Current settings cache
        self._settings: Optional[Settings] = None
        self._change_listeners: List[Callable[[str, Any], None]] = []
        
        self.logger.info(f"Settings manager initialized with config dir: {self.config_dir}")
    
    def _get_default_config_dir(self) -> Path:
        """Get platform-appropriate configuration directory."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', '~'))
        else:  # Linux/Mac
            base_dir = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config'))
        
        return base_dir / "StudyBuddy"
    
    def load_settings(self) -> Settings:
        """Load settings from file with validation and migration."""
        try:
            if not self.config_file.exists():
                self.logger.info("Configuration file not found, creating default settings")
                settings = Settings()
                self.save_settings(settings)
                return settings
            
            # Read configuration file
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Migrate configuration if needed
            config_data = self.validator.migrate_config(config_data)
            
            # Create settings object
            settings = Settings.from_dict(config_data)
            
            # Validate settings
            validation_errors = self.validator.validate_settings(settings)
            if validation_errors:
                self.logger.warning(f"Configuration validation errors: {validation_errors}")
                # Could either fix automatically or use defaults
                
            self._settings = settings
            self.logger.info("Settings loaded successfully")
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {str(e)}")
            # Return default settings on error
            settings = Settings()
            self._settings = settings
            return settings
    
    def save_settings(self, settings: Settings) -> None:
        """Save settings to file with validation and backup."""
        try:
            # Validate before saving
            validation_errors = self.validator.validate_settings(settings)
            if validation_errors:
                raise ConfigurationError(f"Invalid settings: {validation_errors}")
            
            # Create backup if file exists
            if self.auto_backup and self.config_file.exists():
                self._create_backup()
            
            # Save to file
            config_data = settings.to_dict()
            
            # Write atomically (write to temp file, then rename)
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self.config_file)
            
            self._settings = settings
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {str(e)}")
            raise ConfigurationError(f"Failed to save settings: {str(e)}")
    
    def get_setting(self, key_path: str) -> Any:
        """Get setting by dot-notation path (e.g., 'mcp_server.host')."""
        if not self._settings:
            self._settings = self.load_settings()
        
        try:
            value = self._settings
            for key in key_path.split('.'):
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    raise KeyError(f"Setting key not found: {key}")
            return value
        except Exception as e:
            raise ConfigurationError(f"Failed to get setting '{key_path}': {str(e)}")
    
    def set_setting(self, key_path: str, value: Any) -> None:
        """Set setting by dot-notation path."""
        if not self._settings:
            self._settings = self.load_settings()
        
        try:
            # Navigate to parent object
            obj = self._settings
            keys = key_path.split('.')
            
            for key in keys[:-1]:
                if hasattr(obj, key):
                    obj = getattr(obj, key)
                else:
                    raise KeyError(f"Setting path not found: {key}")
            
            # Set final value
            final_key = keys[-1]
            if hasattr(obj, final_key):
                setattr(obj, final_key, value)
                
                # Save to persistence
                self.save_settings(self._settings)
                
                # Notify listeners
                for listener in self._change_listeners:
                    try:
                        listener(key_path, value)
                    except Exception as e:
                        self.logger.error(f"Setting change listener error: {str(e)}")
            else:
                raise KeyError(f"Setting key not found: {final_key}")
                
        except Exception as e:
            raise ConfigurationError(f"Failed to set setting '{key_path}': {str(e)}")
    
    def add_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Add callback for setting changes."""
        if callback not in self._change_listeners:
            self._change_listeners.append(callback)
    
    def remove_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Remove setting change callback."""
        if callback in self._change_listeners:
            self._change_listeners.remove(callback)
    
    def _create_backup(self) -> None:
        """Create backup of current configuration file."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"settings_{timestamp}.json"
            
            with open(self.config_file, 'rb') as src, open(backup_file, 'wb') as dst:
                dst.write(src.read())
            
            # Keep only last 10 backups
            self._cleanup_old_backups()
            
            self.logger.debug(f"Created settings backup: {backup_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create settings backup: {str(e)}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent."""
        try:
            backup_files = list(self.backup_dir.glob("settings_*.json"))
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Keep only the 10 most recent
            for old_backup in backup_files[10:]:
                old_backup.unlink()
                self.logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {str(e)}")


class ConfigurationService:
    """
    Configuration service providing high-level configuration management.
    
    This service acts as the main entry point for configuration operations,
    providing a clean interface for GUI components following Clean Architecture
    principles. It orchestrates the settings manager, encryption, and validation.
    """
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)
        self._current_settings: Optional[Settings] = None
    
    def initialize(self) -> Settings:
        """Initialize configuration service and load settings."""
        try:
            self._current_settings = self.settings_manager.load_settings()
            self.logger.info("Configuration service initialized successfully")
            return self._current_settings
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration service: {str(e)}")
            raise ConfigurationError(f"Configuration initialization failed: {str(e)}")
    
    def get_settings(self) -> Settings:
        """Get current settings (loads if not already loaded)."""
        if self._current_settings is None:
            self._current_settings = self.settings_manager.load_settings()
        return self._current_settings
    
    def update_settings(self, settings: Settings) -> None:
        """Update and save settings."""
        try:
            self.settings_manager.save_settings(settings)
            self._current_settings = settings
            self.logger.info("Settings updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update settings: {str(e)}")
            raise ConfigurationError(f"Settings update failed: {str(e)}")
    
    def get_mcp_config(self) -> MCPServerConfig:
        """Get MCP server configuration for client creation."""
        settings = self.get_settings()
        return settings.mcp_server
    
    def get_theme_config(self) -> ThemeConfig:
        """Get theme configuration for GUI styling."""
        settings = self.get_settings()
        return settings.theme
    
    def get_window_config(self) -> WindowConfig:
        """Get window configuration for main window setup."""
        settings = self.get_settings()
        return settings.window
    
    def update_window_state(self, width: int, height: int, x: int, y: int, state: WindowState) -> None:
        """Update window state (called when window changes)."""
        try:
            settings = self.get_settings()
            if settings.window.remember_size:
                settings.window.width = width
                settings.window.height = height
            if settings.window.remember_position:
                settings.window.x = x
                settings.window.y = y
            settings.window.state = state
            
            self.settings_manager.save_settings(settings)
            self._current_settings = settings
        except Exception as e:
            self.logger.error(f"Failed to update window state: {str(e)}")
    
    def add_setting_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Add listener for setting changes."""
        self.settings_manager.add_change_listener(callback)
    
    def remove_setting_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Remove setting change listener."""
        self.settings_manager.remove_change_listener(callback)