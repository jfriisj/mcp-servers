"""
Study Buddy GUI - Debug Logging System

Provides configurable debug logging with structured output, log rotation,
and runtime level changes for the GUI application.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Observer Pattern, Singleton Pattern  
SOLID: SRP (logging only), OCP (extensible formats), DIP (abstraction-based)
"""

import json
import logging
import logging.handlers
import sys
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union
from dataclasses import dataclass, asdict


class LogLevel(Enum):
    """Logging levels with numeric values."""

    DEBUG = logging.DEBUG  # 10 - Detailed diagnostic info
    INFO = logging.INFO  # 20 - General information
    WARNING = logging.WARNING  # 30 - Warning messages
    ERROR = logging.ERROR  # 40 - Error messages
    CRITICAL = logging.CRITICAL  # 50 - Critical failures

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """Create LogLevel from string."""
        level_map = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL,
        }
        return level_map.get(level_str.lower(), cls.INFO)


class LogFormat(Enum):
    """Available log output formats."""

    SIMPLE = "simple"  # Basic text format
    DETAILED = "detailed"  # Detailed text with context
    JSON = "json"  # Structured JSON format
    STRUCTURED = "structured"  # Key-value structured format


@dataclass
class LogEntry:
    """Structured log entry with comprehensive context."""

    # Basic information
    timestamp: datetime
    level: str
    logger_name: str
    message: str

    # Execution context
    module: str = ""
    function: str = ""
    line_number: int = 0
    thread_id: int = 0
    thread_name: str = ""
    process_id: int = 0

    # Application context
    widget_id: Optional[str] = None
    user_action: Optional[str] = None
    operation_id: Optional[str] = None
    session_id: Optional[str] = None

    # Error context (if applicable)
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    stack_trace: Optional[str] = None

    # Performance context
    execution_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    # Additional metadata
    extra: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class ILogFormatter(ABC):
    """
    Interface for log formatters.

    Allows different output formats for log entries.
    """

    @abstractmethod
    def format(self, entry: LogEntry) -> str:
        """Format log entry to string."""
        pass


class SimpleFormatter(ILogFormatter):
    """Simple text formatter for basic logging."""

    def format(self, entry: LogEntry) -> str:
        """Format as simple text line."""
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} [{entry.level:8}] {entry.logger_name}: {entry.message}"


class DetailedFormatter(ILogFormatter):
    """Detailed text formatter with context information."""

    def format(self, entry: LogEntry) -> str:
        """Format with detailed context."""
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Base message
        msg = f"{timestamp} [{entry.level:8}] {entry.logger_name}: {entry.message}"

        # Add context
        context_parts = []
        if entry.module:
            context_parts.append(f"module={entry.module}")
        if entry.function:
            context_parts.append(f"function={entry.function}")
        if entry.line_number:
            context_parts.append(f"line={entry.line_number}")
        if entry.widget_id:
            context_parts.append(f"widget={entry.widget_id}")
        if entry.thread_name:
            context_parts.append(f"thread={entry.thread_name}")

        if context_parts:
            msg += f" [{', '.join(context_parts)}]"

        # Add performance info
        perf_parts = []
        if entry.execution_time_ms is not None:
            perf_parts.append(f"exec_time={entry.execution_time_ms:.2f}ms")
        if entry.memory_usage_mb is not None:
            perf_parts.append(f"memory={entry.memory_usage_mb:.1f}MB")

        if perf_parts:
            msg += f" <{', '.join(perf_parts)}>"

        # Add exception info
        if entry.exception_type:
            msg += f"\nException: {entry.exception_type}: {entry.exception_message}"
            if entry.stack_trace:
                msg += f"\nStack trace:\n{entry.stack_trace}"

        return msg


class JSONFormatter(ILogFormatter):
    """JSON formatter for structured logging."""

    def format(self, entry: LogEntry) -> str:
        """Format as JSON for structured processing."""
        return json.dumps(entry.to_dict(), ensure_ascii=False)


class StructuredFormatter(ILogFormatter):
    """Key-value structured formatter."""

    def format(self, entry: LogEntry) -> str:
        """Format as key=value pairs."""
        data = entry.to_dict()

        # Format key-value pairs
        pairs = []
        for key, value in data.items():
            if value is not None and value != "":
                if isinstance(value, str) and " " in value:
                    pairs.append(f'{key}="{value}"')
                else:
                    pairs.append(f"{key}={value}")

        return " ".join(pairs)


class LogHandler:
    """
    Custom log handler that creates structured log entries.

    Captures comprehensive context and formats according to strategy.
    """

    def __init__(
        self,
        formatter: ILogFormatter,
        output: Union[TextIO, Path, str],
        max_size_mb: int = 50,
        backup_count: int = 5,
    ):
        """
        Initialize log handler.

        Args:
            formatter: Log formatter strategy
            output: Output destination (file path or stream)
            max_size_mb: Maximum log file size in MB before rotation
            backup_count: Number of backup files to keep
        """
        self.formatter = formatter
        self._lock = threading.Lock()
        self._session_id = str(int(time.time()))

        # Set up output handler
        if isinstance(output, (str, Path)):
            # File output with rotation
            log_path = Path(output)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            self._file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            self._output = None
        else:
            # Stream output
            self._file_handler = None
            self._output = output

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record as structured entry."""
        try:
            # Create structured log entry
            entry = self._create_log_entry(record)

            # Format entry
            formatted_message = self.formatter.format(entry)

            # Output message
            with self._lock:
                if self._file_handler:
                    # Use file handler
                    record.msg = formatted_message
                    record.args = ()  # Already formatted
                    self._file_handler.emit(record)
                elif self._output:
                    # Write to stream
                    self._output.write(formatted_message + "\n")
                    self._output.flush()

        except Exception:
            # Don't fail application if logging fails
            pass

    def _create_log_entry(self, record: logging.LogRecord) -> LogEntry:
        """Create structured log entry from record."""
        # Basic information
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created, timezone.utc),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            # Execution context
            module=record.module if hasattr(record, "module") else "",
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread or 0,
            thread_name=record.threadName or "",
            process_id=record.process or 0,
            session_id=self._session_id,
        )

        # Extract additional context from record
        if hasattr(record, "widget_id"):
            entry.widget_id = getattr(record, "widget_id")
        if hasattr(record, "user_action"):
            entry.user_action = getattr(record, "user_action")
        if hasattr(record, "operation_id"):
            entry.operation_id = getattr(record, "operation_id")
        if hasattr(record, "execution_time_ms"):
            entry.execution_time_ms = getattr(record, "execution_time_ms")
        if hasattr(record, "memory_usage_mb"):
            entry.memory_usage_mb = getattr(record, "memory_usage_mb")

        # Exception information
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            entry.exception_type = exc_type.__name__ if exc_type else None
            entry.exception_message = str(exc_value) if exc_value else None
            if exc_traceback:
                import traceback

                entry.stack_trace = "".join(traceback.format_tb(exc_traceback))

        # Extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "exc_info",
                "exc_text",
                "stack_info",
                "getMessage",
            }:
                extra_fields[key] = value

        if extra_fields:
            entry.extra = extra_fields

        return entry

    def close(self) -> None:
        """Close handler resources."""
        if self._file_handler:
            self._file_handler.close()


class DebugLogger:
    """
    Comprehensive debug logging system.

    Responsibilities:
    - Manage structured logging with configurable levels
    - Support multiple output formats and destinations
    - Provide performance and context tracking
    - Enable runtime configuration changes
    - Maintain session and operation correlation
    """

    def __init__(
        self,
        name: str = "study_buddy_gui",
        level: LogLevel = LogLevel.INFO,
        log_format: LogFormat = LogFormat.DETAILED,
        log_dir: Optional[Path] = None,
        console_output: bool = True,
    ):
        """
        Initialize debug logger.

        Args:
            name: Logger name
            level: Initial logging level
            log_format: Log output format
            log_dir: Directory for log files (None = no file logging)
            console_output: Whether to output to console
        """
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level.value)

        # Clear existing handlers
        self._logger.handlers.clear()

        # Create formatters
        self._formatters = {
            LogFormat.SIMPLE: SimpleFormatter(),
            LogFormat.DETAILED: DetailedFormatter(),
            LogFormat.JSON: JSONFormatter(),
            LogFormat.STRUCTURED: StructuredFormatter(),
        }

        # Set up handlers
        self._handlers: List[LogHandler] = []
        self._setup_handlers(log_format, log_dir, console_output)

        # Configuration
        self._current_level = level
        self._current_format = log_format

        # Context tracking
        self._default_context: Dict[str, Any] = {}

    def _setup_handlers(
        self, log_format: LogFormat, log_dir: Optional[Path], console_output: bool
    ) -> None:
        """Set up log handlers."""
        formatter = self._formatters[log_format]

        # Console handler
        if console_output:
            console_handler = LogHandler(formatter, sys.stdout)
            self._handlers.append(console_handler)

            # Create Python logging handler adapter
            class HandlerAdapter(logging.Handler):
                def __init__(self, log_handler):
                    super().__init__()
                    self.log_handler = log_handler

                def emit(self, record):
                    self.log_handler.emit(record)

            self._logger.addHandler(HandlerAdapter(console_handler))

        # File handler
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Main log file
            main_log = log_dir / f"{self.name}.log"
            file_handler = LogHandler(formatter, main_log)
            self._handlers.append(file_handler)

            class FileHandlerAdapter(logging.Handler):
                def __init__(self, log_handler):
                    super().__init__()
                    self.log_handler = log_handler

                def emit(self, record):
                    self.log_handler.emit(record)

            self._logger.addHandler(FileHandlerAdapter(file_handler))

            # Error log file (errors only)
            if log_format != LogFormat.JSON:  # JSON format goes to main log only
                error_formatter = self._formatters[LogFormat.DETAILED]
            else:
                error_formatter = formatter

            error_log = log_dir / f"{self.name}_errors.log"
            error_handler = LogHandler(error_formatter, error_log)

            class ErrorHandlerAdapter(logging.Handler):
                def __init__(self, log_handler):
                    super().__init__()
                    self.log_handler = log_handler
                    self.setLevel(logging.ERROR)

                def emit(self, record):
                    self.log_handler.emit(record)

            self._logger.addHandler(ErrorHandlerAdapter(error_handler))

    def set_level(self, level: LogLevel) -> None:
        """Change logging level at runtime."""
        self._logger.setLevel(level.value)
        self._current_level = level

    def set_format(self, log_format: LogFormat) -> None:
        """Change log format at runtime."""
        # Update formatter for all handlers
        formatter = self._formatters[log_format]
        for handler in self._handlers:
            handler.formatter = formatter

        self._current_format = log_format

    def set_context(self, **context) -> None:
        """Set default context for all log messages."""
        self._default_context.update(context)

    def clear_context(self) -> None:
        """Clear default context."""
        self._default_context.clear()

    def debug(self, message: str, **context) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **context)

    def error(self, message: str, **context) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, **context)

    def critical(self, message: str, **context) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **context)

    def exception(self, message: str, **context) -> None:
        """Log exception with stack trace."""
        self._log(LogLevel.ERROR, message, exc_info=True, **context)

    def log_performance(
        self,
        operation: str,
        execution_time_ms: float,
        memory_usage_mb: Optional[float] = None,
        **context,
    ) -> None:
        """Log performance information."""
        self._log(
            LogLevel.INFO,
            f"Performance: {operation}",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            **context,
        )

    def log_user_action(self, action: str, widget_id: str, **context) -> None:
        """Log user action for audit trail."""
        self._log(
            LogLevel.INFO,
            f"User action: {action}",
            user_action=action,
            widget_id=widget_id,
            **context,
        )

    def log_mcp_operation(
        self, operation: str, success: bool, execution_time_ms: float, **context
    ) -> None:
        """Log MCP operation."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "success" if success else "failed"

        self._log(
            level,
            f"MCP operation {status}: {operation}",
            mcp_operation=operation,
            mcp_success=success,
            execution_time_ms=execution_time_ms,
            **context,
        )

    def _log(self, level: LogLevel, message: str, **context) -> None:
        """Internal logging method."""
        # Merge default context with message context
        full_context = {**self._default_context, **context}

        # Log with context as extra fields
        self._logger.log(level.value, message, extra=full_context)

    def close(self) -> None:
        """Close logger and cleanup resources."""
        for handler in self._handlers:
            handler.close()

        # Remove handlers from Python logger
        self._logger.handlers.clear()


# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None
_logger_lock = threading.Lock()


def get_debug_logger() -> DebugLogger:
    """
    Get global debug logger instance (singleton pattern).

    Returns:
        DebugLogger instance
    """
    global _debug_logger

    if _debug_logger is None:
        with _logger_lock:
            if _debug_logger is None:
                # Default configuration
                log_dir = Path.home() / ".study_buddy" / "logs"
                _debug_logger = DebugLogger(
                    name="study_buddy_gui",
                    level=LogLevel.INFO,
                    log_format=LogFormat.DETAILED,
                    log_dir=log_dir,
                    console_output=True,
                )

    return _debug_logger


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    log_format: LogFormat = LogFormat.DETAILED,
    log_dir: Optional[Path] = None,
    console_output: bool = True,
) -> DebugLogger:
    """
    Configure global debug logger.

    Args:
        level: Logging level
        log_format: Log output format
        log_dir: Directory for log files
        console_output: Whether to output to console

    Returns:
        Configured DebugLogger instance
    """
    global _debug_logger

    with _logger_lock:
        # Close existing logger
        if _debug_logger:
            _debug_logger.close()

        # Create new logger
        if log_dir is None:
            log_dir = Path.home() / ".study_buddy" / "logs"

        _debug_logger = DebugLogger(
            name="study_buddy_gui",
            level=level,
            log_format=log_format,
            log_dir=log_dir,
            console_output=console_output,
        )

    return _debug_logger


# Convenience functions
def debug(message: str, **context) -> None:
    """Log debug message."""
    logger = get_debug_logger()
    logger.debug(message, **context)


def info(message: str, **context) -> None:
    """Log info message."""
    logger = get_debug_logger()
    logger.info(message, **context)


def warning(message: str, **context) -> None:
    """Log warning message."""
    logger = get_debug_logger()
    logger.warning(message, **context)


def error(message: str, **context) -> None:
    """Log error message."""
    logger = get_debug_logger()
    logger.error(message, **context)


def critical(message: str, **context) -> None:
    """Log critical message."""
    logger = get_debug_logger()
    logger.critical(message, **context)


def exception(message: str, **context) -> None:
    """Log exception with stack trace."""
    logger = get_debug_logger()
    logger.exception(message, **context)


# Context managers for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing."""

    def __init__(
        self, operation_name: str, logger: Optional[DebugLogger] = None, **context
    ):
        self.operation_name = operation_name
        self.logger = logger or get_debug_logger()
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(
            f"Starting operation: {self.operation_name}",
            operation=self.operation_name,
            **self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            execution_time = (time.time() - self.start_time) * 1000
        else:
            execution_time = 0.0

        if exc_type is None:
            self.logger.log_performance(
                operation=self.operation_name,
                execution_time_ms=execution_time,
                **self.context,
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                operation=self.operation_name,
                execution_time_ms=execution_time,
                exception_type=exc_type.__name__,
                exception_message=str(exc_val),
                **self.context,
            )


def logged_operation(operation_name: str, **context):
    """Create logged operation context manager."""
    return LoggedOperation(operation_name, **context)
