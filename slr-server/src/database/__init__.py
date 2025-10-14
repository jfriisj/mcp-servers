"""
Database infrastructure for Systematic Literature Review MCP Server.

This module provides database connection management, schema initialization,
and migration support for academic research data persistence following
Clean Architecture Layer 4 principles.

Key components:
- DatabaseConnection: Connection lifecycle and transaction management
- SchemaManager: Schema creation and versioning
- Database: Main database interface combining connection and schema management

Example usage:
    from database import Database
    
    db = Database("slr_database.db")
    # Database is automatically initialized with proper schema
    
    # Use with repositories
    paper_repo = PaperRepository(db)
"""

from .connection import DatabaseConnection
from .schema import SchemaManager


class Database:
    """
    Main database interface combining connection and schema management.
    
    This class provides a unified interface for database operations,
    automatically handling connection setup and schema initialization.
    
    Clean Architecture Layer 4: Infrastructure
    - Pure infrastructure concern
    - No business logic dependencies
    - Framework-agnostic implementation
    """
    
    def __init__(self, database_path: str = "slr_database.db"):
        """
        Initialize database with automatic schema setup.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.connection = DatabaseConnection(database_path)
        self.schema_manager = SchemaManager(self.connection)
        
        # Initialize schema if needed
        if not self.schema_manager.verify_schema():
            self.schema_manager.initialize_schema()
    
    def __getattr__(self, name):
        """Delegate attribute access to connection for convenience."""
        return getattr(self.connection, name)


__all__ = [
    'Database',
    'DatabaseConnection', 
    'SchemaManager'
]