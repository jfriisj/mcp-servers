"""
Bookmark repository for data access operations.

This module implements bookmark data persistence following Clean Architecture
Layer 3 principles. Provides CRUD operations and bookmark-specific queries.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.bookmark import Bookmark
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class BookmarkRepository(BaseRepository[Bookmark]):
    """
    Repository for bookmark data access operations.

    Provides bookmark-specific CRUD operations and queries while maintaining
    Clean Architecture Layer 3 responsibilities:

    - Abstract database operations behind clean interface
    - Transform between domain models and database rows
    - Handle database transactions and error mapping
    - Implement bookmark-specific query patterns

    Follows SOLID principles:
    - SRP: Only handles bookmark data persistence
    - OCP: Extensible for new bookmark query patterns
    - LSP: Can be substituted for BaseRepository[Bookmark]
    - ISP: Focused interface for bookmark operations
    - DIP: Depends on DatabaseConnection abstraction
    """

    def create(self, bookmark: Bookmark) -> Bookmark:
        """
        Create a new bookmark in the database.

        Args:
            bookmark: Bookmark domain model to persist

        Returns:
            Bookmark with populated ID and timestamps

        Raises:
            ValueError: If bookmark validation fails
            sqlite3.Error: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            # Prepare bookmark data for insertion
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO bookmarks (
                    title, document_id, chunk_id, category, notes,
                    page_number, position, tags, color, is_favorite,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bookmark.title,
                bookmark.document_id,
                bookmark.chunk_id,
                bookmark.category,
                bookmark.notes,
                bookmark.page_number,
                bookmark.position,
                ','.join(bookmark.tags) if bookmark.tags else None,
                bookmark.color,
                bookmark.is_favorite,
                now,
                now
            ))

            # Set the generated ID
            bookmark.id = cursor.lastrowid
            bookmark.created_at = datetime.fromisoformat(now)
            bookmark.updated_at = datetime.fromisoformat(now)

            self.db.commit()
            logger.info(f"Created bookmark {bookmark.id}: {bookmark.title}")

            return bookmark

        except sqlite3.Error as e:
            self.db.rollback()
            logger.error(f"Failed to create bookmark: {e}")
            raise

    def get_by_id(self, bookmark_id: int) -> Optional[Bookmark]:
        """
        Retrieve bookmark by ID.

        Args:
            bookmark_id: Bookmark primary key

        Returns:
            Bookmark if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,))
            row = cursor.fetchone()

            return self._row_to_bookmark(row) if row else None

        except sqlite3.Error as e:
            logger.error(f"Failed to get bookmark {bookmark_id}: {e}")
            return None

    def update(self, bookmark: Bookmark) -> Bookmark:
        """
        Update existing bookmark.

        Args:
            bookmark: Bookmark with updated data

        Returns:
            Updated bookmark

        Raises:
            ValueError: If bookmark ID is None
            sqlite3.Error: If database operation fails
        """
        if bookmark.id is None:
            raise ValueError("Cannot update bookmark without ID")

        try:
            cursor = self.db.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                UPDATE bookmarks SET
                    title = ?, document_id = ?, chunk_id = ?, category = ?,
                    notes = ?, page_number = ?, position = ?, tags = ?,
                    color = ?, is_favorite = ?, updated_at = ?
                WHERE id = ?
            """, (
                bookmark.title,
                bookmark.document_id,
                bookmark.chunk_id,
                bookmark.category,
                bookmark.notes,
                bookmark.page_number,
                bookmark.position,
                ','.join(bookmark.tags) if bookmark.tags else None,
                bookmark.color,
                bookmark.is_favorite,
                now,
                bookmark.id
            ))

            bookmark.updated_at = datetime.fromisoformat(now)

            self.db.commit()
            logger.info(f"Updated bookmark {bookmark.id}: {bookmark.title}")

            return bookmark

        except sqlite3.Error as e:
            self.db.rollback()
            logger.error(f"Failed to update bookmark {bookmark.id}: {e}")
            raise

    def delete(self, bookmark_id: int) -> bool:
        """
        Delete bookmark by ID.

        Args:
            bookmark_id: ID of bookmark to delete

        Returns:
            True if bookmark was deleted, False if not found
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))

            deleted = cursor.rowcount > 0
            self.db.commit()

            if deleted:
                logger.info(f"Deleted bookmark {bookmark_id}")

            return deleted

        except sqlite3.Error as e:
            self.db.rollback()
            logger.error(f"Failed to delete bookmark {bookmark_id}: {e}")
            return False

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Bookmark]:
        """
        List all bookmarks with optional filtering.

        Args:
            filters: Optional filter criteria

        Returns:
            List of matching bookmarks
        """
        try:
            cursor = self.db.cursor()

            query = "SELECT * FROM bookmarks WHERE 1=1"
            params = []

            if filters:
                if "document_id" in filters:
                    query += " AND document_id = ?"
                    params.append(filters["document_id"])

                if "category" in filters:
                    query += " AND category = ?"
                    params.append(filters["category"])

                if "is_favorite" in filters:
                    query += " AND is_favorite = ?"
                    params.append(filters["is_favorite"])

                if "chunk_id" in filters:
                    if filters["chunk_id"] is None:
                        query += " AND chunk_id IS NULL"
                    else:
                        query += " AND chunk_id = ?"
                        params.append(filters["chunk_id"])

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_bookmark(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to list bookmarks: {e}")
            return []

    def get_by_document_id(self, document_id: int) -> List[Bookmark]:
        """
        Get all bookmarks for a specific document.

        Args:
            document_id: Document ID to find bookmarks for

        Returns:
            List of bookmarks for the document
        """
        return self.list_all({"document_id": document_id})

    def get_by_category(self, category: str) -> List[Bookmark]:
        """
        Get all bookmarks in a specific category.

        Args:
            category: Category name

        Returns:
            List of bookmarks in the category
        """
        return self.list_all({"category": category})

    def get_favorites(self) -> List[Bookmark]:
        """
        Get all favorite bookmarks.

        Returns:
            List of favorite bookmarks
        """
        return self.list_all({"is_favorite": True})

    def get_categories(self) -> List[str]:
        """
        Get all unique bookmark categories.

        Returns:
            List of category names
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT DISTINCT category FROM bookmarks ORDER BY category")
            rows = cursor.fetchall()

            return [row[0] for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to get bookmark categories: {e}")
            return []

    def search_bookmarks(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Bookmark]:
        """
        Search bookmarks by title, notes, or tags.

        Args:
            query: Search query text
            filters: Optional additional filters

        Returns:
            List of matching bookmarks
        """
        try:
            cursor = self.db.cursor()

            search_query = """
                SELECT * FROM bookmarks
                WHERE (
                    title LIKE ? OR
                    notes LIKE ? OR
                    tags LIKE ?
                )
            """

            search_term = f"%{query}%"
            params = [search_term, search_term, search_term]

            if filters:
                if "document_id" in filters:
                    search_query += " AND document_id = ?"
                    params.append(filters["document_id"])

                if "category" in filters:
                    search_query += " AND category = ?"
                    params.append(filters["category"])

            search_query += " ORDER BY created_at DESC"

            cursor.execute(search_query, params)
            rows = cursor.fetchall()

            return [self._row_to_bookmark(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to search bookmarks: {e}")
            return []

    def delete_by_document_id(self, document_id: int) -> int:
        """
        Delete all bookmarks for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of bookmarks deleted
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE document_id = ?", (document_id,))

            deleted_count = cursor.rowcount
            self.db.commit()

            logger.info(f"Deleted {deleted_count} bookmarks for document {document_id}")
            return deleted_count

        except sqlite3.Error as e:
            self.db.rollback()
            logger.error(f"Failed to delete bookmarks for document {document_id}: {e}")
            return 0

    def _row_to_bookmark(self, row: tuple) -> Bookmark:
        """
        Convert database row to Bookmark model.

        Args:
            row: SQLite row tuple

        Returns:
            Bookmark domain model
        """
        # Parse tags from comma-separated string
        tags = []
        if row[8]:  # tags column
            tags = [tag.strip() for tag in row[8].split(',') if tag.strip()]

        # Parse timestamps
        created_at = datetime.fromisoformat(row[11]) if row[11] else None
        updated_at = datetime.fromisoformat(row[12]) if row[12] else None

        return Bookmark(
            id=row[0],
            title=row[1],
            document_id=row[2],
            chunk_id=row[3],
            category=row[4],
            notes=row[5],
            page_number=row[6],
            position=row[7],
            tags=tags,
            color=row[9],
            is_favorite=bool(row[10]),
            created_at=created_at,
            updated_at=updated_at
        )
