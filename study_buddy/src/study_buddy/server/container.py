"""
Dependency Injection Container for Study Buddy MCP Server.

This module implements a Clean Architecture dependency injection container
following SOLID principles to wire all application components together.
"""

import os
from typing import Optional

# Handle imports for both module and direct execution
try:
    # Relative imports (when run as module)
    from .chunking.strategy_factory import ChunkingStrategyFactory
    from .database.connection import DatabaseConnection
    from .database.schema import SchemaManager
    from .handlers.mcp_handler import MCPHandler
    from .parsers.parser_factory import ParserFactory
    from .repositories.chunk_repository import ChunkRepository
    from .repositories.document_repository import DocumentRepository
    from .repositories.progress_repository import ProgressRepository
    from .repositories.session_repository import SessionRepository
    from .repositories.summary_repository import SummaryRepository
    from .repositories.bookmark_repository import BookmarkRepository
    from .services.chunking_service import ChunkingService
    from .services.document_service import DocumentService
    from .services.progress_service import ProgressService
    from .services.summary_service import SummaryService
    from .services.bookmark_service import BookmarkService
    from .services.prompt_service import PromptService
except ImportError:
    # Absolute imports (when run directly)
    from study_buddy.server.chunking.strategy_factory import ChunkingStrategyFactory
    from study_buddy.server.database.connection import DatabaseConnection
    from study_buddy.server.database.schema import SchemaManager
    from study_buddy.server.handlers.mcp_handler import MCPHandler
    from study_buddy.server.parsers.parser_factory import ParserFactory
    from study_buddy.server.repositories.chunk_repository import ChunkRepository
    from study_buddy.server.repositories.document_repository import DocumentRepository
    from study_buddy.server.repositories.progress_repository import ProgressRepository
    from study_buddy.server.repositories.session_repository import SessionRepository
    from study_buddy.server.repositories.summary_repository import SummaryRepository
    from study_buddy.server.repositories.bookmark_repository import BookmarkRepository
    from study_buddy.server.services.chunking_service import ChunkingService
    from study_buddy.server.services.document_service import DocumentService
    from study_buddy.server.services.progress_service import ProgressService
    from study_buddy.server.services.summary_service import SummaryService
    from study_buddy.server.services.bookmark_service import BookmarkService
    from study_buddy.server.services.prompt_service import PromptService


class Container:
    """
    Dependency injection container for Study Buddy MCP Server.

    This class follows Clean Architecture principles by:
    - Centralizing dependency wiring and configuration
    - Ensuring proper layer separation (dependencies flow inward)
    - Supporting dependency injection for testability
    - Managing singleton instances for shared resources

    SOLID Principles Applied:
    - Single Responsibility: Only manages dependency creation and wiring
    - Open/Closed: Extensible for new services without modifying existing code
    - Dependency Inversion: Wires abstractions, not concrete implementations

    Usage:
        container = Container()
        mcp_handler = container.get_mcp_handler()
        # All dependencies automatically wired
    """

    def __init__(self, database_path: Optional[str] = None, environment: str = "production"):
        """
        Initialize dependency injection container.

        Args:
            database_path: Path to SQLite database file (defaults to data/study_buddy.db)
            environment: Environment mode ("production", "testing", "development")
        """
        self.environment = environment
        self.database_path = database_path or self._get_default_database_path()

        # Singleton instances (shared across application)
        self._database_connection: Optional[DatabaseConnection] = None
        self._schema_manager: Optional[SchemaManager] = None
        self._parser_factory: Optional[ParserFactory] = None

        # Repository singletons
        self._document_repository: Optional[DocumentRepository] = None
        self._chunk_repository: Optional[ChunkRepository] = None
        self._summary_repository: Optional[SummaryRepository] = None
        self._bookmark_repository: Optional[BookmarkRepository] = None
        self._progress_repository: Optional[ProgressRepository] = None
        self._session_repository: Optional[SessionRepository] = None

        # Service singletons
        self._document_service: Optional[DocumentService] = None
        self._chunking_service: Optional[ChunkingService] = None
        self._summary_service: Optional[SummaryService] = None
        self._bookmark_service: Optional[BookmarkService] = None
        self._progress_service: Optional[ProgressService] = None
        self._prompt_service: Optional[PromptService] = None

        # Handler singletons
        self._mcp_handler: Optional[MCPHandler] = None

        # Strategy factories
        self._chunking_strategy_factory: Optional[ChunkingStrategyFactory] = None

    def _get_default_database_path(self) -> str:
        """Get default database path based on environment."""
        # First check environment variable (primary source of truth)
        env_path = os.getenv("STUDY_BUDDY_DB_PATH")
        if env_path:
            return env_path
            
        # Fallback to environment-specific defaults
        if self.environment == "testing":
            return ":memory:"  # In-memory database for tests
        elif self.environment == "development":
            return "data/study_buddy_dev.db"
        else:
            return "data/study_buddy.db"  # Standard database file

    # Infrastructure Layer (Layer 4) Dependencies

    def get_database_connection(self) -> DatabaseConnection:
        """
        Get database connection (singleton).

        Returns:
            DatabaseConnection instance
        """
        if self._database_connection is None:
            # Ensure data directory exists
            if self.database_path != ":memory:":
                os.makedirs(os.path.dirname(self.database_path), exist_ok=True)

            self._database_connection = DatabaseConnection(self.database_path)

        return self._database_connection

    def get_schema_manager(self) -> SchemaManager:
        """
        Get schema manager (singleton).

        Returns:
            SchemaManager instance
        """
        if self._schema_manager is None:
            db_connection = self.get_database_connection()
            self._schema_manager = SchemaManager(db_connection)

        return self._schema_manager

    def get_parser_factory(self) -> ParserFactory:
        """
        Get parser factory (singleton).

        Returns:
            ParserFactory instance with all parsers registered
        """
        if self._parser_factory is None:
            self._parser_factory = ParserFactory()

        return self._parser_factory

    def get_chunking_strategy_factory(self) -> ChunkingStrategyFactory:
        """
        Get chunking strategy factory (singleton).

        Returns:
            ChunkingStrategyFactory instance with all strategies registered
        """
        if self._chunking_strategy_factory is None:
            self._chunking_strategy_factory = ChunkingStrategyFactory()

        return self._chunking_strategy_factory

    # Data Access Layer (Layer 3) Dependencies

    def get_document_repository(self) -> DocumentRepository:
        """
        Get document repository (singleton).

        Returns:
            DocumentRepository with database dependency injected
        """
        if self._document_repository is None:
            db_connection = self.get_database_connection()
            self._document_repository = DocumentRepository(db_connection)

        return self._document_repository

    def get_chunk_repository(self) -> ChunkRepository:
        """
        Get chunk repository (singleton).

        Returns:
            ChunkRepository with database dependency injected
        """
        if self._chunk_repository is None:
            db_connection = self.get_database_connection()
            self._chunk_repository = ChunkRepository(db_connection)

        return self._chunk_repository

    def get_summary_repository(self) -> SummaryRepository:
        """
        Get summary repository (singleton).

        Returns:
            SummaryRepository with database dependency injected
        """
        if self._summary_repository is None:
            db_connection = self.get_database_connection()
            self._summary_repository = SummaryRepository(db_connection)

        return self._summary_repository

    def get_bookmark_repository(self) -> BookmarkRepository:
        """
        Get bookmark repository (singleton).

        Returns:
            BookmarkRepository with database dependency injected
        """
        if self._bookmark_repository is None:
            db_connection = self.get_database_connection()
            self._bookmark_repository = BookmarkRepository(db_connection)

        return self._bookmark_repository

    def get_progress_repository(self) -> ProgressRepository:
        """
        Get progress repository (singleton).

        Returns:
            ProgressRepository with database dependency injected
        """
        if self._progress_repository is None:
            db_connection = self.get_database_connection()
            self._progress_repository = ProgressRepository(db_connection)

        return self._progress_repository

    def get_session_repository(self) -> SessionRepository:
        """
        Get session repository (singleton).

        Returns:
            SessionRepository with database dependency injected
        """
        if self._session_repository is None:
            db_connection = self.get_database_connection()
            self._session_repository = SessionRepository(db_connection)

        return self._session_repository

    # Business Logic Layer (Layer 2) Dependencies

    def get_document_service(self) -> DocumentService:
        """
        Get document service (singleton).

        Returns:
            DocumentService with all dependencies injected:
            - DocumentRepository (data access)
            - ParserFactory (parsing strategy)
        """
        if self._document_service is None:
            document_repo = self.get_document_repository()
            parser_factory = self.get_parser_factory()

            self._document_service = DocumentService(
                document_repository=document_repo,
                parser_factory=parser_factory
            )

        return self._document_service

    def get_chunking_service(self) -> ChunkingService:
        """
        Get chunking service (singleton).

        Returns:
            ChunkingService with all dependencies injected:
            - DocumentRepository (document access)
            - ChunkRepository (chunk persistence)
            - ChunkingStrategyFactory (chunking strategies)
            - ParserFactory (content re-parsing)
        """
        if self._chunking_service is None:
            document_repo = self.get_document_repository()
            chunk_repo = self.get_chunk_repository()
            strategy_factory = self.get_chunking_strategy_factory()
            parser_factory = self.get_parser_factory()

            self._chunking_service = ChunkingService(
                document_repository=document_repo,
                chunk_repository=chunk_repo,
                strategy_factory=strategy_factory,
                parser_factory=parser_factory
            )

        return self._chunking_service

    def get_summary_service(self) -> SummaryService:
        """
        Get summary service (singleton).

        Returns:
            SummaryService with all dependencies injected:
            - SummaryRepository (summary persistence)
            - ChunkRepository (chunk access for validation)
            - DocumentRepository (document access for validation)
        """
        if self._summary_service is None:
            summary_repo = self.get_summary_repository()
            chunk_repo = self.get_chunk_repository()
            document_repo = self.get_document_repository()

            self._summary_service = SummaryService(
                summary_repository=summary_repo,
                chunk_repository=chunk_repo,
                document_repository=document_repo
            )

        return self._summary_service

    def get_bookmark_service(self) -> BookmarkService:
        """
        Get bookmark service (singleton).

        Returns:
            BookmarkService with all dependencies injected:
            - BookmarkRepository (bookmark persistence)
            - DocumentRepository (document validation)
            - ChunkRepository (chunk validation)
        """
        if self._bookmark_service is None:
            bookmark_repo = self.get_bookmark_repository()
            document_repo = self.get_document_repository()
            chunk_repo = self.get_chunk_repository()

            self._bookmark_service = BookmarkService(
                bookmark_repository=bookmark_repo,
                document_repository=document_repo,
                chunk_repository=chunk_repo
            )

        return self._bookmark_service

    def get_progress_service(self) -> ProgressService:
        """
        Get progress service (singleton).

        Returns:
            ProgressService with all dependencies injected:
            - ProgressRepository (progress persistence)
            - SessionRepository (session persistence)
            - DocumentRepository (document validation)
            - ChunkRepository (chunk validation)
        """
        if self._progress_service is None:
            progress_repo = self.get_progress_repository()
            session_repo = self.get_session_repository()
            document_repo = self.get_document_repository()
            chunk_repo = self.get_chunk_repository()

            self._progress_service = ProgressService(
                progress_repo=progress_repo,
                session_repo=session_repo,
                document_repo=document_repo,
                chunk_repo=chunk_repo
            )

        return self._progress_service

    def get_prompt_service(self) -> PromptService:
        """
        Get prompt service (singleton).

        Returns:
            PromptService with all dependencies injected:
            - DocumentRepository (document validation and access)
            - ChunkRepository (chunk validation and access)
            - PromptStrategyFactory (strategy creation)
        """
        if self._prompt_service is None:
            document_repo = self.get_document_repository()
            chunk_repo = self.get_chunk_repository()
            
            # Note: PromptStrategyFactory doesn't need to be singleton since it's stateless
            from study_buddy.server.prompts.strategy_factory import PromptStrategyFactory
            strategy_factory = PromptStrategyFactory()

            self._prompt_service = PromptService(
                document_repo=document_repo,
                chunk_repo=chunk_repo,
                strategy_factory=strategy_factory
            )

        return self._prompt_service

    # External Interface Layer (Layer 1) Dependencies

    def get_mcp_handler(self) -> MCPHandler:
        """
        Get MCP handler (singleton).

        Returns:
            MCPHandler with all service dependencies injected:
            - DocumentService (document operations)
            - ChunkingService (indexing operations)
            - SummaryService (summary operations)
            - BookmarkService (bookmark operations)
            - ProgressService (progress tracking operations)
            - PromptService (AI prompt generation operations)

        This is the main entry point for MCP protocol interactions.
        """
        if self._mcp_handler is None:
            document_service = self.get_document_service()
            chunking_service = self.get_chunking_service()
            summary_service = self.get_summary_service()
            bookmark_service = self.get_bookmark_service()
            progress_service = self.get_progress_service()
            prompt_service = self.get_prompt_service()

            self._mcp_handler = MCPHandler(
                document_service=document_service,
                chunking_service=chunking_service,
                summary_service=summary_service,
                bookmark_service=bookmark_service,
                progress_service=progress_service,
                prompt_service=prompt_service
            )

        return self._mcp_handler

    # Lifecycle Management

    def initialize_database(self) -> None:
        """
        Initialize database schema if needed.

        This ensures the database is properly set up with all tables,
        indexes, and FTS search capabilities before first use.

        Raises:
            Exception: If schema initialization fails
        """
        schema_manager = self.get_schema_manager()

        if not schema_manager.verify_schema():
            schema_manager.initialize_schema()

    def close(self) -> None:
        """
        Close all connections and clean up resources.

        Should be called when shutting down the application
        to ensure proper cleanup of database connections.
        """
        if self._database_connection:
            self._database_connection.close()
            self._database_connection = None

        # Reset all singletons
        self._schema_manager = None
        self._parser_factory = None
        self._chunking_strategy_factory = None
        self._document_repository = None
        self._chunk_repository = None
        self._summary_repository = None
        self._bookmark_repository = None
        self._progress_repository = None
        self._session_repository = None
        self._document_service = None
        self._chunking_service = None
        self._summary_service = None
        self._bookmark_service = None
        self._progress_service = None
        self._prompt_service = None
        self._mcp_handler = None

    def health_check(self) -> dict:
        """
        Perform health check of all system components.

        Returns:
            Health status dictionary with component statuses
        """
        health = {
            "database": "unknown",
            "schema": "unknown",
            "repositories": "unknown",
            "services": "unknown",
            "mcp_handler": "unknown",
            "overall": "unhealthy"
        }

        try:
            # Check database connection
            db = self.get_database_connection()
            db.execute("SELECT 1").fetchone()
            health["database"] = "healthy"

            # Check schema
            schema_manager = self.get_schema_manager()
            if schema_manager.verify_schema():
                health["schema"] = "healthy"
            else:
                health["schema"] = "missing_or_outdated"

            # Check repositories (basic instantiation)
            self.get_document_repository()
            self.get_chunk_repository()
            self.get_summary_repository()
            self.get_bookmark_repository()
            self.get_progress_repository()
            self.get_session_repository()
            health["repositories"] = "healthy"

            # Check services (basic instantiation)
            self.get_document_service()
            self.get_chunking_service()
            self.get_summary_service()
            self.get_bookmark_service()
            self.get_progress_service()
            self.get_prompt_service()
            health["services"] = "healthy"

            # Check MCP handler
            self.get_mcp_handler()
            health["mcp_handler"] = "healthy"

            # Overall health
            if all(status == "healthy" for key, status in health.items() if key != "overall"):
                health["overall"] = "healthy"
            else:
                health["overall"] = "degraded"

        except Exception as e:
            health["error"] = str(e)
            health["overall"] = "unhealthy"

        return health


# Global container instance for application
_container: Optional[Container] = None


def get_container(
    database_path: Optional[str] = None,
    environment: str = "production"
) -> Container:
    """
    Get global container instance (singleton pattern).

    This provides a convenient way to access the dependency injection
    container throughout the application while maintaining singleton behavior.

    Args:
        database_path: Path to database file (only used on first call)
        environment: Environment mode (only used on first call)

    Returns:
        Global Container instance
    """
    global _container

    if _container is None:
        _container = Container(database_path, environment)

    return _container


def reset_container() -> None:
    """
    Reset global container (mainly for testing).

    This closes the current container and resets the global instance,
    allowing tests to create fresh containers with different configurations.
    """
    global _container

    if _container:
        _container.close()
        _container = None


# Convenience functions for common dependencies
def get_mcp_handler() -> MCPHandler:
    """Get MCP handler from global container."""
    return get_container().get_mcp_handler()


def get_database_connection() -> DatabaseConnection:
    """Get database connection from global container."""
    return get_container().get_database_connection()


def initialize_application(
    database_path: Optional[str] = None,
    environment: str = "production"
) -> Container:
    """
    Initialize complete Study Buddy application.

    This is the main entry point for setting up the entire application
    with all dependencies properly wired and database initialized.

    Args:
        database_path: Path to database file
        environment: Environment mode

    Returns:
        Configured Container instance

    Raises:
        Exception: If application initialization fails
    """
    # Create container
    container = get_container(database_path, environment)

    # Initialize database schema
    container.initialize_database()

    # Verify health
    health = container.health_check()
    if health["overall"] != "healthy":
        raise RuntimeError(f"Application health check failed: {health}")

    return container
