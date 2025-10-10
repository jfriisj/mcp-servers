"""
Study Buddy GUI - Performance Monitoring System

Provides operation timing alerts, performance degradation detection,
and performance monitoring integration with error handling.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Observer Pattern, Strategy Pattern, Threshold Pattern
SOLID: SRP (performance monitoring), OCP (extensible alerts), DIP (abstraction-based)
"""

import asyncio
import statistics
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union
from collections import deque, defaultdict

from gui.error_handling.error_tracker import ErrorSeverity, ErrorTracker, get_error_tracker
from gui.performance.memory_monitor import get_memory_monitor


class PerformanceMetric(Enum):
    """Types of performance metrics tracked."""
    
    OPERATION_TIME = "operation_time"      # Operation execution time
    MEMORY_USAGE = "memory_usage"          # Memory consumption  
    CPU_USAGE = "cpu_usage"               # CPU utilization
    NETWORK_LATENCY = "network_latency"    # Network response time
    UI_RESPONSIVENESS = "ui_responsiveness" # UI update time
    THROUGHPUT = "throughput"              # Operations per second


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    
    metric: PerformanceMetric
    warning_value: float
    critical_value: float
    measurement_unit: str = ""
    description: str = ""
    enabled: bool = True
    
    def check_value(self, value: float) -> Optional[ErrorSeverity]:
        """
        Check value against thresholds.
        
        Args:
            value: Value to check
            
        Returns:
            ErrorSeverity if threshold exceeded, None otherwise
        """
        if not self.enabled:
            return None
        
        if value >= self.critical_value:
            return ErrorSeverity.HIGH
        elif value >= self.warning_value:
            return ErrorSeverity.MEDIUM
        
        return None


@dataclass
class PerformanceAlert:
    """Performance alert information."""
    
    metric: PerformanceMetric
    severity: ErrorSeverity
    current_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    operation_id: Optional[str] = None
    operation_name: str = ""
    widget_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric.value,
            "severity": self.severity.value,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "operation_id": self.operation_id,
            "operation_name": self.operation_name,
            "widget_id": self.widget_id,
            "context": self.context,
        }


class IPerformanceAlertHandler(ABC):
    """Interface for handling performance alerts."""
    
    @abstractmethod
    def handle_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        pass


class LoggingAlertHandler(IPerformanceAlertHandler):
    """Logs performance alerts to debug logger."""
    
    def handle_alert(self, alert: PerformanceAlert) -> None:
        """Log performance alert."""
        try:
            from gui.error_handling.debug_logger import get_debug_logger
            
            logger = get_debug_logger()
            message = (
                f"Performance alert: {alert.operation_name or alert.metric.value} "
                f"exceeded threshold ({alert.current_value:.2f} > {alert.threshold_value:.2f})"
            )
            
            if alert.severity == ErrorSeverity.HIGH:
                logger.error(message, 
                    metric=alert.metric.value,
                    current_value=alert.current_value,
                    threshold_value=alert.threshold_value,
                    operation_id=alert.operation_id,
                    widget_id=alert.widget_id,
                    **alert.context
                )
            else:
                logger.warning(message,
                    metric=alert.metric.value,
                    current_value=alert.current_value, 
                    threshold_value=alert.threshold_value,
                    operation_id=alert.operation_id,
                    widget_id=alert.widget_id,
                    **alert.context
                )
        except Exception:
            # Don't fail performance monitoring if logging fails
            pass


class ErrorTrackingAlertHandler(IPerformanceAlertHandler):
    """Creates error tracker entries for performance alerts."""
    
    def __init__(self):
        self._error_tracker = get_error_tracker()
    
    def handle_alert(self, alert: PerformanceAlert) -> None:
        """Create error tracker entry for performance issue."""
        try:
            from gui.error_handling.error_tracker import ErrorCategory
            
            # Create performance exception
            class PerformanceThresholdException(Exception):
                pass
            
            message = (
                f"Performance threshold exceeded: {alert.metric.value} "
                f"({alert.current_value:.2f} > {alert.threshold_value:.2f})"
            )
            
            exception = PerformanceThresholdException(message)
            
            self._error_tracker.capture_error(
                exception=exception,
                severity=alert.severity,
                category=ErrorCategory.PERFORMANCE,
                widget_id=alert.widget_id,
                user_action=f"Performance monitoring: {alert.operation_name}",
                operation_context={
                    "metric": alert.metric.value,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "operation_id": alert.operation_id,
                    **alert.context
                }
            )
        except Exception:
            # Don't fail performance monitoring if error tracking fails  
            pass


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""
    
    operation_name: str
    execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    success_count: int = 0
    failure_count: int = 0
    last_execution: Optional[datetime] = None
    
    def add_execution_time(self, time_ms: float, success: bool = True) -> None:
        """Add execution time measurement."""
        self.execution_times.append(time_ms)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_execution = datetime.now(timezone.utc)
    
    def get_average_time(self) -> float:
        """Get average execution time."""
        return statistics.mean(self.execution_times) if self.execution_times else 0.0
    
    def get_median_time(self) -> float:
        """Get median execution time."""
        return statistics.median(self.execution_times) if self.execution_times else 0.0
    
    def get_p95_time(self) -> float:
        """Get 95th percentile execution time."""
        if not self.execution_times:
            return 0.0
        sorted_times = sorted(self.execution_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_success_rate(self) -> float:
        """Get operation success rate."""
        total = self.success_count + self.failure_count
        return (self.success_count / total) if total > 0 else 0.0


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    
    Responsibilities:
    - Track operation execution times and success rates
    - Monitor system resource usage
    - Detect performance degradation
    - Generate alerts for threshold violations
    - Provide performance analytics and statistics
    """
    
    def __init__(self):
        self._thresholds: Dict[PerformanceMetric, PerformanceThreshold] = {}
        self._alert_handlers: List[IPerformanceAlertHandler] = []
        self._operation_metrics: Dict[str, OperationMetrics] = {}
        self._lock = threading.RLock()
        
        # Performance history
        self._performance_history: Dict[PerformanceMetric, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Setup default thresholds
        self._setup_default_thresholds()
        
        # Setup default alert handlers
        self._setup_default_handlers()
        
        # Memory monitor integration
        self._memory_monitor = None
        try:
            self._memory_monitor = get_memory_monitor()
        except Exception:
            pass
    
    def _setup_default_thresholds(self) -> None:
        """Setup default performance thresholds."""
        self._thresholds = {
            PerformanceMetric.OPERATION_TIME: PerformanceThreshold(
                metric=PerformanceMetric.OPERATION_TIME,
                warning_value=2000.0,  # 2 seconds
                critical_value=5000.0,  # 5 seconds
                measurement_unit="ms",
                description="Operation execution time",
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.MEMORY_USAGE,
                warning_value=400.0,  # 400 MB
                critical_value=500.0,  # 500 MB
                measurement_unit="MB", 
                description="Application memory usage",
            ),
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.CPU_USAGE,
                warning_value=80.0,   # 80%
                critical_value=95.0,  # 95%
                measurement_unit="%",
                description="CPU utilization",
            ),
            PerformanceMetric.NETWORK_LATENCY: PerformanceThreshold(
                metric=PerformanceMetric.NETWORK_LATENCY,
                warning_value=3000.0,  # 3 seconds
                critical_value=10000.0,  # 10 seconds
                measurement_unit="ms",
                description="Network operation latency",
            ),
            PerformanceMetric.UI_RESPONSIVENESS: PerformanceThreshold(
                metric=PerformanceMetric.UI_RESPONSIVENESS,
                warning_value=100.0,   # 100ms
                critical_value=500.0,  # 500ms  
                measurement_unit="ms",
                description="UI update responsiveness",
            ),
            PerformanceMetric.THROUGHPUT: PerformanceThreshold(
                metric=PerformanceMetric.THROUGHPUT,
                warning_value=5.0,     # Min 5 ops/sec
                critical_value=1.0,    # Min 1 ops/sec
                measurement_unit="ops/sec",
                description="Operation throughput",
            ),
        }
    
    def _setup_default_handlers(self) -> None:
        """Setup default alert handlers."""
        self.add_alert_handler(LoggingAlertHandler())
        self.add_alert_handler(ErrorTrackingAlertHandler())
    
    def add_alert_handler(self, handler: IPerformanceAlertHandler) -> None:
        """Add performance alert handler."""
        with self._lock:
            if handler not in self._alert_handlers:
                self._alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: IPerformanceAlertHandler) -> None:
        """Remove performance alert handler."""
        with self._lock:
            if handler in self._alert_handlers:
                self._alert_handlers.remove(handler)
    
    def set_threshold(self, threshold: PerformanceThreshold) -> None:
        """Set performance threshold."""
        with self._lock:
            self._thresholds[threshold.metric] = threshold
    
    def get_threshold(self, metric: PerformanceMetric) -> Optional[PerformanceThreshold]:
        """Get performance threshold."""
        with self._lock:
            return self._thresholds.get(metric)
    
    def record_operation_time(
        self,
        operation_name: str,
        execution_time_ms: float,
        success: bool = True,
        widget_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        **context
    ) -> None:
        """
        Record operation execution time.
        
        Args:
            operation_name: Name of the operation
            execution_time_ms: Execution time in milliseconds
            success: Whether operation was successful
            widget_id: ID of widget that performed operation
            operation_id: Unique operation identifier
            **context: Additional context information
        """
        with self._lock:
            # Record operation metrics
            if operation_name not in self._operation_metrics:
                self._operation_metrics[operation_name] = OperationMetrics(operation_name)
            
            metrics = self._operation_metrics[operation_name]
            metrics.add_execution_time(execution_time_ms, success)
            
            # Record in performance history
            self._performance_history[PerformanceMetric.OPERATION_TIME].append({
                "timestamp": datetime.now(timezone.utc),
                "value": execution_time_ms,
                "operation": operation_name,
                "success": success,
                "widget_id": widget_id,
                "operation_id": operation_id,
                **context
            })
            
            # Check threshold
            threshold = self._thresholds.get(PerformanceMetric.OPERATION_TIME)
            if threshold:
                severity = threshold.check_value(execution_time_ms)
                if severity:
                    alert = PerformanceAlert(
                        metric=PerformanceMetric.OPERATION_TIME,
                        severity=severity,
                        current_value=execution_time_ms,
                        threshold_value=threshold.critical_value if severity == ErrorSeverity.HIGH else threshold.warning_value,
                        operation_id=operation_id,
                        operation_name=operation_name,
                        widget_id=widget_id,
                        context=context,
                    )
                    self._trigger_alert(alert)
    
    def record_memory_usage(
        self,
        memory_mb: float,
        widget_id: Optional[str] = None,
        **context
    ) -> None:
        """Record memory usage measurement."""
        with self._lock:
            # Record in history
            self._performance_history[PerformanceMetric.MEMORY_USAGE].append({
                "timestamp": datetime.now(timezone.utc),
                "value": memory_mb,
                "widget_id": widget_id,
                **context
            })
            
            # Check threshold
            threshold = self._thresholds.get(PerformanceMetric.MEMORY_USAGE)
            if threshold:
                severity = threshold.check_value(memory_mb)
                if severity:
                    alert = PerformanceAlert(
                        metric=PerformanceMetric.MEMORY_USAGE,
                        severity=severity,
                        current_value=memory_mb,
                        threshold_value=threshold.critical_value if severity == ErrorSeverity.HIGH else threshold.warning_value,
                        widget_id=widget_id,
                        context=context,
                    )
                    self._trigger_alert(alert)
    
    def record_network_latency(
        self,
        latency_ms: float,
        operation_name: str = "",
        **context
    ) -> None:
        """Record network operation latency."""
        with self._lock:
            # Record in history
            self._performance_history[PerformanceMetric.NETWORK_LATENCY].append({
                "timestamp": datetime.now(timezone.utc),
                "value": latency_ms,
                "operation": operation_name,
                **context
            })
            
            # Check threshold
            threshold = self._thresholds.get(PerformanceMetric.NETWORK_LATENCY)
            if threshold:
                severity = threshold.check_value(latency_ms)
                if severity:
                    alert = PerformanceAlert(
                        metric=PerformanceMetric.NETWORK_LATENCY,
                        severity=severity,
                        current_value=latency_ms,
                        threshold_value=threshold.critical_value if severity == ErrorSeverity.HIGH else threshold.warning_value,
                        operation_name=operation_name,
                        context=context,
                    )
                    self._trigger_alert(alert)
    
    def get_operation_statistics(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for specific operation."""
        with self._lock:
            metrics = self._operation_metrics.get(operation_name)
            if not metrics:
                return None
            
            return {
                "operation_name": operation_name,
                "total_executions": len(metrics.execution_times),
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "success_rate": metrics.get_success_rate(),
                "average_time_ms": metrics.get_average_time(),
                "median_time_ms": metrics.get_median_time(),
                "p95_time_ms": metrics.get_p95_time(),
                "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None,
            }
    
    def get_all_operation_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all operations."""
        with self._lock:
            stats = []
            for op_name in self._operation_metrics.keys():
                op_stats = self.get_operation_statistics(op_name)
                if op_stats is not None:
                    stats.append(op_stats)
            return stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_operations": len(self._operation_metrics),
                "metrics_tracked": len(self._performance_history),
                "alert_handlers": len(self._alert_handlers),
            }
            
            # Add metric summaries
            for metric, history in self._performance_history.items():
                if history:
                    recent_values = [entry["value"] for entry in list(history)[-10:]]
                    summary[f"{metric.value}_recent_avg"] = statistics.mean(recent_values)
                    summary[f"{metric.value}_recent_max"] = max(recent_values)
                    summary[f"{metric.value}_total_samples"] = len(history)
            
            return summary
    
    def detect_performance_degradation(self, operation_name: str, window_size: int = 10) -> Optional[Dict[str, Any]]:
        """
        Detect performance degradation for operation.
        
        Args:
            operation_name: Operation to analyze
            window_size: Number of recent samples to compare
            
        Returns:
            Degradation analysis or None if no degradation detected
        """
        with self._lock:
            metrics = self._operation_metrics.get(operation_name)
            if not metrics or len(metrics.execution_times) < window_size * 2:
                return None
            
            # Compare recent performance to historical baseline
            times = list(metrics.execution_times)
            recent_times = times[-window_size:]
            historical_times = times[:-window_size]
            
            recent_avg = statistics.mean(recent_times)
            historical_avg = statistics.mean(historical_times)
            
            # Check for significant degradation (>50% increase)
            degradation_factor = recent_avg / historical_avg if historical_avg > 0 else 1.0
            
            if degradation_factor > 1.5:  # 50% slower
                return {
                    "operation_name": operation_name,
                    "degradation_factor": degradation_factor,
                    "recent_avg_ms": recent_avg,
                    "historical_avg_ms": historical_avg,
                    "degradation_percentage": (degradation_factor - 1.0) * 100,
                    "samples_analyzed": len(times),
                }
            
            return None
    
    def clear_metrics(self, operation_name: Optional[str] = None) -> None:
        """Clear performance metrics."""
        with self._lock:
            if operation_name:
                if operation_name in self._operation_metrics:
                    del self._operation_metrics[operation_name]
            else:
                self._operation_metrics.clear()
                self._performance_history.clear()
    
    def _trigger_alert(self, alert: PerformanceAlert) -> None:
        """Trigger performance alert to all handlers."""
        for handler in self._alert_handlers:
            try:
                handler.handle_alert(alert)
            except Exception:
                # Don't fail performance monitoring if handler fails
                pass


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None
_performance_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance (singleton pattern).
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        with _performance_monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


# Context managers for performance tracking
class TimedOperation:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        operation_name: str,
        widget_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        **context
    ):
        self.operation_name = operation_name
        self.widget_id = widget_id
        self.operation_id = operation_id
        self.context = context
        self.start_time = None
        self.monitor = get_performance_monitor()
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            execution_time = (time.time() - self.start_time) * 1000  # Convert to ms
            success = exc_type is None
            
            self.monitor.record_operation_time(
                operation_name=self.operation_name,
                execution_time_ms=execution_time,
                success=success,
                widget_id=self.widget_id,
                operation_id=self.operation_id,
                **self.context
            )


def timed_operation(operation_name: str, widget_id: Optional[str] = None, **context):
    """Create timed operation context manager."""
    return TimedOperation(operation_name, widget_id, **context)


# Convenience functions
def record_operation(operation_name: str, execution_time_ms: float, success: bool = True, **context) -> None:
    """Record operation performance."""
    monitor = get_performance_monitor()
    monitor.record_operation_time(operation_name, execution_time_ms, success, **context)


def record_memory(memory_mb: float, **context) -> None:
    """Record memory usage."""
    monitor = get_performance_monitor()
    monitor.record_memory_usage(memory_mb, **context)


def record_network(latency_ms: float, operation_name: str = "", **context) -> None:
    """Record network latency."""
    monitor = get_performance_monitor()
    monitor.record_network_latency(latency_ms, operation_name, **context)