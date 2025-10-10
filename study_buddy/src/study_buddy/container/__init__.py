"""
Container Module for Study Buddy Application

This module provides dependency injection capabilities for the Study Buddy application.
It includes the DI container implementation and container configuration utilities.
"""

from .di_container import (
    DependencyInjectionContainer,
    ServiceDescriptor,
    ServiceLifetime,
    get_container,
    inject
)

from .container_builder import ContainerBuilder

__all__ = [
    "DependencyInjectionContainer",
    "ServiceDescriptor", 
    "ServiceLifetime",
    "get_container",
    "inject",
    "ContainerBuilder"
]