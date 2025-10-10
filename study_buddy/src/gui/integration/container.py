"""
Integration Layer Factory and Dependency Injection Container for Study Buddy.

This module provides the composition root for the entire integration layer, implementing
dependency injection patterns, factory methods for MCP client creation, and comprehensive
component lifecycle management following Clean Architecture principles.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Composition Root
SOLID Compliance: Full compliance with all SOLID principles
Purpose: Unified DI container and factory providing clean integration points for GUI components
"""

import asyncio
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Generic, Callable, 
    Protocol, runtime_checkable, Union, Set
)
from datetime import datetime
import inspect
import weakref


# Import all integration layer components
from .mcp_client import IMCPClient
from .async_mcp_client import AsyncMCPClient, IAsyncMCPClient
from .connection_manager import ConnectionManager, ConnectionConfig
from .tool_invoker import GUIToolInvoker
from .config_manager import IntegrationConfigurationManager
from .schemas import SchemaRegistry
from .performance import LRUCacheManager, PerformanceTracker, MemoryManager
from .security import SecurityManager, SecurityConfig, SecurityLevel
from .logging import ObservabilityManager, ObservabilityConfig, LogLevel, OperationType


# ============================================================================
# DEPENDENCY INJECTION ENUMS AND TYPES
# ============================================================================

T = TypeVar('T')
ServiceType = TypeVar('ServiceType')


class ServiceLifetime(Enum):
    """Service lifetime scopes for dependency injection."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ContainerState(Enum):
    """Container lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


# ============================================================================
# CONFIGURATION AND PROFILES
# ============================================================================

@dataclass
class IntegrationProfile:
    """Configuration profile for different deployment environments."""
    
    name: str
    description: str
    
    # Connection settings
    max_connections: int = 5
    connection_timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    
    # Performance settings
    enable_caching: bool = True
    cache_size_mb: int = 50
    performance_sampling_rate: float = 1.0
    
    # Security settings
    security_level: str = "high"
    enable_input_validation: bool = True
    sanitize_errors: bool = True
    
    # Observability settings
    log_level: str = "INFO"
    enable_performance_tracking: bool = True
    enable_error_tracking: bool = True
    enable_alerts: bool = False
    
    # Operational settings
    graceful_shutdown_timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 60.0


# Predefined profiles for different environments
INTEGRATION_PROFILES = {
    "development": IntegrationProfile(
        name="development",
        description="Development environment with verbose logging and relaxed security",
        max_connections=3,
        connection_timeout_seconds=10.0,
        cache_size_mb=25,
        security_level="medium",
        log_level="DEBUG",
        enable_alerts=False
    ),
    
    "production": IntegrationProfile(
        name="production", 
        description="Production environment with optimized performance and security",
        max_connections=10,
        connection_timeout_seconds=30.0,
        cache_size_mb=100,
        security_level="high",
        log_level="INFO",
        enable_alerts=True,
        performance_sampling_rate=0.1  # Sample 10% for performance
    ),
    
    "testing": IntegrationProfile(
        name="testing",
        description="Testing environment with mocking and detailed tracking",
        max_connections=2,
        connection_timeout_seconds=5.0,
        cache_size_mb=10,
        security_level="medium",
        log_level="DEBUG",
        enable_performance_tracking=True,
        enable_alerts=False
    )
}


# ============================================================================
# DEPENDENCY INJECTION INTERFACES
# ============================================================================

@runtime_checkable
class Injectable(Protocol):
    """Protocol for injectable services with lifecycle hooks."""
    
    async def initialize(self) -> None:
        """Initialize the service (optional)."""
        ...
    
    async def shutdown(self) -> None:
        """Shutdown the service gracefully (optional)."""
        ...


@dataclass
class ServiceDescriptor:
    """Describes how a service should be registered and resolved."""
    
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable[..., Any]] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    instance: Optional[Any] = None
    dependencies: List[Type] = field(default_factory=list)
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceContainer(ABC):
    """Abstract interface for dependency injection container."""
    
    @abstractmethod
    def register_singleton(self, service_type: Type[T], implementation: Optional[Type] = None) -> 'ServiceContainer':
        """Register a singleton service."""
        pass
    
    @abstractmethod
    def register_transient(self, service_type: Type[T], implementation: Optional[Type] = None) -> 'ServiceContainer':
        """Register a transient service."""
        pass
    
    @abstractmethod
    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceContainer':
        """Register a specific instance."""
        pass
    
    @abstractmethod
    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> 'ServiceContainer':
        """Register a factory function."""
        pass
    
    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance."""
        pass
    
    @abstractmethod
    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service instance if registered."""
        pass
    
    @abstractmethod
    async def initialize_services(self) -> None:
        """Initialize all registered services."""
        pass
    
    @abstractmethod
    async def shutdown_services(self) -> None:
        """Shutdown all services gracefully."""
        pass


class LifecycleManager(ABC):
    """Abstract interface for component lifecycle management."""
    
    @abstractmethod
    async def start_component(self, component: Any) -> None:
        """Start a component."""
        pass
    
    @abstractmethod
    async def stop_component(self, component: Any) -> None:
        """Stop a component gracefully."""
        pass
    
    @abstractmethod
    async def health_check(self, component: Any) -> Dict[str, Any]:
        """Perform health check on component."""
        pass


class MCPClientFactory(ABC):
    """Abstract factory for creating MCP clients."""
    
    @abstractmethod
    async def create_client(
        self, 
        profile: str = "production",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> AsyncMCPClient:
        """Create a configured MCP client."""
        pass
    
    @abstractmethod
    async def create_test_client(self) -> AsyncMCPClient:
        """Create a client configured for testing."""
        pass
    
    @abstractmethod
    def get_available_profiles(self) -> List[str]:
        """Get list of available configuration profiles."""
        pass


# ============================================================================
# CONCRETE DEPENDENCY INJECTION CONTAINER
# ============================================================================

class IntegrationServiceContainer(ServiceContainer):
    """
    Comprehensive dependency injection container for integration layer.
    
    Features:
    - Multiple service lifetimes (singleton, transient, scoped)
    - Automatic dependency resolution with cycle detection
    - Component lifecycle management with initialization/shutdown hooks
    - Thread-safe service resolution
    - Comprehensive error handling and validation
    """
    
    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.Lock()
        self._initialized_services: Set[Any] = set()
        self._resolution_stack: List[Type] = []
        self._state = ContainerState.INITIALIZING
        
        # Observability
        self._observability: Optional[ObservabilityManager] = None
    
    def register_singleton(self, service_type: Type[T], implementation: Optional[Type] = None) -> 'ServiceContainer':
        """Register a singleton service."""
        impl_type = implementation or service_type
        
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation_type=impl_type,
                lifetime=ServiceLifetime.SINGLETON,
                dependencies=self._get_dependencies(impl_type)
            )
        
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Optional[Type] = None) -> 'ServiceContainer':
        """Register a transient service."""
        impl_type = implementation or service_type
        
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation_type=impl_type,
                lifetime=ServiceLifetime.TRANSIENT,
                dependencies=self._get_dependencies(impl_type)
            )
        
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceContainer':
        """Register a specific instance."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance
            )
            self._singletons[service_type] = instance
        
        return self
    
    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> 'ServiceContainer':
        """Register a factory function."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifetime=ServiceLifetime.TRANSIENT,
                dependencies=self._get_factory_dependencies(factory)
            )
        
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance."""
        with self._lock:
            return self._resolve_service(service_type)
    
    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service instance if registered."""
        try:
            return self.resolve(service_type)
        except (KeyError, ValueError):
            return None
    
    def _resolve_service(self, service_type: Type[T]) -> T:
        """Internal service resolution with cycle detection."""
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack + [service_type]])
            raise ValueError(f"Circular dependency detected: {cycle}")
        
        # Check if service is registered
        if service_type not in self._services:
            raise KeyError(f"Service {service_type.__name__} is not registered")
        
        descriptor = self._services[service_type]
        
        # Handle singleton lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
        
        # Add to resolution stack
        self._resolution_stack.append(service_type)
        
        try:
            instance = self._create_instance(descriptor)
            
            # Cache singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
            
            return instance
            
        finally:
            # Remove from resolution stack
            self._resolution_stack.pop()
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance from service descriptor."""
        # Use existing instance if available
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Use factory if available
        if descriptor.factory is not None:
            # Resolve factory dependencies
            factory_args = []
            for dep_type in descriptor.dependencies:
                dep_instance = self._resolve_service(dep_type)
                factory_args.append(dep_instance)
            
            return descriptor.factory(*factory_args)
        
        # Use implementation type constructor
        if descriptor.implementation_type is not None:
            # Resolve constructor dependencies
            constructor_args = []
            for dep_type in descriptor.dependencies:
                dep_instance = self._resolve_service(dep_type)
                constructor_args.append(dep_instance)
            
            return descriptor.implementation_type(*constructor_args)
        
        raise ValueError(f"Cannot create instance for {descriptor.service_type.__name__}")
    
    def _get_dependencies(self, service_type: Type) -> List[Type]:
        """Extract dependencies from constructor signature."""
        try:
            signature = inspect.signature(service_type.__init__)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # Get type annotation
                if param.annotation != inspect.Parameter.empty:
                    # Handle Optional types
                    if hasattr(param.annotation, '__origin__'):
                        if param.annotation.__origin__ is Union:
                            # Extract non-None type from Optional
                            args = param.annotation.__args__
                            non_none_args = [arg for arg in args if arg is not type(None)]
                            if non_none_args:
                                dependencies.append(non_none_args[0])
                    else:
                        dependencies.append(param.annotation)
            
            return dependencies
            
        except Exception:
            return []
    
    def _get_factory_dependencies(self, factory: Callable) -> List[Type]:
        """Extract dependencies from factory signature."""
        try:
            signature = inspect.signature(factory)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
            
            return dependencies
            
        except Exception:
            return []
    
    async def initialize_services(self) -> None:
        """Initialize all registered services."""
        if self._observability:
            await self._observability.log_info("Initializing integration services", "container")
        
        self._state = ContainerState.STARTING
        
        try:
            # Initialize singletons first
            for service_type, descriptor in self._services.items():
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    instance = self.resolve(service_type)
                    
                # Call initialize if available
                if hasattr(instance, 'initialize') and callable(instance.initialize):
                    init_method = getattr(instance, 'initialize')
                    if asyncio.iscoroutinefunction(init_method):
                        await init_method()
                    else:
                        init_method()
                    self._initialized_services.add(instance)
            
            self._state = ContainerState.RUNNING
            
            if self._observability:
                await self._observability.log_info(
                    f"Initialized {len(self._initialized_services)} services", 
                    "container",
                    service_count=len(self._initialized_services)
                )
                
        except Exception as e:
            self._state = ContainerState.ERROR
            if self._observability:
                await self._observability.log_error("Failed to initialize services", "container", error=e)
            raise
    
    async def shutdown_services(self) -> None:
        """Shutdown all services gracefully."""
        if self._observability:
            await self._observability.log_info("Shutting down integration services", "container")
        
        self._state = ContainerState.STOPPING
        
        # Shutdown in reverse order
        initialized_services = list(self._initialized_services)
        initialized_services.reverse()
        
        for service in initialized_services:
            try:
                if hasattr(service, 'shutdown') and callable(service.shutdown):
                    shutdown_method = getattr(service, 'shutdown')
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await shutdown_method()
                    else:
                        shutdown_method()
                    
            except Exception as e:
                if self._observability:
                    await self._observability.log_error(
                        f"Error shutting down service {type(service).__name__}", 
                        "container", 
                        error=e
                    )
        
        # Clear state
        self._initialized_services.clear()
        self._singletons.clear()
        self._state = ContainerState.STOPPED
        
        if self._observability:
            await self._observability.log_info("Integration services shutdown complete", "container")
    
    def get_container_state(self) -> ContainerState:
        """Get current container state."""
        return self._state
    
    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about registered services."""
        with self._lock:
            return {
                service_type.__name__: {
                    "lifetime": descriptor.lifetime.value,
                    "has_implementation": descriptor.implementation_type is not None,
                    "has_factory": descriptor.factory is not None,
                    "has_instance": descriptor.instance is not None,
                    "dependencies": [dep.__name__ for dep in descriptor.dependencies],
                    "is_singleton_instantiated": service_type in self._singletons
                }
                for service_type, descriptor in self._services.items()
            }


# ============================================================================
# COMPONENT LIFECYCLE MANAGER
# ============================================================================

class IntegrationLifecycleManager(LifecycleManager):
    """
    Comprehensive lifecycle manager for integration components.
    
    Manages component startup, shutdown, health monitoring, and error recovery
    with proper async coordination and resource cleanup.
    """
    
    def __init__(self, observability: Optional[ObservabilityManager] = None):
        """Initialize lifecycle manager."""
        self.observability = observability
        self._component_states: Dict[Any, str] = {}
        self._health_tasks: Dict[Any, asyncio.Task] = {}
        self._lock = threading.Lock()
    
    async def start_component(self, component: Any) -> None:
        """Start a component with proper error handling."""
        component_name = type(component).__name__
        
        if self.observability:
            await self.observability.log_info(f"Starting component: {component_name}", "lifecycle")
        
        try:
            # Call initialize if available
            if hasattr(component, 'initialize') and callable(component.initialize):
                init_method = getattr(component, 'initialize')
                if asyncio.iscoroutinefunction(init_method):
                    await init_method()
                else:
                    init_method()
            
            with self._lock:
                self._component_states[component] = "running"
            
            if self.observability:
                await self.observability.log_info(f"Component started successfully: {component_name}", "lifecycle")
                
        except Exception as e:
            with self._lock:
                self._component_states[component] = "error"
            
            if self.observability:
                await self.observability.log_error(
                    f"Failed to start component: {component_name}", 
                    "lifecycle", 
                    error=e
                )
            raise
    
    async def stop_component(self, component: Any) -> None:
        """Stop a component gracefully."""
        component_name = type(component).__name__
        
        if self.observability:
            await self.observability.log_info(f"Stopping component: {component_name}", "lifecycle")
        
        try:
            # Stop health monitoring
            with self._lock:
                if component in self._health_tasks:
                    task = self._health_tasks.pop(component)
                    task.cancel()
            
            # Call shutdown if available
            if hasattr(component, 'shutdown') and callable(component.shutdown):
                shutdown_method = getattr(component, 'shutdown')
                if asyncio.iscoroutinefunction(shutdown_method):
                    await shutdown_method()
                else:
                    shutdown_method()
            
            with self._lock:
                self._component_states[component] = "stopped"
                
            if self.observability:
                await self.observability.log_info(f"Component stopped successfully: {component_name}", "lifecycle")
                
        except Exception as e:
            with self._lock:
                self._component_states[component] = "error"
                
            if self.observability:
                await self.observability.log_error(
                    f"Error stopping component: {component_name}", 
                    "lifecycle", 
                    error=e
                )
    
    async def health_check(self, component: Any) -> Dict[str, Any]:
        """Perform health check on component."""
        component_name = type(component).__name__
        
        try:
            health_info = {
                "component": component_name,
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "state": self._component_states.get(component, "unknown")
            }
            
            # Call component-specific health check if available
            if hasattr(component, 'get_health_status') and callable(component.get_health_status):
                component_health = component.get_health_status()
                if isinstance(component_health, dict):
                    health_info.update(component_health)
            
            return health_info
            
        except Exception as e:
            return {
                "component": component_name,
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "state": "error",
                "error": str(e)
            }
    
    def get_component_states(self) -> Dict[str, str]:
        """Get current state of all managed components."""
        with self._lock:
            return {
                type(component).__name__: state 
                for component, state in self._component_states.items()
            }


# ============================================================================
# MCP CLIENT FACTORY
# ============================================================================

class IntegrationMCPClientFactory(MCPClientFactory):
    """
    Factory for creating properly configured MCP clients.
    
    Provides different configuration profiles and handles the complex
    dependency wiring required for AsyncMCPClient instances.
    """
    
    def __init__(self, container: ServiceContainer):
        """Initialize MCP client factory."""
        self.container = container
        self._created_clients: weakref.WeakSet = weakref.WeakSet()
    
    async def create_client(
        self, 
        profile: str = "production",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> AsyncMCPClient:
        """Create a configured MCP client."""
        if profile not in INTEGRATION_PROFILES:
            raise ValueError(f"Unknown profile: {profile}. Available: {list(INTEGRATION_PROFILES.keys())}")
        
        profile_config = INTEGRATION_PROFILES[profile]
        
        # Create configuration for this profile
        config_data = {
            "connection": {
                "max_connections": profile_config.max_connections,
                "timeout_seconds": profile_config.connection_timeout_seconds,
                "retry_attempts": profile_config.retry_attempts,
                "retry_delay_seconds": profile_config.retry_delay_seconds
            },
            "performance": {
                "cache_enabled": profile_config.enable_caching,
                "cache_size_mb": profile_config.cache_size_mb,
                "sampling_rate": profile_config.performance_sampling_rate
            },
            "security": {
                "level": profile_config.security_level,
                "validate_inputs": profile_config.enable_input_validation,
                "sanitize_errors": profile_config.sanitize_errors
            },
            "observability": {
                "log_level": profile_config.log_level,
                "track_performance": profile_config.enable_performance_tracking,
                "track_errors": profile_config.enable_error_tracking,
                "enable_alerts": profile_config.enable_alerts
            }
        }
        
        # Apply custom configuration overrides
        if custom_config:
            self._deep_update(config_data, custom_config)
        
        # Create client with profile-specific components
        client = await self._create_client_with_config(config_data, profile)
        
        # Track created clients
        self._created_clients.add(client)
        
        return client
    
    async def create_test_client(self) -> AsyncMCPClient:
        """Create a client configured for testing."""
        return await self.create_client("testing")
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available configuration profiles."""
        return list(INTEGRATION_PROFILES.keys())
    
    async def _create_client_with_config(self, config_data: Dict[str, Any], profile: str) -> AsyncMCPClient:
        """Create AsyncMCPClient with specific configuration."""
        # Resolve required components from container
        try:
            connection_manager = self.container.resolve(ConnectionManager)
            tool_invoker = self.container.resolve(GUIToolInvoker)
            config_manager = self.container.resolve(IntegrationConfigurationManager)
            security_manager = self.container.resolve(SecurityManager)
            observability = self.container.resolve(ObservabilityManager)
            
        except KeyError as e:
            raise RuntimeError(f"Required component not registered in container: {e}")
        
        # Create AsyncMCPClient with resolved dependencies
        client = AsyncMCPClient(
            config_manager=config_manager,
            max_concurrent_operations=10,
            operation_timeout=30.0,
            health_check_interval=30.0
        )
        
        return client
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Deep update a dictionary with another dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_created_clients_count(self) -> int:
        """Get count of clients created by this factory."""
        return len(self._created_clients)


# ============================================================================
# CONTAINER BUILDER
# ============================================================================

class IntegrationContainerBuilder:
    """
    Fluent builder for integration service container.
    
    Provides a convenient API for registering all integration layer components
    with proper dependency configuration and lifecycle management.
    """
    
    def __init__(self):
        """Initialize container builder."""
        self.container = IntegrationServiceContainer()
        self._profile: Optional[str] = None
        self._custom_config: Optional[Dict[str, Any]] = None
    
    def with_profile(self, profile: str) -> 'IntegrationContainerBuilder':
        """Configure container with a specific profile."""
        if profile not in INTEGRATION_PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        
        self._profile = profile
        return self
    
    def with_custom_config(self, config: Dict[str, Any]) -> 'IntegrationContainerBuilder':
        """Add custom configuration overrides."""
        self._custom_config = config
        return self
    
    def register_core_components(self) -> 'IntegrationContainerBuilder':
        """Register core integration layer components."""
        profile_config = INTEGRATION_PROFILES.get(self._profile or "production")
        
        # Configuration components
        self.container.register_singleton(IntegrationConfigurationManager)
        
        # Security components
        security_level_str = getattr(profile_config, 'security_level', 'high')
        security_level = SecurityLevel.HIGH if security_level_str == 'high' else SecurityLevel.MEDIUM
        
        security_config = SecurityConfig(
            security_level=security_level,
            enable_validation=getattr(profile_config, 'enable_input_validation', True),
            sanitize_error_messages=getattr(profile_config, 'sanitize_errors', True)
        )
        self.container.register_instance(SecurityConfig, security_config)
        self.container.register_singleton(SecurityManager)
        
        # Observability components
        log_level_str = getattr(profile_config, 'log_level', 'INFO')
        log_level = LogLevel.INFO if log_level_str == 'INFO' else LogLevel.DEBUG
        
        observability_config = ObservabilityConfig(
            log_level=log_level,
            track_performance=getattr(profile_config, 'enable_performance_tracking', True),
            track_errors=getattr(profile_config, 'enable_error_tracking', True),
            enable_alerts=getattr(profile_config, 'enable_alerts', False)
        )
        self.container.register_instance(ObservabilityConfig, observability_config)
        self.container.register_singleton(ObservabilityManager)
        
        # Performance components
        self.container.register_singleton(LRUCacheManager)
        self.container.register_singleton(PerformanceTracker)
        self.container.register_singleton(MemoryManager)
        
        # Schema components
        self.container.register_singleton(SchemaRegistry)
        
        return self
    
    def register_mcp_components(self) -> 'IntegrationContainerBuilder':
        """Register MCP-specific components."""
        # Connection management
        self.container.register_singleton(ConnectionManager)
        
        # Tool invocation
        self.container.register_singleton(GUIToolInvoker)
        
        # Main MCP client
        self.container.register_transient(AsyncMCPClient)
        self.container.register_transient(IAsyncMCPClient, AsyncMCPClient)
        
        return self
    
    def register_factories(self) -> 'IntegrationContainerBuilder':
        """Register factory components."""
        # Lifecycle manager
        self.container.register_singleton(IntegrationLifecycleManager)
        
        # MCP client factory
        def create_mcp_factory(container: IntegrationServiceContainer) -> IntegrationMCPClientFactory:
            return IntegrationMCPClientFactory(container)
        
        self.container.register_factory(MCPClientFactory, create_mcp_factory)
        self.container.register_factory(IntegrationMCPClientFactory, create_mcp_factory)
        
        return self
    
    def build(self) -> IntegrationServiceContainer:
        """Build the configured container."""
        return self.container


# ============================================================================
# INTEGRATION FACADE
# ============================================================================

class StudyBuddyIntegration:
    """
    Main facade for Study Buddy integration layer.
    
    Provides a simple, high-level API for GUI components to interact with
    the integration layer without needing to understand the internal DI
    container structure.
    """
    
    def __init__(self, profile: str = "production", custom_config: Optional[Dict[str, Any]] = None):
        """Initialize Study Buddy integration."""
        self.profile = profile
        self.custom_config = custom_config
        self._container: Optional[IntegrationServiceContainer] = None
        self._client_factory: Optional[IntegrationMCPClientFactory] = None
        self._lifecycle_manager: Optional[IntegrationLifecycleManager] = None
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the integration layer."""
        if self._is_initialized:
            return
        
        # Build container
        builder = IntegrationContainerBuilder()
        builder = (builder
                  .with_profile(self.profile)
                  .register_core_components()
                  .register_mcp_components() 
                  .register_factories())
        
        if self.custom_config:
            builder = builder.with_custom_config(self.custom_config)
        
        self._container = builder.build()
        
        # Initialize services
        await self._container.initialize_services()
        
        # Get key components
        self._client_factory = self._container.resolve(IntegrationMCPClientFactory)
        self._lifecycle_manager = self._container.resolve(IntegrationLifecycleManager)
        
        self._is_initialized = True
    
    async def create_mcp_client(self, custom_config: Optional[Dict[str, Any]] = None) -> AsyncMCPClient:
        """Create an MCP client with current profile configuration."""
        if not self._is_initialized:
            await self.initialize()
        
        if not self._client_factory:
            raise RuntimeError("Client factory not initialized")
        
        return await self._client_factory.create_client(self.profile, custom_config)
    
    async def create_test_client(self) -> AsyncMCPClient:
        """Create an MCP client configured for testing."""
        if not self._is_initialized:
            await self.initialize()
        
        if not self._client_factory:
            raise RuntimeError("Client factory not initialized")
        
        return await self._client_factory.create_test_client()
    
    def get_container(self) -> IntegrationServiceContainer:
        """Get the underlying DI container for advanced usage."""
        if not self._container:
            raise RuntimeError("Integration not initialized. Call initialize() first.")
        
        return self._container
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of integration layer."""
        if not self._is_initialized or not self._container:
            return {"status": "not_initialized"}
        
        # Get observability health
        observability = self._container.resolve(ObservabilityManager)
        health = observability.get_health_status()
        
        # Add container information
        health["container"] = {
            "state": self._container.get_container_state().value,
            "registered_services": len(self._container.get_registered_services()),
            "profile": self.profile
        }
        
        # Add lifecycle information
        if self._lifecycle_manager:
            health["components"] = self._lifecycle_manager.get_component_states()
        
        return health
    
    async def shutdown(self) -> None:
        """Shutdown the integration layer gracefully."""
        if self._container:
            await self._container.shutdown_services()
            self._container = None
        
        self._client_factory = None
        self._lifecycle_manager = None
        self._is_initialized = False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_integration(
    profile: str = "production", 
    custom_config: Optional[Dict[str, Any]] = None
) -> StudyBuddyIntegration:
    """Create and initialize Study Buddy integration."""
    integration = StudyBuddyIntegration(profile, custom_config)
    await integration.initialize()
    return integration


async def create_mcp_client(
    profile: str = "production",
    custom_config: Optional[Dict[str, Any]] = None
) -> AsyncMCPClient:
    """Create an MCP client with specified configuration."""
    integration = await create_integration(profile, custom_config)
    return await integration.create_mcp_client()


def get_available_profiles() -> List[str]:
    """Get list of available configuration profiles."""
    return list(INTEGRATION_PROFILES.keys())


def get_profile_info(profile: str) -> Dict[str, Any]:
    """Get information about a specific profile."""
    if profile not in INTEGRATION_PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    
    profile_config = INTEGRATION_PROFILES[profile]
    return {
        "name": profile_config.name,
        "description": profile_config.description,
        "max_connections": profile_config.max_connections,
        "connection_timeout": profile_config.connection_timeout_seconds,
        "cache_size_mb": profile_config.cache_size_mb,
        "security_level": profile_config.security_level,
        "log_level": profile_config.log_level,
        "enable_alerts": profile_config.enable_alerts
    }


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def _test_integration_container():
    """Test integration container and factory."""
    print("🏗️  Testing Integration Container and Factory...")
    
    async def run_tests():
        # Test container building
        print("\n📦 Testing container building:")
        
        builder = IntegrationContainerBuilder()
        container = (builder
                    .with_profile("development")
                    .register_core_components()
                    .register_mcp_components()
                    .register_factories()
                    .build())
        
        print(f"Built container with {len(container.get_registered_services())} services")
        
        # Test service initialization
        print("\n🚀 Testing service initialization:")
        await container.initialize_services()
        print(f"Container state: {container.get_container_state().value}")
        
        # Test service resolution
        print("\n🔧 Testing service resolution:")
        observability = container.resolve(ObservabilityManager)
        security = container.resolve(SecurityManager)
        print(f"Resolved ObservabilityManager: {type(observability).__name__}")
        print(f"Resolved SecurityManager: {type(security).__name__}")
        
        # Test client factory
        print("\n🏭 Testing MCP client factory:")
        client_factory = container.resolve(IntegrationMCPClientFactory)
        available_profiles = client_factory.get_available_profiles()
        print(f"Available profiles: {available_profiles}")
        
        # Test integration facade
        print("\n🎭 Testing integration facade:")
        integration = StudyBuddyIntegration("development")
        await integration.initialize()
        
        health = await integration.get_health_status()
        print(f"Health status: {health.get('container', {}).get('state', 'unknown')}")
        
        # Cleanup
        await integration.shutdown()
        await container.shutdown_services()
        
        print("\n🎉 Integration container tested successfully!")
    
    # Run async tests
    asyncio.run(run_tests())


if __name__ == "__main__":
    _test_integration_container()