"""
Study Buddy GUI - Async Operation Queue

Manages asynchronous MCP operations with priority queuing, progress tracking,
and cancellation support for optimal user experience.

Architecture: Clean Architecture Layer 4 (Infrastructure)  
Patterns: Queue Pattern, Priority Pattern, Observer Pattern
SOLID: SRP (queue management only), OCP (extensible priorities), DIP (abstraction-based)
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar
from uuid import uuid4

T = TypeVar("T")


class OperationPriority(Enum):
    """Priority levels for async operations."""

    URGENT = 0  # User-initiated operations (clicks, selections)
    HIGH = 10  # Content loading for current view
    NORMAL = 20  # Background loading
    LOW = 30  # Preemptive/cache loading
    IDLE = 40  # Cleanup and maintenance


class OperationStatus(Enum):
    """Status of async operations."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationProgress:
    """Progress information for an operation."""

    current: int = 0
    total: int = 100
    message: str = ""

    @property
    def percentage(self) -> float:
        """Get completion percentage (0-100)."""
        if self.total == 0:
            return 100.0
        return min(100.0, (self.current / self.total) * 100.0)

    @property
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.current >= self.total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "message": self.message,
            "is_complete": self.is_complete,
        }


@dataclass
class QueuedOperation:
    """Represents an operation in the queue."""

    operation_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    priority: OperationPriority = OperationPriority.NORMAL
    coroutine: Optional[Coroutine] = None
    callback: Optional[Callable[[Any], None]] = None
    error_callback: Optional[Callable[[Exception], None]] = None
    progress_callback: Optional[Callable[[OperationProgress], None]] = None

    # Metadata
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: OperationStatus = OperationStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[Exception] = None

    # Execution control
    cancellation_token: Optional[asyncio.Event] = None
    timeout: Optional[float] = None

    def __post_init__(self):
        """Initialize cancellation token."""
        if self.cancellation_token is None:
            self.cancellation_token = asyncio.Event()

    @property
    def age_seconds(self) -> float:
        """Get age of operation in seconds."""
        return time.time() - self.created_at

    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.started_at is None:
            return None

        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    def cancel(self) -> None:
        """Cancel the operation."""
        if self.cancellation_token:
            self.cancellation_token.set()
        self.status = OperationStatus.CANCELLED

    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self.status == OperationStatus.CANCELLED or (
            self.cancellation_token is not None and self.cancellation_token.is_set()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring/logging."""
        return {
            "operation_id": self.operation_id,
            "name": self.name,
            "priority": self.priority.value,
            "status": self.status.value,
            "age_seconds": self.age_seconds,
            "execution_time": self.execution_time,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "has_error": self.error is not None,
            "error_message": str(self.error) if self.error else None,
        }


class IOperationMonitor(ABC):
    """Interface for monitoring operation execution."""

    @abstractmethod
    def on_operation_started(self, operation: QueuedOperation) -> None:
        """Called when operation starts execution."""
        pass

    @abstractmethod
    def on_operation_completed(self, operation: QueuedOperation) -> None:
        """Called when operation completes successfully."""
        pass

    @abstractmethod
    def on_operation_failed(self, operation: QueuedOperation) -> None:
        """Called when operation fails."""
        pass

    @abstractmethod
    def on_operation_cancelled(self, operation: QueuedOperation) -> None:
        """Called when operation is cancelled."""
        pass

    @abstractmethod
    def on_queue_status_changed(self, queue_size: int, active_operations: int) -> None:
        """Called when queue status changes."""
        pass


class DefaultOperationMonitor(IOperationMonitor):
    """Default operation monitor that logs events."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def on_operation_started(self, operation: QueuedOperation) -> None:
        """Log operation start."""
        self._logger.debug(
            f"Operation started: {operation.name} ({operation.operation_id})"
        )

    def on_operation_completed(self, operation: QueuedOperation) -> None:
        """Log operation completion."""
        exec_time = operation.execution_time or 0
        self._logger.debug(
            f"Operation completed: {operation.name} "
            f"in {exec_time:.2f}s ({operation.operation_id})"
        )

    def on_operation_failed(self, operation: QueuedOperation) -> None:
        """Log operation failure."""
        self._logger.warning(
            f"Operation failed: {operation.name} - {operation.error} "
            f"({operation.operation_id})"
        )

    def on_operation_cancelled(self, operation: QueuedOperation) -> None:
        """Log operation cancellation."""
        self._logger.debug(
            f"Operation cancelled: {operation.name} ({operation.operation_id})"
        )

    def on_queue_status_changed(self, queue_size: int, active_operations: int) -> None:
        """Log queue status changes."""
        if queue_size > 10 or active_operations > 5:  # Only log when busy
            self._logger.info(
                f"Queue status: {queue_size} queued, "
                f"{active_operations} active operations"
            )


class AsyncOperationQueue:
    """
    Priority-based async operation queue manager.

    Provides controlled execution of MCP operations with:
    - Priority-based scheduling (urgent operations execute first)
    - Concurrency limits to prevent overwhelming MCP server
    - Progress tracking and monitoring
    - Cancellation support for responsive UI
    - Operation timeout handling
    - Comprehensive logging and statistics
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        monitor: Optional[IOperationMonitor] = None,
        default_timeout: float = 30.0,
    ):
        """
        Initialize operation queue.

        Args:
            max_concurrent: Maximum concurrent operations
            monitor: Operation execution monitor
            default_timeout: Default operation timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.monitor = monitor or DefaultOperationMonitor()
        self.default_timeout = default_timeout

        # Queue and execution state
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._operations: Dict[str, QueuedOperation] = {}
        self._active_operations: Dict[str, asyncio.Task] = {}
        self._completed_operations: List[QueuedOperation] = []

        # Control
        self._is_running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        self._queue_lock = asyncio.Lock()

        # Statistics
        self._stats = {
            "total_queued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
        }

        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the operation queue workers."""
        if self._is_running:
            return

        self._is_running = True
        self._shutdown_event.clear()

        # Start worker tasks
        self._worker_tasks = [
            asyncio.create_task(self._worker(f"worker_{i}"))
            for i in range(self.max_concurrent)
        ]

        self._logger.info(f"Operation queue started with {self.max_concurrent} workers")

    async def stop(self) -> None:
        """Stop the operation queue and cancel all operations."""
        if not self._is_running:
            return

        self._is_running = False
        self._shutdown_event.set()

        # Cancel all queued operations
        await self.cancel_all_operations()

        # Cancel worker tasks
        for task in self._worker_tasks:
            if not task.done():
                task.cancel()

        # Wait for workers to finish
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()
        self._logger.info("Operation queue stopped")

    async def queue_operation(
        self,
        coroutine: Coroutine[Any, Any, T],
        name: str,
        priority: OperationPriority = OperationPriority.NORMAL,
        callback: Optional[Callable[[T], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None,
        timeout: Optional[float] = None,
    ) -> QueuedOperation:
        """
        Queue an async operation for execution.

        Args:
            coroutine: Async function to execute
            name: Human-readable operation name
            priority: Operation priority
            callback: Success callback
            error_callback: Error callback
            progress_callback: Progress update callback
            timeout: Operation timeout (uses default if None)

        Returns:
            QueuedOperation object for monitoring
        """
        if not self._is_running:
            raise RuntimeError("Queue is not running. Call start() first.")

        operation = QueuedOperation(
            name=name,
            priority=priority,
            coroutine=coroutine,
            callback=callback,
            error_callback=error_callback,
            progress_callback=progress_callback,
            timeout=timeout or self.default_timeout,
        )

        async with self._queue_lock:
            self._operations[operation.operation_id] = operation
            # Priority queue uses tuple: (priority_value, operation)
            await self._queue.put((priority.value, operation))
            self._stats["total_queued"] += 1

        self._logger.debug(
            f"Queued operation: {name} "
            f"(priority={priority.value}, id={operation.operation_id})"
        )

        # Notify monitor
        await self._notify_queue_status_changed()

        return operation

    async def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel a specific operation.

        Args:
            operation_id: ID of operation to cancel

        Returns:
            True if operation was cancelled, False if not found
        """
        async with self._queue_lock:
            operation = self._operations.get(operation_id)
            if not operation:
                return False

            # Cancel the operation
            operation.cancel()

            # Cancel running task if exists
            if operation_id in self._active_operations:
                task = self._active_operations[operation_id]
                if not task.done():
                    task.cancel()

            self._stats["total_cancelled"] += 1
            self._logger.debug(
                f"Cancelled operation: {operation.name} ({operation_id})"
            )

            # Notify monitor
            self.monitor.on_operation_cancelled(operation)
            await self._notify_queue_status_changed()

            return True

    async def cancel_all_operations(self) -> int:
        """
        Cancel all queued and active operations.

        Returns:
            Number of operations cancelled
        """
        async with self._queue_lock:
            cancelled_count = 0

            # Cancel all operations in our tracking dict
            for operation in self._operations.values():
                if operation.status in [
                    OperationStatus.QUEUED,
                    OperationStatus.RUNNING,
                ]:
                    operation.cancel()
                    cancelled_count += 1

            # Cancel all active tasks
            for task in self._active_operations.values():
                if not task.done():
                    task.cancel()

            self._stats["total_cancelled"] += cancelled_count
            self._logger.info(f"Cancelled {cancelled_count} operations")

            await self._notify_queue_status_changed()
            return cancelled_count

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes queued operations."""
        self._logger.debug(f"Worker {worker_name} started")

        try:
            while self._is_running and not self._shutdown_event.is_set():
                try:
                    # Wait for next operation with timeout
                    try:
                        _, operation = await asyncio.wait_for(
                            self._queue.get(),
                            timeout=1.0,  # Check shutdown periodically
                        )
                    except asyncio.TimeoutError:
                        continue  # Check shutdown and retry

                    # Skip cancelled operations
                    if operation.is_cancelled():
                        self._queue.task_done()
                        continue

                    # Execute the operation
                    await self._execute_operation(operation, worker_name)
                    self._queue.task_done()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error(
                        f"Worker {worker_name} error: {e}", exc_info=True
                    )

        finally:
            self._logger.debug(f"Worker {worker_name} stopped")

    async def _execute_operation(
        self, operation: QueuedOperation, worker_name: str
    ) -> None:
        """Execute a single operation with proper error handling and monitoring."""
        operation.started_at = time.time()
        operation.status = OperationStatus.RUNNING

        async with self._queue_lock:
            current_task = asyncio.current_task()
            if current_task:
                self._active_operations[operation.operation_id] = current_task

        self._logger.debug(f"Worker {worker_name} executing: {operation.name}")
        self.monitor.on_operation_started(operation)

        try:
            # Execute with timeout and cancellation support
            if operation.coroutine is None:
                raise RuntimeError(
                    f"No coroutine provided for operation {operation.name}"
                )

            result = await asyncio.wait_for(
                operation.coroutine, timeout=operation.timeout
            )

            # Check for cancellation after execution
            if operation.is_cancelled():
                operation.status = OperationStatus.CANCELLED
                self.monitor.on_operation_cancelled(operation)
                return

            # Success
            operation.result = result
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = time.time()

            self._stats["total_completed"] += 1
            self.monitor.on_operation_completed(operation)

            # Call success callback
            if operation.callback:
                try:
                    operation.callback(result)
                except Exception as e:
                    self._logger.warning(
                        f"Success callback failed for {operation.name}: {e}"
                    )

        except asyncio.CancelledError:
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = time.time()
            self.monitor.on_operation_cancelled(operation)

        except Exception as e:
            operation.error = e
            operation.status = OperationStatus.FAILED
            operation.completed_at = time.time()

            self._stats["total_failed"] += 1
            self.monitor.on_operation_failed(operation)

            # Call error callback
            if operation.error_callback:
                try:
                    operation.error_callback(e)
                except Exception as callback_error:
                    self._logger.warning(
                        f"Error callback failed for {operation.name}: {callback_error}"
                    )

        finally:
            # Cleanup
            async with self._queue_lock:
                self._active_operations.pop(operation.operation_id, None)

                # Move to completed operations (keep limited history)
                self._completed_operations.append(operation)
                if len(self._completed_operations) > 100:  # Keep last 100
                    self._completed_operations = self._completed_operations[-50:]

            await self._notify_queue_status_changed()

    async def _notify_queue_status_changed(self) -> None:
        """Notify monitor of queue status changes."""
        try:
            queue_size = self._queue.qsize()
            active_count = len(self._active_operations)
            self.monitor.on_queue_status_changed(queue_size, active_count)
        except Exception as e:
            self._logger.warning(f"Monitor notification failed: {e}")

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific operation."""
        operation = self._operations.get(operation_id)
        if not operation:
            # Check completed operations
            for op in self._completed_operations:
                if op.operation_id == operation_id:
                    return op.to_dict()
            return None

        return operation.to_dict()

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        return {
            "queue_size": self._queue.qsize(),
            "active_operations": len(self._active_operations),
            "total_queued": self._stats["total_queued"],
            "total_completed": self._stats["total_completed"],
            "total_failed": self._stats["total_failed"],
            "total_cancelled": self._stats["total_cancelled"],
            "is_running": self._is_running,
            "max_concurrent": self.max_concurrent,
            "success_rate": (
                self._stats["total_completed"]
                / max(1, self._stats["total_queued"])
                * 100
            ),
        }

    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get list of currently active operations."""
        return [
            operation.to_dict()
            for operation_id, operation in self._operations.items()
            if operation.status == OperationStatus.RUNNING
        ]

    def get_queued_operations(self) -> List[Dict[str, Any]]:
        """Get list of queued operations."""
        return [
            operation.to_dict()
            for operation in self._operations.values()
            if operation.status == OperationStatus.QUEUED
        ]


# Global operation queue instance
_global_operation_queue: Optional[AsyncOperationQueue] = None


async def get_operation_queue() -> AsyncOperationQueue:
    """Get global operation queue instance."""
    global _global_operation_queue
    if _global_operation_queue is None:
        _global_operation_queue = AsyncOperationQueue()
        await _global_operation_queue.start()
    return _global_operation_queue
