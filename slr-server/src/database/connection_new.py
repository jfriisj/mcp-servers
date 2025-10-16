"""
Enhanced database connection manager using adapter pattern.
Supports SQLite (default) and PostgreSQL for large projects.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from .adapter import DatabaseAdapter, DatabaseFactory


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Enhanced database connection manager with multi-database support.
    
    Uses the adapter pattern to support different database backends:
    - SQLite: Default for development and small projects
    - PostgreSQL: For large projects requiring advanced features
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize database manager with configuration.
        
        Args:
            config: Database configuration dict, or None for environment-based config
        """
        self._adapter: Optional[DatabaseAdapter] = None
        self._config = config
        self.logger = logging.getLogger(__name__)
    
    @property
    def adapter(self) -> DatabaseAdapter:
        """Get or create database adapter."""
        if self._adapter is None:
            self._adapter = DatabaseFactory.create_adapter(self._config)
            # Ensure tables exist
            self._adapter.create_tables_if_not_exist()
        return self._adapter
    
    def connect(self) -> Any:
        """Connect to the database."""
        return self.adapter.connect()
    
    def close(self) -> None:
        """Close database connection."""
        if self._adapter:
            self._adapter.close()
            self._adapter = None
    
    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for database transactions."""
        with self.adapter.transaction() as conn:
            yield conn
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query."""
        return self.adapter.execute(query, params)
    
    def get_sql_dialect(self) -> str:
        """Get the SQL dialect (sqlite, postgresql)."""
        return self.adapter.get_sql_dialect()
    
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.get_sql_dialect() == "postgresql"
    
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.get_sql_dialect() == "sqlite"


# Backward compatibility - create a connection instance that mimics the old DatabaseConnection
def create_database_connection(database_path: Optional[str] = None) -> DatabaseManager:
    """
    Create a database connection with backward compatibility.
    
    Args:
        database_path: Path to SQLite database (for backward compatibility)
        
    Returns:
        DatabaseManager instance
    """
    if database_path:
        # Legacy SQLite path provided
        config = {
            "type": "sqlite",
            "path": database_path
        }
        return DatabaseManager(config)
    else:
        # Use environment-based configuration
        return DatabaseManager()


# Legacy alias for backward compatibility
DatabaseConnection = DatabaseManager