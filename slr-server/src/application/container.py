"""
Dependency Injection Container

A SOLID-compliant DI container that follows DIP by binding interfaces to implementations.
"""

from typing import Type, TypeVar, Dict, Any, Callable
from abc import ABC, abstractmethod
import inspect
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class IDependencyContainer(ABC):
    """
    Interface for dependency injection container following DIP.
    """
    
    @abstractmethod
    def bind(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
        """Bind an interface to its implementation."""
        pass
    
    @abstractmethod
    def bind_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> None:
        """Bind an interface to a factory function."""
        pass
    
    @abstractmethod
    def get(self, interface: Type[T]) -> T:
        """Resolve an instance of the interface."""
        pass
    
    @abstractmethod
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if an interface is registered."""
        pass


class DependencyContainer(IDependencyContainer):
    """
    Dependency injection container implementation.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles dependency resolution
    - Open/Closed: Can be extended with new binding types
    - Liskov Substitution: Implements IDependencyContainer interface
    - Interface Segregation: Clean, focused interface
    - Dependency Inversion: Works with abstractions, not concretions
    """
    
    def __init__(self):
        self._bindings: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singleton_flags: Dict[Type, bool] = {}
    
    def bind(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
        """
        Bind an interface to its implementation.
        
        Args:
            interface: The interface/abstract class
            implementation: The concrete implementation
            singleton: Whether to create singleton instances
        """
        if not self._is_valid_binding(interface, implementation):
            raise ValueError(f"Invalid binding: {implementation} does not implement {interface}")
        
        self._bindings[interface] = implementation
        self._singleton_flags[interface] = singleton
        
        logger.debug(f"Bound {interface.__name__} to {implementation.__name__} (singleton={singleton})")
    
    def bind_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> None:
        """
        Bind an interface to a factory function.
        
        Args:
            interface: The interface/abstract class
            factory: Factory function that creates instances
            singleton: Whether to cache the created instance
        """
        self._factories[interface] = factory
        self._singleton_flags[interface] = singleton
        
        logger.debug(f"Bound {interface.__name__} to factory function (singleton={singleton})")
    
    def get(self, interface: Type[T]) -> T:
        """
        Resolve an instance of the interface.
        
        Args:
            interface: The interface to resolve
            
        Returns:
            Instance implementing the interface
            
        Raises:
            ValueError: If interface is not registered
        """
        if not self.is_registered(interface):
            raise ValueError(f"Interface {interface.__name__} is not registered")
        
        # Check if we need to return singleton
        if self._singleton_flags.get(interface, True):
            if interface in self._singletons:
                return self._singletons[interface]
        
        # Create instance
        instance = self._create_instance(interface)
        
        # Cache if singleton
        if self._singleton_flags.get(interface, True):
            self._singletons[interface] = instance
        
        return instance
    
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if an interface is registered."""
        return interface in self._bindings or interface in self._factories
    
    def _create_instance(self, interface: Type[T]) -> T:
        """Create an instance of the interface implementation."""
        # Check if we have a factory
        if interface in self._factories:
            return self._factories[interface]()
        
        # Get the implementation class
        implementation = self._bindings[interface]
        
        # Get constructor parameters
        constructor_params = self._get_constructor_params(implementation)
        
        # Resolve dependencies
        resolved_params = {}
        for param_name, param_type in constructor_params.items():
            if self.is_registered(param_type):
                resolved_params[param_name] = self.get(param_type)
            else:
                # Try to create without dependencies if optional
                if self._is_optional_param(implementation, param_name):
                    continue
                else:
                    logger.warning(f"Cannot resolve dependency {param_type.__name__} for {implementation.__name__}")
        
        # Create instance with resolved dependencies
        try:
            return implementation(**resolved_params)
        except Exception as e:
            raise ValueError(f"Failed to create instance of {implementation.__name__}: {str(e)}")
    
    def _get_constructor_params(self, implementation: Type) -> Dict[str, Type]:
        """Get constructor parameter types using type hints."""
        sig = inspect.signature(implementation.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                params[param_name] = param.annotation
        
        return params
    
    def _is_optional_param(self, implementation: Type, param_name: str) -> bool:
        """Check if a constructor parameter is optional."""
        sig = inspect.signature(implementation.__init__)
        param = sig.parameters.get(param_name)
        return param and param.default != inspect.Parameter.empty
    
    def _is_valid_binding(self, interface: Type, implementation: Type) -> bool:
        """Check if implementation is valid for interface."""
        try:
            # Check if implementation is a subclass of interface
            return issubclass(implementation, interface)
        except TypeError:
            # Handle cases where interface is not a class
            return True


class ContainerBuilder:
    """
    Builder for setting up the dependency injection container.
    
    Follows Builder pattern and makes container setup more readable.
    """
    
    def __init__(self):
        self._container = DependencyContainer()
    
    def bind(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> 'ContainerBuilder':
        """Bind interface to implementation and return builder for chaining."""
        self._container.bind(interface, implementation, singleton)
        return self
    
    def bind_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> 'ContainerBuilder':
        """Bind interface to factory and return builder for chaining."""
        self._container.bind_factory(interface, factory, singleton)
        return self
    
    def build(self) -> IDependencyContainer:
        """Build and return the configured container."""
        return self._container


# Convenience function for creating configured container
def create_container() -> ContainerBuilder:
    """Create a new container builder."""
    return ContainerBuilder()