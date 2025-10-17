"""
Application Layer - Use Cases and Application Services

This layer contains:
- Use case implementations
- Application services
- Data transfer objects (DTOs)
- Command and query handlers

This layer orchestrates domain objects to fulfill application requirements.
"""

# Application Services
from .container import IDependencyContainer

# Handlers
from .handlers.solid_mcp_handler import SOLIDMCPHandler

__all__ = [
    # Container
    "IDependencyContainer",
    # Handlers
    "SOLIDMCPHandler",
]