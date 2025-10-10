"""
Configuration Factory for Study Buddy Application

This factory provides easy creation of properly configured ConfigurationManager instances
following dependency injection patterns and SOLID principles.
"""

from typing import List, Optional, Dict, Any, Sequence
from pathlib import Path

from .configuration import (
    ConfigurationManager, FileConfigurationSource, EnvironmentConfigurationSource,
    SchemaConfigurationValidator, IConfigurationSource, IConfigurationValidator, StandardLogger
)
from ..interfaces.core import IConfigurationManager, ILogger


class ConfigurationFactory:
    """Factory for creating configuration managers."""
    
    @staticmethod
    def create_default_config_manager(logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create configuration manager with default settings."""
        actual_logger = logger or StandardLogger()
        sources: List[IConfigurationSource] = [
            EnvironmentConfigurationSource("STUDY_BUDDY", actual_logger),
            FileConfigurationSource(Path("config/app.json"), actual_logger)
        ]
        
        return ConfigurationManager(sources=sources, logger=actual_logger)
    
    @staticmethod
    def create_file_config_manager(config_path: Path, 
                                  logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create file-based configuration manager."""
        sources = [FileConfigurationSource(config_path, logger)]
        return ConfigurationManager(sources=sources, logger=logger)
    
    @staticmethod
    def create_environment_config_manager(prefix: str = "STUDY_BUDDY",
                                        logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create environment-based configuration manager."""
        sources = [EnvironmentConfigurationSource(prefix, logger)]
        return ConfigurationManager(sources=sources, logger=logger)
    
    @staticmethod
    def create_validated_config_manager(sources: List[IConfigurationSource],
                                      schema: Dict[str, Any],
                                      logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create configuration manager with validation."""
        validator = SchemaConfigurationValidator(schema, logger)
        return ConfigurationManager(sources=sources, validator=validator, logger=logger)
    
    @staticmethod
    def create_production_config_manager(config_dir: Path,
                                       logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create production-ready configuration manager."""
        sources = [
            # Environment variables take precedence
            EnvironmentConfigurationSource("STUDY_BUDDY", logger),
            # File configuration as fallback
            FileConfigurationSource(config_dir / "production.json", logger),
            FileConfigurationSource(config_dir / "app.json", logger)
        ]
        
        # Production schema
        schema = {
            "type": "object",
            "required": ["database_path", "log_level"],
            "properties": {
                "database_path": {"type": "string", "minLength": 1},
                "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "server": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "default": "localhost"},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "timeout": {"type": "number", "minimum": 1.0}
                    }
                }
            }
        }
        
        validator = SchemaConfigurationValidator(schema, logger)
        return ConfigurationManager(sources=sources, validator=validator, logger=logger)
    
    @staticmethod
    def create_test_config_manager(logger: Optional[ILogger] = None) -> IConfigurationManager:
        """Create test configuration manager with in-memory config."""
        # Use environment source for test isolation
        sources = [EnvironmentConfigurationSource("TEST_STUDY_BUDDY", logger)]
        
        config_manager = ConfigurationManager(sources=sources, logger=logger)
        
        # Set test defaults
        test_config = {
            "database_path": ":memory:",
            "log_level": "DEBUG",
            "server": {
                "host": "localhost",
                "port": 3001,
                "timeout": 5.0
            }
        }
        
        config_manager.load_configuration(test_config)
        return config_manager