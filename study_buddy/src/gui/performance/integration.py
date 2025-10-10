"""
Study Buddy GUI - Performance Integration Mixins

Provides mixins and utilities for integrating performance features into existing widgets.
Enables backwards-compatible performance enhancements without breaking existing code.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Mixin Pattern, Adapter Pattern, Strategy Pattern
SOLID: SRP (integration only), OCP (extensible), DIP (abstraction-based)
"""

import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Union

from gui.performance.async_queue import AsyncOperationQueue, OperationPriority, get_operation_queue
from gui.performance.cache_manager import CacheKey, CacheManager, get_document_cache, get_chunk_cache, get_summary_cache
from gui.performance.lazy_loader import LazyLoader, LazyProxy, get_lazy_loader
from gui.performance.memory_monitor import (
    IMonitorable,
    MemoryMonitor,
    WidgetMemoryInfo,
    get_memory_monitor,
)

T = TypeVar("T")


class CacheableMixin:
    """
    Mixin to add caching capabilities to widgets.
    
    Provides automatic caching for MCP operations with configurable policies.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize caching mixin."""
        super().__init__(*args, **kwargs)
        self._cache_enabled = True
        self._cache_prefix = getattr(self, "widget_id", self.__class__.__name__)
        self._logger = logging.getLogger(__name__)
    
    def get_cache_manager(self, cache_type: str = "document") -> CacheManager[Dict[str, Any]]:
        """
        Get appropriate cache manager for data type.
        
        Args:
            cache_type: Type of cache ("document", "chunk", "summary")
            
        Returns:
            Cache manager instance
        """
        cache_managers = {
            "document": get_document_cache,
            "chunk": get_chunk_cache,
            "summary": get_summary_cache,
        }
        
        cache_func = cache_managers.get(cache_type)
        if not cache_func:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        return cache_func()
    
    def create_cache_key(
        self, category: str, identifier: Union[int, str], context: Optional[Dict[str, Any]] = None
    ) -> CacheKey:
        """
        Create cache key with widget prefix.
        
        Args:
            category: Data category (e.g., "document", "chunk")
            identifier: Unique identifier
            context: Additional context for cache differentiation
            
        Returns:
            Cache key with widget context
        """
        widget_context = {"widget": self._cache_prefix}
        if context:
            widget_context.update(context)
        
        return CacheKey(category=category, identifier=identifier, context=widget_context)
    
    def get_cached_data(
        self,
        cache_type: str,
        category: str,
        identifier: Union[int, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache.
        
        Args:
            cache_type: Cache type ("document", "chunk", "summary")
            category: Data category
            identifier: Data identifier
            context: Additional context
            
        Returns:
            Cached data or None if not found
        """
        if not self._cache_enabled:
            return None
        
        try:
            cache = self.get_cache_manager(cache_type)
            key = self.create_cache_key(category, identifier, context)
            return cache.get(key)
        except Exception as e:
            self._logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    def cache_data(
        self,
        cache_type: str,
        category: str,
        identifier: Union[int, str],
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Store data in cache.
        
        Args:
            cache_type: Cache type ("document", "chunk", "summary")
            category: Data category
            identifier: Data identifier
            data: Data to cache
            context: Additional context
            ttl: Time-to-live override
        """
        if not self._cache_enabled:
            return
        
        try:
            cache = self.get_cache_manager(cache_type)
            key = self.create_cache_key(category, identifier, context)
            cache.put(key, data, ttl)
        except Exception as e:
            self._logger.warning(f"Cache storage failed: {e}")
    
    def invalidate_cache(
        self,
        cache_type: str,
        category: str,
        identifier: Union[int, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Remove data from cache.
        
        Args:
            cache_type: Cache type
            category: Data category
            identifier: Data identifier
            context: Additional context
            
        Returns:
            True if data was removed
        """
        try:
            cache = self.get_cache_manager(cache_type)
            key = self.create_cache_key(category, identifier, context)
            return cache.invalidate(key)
        except Exception as e:
            self._logger.warning(f"Cache invalidation failed: {e}")
            return False
    
    def enable_cache(self) -> None:
        """Enable caching for this widget."""
        self._cache_enabled = True
    
    def disable_cache(self) -> None:
        """Disable caching for this widget."""
        self._cache_enabled = False
    
    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache_enabled


class LazyLoadableMixin:
    """
    Mixin to add lazy loading capabilities to widgets.
    
    Provides on-demand data loading for improved performance with large datasets.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize lazy loading mixin."""
        super().__init__(*args, **kwargs)
        self._lazy_loader = get_lazy_loader()
        self._lazy_proxies: Dict[str, LazyProxy] = {}
        self._logger = logging.getLogger(__name__)
    
    def create_lazy_proxy(
        self,
        key: str,
        loader_func,
        priority: int = 10,
        cache_result: bool = True,
        cache_type: str = "document",
    ) -> LazyProxy[T]:
        """
        Create lazy proxy for data loading.
        
        Args:
            key: Unique key for this data
            loader_func: Function to load the data
            priority: Loading priority (0 = highest)
            cache_result: Whether to cache the result
            cache_type: Cache type if caching enabled
            
        Returns:
            LazyProxy for the data
        """
        # Wrap loader with caching if enabled
        if cache_result and hasattr(self, "_cache_enabled") and self._cache_enabled:
            original_loader = loader_func
            
            async def cached_loader():
                # Try cache first
                cached_data = self.get_cached_data(cache_type, "lazy_data", key)
                if cached_data is not None:
                    return cached_data
                
                # Load data and cache it
                data = await original_loader()
                self.cache_data(cache_type, "lazy_data", key, data)
                return data
            
            loader_func = cached_loader
        
        proxy = LazyProxy(loader=loader_func, key=key, priority=priority)
        self._lazy_proxies[key] = proxy
        return proxy
    
    async def load_data_async(self, key: str) -> Any:
        """
        Load data asynchronously through lazy loader.
        
        Args:
            key: Key of data to load
            
        Returns:
            Loaded data
        """
        proxy = self._lazy_proxies.get(key)
        if not proxy:
            raise ValueError(f"No lazy proxy found for key: {key}")
        
        return await self._lazy_loader.load_item(proxy)
    
    def get_proxy(self, key: str) -> Optional[LazyProxy]:
        """Get lazy proxy by key."""
        return self._lazy_proxies.get(key)
    
    def get_loading_progress(self) -> Dict[str, Any]:
        """Get loading progress for all proxies."""
        total = len(self._lazy_proxies)
        loaded = sum(1 for proxy in self._lazy_proxies.values() if proxy.is_loaded)
        
        return {
            "total": total,
            "loaded": loaded,
            "percentage": (loaded / total * 100) if total > 0 else 100,
            "active_loads": [key for key, proxy in self._lazy_proxies.items() if proxy.is_loading],
        }
    
    def cancel_loading(self, key: Optional[str] = None) -> None:
        """
        Cancel loading operations.
        
        Args:
            key: Specific key to cancel, or None to cancel all
        """
        if key:
            proxy = self._lazy_proxies.get(key)
            if proxy:
                proxy.cancel()
        else:
            for proxy in self._lazy_proxies.values():
                proxy.cancel()


class AsyncQueueMixin:
    """
    Mixin to add async operation queue capabilities to widgets.
    
    Provides priority-based async operations with progress tracking.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize async queue mixin."""
        super().__init__(*args, **kwargs)
        self._operation_queue: Optional[AsyncOperationQueue] = None
        self._widget_operations: Dict[str, str] = {}  # operation_name -> operation_id
        self._logger = logging.getLogger(__name__)
    
    async def get_operation_queue(self) -> AsyncOperationQueue:
        """Get operation queue instance."""
        if self._operation_queue is None:
            self._operation_queue = await get_operation_queue()
        return self._operation_queue
    
    async def queue_mcp_operation(
        self,
        operation_name: str,
        mcp_tool: str,
        tool_args: Dict[str, Any],
        priority: OperationPriority = OperationPriority.NORMAL,
        timeout: Optional[float] = None,
        cache_result: bool = True,
    ) -> str:
        """
        Queue MCP operation with caching support.
        
        Args:
            operation_name: Human-readable operation name
            mcp_tool: MCP tool name to call
            tool_args: Arguments for the MCP tool
            priority: Operation priority
            timeout: Operation timeout
            cache_result: Whether to cache the result
            
        Returns:
            Operation ID for tracking
        """
        queue = await self.get_operation_queue()
        
        # Create MCP operation coroutine
        async def mcp_operation():
            # Check cache first if enabled
            if cache_result and hasattr(self, "_cache_enabled") and self._cache_enabled:
                cache_key_str = f"{mcp_tool}_{hash(str(tool_args))}"
                cached_result = self.get_cached_data("document", mcp_tool, cache_key_str)
                if cached_result:
                    return cached_result
            
            # Execute MCP call (assumes self has mcp_client)
            if not hasattr(self, "mcp_client"):
                raise RuntimeError("Widget must have mcp_client attribute for MCP operations")
            
            response = await self.mcp_client.call_tool(mcp_tool, tool_args)
            
            # Cache result if successful
            if (
                cache_result
                and hasattr(self, "_cache_enabled")
                and self._cache_enabled
                and response
                and hasattr(response, "data")
                and response.data
            ):
                cache_key_str = f"{mcp_tool}_{hash(str(tool_args))}"
                self.cache_data("document", mcp_tool, cache_key_str, response.data)
            
            return response
        
        # Queue the operation
        operation = await queue.queue_operation(
            coroutine=mcp_operation(),
            name=f"{self.__class__.__name__}: {operation_name}",
            priority=priority,
            timeout=timeout,
        )
        
        # Track operation
        self._widget_operations[operation_name] = operation.operation_id
        
        return operation.operation_id
    
    async def wait_for_operation(self, operation_name: str) -> Any:
        """
        Wait for a queued operation to complete.
        
        Args:
            operation_name: Name of operation to wait for
            
        Returns:
            Operation result
        """
        operation_id = self._widget_operations.get(operation_name)
        if not operation_id:
            raise ValueError(f"No operation found with name: {operation_name}")
        
        queue = await self.get_operation_queue()
        
        # Wait for operation to complete (polling approach)
        while True:
            status = queue.get_operation_status(operation_id)
            if not status:
                raise RuntimeError(f"Operation {operation_id} not found")
            
            if status["status"] == "completed":
                # Get the operation object to access result
                # This is a simplified approach - in production you might want a better way
                return status.get("result")
            elif status["status"] == "failed":
                error_msg = status.get("error_message", "Unknown error")
                raise RuntimeError(f"Operation failed: {error_msg}")
            elif status["status"] == "cancelled":
                raise RuntimeError("Operation was cancelled")
            
            # Wait a bit before checking again
            await asyncio.sleep(0.1)
    
    def cancel_operation(self, operation_name: str) -> None:
        """Cancel a queued operation."""
        operation_id = self._widget_operations.get(operation_name)
        if operation_id and self._operation_queue:
            asyncio.create_task(self._operation_queue.cancel_operation(operation_id))
    
    def get_operation_status(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get status of operation by name."""
        operation_id = self._widget_operations.get(operation_name)
        if not operation_id or not self._operation_queue:
            return None
        
        return self._operation_queue.get_operation_status(operation_id)


class MonitorableMixin(IMonitorable):
    """
    Mixin to add memory monitoring capabilities to widgets.
    
    Implements IMonitorable interface for automatic memory tracking.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize monitorable mixin."""
        super().__init__(*args, **kwargs)
        self._memory_monitor = get_memory_monitor()
        self._is_monitored = False
        self._logger = logging.getLogger(__name__)
        
        # Register for monitoring if widget has ID
        if hasattr(self, "widget_id"):
            self.enable_monitoring()
    
    def enable_monitoring(self) -> None:
        """Enable memory monitoring for this widget."""
        if hasattr(self, "widget_id") and not self._is_monitored:
            self._memory_monitor.register_widget(self.widget_id, self)
            self._is_monitored = True
            self._logger.debug(f"Memory monitoring enabled for {self.widget_id}")
    
    def disable_monitoring(self) -> None:
        """Disable memory monitoring for this widget."""
        if hasattr(self, "widget_id") and self._is_monitored:
            self._memory_monitor.unregister_widget(self.widget_id)
            self._is_monitored = False
            self._logger.debug(f"Memory monitoring disabled for {self.widget_id}")
    
    def get_memory_info(self) -> WidgetMemoryInfo:
        """Get memory usage information for this widget."""
        widget_id = getattr(self, "widget_id", self.__class__.__name__)
        
        # Estimate memory usage
        memory_bytes = 0
        object_count = 0
        
        try:
            # Get approximate memory usage
            memory_bytes = sys.getsizeof(self)
            
            # Count major objects
            for attr_name in dir(self):
                if not attr_name.startswith("_"):
                    try:
                        attr_value = getattr(self, attr_name)
                        if not callable(attr_value):
                            memory_bytes += sys.getsizeof(attr_value)
                            object_count += 1
                    except Exception:
                        pass  # Skip problematic attributes
        
        except Exception as e:
            self._logger.warning(f"Memory calculation failed for {widget_id}: {e}")
        
        return WidgetMemoryInfo(
            widget_id=widget_id,
            widget_class=self.__class__.__name__,
            memory_bytes=memory_bytes,
            object_count=object_count,
        )
    
    def cleanup_memory(self) -> None:
        """Perform memory cleanup for this widget."""
        try:
            # Cancel any lazy loading operations
            if hasattr(self, "_lazy_proxies"):
                for proxy in self._lazy_proxies.values():
                    proxy.cancel()
                self._lazy_proxies.clear()
            
            # Cancel queued operations
            if hasattr(self, "_widget_operations"):
                for operation_name in list(self._widget_operations.keys()):
                    self.cancel_operation(operation_name)
                self._widget_operations.clear()
            
            # Clear any large data structures
            for attr_name in ["_cached_data", "_loaded_items", "_data_cache"]:
                if hasattr(self, attr_name):
                    try:
                        delattr(self, attr_name)
                    except Exception:
                        pass
            
            self._logger.debug(f"Memory cleanup completed for {self.__class__.__name__}")
        
        except Exception as e:
            self._logger.warning(f"Memory cleanup failed: {e}")


class PerformanceWidget(CacheableMixin, LazyLoadableMixin, AsyncQueueMixin, MonitorableMixin):
    """
    Complete performance-enhanced widget mixin.
    
    Combines all performance features into a single mixin for convenience.
    Widgets can inherit from this to get all performance capabilities.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize performance widget with all capabilities."""
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)
        self._logger.debug(f"Performance features enabled for {self.__class__.__name__}")
    
    def get_performance_status(self) -> Dict[str, Any]:
        """Get comprehensive performance status for this widget."""
        return {
            "cache_enabled": self.is_cache_enabled(),
            "memory_monitored": self._is_monitored,
            "loading_progress": self.get_loading_progress(),
            "memory_info": self.get_memory_info().to_dict() if hasattr(self, "get_memory_info") else {},
            "active_operations": len(self._widget_operations),
        }
    
    async def preload_data(self, keys: list[str]) -> None:
        """Preload multiple data items for improved performance."""
        tasks = []
        for key in keys:
            if key in self._lazy_proxies:
                tasks.append(self.load_data_async(key))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def optimize_performance(self) -> None:
        """Run performance optimizations for this widget."""
        try:
            # Enable caching if not already enabled
            if not self.is_cache_enabled():
                self.enable_cache()
            
            # Enable monitoring if not already enabled
            if not self._is_monitored:
                self.enable_monitoring()
            
            # Force memory cleanup
            self.cleanup_memory()
            
            self._logger.info(f"Performance optimization completed for {self.__class__.__name__}")
        
        except Exception as e:
            self._logger.warning(f"Performance optimization failed: {e}")


# Utility function for easy integration
def add_performance_features(widget_class):
    """
    Decorator to add performance features to existing widget classes.
    
    Usage:
        @add_performance_features
        class MyWidget(BaseWidget):
            pass
    """
    
    class PerformanceEnhancedWidget(PerformanceWidget, widget_class):
        pass
    
    return PerformanceEnhancedWidget