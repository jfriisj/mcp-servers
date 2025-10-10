"""
Database schema management and initialization for Study Buddy MCP Server.

This module implements Clean Architecture Layer 4 infrastructure for database
schema creation, migration, and management following SOLID principles and FTS5
search setup.
"""

import logging

from ..database.connection import DatabaseConnection


class SchemaManager:
    """
    Database schema management for Study Buddy application.

    This class follows the Single Responsibility Principle (SRP) by handling
    only database schema operations and initialization. It provides:

    - Schema creation and initialization
    - FTS5 full-text search index setup
    - Schema version management
    - Table creation with proper constraints
    - Index optimization

    Clean Architecture Layer 4: Infrastructure
    - No dependencies on business logic or application layers
    - Pure infrastructure concern for database schema
    - Can be tested independently with in-memory databases
    """

    # Current schema version for migration tracking
    SCHEMA_VERSION = 1

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize schema manager with database connection.

        Args:
            db_connection: Database connection manager instance
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)

    def initialize_schema(self) -> None:
        """
        Initialize complete database schema with all tables and indexes.

        Creates all necessary tables, indexes, and FTS5 search tables
        in the correct order respecting foreign key dependencies.

        Raises:
            sqlite3.Error: If schema creation fails
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Create tables in dependency order
                self._create_documents_table(cursor)
                self._create_chunks_table(cursor)
                self._create_summaries_table(cursor)
                self._create_bookmarks_table(cursor)
                self._create_reading_progress_table(cursor)
                self._create_study_sessions_table(cursor)

                # Create FTS5 search indexes
                self._create_search_indexes(cursor)

                # Create additional indexes for performance
                self._create_performance_indexes(cursor)

                # Initialize schema metadata
                self._initialize_metadata(cursor)

                self.logger.info("Database schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize schema: {e}")
            raise

    def _create_documents_table(self, cursor) -> None:
        """
        Create documents table with metadata and constraints.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                file_type TEXT NOT NULL CHECK (
                    file_type IN ('pdf', 'docx', 'pptx', 'md', 'txt')
                ),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                total_pages INTEGER,
                total_words INTEGER,
                tags TEXT DEFAULT '[]',  -- JSON array of strings
                notes TEXT,
                indexed BOOLEAN DEFAULT 0,
                summarized BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.logger.debug("Documents table created")

    def _create_chunks_table(self, cursor) -> None:
        """
        Create chunks table with document relationships.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_type TEXT DEFAULT 'auto' CHECK (
                    chunk_type IN (
                        'chapter', 'section', 'heading', 'slide',
                        'paragraph', 'auto'
                    )
                ),
                title TEXT,
                content TEXT NOT NULL,
                start_page INTEGER,
                end_page INTEGER,
                word_count INTEGER,
                metadata TEXT DEFAULT '{}',  -- JSON object for chunk-specific metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(document_id, chunk_index)
            )
        """
        )

        self.logger.debug("Chunks table created")

    def _create_summaries_table(self, cursor) -> None:
        """
        Create summaries table for AI-generated content.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                chunk_id INTEGER,
                summary_type TEXT NOT NULL CHECK (
                    summary_type IN ('brief', 'standard', 'detailed', 'custom')
                ),
                summary_content TEXT NOT NULL,
                word_count INTEGER,
                model_name TEXT,  -- AI model used for generation
                generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',  -- JSON object for summary metadata

                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,

                -- Ensure either document_id or chunk_id is set, but not both
                CHECK (
                    (document_id IS NOT NULL AND chunk_id IS NULL) OR
                    (document_id IS NULL AND chunk_id IS NOT NULL)
                ),

                -- Prevent duplicate summaries of same type for same target
                UNIQUE(document_id, summary_type, chunk_id)
            )
        """
        )

        self.logger.debug("Summaries table created")

    def _create_bookmarks_table(self, cursor) -> None:
        """
        Create bookmarks table for user bookmarks and annotations.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                document_id INTEGER NOT NULL,
                chunk_id INTEGER,  -- Optional: bookmark specific chunk
                category TEXT NOT NULL DEFAULT 'General',
                notes TEXT,
                page_number INTEGER,  -- For PDF page references
                position TEXT,  -- For specific position within content
                tags TEXT,  -- Comma-separated tags
                color TEXT NOT NULL DEFAULT '#FFD700' CHECK (
                    color GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]' OR
                    color GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
                ),
                is_favorite BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,

                -- Ensure valid page number if provided
                CHECK (page_number IS NULL OR page_number > 0)
            )
        """
        )

        self.logger.debug("Bookmarks table created")

    def _create_reading_progress_table(self, cursor) -> None:
        """
        Create reading progress table for tracking document/chunk reading progress.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reading_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_id INTEGER,  -- NULL for document-level progress
                current_page INTEGER,
                current_position INTEGER DEFAULT 0,
                completion_percentage REAL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 100.0),
                first_read_time TIMESTAMP,
                last_read_time TIMESTAMP,
                completion_date TIMESTAMP,
                total_time_spent INTEGER DEFAULT 0,  -- in seconds
                session_count INTEGER DEFAULT 0,
                is_completed BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,

                -- Unique constraint: one progress entry per document/chunk combination
                UNIQUE(document_id, chunk_id),

                -- Ensure valid page number if provided
                CHECK (current_page IS NULL OR current_page > 0),
                -- Ensure valid position
                CHECK (current_position >= 0),
                -- Ensure valid time spent
                CHECK (total_time_spent >= 0),
                -- Ensure valid session count
                CHECK (session_count >= 0)
            )
        """
        )

        self.logger.debug("Reading progress table created")

    def _create_study_sessions_table(self, cursor) -> None:
        """
        Create study sessions table for tracking focused study periods.

        Args:
            cursor: Database cursor for executing statements
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_id INTEGER,  -- NULL for document-level sessions
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                planned_duration INTEGER,  -- in seconds
                actual_duration INTEGER,   -- in seconds
                session_type TEXT NOT NULL DEFAULT 'reading' CHECK (
                    session_type IN ('reading', 'reviewing', 'analyzing', 'note_taking', 'researching')
                ),
                status TEXT NOT NULL DEFAULT 'active' CHECK (
                    status IN ('active', 'paused', 'completed', 'cancelled', 'interrupted')
                ),
                start_page INTEGER,
                end_page INTEGER,
                start_position INTEGER,
                end_position INTEGER,
                focus_score REAL CHECK (focus_score IS NULL OR (focus_score >= 1.0 AND focus_score <= 10.0)),
                productivity_score REAL CHECK (productivity_score IS NULL OR (productivity_score >= 1.0 AND productivity_score <= 10.0)),
                interruption_count INTEGER DEFAULT 0 CHECK (interruption_count >= 0),
                goals TEXT,
                notes TEXT,
                achievements TEXT,
                challenges TEXT,
                words_read INTEGER CHECK (words_read IS NULL OR words_read >= 0),
                pages_read INTEGER CHECK (pages_read IS NULL OR pages_read >= 0),
                concepts_learned INTEGER CHECK (concepts_learned IS NULL OR concepts_learned >= 0),
                questions_raised INTEGER CHECK (questions_raised IS NULL OR questions_raised >= 0),
                tags TEXT,  -- JSON array of tags
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,

                -- Ensure valid page ranges
                CHECK (start_page IS NULL OR start_page > 0),
                CHECK (end_page IS NULL OR end_page > 0),
                CHECK (start_page IS NULL OR end_page IS NULL OR end_page >= start_page),

                -- Ensure valid position ranges
                CHECK (start_position IS NULL OR start_position >= 0),
                CHECK (end_position IS NULL OR end_position >= 0),
                CHECK (start_position IS NULL OR end_position IS NULL OR end_position >= start_position),

                -- Ensure valid durations
                CHECK (planned_duration IS NULL OR planned_duration > 0),
                CHECK (actual_duration IS NULL OR actual_duration > 0),

                -- Ensure logical time ordering
                CHECK (start_time IS NULL OR end_time IS NULL OR end_time >= start_time)
            )
        """
        )

        self.logger.debug("Study sessions table created")

    def _create_search_indexes(self, cursor) -> None:
        """
        Create FTS5 full-text search indexes for efficient searching.

        Args:
            cursor: Database cursor for executing statements
        """
        # FTS5 index for documents (title, content via chunks)
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                document_id UNINDEXED,
                title,
                content
            )
        """
        )

        # FTS5 index for chunks (title and content)
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                title,
                content
            )
        """
        )

        # FTS5 index for summaries
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS summaries_fts USING fts5(
                summary_id UNINDEXED,
                document_id UNINDEXED,
                chunk_id UNINDEXED,
                summary_content,
                content=''
            )
        """
        )

        # FTS5 index for bookmarks
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts USING fts5(
                bookmark_id UNINDEXED,
                document_id UNINDEXED,
                title,
                notes,
                tags,
                content=''
            )
        """
        )

        # Create triggers to maintain FTS5 indexes
        self._create_fts_triggers(cursor)

        self.logger.debug("FTS5 search indexes created")

    def _create_fts_triggers(self, cursor) -> None:
        """
        Create triggers to automatically maintain FTS5 indexes.

        Args:
            cursor: Database cursor for executing statements
        """
        # Document FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents
            BEGIN
                INSERT INTO documents_fts(document_id, title, content)
                VALUES (NEW.id, NEW.title, '');
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents
            BEGIN
                DELETE FROM documents_fts WHERE document_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents
            BEGIN
                UPDATE documents_fts
                SET title = NEW.title
                WHERE document_id = NEW.id;
            END
        """
        )

        # Chunk FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_insert AFTER INSERT ON chunks
            BEGIN
                INSERT INTO chunks_fts(chunk_id, document_id, title, content)
                VALUES (NEW.id, NEW.document_id, NEW.title, NEW.content);

                -- Update document FTS with aggregated chunk content
                UPDATE documents_fts
                SET content = (
                    SELECT GROUP_CONCAT(content, ' ')
                    FROM chunks
                    WHERE document_id = NEW.document_id
                )
                WHERE document_id = NEW.document_id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_delete AFTER DELETE ON chunks
            BEGIN
                DELETE FROM chunks_fts WHERE chunk_id = OLD.id;

                -- Update document FTS content
                UPDATE documents_fts
                SET content = COALESCE((
                    SELECT GROUP_CONCAT(content, ' ')
                    FROM chunks
                    WHERE document_id = OLD.document_id
                ), '')
                WHERE document_id = OLD.document_id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_update AFTER UPDATE ON chunks
            BEGIN
                UPDATE chunks_fts
                SET title = NEW.title, content = NEW.content
                WHERE chunk_id = NEW.id;

                -- Update document FTS content
                UPDATE documents_fts
                SET content = (
                    SELECT GROUP_CONCAT(content, ' ')
                    FROM chunks
                    WHERE document_id = NEW.document_id
                )
                WHERE document_id = NEW.document_id;
            END
        """
        )

        # Summary FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS summaries_fts_insert AFTER INSERT ON summaries
            BEGIN
                INSERT INTO summaries_fts(summary_id, document_id, chunk_id, summary_content)
                VALUES (NEW.id, NEW.document_id, NEW.chunk_id, NEW.summary_content);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS summaries_fts_delete AFTER DELETE ON summaries
            BEGIN
                DELETE FROM summaries_fts WHERE summary_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS summaries_fts_update AFTER UPDATE ON summaries
            BEGIN
                UPDATE summaries_fts
                SET summary_content = NEW.summary_content
                WHERE summary_id = NEW.id;
            END
        """
        )

        # Bookmark FTS triggers
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_insert AFTER INSERT ON bookmarks
            BEGIN
                INSERT INTO bookmarks_fts(bookmark_id, document_id, title, notes, tags)
                VALUES (NEW.id, NEW.document_id, NEW.title, NEW.notes, NEW.tags);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_delete AFTER DELETE ON bookmarks
            BEGIN
                DELETE FROM bookmarks_fts WHERE bookmark_id = OLD.id;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_update AFTER UPDATE ON bookmarks
            BEGIN
                UPDATE bookmarks_fts
                SET title = NEW.title, notes = NEW.notes, tags = NEW.tags
                WHERE bookmark_id = NEW.id;
            END
        """
        )

        self.logger.debug("FTS5 triggers created")

    def _create_performance_indexes(self, cursor) -> None:
        """
        Create additional indexes for query performance optimization.

        Args:
            cursor: Database cursor for executing statements
        """
        # Document indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_indexed ON documents(indexed)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path)"
        )

        # Chunk indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_document_index ON chunks(document_id, chunk_index)"
        )

        # Summary indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_summaries_document_id ON summaries(document_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_summaries_chunk_id ON summaries(chunk_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_summaries_type ON summaries(summary_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_summaries_date ON summaries(generation_date)"
        )

        # Bookmark indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_document_id ON bookmarks(document_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_chunk_id ON bookmarks(chunk_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_category ON bookmarks(category)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_favorite ON bookmarks(is_favorite)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON bookmarks(created_at)"
        )

        # Reading progress indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_progress_document_id ON reading_progress(document_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_progress_chunk_id ON reading_progress(chunk_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_progress_completed ON reading_progress(is_completed)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_progress_last_read ON reading_progress(last_read_time)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reading_progress_completion ON reading_progress(completion_percentage)"
        )

        # Study session indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_document_id ON study_sessions(document_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_chunk_id ON study_sessions(chunk_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_status ON study_sessions(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_type ON study_sessions(session_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_start_time ON study_sessions(start_time)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_end_time ON study_sessions(end_time)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_study_sessions_active ON study_sessions(status) WHERE status IN ('active', 'paused')"
        )

        self.logger.debug("Performance indexes created")

    def _initialize_metadata(self, cursor) -> None:
        """
        Initialize schema metadata and version tracking.

        Args:
            cursor: Database cursor for executing statements
        """
        # Create metadata table for schema versioning
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert schema version
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_metadata (key, value)
            VALUES ('schema_version', ?), ('initialized_at', CURRENT_TIMESTAMP)
        """,
            (str(self.SCHEMA_VERSION),),
        )

        self.logger.debug(
            f"Schema metadata initialized (version {self.SCHEMA_VERSION})"
        )

    def get_schema_version(self) -> int:
        """
        Get current schema version from ..database.

        Returns:
            Schema version number, 0 if not initialized
        """
        try:
            cursor = self.db.execute(
                "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
            )
            result = cursor.fetchone()
            return int(result[0]) if result else 0
        except Exception:
            return 0

    def verify_schema(self) -> bool:
        """
        Verify that database schema is properly initialized.

        Returns:
            True if schema is valid, False otherwise
        """
        try:
            required_tables = [
                "documents",
                "chunks",
                "summaries",
                "bookmarks",
                "reading_progress",
                "study_sessions",
                "schema_metadata",
            ]
            required_fts_tables = [
                "documents_fts",
                "chunks_fts",
                "summaries_fts",
                "bookmarks_fts",
            ]

            cursor = self.db.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            )

            existing_tables = {row[0] for row in cursor.fetchall()}

            # Check all required tables exist
            missing_tables = (
                set(required_tables + required_fts_tables) - existing_tables
            )
            if missing_tables:
                self.logger.error(f"Missing tables: {missing_tables}")
                return False

            # Check schema version
            current_version = self.get_schema_version()
            if current_version != self.SCHEMA_VERSION:
                self.logger.error(
                    f"Schema version mismatch: {current_version} != {self.SCHEMA_VERSION}"
                )
                return False

            self.logger.info("Schema verification successful")
            return True

        except Exception as e:
            self.logger.error(f"Schema verification failed: {e}")
            return False

    def drop_schema(self) -> None:
        """
        Drop all schema objects (for testing/cleanup).

        WARNING: This will delete all data!

        Raises:
            sqlite3.Error: If schema deletion fails
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Drop FTS tables first (they may reference main tables)
                fts_tables = ["documents_fts", "chunks_fts", "summaries_fts", "bookmarks_fts"]
                for table in fts_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                # Drop main tables in reverse dependency order
                main_tables = [
                    "summaries",
                    "bookmarks",
                    "reading_progress",
                    "study_sessions",
                    "chunks",
                    "documents",
                    "schema_metadata",
                ]
                for table in main_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                self.logger.warning("All schema objects dropped")

        except Exception as e:
            self.logger.error(f"Failed to drop schema: {e}")
            raise


def initialize_database(
    database_path: str = "data/study_buddy.db",
) -> DatabaseConnection:
    """
    Initialize database with schema for Study Buddy application.

    This is a convenience function for setting up a complete database
    with proper schema and returning a configured connection.

    Args:
        database_path: Path to SQLite database file

    Returns:
        Configured DatabaseConnection instance

    Raises:
        sqlite3.Error: If database initialization fails
    """
    # Create database connection
    db = DatabaseConnection(database_path)

    # Initialize schema
    schema_manager = SchemaManager(db)

    # Check if schema needs initialization
    if not schema_manager.verify_schema():
        schema_manager.initialize_schema()

    return db
