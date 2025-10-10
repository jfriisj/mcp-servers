"""
Study Buddy GUI - Error Tracking System

Provides comprehensive error context capture, categorization, correlation,
and root cause analysis for the GUI application.

Architecture: Clean Architecture Layer 4 (Infrastructure) 
Patterns: Observer Pattern, Strategy Pattern, Singleton Pattern
SOLID: SRP (error tracking only), OCP (extensible categories), DIP (abstraction-based)
"""

import sys
import threading
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
import psutil

from gui.performance.memory_monitor import get_memory_monitor


class ErrorSeverity(Enum):
    """Error severity levels for categorization and prioritization."""

    CRITICAL = "critical"  # System failures, crashes, data corruption
    HIGH = "high"  # Feature failures, MCP server errors
    MEDIUM = "medium"  # Recoverable errors, validation failures
    LOW = "low"  # Minor issues, warnings
    INFO = "info"  # Informational messages, user actions


class ErrorCategory(Enum):
    """Error categories for organization and handling strategies."""

    USER_INPUT = "user_input"  # Invalid user inputs, validation errors
    NETWORK = "network"  # MCP server communication failures
    PERFORMANCE = "performance"  # Slow operations, memory issues
    UI = "ui"  # Widget rendering, layout issues
    DATA = "data"  # File access, parsing errors
    SYSTEM = "system"  # OS-level errors, permissions
    CONFIGURATION = "configuration"  # Settings, theme, config errors
    INTEGRATION = "integration"  # MCP protocol, external service errors
    SECURITY = "security"  # Security violations, injection attacks, permission errors


@dataclass
class ErrorContext:
    """
    Comprehensive error context information.

    Captures all relevant information for error analysis and debugging.
    """

    # Error Identity
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Error Classification
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM
    error_type: str = ""  # Exception class name
    error_message: str = ""

    # Execution Context
    function_name: str = ""
    class_name: str = ""
    module_name: str = ""
    file_path: str = ""
    line_number: int = 0

    # Application Context
    widget_id: Optional[str] = None
    widget_class: Optional[str] = None
    user_action: Optional[str] = None  # What user was doing
    operation_context: Dict[str, Any] = field(default_factory=dict)

    # System Context
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_threads: int = 0
    mcp_connection_status: Optional[str] = None

    # Error Details
    stack_trace: str = ""
    inner_exception: Optional[str] = None
    correlation_id: Optional[str] = None  # Link related errors

    # Recovery Information
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[str] = None

    # Additional Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data["severity"] = self.severity.value
        data["category"] = self.category.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorContext":
        """Create from dictionary."""
        # Convert string enums back
        data["severity"] = ErrorSeverity(data["severity"])
        data["category"] = ErrorCategory(data["category"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata entry."""
        self.metadata[key] = value

    def set_recovery_info(
        self, attempted: bool, successful: bool = False, strategy: str = ""
    ) -> None:
        """Set recovery attempt information."""
        self.recovery_attempted = attempted
        self.recovery_successful = successful
        if strategy:
            self.recovery_strategy = strategy


class IErrorObserver(ABC):
    """
    Interface for error observers.

    Allows different components to react to error events.
    """

    @abstractmethod
    def on_error_captured(self, context: ErrorContext) -> None:
        """Called when an error is captured."""
        pass

    @abstractmethod
    def on_error_resolved(self, context: ErrorContext) -> None:
        """Called when an error is resolved."""
        pass


class ErrorCorrelator:
    """
    Correlates related errors for root cause analysis.

    Groups errors that likely have the same underlying cause.
    """

    def __init__(self):
        self._error_groups: Dict[str, List[str]] = {}
        self._correlation_window = 300  # 5 minutes

    def correlate_error(self, context: ErrorContext) -> Optional[str]:
        """
        Find correlation group for error or create new one.

        Args:
            context: Error context to correlate

        Returns:
            Correlation ID if error is part of a group
        """
        # Simple correlation based on error type and location
        correlation_key = (
            f"{context.error_type}:{context.function_name}:{context.class_name}"
        )

        # Find recent errors with same key
        current_time = time.time()
        for group_id, error_ids in list(self._error_groups.items()):
            # Remove old groups (outside correlation window)
            if current_time - float(group_id.split("_")[0]) > self._correlation_window:
                del self._error_groups[group_id]
                continue

            # Check if this error belongs to existing group
            if correlation_key in group_id:
                error_ids.append(context.error_id)
                context.correlation_id = group_id
                return group_id

        # Create new correlation group
        group_id = f"{int(current_time)}_{correlation_key}"
        self._error_groups[group_id] = [context.error_id]
        context.correlation_id = group_id
        return group_id

    def get_correlated_errors(self, correlation_id: str) -> List[str]:
        """Get all error IDs in correlation group."""
        return self._error_groups.get(correlation_id, [])


class ErrorTracker:
    """
    Central error tracking and context capture system.

    Responsibilities:
    - Capture comprehensive error context
    - Categorize and prioritize errors
    - Notify observers of error events
    - Correlate related errors
    - Maintain error history
    """

    def __init__(self):
        self._errors: Dict[str, ErrorContext] = {}
        self._observers: List[IErrorObserver] = []
        self._correlator = ErrorCorrelator()
        self._lock = threading.RLock()
        self._max_errors = 10000  # Memory limit

        # System monitoring
        self._memory_monitor = None
        self._process = psutil.Process()

    def add_observer(self, observer: IErrorObserver) -> None:
        """Add error observer."""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def remove_observer(self, observer: IErrorObserver) -> None:
        """Remove error observer."""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def capture_error(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        widget_id: Optional[str] = None,
        user_action: Optional[str] = None,
        operation_context: Optional[Dict[str, Any]] = None,
        **metadata,
    ) -> ErrorContext:
        """
        Capture comprehensive error context.

        Args:
            exception: The exception that occurred
            severity: Error severity level
            category: Error category
            widget_id: ID of widget where error occurred
            user_action: What user was doing when error occurred
            operation_context: Additional operation context
            **metadata: Additional metadata

        Returns:
            ErrorContext with captured information
        """
        with self._lock:
            # Create error context
            context = ErrorContext(
                severity=severity,
                category=category,
                error_type=type(exception).__name__,
                error_message=str(exception),
                widget_id=widget_id,
                user_action=user_action,
                operation_context=operation_context or {},
            )

            # Capture execution context
            self._capture_execution_context(context, exception)

            # Capture system context
            self._capture_system_context(context)

            # Add metadata
            for key, value in metadata.items():
                context.add_metadata(key, value)

            # Correlate with other errors
            self._correlator.correlate_error(context)

            # Store error
            self._store_error(context)

            # Notify observers
            self._notify_observers_error_captured(context)

            return context

    def capture_from_current_exception(
        self,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        widget_id: Optional[str] = None,
        user_action: Optional[str] = None,
        operation_context: Optional[Dict[str, Any]] = None,
        **metadata,
    ) -> Optional[ErrorContext]:
        """
        Capture error from current exception context.

        Convenience method for use in except blocks.
        """
        exc_info = sys.exc_info()
        if exc_info[1] is None:
            return None

        return self.capture_error(
            exception=exc_info[1],
            severity=severity,
            category=category,
            widget_id=widget_id,
            user_action=user_action,
            operation_context=operation_context,
            **metadata,
        )

    def mark_error_resolved(
        self,
        error_id: str,
        recovery_strategy: str = "",
        resolution_details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an error as resolved.

        Args:
            error_id: ID of resolved error
            recovery_strategy: How the error was resolved
            resolution_details: Additional resolution information

        Returns:
            True if error was found and marked resolved
        """
        with self._lock:
            if error_id not in self._errors:
                return False

            context = self._errors[error_id]
            context.set_recovery_info(
                attempted=True, successful=True, strategy=recovery_strategy
            )

            if resolution_details:
                context.metadata.update(resolution_details)

            # Notify observers
            self._notify_observers_error_resolved(context)

            return True

    def get_error(self, error_id: str) -> Optional[ErrorContext]:
        """Get error by ID."""
        with self._lock:
            return self._errors.get(error_id)

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorContext]:
        """Get all errors in category."""
        with self._lock:
            return [ctx for ctx in self._errors.values() if ctx.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorContext]:
        """Get all errors with severity."""
        with self._lock:
            return [ctx for ctx in self._errors.values() if ctx.severity == severity]

    def get_correlated_errors(self, error_id: str) -> List[ErrorContext]:
        """Get all errors correlated with given error."""
        with self._lock:
            context = self._errors.get(error_id)
            if not context or not context.correlation_id:
                return []

            correlated_ids = self._correlator.get_correlated_errors(
                context.correlation_id
            )
            return [self._errors[eid] for eid in correlated_ids if eid in self._errors]

    def get_recent_errors(self, hours: int = 24) -> List[ErrorContext]:
        """Get errors from last N hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        with self._lock:
            return [
                ctx
                for ctx in self._errors.values()
                if ctx.timestamp.timestamp() >= cutoff
            ]

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics summary."""
        with self._lock:
            total_errors = len(self._errors)

            # Count by severity
            severity_counts = {}
            for severity in ErrorSeverity:
                severity_counts[severity.value] = len(
                    self.get_errors_by_severity(severity)
                )

            # Count by category
            category_counts = {}
            for category in ErrorCategory:
                category_counts[category.value] = len(
                    self.get_errors_by_category(category)
                )

            # Recent error rate
            recent_errors = self.get_recent_errors(1)  # Last hour

            return {
                "total_errors": total_errors,
                "recent_errors_1h": len(recent_errors),
                "severity_breakdown": severity_counts,
                "category_breakdown": category_counts,
                "correlation_groups": len(self._correlator._error_groups),
            }

    def clear_old_errors(self, max_age_days: int = 7) -> int:
        """Clear errors older than specified days."""
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 24 * 3600)

        with self._lock:
            old_error_ids = [
                error_id
                for error_id, ctx in self._errors.items()
                if ctx.timestamp.timestamp() < cutoff
            ]

            for error_id in old_error_ids:
                del self._errors[error_id]

            return len(old_error_ids)

    def _capture_execution_context(
        self, context: ErrorContext, exception: Exception
    ) -> None:
        """Capture execution context from exception."""
        # Get stack trace
        context.stack_trace = traceback.format_exc()

        # Get frame information
        tb = exception.__traceback__
        if tb:
            frame = tb.tb_frame
            context.function_name = frame.f_code.co_name
            context.file_path = frame.f_code.co_filename
            context.line_number = tb.tb_lineno
            context.module_name = frame.f_globals.get("__name__", "")

            # Try to get class name if method
            if "self" in frame.f_locals:
                self_obj = frame.f_locals["self"]
                context.class_name = type(self_obj).__name__
                context.widget_class = context.class_name

        # Handle chained exceptions
        if exception.__cause__:
            context.inner_exception = str(exception.__cause__)

    def _capture_system_context(self, context: ErrorContext) -> None:
        """Capture system performance context."""
        try:
            # Memory usage
            memory_info = self._process.memory_info()
            context.memory_usage_mb = memory_info.rss / 1024 / 1024

            # CPU usage
            context.cpu_usage_percent = self._process.cpu_percent()

            # Thread count
            context.active_threads = threading.active_count()

            # Memory monitor integration
            if self._memory_monitor is None:
                try:
                    self._memory_monitor = get_memory_monitor()
                except Exception:
                    pass  # Memory monitor might not be available

            if self._memory_monitor:
                memory_status = self._memory_monitor.get_memory_status()
                context.add_metadata("memory_status", memory_status)

        except Exception:
            # Don't fail error capture if system monitoring fails
            pass

    def _store_error(self, context: ErrorContext) -> None:
        """Store error with memory management."""
        self._errors[context.error_id] = context

        # Maintain memory limit
        if len(self._errors) > self._max_errors:
            # Remove oldest errors
            oldest_errors = sorted(self._errors.items(), key=lambda x: x[1].timestamp)[
                : len(self._errors) - self._max_errors + 1
            ]

            for error_id, _ in oldest_errors:
                del self._errors[error_id]

    def _notify_observers_error_captured(self, context: ErrorContext) -> None:
        """Notify observers of error capture."""
        for observer in self._observers:
            try:
                observer.on_error_captured(context)
            except Exception:
                # Don't fail error tracking if observer fails
                pass

    def _notify_observers_error_resolved(self, context: ErrorContext) -> None:
        """Notify observers of error resolution."""
        for observer in self._observers:
            try:
                observer.on_error_resolved(context)
            except Exception:
                # Don't fail error tracking if observer fails
                pass


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None
_error_tracker_lock = threading.Lock()


def get_error_tracker() -> ErrorTracker:
    """
    Get global error tracker instance (singleton pattern).

    Returns:
        ErrorTracker instance
    """
    global _error_tracker

    if _error_tracker is None:
        with _error_tracker_lock:
            if _error_tracker is None:
                _error_tracker = ErrorTracker()

    return _error_tracker


# Convenience functions for common error capture patterns
def capture_exception(
    exception: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    widget_id: Optional[str] = None,
    user_action: Optional[str] = None,
    **metadata,
) -> ErrorContext:
    """Capture exception with error tracker."""
    tracker = get_error_tracker()
    return tracker.capture_error(
        exception=exception,
        severity=severity,
        category=category,
        widget_id=widget_id,
        user_action=user_action,
        **metadata,
    )


def capture_current_exception(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    widget_id: Optional[str] = None,
    user_action: Optional[str] = None,
    **metadata,
) -> Optional[ErrorContext]:
    """Capture current exception context."""
    tracker = get_error_tracker()
    return tracker.capture_from_current_exception(
        severity=severity,
        category=category,
        widget_id=widget_id,
        user_action=user_action,
        **metadata,
    )


# Decorator for automatic error capture
def track_errors(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    widget_id: Optional[str] = None,
):
    """
    Decorator to automatically track errors in functions.

    Args:
        severity: Default severity for captured errors
        category: Default category for captured errors
        widget_id: Widget ID context
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture error context
                capture_exception(
                    exception=e,
                    severity=severity,
                    category=category,
                    widget_id=widget_id,
                    function_name=func.__name__,
                    function_args=str(args),
                    function_kwargs=str(kwargs),
                )
                # Re-raise the exception
                raise

        return wrapper

    return decorator
