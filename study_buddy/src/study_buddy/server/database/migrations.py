"""
Database migration management system for Study Buddy MCP Server.

This module provides versioned database migration capabilities with rollback
support and integrity validation following Clean Architecture principles.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..database.connection import DatabaseConnection


class Migration:
    """
    Represents a single database migration.

    Encapsulates migration metadata, SQL content, and execution tracking
    following Single Responsibility Principle.
    """

    def __init__(
        self,
        version: str,
        description: str,
        up_sql: str,
        down_sql: str,
        file_path: Optional[str] = None
    ):
        """
        Initialize migration instance.

        Args:
            version: Migration version (e.g., "001", "002")
            description: Human-readable migration description
            up_sql: SQL for applying the migration
            down_sql: SQL for rolling back the migration
            file_path: Optional path to migration file
        """
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.file_path = file_path
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of migration content."""
        content = f"{self.version}{self.description}{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class MigrationManager:
    """
    Database migration management with versioning and rollback capabilities.

    This class follows Clean Architecture Layer 4 principles by providing
    infrastructure concerns for database schema evolution:

    - Version tracking and migration state management
    - Atomic migration execution with rollback support
    - Migration validation and integrity checking
    - Safe upgrade/downgrade paths with data preservation

    SOLID Principles Applied:
    - SRP: Only manages migration execution and tracking
    - OCP: Extensible for new migration sources without modification
    - DIP: Depends on DatabaseConnection abstraction
    """

    def __init__(self, db_connection: DatabaseConnection, migrations_dir: str = "migrations"):
        """
        Initialize migration manager.

        Args:
            db_connection: Database connection manager
            migrations_dir: Directory containing migration files
        """
        self.db = db_connection
        self.migrations_dir = Path(migrations_dir)
        self.logger = logging.getLogger(__name__)
        self._ensure_migration_table()

    def _ensure_migration_table(self) -> None:
        """Create migration tracking table if it doesn't exist."""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                rollback_sql TEXT
            )
        """)
        self.db.commit()

    def load_migrations_from_directory(self) -> List[Migration]:
        """
        Load migration files from the migrations directory.

        Returns:
            List of Migration objects sorted by version

        Raises:
            ValueError: If migration files are malformed or duplicated
        """
        migrations = []

        if not self.migrations_dir.exists():
            self.logger.warning(f"Migrations directory {self.migrations_dir} not found")
            return migrations

        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            try:
                migration = self._parse_migration_file(file_path)
                migrations.append(migration)
            except Exception as e:
                raise ValueError(f"Failed to parse migration {file_path}: {str(e)}")

        return migrations

    def _parse_migration_file(self, file_path: Path) -> Migration:
        """
        Parse a migration file with -- UP and -- DOWN sections.

        Expected format:
        -- Migration: 001_initial_schema
        -- Description: Create initial database schema
        -- UP
        CREATE TABLE documents (...);
        -- DOWN
        DROP TABLE documents;

        Args:
            file_path: Path to migration SQL file

        Returns:
            Migration object

        Raises:
            ValueError: If migration format is invalid
        """
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Extract metadata
        version = None
        description = None
        up_sql = []
        down_sql = []
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith('-- Migration:'):
                version = line.split(':', 1)[1].strip()
            elif line.startswith('-- Description:'):
                description = line.split(':', 1)[1].strip()
            elif line == '-- UP':
                current_section = 'up'
            elif line == '-- DOWN':
                current_section = 'down'
            elif line.startswith('--') or not line:
                continue  # Skip comments and empty lines
            elif current_section == 'up':
                up_sql.append(line)
            elif current_section == 'down':
                down_sql.append(line)

        if not version or not description:
            raise ValueError(f"Migration file {file_path} missing version or description")

        return Migration(
            version=version,
            description=description,
            up_sql='\n'.join(up_sql),
            down_sql='\n'.join(down_sql),
            file_path=str(file_path)
        )

    def get_applied_migrations(self) -> List[Dict]:
        """Get list of applied migrations from ..database."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT version, description, checksum, applied_at, execution_time_ms
            FROM schema_migrations
            ORDER BY version
        """)

        columns = ['version', 'description', 'checksum', 'applied_at', 'execution_time_ms']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_pending_migrations(self, available_migrations: List[Migration]) -> List[Migration]:
        """
        Get migrations that haven't been applied yet.

        Args:
            available_migrations: All available migrations

        Returns:
            List of pending migrations in version order
        """
        applied_versions = {m['version'] for m in self.get_applied_migrations()}
        return [m for m in available_migrations if m.version not in applied_versions]

    def validate_migration_integrity(self, migrations: List[Migration]) -> None:
        """
        Validate migration integrity and detect conflicts.

        Args:
            migrations: Migrations to validate

        Raises:
            ValueError: If migrations are invalid or conflicted
        """
        applied = {m['version']: m['checksum'] for m in self.get_applied_migrations()}

        for migration in migrations:
            if migration.version in applied:
                if migration.checksum != applied[migration.version]:
                    raise ValueError(
                        f"Migration {migration.version} checksum mismatch. "
                        f"Applied: {applied[migration.version]}, "
                        f"File: {migration.checksum}"
                    )

    def apply_migration(self, migration: Migration) -> None:
        """
        Apply a single migration atomically.

        Args:
            migration: Migration to apply

        Raises:
            Exception: If migration execution fails
        """
        start_time = datetime.now()

        cursor = self.db.cursor()

        try:
            # Begin transaction explicitly
            cursor.execute("BEGIN TRANSACTION")

            # Execute UP SQL
            statements = [stmt.strip() for stmt in migration.up_sql.split(';') if stmt.strip()]
            for statement in statements:
                cursor.execute(statement)

            # Record migration
            cursor.execute("""
                INSERT INTO schema_migrations
                (version, description, checksum, execution_time_ms, rollback_sql)
                VALUES (?, ?, ?, ?, ?)
            """, (
                migration.version,
                migration.description,
                migration.checksum,
                int((datetime.now() - start_time).total_seconds() * 1000),
                migration.down_sql
            ))

            # Commit transaction
            cursor.execute("COMMIT")
            self.logger.info(f"Applied migration {migration.version}: {migration.description}")

        except Exception as e:
            # Rollback transaction
            cursor.execute("ROLLBACK")
            self.logger.error(f"Failed to apply migration {migration.version}: {str(e)}")
            raise

    def rollback_migration(self, version: str) -> None:
        """
        Rollback a specific migration.

        Args:
            version: Version of migration to rollback

        Raises:
            ValueError: If migration not found or rollback fails
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT rollback_sql FROM schema_migrations
            WHERE version = ?
        """, (version,))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Migration {version} not found in applied migrations")

        rollback_sql = row[0]
        if not rollback_sql:
            raise ValueError(f"Migration {version} has no rollback SQL")

        try:
            # Begin transaction explicitly
            cursor.execute("BEGIN TRANSACTION")

            # Execute rollback SQL
            statements = [stmt.strip() for stmt in rollback_sql.split(';') if stmt.strip()]
            for statement in statements:
                cursor.execute(statement)

            # Remove migration record
            cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))

            # Commit transaction
            cursor.execute("COMMIT")
            self.logger.info(f"Rolled back migration {version}")

        except Exception as e:
            # Rollback transaction
            cursor.execute("ROLLBACK")
            self.logger.error(f"Failed to rollback migration {version}: {str(e)}")
            raise

    def migrate_up(self, target_version: Optional[str] = None) -> int:
        """
        Apply all pending migrations up to target version.

        Args:
            target_version: Optional target version (applies all if None)

        Returns:
            Number of migrations applied

        Raises:
            ValueError: If target version not found or migration fails
        """
        migrations = self.load_migrations_from_directory()
        self.validate_migration_integrity(migrations)

        pending = self.get_pending_migrations(migrations)

        if target_version:
            # Filter to target version
            target_index = -1
            for i, migration in enumerate(pending):
                if migration.version == target_version:
                    target_index = i
                    break

            if target_index == -1:
                raise ValueError(f"Target version {target_version} not found")

            pending = pending[:target_index + 1]

        applied_count = 0
        for migration in pending:
            self.apply_migration(migration)
            applied_count += 1

        return applied_count

    def migrate_down(self, target_version: str) -> int:
        """
        Rollback migrations down to target version (exclusive).

        Args:
            target_version: Target version to rollback to

        Returns:
            Number of migrations rolled back
        """
        applied = self.get_applied_migrations()
        applied.reverse()  # Rollback in reverse order

        rollback_count = 0
        for migration in applied:
            if migration['version'] <= target_version:
                break

            self.rollback_migration(migration['version'])
            rollback_count += 1

        return rollback_count

    def get_current_version(self) -> Optional[str]:
        """Get the current schema version (latest applied migration)."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT version FROM schema_migrations
            ORDER BY version DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        return row[0] if row else None

    def get_migration_status(self) -> Dict:
        """
        Get comprehensive migration status information.

        Returns:
            Dictionary with migration status details
        """
        migrations = self.load_migrations_from_directory()
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations(migrations)
        current_version = self.get_current_version()

        return {
            "current_version": current_version,
            "total_migrations": len(migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": [
                {
                    "version": m["version"],
                    "description": m["description"],
                    "applied_at": m["applied_at"]
                }
                for m in applied
            ],
            "pending_migrations": [
                {
                    "version": m.version,
                    "description": m.description,
                    "file_path": m.file_path
                }
                for m in pending
            ]
        }
