"""
Container Builder for Study Buddy Application

This module provides a fluent API for configuring the dependency injection container.
It simplifies service registration and provides sensible defaults for common scenarios.
"""

import logging
from pathlib import Path
from typing import Type, Any, Optional

from .di_container import DependencyInjectionContainer, ServiceLifetime
from ..interfaces.core import (
    IContainer, ILogger, IConfigurationManager, ISecurityManager,
    IStorageProvider, IDocumentProcessor, IMCPClient
)
from ..interfaces.services import (
    IDocumentService, ISearchService, ISummaryService, IAnalyticsService
)
from ..interfaces.repositories import (
    IDocumentRepository, IChunkRepository, ISummaryRepository, IUserRepository
)

logger = logging.getLogger(__name__)


class ContainerBuilder:
    """
    Fluent builder for configuring the dependency injection container.
    
    Provides a clean API for registering services and configuring dependencies.
    """
    
    def __init__(self):
        self.container = DependencyInjectionContainer()
        self._configured = False
    
    def with_core_services(self) -> 'ContainerBuilder':
        """Register core services with default implementations."""
        logger.info("Registering core services...")
        
        # Import core implementations
        from ..core.configuration import StandardLogger, ConfigurationManager
        from ..core.config_factory import ConfigurationFactory
        
        # Register logger as singleton
        self.container.register_singleton(ILogger, StandardLogger)
        
        # Register configuration manager factory
        def config_factory() -> IConfigurationManager:
            return ConfigurationFactory.create_default_config_manager()
        
        self.container.register_factory(IConfigurationManager, config_factory)
        
        logger.info("Core services configured")
        return self
    
    def with_business_services(self) -> 'ContainerBuilder':
        """Register business logic services."""
        logger.info("Registering business services...")
        
        # Business service registrations will be added when implementations exist
        
        logger.info("Business services configured")
        return self
    
    def with_data_services(self) -> 'ContainerBuilder':
        """Register data access services."""
        logger.info("Registering data services...")
        
        # Repository registrations will be added when implementations exist
        
        logger.info("Data services configured")
        return self
    
    def with_configuration(self, config_path: Optional[Path] = None) -> 'ContainerBuilder':
        """Configure application settings."""
        logger.info(f"Configuring application with config path: {config_path}")
        
        # Configuration setup will be implemented with the configuration manager
        
        return self
    
    def with_logging(self, log_level: str = "INFO") -> 'ContainerBuilder':
        """Configure logging services."""
        logger.info(f"Configuring logging with level: {log_level}")
        
        # Logging configuration will be implemented
        
        return self
    
    def with_security(self, security_config: Optional[dict] = None) -> 'ContainerBuilder':
        """Configure security services."""
        logger.info("Configuring security services...")
        
        # Security configuration will be implemented
        
        return self
    
    def register_singleton(self, interface: Type, implementation: Type) -> 'ContainerBuilder':
        """Register a singleton service."""
        self.container.register_singleton(interface, implementation)
        return self
    
    def register_transient(self, interface: Type, implementation: Type) -> 'ContainerBuilder':
        """Register a transient service."""
        self.container.register_transient(interface, implementation)
        return self
    
    def register_factory(self, interface: Type, factory_func) -> 'ContainerBuilder':
        """Register a factory function."""
        self.container.register_factory(interface, factory_func)
        return self
    
    def register_instance(self, interface: Type, instance: Any) -> 'ContainerBuilder':
        """Register a pre-created instance."""
        self.container.register_instance(interface, instance)
        return self
    
    def build(self) -> DependencyInjectionContainer:
        """Build and return the configured container."""
        if not self._configured:
            self._configure_defaults()
            self._configured = True
        
        # Perform health check
        health = self.container.health_check()
        if not health["healthy"]:
            logger.warning(f"Container health issues: {health.get('issues', [])}")
        else:
            logger.info(f"Container built successfully with {health['total_services']} services")
        
        return self.container
    
    def _configure_defaults(self) -> None:
        """Configure default services and settings."""
        logger.debug("Configuring default services...")
        
        # Default configurations will be added as implementations are created
        
        logger.debug("Default services configured")


def create_default_container() -> DependencyInjectionContainer:
    """Create a container with default configuration."""
    return (ContainerBuilder()
            .with_core_services()
            .with_business_services() 
            .with_data_services()
            .with_logging()
            .build())


def create_test_container() -> DependencyInjectionContainer:
    """Create a container configured for testing."""
    return (ContainerBuilder()
            .with_core_services()
            .with_logging("DEBUG")
            .build())


def create_production_container(config_path: Optional[Path] = None) -> DependencyInjectionContainer:
    """Create a container configured for production."""
    return (ContainerBuilder()
            .with_configuration(config_path)
            .with_core_services()
            .with_business_services()
            .with_data_services()
            .with_security()
            .with_logging("INFO")
            .build())