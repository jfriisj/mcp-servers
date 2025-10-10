"""
Core Configuration Management Implementation

This module provides a clean, SOLID-compliant configuration management system
that addresses the architectural issues identified in the original config_manager.py.

Key Improvements:
- Single Responsibility: Each class has one clear purpose
- Open/Closed: Extensible through interfaces and strategies
- Liskov Substitution: All implementations properly substitute their interfaces
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions

Architecture:
- IConfigurationManager: Main interface for configuration operations
- ConfigurationSource: Strategy pattern for different config sources
- ConfigurationValidator: Validation logic separation
- ConfigurationStore: Storage abstraction
"""

import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Type, Union, Sequence
from pathlib import Path
from dataclasses import dataclass
import threading

from ..interfaces.core import IConfigurationManager, ILogger


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class ValidationError(ConfigurationError):
    """Configuration validation errors."""
    pass


@dataclass
class ConfigurationEntry:
    """Represents a single configuration entry."""
    key: str
    value: Any
    source: str
    is_sensitive: bool = False
    description: Optional[str] = None


class IConfigurationSource(ABC):
    """Interface for configuration sources."""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration from source."""
        pass
    
    @abstractmethod
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to source."""
        pass
    
    @abstractmethod
    def exists(self) -> bool:
        """Check if configuration source exists."""
        pass


class IConfigurationValidator(ABC):
    """Interface for configuration validation."""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        pass


class FileConfigurationSource(IConfigurationSource):
    """File-based configuration source."""
    
    def __init__(self, file_path: Path, logger: Optional[ILogger] = None):
        self.file_path = file_path
        self.logger = logger or StandardLogger()
        self._lock = threading.Lock()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with self._lock:
            try:
                if not self.file_path.exists():
                    self.logger.info(f"Configuration file does not exist: {self.file_path}")
                    return {}
                
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.logger.debug(f"Loaded configuration from {self.file_path}")
                return config
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {self.file_path}: {e}")
                raise ConfigurationError(f"Invalid JSON: {e}")
            except Exception as e:
                self.logger.error(f"Failed to load {self.file_path}: {e}")
                raise ConfigurationError(f"Load failed: {e}")
    
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file."""
        with self._lock:
            try:
                # Ensure directory exists
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self.logger.debug(f"Saved configuration to {self.file_path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save {self.file_path}: {e}")
                return False
    
    def exists(self) -> bool:
        """Check if configuration file exists."""
        return self.file_path.exists()


class EnvironmentConfigurationSource(IConfigurationSource):
    """Environment variable configuration source."""
    
    def __init__(self, prefix: str, logger: Optional[ILogger] = None):
        self.prefix = prefix.upper() + "_" if prefix else ""
        self.logger = logger or StandardLogger()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                # Try to parse as JSON for complex values
                try:
                    config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    config[config_key] = value
        
        self.logger.debug(f"Loaded {len(config)} items from environment")
        return config
    
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to environment variables."""
        try:
            for key, value in config.items():
                env_key = self.prefix + key.upper()
                if isinstance(value, (dict, list)):
                    os.environ[env_key] = json.dumps(value)
                else:
                    os.environ[env_key] = str(value)
            
            self.logger.debug(f"Saved {len(config)} items to environment")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save to environment: {e}")
            return False
    
    def exists(self) -> bool:
        """Check if any environment variables exist with prefix."""
        return any(key.startswith(self.prefix) for key in os.environ.keys())


class SchemaConfigurationValidator(IConfigurationValidator):
    """Schema-based configuration validator."""
    
    def __init__(self, schema: Dict[str, Any], logger: Optional[ILogger] = None):
        self.schema = schema
        self.logger = logger or StandardLogger()
        self.errors: List[str] = []
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        self.errors.clear()
        
        try:
            self._validate_required_fields(config)
            self._validate_field_types(config)
            self._validate_field_constraints(config)
            
            is_valid = len(self.errors) == 0
            if is_valid:
                self.logger.debug("Configuration validation passed")
            else:
                self.logger.warning(f"Configuration validation failed: {self.errors}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            self.errors.append(str(e))
            return False
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors.copy()
    
    def _validate_required_fields(self, config: Dict[str, Any]) -> None:
        """Validate required fields are present."""
        required = self.schema.get('required', [])
        for field in required:
            if field not in config:
                self.errors.append(f"Required field missing: {field}")
    
    def _validate_field_types(self, config: Dict[str, Any]) -> None:
        """Validate field types."""
        properties = self.schema.get('properties', {})
        for field, value in config.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type and not self._check_type(value, expected_type):
                    self.errors.append(f"Invalid type for {field}: expected {expected_type}")
    
    def _validate_field_constraints(self, config: Dict[str, Any]) -> None:
        """Validate field constraints."""
        properties = self.schema.get('properties', {})
        for field, value in config.items():
            if field in properties:
                constraints = properties[field]
                self._check_constraints(field, value, constraints)
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True
    
    def _check_constraints(self, field: str, value: Any, constraints: Dict[str, Any]) -> None:
        """Check field constraints."""
        if 'minimum' in constraints and isinstance(value, (int, float)):
            if value < constraints['minimum']:
                self.errors.append(f"{field} below minimum: {constraints['minimum']}")
        
        if 'maximum' in constraints and isinstance(value, (int, float)):
            if value > constraints['maximum']:
                self.errors.append(f"{field} above maximum: {constraints['maximum']}")
        
        if 'minLength' in constraints and isinstance(value, str):
            if len(value) < constraints['minLength']:
                self.errors.append(f"{field} too short: minimum {constraints['minLength']}")
        
        if 'maxLength' in constraints and isinstance(value, str):
            if len(value) > constraints['maxLength']:
                self.errors.append(f"{field} too long: maximum {constraints['maxLength']}")


class ConfigurationManager(IConfigurationManager):
    """
    Clean implementation of configuration management.
    
    This class follows SOLID principles:
    - SRP: Only manages configuration operations
    - OCP: Extensible through source and validator interfaces
    - LSP: Properly implements IConfigurationManager
    - ISP: Uses focused interfaces
    - DIP: Depends on abstractions (IConfigurationSource, IConfigurationValidator)
    """
    
    def __init__(self, sources: Sequence[IConfigurationSource], 
                 validator: Optional[IConfigurationValidator] = None,
                 logger: Optional[ILogger] = None):
        self.sources = sources
        self.validator = validator
        self.logger = logger or self._create_default_logger()
        self.config: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        # Load initial configuration
        self._load_from_sources()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        with self._lock:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        with self._lock:
            keys = key.split('.')
            config = self.config
            
            # Navigate to parent
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set value
            config[keys[-1]] = value
            
            self.logger.debug(f"Set configuration value: {key} = {value}")
    
    def load_configuration(self, source: Union[str, Path, Dict]) -> None:
        """Load configuration from source."""
        if isinstance(source, dict):
            with self._lock:
                self.config.update(source)
                self.logger.debug("Loaded configuration from dictionary")
        else:
            # Reload from all sources
            self._load_from_sources()
    
    def save_configuration(self, target: Union[str, Path]) -> None:
        """Save configuration to target."""
        # Save to first writable source (typically file source)
        for source in self.sources:
            if hasattr(source, 'save') and source.save(self.config):
                self.logger.info(f"Saved configuration via {source.__class__.__name__}")
                return
        
        raise ConfigurationError("No writable configuration source available")
    
    def validate_configuration(self) -> bool:
        """Validate current configuration."""
        if self.validator:
            return self.validator.validate(self.config)
        return True
    
    def _load_from_sources(self) -> None:
        """Load configuration from all sources."""
        with self._lock:
            self.config.clear()
            
            for source in self.sources:
                try:
                    source_config = source.load()
                    self.config.update(source_config)
                    self.logger.debug(f"Loaded from {source.__class__.__name__}")
                except Exception as e:
                    self.logger.error(f"Failed to load from {source.__class__.__name__}: {e}")
            
            # Validate after loading
            if self.validator and not self.validator.validate(self.config):
                errors = self.validator.get_errors()
                self.logger.warning(f"Configuration validation errors: {errors}")
    
    def _create_default_logger(self) -> ILogger:
        """Create default logger implementation."""
        return StandardLogger()


class StandardLogger(ILogger):
    """Standard logging implementation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, **kwargs)