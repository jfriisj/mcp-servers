"""
Core Module for Study Buddy Application

This module contains the core implementations that address SOLID principle violations
identified in the original codebase. It provides clean, well-designed implementations
of fundamental services.

Components:
- Configuration Management: SOLID-compliant configuration system
- Logging: Clean logging abstractions
- Security: Secure data handling
- Storage: Data persistence abstractions
"""

from .configuration import (
    ConfigurationManager,
    FileConfigurationSource,
    EnvironmentConfigurationSource,
    SchemaConfigurationValidator,
    StandardLogger,
    ConfigurationError,
    ValidationError
)

from .config_factory import ConfigurationFactory

__all__ = [
    # Configuration
    "ConfigurationManager",
    "FileConfigurationSource", 
    "EnvironmentConfigurationSource",
    "SchemaConfigurationValidator",
    "ConfigurationFactory",
    "ConfigurationError",
    "ValidationError",
    
    # Logging
    "StandardLogger"
]