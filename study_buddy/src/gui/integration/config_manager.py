"""
GUI Integration Layer - Configuration Manager with Multi-Source Support

This module implements a comprehensive configuration management system for the GUI
integration layer, providing:
- Multi-source configuration (environment variables, JSON files, runtime updates)
- Configuration validation with defaults and environment-specific profiles
- Secure handling of sensitive configuration data
- Hot-reload capabilities for runtime updates
- Clean Architecture compliance with dependency injection support

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Observer Pattern, Factory Pattern
SOLID: SRP (configuration management), OCP (extensible sources), LSP (source substitution), 
       ISP (focused interfaces), DIP (abstractions for sources)
"""

import os
import json
import logging
import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union, Callable, Type, TypeVar
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field, ValidationError, validator

# Optional watchdog import for file monitoring
try:
    import watchdog.observers
    import watchdog.events
    WATCHDOG_AVAILABLE = True
    Observer = watchdog.observers.Observer  # type: ignore
    FileSystemEventHandler = watchdog.events.FileSystemEventHandler  # type: ignore
except ImportError:
    # Fallback implementations when watchdog is not available
    class FileSystemEventHandler:
        """Fallback FileSystemEventHandler when watchdog is not available"""
        pass
    
    class Observer:
        """Fallback Observer when watchdog is not available"""
        def __init__(self):
            pass
        
        def schedule(self, handler, path, recursive=False):
            pass
        
        def start(self):
            pass
        
        def stop(self):
            pass
        
        def join(self):
            pass
    
    WATCHDOG_AVAILABLE = False


# Local imports for GUI integration
from gui.error_handling import (
    get_debug_logger, get_error_tracker, ErrorSeverity, ErrorCategory
)


class ConfigurationSource(Enum):
    """Configuration source types."""
    ENVIRONMENT = "environment"
    JSON_FILE = "json_file"
    RUNTIME = "runtime"
    DEFAULT = "default"


class ConfigurationProfile(Enum):
    """Environment-specific configuration profiles."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class ConfigurationChange:
    """Represents a configuration change event."""
    key: str
    old_value: Any
    new_value: Any
    source: ConfigurationSource
    timestamp: datetime
    profile: ConfigurationProfile


# Type for configuration change callbacks
ConfigurationCallback = Callable[[ConfigurationChange], None]

# Generic type for configuration schemas
T = TypeVar('T', bound=BaseModel)


class IConfigurationSource(ABC):
    """Abstract interface for configuration sources."""
    
    @abstractmethod
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from this source."""
        pass
    
    @abstractmethod
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration to this source (if supported)."""
        pass
    
    @abstractmethod
    def supports_hot_reload(self) -> bool:
        """Check if this source supports hot-reload."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> ConfigurationSource:
        """Get the type of this configuration source."""
        pass


class EnvironmentConfigurationSource(IConfigurationSource):
    """Configuration source that reads from environment variables."""
    
    def __init__(self, prefix: str = "STUDY_BUDDY_"):
        """
        Initialize environment configuration source.
        
        Args:
            prefix: Environment variable prefix to filter by
        """
        self.prefix = prefix
        self.logger = get_debug_logger()
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                
                # Try to parse as JSON first, then as string
                try:
                    config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    # Handle boolean values
                    if value.lower() in ('true', 'false'):
                        config[config_key] = value.lower() == 'true'
                    # Handle numeric values
                    elif value.isdigit():
                        config[config_key] = int(value)
                    elif value.replace('.', '').isdigit():
                        config[config_key] = float(value)
                    else:
                        config[config_key] = value
        
        return config
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Environment variables cannot be saved (read-only source)."""
        return False
    
    def supports_hot_reload(self) -> bool:
        """Environment variables do not support hot-reload."""
        return False
    
    def get_source_type(self) -> ConfigurationSource:
        """Get source type."""
        return ConfigurationSource.ENVIRONMENT


class JSONFileConfigurationSource(IConfigurationSource):
    """Configuration source that reads/writes JSON files with hot-reload support."""
    
    def __init__(self, file_path: Union[str, Path], create_if_missing: bool = True):
        """
        Initialize JSON file configuration source.
        
        Args:
            file_path: Path to JSON configuration file
            create_if_missing: Whether to create file if it doesn't exist
        """
        self.file_path = Path(file_path)
        self.create_if_missing = create_if_missing
        self.logger = get_debug_logger()
        self._last_modified = None
        self._config_cache = {}
        self._observers = []
        self._lock = threading.Lock()
        self._file_monitor = None
        
        # Initialize file monitoring if watchdog is available
        if WATCHDOG_AVAILABLE:
            self._setup_file_monitoring()
        else:
            self.logger.warning("Watchdog not available, file hot-reload disabled")
        
        # Create directory if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file with defaults if missing
        if create_if_missing and not self.file_path.exists():
            self._create_default_file()
    
    def _setup_file_monitoring(self):
        """Set up file monitoring for hot-reload capability."""
        if not WATCHDOG_AVAILABLE:
            return
            
        try:
            # Create a file monitor handler
            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, source_instance):
                    self.source = source_instance
                
                def on_modified(self, event):
                    if not event.is_directory and Path(event.src_path) == self.source.file_path:
                        self.source.logger.debug(f"Configuration file modified: {self.source.file_path}")
                        # Clear cache to force reload on next access
                        with self.source._lock:
                            self.source._last_modified = None
            
            self._file_monitor = ConfigFileHandler(self)
            
        except Exception as e:
            self.logger.warning(f"Failed to setup file monitoring: {e}")
    
    def _create_default_file(self):
        """Create default configuration file."""
        default_config = {
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "profile": "local",
            "mcp_server": {
                "host": "localhost",
                "port": 3000,
                "timeout": 30.0
            },
            "logging": {
                "level": "INFO",
                "format": "structured"
            }
        }
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Created default configuration file: {self.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to create default configuration file: {e}")
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with self._lock:
            try:
                if not self.file_path.exists():
                    return {}
                
                # Check if file has been modified
                current_mtime = self.file_path.stat().st_mtime
                if self._last_modified != current_mtime:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        self._config_cache = json.load(f)
                    self._last_modified = current_mtime
                    self.logger.debug(f"Loaded configuration from {self.file_path}")
                
                return self._config_cache.copy()
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in configuration file {self.file_path}: {e}")
                return {}
            except Exception as e:
                self.logger.error(f"Failed to load configuration from {self.file_path}: {e}")
                return {}
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file."""
        with self._lock:
            try:
                # Add metadata
                config_with_meta = config.copy()
                config_with_meta["last_updated"] = datetime.now().isoformat()
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_with_meta, f, indent=2, ensure_ascii=False)
                
                # Update cache and timestamp
                self._config_cache = config_with_meta
                self._last_modified = self.file_path.stat().st_mtime
                
                self.logger.info(f"Saved configuration to {self.file_path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save configuration to {self.file_path}: {e}")
                return False
    
    def supports_hot_reload(self) -> bool:
        """JSON files support hot-reload through file watching."""
        return True
    
    def get_source_type(self) -> ConfigurationSource:
        """Get source type."""
        return ConfigurationSource.JSON_FILE
    
    # File system event handler methods
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and Path(event.src_path) == self.file_path:
            self.logger.debug(f"Configuration file modified: {self.file_path}")
            # Reload will happen automatically on next load_configuration call


class RuntimeConfigurationSource(IConfigurationSource):
    """Configuration source for runtime updates (in-memory)."""
    
    def __init__(self):
        """Initialize runtime configuration source."""
        self._config = {}
        self._lock = threading.Lock()
        self.logger = get_debug_logger()
    
    def load_configuration(self) -> Dict[str, Any]:
        """Get runtime configuration."""
        with self._lock:
            return self._config.copy()
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Update runtime configuration."""
        with self._lock:
            self._config.update(config)
            return True
    
    def update_value(self, key: str, value: Any):
        """Update a single configuration value at runtime."""
        with self._lock:
            self._config[key] = value
    
    def supports_hot_reload(self) -> bool:
        """Runtime updates are immediately available."""
        return True
    
    def get_source_type(self) -> ConfigurationSource:
        """Get source type."""
        return ConfigurationSource.RUNTIME


class SecureCredentialManager:
    """Manages secure storage and retrieval of sensitive configuration data."""
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        Initialize secure credential manager.
        
        Args:
            key_file: Optional path to encryption key file
        """
        self.key_file = key_file or Path.home() / ".study_buddy" / "config.key"
        self.logger = get_debug_logger()
        self._encryption_key = self._load_or_create_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create new one."""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    return f.read()
            else:
                # Create new key
                key = Fernet.generate_key()
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (owner only)
                os.chmod(self.key_file, 0o600)
                self.logger.info(f"Created new encryption key: {self.key_file}")
                return key
        except Exception as e:
            self.logger.error(f"Failed to load/create encryption key: {e}")
            # Fallback to session key (not persisted)
            return Fernet.generate_key()
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        try:
            encrypted = self._cipher.encrypt(value.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to encrypt value: {e}")
            raise ValueError("Encryption failed")
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to decrypt value: {e}")
            raise ValueError("Decryption failed")
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted."""
        try:
            # Simple heuristic: encrypted values are base64 and longer than typical values
            if len(value) > 50 and '=' in value[-3:]:
                base64.b64decode(value)
                return True
        except Exception:
            pass
        return False


# Configuration schema for validation
class MCPServerConfig(BaseModel):
    """MCP server configuration schema."""
    host: str = Field(default="localhost", description="MCP server host")
    port: int = Field(default=3000, ge=1, le=65535, description="MCP server port")
    timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="Connection timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum connection retries")
    use_tls: bool = Field(default=False, description="Use TLS encryption")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    @validator('host')
    def validate_host(cls, v):
        """Validate host format."""
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()


class LoggingConfig(BaseModel):
    """Logging configuration schema."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="structured", description="Log format")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, ge=1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=1, le=20, description="Number of backup log files")
    
    @validator('level')
    def validate_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class IntegrationConfig(BaseModel):
    """Complete integration layer configuration schema."""
    profile: str = Field(default="local", description="Configuration profile")
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: Dict[str, Any] = Field(default_factory=dict, description="Security settings")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance settings")
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")


class IntegrationConfigurationManager:
    """
    Comprehensive configuration manager for GUI integration layer.
    
    Provides multi-source configuration management with validation, security,
    hot-reload capabilities, and Clean Architecture compliance.
    """
    
    def __init__(
        self,
        profile: ConfigurationProfile = ConfigurationProfile.LOCAL,
        config_dir: Optional[Path] = None,
        enable_hot_reload: bool = True
    ):
        """
        Initialize configuration manager.
        
        Args:
            profile: Configuration profile to use
            config_dir: Directory for configuration files
            enable_hot_reload: Whether to enable hot-reload capabilities
        """
        self.profile = profile
        self.config_dir = config_dir or Path.home() / ".study_buddy" / "config"
        self.enable_hot_reload = enable_hot_reload
        
        self.logger = get_debug_logger()
        self.error_tracker = get_error_tracker()
        
        # Configuration sources (ordered by priority: runtime > env > file > default)
        self._sources: List[IConfigurationSource] = []
        self._current_config = IntegrationConfig()
        self._change_callbacks: List[ConfigurationCallback] = []
        self._file_observer: Optional[Observer] = None
        self._lock = threading.Lock()
        
        # Security manager for sensitive data
        self.credential_manager = SecureCredentialManager()
        
        # Initialize configuration sources
        self._initialize_sources()
        
        # Load initial configuration
        self._load_configuration()
        
        # Set up hot-reload if enabled
        if enable_hot_reload:
            self._setup_hot_reload()
        
        self.logger.info(f"Configuration manager initialized with profile: {profile.value}")
    
    def _initialize_sources(self):
        """Initialize configuration sources in priority order."""
        # 1. Runtime source (highest priority)
        self._sources.append(RuntimeConfigurationSource())
        
        # 2. Environment variables
        self._sources.append(EnvironmentConfigurationSource())
        
        # 3. JSON file source
        config_file = self.config_dir / f"integration_{self.profile.value}.json"
        self._sources.append(JSONFileConfigurationSource(config_file))
        
        self.logger.debug(f"Initialized {len(self._sources)} configuration sources")
    
    def _load_configuration(self):
        """Load configuration from all sources and merge."""
        with self._lock:
            merged_config = {}
            
            # Load from sources in reverse priority order (default -> file -> env -> runtime)
            for source in reversed(self._sources):
                try:
                    source_config = source.load_configuration()
                    if source_config:
                        merged_config.update(source_config)
                        self.logger.debug(
                            f"Loaded {len(source_config)} settings from {source.get_source_type().value}"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to load from {source.get_source_type().value}: {e}")
            
            # Validate and update current configuration
            try:
                self._current_config = IntegrationConfig(**merged_config)
                self.logger.info("Configuration loaded and validated successfully")
            except ValidationError as e:
                self.logger.error(f"Configuration validation failed: {e}")
                # Use default configuration on validation failure
                self._current_config = IntegrationConfig()
    
    def _setup_hot_reload(self):
        """Set up file system monitoring for hot-reload."""
        try:
            self._file_observer = Observer()
            
            # Watch configuration directory
            if self.config_dir.exists():
                self._file_observer.schedule(
                    self._get_file_handler(),
                    str(self.config_dir),
                    recursive=False
                )
                self._file_observer.start()
                self.logger.debug(f"File system monitoring enabled for {self.config_dir}")
            
        except Exception as e:
            self.logger.warning(f"Failed to setup hot-reload monitoring: {e}")
    
    def _get_file_handler(self):
        """Get file system event handler for configuration changes."""
        class ConfigFileHandler(FileSystemEventHandler):
            def __init__(self, config_manager):
                self.config_manager = config_manager
            
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.json'):
                    self.config_manager.logger.debug(f"Configuration file changed: {event.src_path}")
                    # Reload configuration after a brief delay to avoid multiple rapid changes
                    threading.Timer(1.0, self.config_manager.reload_configuration).start()
        
        return ConfigFileHandler(self)
    
    def get_config(self, config_class: Optional[Type[T]] = None) -> Union[IntegrationConfig, T]:
        """
        Get current configuration.
        
        Args:
            config_class: Optional specific configuration class to extract
            
        Returns:
            Configuration object
        """
        if config_class:
            # Extract specific configuration section
            config_dict = self._current_config.dict()
            return config_class(**config_dict)
        
        return self._current_config
    
    def get_value(self, key: str, default: Any = None, decrypt: bool = False) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'mcp_server.host')
            default: Default value if key not found
            decrypt: Whether to decrypt the value if it's encrypted
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._current_config.dict()
        
        try:
            for k in keys:
                value = value[k]
            
            # Decrypt if requested and value appears encrypted
            if decrypt and isinstance(value, str) and self.credential_manager.is_encrypted(value):
                value = self.credential_manager.decrypt_value(value)
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set_value(self, key: str, value: Any, encrypt: bool = False, persist: bool = True) -> bool:
        """
        Set a configuration value at runtime.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            encrypt: Whether to encrypt the value (for sensitive data)
            persist: Whether to persist the change to file
            
        Returns:
            True if successful
        """
        try:
            # Encrypt sensitive values
            if encrypt and isinstance(value, str):
                value = self.credential_manager.encrypt_value(value)
            
            # Update runtime source
            runtime_source = self._get_runtime_source()
            if runtime_source:
                runtime_source.update_value(key, value)
            
            # Reload configuration to apply changes
            old_value = self.get_value(key)
            self._load_configuration()
            new_value = self.get_value(key)
            
            # Notify callbacks of change
            if old_value != new_value:
                change = ConfigurationChange(
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                    source=ConfigurationSource.RUNTIME,
                    timestamp=datetime.now(),
                    profile=self.profile
                )
                self._notify_change_callbacks(change)
            
            # Persist to file if requested
            if persist:
                self.save_configuration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration value {key}: {e}")
            return False
    
    def _get_runtime_source(self) -> Optional[RuntimeConfigurationSource]:
        """Get the runtime configuration source."""
        for source in self._sources:
            if isinstance(source, RuntimeConfigurationSource):
                return source
        return None
    
    def reload_configuration(self):
        """Reload configuration from all sources."""
        self.logger.info("Reloading configuration from all sources")
        self._load_configuration()
    
    def save_configuration(self) -> bool:
        """Save current configuration to persistent storage."""
        try:
            # Save to JSON file source
            for source in self._sources:
                if isinstance(source, JSONFileConfigurationSource):
                    config_dict = self._current_config.dict()
                    return source.save_configuration(config_dict)
            
            self.logger.warning("No writable configuration source found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def add_change_callback(self, callback: ConfigurationCallback):
        """Add a callback for configuration changes."""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: ConfigurationCallback):
        """Remove a configuration change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_change_callbacks(self, change: ConfigurationChange):
        """Notify all registered callbacks of configuration changes."""
        for callback in self._change_callbacks:
            try:
                callback(change)
            except Exception as e:
                self.logger.error(f"Configuration change callback failed: {e}")
    
    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration and return any errors.
        
        Returns:
            List of validation error messages
        """
        try:
            # Re-validate current configuration
            IntegrationConfig(**self._current_config.dict())
            return []
        except ValidationError as e:
            return [str(error) for error in e.errors()]
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Get information about current configuration profile."""
        return {
            'profile': self.profile.value,
            'config_dir': str(self.config_dir),
            'sources': [source.get_source_type().value for source in self._sources],
            'hot_reload_enabled': self.enable_hot_reload,
            'last_loaded': datetime.now().isoformat()
        }
    
    def export_configuration(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Export current configuration for backup or transfer.
        
        Args:
            include_sensitive: Whether to include encrypted sensitive data
            
        Returns:
            Configuration dictionary
        """
        config_dict = self._current_config.dict()
        
        if not include_sensitive:
            # Remove potentially sensitive keys
            sensitive_keys = ['password', 'token', 'key', 'secret', 'credential']
            config_dict = self._filter_sensitive_keys(config_dict, sensitive_keys)
        
        return {
            'profile': self.profile.value,
            'exported_at': datetime.now().isoformat(),
            'configuration': config_dict
        }
    
    def _filter_sensitive_keys(self, config: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
        """Recursively filter out keys that might contain sensitive data."""
        filtered = {}
        
        for key, value in config.items():
            key_lower = key.lower()
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)
            
            if isinstance(value, dict):
                filtered[key] = self._filter_sensitive_keys(value, sensitive_keys)
            elif not is_sensitive:
                filtered[key] = value
            
        return filtered
    
    def import_configuration(self, config_data: Dict[str, Any], merge: bool = True) -> bool:
        """
        Import configuration from external source.
        
        Args:
            config_data: Configuration data to import
            merge: Whether to merge with existing configuration
            
        Returns:
            True if successful
        """
        try:
            if 'configuration' in config_data:
                imported_config = config_data['configuration']
            else:
                imported_config = config_data
            
            if merge:
                # Merge with current configuration
                current_dict = self._current_config.dict()
                current_dict.update(imported_config)
                self._current_config = IntegrationConfig(**current_dict)
            else:
                # Replace current configuration
                self._current_config = IntegrationConfig(**imported_config)
            
            # Save to persistent storage
            self.save_configuration()
            
            self.logger.info("Configuration imported successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def shutdown(self):
        """Shutdown configuration manager and cleanup resources."""
        self.logger.info("Shutting down configuration manager")
        
        # Stop file observer
        if self._file_observer:
            self._file_observer.stop()
            self._file_observer.join()
        
        # Clear callbacks
        self._change_callbacks.clear()
        
        self.logger.info("Configuration manager shutdown complete")


# Factory function for easy instantiation
def create_configuration_manager(
    profile: ConfigurationProfile = ConfigurationProfile.LOCAL,
    config_dir: Optional[Path] = None,
    enable_hot_reload: bool = True
) -> IntegrationConfigurationManager:
    """
    Factory function to create a configured IntegrationConfigurationManager.
    
    Args:
        profile: Configuration profile to use
        config_dir: Optional custom configuration directory
        enable_hot_reload: Whether to enable hot-reload capabilities
        
    Returns:
        Configured IntegrationConfigurationManager instance
    """
    return IntegrationConfigurationManager(
        profile=profile,
        config_dir=config_dir,
        enable_hot_reload=enable_hot_reload
    )


# Singleton instance for easy access (optional)
_default_config_manager: Optional[IntegrationConfigurationManager] = None

def get_default_config_manager() -> IntegrationConfigurationManager:
    """Get or create the default configuration manager instance."""
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = create_configuration_manager()
    return _default_config_manager