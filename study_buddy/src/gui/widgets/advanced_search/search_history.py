"""
Search History Management for Study Buddy GUI Application.

Provides persistent search history storage, favorites management, and
search analytics for the advanced search system.

Part of Task 14, Phase 1: Advanced Search Enhancement
Architecture: Clean Architecture Layer 2 (Business Logic)  
SOLID Compliance: Single Responsibility, Interface Segregation via focused interfaces
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from abc import ABC, abstractmethod
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass 
class SearchEntry:
    """Represents a single search history entry."""
    query: str
    timestamp: datetime
    result_count: int = 0
    execution_time_ms: int = 0
    filters_used: Dict[str, Any] = field(default_factory=dict)
    selected_result_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchEntry':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class SavedSearch:
    """Represents a saved/favorite search."""
    name: str
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    is_favorite: bool = False
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_date'] = self.created_date.isoformat()
        data['last_used'] = self.last_used.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedSearch':
        """Create from dictionary."""
        data = data.copy()
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)


@dataclass
class SearchAnalytics:
    """Search analytics and statistics."""
    total_searches: int = 0
    unique_queries: int = 0
    average_results_per_search: float = 0.0
    average_execution_time_ms: float = 0.0
    most_common_queries: List[Tuple[str, int]] = field(default_factory=list)
    search_frequency_by_hour: Dict[int, int] = field(default_factory=dict)
    search_frequency_by_day: Dict[str, int] = field(default_factory=dict)
    popular_filters: Dict[str, int] = field(default_factory=dict)
    success_rate: float = 0.0  # Percentage of searches that returned results


class HistoryStorage(ABC):
    """Abstract interface for search history storage."""
    
    @abstractmethod
    async def save_search_entry(self, entry: SearchEntry) -> None:
        """Save a search history entry."""
        pass
    
    @abstractmethod
    async def get_search_history(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[SearchEntry]:
        """Retrieve search history entries."""
        pass
    
    @abstractmethod
    async def save_saved_search(self, saved_search: SavedSearch) -> None:
        """Save a favorite search."""
        pass
    
    @abstractmethod
    async def get_saved_searches(self) -> List[SavedSearch]:
        """Retrieve all saved searches."""
        pass
    
    @abstractmethod
    async def delete_saved_search(self, name: str) -> bool:
        """Delete a saved search by name."""
        pass
    
    @abstractmethod
    async def clear_history(self, older_than: Optional[datetime] = None) -> int:
        """Clear search history, optionally older than specified date."""
        pass


class SQLiteHistoryStorage(HistoryStorage):
    """SQLite implementation of search history storage."""
    
    def __init__(self, db_path: str):
        """Initialize SQLite storage."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self) -> None:
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    result_count INTEGER DEFAULT 0,
                    execution_time_ms INTEGER DEFAULT 0,
                    filters_used TEXT DEFAULT '{}',
                    selected_result_id TEXT,
                    session_id TEXT,
                    UNIQUE(query, timestamp)
                )
            """)
            
            # Saved searches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_searches (
                    name TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    filters TEXT DEFAULT '{}',
                    description TEXT DEFAULT '',
                    created_date TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    use_count INTEGER DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    tags TEXT DEFAULT '[]'
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_timestamp 
                ON search_history(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_query 
                ON search_history(query)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_saved_last_used 
                ON saved_searches(last_used)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Search history database initialized: %s", self.db_path)
            
        except Exception as e:
            logger.error("Failed to initialize search history database: %s", e)
            raise
    
    async def save_search_entry(self, entry: SearchEntry) -> None:
        """Save search entry to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO search_history 
                (query, timestamp, result_count, execution_time_ms, filters_used, 
                 selected_result_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.query,
                entry.timestamp.isoformat(),
                entry.result_count,
                entry.execution_time_ms,
                json.dumps(entry.filters_used),
                entry.selected_result_id,
                entry.session_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug("Saved search entry: %s", entry.query)
            
        except Exception as e:
            logger.error("Failed to save search entry: %s", e)
            raise
    
    async def get_search_history(
        self,
        limit: Optional[int] = None,
        offset: int = 0, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[SearchEntry]:
        """Retrieve search history from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM search_history WHERE 1=1"
            params = []
            
            if date_from:
                query += " AND timestamp >= ?"
                params.append(date_from.isoformat())
            
            if date_to:
                query += " AND timestamp <= ?"
                params.append(date_to.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            entries = []
            for row in rows:
                entry = SearchEntry(
                    query=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    result_count=row[3],
                    execution_time_ms=row[4],
                    filters_used=json.loads(row[5]) if row[5] else {},
                    selected_result_id=row[6],
                    session_id=row[7]
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error("Failed to retrieve search history: %s", e)
            return []
    
    async def save_saved_search(self, saved_search: SavedSearch) -> None:
        """Save favorite search to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO saved_searches 
                (name, query, filters, description, created_date, last_used, 
                 use_count, is_favorite, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                saved_search.name,
                saved_search.query,
                json.dumps(saved_search.filters),
                saved_search.description,
                saved_search.created_date.isoformat(),
                saved_search.last_used.isoformat(),
                saved_search.use_count,
                saved_search.is_favorite,
                json.dumps(saved_search.tags)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("Saved search: %s", saved_search.name)
            
        except Exception as e:
            logger.error("Failed to save search: %s", e)
            raise
    
    async def get_saved_searches(self) -> List[SavedSearch]:
        """Retrieve all saved searches from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM saved_searches ORDER BY last_used DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            saved_searches = []
            for row in rows:
                saved_search = SavedSearch(
                    name=row[0],
                    query=row[1],
                    filters=json.loads(row[2]) if row[2] else {},
                    description=row[3],
                    created_date=datetime.fromisoformat(row[4]),
                    last_used=datetime.fromisoformat(row[5]),
                    use_count=row[6],
                    is_favorite=bool(row[7]),
                    tags=json.loads(row[8]) if row[8] else []
                )
                saved_searches.append(saved_search)
            
            return saved_searches
            
        except Exception as e:
            logger.error("Failed to retrieve saved searches: %s", e)
            return []
    
    async def delete_saved_search(self, name: str) -> bool:
        """Delete saved search by name."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM saved_searches WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info("Deleted saved search: %s", name)
            
            return deleted
            
        except Exception as e:
            logger.error("Failed to delete saved search: %s", e)
            return False
    
    async def clear_history(self, older_than: Optional[datetime] = None) -> int:
        """Clear search history entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if older_than:
                cursor.execute(
                    "DELETE FROM search_history WHERE timestamp < ?",
                    (older_than.isoformat(),)
                )
            else:
                cursor.execute("DELETE FROM search_history")
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info("Cleared %d search history entries", deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to clear search history: %s", e)
            return 0


class SearchHistoryManager:
    """
    Search history and favorites management system.
    
    Responsibilities:
    - Persist search queries and metadata for analytics
    - Manage saved/favorite searches with organization
    - Provide search analytics and usage statistics
    - Support search history cleanup and maintenance
    
    Architecture:
    - Uses Strategy pattern for different storage backends
    - Provides async interface for non-blocking operations
    - Integrates with search analytics for insights
    - Follows Single Responsibility and Interface Segregation principles
    """
    
    def __init__(self, storage: HistoryStorage, mcp_client: Optional[Any] = None):
        """
        Initialize search history manager.
        
        Args:
            storage: History storage implementation
            mcp_client: Optional MCP client for advanced features
        """
        self.storage = storage
        self.mcp_client = mcp_client
        
        # Cache for performance
        self._saved_searches_cache: Optional[List[SavedSearch]] = None
        self._cache_last_updated: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        
        logger.info("SearchHistoryManager initialized")
    
    async def record_search(
        self,
        query: str,
        result_count: int = 0,
        execution_time_ms: int = 0,
        filters_used: Optional[Dict[str, Any]] = None,
        selected_result_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Record a search query in history.
        
        Args:
            query: The search query that was executed
            result_count: Number of results returned
            execution_time_ms: Query execution time in milliseconds
            filters_used: Filters that were applied
            selected_result_id: ID of result that was selected (if any)
            session_id: Current user session ID
        """
        if not query.strip():
            return
        
        entry = SearchEntry(
            query=query.strip(),
            timestamp=datetime.now(),
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            filters_used=filters_used or {},
            selected_result_id=selected_result_id,
            session_id=session_id
        )
        
        try:
            await self.storage.save_search_entry(entry)
            logger.debug("Recorded search: '%s' (%d results, %dms)", query, result_count, execution_time_ms)
        except Exception as e:
            logger.error("Failed to record search: %s", e)
    
    async def get_recent_searches(self, limit: int = 20) -> List[SearchEntry]:
        """
        Get recent search queries.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of recent search entries
        """
        try:
            return await self.storage.get_search_history(limit=limit)
        except Exception as e:
            logger.error("Failed to get recent searches: %s", e)
            return []
    
    async def get_unique_recent_queries(self, limit: int = 10) -> List[str]:
        """
        Get unique recent search queries (no duplicates).
        
        Args:
            limit: Maximum number of unique queries to return
            
        Returns:
            List of unique search query strings
        """
        try:
            # Get more entries than needed to account for duplicates
            entries = await self.storage.get_search_history(limit=limit * 3)
            
            # Extract unique queries while preserving order
            seen = set()
            unique_queries = []
            
            for entry in entries:
                if entry.query not in seen:
                    seen.add(entry.query)
                    unique_queries.append(entry.query)
                    
                    if len(unique_queries) >= limit:
                        break
            
            return unique_queries
            
        except Exception as e:
            logger.error("Failed to get unique recent queries: %s", e)
            return []
    
    async def save_search(
        self,
        name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        is_favorite: bool = False
    ) -> SavedSearch:
        """
        Save a search as favorite for quick access.
        
        Args:
            name: Unique name for the saved search
            query: The search query
            filters: Search filters to save with query
            description: Optional description
            tags: Optional tags for organization
            is_favorite: Whether to mark as favorite
            
        Returns:
            The created SavedSearch object
        """
        saved_search = SavedSearch(
            name=name,
            query=query,
            filters=filters or {},
            description=description,
            tags=tags or [],
            is_favorite=is_favorite
        )
        
        try:
            await self.storage.save_saved_search(saved_search)
            
            # Invalidate cache
            self._saved_searches_cache = None
            
            logger.info("Saved search '%s': %s", name, query)
            return saved_search
            
        except Exception as e:
            logger.error("Failed to save search '%s': %s", name, e)
            raise
    
    async def get_saved_searches(self, force_reload: bool = False) -> List[SavedSearch]:
        """
        Get all saved searches with caching.
        
        Args:
            force_reload: Force reload from storage, bypassing cache
            
        Returns:
            List of saved searches
        """
        now = datetime.now()
        
        # Check if cache is valid
        if (not force_reload and 
            self._saved_searches_cache is not None and 
            self._cache_last_updated is not None and 
            now - self._cache_last_updated < self._cache_ttl):
            return self._saved_searches_cache
        
        # Load from storage
        try:
            saved_searches = await self.storage.get_saved_searches()
            
            # Update cache
            self._saved_searches_cache = saved_searches
            self._cache_last_updated = now
            
            return saved_searches
            
        except Exception as e:
            logger.error("Failed to get saved searches: %s", e)
            return []
    
    async def update_saved_search_usage(self, name: str) -> None:
        """
        Update usage statistics for saved search.
        
        Args:
            name: Name of the saved search that was used
        """
        try:
            saved_searches = await self.get_saved_searches()
            
            for saved_search in saved_searches:
                if saved_search.name == name:
                    saved_search.use_count += 1
                    saved_search.last_used = datetime.now()
                    
                    await self.storage.save_saved_search(saved_search)
                    
                    # Invalidate cache
                    self._saved_searches_cache = None
                    
                    logger.debug("Updated usage for saved search: %s", name)
                    break
                    
        except Exception as e:
            logger.error("Failed to update saved search usage: %s", e)
    
    async def delete_saved_search(self, name: str) -> bool:
        """
        Delete a saved search.
        
        Args:
            name: Name of saved search to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            success = await self.storage.delete_saved_search(name)
            
            if success:
                # Invalidate cache
                self._saved_searches_cache = None
                logger.info("Deleted saved search: %s", name)
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete saved search '%s': %s", name, e)
            return False
    
    async def get_favorites(self) -> List[SavedSearch]:
        """Get only favorite saved searches."""
        saved_searches = await self.get_saved_searches()
        return [s for s in saved_searches if s.is_favorite]
    
    async def get_searches_by_tag(self, tag: str) -> List[SavedSearch]:
        """Get saved searches with specific tag."""
        saved_searches = await self.get_saved_searches()
        return [s for s in saved_searches if tag in s.tags]
    
    async def get_search_analytics(self, days: int = 30) -> SearchAnalytics:
        """
        Generate search analytics and statistics.
        
        Args:
            days: Number of days to include in analytics
            
        Returns:
            SearchAnalytics object with statistics
        """
        try:
            # Get search history for the specified period
            date_from = datetime.now() - timedelta(days=days)
            entries = await self.storage.get_search_history(date_from=date_from)
            
            if not entries:
                return SearchAnalytics()
            
            # Calculate analytics
            total_searches = len(entries)
            unique_queries = len(set(entry.query for entry in entries))
            
            total_results = sum(entry.result_count for entry in entries)
            avg_results = total_results / total_searches if total_searches > 0 else 0
            
            total_time = sum(entry.execution_time_ms for entry in entries)
            avg_time = total_time / total_searches if total_searches > 0 else 0
            
            # Most common queries
            query_counts = {}
            for entry in entries:
                query_counts[entry.query] = query_counts.get(entry.query, 0) + 1
            
            most_common = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Search frequency by hour
            hour_counts = {}
            day_counts = {}
            
            for entry in entries:
                hour = entry.timestamp.hour
                day = entry.timestamp.strftime('%Y-%m-%d')
                
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
            
            # Filter usage statistics
            filter_counts = {}
            for entry in entries:
                for filter_key in entry.filters_used.keys():
                    filter_counts[filter_key] = filter_counts.get(filter_key, 0) + 1
            
            # Success rate (searches that returned results)
            successful_searches = sum(1 for entry in entries if entry.result_count > 0)
            success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
            
            return SearchAnalytics(
                total_searches=total_searches,
                unique_queries=unique_queries,
                average_results_per_search=avg_results,
                average_execution_time_ms=avg_time,
                most_common_queries=most_common,
                search_frequency_by_hour=hour_counts,
                search_frequency_by_day=day_counts,
                popular_filters=filter_counts,
                success_rate=success_rate
            )
            
        except Exception as e:
            logger.error("Failed to generate search analytics: %s", e)
            return SearchAnalytics()
    
    async def cleanup_old_history(self, days_to_keep: int = 90) -> int:
        """
        Clean up old search history entries.
        
        Args:
            days_to_keep: Number of days of history to keep
            
        Returns:
            Number of entries deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = await self.storage.clear_history(older_than=cutoff_date)
            
            logger.info("Cleaned up %d old search history entries", deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup search history: %s", e)
            return 0
    
    async def export_saved_searches(self) -> Dict[str, Any]:
        """Export saved searches for backup or transfer."""
        try:
            saved_searches = await self.get_saved_searches()
            
            export_data = {
                "version": "1.0",
                "export_date": datetime.now().isoformat(),
                "saved_searches": [search.to_dict() for search in saved_searches]
            }
            
            logger.info("Exported %d saved searches", len(saved_searches))
            return export_data
            
        except Exception as e:
            logger.error("Failed to export saved searches: %s", e)
            return {"version": "1.0", "saved_searches": []}
    
    async def import_saved_searches(self, export_data: Dict[str, Any], overwrite_existing: bool = False) -> int:
        """
        Import saved searches from export data.
        
        Args:
            export_data: Export data from export_saved_searches()
            overwrite_existing: Whether to overwrite existing searches with same name
            
        Returns:
            Number of searches imported
        """
        try:
            imported_count = 0
            
            if "saved_searches" not in export_data:
                logger.warning("Invalid export data: missing saved_searches")
                return 0
            
            existing_searches = {s.name for s in await self.get_saved_searches()}
            
            for search_data in export_data["saved_searches"]:
                try:
                    saved_search = SavedSearch.from_dict(search_data)
                    
                    if saved_search.name in existing_searches and not overwrite_existing:
                        logger.warning("Skipping existing search: %s", saved_search.name)
                        continue
                    
                    await self.storage.save_saved_search(saved_search)
                    imported_count += 1
                    
                except Exception as e:
                    logger.error("Failed to import search '%s': %s", search_data.get("name", "unknown"), e)
            
            # Invalidate cache
            self._saved_searches_cache = None
            
            logger.info("Imported %d saved searches", imported_count)
            return imported_count
            
        except Exception as e:
            logger.error("Failed to import saved searches: %s", e)
            return 0