"""
Study Buddy GUI - Lazy Loading System

Provides on-demand data loading for improved performance with large document collections.
Implements lazy loading patterns for documents, chunks, and summaries.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Lazy Initialization, Proxy Pattern, Observer Pattern
SOLID: SRP (loading only), OCP (extensible strategies), DIP (abstraction-based)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class LoadingState(Enum):
    """States for lazy loading operations."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    CANCELLED = "cancelled"


class LoadingStrategy(Enum):
    """Different lazy loading strategies."""

    ON_DEMAND = "on_demand"  # Load when first accessed
    PREEMPTIVE = "preemptive"  # Load likely-needed items ahead of time
    BATCH = "batch"  # Load items in batches
    VIRTUAL = "virtual"  # Load only visible items (virtual scrolling)


@dataclass
class LoadingProgress:
    """Progress information for loading operations."""

    loaded: int = 0
    total: int = 0
    current_item: Optional[str] = None
    error: Optional[str] = None

    @property
    def percentage(self) -> float:
        """Get loading percentage (0-100)."""
        if self.total == 0:
            return 100.0
        return min(100.0, (self.loaded / self.total) * 100.0)

    @property
    def is_complete(self) -> bool:
        """Check if loading is complete."""
        return self.loaded >= self.total and self.total > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "loaded": self.loaded,
            "total": self.total,
            "percentage": self.percentage,
            "current_item": self.current_item,
            "error": self.error,
            "is_complete": self.is_complete,
        }


class ILazyLoadable(ABC):
    """Interface for objects that support lazy loading."""

    @abstractmethod
    async def load_data(self) -> Any:
        """Load the actual data for this object."""
        pass

    @abstractmethod
    def get_loading_key(self) -> str:
        """Get unique key for this loading operation."""
        pass

    @abstractmethod
    def get_loading_priority(self) -> int:
        """Get loading priority (0 = highest, higher numbers = lower priority)."""
        pass


class LazyProxy(Generic[T]):
    """
    Proxy object that loads data on-demand.

    Provides transparent access to data with automatic loading when accessed.
    Supports caching and progress tracking.
    """

    def __init__(self, loader: Callable[[], T], key: str, priority: int = 10):
        """
        Initialize lazy proxy.

        Args:
            loader: Function to load the actual data
            key: Unique key for this loading operation
            priority: Loading priority (0 = highest)
        """
        self._loader = loader
        self._key = key
        self._priority = priority
        self._state = LoadingState.UNLOADED
        self._data: Optional[T] = None
        self._error: Optional[Exception] = None
        self._loading_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[T], None]] = []

    @property
    def is_loaded(self) -> bool:
        """Check if data is loaded."""
        return self._state == LoadingState.LOADED

    @property
    def is_loading(self) -> bool:
        """Check if currently loading."""
        return self._state == LoadingState.LOADING

    @property
    def has_error(self) -> bool:
        """Check if loading failed."""
        return self._state == LoadingState.ERROR

    @property
    def key(self) -> str:
        """Get loading key."""
        return self._key

    @property
    def priority(self) -> int:
        """Get loading priority."""
        return self._priority

    async def load(self) -> T:
        """Load data if not already loaded."""
        if self._state == LoadingState.LOADED and self._data is not None:
            return self._data

        if self._state == LoadingState.LOADING:
            if self._loading_task:
                return await self._loading_task
            else:
                raise RuntimeError("Loading in progress but no task found")

        self._state = LoadingState.LOADING

        try:
            # Create loading task
            self._loading_task = asyncio.create_task(self._load_data())
            self._data = await self._loading_task

            self._state = LoadingState.LOADED

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(self._data)
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Callback error: {e}")

            return self._data

        except Exception as e:
            self._error = e
            self._state = LoadingState.ERROR
            raise
        finally:
            self._loading_task = None

    async def _load_data(self) -> T:
        """Execute the actual data loading."""
        if asyncio.iscoroutinefunction(self._loader):
            return await self._loader()
        else:
            # Run synchronous loader in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._loader)

    def add_callback(self, callback: Callable[[T], None]) -> None:
        """Add callback to be called when data is loaded."""
        self._callbacks.append(callback)

    def cancel(self) -> None:
        """Cancel loading operation."""
        if self._loading_task and not self._loading_task.done():
            self._loading_task.cancel()
            self._state = LoadingState.CANCELLED


@dataclass
class LazyCollection(Generic[T]):
    """
    Collection that loads items on-demand.

    Supports various loading strategies and virtual scrolling for large datasets.
    """

    items: List[LazyProxy[T]] = field(default_factory=list)
    strategy: LoadingStrategy = LoadingStrategy.ON_DEMAND
    batch_size: int = 10
    preload_count: int = 5

    def __len__(self) -> int:
        """Get collection size."""
        return len(self.items)

    def __getitem__(self, index: int) -> LazyProxy[T]:
        """Get item at index."""
        if not 0 <= index < len(self.items):
            raise IndexError("Index out of range")
        return self.items[index]

    async def load_item(self, index: int) -> T:
        """Load specific item by index."""
        if not 0 <= index < len(self.items):
            raise IndexError("Index out of range")

        proxy = self.items[index]

        # Apply loading strategy
        if self.strategy == LoadingStrategy.PREEMPTIVE:
            await self._preload_around(index)
        elif self.strategy == LoadingStrategy.BATCH:
            await self._load_batch(index)

        return await proxy.load()

    async def load_range(self, start: int, end: int) -> List[T]:
        """Load range of items."""
        if start < 0 or end > len(self.items) or start >= end:
            raise ValueError("Invalid range")

        # Load items concurrently
        tasks = [self.items[i].load() for i in range(start, end)]
        return await asyncio.gather(*tasks)

    async def _preload_around(self, index: int) -> None:
        """Preload items around the requested index."""
        start = max(0, index - self.preload_count)
        end = min(len(self.items), index + self.preload_count + 1)

        # Start loading tasks (don't await to avoid blocking)
        for i in range(start, end):
            if not self.items[i].is_loaded and not self.items[i].is_loading:
                asyncio.create_task(self.items[i].load())

    async def _load_batch(self, index: int) -> None:
        """Load batch containing the requested index."""
        batch_start = (index // self.batch_size) * self.batch_size
        batch_end = min(len(self.items), batch_start + self.batch_size)

        # Load batch items concurrently
        tasks = []
        for i in range(batch_start, batch_end):
            if not self.items[i].is_loaded and not self.items[i].is_loading:
                tasks.append(self.items[i].load())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_loaded_count(self) -> int:
        """Get number of currently loaded items."""
        return sum(1 for item in self.items if item.is_loaded)

    def get_loading_progress(self) -> LoadingProgress:
        """Get overall loading progress."""
        total = len(self.items)
        loaded = self.get_loaded_count()

        # Find currently loading item
        current_item = None
        for item in self.items:
            if item.is_loading:
                current_item = item.key
                break

        return LoadingProgress(loaded=loaded, total=total, current_item=current_item)


class LazyLoader:
    """
    Main lazy loading manager.

    Coordinates lazy loading operations across the application and manages
    loading queues, priorities, and strategies.
    """

    def __init__(self, max_concurrent_loads: int = 5):
        """
        Initialize lazy loader.

        Args:
            max_concurrent_loads: Maximum concurrent loading operations
        """
        self.max_concurrent_loads = max_concurrent_loads
        self._loading_queue: asyncio.Queue = asyncio.Queue()
        self._active_loads: Dict[str, LazyProxy] = {}
        self._load_semaphore = asyncio.Semaphore(max_concurrent_loads)
        self._logger = logging.getLogger(__name__)
        self._progress_callbacks: List[Callable[[LoadingProgress], None]] = []

        # Start loading worker
        self._worker_task = asyncio.create_task(self._loading_worker())

    async def load_item(self, proxy: LazyProxy[T]) -> T:
        """
        Load item through the managed loading queue.

        Args:
            proxy: Lazy proxy to load

        Returns:
            Loaded data
        """
        if proxy.is_loaded:
            return await proxy.load()

        # Add to queue if not already loading
        if proxy.key not in self._active_loads:
            await self._loading_queue.put(proxy)
            self._active_loads[proxy.key] = proxy

        # Wait for loading to complete
        return await proxy.load()

    async def _loading_worker(self) -> None:
        """Background worker that processes loading queue."""
        while True:
            try:
                # Get next item to load
                proxy = await self._loading_queue.get()

                # Skip if already loaded or loading
                if proxy.is_loaded or proxy.is_loading:
                    self._loading_queue.task_done()
                    continue

                # Acquire semaphore for concurrent loading limit
                async with self._load_semaphore:
                    try:
                        await proxy.load()
                        self._logger.debug(f"Loaded item: {proxy.key}")
                    except Exception as e:
                        self._logger.error(f"Failed to load item {proxy.key}: {e}")
                    finally:
                        # Remove from active loads
                        self._active_loads.pop(proxy.key, None)
                        self._loading_queue.task_done()

                        # Notify progress callbacks
                        self._notify_progress()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Loading worker error: {e}")

    def _notify_progress(self) -> None:
        """Notify progress callbacks of loading status."""
        progress = LoadingProgress(
            loaded=0,  # Would need to track globally
            total=0,  # Would need to track globally
            current_item=None,
        )

        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                self._logger.warning(f"Progress callback error: {e}")

    def add_progress_callback(
        self, callback: Callable[[LoadingProgress], None]
    ) -> None:
        """Add progress callback."""
        self._progress_callbacks.append(callback)

    def get_active_loads(self) -> List[str]:
        """Get keys of currently loading items."""
        return list(self._active_loads.keys())

    def cancel_all_loads(self) -> None:
        """Cancel all active loading operations."""
        for proxy in self._active_loads.values():
            proxy.cancel()
        self._active_loads.clear()

    async def shutdown(self) -> None:
        """Shutdown the lazy loader."""
        self.cancel_all_loads()

        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass


# Document-specific lazy loading utilities


class LazyDocumentLoader:
    """Lazy loader specifically for document operations."""

    def __init__(self, mcp_client):
        """Initialize with MCP client for data operations."""
        self.mcp_client = mcp_client
        self._logger = logging.getLogger(__name__)

    def create_document_proxy(self, document_id: int) -> LazyProxy[Dict[str, Any]]:
        """Create lazy proxy for document data."""

        async def load_document() -> Dict[str, Any]:
            response = await self.mcp_client.call_tool(
                "get_document", {"document_id": document_id}
            )
            if response and hasattr(response, "data") and response.data.get("success"):
                return response.data.get("document", {})
            raise RuntimeError(f"Failed to load document {document_id}")

        return LazyProxy(
            loader=load_document, key=f"document_{document_id}", priority=5
        )

    def create_chunk_proxy(self, chunk_id: int) -> LazyProxy[Dict[str, Any]]:
        """Create lazy proxy for chunk content."""

        async def load_chunk() -> Dict[str, Any]:
            response = await self.mcp_client.call_tool(
                "get_chunk_content", {"chunk_id": chunk_id}
            )
            if response and hasattr(response, "data") and response.data.get("success"):
                return response.data
            raise RuntimeError(f"Failed to load chunk {chunk_id}")

        return LazyProxy(
            loader=load_chunk,
            key=f"chunk_{chunk_id}",
            priority=1,  # Higher priority for content
        )

    def create_structure_proxy(self, document_id: int) -> LazyProxy[Dict[str, Any]]:
        """Create lazy proxy for document structure."""

        async def load_structure() -> Dict[str, Any]:
            response = await self.mcp_client.call_tool(
                "get_document_structure", {"document_id": document_id}
            )
            if response and hasattr(response, "data") and response.data.get("success"):
                return response.data
            raise RuntimeError(f"Failed to load structure for document {document_id}")

        return LazyProxy(
            loader=load_structure, key=f"structure_{document_id}", priority=3
        )


# Global lazy loader instance
_global_lazy_loader: Optional[LazyLoader] = None


def get_lazy_loader() -> LazyLoader:
    """Get global lazy loader instance."""
    global _global_lazy_loader
    if _global_lazy_loader is None:
        _global_lazy_loader = LazyLoader()
    return _global_lazy_loader
