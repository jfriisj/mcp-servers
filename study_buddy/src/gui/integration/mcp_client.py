"""
Study Buddy GUI - MCP Client Interface Foundation

This module provides the abstract interfaces and base classes that define the contract
for MCP protocol communication. It establishes the foundation for Clean Architecture
dependency inversion, allowing GUI components to depend on abstractions rather than
concrete MCP protocol implementations.

Architecture: Clean Architecture Layer 3 (Data Access Abstraction)
Patterns: Abstract Factory, Observer, Strategy, Command
SOLID: DIP (abstractions for dependencies), ISP (focused interfaces), SRP (single interface responsibility)
"""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Integration with existing error handling and logging systems
from gui.error_handling import (
    get_debug_logger,
    get_error_tracker,
    ErrorSeverity,
    ErrorCategory,
)


class ConnectionState(Enum):
    """MCP connection state enumeration for health monitoring."""

    DISCONNECTED = "disconnected"  # Not connected to MCP server
    CONNECTING = "connecting"  # Establishing connection
    CONNECTED = "connected"  # Successfully connected and healthy
    RECONNECTING = "reconnecting"  # Attempting to reconnect after failure
    ERROR = "error"  # Connection error state
    DEGRADED = "degraded"  # Connected but with performance issues


class OperationStatus(Enum):
    """Status of MCP operation execution."""

    PENDING = "pending"  # Operation queued for execution
    RUNNING = "running"  # Operation currently executing
    COMPLETED = "completed"  # Operation completed successfully
    FAILED = "failed"  # Operation failed with error
    CANCELLED = "cancelled"  # Operation was cancelled
    TIMEOUT = "timeout"  # Operation timed out


class ProgressPhase(Enum):
    """Phases of MCP operation progress for detailed tracking."""

    VALIDATING = auto()  # Validating input parameters
    CONNECTING = auto()  # Establishing server connection
    TRANSMITTING = auto()  # Sending request to server
    PROCESSING = auto()  # Server processing request
    RECEIVING = auto()  # Receiving response from server
    FINALIZING = auto()  # Processing and validating response


@dataclass
class OperationProgress:
    """Progress information for long-running MCP operations."""

    operation_id: str
    operation_name: str
    phase: ProgressPhase
    progress_percent: float  # 0.0 to 100.0
    current_step: str
    total_steps: Optional[int] = None
    elapsed_time_ms: float = 0.0
    estimated_remaining_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate progress data."""
        self.progress_percent = max(0.0, min(100.0, self.progress_percent))


@dataclass
class MCPResponse:
    """
    Standardized response container for all MCP operations.

    Provides consistent structure for success/error handling and integrates
    with the GUI error handling system for comprehensive error tracking.
    """

    success: bool
    operation_id: str
    operation_name: str
    data: Optional[Any] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    timestamp: Optional[datetime] = None
    server_version: Optional[str] = None

    def __post_init__(self):
        """Initialize response with current timestamp."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ConnectionHealth:
    """Health status information for MCP server connection."""

    is_connected: bool
    connection_state: ConnectionState
    last_successful_operation: Optional[datetime] = None
    last_error: Optional[str] = None
    round_trip_time_ms: Optional[float] = None
    server_version: Optional[str] = None
    active_operations: int = 0
    total_operations: int = 0
    error_count: int = 0
    uptime_seconds: float = 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.error_count / self.total_operations) * 100.0


# Type aliases for callback functions
ProgressCallback = Callable[[OperationProgress], None]
ConnectionCallback = Callable[[ConnectionState], None]
ErrorCallback = Callable[[Exception, Dict[str, Any]], None]

# Generic type for async operations
T = TypeVar("T")


class IProgressTracker(ABC):
    """Interface for tracking progress of long-running operations."""

    @abstractmethod
    def start_operation(
        self,
        operation_id: str,
        operation_name: str,
        estimated_duration_ms: Optional[float] = None,
    ) -> None:
        """Start tracking a new operation."""
        pass

    @abstractmethod
    def update_progress(
        self,
        operation_id: str,
        phase: ProgressPhase,
        progress_percent: float,
        current_step: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update operation progress."""
        pass

    @abstractmethod
    def complete_operation(self, operation_id: str, success: bool) -> None:
        """Mark operation as completed."""
        pass

    @abstractmethod
    def cancel_operation(self, operation_id: str) -> None:
        """Cancel a running operation."""
        pass


class IConnectionManager(ABC):
    """Interface for MCP server connection management."""

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to MCP server.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect from MCP server."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if currently connected to MCP server.

        Returns:
            True if connected and healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_connection_health(self) -> ConnectionHealth:
        """
        Get comprehensive connection health information.

        Returns:
            ConnectionHealth with current status and statistics
        """
        pass

    @abstractmethod
    def add_connection_listener(self, callback: ConnectionCallback) -> None:
        """Add callback for connection state changes."""
        pass

    @abstractmethod
    def remove_connection_listener(self, callback: ConnectionCallback) -> None:
        """Remove connection state change callback."""
        pass


class IToolInvoker(ABC):
    """Interface for MCP tool execution with validation and progress tracking."""

    @abstractmethod
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> MCPResponse:
        """
        Invoke MCP tool with comprehensive validation and progress tracking.

        Args:
            tool_name: Name of MCP tool to invoke
            parameters: Tool parameters (will be validated against schema)
            timeout: Optional timeout override for this operation
            progress_callback: Optional callback for progress updates

        Returns:
            MCPResponse with operation result

        Raises:
            ConnectionError: If not connected to MCP server
            ValidationError: If parameters fail schema validation
            TimeoutError: If operation times out
            ToolNotFoundError: If specified tool doesn't exist
        """
        pass

    @abstractmethod
    async def get_available_tools(self) -> List[str]:
        """
        Get list of available MCP tools.

        Returns:
            List of tool names available on the server
        """
        pass

    @abstractmethod
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Get parameter schema for specified tool.

        Args:
            tool_name: Name of tool to get schema for

        Returns:
            Tool parameter schema as dictionary
        """
        pass


class IConfigurationProvider(ABC):
    """Interface for MCP client configuration management."""

    @abstractmethod
    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration parameters."""
        pass

    @abstractmethod
    def get_operation_config(self) -> Dict[str, Any]:
        """Get operation configuration parameters."""
        pass

    @abstractmethod
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration parameters."""
        pass

    @abstractmethod
    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """Update configuration section with new values."""
        pass

    @abstractmethod
    def add_config_listener(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Add callback for configuration changes."""
        pass


class IMCPClient(ABC):
    """
    Primary interface for MCP client operations.

    This is the main interface that GUI components depend on for all MCP
    server communication. It coordinates connection management, tool invocation,
    and error handling while providing a clean abstraction over the MCP protocol.

    Design Principles:
    - Single entry point for all MCP operations (Facade pattern)
    - Async-first design for non-blocking GUI operations
    - Comprehensive error handling with detailed context
    - Progress tracking for long-running operations
    - Health monitoring and automatic recovery
    - Type-safe parameter validation
    """

    # Connection Management
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to MCP server with health monitoring.

        Returns:
            True if connection established successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server gracefully."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """
        Check if client is connected and healthy.

        Returns:
            True if client can perform operations
        """
        pass

    @abstractmethod
    async def get_health_status(self) -> ConnectionHealth:
        """Get detailed health and performance information."""
        pass

    # Event Management
    @abstractmethod
    def add_connection_listener(self, callback: ConnectionCallback) -> None:
        """Add callback for connection state changes."""
        pass

    @abstractmethod
    def remove_connection_listener(self, callback: ConnectionCallback) -> None:
        """Remove connection state callback."""
        pass

    @abstractmethod
    def add_error_listener(self, callback: ErrorCallback) -> None:
        """Add callback for error events."""
        pass

    @abstractmethod
    def remove_error_listener(self, callback: ErrorCallback) -> None:
        """Remove error event callback."""
        pass

    # Document Management Operations
    @abstractmethod
    async def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> MCPResponse:
        """
        Upload and parse a document file.

        Args:
            file_path: Path to document file
            title: Optional document title override
            tags: Optional tags for categorization
            progress_callback: Optional progress tracking

        Returns:
            MCPResponse with upload result including document_id
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: int) -> MCPResponse:
        """
        Retrieve document metadata by ID.

        Args:
            document_id: Unique document identifier

        Returns:
            MCPResponse with document information
        """
        pass

    @abstractmethod
    async def list_documents(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 20, offset: int = 0
    ) -> MCPResponse:
        """
        List documents with optional filtering and pagination.

        Args:
            filters: Optional filters (file_type, tags, date_range, etc.)
            limit: Maximum number of documents to return
            offset: Number of documents to skip (pagination)

        Returns:
            MCPResponse with list of documents and total count
        """
        pass

    @abstractmethod
    async def search_documents(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20
    ) -> MCPResponse:
        """
        Search documents using full-text search.

        Args:
            query: Search query string
            filters: Optional additional filters
            limit: Maximum results to return

        Returns:
            MCPResponse with search results and relevance scores
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: int) -> MCPResponse:
        """
        Delete document and all related data.

        Args:
            document_id: Document to delete

        Returns:
            MCPResponse confirming deletion
        """
        pass

    # Document Structure Operations
    @abstractmethod
    async def index_document(
        self,
        document_id: int,
        strategy: str = "auto",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> MCPResponse:
        """
        Create searchable chunks from document content.

        Args:
            document_id: Document to index
            strategy: Chunking strategy ("auto", "chapter", "section", "fixed")
            progress_callback: Optional progress tracking

        Returns:
            MCPResponse with indexing results and chunk count
        """
        pass

    @abstractmethod
    async def get_document_structure(self, document_id: int) -> MCPResponse:
        """
        Get document outline/structure (list of chunks/chapters).

        Args:
            document_id: Document to get structure for

        Returns:
            MCPResponse with document structure information
        """
        pass

    @abstractmethod
    async def get_chunk_content(self, chunk_id: int) -> MCPResponse:
        """
        Retrieve full text content of specific chunk.

        Args:
            chunk_id: Chunk to retrieve

        Returns:
            MCPResponse with chunk text content
        """
        pass

    # Summary Management Operations
    @abstractmethod
    async def get_summary(
        self,
        chunk_id: Optional[int] = None,
        document_id: Optional[int] = None,
        summary_type: str = "standard",
    ) -> MCPResponse:
        """
        Retrieve existing summary for chunk or document.

        Args:
            chunk_id: Optional specific chunk to get summary for
            document_id: Optional document to get summary for
            summary_type: Type of summary ("brief", "standard", "detailed")

        Returns:
            MCPResponse with summary content
        """
        pass

    @abstractmethod
    async def save_summary(
        self,
        summary_content: str,
        summary_type: str = "standard",
        chunk_id: Optional[int] = None,
        document_id: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> MCPResponse:
        """
        Save AI-generated summary.

        Args:
            summary_content: The summary text in markdown format
            summary_type: Type of summary ("brief", "standard", "detailed")
            chunk_id: Optional chunk this summary applies to
            document_id: Optional document this summary applies to
            model_name: Optional name of AI model that generated summary

        Returns:
            MCPResponse confirming summary saved
        """
        pass

    @abstractmethod
    async def list_summaries(
        self, document_id: Optional[int] = None, chunk_id: Optional[int] = None
    ) -> MCPResponse:
        """
        List available summaries for document or chunk.

        Args:
            document_id: Optional document to list summaries for
            chunk_id: Optional chunk to list summaries for

        Returns:
            MCPResponse with list of available summaries
        """
        pass


class MCPClientError(Exception):
    """Base exception for MCP client errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        operation_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.operation_id = operation_id
        self.original_error = original_error


class ConnectionError(MCPClientError):
    """Exception for MCP server connection issues."""

    pass


class ValidationError(MCPClientError):
    """Exception for parameter validation failures."""

    pass


class TimeoutError(MCPClientError):
    """Exception for operation timeout."""

    pass


class ToolNotFoundError(MCPClientError):
    """Exception for unknown MCP tool."""

    pass


class ServerError(MCPClientError):
    """Exception for MCP server-side errors."""

    pass


class BaseProgressTracker(IProgressTracker):
    """
    Base implementation of progress tracking with logging integration.

    Provides standard progress tracking functionality that can be extended
    or used directly by concrete MCP client implementations.
    """

    def __init__(self):
        self._active_operations: Dict[str, OperationProgress] = {}
        self._callbacks: List[ProgressCallback] = []
        self._lock = threading.RLock()
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()

    def start_operation(
        self,
        operation_id: str,
        operation_name: str,
        estimated_duration_ms: Optional[float] = None,
    ) -> None:
        """Start tracking a new operation."""
        with self._lock:
            progress = OperationProgress(
                operation_id=operation_id,
                operation_name=operation_name,
                phase=ProgressPhase.VALIDATING,
                progress_percent=0.0,
                current_step="Starting operation",
                details={"estimated_duration_ms": estimated_duration_ms},
            )

            self._active_operations[operation_id] = progress
            self._notify_callbacks(progress)

            self._logger.debug(
                f"Started tracking operation: {operation_name}",
                operation_id=operation_id,
                estimated_duration_ms=estimated_duration_ms,
            )

    def update_progress(
        self,
        operation_id: str,
        phase: ProgressPhase,
        progress_percent: float,
        current_step: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update operation progress."""
        with self._lock:
            if operation_id not in self._active_operations:
                return

            progress = self._active_operations[operation_id]
            progress.phase = phase
            progress.progress_percent = max(0.0, min(100.0, progress_percent))
            progress.current_step = current_step

            if details:
                if progress.details is None:
                    progress.details = {}
                progress.details.update(details)

            self._notify_callbacks(progress)

    def complete_operation(self, operation_id: str, success: bool) -> None:
        """Mark operation as completed."""
        with self._lock:
            if operation_id not in self._active_operations:
                return

            progress = self._active_operations[operation_id]
            progress.phase = ProgressPhase.FINALIZING
            progress.progress_percent = 100.0
            progress.current_step = "Completed" if success else "Failed"

            self._notify_callbacks(progress)

            # Remove from active operations
            del self._active_operations[operation_id]

            self._logger.debug(
                f"Operation completed: {progress.operation_name}",
                operation_id=operation_id,
                success=success,
                elapsed_time_ms=progress.elapsed_time_ms,
            )

    def cancel_operation(self, operation_id: str) -> None:
        """Cancel a running operation."""
        with self._lock:
            if operation_id not in self._active_operations:
                return

            progress = self._active_operations[operation_id]
            progress.current_step = "Cancelled"

            self._notify_callbacks(progress)

            # Remove from active operations
            del self._active_operations[operation_id]

            self._logger.info(
                f"Operation cancelled: {progress.operation_name}",
                operation_id=operation_id,
            )

    def add_progress_callback(self, callback: ProgressCallback) -> None:
        """Add progress update callback."""
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_progress_callback(self, callback: ProgressCallback) -> None:
        """Remove progress update callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def get_active_operations(self) -> List[OperationProgress]:
        """Get list of currently active operations."""
        with self._lock:
            return list(self._active_operations.values())

    def _notify_callbacks(self, progress: OperationProgress) -> None:
        """Notify all registered callbacks of progress update."""
        for callback in self._callbacks:
            try:
                callback(progress)
            except Exception as e:
                self._logger.error(f"Progress callback failed: {e}")
                self._error_tracker.capture_error(
                    exception=e,
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.INTEGRATION,
                    user_action="Progress tracking",
                    operation_context={
                        "operation_id": progress.operation_id,
                        "operation_name": progress.operation_name,
                        "progress_percent": progress.progress_percent,
                    },
                )


# Factory function type for dependency injection
MCPClientFactory = Callable[..., IMCPClient]
