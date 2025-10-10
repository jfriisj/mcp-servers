"""
Study Buddy GUI - Memory Monitor

Provides memory usage tracking and optimization for GUI components.
Monitors widget memory usage, cache sizes, and provides alerts for memory thresholds.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Observer Pattern (notifications), Singleton Pattern (global monitor)
SOLID: SRP (memory monitoring only), DIP (abstraction-based interfaces)
"""

import gc
import logging
import psutil
import threading
import time
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

try:
    import tracemalloc

    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False


class MemoryUnit(Enum):
    """Memory measurement units."""

    BYTES = "B"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"


class MemoryAlertLevel(Enum):
    """Memory alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MemoryUsage:
    """Memory usage information."""

    total_bytes: int = 0
    available_bytes: int = 0
    used_bytes: int = 0
    percentage: float = 0.0

    def format_bytes(
        self, bytes_value: int, unit: MemoryUnit = MemoryUnit.MEGABYTES
    ) -> str:
        """Format bytes value in specified unit."""
        conversions = {
            MemoryUnit.BYTES: 1,
            MemoryUnit.KILOBYTES: 1024,
            MemoryUnit.MEGABYTES: 1024 * 1024,
            MemoryUnit.GIGABYTES: 1024 * 1024 * 1024,
        }

        divisor = conversions[unit]
        value = bytes_value / divisor

        return f"{value:.1f} {unit.value}"

    def to_dict(self, unit: MemoryUnit = MemoryUnit.MEGABYTES) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total": self.format_bytes(self.total_bytes, unit),
            "available": self.format_bytes(self.available_bytes, unit),
            "used": self.format_bytes(self.used_bytes, unit),
            "percentage": f"{self.percentage:.1f}%",
            "total_bytes": self.total_bytes,
            "available_bytes": self.available_bytes,
            "used_bytes": self.used_bytes,
        }


@dataclass
class WidgetMemoryInfo:
    """Memory information for a specific widget."""

    widget_id: str
    widget_class: str
    memory_bytes: int = 0
    object_count: int = 0
    last_updated: float = field(default_factory=time.time)

    def age_seconds(self) -> float:
        """Get age of this measurement in seconds."""
        return time.time() - self.last_updated

    def format_memory(self, unit: MemoryUnit = MemoryUnit.KILOBYTES) -> str:
        """Format memory usage in specified unit."""
        usage = MemoryUsage()
        return usage.format_bytes(self.memory_bytes, unit)


@dataclass
class MemoryAlert:
    """Memory usage alert."""

    level: MemoryAlertLevel
    message: str
    current_usage: MemoryUsage
    threshold_percentage: float
    timestamp: float = field(default_factory=time.time)
    component: Optional[str] = None

    def age_seconds(self) -> float:
        """Get age of this alert in seconds."""
        return time.time() - self.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "level": self.level.value,
            "message": self.message,
            "usage": self.current_usage.to_dict(),
            "threshold": f"{self.threshold_percentage:.1f}%",
            "timestamp": self.timestamp,
            "component": self.component,
            "age_seconds": self.age_seconds(),
        }


class IMonitorable(Protocol):
    """Interface for objects that can be memory monitored."""

    def get_memory_info(self) -> WidgetMemoryInfo:
        """Get memory usage information for this object."""
        ...

    def cleanup_memory(self) -> None:
        """Perform memory cleanup for this object."""
        ...


class IMemoryAlertHandler(ABC):
    """Interface for handling memory alerts."""

    @abstractmethod
    def handle_alert(self, alert: MemoryAlert) -> None:
        """Handle a memory usage alert."""
        pass


class DefaultAlertHandler(IMemoryAlertHandler):
    """Default memory alert handler that logs alerts."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def handle_alert(self, alert: MemoryAlert) -> None:
        """Log memory alert with appropriate level."""
        log_methods = {
            MemoryAlertLevel.INFO: self._logger.info,
            MemoryAlertLevel.WARNING: self._logger.warning,
            MemoryAlertLevel.CRITICAL: self._logger.error,
        }

        log_method = log_methods.get(alert.level, self._logger.info)
        log_method(
            f"Memory Alert [{alert.level.value.upper()}]: {alert.message} "
            f"(Usage: {alert.current_usage.percentage:.1f}%)"
        )


class MemoryThresholds:
    """Configurable memory thresholds for alerts."""

    def __init__(
        self,
        warning_percentage: float = 75.0,
        critical_percentage: float = 90.0,
        widget_warning_mb: float = 50.0,
        cache_warning_mb: float = 100.0,
    ):
        """
        Initialize memory thresholds.

        Args:
            warning_percentage: System memory warning threshold
            critical_percentage: System memory critical threshold
            widget_warning_mb: Individual widget memory warning (MB)
            cache_warning_mb: Cache memory warning threshold (MB)
        """
        self.warning_percentage = warning_percentage
        self.critical_percentage = critical_percentage
        self.widget_warning_mb = widget_warning_mb
        self.cache_warning_mb = cache_warning_mb

    def check_system_memory(self, usage: MemoryUsage) -> Optional[MemoryAlertLevel]:
        """Check if system memory usage exceeds thresholds."""
        if usage.percentage >= self.critical_percentage:
            return MemoryAlertLevel.CRITICAL
        elif usage.percentage >= self.warning_percentage:
            return MemoryAlertLevel.WARNING
        return None

    def check_widget_memory(
        self, widget_info: WidgetMemoryInfo
    ) -> Optional[MemoryAlertLevel]:
        """Check if widget memory usage exceeds thresholds."""
        mb_usage = widget_info.memory_bytes / (1024 * 1024)

        if mb_usage >= self.widget_warning_mb:
            return MemoryAlertLevel.WARNING
        return None


class MemoryMonitor:
    """
    Application memory monitor and optimizer.

    Tracks system and application memory usage, provides alerts when
    thresholds are exceeded, and coordinates memory optimization.

    Features:
    - System memory monitoring with configurable thresholds
    - Widget-level memory tracking
    - Cache memory monitoring
    - Automatic garbage collection optimization
    - Memory alert system with handlers
    - Memory usage statistics and reporting
    """

    def __init__(
        self,
        thresholds: Optional[MemoryThresholds] = None,
        alert_handler: Optional[IMemoryAlertHandler] = None,
        monitoring_interval: float = 30.0,
    ):
        """
        Initialize memory monitor.

        Args:
            thresholds: Memory thresholds configuration
            alert_handler: Handler for memory alerts
            monitoring_interval: Monitoring interval in seconds
        """
        self.thresholds = thresholds or MemoryThresholds()
        self.alert_handler = alert_handler or DefaultAlertHandler()
        self.monitoring_interval = monitoring_interval

        # State
        self._monitored_widgets: Dict[str, weakref.ReferenceType] = {}
        self._widget_memory_history: Dict[str, List[WidgetMemoryInfo]] = {}
        self._system_memory_history: List[MemoryUsage] = []
        self._alert_history: List[MemoryAlert] = []
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # Initialize tracemalloc if available
        if TRACEMALLOC_AVAILABLE:
            try:
                tracemalloc.start()
                self._logger.info("Memory tracing enabled")
            except RuntimeError:
                # Already started
                pass

    def register_widget(self, widget_id: str, widget: IMonitorable) -> None:
        """
        Register widget for memory monitoring.

        Args:
            widget_id: Unique widget identifier
            widget: Widget to monitor (using weak reference)
        """
        with self._lock:
            self._monitored_widgets[widget_id] = weakref.ref(widget)
            self._widget_memory_history[widget_id] = []
            self._logger.debug(f"Registered widget for monitoring: {widget_id}")

    def unregister_widget(self, widget_id: str) -> None:
        """
        Unregister widget from monitoring.

        Args:
            widget_id: Widget identifier to unregister
        """
        with self._lock:
            self._monitored_widgets.pop(widget_id, None)
            # Keep history for analysis but stop active monitoring
            self._logger.debug(f"Unregistered widget from monitoring: {widget_id}")

    def start_monitoring(self) -> None:
        """Start continuous memory monitoring."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, name="MemoryMonitor", daemon=True
        )
        self._monitor_thread.start()

        self._logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop continuous memory monitoring."""
        if not self._is_monitoring:
            return

        self._is_monitoring = False
        self._stop_event.set()

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            if self._monitor_thread.is_alive():
                self._logger.warning("Monitor thread did not stop gracefully")

        self._logger.info("Memory monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Check system memory
                self._check_system_memory()

                # Check widget memory
                self._check_widget_memory()

                # Cleanup old history
                self._cleanup_history()

            except Exception as e:
                self._logger.error(f"Monitoring loop error: {e}", exc_info=True)

            # Wait for next check
            self._stop_event.wait(self.monitoring_interval)

    def _check_system_memory(self) -> None:
        """Check system memory usage and generate alerts."""
        try:
            memory = psutil.virtual_memory()

            usage = MemoryUsage(
                total_bytes=memory.total,
                available_bytes=memory.available,
                used_bytes=memory.used,
                percentage=memory.percent,
            )

            with self._lock:
                self._system_memory_history.append(usage)

            # Check thresholds
            alert_level = self.thresholds.check_system_memory(usage)
            if alert_level:
                alert = MemoryAlert(
                    level=alert_level,
                    message=f"System memory usage high: {usage.percentage:.1f}%",
                    current_usage=usage,
                    threshold_percentage=(
                        self.thresholds.critical_percentage
                        if alert_level == MemoryAlertLevel.CRITICAL
                        else self.thresholds.warning_percentage
                    ),
                )

                self._handle_alert(alert)

        except Exception as e:
            self._logger.error(f"System memory check failed: {e}")

    def _check_widget_memory(self) -> None:
        """Check memory usage for all registered widgets."""
        with self._lock:
            widgets_to_remove = []

            for widget_id, widget_ref in self._monitored_widgets.items():
                widget = widget_ref()
                if widget is None:
                    # Widget was garbage collected
                    widgets_to_remove.append(widget_id)
                    continue

                try:
                    memory_info = widget.get_memory_info()
                    self._widget_memory_history[widget_id].append(memory_info)

                    # Check widget thresholds
                    alert_level = self.thresholds.check_widget_memory(memory_info)
                    if alert_level:
                        alert = MemoryAlert(
                            level=alert_level,
                            message=f"Widget memory usage high: {widget_id} "
                            f"({memory_info.format_memory()})",
                            current_usage=MemoryUsage(),  # System usage for context
                            threshold_percentage=0,  # Widget threshold is in MB
                            component=widget_id,
                        )
                        self._handle_alert(alert)

                except Exception as e:
                    self._logger.warning(f"Failed to check memory for {widget_id}: {e}")

            # Remove garbage collected widgets
            for widget_id in widgets_to_remove:
                self._monitored_widgets.pop(widget_id, None)

    def _handle_alert(self, alert: MemoryAlert) -> None:
        """Handle memory alert."""
        with self._lock:
            self._alert_history.append(alert)

        # Notify alert handler
        try:
            self.alert_handler.handle_alert(alert)
        except Exception as e:
            self._logger.error(f"Alert handler failed: {e}")

        # Auto-cleanup for critical alerts
        if alert.level == MemoryAlertLevel.CRITICAL:
            self.force_cleanup()

    def _cleanup_history(self) -> None:
        """Clean up old history data to prevent memory leaks."""
        max_history_age = 3600  # 1 hour
        current_time = time.time()

        with self._lock:
            # Clean system memory history
            self._system_memory_history = [
                usage
                for usage in self._system_memory_history
                if current_time - usage.last_updated < max_history_age
            ]

            # Clean widget memory history
            for widget_id in self._widget_memory_history:
                self._widget_memory_history[widget_id] = [
                    info
                    for info in self._widget_memory_history[widget_id]
                    if info.age_seconds() < max_history_age
                ]

            # Clean alert history
            self._alert_history = [
                alert
                for alert in self._alert_history
                if alert.age_seconds() < max_history_age
            ]

    def get_current_usage(self) -> MemoryUsage:
        """Get current system memory usage."""
        try:
            memory = psutil.virtual_memory()
            return MemoryUsage(
                total_bytes=memory.total,
                available_bytes=memory.available,
                used_bytes=memory.used,
                percentage=memory.percent,
            )
        except Exception as e:
            self._logger.error(f"Failed to get memory usage: {e}")
            return MemoryUsage()

    def get_widget_memory(self, widget_id: str) -> Optional[WidgetMemoryInfo]:
        """Get current memory info for specific widget."""
        with self._lock:
            widget_ref = self._monitored_widgets.get(widget_id)
            if not widget_ref:
                return None

            widget = widget_ref()
            if not widget:
                return None

            try:
                return widget.get_memory_info()
            except Exception as e:
                self._logger.warning(f"Failed to get widget memory {widget_id}: {e}")
                return None

    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report."""
        current_usage = self.get_current_usage()

        with self._lock:
            widget_info = {}
            for widget_id in self._monitored_widgets:
                memory_info = self.get_widget_memory(widget_id)
                if memory_info:
                    widget_info[widget_id] = {
                        "memory": memory_info.format_memory(),
                        "objects": memory_info.object_count,
                        "class": memory_info.widget_class,
                    }

            recent_alerts = [alert.to_dict() for alert in self._alert_history[-10:]]

        return {
            "system_memory": current_usage.to_dict(),
            "widgets": widget_info,
            "recent_alerts": recent_alerts,
            "monitoring_active": self._is_monitoring,
            "thresholds": {
                "warning_pct": self.thresholds.warning_percentage,
                "critical_pct": self.thresholds.critical_percentage,
                "widget_warning_mb": self.thresholds.widget_warning_mb,
            },
        }

    def force_cleanup(self) -> None:
        """Force garbage collection and cleanup operations."""
        self._logger.info("Forcing memory cleanup...")

        # Trigger garbage collection
        collected = gc.collect()
        self._logger.info(f"Garbage collection freed {collected} objects")

        # Ask all registered widgets to cleanup
        with self._lock:
            for widget_id, widget_ref in self._monitored_widgets.items():
                widget = widget_ref()
                if widget:
                    try:
                        widget.cleanup_memory()
                    except Exception as e:
                        self._logger.warning(f"Widget cleanup failed {widget_id}: {e}")

    def set_thresholds(self, thresholds: MemoryThresholds) -> None:
        """Update memory thresholds."""
        self.thresholds = thresholds
        self._logger.info("Memory thresholds updated")


# Global memory monitor instance
_global_memory_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """Get global memory monitor instance."""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor
