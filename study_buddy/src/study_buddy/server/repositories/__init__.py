"""Repository layer for data access operations.

This package contains all repository implementations following
the Repository pattern and Clean Architecture Layer 3 principles.

The repository layer provides:
- Abstract base repository for consistent CRUD operations
- Concrete repositories for each domain entity
- Transaction management and error handling
- Database abstraction for business logic layers

Dependencies:
- Database connection abstraction
- Domain models for type safety
- No business logic or external protocols
"""

from .base_repository import (
    BaseRepository,
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
)
from .document_repository import DocumentRepository

__all__ = [
    "BaseRepository",
    "DocumentRepository",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
]
