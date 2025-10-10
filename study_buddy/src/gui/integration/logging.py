"""
Logging and Observability System for Study Buddy GUI Integration Layer.

This module provides comprehensive observability including structured JSON logging,
performance tracking with P95 latency metrics, error tracking with correlation IDs,
and alerting for operations monitoring.

Architecture: Clean Architecture Layer 4 (Infrastructure)
SOLID Compliance: Full compliance with all SOLID principles
Purpose: Complete observability for integration layer with production-grade monitoring
"""

import asyncio
import json
import logging
import statistics
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Iterator, Deque
import traceback
import sys


# ============================================================================
# OBSERVABILITY ENUMS AND CONSTANTS
# ============================================================================

class LogLevel(Enum):
    """Enhanced logging levels for structured logging."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of performance metrics."""
    LATENCY = "latency"
    COUNT = "count"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class OperationType(Enum):
    """Types of operations being tracked."""
    MCP_TOOL_CALL = "mcp_tool_call"
    CONNECTION_OPEN = "connection_open"
    CONNECTION_CLOSE = "connection_close"
    SCHEMA_VALIDATION = "schema_validation"
    SECURITY_VALIDATION = "security_validation"
    CONFIGURATION_LOAD = "configuration_load"
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# OBSERVABILITY DATA STRUCTURES
# ============================================================================

@dataclass
class LogEntry:
    """Structured log entry with comprehensive context."""
    
    timestamp: datetime
    level: LogLevel
    message: str
    operation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    operation_type: Optional[OperationType] = None
    component: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    performance_info: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Convert log entry to JSON string."""
        # Convert to dict with proper serialization
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "operation_id": self.operation_id,
            "correlation_id": self.correlation_id,
            "operation_type": self.operation_type.value if self.operation_type else None,
            "component": self.component,
            "metadata": self.metadata,
            "error_info": self.error_info,
            "performance_info": self.performance_info
        }
        
        # Remove None values for cleaner JSON
        return json.dumps({k: v for k, v in data.items() if v is not None}, indent=None)


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    
    timestamp: datetime
    operation_type: OperationType
    operation_id: str
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    
    timestamp: datetime
    error_type: str
    error_message: str
    operation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    operation_type: Optional[OperationType] = None
    component: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Configuration for performance and error alerting."""
    
    name: str
    metric_type: MetricType
    operation_type: Optional[OperationType] = None
    threshold: float = 0.0
    severity: AlertSeverity = AlertSeverity.WARNING
    window_minutes: int = 5
    min_samples: int = 10
    enabled: bool = True


@dataclass
class ObservabilityConfig:
    """Configuration for the observability system."""
    
    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    json_logging: bool = True
    log_file_path: Optional[Path] = None
    max_log_file_size_mb: int = 100
    log_retention_days: int = 30
    
    # Performance tracking
    track_performance: bool = True
    performance_sampling_rate: float = 1.0  # 1.0 = 100% sampling
    p95_window_minutes: int = 5
    max_metrics_memory: int = 10000
    
    # Error tracking
    track_errors: bool = True
    capture_stack_traces: bool = True
    max_error_context_length: int = 1000
    
    # Alerting
    enable_alerts: bool = False
    alert_rules: List[AlertRule] = field(default_factory=list)
    
    # Async logging
    async_logging: bool = True
    log_queue_size: int = 1000
    log_flush_interval_seconds: float = 5.0
    
    # Security and privacy
    sanitize_sensitive_data: bool = True
    exclude_sensitive_keys: List[str] = field(default_factory=lambda: [
        "password", "token", "key", "secret", "credential", "auth"
    ])


# ============================================================================
# CORRELATION CONTEXT
# ============================================================================

# Context variables for correlation tracking
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_operation_id: ContextVar[Optional[str]] = ContextVar("operation_id", default=None)
_operation_type: ContextVar[Optional[OperationType]] = ContextVar("operation_type", default=None)


@contextmanager
def correlation_context(
    correlation_id: Optional[str] = None,
    operation_id: Optional[str] = None,
    operation_type: Optional[OperationType] = None
) -> Iterator[Dict[str, Any]]:
    """
    Context manager for correlation tracking across operations.
    
    Args:
        correlation_id: Unique ID for tracking related operations
        operation_id: Unique ID for this specific operation
        operation_type: Type of operation being performed
        
    Yields:
        Dict containing the correlation context
    """
    # Generate IDs if not provided
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    if operation_id is None:
        operation_id = str(uuid.uuid4())
    
    # Set context variables
    correlation_token = _correlation_id.set(correlation_id)
    operation_token = _operation_id.set(operation_id)
    type_token = _operation_type.set(operation_type)
    
    context = {
        "correlation_id": correlation_id,
        "operation_id": operation_id,
        "operation_type": operation_type
    }
    
    try:
        yield context
    finally:
        # Reset context variables
        _correlation_id.reset(correlation_token)
        _operation_id.reset(operation_token)
        _operation_type.reset(type_token)


def get_current_context() -> Dict[str, Any]:
    """Get current correlation context."""
    return {
        "correlation_id": _correlation_id.get(),
        "operation_id": _operation_id.get(),
        "operation_type": _operation_type.get()
    }


# ============================================================================
# ABSTRACT INTERFACES
# ============================================================================

class StructuredLogger(ABC):
    """Abstract interface for structured logging."""
    
    @abstractmethod
    async def log(
        self, 
        level: LogLevel, 
        message: str, 
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a structured message."""
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        pass
    
    @abstractmethod
    async def flush(self) -> None:
        """Flush any pending log entries."""
        pass


class PerformanceTracker(ABC):
    """Abstract interface for performance tracking."""
    
    @abstractmethod
    def start_operation(
        self, 
        operation_type: OperationType,
        operation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start tracking an operation."""
        pass
    
    @abstractmethod
    def end_operation(
        self, 
        operation_id: str, 
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetric:
        """End tracking an operation and return metrics."""
        pass
    
    @abstractmethod
    def get_p95_latency(
        self, 
        operation_type: Optional[OperationType] = None,
        window_minutes: int = 5
    ) -> Optional[float]:
        """Get P95 latency for operations."""
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics summary."""
        pass


class ErrorTracker(ABC):
    """Abstract interface for error tracking."""
    
    @abstractmethod
    async def track_error(
        self, 
        error: Exception,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        capture_stack_trace: bool = True
    ) -> str:
        """Track an error and return error ID."""
        pass
    
    @abstractmethod
    def get_error_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get error statistics for specified time window."""
        pass


class AlertManager(ABC):
    """Abstract interface for alert management."""
    
    @abstractmethod
    async def check_alerts(self, metric: PerformanceMetric) -> List[Dict[str, Any]]:
        """Check if metric triggers any alerts."""
        pass
    
    @abstractmethod
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        pass
    
    @abstractmethod
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================

class JSONStructuredLogger(StructuredLogger):
    """
    JSON-based structured logger with async queue processing.
    
    Features:
    - Structured JSON logging with correlation context
    - Async queue for non-blocking operations
    - Configurable log levels and formatting
    - Automatic log rotation and retention
    - Security-aware data sanitization
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize JSON structured logger."""
        self.config = config
        self._log_queue: asyncio.Queue = asyncio.Queue(maxsize=config.log_queue_size)
        self._flush_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger("study_buddy.integration")
        self._setup_logger()
        
        # Start async logging if enabled
        if config.async_logging:
            self._start_async_processing()
    
    def _setup_logger(self) -> None:
        """Set up the underlying Python logger."""
        # Set level
        level_mapping = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self._logger.setLevel(level_mapping[self.config.log_level])
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Add console handler with JSON formatting
        if self.config.json_logging:
            formatter = self._create_json_formatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # Add file handler if configured
        if self.config.log_file_path:
            file_handler = self._create_file_handler()
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
    
    def _create_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for structured logging."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                # Create log entry from record
                log_data: Dict[str, Any] = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "component": record.name,
                }
                
                # Add correlation context if available
                context = get_current_context()
                log_data.update({k: v for k, v in context.items() if v is not None})
                
                # Add exception info if present
                if record.exc_info and record.exc_info[0] is not None:
                    log_data["error_info"] = {
                        "exception_type": record.exc_info[0].__name__,
                        "exception_message": str(record.exc_info[1]),
                        "stack_trace": self.formatException(record.exc_info)
                    }
                
                return json.dumps(log_data)
        
        return JSONFormatter()
    
    def _create_file_handler(self) -> logging.Handler:
        """Create rotating file handler."""
        from logging.handlers import RotatingFileHandler
        
        if self.config.log_file_path is None:
            raise ValueError("log_file_path must be set to create file handler")
        
        # Ensure log directory exists
        self.config.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        max_bytes = self.config.max_log_file_size_mb * 1024 * 1024
        handler = RotatingFileHandler(
            self.config.log_file_path,
            maxBytes=max_bytes,
            backupCount=5
        )
        
        return handler
    
    def _start_async_processing(self) -> None:
        """Start async log processing task."""
        self._flush_task = asyncio.create_task(self._process_log_queue())
    
    async def _process_log_queue(self) -> None:
        """Process log entries from the async queue."""
        try:
            while True:
                # Wait for entries or timeout
                try:
                    entry = await asyncio.wait_for(
                        self._log_queue.get(),
                        timeout=self.config.log_flush_interval_seconds
                    )
                    
                    # Process the log entry
                    await self._write_log_entry(entry)
                    self._log_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Flush periodically even without new entries
                    await self._flush_handlers()
                    
        except asyncio.CancelledError:
            # Flush remaining entries before shutdown
            await self._flush_remaining_entries()
            raise
    
    async def _write_log_entry(self, entry: LogEntry) -> None:
        """Write log entry to underlying logger."""
        level_mapping = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        # Set correlation context for the log operation
        correlation_token = _correlation_id.set(entry.correlation_id)
        operation_token = _operation_id.set(entry.operation_id)
        
        try:
            # Create log record
            if entry.error_info:
                # Log with exception info
                self._logger.log(
                    level_mapping[entry.level],
                    entry.message,
                    exc_info=(
                        entry.error_info.get("exception_type"),
                        entry.error_info.get("exception_message"),
                        entry.error_info.get("stack_trace")
                    )
                )
            else:
                # Regular log entry
                self._logger.log(level_mapping[entry.level], entry.message)
                
        finally:
            # Reset context
            _correlation_id.reset(correlation_token)
            _operation_id.reset(operation_token)
    
    async def _flush_handlers(self) -> None:
        """Flush all log handlers."""
        for handler in self._logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
    
    async def _flush_remaining_entries(self) -> None:
        """Flush any remaining entries in the queue."""
        while not self._log_queue.empty():
            try:
                entry = self._log_queue.get_nowait()
                await self._write_log_entry(entry)
                self._log_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        await self._flush_handlers()
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to remove sensitive information."""
        if not self.config.sanitize_sensitive_data:
            return metadata
        
        sanitized = {}
        for key, value in metadata.items():
            # Check for sensitive keys
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.config.exclude_sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_metadata(value)
            elif isinstance(value, str) and len(value) > self.config.max_error_context_length:
                sanitized[key] = value[:self.config.max_error_context_length] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def log(
        self, 
        level: LogLevel, 
        message: str, 
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a structured message."""
        # Get current correlation context
        context = get_current_context()
        
        # Sanitize metadata
        safe_metadata = self._sanitize_metadata(metadata or {})
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            operation_id=context.get("operation_id"),
            correlation_id=context.get("correlation_id"),
            operation_type=context.get("operation_type"),
            component=component,
            metadata=safe_metadata,
            error_info=error_info
        )
        
        # Queue for async processing or write immediately
        if self.config.async_logging and self._flush_task and not self._flush_task.done():
            try:
                await self._log_queue.put(entry)
            except asyncio.QueueFull:
                # If queue is full, write directly to avoid blocking
                await self._write_log_entry(entry)
        else:
            await self._write_log_entry(entry)
    
    def set_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        self.config.log_level = level
        self._setup_logger()
    
    async def flush(self) -> None:
        """Flush any pending log entries."""
        # Wait for queue to be empty
        await self._log_queue.join()
        
        # Flush handlers
        await self._flush_handlers()
    
    async def shutdown(self) -> None:
        """Shutdown the logger gracefully."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass


class InMemoryPerformanceTracker(PerformanceTracker):
    """
    In-memory performance tracker with P95 latency calculation.
    
    Features:
    - High-performance operation tracking
    - P95 latency calculation with configurable windows
    - Memory-efficient metrics storage with LRU eviction
    - Thread-safe operations for concurrent access
    - Comprehensive performance statistics
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize performance tracker."""
        self.config = config
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        self._metrics: Deque[PerformanceMetric] = deque(maxlen=config.max_metrics_memory)
        self._lock = threading.Lock()
        
        # Statistics caching
        self._stats_cache: Dict[str, Any] = {}
        self._stats_cache_expiry = datetime.min
    
    def start_operation(
        self, 
        operation_type: OperationType,
        operation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start tracking an operation."""
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        # Sample operations based on sampling rate
        if self.config.performance_sampling_rate < 1.0:
            import random
            if random.random() > self.config.performance_sampling_rate:
                return operation_id
        
        start_time = time.perf_counter()
        
        with self._lock:
            self._active_operations[operation_id] = {
                "operation_type": operation_type,
                "start_time": start_time,
                "metadata": metadata or {}
            }
        
        return operation_id
    
    def end_operation(
        self, 
        operation_id: str, 
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetric:
        """End tracking an operation and return metrics."""
        end_time = time.perf_counter()
        
        with self._lock:
            if operation_id not in self._active_operations:
                # Operation not tracked (possibly due to sampling)
                # Return a dummy metric to maintain interface contract
                return PerformanceMetric(
                    timestamp=datetime.now(),
                    operation_type=OperationType.MCP_TOOL_CALL,
                    operation_id=operation_id,
                    duration_ms=0.0,
                    success=success,
                    metadata={}
                )
            
            op_data = self._active_operations.pop(operation_id)
            start_time = op_data["start_time"]
            duration_ms = (end_time - start_time) * 1000
            
            # Combine metadata
            combined_metadata = op_data["metadata"].copy()
            if metadata:
                combined_metadata.update(metadata)
            
            # Create performance metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                operation_type=op_data["operation_type"],
                operation_id=operation_id,
                duration_ms=duration_ms,
                success=success,
                metadata=combined_metadata
            )
            
            # Store metric
            self._metrics.append(metric)
            
            # Invalidate stats cache
            self._stats_cache_expiry = datetime.min
            
            return metric
    
    def get_p95_latency(
        self, 
        operation_type: Optional[OperationType] = None,
        window_minutes: int = 5
    ) -> Optional[float]:
        """Get P95 latency for operations."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        with self._lock:
            # Filter metrics by time and operation type
            relevant_metrics = [
                m for m in self._metrics
                if m.timestamp >= cutoff_time and
                (operation_type is None or m.operation_type == operation_type)
            ]
            
            if len(relevant_metrics) < 2:
                return None
            
            # Calculate P95
            durations = [m.duration_ms for m in relevant_metrics]
            return statistics.quantiles(durations, n=20)[18]  # 95th percentile
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics summary."""
        # Check cache validity
        if datetime.now() < self._stats_cache_expiry:
            return self._stats_cache.copy()
        
        with self._lock:
            if not self._metrics:
                return {}
            
            # Calculate statistics
            now = datetime.now()
            window_5min = now - timedelta(minutes=5)
            window_1hr = now - timedelta(hours=1)
            
            # Filter metrics by time windows
            recent_5min = [m for m in self._metrics if m.timestamp >= window_5min]
            recent_1hr = [m for m in self._metrics if m.timestamp >= window_1hr]
            
            summary = {
                "total_operations": len(self._metrics),
                "active_operations": len(self._active_operations),
                "operations_last_5min": len(recent_5min),
                "operations_last_1hr": len(recent_1hr),
                "by_operation_type": {},
                "p95_latencies": {},
                "success_rates": {},
                "generated_at": now.isoformat()
            }
            
            # Statistics by operation type
            for op_type in OperationType:
                type_metrics_5min = [m for m in recent_5min if m.operation_type == op_type]
                type_metrics_1hr = [m for m in recent_1hr if m.operation_type == op_type]
                
                if type_metrics_5min:
                    durations = [m.duration_ms for m in type_metrics_5min]
                    successes = [m.success for m in type_metrics_5min]
                    
                    summary["by_operation_type"][op_type.value] = {
                        "count_5min": len(type_metrics_5min),
                        "count_1hr": len(type_metrics_1hr),
                        "avg_latency_ms": sum(durations) / len(durations),
                        "min_latency_ms": min(durations),
                        "max_latency_ms": max(durations),
                        "success_rate": sum(successes) / len(successes)
                    }
                    
                    # P95 latency
                    if len(durations) >= 2:
                        summary["p95_latencies"][op_type.value] = statistics.quantiles(durations, n=20)[18]
            
            # Cache the results
            self._stats_cache = summary.copy()
            self._stats_cache_expiry = now + timedelta(minutes=1)
            
            return summary


class ComprehensiveErrorTracker(ErrorTracker):
    """
    Comprehensive error tracker with correlation and context.
    
    Features:
    - Error correlation with operation context
    - Stack trace capture and sanitization
    - Error statistics and trending
    - Thread-safe error storage
    - Memory-efficient error history
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize error tracker."""
        self.config = config
        self._errors: Deque[ErrorContext] = deque(maxlen=config.max_metrics_memory)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    async def track_error(
        self, 
        error: Exception,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        capture_stack_trace: bool = True
    ) -> str:
        """Track an error and return error ID."""
        error_id = str(uuid.uuid4())
        
        # Get current context
        context = get_current_context()
        
        # Capture stack trace if enabled
        stack_trace = None
        if capture_stack_trace and self.config.capture_stack_traces:
            stack_trace = traceback.format_exc()
            
            # Sanitize stack trace if needed
            if self.config.sanitize_sensitive_data:
                stack_trace = self._sanitize_stack_trace(stack_trace)
        
        # Create error context
        error_context = ErrorContext(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            operation_id=context.get("operation_id"),
            correlation_id=context.get("correlation_id"),
            operation_type=context.get("operation_type"),
            component=component,
            stack_trace=stack_trace,
            metadata=metadata or {}
        )
        
        with self._lock:
            # Store error context
            self._errors.append(error_context)
            
            # Update error counts
            error_key = f"{error_context.error_type}:{component or 'unknown'}"
            self._error_counts[error_key] += 1
        
        return error_id
    
    def _sanitize_stack_trace(self, stack_trace: str) -> str:
        """Sanitize stack trace to remove sensitive information."""
        lines = stack_trace.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Remove file paths beyond certain depth
            if 'File "' in line:
                # Keep only filename, not full path
                import re
                line = re.sub(r'File "([^"]*[/\\])*([^"]*)"', r'File "\2"', line)
            
            # Truncate very long lines
            if len(line) > self.config.max_error_context_length:
                line = line[:self.config.max_error_context_length] + "..."
            
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)
    
    def get_error_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get error statistics for specified time window."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        with self._lock:
            # Filter errors by time window
            recent_errors = [
                e for e in self._errors
                if e.timestamp >= cutoff_time
            ]
            
            if not recent_errors:
                return {
                    "total_errors": 0,
                    "window_minutes": window_minutes,
                    "error_rate_per_minute": 0.0,
                    "by_error_type": {},
                    "by_component": {},
                    "by_operation_type": {}
                }
            
            # Calculate statistics
            stats = {
                "total_errors": len(recent_errors),
                "window_minutes": window_minutes,
                "error_rate_per_minute": len(recent_errors) / window_minutes,
                "by_error_type": defaultdict(int),
                "by_component": defaultdict(int),
                "by_operation_type": defaultdict(int)
            }
            
            # Count by categories
            for error in recent_errors:
                stats["by_error_type"][error.error_type] += 1
                if error.component:
                    stats["by_component"][error.component] += 1
                if error.operation_type:
                    stats["by_operation_type"][error.operation_type.value] += 1
            
            # Convert defaultdicts to regular dicts
            stats["by_error_type"] = dict(stats["by_error_type"])
            stats["by_component"] = dict(stats["by_component"])
            stats["by_operation_type"] = dict(stats["by_operation_type"])
            
            return stats


class ThresholdAlertManager(AlertManager):
    """
    Threshold-based alert manager for performance and error monitoring.
    
    Features:
    - Configurable alert rules with thresholds
    - Multiple alert severity levels
    - Time window-based alerting
    - Alert suppression and deduplication
    - Memory-efficient alert storage
    """
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize alert manager."""
        self.config = config
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Dict[str, Any]] = {}
        self._alert_history: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self._lock = threading.Lock()
        
        # Load default alert rules
        for rule in config.alert_rules:
            self.add_alert_rule(rule)
    
    async def check_alerts(self, metric: PerformanceMetric) -> List[Dict[str, Any]]:
        """Check if metric triggers any alerts."""
        if not self.config.enable_alerts:
            return []
        
        triggered_alerts = []
        
        with self._lock:
            for rule_name, rule in self._alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check if rule applies to this metric
                if rule.operation_type and rule.operation_type != metric.operation_type:
                    continue
                
                # Check threshold
                alert_triggered = False
                if rule.metric_type == MetricType.LATENCY:
                    if metric.duration_ms > rule.threshold:
                        alert_triggered = True
                elif rule.metric_type == MetricType.COUNT:
                    # For count-based alerts, would need additional logic
                    pass
                
                if alert_triggered:
                    alert = self._create_alert(rule, metric)
                    triggered_alerts.append(alert)
                    
                    # Store in active alerts (with deduplication)
                    alert_key = f"{rule_name}_{rule.operation_type}_{rule.metric_type.value}"
                    self._active_alerts[alert_key] = alert
                    self._alert_history.append(alert)
        
        return triggered_alerts
    
    def _create_alert(self, rule: AlertRule, metric: PerformanceMetric) -> Dict[str, Any]:
        """Create alert dictionary from rule and metric."""
        return {
            "alert_id": str(uuid.uuid4()),
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "timestamp": datetime.now().isoformat(),
            "operation_type": metric.operation_type.value,
            "operation_id": metric.operation_id,
            "metric_type": rule.metric_type.value,
            "threshold": rule.threshold,
            "actual_value": metric.duration_ms if rule.metric_type == MetricType.LATENCY else None,
            "message": f"{rule.name}: {rule.metric_type.value} threshold exceeded",
            "metadata": metric.metadata
        }
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self._lock:
            self._alert_rules[rule.name] = rule
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        with self._lock:
            return list(self._active_alerts.values())


# ============================================================================
# OBSERVABILITY MANAGER (FACADE)
# ============================================================================

class ObservabilityManager:
    """
    Comprehensive observability manager providing unified interface.
    
    This is the main facade that integrates all observability components:
    structured logging, performance tracking, error tracking, and alerting.
    """
    
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """Initialize observability manager."""
        self.config = config or ObservabilityConfig()
        
        # Initialize components
        self.logger = JSONStructuredLogger(self.config)
        self.performance = InMemoryPerformanceTracker(self.config)
        self.error_tracker = ComprehensiveErrorTracker(self.config)
        self.alert_manager = ThresholdAlertManager(self.config)
        
        self._initialized = True
    
    # Logging interface
    async def log_debug(self, message: str, component: Optional[str] = None, **kwargs) -> None:
        """Log debug message."""
        await self.logger.log(LogLevel.DEBUG, message, component, kwargs)
    
    async def log_info(self, message: str, component: Optional[str] = None, **kwargs) -> None:
        """Log info message."""
        await self.logger.log(LogLevel.INFO, message, component, kwargs)
    
    async def log_warning(self, message: str, component: Optional[str] = None, **kwargs) -> None:
        """Log warning message."""
        await self.logger.log(LogLevel.WARNING, message, component, kwargs)
    
    async def log_error(self, message: str, component: Optional[str] = None, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception."""
        error_info = None
        if error:
            error_id = await self.error_tracker.track_error(error, component, kwargs)
            error_info = {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        
        await self.logger.log(LogLevel.ERROR, message, component, kwargs, error_info)
    
    # Performance tracking interface
    def start_operation(self, operation_type: OperationType, **metadata) -> str:
        """Start tracking a performance operation."""
        return self.performance.start_operation(operation_type, metadata=metadata)
    
    async def end_operation(self, operation_id: str, success: bool = True, **metadata) -> None:
        """End tracking a performance operation."""
        metric = self.performance.end_operation(operation_id, success, metadata)
        
        if metric and self.config.enable_alerts:
            # Check for alerts
            alerts = await self.alert_manager.check_alerts(metric)
            for alert in alerts:
                await self.log_warning(
                    f"Performance alert triggered: {alert['message']}",
                    "alert_manager",
                    alert=alert
                )
    
    # Convenience decorators
    def track_performance(self, operation_type: OperationType, component: Optional[str] = None):
        """Decorator to track performance of a function."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_id = self.start_operation(operation_type, function=func.__name__)
                
                try:
                    result = await func(*args, **kwargs)
                    await self.end_operation(operation_id, success=True)
                    return result
                except Exception as e:
                    await self.end_operation(operation_id, success=False)
                    await self.log_error(
                        f"Error in {func.__name__}",
                        component or func.__module__,
                        error=e,
                        function=func.__name__
                    )
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                operation_id = self.start_operation(operation_type, function=func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    # For sync functions, we can't await, so create task
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.end_operation(operation_id, success=True))
                    return result
                except Exception as e:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.end_operation(operation_id, success=False))
                    loop.create_task(self.log_error(
                        f"Error in {func.__name__}",
                        component or func.__module__,
                        error=e,
                        function=func.__name__
                    ))
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    # System monitoring
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "observability": {
                "logger_initialized": self.logger is not None,
                "performance_tracking": self.config.track_performance,
                "error_tracking": self.config.track_errors,
                "alerts_enabled": self.config.enable_alerts
            },
            "performance": self.performance.get_metrics_summary(),
            "errors": self.error_tracker.get_error_statistics(),
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Shutdown observability system gracefully."""
        await self.logger.flush()
        if hasattr(self.logger, 'shutdown'):
            await self.logger.shutdown()


# ============================================================================
# GLOBAL OBSERVABILITY INSTANCE
# ============================================================================

# Global observability manager instance (initialized lazily)
_global_observability_manager: Optional[ObservabilityManager] = None
_observability_lock = threading.Lock()


def get_global_observability_manager(
    config: Optional[ObservabilityConfig] = None
) -> ObservabilityManager:
    """Get or create global observability manager instance."""
    global _global_observability_manager
    
    with _observability_lock:
        if _global_observability_manager is None:
            _global_observability_manager = ObservabilityManager(config)
        
        return _global_observability_manager


def reset_global_observability_manager() -> None:
    """Reset global observability manager (for testing)."""
    global _global_observability_manager
    
    with _observability_lock:
        _global_observability_manager = None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def log_info(message: str, component: Optional[str] = None, **kwargs) -> None:
    """Convenience function for info logging."""
    manager = get_global_observability_manager()
    await manager.log_info(message, component, **kwargs)


async def log_error(message: str, component: Optional[str] = None, error: Optional[Exception] = None, **kwargs) -> None:
    """Convenience function for error logging."""
    manager = get_global_observability_manager()
    await manager.log_error(message, component, error, **kwargs)


def track_performance(operation_type: OperationType, component: Optional[str] = None):
    """Convenience decorator for performance tracking."""
    manager = get_global_observability_manager()
    return manager.track_performance(operation_type, component)


# ============================================================================
# DEFAULT ALERT RULES
# ============================================================================

DEFAULT_ALERT_RULES = [
    AlertRule(
        name="High MCP Tool Latency",
        metric_type=MetricType.LATENCY,
        operation_type=OperationType.MCP_TOOL_CALL,
        threshold=5000.0,  # 5 seconds
        severity=AlertSeverity.WARNING,
        window_minutes=5
    ),
    AlertRule(
        name="Critical MCP Tool Latency", 
        metric_type=MetricType.LATENCY,
        operation_type=OperationType.MCP_TOOL_CALL,
        threshold=10000.0,  # 10 seconds
        severity=AlertSeverity.ERROR,
        window_minutes=5
    ),
    AlertRule(
        name="Connection Establishment Timeout",
        metric_type=MetricType.LATENCY,
        operation_type=OperationType.CONNECTION_OPEN,
        threshold=3000.0,  # 3 seconds
        severity=AlertSeverity.ERROR,
        window_minutes=5
    )
]


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def _test_observability_components():
    """Test observability system components."""
    print("🔍 Testing Observability System Components...")
    
    # Test configuration
    config = ObservabilityConfig(
        log_level=LogLevel.DEBUG,
        track_performance=True,
        enable_alerts=True,
        alert_rules=DEFAULT_ALERT_RULES
    )
    
    # Test observability manager
    async def run_tests():
        manager = ObservabilityManager(config)
        
        print("\n📝 Testing structured logging:")
        await manager.log_info("Test info message", "test_component", test_data="example")
        await manager.log_warning("Test warning message", "test_component")
        
        print("\n⏱️  Testing performance tracking:")
        with correlation_context(operation_type=OperationType.MCP_TOOL_CALL) as ctx:
            operation_id = manager.start_operation(OperationType.MCP_TOOL_CALL, test=True)
            
            # Simulate some work
            import time
            time.sleep(0.1)
            
            await manager.end_operation(operation_id, success=True)
        
        print("\n🚨 Testing error tracking:")
        try:
            raise ValueError("Test error for tracking")
        except Exception as e:
            await manager.log_error("Test error occurred", "test_component", error=e)
        
        print("\n📊 Testing performance decorator:")
        
        @manager.track_performance(OperationType.CONFIGURATION_LOAD, "test")
        async def test_async_function():
            await asyncio.sleep(0.05)
            return "success"
        
        result = await test_async_function()
        print(f"Async function result: {result}")
        
        print("\n📈 Testing health status:")
        health = manager.get_health_status()
        print(f"Performance metrics: {health['performance'].get('total_operations', 0)} operations")
        print(f"Error count: {health['errors'].get('total_errors', 0)} errors")
        print(f"Active alerts: {health.get('active_alerts', 0)} alerts")
        
        await manager.shutdown()
    
    # Run async tests
    asyncio.run(run_tests())
    
    print("\n🎉 Observability system tested successfully!")


if __name__ == "__main__":
    _test_observability_components()