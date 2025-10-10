"""
Study Buddy GUI - Performance Optimization Package

Provides caching, lazy loading, memory management, and async operation optimization
for improved application performance with large document collections.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy (cache policies), Observer (memory monitoring), Factory (cache creation)
SOLID: All principles followed with proper abstractions and dependency injection
"""

from gui.performance.async_queue import AsyncOperationQueue, OperationPriority
from gui.performance.cache_manager import CacheManager, ICacheable
from gui.performance.lazy_loader import ILazyLoadable, LazyLoader
from gui.performance.memory_monitor import IMonitorable, MemoryMonitor

__all__ = [
    "CacheManager",
    "ICacheable",
    "LazyLoader",
    "ILazyLoadable",
    "MemoryMonitor",
    "IMonitorable",
    "AsyncOperationQueue",
    "OperationPriority",
]
