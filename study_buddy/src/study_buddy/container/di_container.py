"""
Dependency Injection Container for Study Buddy Application

This module provides a lightweight dependency injection container that implements
the IContainer interface. It supports singleton, transient, and factory registrations
to enable proper dependency inversion throughout the application.

Key Features:
- Singleton instances (created once, reused)
- Transient instances (created every time)
- Factory functions for complex object creation
- Automatic dependency resolution
- Health checking capabilities
- Thread-safe operations
"""

import threading
import logging
from typing import Any, Dict, Type, Callable, Optional, TypeVar, get_type_hints
import inspect
from functools import wraps

from ..interfaces.core import IContainer

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceLifetime:
    """Service lifetime constants."""
    SINGLETON = "singleton"
    TRANSIENT = "transient" 
    FACTORY = "factory"


class ServiceDescriptor:
    """Describes how a service should be created and managed."""
    
    def __init__(self, interface: Type, implementation: Optional[Type] = None, 
                 factory: Optional[Callable] = None, lifetime: str = ServiceLifetime.TRANSIENT):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.lifetime = lifetime
        self.instance = None
        
    def __repr__(self):
        impl_name = self.implementation.__name__ if self.implementation else "Factory"
        return f"ServiceDescriptor({self.interface.__name__} -> {impl_name}, {self.lifetime})"


class DependencyInjectionContainer(IContainer):
    """
    Lightweight dependency injection container.
    
    Provides service registration and resolution with automatic dependency injection.
    Supports singleton, transient, and factory patterns.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack = set()
        
        logger.debug("DI Container initialized")
    
    def register_singleton(self, interface: Type, implementation: Type) -> None:
        """Register a singleton service."""
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                lifetime=ServiceLifetime.SINGLETON
            )
            self._services[interface] = descriptor
            logger.debug(f"Registered singleton: {interface.__name__} -> {implementation.__name__}")
    
    def register_transient(self, interface: Type, implementation: Type) -> None:
        """Register a transient service."""
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                lifetime=ServiceLifetime.TRANSIENT
            )
            self._services[interface] = descriptor
            logger.debug(f"Registered transient: {interface.__name__} -> {implementation.__name__}")
    
    def register_factory(self, interface: Type, factory_func: Callable[..., Any]) -> None:
        """Register a factory function for creating instances."""
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                factory=factory_func,
                lifetime=ServiceLifetime.FACTORY
            )
            self._services[interface] = descriptor
            logger.debug(f"Registered factory: {interface.__name__} -> {factory_func.__name__}")
    
    def register_instance(self, interface: Type, instance: Any) -> None:
        """Register a pre-created instance."""
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                lifetime=ServiceLifetime.SINGLETON
            )
            descriptor.instance = instance
            self._services[interface] = descriptor
            self._instances[interface] = instance
            logger.debug(f"Registered instance: {interface.__name__}")
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve an instance of the given interface."""
        with self._lock:
            # Check for circular dependencies
            if interface in self._resolution_stack:
                raise ValueError(f"Circular dependency detected for {interface.__name__}")
            
            # Check if service is registered
            if interface not in self._services:
                raise ValueError(f"Service not registered: {interface.__name__}")
            
            descriptor = self._services[interface]
            
            # Return singleton instance if already created
            if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
                return descriptor.instance
            
            # Add to resolution stack to detect circular dependencies
            self._resolution_stack.add(interface)
            
            try:
                instance = self._create_instance(descriptor)
                
                # Store singleton instances
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    descriptor.instance = instance
                    self._instances[interface] = instance
                
                logger.debug(f"Resolved: {interface.__name__}")
                return instance
                
            finally:
                self._resolution_stack.discard(interface)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance based on the service descriptor."""
        if descriptor.factory:
            # Use factory function
            return self._invoke_factory(descriptor.factory)
        elif descriptor.implementation:
            # Create instance with dependency injection
            return self._create_with_dependencies(descriptor.implementation)
        else:
            raise ValueError(f"No implementation or factory for {descriptor.interface.__name__}")
    
    def _invoke_factory(self, factory: Callable) -> Any:
        """Invoke a factory function with dependency injection."""
        sig = inspect.signature(factory)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                # Resolve dependency
                kwargs[param_name] = self.resolve(param.annotation)
        
        return factory(**kwargs)
    
    def _create_with_dependencies(self, implementation: Type) -> Any:
        """Create an instance with automatic dependency injection."""
        try:
            # Get constructor signature
            sig = inspect.signature(implementation.__init__)
            kwargs = {}
            
            # Resolve dependencies for constructor parameters
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    # Try to resolve the dependency
                    try:
                        kwargs[param_name] = self.resolve(param.annotation)
                    except ValueError:
                        # If dependency not registered, check if parameter has default
                        if param.default == inspect.Parameter.empty:
                            logger.warning(f"Cannot resolve dependency {param.annotation} for {implementation.__name__}")
                            raise
            
            return implementation(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to create instance of {implementation.__name__}: {e}")
            raise
    
    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return interface in self._services
    
    def get_registrations(self) -> Dict[Type, ServiceDescriptor]:
        """Get all service registrations."""
        return self._services.copy()
    
    def clear(self) -> None:
        """Clear all registrations and instances."""
        with self._lock:
            self._services.clear()
            self._instances.clear()
            logger.debug("Container cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform container health check."""
        try:
            with self._lock:
                total_services = len(self._services)
                singleton_instances = len(self._instances)
                
                # Check for potential issues
                issues = []
                
                # Check for unresolvable dependencies
                for interface, descriptor in self._services.items():
                    if descriptor.implementation:
                        try:
                            sig = inspect.signature(descriptor.implementation.__init__)
                            for param_name, param in sig.parameters.items():
                                if param_name == 'self':
                                    continue
                                if (param.annotation != inspect.Parameter.empty and 
                                    param.default == inspect.Parameter.empty and
                                    param.annotation not in self._services):
                                    issues.append(f"Unresolved dependency: {param.annotation} for {interface.__name__}")
                        except Exception as e:
                            issues.append(f"Cannot analyze {interface.__name__}: {e}")
                
                return {
                    "healthy": len(issues) == 0,
                    "total_services": total_services,
                    "singleton_instances": singleton_instances,
                    "issues": issues,
                    "services": [f"{i.__name__} ({d.lifetime})" for i, d in self._services.items()]
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }


# Global container instance
_container: Optional[DependencyInjectionContainer] = None
_container_lock = threading.Lock()


def get_container() -> DependencyInjectionContainer:
    """Get the global container instance."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DependencyInjectionContainer()
    return _container


def inject(*dependencies: Type) -> Callable:
    """
    Decorator for automatic dependency injection.
    
    Usage:
        @inject(ILogger, IConfigurationManager)
        def my_function(logger: ILogger, config: IConfigurationManager):
            # Function implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            
            # Resolve dependencies and add to kwargs
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param.annotation in dependencies and param_name not in kwargs:
                    kwargs[param_name] = container.resolve(param.annotation)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator