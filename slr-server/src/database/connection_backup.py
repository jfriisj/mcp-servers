"""
Database connection and lifecycle management for SLR MCP Server.

This module implements Clean Architecture Layer 4 infrastructure for SQLite database
connection management with transaction support, connection pooling, and proper lifecycle
management following SOLID principles.
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional


class DatabaseConnection:
    """
    SQLite database connection manager with transaction support and lifecycle management.

    This class follows the Single Responsibility Principle (SRP) by handling only
    database connection management and lifecycle operations. It provides:

    - Connection lifecycle management (create, close, reconnect)
    - Transaction context managers for ACID compliance
    - Thread-safe connection handling
    - Proper error handling and logging
    - Database file management

    Clean Architecture Layer 4: Infrastructure
    - No dependencies on business logic or application layers
    - Pure infrastructure concern for database connectivity
    - Can be tested independently with in-memory databases
    """

    def __init__(self, database_path: str = "slr_database.db"):
        """
        Initialize database connection manager.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = Path(database_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection with proper configuration.

        Returns:
            Configured SQLite connection

        Raises:
            sqlite3.Error: If connection fails
        """
        with self._lock:
            if self._connection is None:
                try:
                    self._connection = sqlite3.connect(
                        str(self.database_path),
                        check_same_thread=False,
                        timeout=30.0,
                    )

                    # Configure connection for optimal performance and FTS5 support
                    self._configure_connection(self._connection)

                    self.logger.info(
                        f"Database connected: {self.database_path}"
                    )

                except sqlite3.Error as e:
                    self.logger.error(f"Failed to connect to database: {e}")
                    raise

            return self._connection

    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """
        Configure SQLite connection with optimal settings.

        Args:
            conn: SQLite connection to configure
        """
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Configure for better performance
        cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        cursor.execute(
            "PRAGMA synchronous = NORMAL"
        )  # Balance safety/performance
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
        cursor.execute("PRAGMA temp_store = MEMORY")  # Temp tables in memory

        # Verify FTS5 extension availability
        cursor.execute(
            "SELECT 1 FROM pragma_compile_options WHERE compile_options = 'ENABLE_FTS5'"
        )
        if not cursor.fetchone():
            self.logger.warning(
                "FTS5 extension not available - search functionality may be limited"
            )

        conn.commit()

    def close(self) -> None:
        """
        Close database connection and cleanup resources.
        """
        with self._lock:
            if self._connection:
                try:
                    self._connection.close()
                    self.logger.info("Database connection closed")
                except sqlite3.Error as e:
                    self.logger.error(
                        f"Error closing database connection: {e}"
                    )
                finally:
                    self._connection = None

    def is_connected(self) -> bool:
        """
        Check if database connection is active.

        Returns:
            True if connected, False otherwise
        """
        with self._lock:
            if self._connection is None:
                return False

            try:
                # Test connection with simple query
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                return True
            except sqlite3.Error:
                return False

    def reconnect(self) -> sqlite3.Connection:
        """
        Force reconnection to database.

        Returns:
            New database connection

        Raises:
            sqlite3.Error: If reconnection fails
        """
        self.close()
        return self.connect()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Transaction context manager for ACID compliance.

        Provides automatic transaction management with proper rollback
        on exceptions and commit on success.

        Yields:
            Database connection within transaction context

        Raises:
            sqlite3.Error: If transaction fails

        Example:
            with db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO papers ...")
                cursor.execute("INSERT INTO authors ...")
                # Automatic commit on success, rollback on exception
        """
        conn = self.connect()

        try:
            # Begin transaction
            conn.execute("BEGIN")
            self.logger.debug("Transaction started")

            yield conn

            # Commit transaction on success
            conn.commit()
            self.logger.debug("Transaction committed")

        except Exception as e:
            # Rollback transaction on any exception
            try:
                conn.rollback()
                self.logger.debug("Transaction rolled back")
            except sqlite3.Error as rollback_error:
                self.logger.error(
                    f"Failed to rollback transaction: {rollback_error}"
                )

            self.logger.error(f"Transaction failed: {e}")
            raise

    def execute(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single SQL statement.

        Args:
            query: SQL query to execute
            parameters: Query parameters

        Returns:
            Database cursor with results

        Raises:
            sqlite3.Error: If query execution fails
        """
        conn = self.connect()
        cursor = conn.cursor()
        return cursor.execute(query, parameters)

    def executemany(self, query: str, parameters_list: list) -> sqlite3.Cursor:
        """
        Execute SQL statement multiple times with different parameters.

        Args:
            query: SQL query to execute
            parameters_list: List of parameter tuples

        Returns:
            Database cursor with results

        Raises:
            sqlite3.Error: If query execution fails
        """
        conn = self.connect()
        cursor = conn.cursor()
        return cursor.executemany(query, parameters_list)

    def executescript(self, script: str) -> None:
        """
        Execute multiple SQL statements from script.

        Args:
            script: SQL script containing multiple statements

        Raises:
            sqlite3.Error: If script execution fails
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executescript(script)
        conn.commit()

    def commit(self) -> None:
        """
        Commit the current transaction.
        
        Note: It's recommended to use the transaction() context manager
        for proper transaction handling instead of manual commits.
        """
        conn = self.connect()
        conn.commit()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()

    def __del__(self):
        """Cleanup connection on destruction."""
        self.close()