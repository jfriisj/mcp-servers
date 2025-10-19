"""
Database adapter interface and implementations for SLR MCP Server.
Supports SQLite (default) and PostgreSQL for large projects.
"""

import logging
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional
import threading


logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""
    
    @abstractmethod
    def connect(self) -> Any:
        """Connect to the database."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for database transactions."""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query."""
        pass
    
    @abstractmethod
    def create_tables_if_not_exist(self) -> None:
        """Create tables if they don't exist."""
        pass
    
    @abstractmethod
    def get_sql_dialect(self) -> str:
        """Get the SQL dialect (sqlite, postgresql)."""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""
    
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self._connection: Optional[Any] = None
        self._lock = threading.RLock()
        
        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
    
    def connect(self) -> Any:
        """Connect to SQLite database."""
        if self._connection is None:
            import sqlite3
            self._connection = sqlite3.connect(
                str(self.database_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            logger.info(f"SQLite connected: {self.database_path}")
        return self._connection
    
    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                logger.info("SQLite connection closed")
    
    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """SQLite transaction context manager."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"SQLite transaction rollback: {e}")
            raise
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute SQLite query."""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            return cursor.execute(query, params)
        return cursor.execute(query)
    
    def create_tables_if_not_exist(self) -> None:
        """Create SQLite tables if they don't exist."""
        from .schema import SchemaManager
        from .connection import DatabaseConnection
        
        # Create a DatabaseConnection instance for the schema manager
        db_connection = DatabaseConnection(str(self.database_path))
        schema_manager = SchemaManager(db_connection)
        schema_manager.initialize_schema()
        db_connection.close()
        logger.info("SQLite tables created/verified")
    
    def get_sql_dialect(self) -> str:
        return "sqlite"


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._connection: Optional[Any] = None
        self._lock = threading.RLock()
    
    def connect(self) -> Any:
        """Connect to PostgreSQL database."""
        if self._connection is None:
            try:
                import psycopg2
                import psycopg2.extras
                
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                self._connection.autocommit = False
                logger.info(f"PostgreSQL connected: {self.host}:{self.port}/{self.database}")
                
            except ImportError:
                raise RuntimeError(
                    "PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary"
                )
        return self._connection
    
    def close(self) -> None:
        """Close PostgreSQL connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                logger.info("PostgreSQL connection closed")
    
    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """PostgreSQL transaction context manager."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"PostgreSQL transaction rollback: {e}")
            raise
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute PostgreSQL query."""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
    
    def create_tables_if_not_exist(self) -> None:
        """Create PostgreSQL tables if they don't exist."""
        from .schema_postgresql import create_tables_postgresql
        conn = self.connect()
        create_tables_postgresql(conn)
        logger.info("PostgreSQL tables created/verified")
    
    def get_sql_dialect(self) -> str:
        return "postgresql"


class DatabaseFactory:
    """Factory for creating database adapters based on configuration."""
    
    @staticmethod
    def create_adapter(config: Optional[Dict[str, Any]] = None) -> DatabaseAdapter:
        """
        Create database adapter based on configuration.
        
        Args:
            config: Database configuration dict or None for environment-based config
            
        Returns:
            DatabaseAdapter instance
        """
        if config is None:
            config = DatabaseFactory._get_config_from_env()
        
        db_type = config.get("type", "sqlite").lower()
        
        if db_type == "sqlite":
            db_path = config.get("path", "database/slr_database.db")
            return SQLiteAdapter(db_path)
            
        elif db_type == "postgresql":
            return PostgreSQLAdapter(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "slr_server"),
                user=config.get("user", "postgres"),
                password=config.get("password", "")
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def _get_config_from_env() -> Dict[str, Any]:
        """Get database configuration from environment variables."""
        # Check for PostgreSQL configuration first
        if os.getenv("POSTGRES_HOST") or os.getenv("DATABASE_URL"):
            return {
                "type": "postgresql",
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "slr_server"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
            }
        
        # Default to SQLite
        return {
            "type": "sqlite",
            "path": os.getenv("DATABASE_PATH", "database/slr_database.db")
        }