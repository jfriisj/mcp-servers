"""
Study Buddy GUI - Graceful Degradation System

Provides graceful degradation when MCP server unavailable, offline mode detection,
cached data fallbacks, and connection retry strategies.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, State Pattern, Circuit Breaker Pattern
SOLID: SRP (degradation management), OCP (extensible fallbacks), DIP (abstraction-based)
"""

import asyncio
import json
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from gui.error_handling.debug_logger import get_debug_logger
from gui.error_handling.error_tracker import (
    ErrorCategory,
    ErrorSeverity,
    get_error_tracker,
)


class DegradationMode(Enum):
    """Application degradation modes."""

    NORMAL = "normal"  # Full functionality available
    REDUCED = "reduced"  # Limited functionality
    OFFLINE = "offline"  # Offline mode with cached data
    EMERGENCY = "emergency"  # Minimal functionality only


class ConnectionState(Enum):
    """MCP server connection states."""

    CONNECTED = "connected"  # Successfully connected
    DISCONNECTED = "disconnected"  # No connection
    CONNECTING = "connecting"  # Attempting to connect
    RETRYING = "retrying"  # Retrying after failure
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker opened


@dataclass
class FallbackData:
    """Cached data for offline fallback."""

    key: str
    data: Any
    timestamp: datetime
    ttl_hours: int = 24

    @property
    def is_expired(self) -> bool:
        """Check if cached data is expired."""
        expiry = self.timestamp + timedelta(hours=self.ttl_hours)
        return datetime.now(timezone.utc) > expiry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "ttl_hours": self.ttl_hours,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackData":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl_hours=data["ttl_hours"],
        )


class IFallbackStrategy(ABC):
    """Interface for fallback strategies."""

    @abstractmethod
    async def get_fallback_data(self, operation: str, **context) -> Optional[Any]:
        """Get fallback data for operation."""
        pass

    @abstractmethod
    def can_handle_operation(self, operation: str) -> bool:
        """Check if strategy can handle operation."""
        pass


class CachedDataFallback(IFallbackStrategy):
    """Fallback using cached data from previous successful operations."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".study_buddy" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._memory_cache: Dict[str, FallbackData] = {}
        self._lock = threading.RLock()

        # Load existing cache
        self._load_cache()

    def store_data(self, key: str, data: Any, ttl_hours: int = 24) -> None:
        """Store data for future fallback."""
        with self._lock:
            fallback_data = FallbackData(
                key=key,
                data=data,
                timestamp=datetime.now(timezone.utc),
                ttl_hours=ttl_hours,
            )

            self._memory_cache[key] = fallback_data
            self._persist_cache()

    async def get_fallback_data(self, operation: str, **context) -> Optional[Any]:
        """Get cached data for operation."""
        with self._lock:
            # Create cache key from operation and context
            key = self._create_cache_key(operation, **context)

            fallback_data = self._memory_cache.get(key)
            if fallback_data and not fallback_data.is_expired:
                return fallback_data.data

            return None

    def can_handle_operation(self, operation: str) -> bool:
        """Check if we have cached data for operation."""
        # For simplicity, assume we can handle any operation that we have cached
        return True

    def _create_cache_key(self, operation: str, **context) -> str:
        """Create cache key from operation and context."""
        # Create deterministic key from operation and sorted context
        context_str = "_".join(
            f"{k}={v}" for k, v in sorted(context.items()) if v is not None
        )
        return f"{operation}_{context_str}" if context_str else operation

    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "fallback_cache.json"
        try:
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                for item_data in cache_data.get("items", []):
                    fallback_data = FallbackData.from_dict(item_data)
                    if not fallback_data.is_expired:
                        self._memory_cache[fallback_data.key] = fallback_data
        except Exception:
            # Don't fail if cache loading fails
            pass

    def _persist_cache(self) -> None:
        """Persist cache to disk."""
        cache_file = self.cache_dir / "fallback_cache.json"
        try:
            # Remove expired items
            valid_items = [
                data.to_dict()
                for data in self._memory_cache.values()
                if not data.is_expired
            ]

            cache_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "items": valid_items,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            # Don't fail if cache persistence fails
            pass


class StaticDataFallback(IFallbackStrategy):
    """Fallback using static default data."""

    def __init__(self):
        self._static_data = {
            "list_documents": {
                "success": True,
                "documents": [],
                "total": 0,
                "message": "No documents available in offline mode",
            },
            "get_document": {
                "success": False,
                "error": "Document not available in offline mode",
            },
            "search_documents": {
                "success": True,
                "results": [],
                "total_results": 0,
                "message": "Search not available in offline mode",
            },
        }

    async def get_fallback_data(self, operation: str, **context) -> Optional[Any]:
        """Get static fallback data."""
        return self._static_data.get(operation)

    def can_handle_operation(self, operation: str) -> bool:
        """Check if operation has static fallback."""
        return operation in self._static_data


@dataclass
class RetryConfig:
    """Configuration for connection retry strategy."""

    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_factor: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_seconds: float = 300.0  # 5 minutes


class CircuitBreaker:
    """Circuit breaker for connection failures."""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = ConnectionState.DISCONNECTED
        self._lock = threading.Lock()

    def can_attempt_connection(self) -> bool:
        """Check if connection attempt is allowed."""
        with self._lock:
            if self.state != ConnectionState.CIRCUIT_OPEN:
                return True

            # Check if circuit breaker timeout has elapsed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time
                >= self.config.circuit_breaker_timeout_seconds
            ):
                # Reset circuit breaker
                self.failure_count = 0
                self.state = ConnectionState.DISCONNECTED
                return True

            return False

    def record_success(self) -> None:
        """Record successful connection."""
        with self._lock:
            self.failure_count = 0
            self.state = ConnectionState.CONNECTED
            self.last_failure_time = None

    def record_failure(self) -> None:
        """Record connection failure."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.config.circuit_breaker_threshold:
                self.state = ConnectionState.CIRCUIT_OPEN
            else:
                self.state = ConnectionState.DISCONNECTED


class GracefulDegradationManager:
    """
    Central manager for graceful degradation.

    Responsibilities:
    - Monitor MCP server connection status
    - Switch between degradation modes
    - Coordinate fallback strategies
    - Manage connection retry logic
    - Provide offline mode functionality
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._current_mode = DegradationMode.NORMAL
        self._connection_state = ConnectionState.DISCONNECTED

        # Fallback strategies
        self._fallback_strategies: List[IFallbackStrategy] = []
        self._setup_default_fallbacks()

        # Circuit breaker
        self._circuit_breaker = CircuitBreaker(self.config)

        # Connection monitoring
        self._last_successful_connection = None
        self._connection_check_task = None

        # Observers
        self._mode_change_callbacks: List[Callable[[DegradationMode], None]] = []

        # Logging
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()

        self._lock = threading.RLock()

    def _setup_default_fallbacks(self) -> None:
        """Setup default fallback strategies."""
        self.add_fallback_strategy(CachedDataFallback())
        self.add_fallback_strategy(StaticDataFallback())

    def add_fallback_strategy(self, strategy: IFallbackStrategy) -> None:
        """Add fallback strategy."""
        with self._lock:
            if strategy not in self._fallback_strategies:
                self._fallback_strategies.append(strategy)

    def remove_fallback_strategy(self, strategy: IFallbackStrategy) -> None:
        """Remove fallback strategy."""
        with self._lock:
            if strategy in self._fallback_strategies:
                self._fallback_strategies.remove(strategy)

    def add_mode_change_callback(
        self, callback: Callable[[DegradationMode], None]
    ) -> None:
        """Add callback for mode changes."""
        with self._lock:
            if callback not in self._mode_change_callbacks:
                self._mode_change_callbacks.append(callback)

    def set_degradation_mode(self, mode: DegradationMode) -> None:
        """Set degradation mode and notify observers."""
        with self._lock:
            if mode != self._current_mode:
                old_mode = self._current_mode
                self._current_mode = mode

                self._logger.info(
                    f"Degradation mode changed: {old_mode.value} -> {mode.value}",
                    old_mode=old_mode.value,
                    new_mode=mode.value,
                    connection_state=self._connection_state.value,
                )

                # Notify observers
                for callback in self._mode_change_callbacks:
                    try:
                        callback(mode)
                    except Exception as e:
                        self._logger.error(f"Mode change callback failed: {e}")

    def get_current_mode(self) -> DegradationMode:
        """Get current degradation mode."""
        return self._current_mode

    def get_connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._connection_state

    def record_connection_success(self) -> None:
        """Record successful MCP server connection."""
        with self._lock:
            self._connection_state = ConnectionState.CONNECTED
            self._last_successful_connection = datetime.now(timezone.utc)
            self._circuit_breaker.record_success()

            # Return to normal mode if we were degraded
            if self._current_mode != DegradationMode.NORMAL:
                self.set_degradation_mode(DegradationMode.NORMAL)

            self._logger.info("MCP server connection restored")

    def record_connection_failure(self, error: Exception) -> None:
        """Record MCP server connection failure."""
        with self._lock:
            self._connection_state = ConnectionState.DISCONNECTED
            self._circuit_breaker.record_failure()

            # Determine degradation mode based on failure count and time
            time_since_last_success = None
            if self._last_successful_connection:
                time_since_last_success = (
                    datetime.now(timezone.utc) - self._last_successful_connection
                )

            if self._circuit_breaker.state == ConnectionState.CIRCUIT_OPEN:
                # Circuit breaker opened - go to offline mode
                self.set_degradation_mode(DegradationMode.OFFLINE)
            elif (
                time_since_last_success
                and time_since_last_success.total_seconds() > 300
            ):  # 5 minutes
                # Long disconnection - reduced mode
                self.set_degradation_mode(DegradationMode.REDUCED)
            else:
                # Short disconnection - try to maintain normal mode briefly
                pass

            # Track error
            self._error_tracker.capture_error(
                exception=error,
                severity=ErrorSeverity.HIGH
                if self._current_mode == DegradationMode.OFFLINE
                else ErrorSeverity.MEDIUM,
                category=ErrorCategory.NETWORK,
                user_action="MCP server communication",
                operation_context={
                    "connection_state": self._connection_state.value,
                    "degradation_mode": self._current_mode.value,
                    "failure_count": self._circuit_breaker.failure_count,
                    "time_since_last_success": time_since_last_success.total_seconds()
                    if time_since_last_success
                    else None,
                },
            )

            self._logger.error(
                f"MCP server connection failed: {error}",
                error_type=type(error).__name__,
                failure_count=self._circuit_breaker.failure_count,
                degradation_mode=self._current_mode.value,
            )

    async def get_fallback_data(self, operation: str, **context) -> Optional[Any]:
        """
        Get fallback data for operation.

        Args:
            operation: MCP operation name
            **context: Operation context

        Returns:
            Fallback data or None if not available
        """
        if self._current_mode == DegradationMode.NORMAL:
            return None  # No fallback needed in normal mode

        # Try fallback strategies in order
        for strategy in self._fallback_strategies:
            if strategy.can_handle_operation(operation):
                try:
                    fallback_data = await strategy.get_fallback_data(
                        operation, **context
                    )
                    if fallback_data is not None:
                        self._logger.debug(
                            f"Using fallback data for operation: {operation}",
                            operation=operation,
                            strategy=type(strategy).__name__,
                            degradation_mode=self._current_mode.value,
                        )
                        return fallback_data
                except Exception as e:
                    self._logger.warning(f"Fallback strategy failed: {e}")

        return None

    def store_successful_operation_data(
        self, operation: str, data: Any, **context
    ) -> None:
        """Store data from successful operation for future fallback."""
        # Store in cached data fallback
        for strategy in self._fallback_strategies:
            if isinstance(strategy, CachedDataFallback):
                key = f"{operation}_{hash(str(sorted(context.items())))}"
                strategy.store_data(key, data)
                break

    async def attempt_connection_recovery(self) -> bool:
        """
        Attempt to recover MCP server connection.

        Returns:
            True if connection recovered, False otherwise
        """
        if not self._circuit_breaker.can_attempt_connection():
            return False

        self._connection_state = ConnectionState.CONNECTING

        try:
            # This would be implemented by the MCP client
            # For now, we just simulate a connection attempt
            await asyncio.sleep(0.1)

            # In real implementation, this would test MCP server connection
            # success = await self._test_mcp_connection()
            success = False  # Placeholder

            if success:
                self.record_connection_success()
                return True
            else:
                raise ConnectionError("Connection test failed")

        except Exception as e:
            self.record_connection_failure(e)
            return False

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary."""
        with self._lock:
            return {
                "degradation_mode": self._current_mode.value,
                "connection_state": self._connection_state.value,
                "circuit_breaker_failures": self._circuit_breaker.failure_count,
                "circuit_breaker_open": self._circuit_breaker.state
                == ConnectionState.CIRCUIT_OPEN,
                "last_successful_connection": (
                    self._last_successful_connection.isoformat()
                    if self._last_successful_connection
                    else None
                ),
                "fallback_strategies_count": len(self._fallback_strategies),
                "mode_change_callbacks_count": len(self._mode_change_callbacks),
            }

    def force_offline_mode(self) -> None:
        """Force application into offline mode."""
        with self._lock:
            self.set_degradation_mode(DegradationMode.OFFLINE)
            self._connection_state = ConnectionState.DISCONNECTED
            self._logger.info("Forced offline mode activated")

    def force_normal_mode(self) -> None:
        """Force application back to normal mode (override degradation)."""
        with self._lock:
            self.set_degradation_mode(DegradationMode.NORMAL)
            self._connection_state = ConnectionState.CONNECTED
            self._circuit_breaker.record_success()
            self._logger.info("Forced normal mode activated")


# Global degradation manager instance
_degradation_manager: Optional[GracefulDegradationManager] = None
_degradation_manager_lock = threading.Lock()


def get_degradation_manager() -> GracefulDegradationManager:
    """
    Get global degradation manager instance (singleton pattern).

    Returns:
        GracefulDegradationManager instance
    """
    global _degradation_manager

    if _degradation_manager is None:
        with _degradation_manager_lock:
            if _degradation_manager is None:
                _degradation_manager = GracefulDegradationManager()

    return _degradation_manager


# Convenience functions
def get_current_mode() -> DegradationMode:
    """Get current degradation mode."""
    manager = get_degradation_manager()
    return manager.get_current_mode()


def is_offline_mode() -> bool:
    """Check if application is in offline mode."""
    return get_current_mode() == DegradationMode.OFFLINE


def record_mcp_success() -> None:
    """Record successful MCP operation."""
    manager = get_degradation_manager()
    manager.record_connection_success()


def record_mcp_failure(error: Exception) -> None:
    """Record failed MCP operation."""
    manager = get_degradation_manager()
    manager.record_connection_failure(error)


async def get_fallback_data(operation: str, **context) -> Optional[Any]:
    """Get fallback data for MCP operation."""
    manager = get_degradation_manager()
    return await manager.get_fallback_data(operation, **context)


def store_operation_data(operation: str, data: Any, **context) -> None:
    """Store successful operation data for fallback."""
    manager = get_degradation_manager()
    manager.store_successful_operation_data(operation, data, **context)
