"""
Migration runner utility for Study Buddy MCP Server.

Provides CLI interface and programmatic access to database migration
operations with comprehensive logging and error handling.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from ..database.connection import DatabaseConnection
from ..database.migrations import MigrationManager


class MigrationRunner:
    """
    Command-line and programmatic interface for database migrations.

    Provides safe migration execution with comprehensive logging,
    error handling, and rollback capabilities following Clean
    Architecture principles.
    """

    def __init__(self, db_path: str = "data/study_buddy.db", migrations_dir: str = "migrations"):
        """
        Initialize migration runner.

        Args:
            db_path: Path to SQLite database file
            migrations_dir: Directory containing migration files
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for migration operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def status(self) -> dict:
        """
        Get current migration status.

        Returns:
            Dictionary with migration status information
        """
        try:
            with DatabaseConnection(self.db_path) as db:
                manager = MigrationManager(db, self.migrations_dir)
                status = manager.get_migration_status()

                self.logger.info(f"Current version: {status['current_version']}")
                self.logger.info(f"Applied migrations: {status['applied_count']}")
                self.logger.info(f"Pending migrations: {status['pending_count']}")

                return status

        except Exception as e:
            self.logger.error(f"Failed to get migration status: {str(e)}")
            raise

    def migrate_up(self, target_version: Optional[str] = None) -> int:
        """
        Apply pending migrations.

        Args:
            target_version: Optional target version to migrate to

        Returns:
            Number of migrations applied
        """
        try:
            with DatabaseConnection(self.db_path) as db:
                manager = MigrationManager(db, self.migrations_dir)

                # Get status before migration
                initial_status = manager.get_migration_status()
                self.logger.info(f"Starting migration from version: {initial_status['current_version']}")

                if initial_status['pending_count'] == 0:
                    self.logger.info("No pending migrations to apply")
                    return 0

                # Apply migrations
                applied_count = manager.migrate_up(target_version)

                # Get final status
                final_status = manager.get_migration_status()
                self.logger.info(f"Migration completed. New version: {final_status['current_version']}")
                self.logger.info(f"Applied {applied_count} migration(s)")

                return applied_count

        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise

    def migrate_down(self, target_version: str) -> int:
        """
        Rollback migrations to target version.

        Args:
            target_version: Version to rollback to

        Returns:
            Number of migrations rolled back
        """
        try:
            with DatabaseConnection(self.db_path) as db:
                manager = MigrationManager(db, self.migrations_dir)

                # Get status before rollback
                initial_status = manager.get_migration_status()
                self.logger.info(f"Starting rollback from version: {initial_status['current_version']}")
                self.logger.info(f"Target version: {target_version}")

                # Confirm rollback (safety check)
                if initial_status['current_version'] and initial_status['current_version'] <= target_version:
                    self.logger.warning("Target version is not older than current version")
                    return 0

                # Perform rollback
                rollback_count = manager.migrate_down(target_version)

                # Get final status
                final_status = manager.get_migration_status()
                self.logger.info(f"Rollback completed. New version: {final_status['current_version']}")
                self.logger.info(f"Rolled back {rollback_count} migration(s)")

                return rollback_count

        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            raise

    def create_migration(self, description: str) -> str:
        """
        Create a new migration file template.

        Args:
            description: Description of the migration

        Returns:
            Path to created migration file
        """
        try:
            # Generate version number
            migrations_path = Path(self.migrations_dir)
            migrations_path.mkdir(exist_ok=True)

            existing_files = list(migrations_path.glob("*.sql"))
            next_version = f"{len(existing_files) + 1:03d}"

            # Create filename
            safe_description = "".join(c if c.isalnum() or c in "-_" else "_" for c in description.lower())
            filename = f"{next_version}_{safe_description}.sql"
            file_path = migrations_path / filename

            # Create template content
            template = f"""-- Migration: {next_version}_{safe_description}
-- Description: {description}

-- UP
-- Add your migration SQL here
-- Example:
-- CREATE TABLE example (
--     id INTEGER PRIMARY KEY,
--     name TEXT NOT NULL
-- );

-- DOWN
-- Add rollback SQL here
-- Example:
-- DROP TABLE example;
"""

            file_path.write_text(template, encoding='utf-8')

            self.logger.info(f"Created migration file: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Failed to create migration: {str(e)}")
            raise

    def validate_migrations(self) -> bool:
        """
        Validate all migration files for integrity.

        Returns:
            True if all migrations are valid
        """
        try:
            with DatabaseConnection(self.db_path) as db:
                manager = MigrationManager(db, self.migrations_dir)

                # Load and validate migrations
                migrations = manager.load_migrations_from_directory()
                manager.validate_migration_integrity(migrations)

                self.logger.info(f"Validated {len(migrations)} migration file(s)")
                return True

        except Exception as e:
            self.logger.error(f"Migration validation failed: {str(e)}")
            return False


def main():
    """Command-line interface for migration operations."""
    parser = argparse.ArgumentParser(description="Study Buddy Database Migration Runner")
    parser.add_argument("--db-path", default="data/study_buddy.db", help="Database file path")
    parser.add_argument("--migrations-dir", default="migrations", help="Migrations directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Up command
    up_parser = subparsers.add_parser("up", help="Apply pending migrations")
    up_parser.add_argument("--target", help="Target version to migrate to")

    # Down command
    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument("target", help="Target version to rollback to")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("description", help="Migration description")

    # Validate command
    subparsers.add_parser("validate", help="Validate migration files")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    runner = MigrationRunner(args.db_path, args.migrations_dir)

    try:
        if args.command == "status":
            status = runner.status()
            print("\nMigration Status:")
            print(f"  Current Version: {status['current_version']}")
            print(f"  Applied: {status['applied_count']}")
            print(f"  Pending: {status['pending_count']}")

            if status['pending_migrations']:
                print("\nPending Migrations:")
                for migration in status['pending_migrations']:
                    print(f"  - {migration['version']}: {migration['description']}")

        elif args.command == "up":
            count = runner.migrate_up(args.target)
            print(f"Applied {count} migration(s)")

        elif args.command == "down":
            count = runner.migrate_down(args.target)
            print(f"Rolled back {count} migration(s)")

        elif args.command == "create":
            file_path = runner.create_migration(args.description)
            print(f"Created migration: {file_path}")

        elif args.command == "validate":
            is_valid = runner.validate_migrations()
            if is_valid:
                print("All migrations are valid")
            else:
                print("Migration validation failed")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
