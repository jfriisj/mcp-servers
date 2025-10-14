"""
Abstract base repository interface for SLR data access layer.

Defines the common CRUD operations that all repositories must implement
following the Repository pattern and Clean Architecture Layer 3 principles.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
import sqlite3

# Generic type parameter for the entity model
T = TypeVar('T')


class DatabaseConnection:
    """Database connection interface for repository layer."""
    
    def __init__(self, database_path: str = "data/slr_server.db"):
        self.database_path = database_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._configure_connection(self._connection)
        return self._connection
    
    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """Configure SQLite connection with optimal settings."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -64000")
        conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute single SQL statement."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        return cursor
    
    def commit(self) -> None:
        """Commit pending transactions."""
        if self._connection:
            self._connection.commit()


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for all SLR repository implementations.

    This class defines the contract that all repositories must follow,
    ensuring consistent data access patterns across the application.

    Follows SOLID principles:
    - Single Responsibility: Only handles data persistence operations
    - Open/Closed: Concrete repositories extend without modifying this base
    - Liskov Substitution: All repositories can be used interchangeably
    - Interface Segregation: Focused interface for data operations only
    - Dependency Inversion: Depends on DatabaseConnection abstraction

    Generic type T represents the domain model (ResearchPaper, AcademicChunk, etc.).
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize repository with database connection.

        Args:
            db: Database connection for executing queries

        Note:
            Repository depends on DatabaseConnection abstraction,
            not concrete SQLite implementation (Dependency Inversion).
        """
        self.db = db

    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create a new entity in the database.

        Args:
            entity: The domain model instance to create

        Returns:
            The created entity with populated ID and metadata

        Raises:
            RepositoryError: If creation fails

        Note:
            Implementation should:
            - Validate entity data
            - Execute INSERT statement with prepared parameters
            - Populate entity ID from database
            - Handle transaction commit/rollback
            - Map database errors to domain errors
        """
        pass

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: Primary key of the entity

        Returns:
            The entity if found, None otherwise

        Raises:
            RepositoryError: If query fails

        Note:
            Implementation should:
            - Execute SELECT with prepared statement
            - Transform database row to domain model
            - Handle case where entity doesn't exist
            - Map database errors appropriately
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update an existing entity in the database.

        Args:
            entity: The domain model instance with updated data

        Returns:
            The updated entity

        Raises:
            RepositoryError: If update fails or entity not found

        Note:
            Implementation should:
            - Validate entity has valid ID
            - Execute UPDATE with prepared parameters
            - Check that entity was actually updated
            - Handle optimistic locking if needed
            - Update entity timestamps
        """
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity from the database.

        Args:
            entity_id: Primary key of the entity to delete

        Returns:
            True if entity was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails

        Note:
            Implementation should:
            - Execute DELETE with prepared statement
            - Check if any rows were affected
            - Handle foreign key constraints appropriately
            - Clean up related data if needed (CASCADE)
        """
        pass

    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        List all entities with optional filtering.

        Args:
            filters: Optional dictionary of filter criteria
                    Format: {"field_name": value, "field2": value}

        Returns:
            List of entities matching the filters

        Raises:
            RepositoryError: If query fails

        Note:
            Implementation should:
            - Build WHERE clause from filters
            - Use prepared statements to prevent SQL injection
            - Transform all rows to domain models
            - Handle empty results gracefully
            - Support pagination if needed
        """
        pass

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            Number of entities matching the filters

        Raises:
            RepositoryError: If query fails

        Note:
            Default implementation using list_all, but concrete
            repositories should override with efficient COUNT query.
        """
        # Default implementation - override for efficiency
        return len(self.list_all(filters))

    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists by ID.

        Args:
            entity_id: Primary key to check

        Returns:
            True if entity exists, False otherwise

        Raises:
            RepositoryError: If query fails

        Note:
            Default implementation using get_by_id, but concrete
            repositories should override with efficient EXISTS query.
        """
        # Default implementation - override for efficiency
        return self.get_by_id(entity_id) is not None

    def _build_where_clause(
        self,
        filters: Optional[Dict[str, Any]]
    ) -> tuple[str, List[Any]]:
        """
        Build WHERE clause and parameters from filters.

        Args:
            filters: Dictionary of field:value filters

        Returns:
            Tuple of (where_clause_string, parameter_list)

        Note:
            Helper method for concrete repositories to build
            dynamic WHERE clauses safely.
        """
        if not filters:
            return "", []

        conditions = []
        parameters = []

        for field, value in filters.items():
            # Validate field name to prevent SQL injection
            if not field.replace('_', '').isalnum():
                raise ValueError(f"Invalid filter field name: {field}")

            conditions.append(f"{field} = ?")
            parameters.append(value)

        where_clause = " AND ".join(conditions)
        return f"WHERE {where_clause}", parameters


class RepositoryError(Exception):
    """
    Base exception for repository layer errors.

    Used to wrap database-specific exceptions and provide
    domain-appropriate error messages.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize repository error.

        Args:
            message: Domain-appropriate error message
            original_error: Original database exception if available
        """
        super().__init__(message)
        self.original_error = original_error


class EntityNotFoundError(RepositoryError):
    """Raised when an entity cannot be found by ID."""

    def __init__(self, entity_type: str, entity_id: int):
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of entity that wasn't found
            entity_id: ID that was searched for
        """
        super().__init__(f"{entity_type} with ID {entity_id} not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create an entity that already exists."""

    def __init__(self, entity_type: str, identifier: str):
        """
        Initialize duplicate entity error.

        Args:
            entity_type: Type of entity that's duplicated
            identifier: Unique identifier that's duplicated
        """
        super().__init__(f"{entity_type} with {identifier} already exists")
        self.entity_type = entity_type
        self.identifier = identifier