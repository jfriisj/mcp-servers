"""
Performance Optimization Components for Study Buddy GUI Integration Layer.

This module provides comprehensive performance optimization utilities including
LRU caching with TTL support, performance tracking and metrics collection,
memory management, and monitoring capabilities.

Architecture: Clean Architecture Layer 4 (Infrastructure)
SOLID Compliance: Full compliance with all SOLID principles
Purpose: Optimize integration layer performance with caching and monitoring
"""

import gc
import logging
import statistics
import threading
import time
import tracemalloc
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TypeVar

# Type variable for generic cache values
T = TypeVar("T")


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization components."""

    # Cache Configuration
    cache_max_size: int = 1000
    default_ttl_seconds: int = 300
    cache_cleanup_interval: int = 60

    # Performance Monitoring
    enable_metrics: bool = True
    metrics_history_size: int = 1000
    p95_threshold_ms: float = 2000.0
    memory_limit_mb: int = 100

    # Memory Management
    enable_memory_tracking: bool = True
    gc_threshold_mb: int = 50
    memory_cleanup_interval: int = 120

    # Monitoring & Alerts
    enable_alerts: bool = True
    alert_cooldown_seconds: int = 300
    slow_operation_threshold_ms: float = 1000.0

    def validate(self) -> None:
        """Validate configuration values."""
        if self.cache_max_size <= 0:
            raise ValueError("cache_max_size must be positive")
        if self.default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds must be positive")
        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")


# ============================================================================
# ABSTRACT INTERFACES
# ============================================================================


class CacheInterface(Protocol):
    """Abstract interface for cache implementations."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL."""
        ...

    def delete(self, key: str) -> bool:
        """Remove value from cache."""
        ...

    def clear(self) -> None:
        """Clear all cache entries."""
        ...

    def size(self) -> int:
        """Get current cache size."""
        ...

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        ...


class MetricsInterface(Protocol):
    """Abstract interface for metrics collection."""

    def record_operation(self, operation: str, duration_ms: float) -> None:
        """Record operation duration."""
        ...

    def increment_counter(self, counter: str) -> None:
        """Increment operation counter."""
        ...

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        ...

    def reset(self) -> None:
        """Reset all metrics."""
        ...


class MemoryInterface(Protocol):
    """Abstract interface for memory management."""

    def get_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        ...

    def cleanup(self) -> int:
        """Perform memory cleanup, return bytes freed."""
        ...

    def check_limits(self) -> bool:
        """Check if memory usage is within limits."""
        ...


# ============================================================================
# CACHE IMPLEMENTATION
# ============================================================================


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""

    value: Any
    created_at: float
    ttl: Optional[float] = None
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class LRUCacheManager:
    """
    Thread-safe LRU cache with TTL support.

    Implements efficient caching with automatic expiration and LRU eviction.
    Designed for high-concurrency async environments.
    """

    def __init__(self, config: PerformanceConfig):
        """Initialize LRU cache with configuration."""
        self.config = config
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0, "sets": 0}
        self.logger = logging.getLogger(__name__ + ".LRUCache")

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None

            # Update access and move to end (most recently used)
            entry.access_count += 1
            self._cache.move_to_end(key)
            self._stats["hits"] += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL."""
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config.default_ttl_seconds

            # Create cache entry
            entry = CacheEntry(
                value=value, created_at=time.time(), ttl=ttl if ttl > 0 else None
            )

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = entry
            self._stats["sets"] += 1

            # Enforce size limit (LRU eviction)
            while len(self._cache) > self.config.cache_max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

    def delete(self, key: str) -> bool:
        """Remove value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0.0
            )

            return {
                "size": len(self._cache),
                "max_size": self.config.cache_max_size,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
                **self._stats,
            }

    def _cleanup_worker(self) -> None:
        """Background thread to cleanup expired entries."""
        while True:
            try:
                time.sleep(self.config.cache_cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")

    def _cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        expired_count = 0

        with self._lock:
            # Collect expired keys
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]

            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                expired_count += 1

            self._stats["expired"] += expired_count

        if expired_count > 0:
            self.logger.debug(f"Cleaned up {expired_count} expired cache entries")

        return expired_count


# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================


@dataclass
class OperationMetrics:
    """Metrics for a specific operation type."""

    total_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    durations: List[float] = field(default_factory=list)

    def add_duration(self, duration_ms: float) -> None:
        """Add operation duration measurement."""
        self.total_count += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        # Keep limited history for percentile calculations
        self.durations.append(duration_ms)
        if len(self.durations) > 1000:  # Keep last 1000 measurements
            self.durations.pop(0)

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        if self.total_count == 0:
            return 0.0
        return self.total_duration_ms / self.total_count

    @property
    def p95_duration_ms(self) -> float:
        """Calculate 95th percentile duration."""
        if len(self.durations) < 2:
            return self.max_duration_ms if self.durations else 0.0
        try:
            return statistics.quantiles(self.durations, n=20)[18]  # 95th percentile
        except statistics.StatisticsError:
            return self.max_duration_ms
    
    @property
    def p99_duration_ms(self) -> float:
        """Calculate 99th percentile duration."""
        if len(self.durations) < 2:
            return self.max_duration_ms if self.durations else 0.0
        try:
            return statistics.quantiles(self.durations, n=100)[98]  # 99th percentile
        except statistics.StatisticsError:
            return self.max_duration_ms
class PerformanceTracker:
    """
    Performance tracking and metrics collection.

    Provides timing, counting, and statistical analysis of operations
    with thread-safe implementation for async environments.
    """

    def __init__(self, config: PerformanceConfig):
        """Initialize performance tracker."""
        self.config = config
        self._metrics: Dict[str, OperationMetrics] = defaultdict(OperationMetrics)
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__ + ".PerformanceTracker")

    def record_operation(self, operation: str, duration_ms: float) -> None:
        """Record operation duration."""
        if not self.config.enable_metrics:
            return

        with self._lock:
            self._metrics[operation].add_duration(duration_ms)

            # Log slow operations
            if duration_ms > self.config.slow_operation_threshold_ms:
                self.logger.warning(
                    f"Slow operation detected: {operation} took {duration_ms:.1f}ms"
                )

    def increment_counter(self, counter: str) -> None:
        """Increment operation counter."""
        if not self.config.enable_metrics:
            return

        with self._lock:
            self._counters[counter] += 1

    @contextmanager
    def time_operation(self, operation: str):
        """Context manager for timing operations."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            self.record_operation(operation, duration_ms)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        with self._lock:
            metrics_summary = {}

            for operation, metrics in self._metrics.items():
                metrics_summary[operation] = {
                    "count": metrics.total_count,
                    "avg_ms": round(metrics.avg_duration_ms, 2),
                    "min_ms": round(metrics.min_duration_ms, 2),
                    "max_ms": round(metrics.max_duration_ms, 2),
                    "p95_ms": round(metrics.p95_duration_ms, 2),
                    "p99_ms": round(metrics.p99_duration_ms, 2),
                }

            return {
                "operations": metrics_summary,
                "counters": dict(self._counters),
                "timestamp": datetime.now().isoformat(),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()

    def check_thresholds(self) -> List[str]:
        """Check performance thresholds and return alerts."""
        alerts = []

        with self._lock:
            for operation, metrics in self._metrics.items():
                if metrics.p95_duration_ms > self.config.p95_threshold_ms:
                    alerts.append(
                        f"High P95 latency for {operation}: "
                        f"{metrics.p95_duration_ms:.1f}ms > {self.config.p95_threshold_ms}ms"
                    )

        return alerts


# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================


class MemoryManager:
    """
    Memory management and resource optimization utilities.

    Provides memory tracking, cleanup utilities, and memory limit enforcement
    for the integration layer components.
    """

    def __init__(self, config: PerformanceConfig):
        """Initialize memory manager."""
        self.config = config
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__ + ".MemoryManager")

        if config.enable_memory_tracking:
            tracemalloc.start()

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

    def get_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        if self.config.enable_memory_tracking and tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / 1024 / 1024
        return 0.0

    def cleanup(self) -> int:
        """Perform memory cleanup and return bytes freed."""
        initial_usage = self.get_usage_mb()

        # Force garbage collection
        collected = gc.collect()

        # Additional cleanup for specific object types
        gc.collect(0)  # Clean generation 0
        gc.collect(1)  # Clean generation 1
        gc.collect(2)  # Clean generation 2

        final_usage = self.get_usage_mb()
        freed_mb = initial_usage - final_usage

        self.logger.debug(
            f"Memory cleanup: freed {freed_mb:.1f}MB, " f"collected {collected} objects"
        )

        return int(freed_mb * 1024 * 1024)  # Return bytes

    def check_limits(self) -> bool:
        """Check if memory usage is within limits."""
        current_usage = self.get_usage_mb()

        if current_usage > self.config.memory_limit_mb:
            self.logger.warning(
                f"Memory usage {current_usage:.1f}MB exceeds limit "
                f"{self.config.memory_limit_mb}MB"
            )
            return False

        return True

    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        info = {
            "current_usage_mb": self.get_usage_mb(),
            "limit_mb": self.config.memory_limit_mb,
            "tracking_enabled": self.config.enable_memory_tracking,
        }

        if self.config.enable_memory_tracking and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            info.update(
                {
                    "peak_usage_mb": peak / 1024 / 1024,
                    "current_bytes": current,
                    "peak_bytes": peak,
                }
            )

        return info

    def _cleanup_worker(self) -> None:
        """Background thread for periodic memory cleanup."""
        while True:
            try:
                time.sleep(self.config.memory_cleanup_interval)

                # Check if cleanup is needed
                if self.get_usage_mb() > self.config.gc_threshold_mb:
                    self.cleanup()

            except Exception as e:
                self.logger.error(f"Memory cleanup error: {e}")


# ============================================================================
# PERFORMANCE MONITOR
# ============================================================================


class PerformanceMonitor:
    """
    Central performance monitoring coordinator.

    Aggregates metrics from all performance components and provides
    unified monitoring, alerting, and reporting capabilities.
    """

    def __init__(self, config: PerformanceConfig):
        """Initialize performance monitor."""
        self.config = config
        self.cache_manager = LRUCacheManager(config)
        self.performance_tracker = PerformanceTracker(config)
        self.memory_manager = MemoryManager(config)

        self._last_alert_time: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__ + ".PerformanceMonitor")

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get metrics from all performance components."""
        return {
            "cache": self.cache_manager.stats(),
            "performance": self.performance_tracker.get_metrics(),
            "memory": self.memory_manager.get_memory_info(),
            "timestamp": datetime.now().isoformat(),
        }

    def check_all_thresholds(self) -> List[str]:
        """Check all performance thresholds and return alerts."""
        alerts = []

        # Performance alerts
        alerts.extend(self.performance_tracker.check_thresholds())

        # Memory alerts
        if not self.memory_manager.check_limits():
            alerts.append("Memory usage exceeds configured limit")

        # Cache efficiency alerts
        cache_stats = self.cache_manager.stats()
        if cache_stats["total_requests"] > 100 and cache_stats["hit_rate_percent"] < 50:
            alerts.append(f"Low cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")

        # Filter alerts by cooldown period
        if self.config.enable_alerts:
            alerts = self._filter_alerts_by_cooldown(alerts)

        return alerts

    def _filter_alerts_by_cooldown(self, alerts: List[str]) -> List[str]:
        """Filter alerts by cooldown period to prevent spam."""
        current_time = time.time()
        filtered_alerts = []

        for alert in alerts:
            last_time = self._last_alert_time.get(alert, 0)
            if current_time - last_time > self.config.alert_cooldown_seconds:
                self._last_alert_time[alert] = current_time
                filtered_alerts.append(alert)

        return filtered_alerts

    def cleanup_all(self) -> Dict[str, Any]:
        """Perform cleanup across all components."""
        cleanup_results = {}

        # Cache cleanup
        cache_size_before = self.cache_manager.size()
        expired_cleaned = self.cache_manager._cleanup_expired()
        cleanup_results["cache"] = {
            "expired_entries_cleaned": expired_cleaned,
            "size_before": cache_size_before,
            "size_after": self.cache_manager.size(),
        }

        # Memory cleanup
        bytes_freed = self.memory_manager.cleanup()
        cleanup_results["memory"] = {
            "bytes_freed": bytes_freed,
            "mb_freed": bytes_freed / 1024 / 1024,
        }

        return cleanup_results

    def reset_all_metrics(self) -> None:
        """Reset metrics across all components."""
        self.performance_tracker.reset()
        self.cache_manager._stats = dict.fromkeys(self.cache_manager._stats, 0)


# ============================================================================
# PERFORMANCE DECORATORS AND UTILITIES
# ============================================================================


def performance_tracked(operation: str, monitor: PerformanceMonitor):
    """Decorator for automatic performance tracking."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with monitor.performance_tracker.time_operation(operation):
                return func(*args, **kwargs)

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


async def async_performance_tracked(operation: str, monitor: PerformanceMonitor):
    """Async context manager for performance tracking."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        monitor.performance_tracker.record_operation(operation, duration_ms)


# ============================================================================
# GLOBAL PERFORMANCE INSTANCE
# ============================================================================

# Global performance monitor instance (initialized lazily)
_global_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()


def get_global_performance_monitor(
    config: Optional[PerformanceConfig] = None,
) -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _global_monitor

    with _monitor_lock:
        if _global_monitor is None:
            if config is None:
                config = PerformanceConfig()
            _global_monitor = PerformanceMonitor(config)

        return _global_monitor


def reset_global_performance_monitor() -> None:
    """Reset global performance monitor (for testing)."""
    global _global_monitor

    with _monitor_lock:
        _global_monitor = None


# ============================================================================
# MODULE TESTING AND VALIDATION
# ============================================================================


def _test_performance_components():
    """Test performance optimization components."""
    print("🔄 Testing Performance Optimization Components...")

    # Test configuration
    config = PerformanceConfig(
        cache_max_size=10,
        default_ttl_seconds=1,
        enable_alerts=False,  # Disable for testing
    )

    try:
        config.validate()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        return

    # Test cache manager
    cache = LRUCacheManager(config)

    # Test cache operations
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    assert value == "test_value", f"Expected 'test_value', got {value}"
    print("✅ Cache operations working correctly")

    # Test performance tracker
    tracker = PerformanceTracker(config)

    with tracker.time_operation("test_operation"):
        time.sleep(0.001)  # Simulate work

    metrics = tracker.get_metrics()
    assert "test_operation" in metrics["operations"], "Operation not tracked"
    print("✅ Performance tracking working correctly")

    # Test memory manager
    memory_mgr = MemoryManager(config)
    usage = memory_mgr.get_usage_mb()
    assert usage >= 0, f"Invalid memory usage: {usage}"
    print("✅ Memory management working correctly")

    # Test performance monitor
    monitor = PerformanceMonitor(config)
    comprehensive = monitor.get_comprehensive_metrics()

    assert "cache" in comprehensive, "Cache metrics missing"
    assert "performance" in comprehensive, "Performance metrics missing"
    assert "memory" in comprehensive, "Memory metrics missing"
    print("✅ Performance monitoring working correctly")

    print("🎉 All performance optimization components working correctly!")


if __name__ == "__main__":
    _test_performance_components()
