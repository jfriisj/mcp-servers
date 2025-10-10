"""
Study Buddy GUI - Cache Management System

Provides LRU caching with configurable size limits and eviction policies.
Implements Strategy pattern for different cache policies and type-safe cache keys.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy (cache policies), Singleton (global cache), Factory (cache creation)  
SOLID: SRP (cache management only), OCP (extensible policies), DIP (abstraction-based)
"""

import hashlib
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")


class CachePolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheKey:
    """Type-safe cache key with metadata."""

    category: str  # e.g., "document", "chunk", "summary"
    identifier: Union[int, str]  # Primary key or unique identifier
    context: Optional[Dict[str, Any]] = (
        None  # Additional context for cache differentiation
    )

    def __post_init__(self):
        """Validate cache key components."""
        if not self.category:
            raise ValueError("Cache key category cannot be empty")
        if not self.identifier:
            raise ValueError("Cache key identifier cannot be empty")

    def to_string(self) -> str:
        """Convert cache key to string representation."""
        key_data = {
            "category": self.category,
            "identifier": str(self.identifier),
            "context": self.context or {},
        }

        # Create deterministic string representation
        key_json = json.dumps(key_data, sort_keys=True, separators=(",", ":"))

        # Hash for consistent key length
        return hashlib.sha256(key_json.encode("utf-8")).hexdigest()

    def __str__(self) -> str:
        return self.to_string()

    def __hash__(self) -> int:
        return hash(self.to_string())

    def __eq__(self, other) -> bool:
        if not isinstance(other, CacheKey):
            return False
        return self.to_string() == other.to_string()


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata and statistics."""

    key: CacheKey
    value: T
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1

    def age(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


class ICacheable(ABC):
    """Interface for cacheable operations."""

    @abstractmethod
    def get_cache_key(self) -> CacheKey:
        """Get the cache key for this operation."""
        pass

    @abstractmethod
    def get_cache_ttl(self) -> Optional[float]:
        """Get time-to-live for cached data (None for no expiration)."""
        pass


class ICachePolicy(ABC, Generic[T]):
    """Abstract interface for cache eviction policies."""

    @abstractmethod
    def should_evict(
        self, entries: Dict[str, CacheEntry[T]], max_size: int
    ) -> Optional[str]:
        """Determine which entry should be evicted. Returns key to evict or None."""
        pass

    @abstractmethod
    def on_access(self, entry: CacheEntry[T]) -> None:
        """Handle entry access for policy tracking."""
        pass

    @abstractmethod
    def on_insert(self, entry: CacheEntry[T]) -> None:
        """Handle entry insertion for policy tracking."""
        pass


class LRUPolicy(ICachePolicy[T]):
    """Least Recently Used eviction policy."""

    def should_evict(
        self, entries: Dict[str, CacheEntry[T]], max_size: int
    ) -> Optional[str]:
        """Evict least recently used entry when cache is full."""
        if len(entries) < max_size:
            return None

        # Find entry with oldest last_accessed time
        oldest_key = None
        oldest_time = float("inf")

        for key, entry in entries.items():
            if entry.last_accessed < oldest_time:
                oldest_time = entry.last_accessed
                oldest_key = key

        return oldest_key

    def on_access(self, entry: CacheEntry[T]) -> None:
        """Update last accessed time."""
        entry.touch()

    def on_insert(self, entry: CacheEntry[T]) -> None:
        """No special handling needed for LRU on insert."""
        pass


class LFUPolicy(ICachePolicy[T]):
    """Least Frequently Used eviction policy."""

    def should_evict(
        self, entries: Dict[str, CacheEntry[T]], max_size: int
    ) -> Optional[str]:
        """Evict least frequently used entry when cache is full."""
        if len(entries) < max_size:
            return None

        # Find entry with lowest access count
        lfu_key = None
        lfu_count = float("inf")

        for key, entry in entries.items():
            if entry.access_count < lfu_count:
                lfu_count = entry.access_count
                lfu_key = key

        return lfu_key

    def on_access(self, entry: CacheEntry[T]) -> None:
        """Update access count."""
        entry.touch()

    def on_insert(self, entry: CacheEntry[T]) -> None:
        """No special handling needed for LFU on insert."""
        pass


class TTLPolicy(ICachePolicy[T]):
    """Time-To-Live eviction policy."""

    def should_evict(
        self, entries: Dict[str, CacheEntry[T]], max_size: int
    ) -> Optional[str]:
        """Evict expired entries first, then oldest entries."""
        # First, find any expired entries
        for key, entry in entries.items():
            if entry.is_expired():
                return key

        # If no expired entries and cache is full, evict oldest
        if len(entries) < max_size:
            return None

        oldest_key = None
        oldest_time = float("inf")

        for key, entry in entries.items():
            if entry.created_at < oldest_time:
                oldest_time = entry.created_at
                oldest_key = key

        return oldest_key

    def on_access(self, entry: CacheEntry[T]) -> None:
        """Update access time."""
        entry.touch()

    def on_insert(self, entry: CacheEntry[T]) -> None:
        """No special handling needed for TTL on insert."""
        pass


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    entries: int = 0
    memory_usage_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage."""
        return 100.0 - self.hit_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "entries": self.entries,
            "memory_usage_bytes": self.memory_usage_bytes,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
        }


class CacheManager(Generic[T]):
    """
    Thread-safe cache manager with configurable eviction policies.

    Provides high-performance caching for document content, chunk data,
    and summary information with automatic memory management.

    Features:
    - Multiple eviction policies (LRU, LFU, TTL)
    - Thread-safe operations with fine-grained locking
    - Comprehensive statistics and monitoring
    - Type-safe cache keys and values
    - Automatic TTL expiration
    """

    def __init__(
        self,
        max_size: int = 1000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: Optional[float] = None,
    ):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of entries to cache
            policy: Eviction policy to use
            default_ttl: Default time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._entries: Dict[str, CacheEntry[T]] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._stats = CacheStats()
        self._logger = logging.getLogger(__name__)

        # Create policy instance
        self._policy = self._create_policy(policy)

    def _create_policy(self, policy: CachePolicy) -> ICachePolicy[T]:
        """Factory method for creating cache policies."""
        policy_map = {
            CachePolicy.LRU: LRUPolicy[T],
            CachePolicy.LFU: LFUPolicy[T],
            CachePolicy.TTL: TTLPolicy[T],
            # FIFO can be implemented as LRU without access time updates
            CachePolicy.FIFO: LRUPolicy[T],
        }

        policy_class = policy_map.get(policy)
        if not policy_class:
            raise ValueError(f"Unsupported cache policy: {policy}")

        return policy_class()

    def get(self, key: CacheKey) -> Optional[T]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key to lookup

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            key_str = key.to_string()
            entry = self._entries.get(key_str)

            if entry is None:
                self._stats.misses += 1
                return None

            # Check if entry has expired
            if entry.is_expired():
                del self._entries[key_str]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None

            # Update access statistics
            self._policy.on_access(entry)
            self._stats.hits += 1

            return entry.value

    def put(self, key: CacheKey, value: T, ttl: Optional[float] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live override (uses default if None)
        """
        with self._lock:
            key_str = key.to_string()

            # Use provided TTL or default
            entry_ttl = ttl if ttl is not None else self.default_ttl

            # Create new cache entry
            entry = CacheEntry(key=key, value=value, ttl=entry_ttl)

            # Check if we need to evict entries
            while len(self._entries) >= self.max_size:
                evict_key = self._policy.should_evict(self._entries, self.max_size)
                if evict_key:
                    del self._entries[evict_key]
                    self._stats.evictions += 1
                else:
                    break

            # Store the entry
            self._entries[key_str] = entry
            self._policy.on_insert(entry)

            # Update statistics
            if key_str not in self._entries:
                self._stats.entries += 1

    def invalidate(self, key: CacheKey) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            key_str = key.to_string()
            if key_str in self._entries:
                del self._entries[key_str]
                self._stats.entries -= 1
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._entries.clear()
            self._stats.entries = 0

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = []

            for key_str, entry in self._entries.items():
                if entry.is_expired():
                    expired_keys.append(key_str)

            for key_str in expired_keys:
                del self._entries[key_str]

            removed_count = len(expired_keys)
            self._stats.entries -= removed_count
            self._stats.evictions += removed_count

            return removed_count

    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        with self._lock:
            # Update current entry count
            self._stats.entries = len(self._entries)
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                entries=self._stats.entries,
                memory_usage_bytes=self._stats.memory_usage_bytes,
            )

    def resize(self, new_max_size: int) -> None:
        """
        Resize cache and evict entries if necessary.

        Args:
            new_max_size: New maximum cache size
        """
        if new_max_size <= 0:
            raise ValueError("Cache size must be positive")

        with self._lock:
            self.max_size = new_max_size

            # Evict entries if cache is now oversized
            while len(self._entries) > self.max_size:
                evict_key = self._policy.should_evict(self._entries, self.max_size)
                if evict_key:
                    del self._entries[evict_key]
                    self._stats.evictions += 1
                else:
                    break

    def contains(self, key: CacheKey) -> bool:
        """Check if key exists in cache (without updating access stats)."""
        with self._lock:
            key_str = key.to_string()
            entry = self._entries.get(key_str)
            return entry is not None and not entry.is_expired()

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._entries)


# Global cache instances for different data types
_document_cache: Optional[CacheManager[Dict[str, Any]]] = None
_chunk_cache: Optional[CacheManager[Dict[str, Any]]] = None
_summary_cache: Optional[CacheManager[Dict[str, Any]]] = None


def get_document_cache() -> CacheManager[Dict[str, Any]]:
    """Get global document cache instance."""
    global _document_cache
    if _document_cache is None:
        _document_cache = CacheManager[Dict[str, Any]](
            max_size=500,  # 500 documents
            policy=CachePolicy.LRU,
            default_ttl=3600,  # 1 hour TTL
        )
    return _document_cache


def get_chunk_cache() -> CacheManager[Dict[str, Any]]:
    """Get global chunk cache instance."""
    global _chunk_cache
    if _chunk_cache is None:
        _chunk_cache = CacheManager[Dict[str, Any]](
            max_size=2000,  # 2000 chunks
            policy=CachePolicy.LRU,
            default_ttl=1800,  # 30 minutes TTL
        )
    return _chunk_cache


def get_summary_cache() -> CacheManager[Dict[str, Any]]:
    """Get global summary cache instance."""
    global _summary_cache
    if _summary_cache is None:
        _summary_cache = CacheManager[Dict[str, Any]](
            max_size=1000,  # 1000 summaries
            policy=CachePolicy.LRU,
            default_ttl=7200,  # 2 hour TTL
        )
    return _summary_cache
