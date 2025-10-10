"""
Progress Repository for Study Buddy MCP Server.

This module implements ProgressRepository, handling data access operations
for reading progress tracking with specialized queries and analytics
for Task 14 Phase 3.

Architecture: Clean Architecture Layer 3 (Data Access)
Dependencies: DatabaseConnection (Layer 4), ReadingProgress model (Layer 4)
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..database.connection import DatabaseConnection
from ..models.reading_progress import ProgressStatus, ProgressType, ReadingProgress

from ..repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProgressRepository(BaseRepository[ReadingProgress]):
    """
    Repository for reading progress data access operations.

    Provides specialized queries for progress tracking, analytics,
    and statistics following repository pattern and SRP.

    Responsibilities:
    - CRUD operations for reading progress
    - Progress analytics queries
    - Statistics calculation
    - Filtering and search operations

    Does NOT:
    - Contain business logic (service responsibility)
    - Handle MCP protocol (handler responsibility)
    - Manage UI state (widget responsibility)
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize progress repository.

        Args:
            db: Database connection instance
        """
        self.db = db
        self._logger = logging.getLogger(f"{__name__}.ProgressRepository")

    def create(self, progress: ReadingProgress) -> ReadingProgress:
        """
        Create new reading progress entry.

        Args:
            progress: ReadingProgress instance to create

        Returns:
            Created progress with populated ID

        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT INTO reading_progress (
                    document_id, chunk_id, completion_percentage, status, progress_type,
                    total_time_spent, session_count, last_read_date, first_read_date,
                    current_page, total_pages, current_position, average_session_time,
                    reading_speed_wpm, focus_score, notes, goals, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress.document_id,
                progress.chunk_id,
                progress.completion_percentage,
                progress.status.value,
                progress.progress_type.value,
                progress.total_time_spent,
                progress.session_count,
                progress.last_read_date.isoformat() if progress.last_read_date else None,
                progress.first_read_date.isoformat() if progress.first_read_date else None,
                progress.current_page,
                progress.total_pages,
                progress.current_position,
                progress.average_session_time,
                progress.reading_speed_wpm,
                progress.focus_score,
                progress.notes,
                progress.goals,
                progress.created_at.isoformat() if progress.created_at else None,
                progress.updated_at.isoformat() if progress.updated_at else None
            ))

            progress.id = cursor.lastrowid
            self.db.commit()

            self._logger.info(f"Created reading progress: {progress.id} for document {progress.document_id}")
            return progress

        except sqlite3.Error as e:
            self._logger.error(f"Failed to create reading progress: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, progress_id: int) -> Optional[ReadingProgress]:
        """
        Retrieve reading progress by ID.

        Args:
            progress_id: Progress entry ID

        Returns:
            ReadingProgress instance or None if not found
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM reading_progress WHERE id = ?", (progress_id,))
            row = cursor.fetchone()

            return self._row_to_model(row) if row else None

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get reading progress {progress_id}: {e}")
            raise

    def update(self, progress: ReadingProgress) -> ReadingProgress:
        """
        Update existing reading progress.

        Args:
            progress: ReadingProgress instance with updates

        Returns:
            Updated progress instance

        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                UPDATE reading_progress SET
                    completion_percentage = ?, status = ?, progress_type = ?,
                    total_time_spent = ?, session_count = ?, last_read_date = ?,
                    first_read_date = ?, current_page = ?, total_pages = ?,
                    current_position = ?, average_session_time = ?, reading_speed_wpm = ?,
                    focus_score = ?, notes = ?, goals = ?, updated_at = ?
                WHERE id = ?
            """, (
                progress.completion_percentage,
                progress.status.value,
                progress.progress_type.value,
                progress.total_time_spent,
                progress.session_count,
                progress.last_read_date.isoformat() if progress.last_read_date else None,
                progress.first_read_date.isoformat() if progress.first_read_date else None,
                progress.current_page,
                progress.total_pages,
                progress.current_position,
                progress.average_session_time,
                progress.reading_speed_wpm,
                progress.focus_score,
                progress.notes,
                progress.goals,
                progress.updated_at.isoformat() if progress.updated_at else None,
                progress.id
            ))

            self.db.commit()

            self._logger.debug(f"Updated reading progress: {progress.id}")
            return progress

        except sqlite3.Error as e:
            self._logger.error(f"Failed to update reading progress {progress.id}: {e}")
            self.db.rollback()
            raise

    def delete(self, progress_id: int) -> bool:
        """
        Delete reading progress entry.

        Args:
            progress_id: Progress entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM reading_progress WHERE id = ?", (progress_id,))
            self.db.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                self._logger.info(f"Deleted reading progress: {progress_id}")

            return deleted

        except sqlite3.Error as e:
            self._logger.error(f"Failed to delete reading progress {progress_id}: {e}")
            self.db.rollback()
            raise

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[ReadingProgress]:
        """
        List reading progress entries with optional filters.

        Args:
            filters: Optional filters dictionary
                - document_id: Filter by document ID
                - chunk_id: Filter by chunk ID (None for document-level)
                - status: Filter by progress status
                - progress_type: Filter by progress type
                - min_completion: Minimum completion percentage
                - max_completion: Maximum completion percentage
                - date_from: Filter by last read date from
                - date_to: Filter by last read date to
                - limit: Maximum number of results
                - order_by: Ordering field (default: updated_at DESC)

        Returns:
            List of ReadingProgress instances
        """
        try:
            cursor = self.db.cursor()

            query = "SELECT * FROM reading_progress WHERE 1=1"
            params = []

            if filters:
                if "document_id" in filters:
                    query += " AND document_id = ?"
                    params.append(filters["document_id"])

                if "chunk_id" in filters:
                    if filters["chunk_id"] is None:
                        query += " AND chunk_id IS NULL"
                    else:
                        query += " AND chunk_id = ?"
                        params.append(filters["chunk_id"])

                if "status" in filters:
                    query += " AND status = ?"
                    params.append(filters["status"])

                if "progress_type" in filters:
                    query += " AND progress_type = ?"
                    params.append(filters["progress_type"])

                if "min_completion" in filters:
                    query += " AND completion_percentage >= ?"
                    params.append(filters["min_completion"])

                if "max_completion" in filters:
                    query += " AND completion_percentage <= ?"
                    params.append(filters["max_completion"])

                if "date_from" in filters:
                    query += " AND last_read_date >= ?"
                    params.append(filters["date_from"])

                if "date_to" in filters:
                    query += " AND last_read_date <= ?"
                    params.append(filters["date_to"])

            # Default ordering
            order_by = filters.get("order_by", "updated_at DESC") if filters else "updated_at DESC"
            query += f" ORDER BY {order_by}"

            # Limit results
            if filters and "limit" in filters:
                query += " LIMIT ?"
                params.append(filters["limit"])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

        except sqlite3.Error as e:
            self._logger.error(f"Failed to list reading progress: {e}")
            raise

    def get_by_document(self, document_id: int) -> List[ReadingProgress]:
        """
        Get all progress entries for a document (document-level and chunk-level).

        Args:
            document_id: Document ID to get progress for

        Returns:
            List of ReadingProgress instances for the document
        """
        return self.list_all({"document_id": document_id})

    def get_document_progress(self, document_id: int) -> Optional[ReadingProgress]:
        """
        Get document-level progress (chunk_id is NULL).

        Args:
            document_id: Document ID

        Returns:
            Document-level ReadingProgress or None if not found
        """
        results = self.list_all({
            "document_id": document_id,
            "chunk_id": None,
            "limit": 1
        })

        return results[0] if results else None

    def get_chunk_progress(self, document_id: int, chunk_id: int) -> Optional[ReadingProgress]:
        """
        Get chunk-level progress.

        Args:
            document_id: Document ID
            chunk_id: Chunk ID

        Returns:
            Chunk-level ReadingProgress or None if not found
        """
        results = self.list_all({
            "document_id": document_id,
            "chunk_id": chunk_id,
            "limit": 1
        })

        return results[0] if results else None

    def get_recent_progress(self, days: int = 7, limit: int = 20) -> List[ReadingProgress]:
        """
        Get recently updated progress entries.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recently updated ReadingProgress instances
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        return self.list_all({
            "date_from": cutoff_date,
            "limit": limit,
            "order_by": "last_read_date DESC"
        })

    def get_incomplete_progress(self, limit: int = 50) -> List[ReadingProgress]:
        """
        Get progress entries that are not completed.

        Args:
            limit: Maximum number of results

        Returns:
            List of incomplete ReadingProgress instances
        """
        return self.list_all({
            "max_completion": 99.9,  # Less than 100%
            "limit": limit,
            "order_by": "last_read_date DESC"
        })

    def get_completed_progress(
        self,
        date_from: Optional[str] = None,
        limit: int = 50
    ) -> List[ReadingProgress]:
        """
        Get completed progress entries.

        Args:
            date_from: Optional date filter (ISO format)
            limit: Maximum number of results

        Returns:
            List of completed ReadingProgress instances
        """
        filters = {
            "min_completion": 100.0,
            "limit": limit,
            "order_by": "updated_at DESC"
        }

        if date_from:
            filters["date_from"] = date_from

        return self.list_all(filters)

    def get_progress_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive progress statistics.

        Returns:
            Dictionary with progress analytics and statistics
        """
        try:
            cursor = self.db.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM reading_progress")
            total_entries = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reading_progress WHERE completion_percentage >= 100.0")
            completed_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reading_progress WHERE completion_percentage > 0 AND completion_percentage < 100.0")
            in_progress_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reading_progress WHERE completion_percentage = 0")
            not_started_count = cursor.fetchone()[0]

            # Averages
            cursor.execute("SELECT AVG(completion_percentage) FROM reading_progress WHERE completion_percentage > 0")
            avg_completion = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT AVG(total_time_spent) FROM reading_progress WHERE total_time_spent > 0")
            avg_time_spent = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT AVG(session_count) FROM reading_progress WHERE session_count > 0")
            avg_sessions = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT AVG(reading_speed_wpm) FROM reading_progress WHERE reading_speed_wpm IS NOT NULL")
            avg_reading_speed = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(focus_score) FROM reading_progress WHERE focus_score IS NOT NULL")
            avg_focus_score = cursor.fetchone()[0]

            # Totals
            cursor.execute("SELECT SUM(total_time_spent) FROM reading_progress")
            total_time_spent = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(session_count) FROM reading_progress")
            total_sessions = cursor.fetchone()[0] or 0

            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM reading_progress WHERE last_read_date >= ?",
                (week_ago,)
            )
            active_last_week = cursor.fetchone()[0]

            # Progress by type
            cursor.execute("""
                SELECT progress_type, COUNT(*), AVG(completion_percentage)
                FROM reading_progress
                GROUP BY progress_type
            """)
            progress_by_type = {}
            for row in cursor.fetchall():
                progress_by_type[row[0]] = {
                    "count": row[1],
                    "avg_completion": round(row[2] or 0.0, 2)
                }

            # Document vs chunk progress
            cursor.execute("SELECT COUNT(*) FROM reading_progress WHERE chunk_id IS NULL")
            document_level_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reading_progress WHERE chunk_id IS NOT NULL")
            chunk_level_count = cursor.fetchone()[0]

            return {
                "total_entries": total_entries,
                "completed_count": completed_count,
                "in_progress_count": in_progress_count,
                "not_started_count": not_started_count,
                "completion_rate": round((completed_count / total_entries * 100) if total_entries > 0 else 0.0, 2),

                "averages": {
                    "completion_percentage": round(avg_completion, 2),
                    "time_spent_seconds": int(avg_time_spent),
                    "time_spent_formatted": self._format_duration(int(avg_time_spent)),
                    "sessions_per_entry": round(avg_sessions, 1),
                    "reading_speed_wpm": round(avg_reading_speed, 1) if avg_reading_speed else None,
                    "focus_score": round(avg_focus_score, 3) if avg_focus_score else None
                },

                "totals": {
                    "time_spent_seconds": total_time_spent,
                    "time_spent_formatted": self._format_duration(total_time_spent),
                    "total_sessions": total_sessions
                },

                "activity": {
                    "active_last_week": active_last_week,
                    "activity_rate": round((active_last_week / total_entries * 100) if total_entries > 0 else 0.0, 2)
                },

                "breakdown": {
                    "by_type": progress_by_type,
                    "document_level": document_level_count,
                    "chunk_level": chunk_level_count
                }
            }

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get progress statistics: {e}")
            raise

    def get_user_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get user-focused analytics for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with user analytics data
        """
        try:
            cursor = self.db.cursor()

            # Date range
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Reading streak calculation (simplified)
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(last_read_date))
                FROM reading_progress
                WHERE last_read_date >= ?
            """, (start_date,))
            active_days = cursor.fetchone()[0]

            # Most productive time analysis would require session data
            # For now, return basic analytics

            # Progress made in period
            cursor.execute("""
                SELECT
                    COUNT(*) as entries_updated,
                    SUM(total_time_spent) as total_time,
                    AVG(completion_percentage) as avg_completion,
                    SUM(session_count) as total_sessions
                FROM reading_progress
                WHERE updated_at >= ?
            """, (start_date,))

            row = cursor.fetchone()
            entries_updated = row[0]
            period_time = row[1] or 0
            avg_completion = row[2] or 0.0
            period_sessions = row[3] or 0

            # Reading goals achievement (simplified)
            cursor.execute("""
                SELECT COUNT(*)
                FROM reading_progress
                WHERE completion_percentage >= 100.0
                AND updated_at >= ?
            """, (start_date,))
            completed_in_period = cursor.fetchone()[0]

            return {
                "period_days": days,
                "active_days": active_days,
                "consistency_rate": round((active_days / days * 100) if days > 0 else 0.0, 2),

                "progress_made": {
                    "entries_updated": entries_updated,
                    "total_time_seconds": period_time,
                    "total_time_formatted": self._format_duration(period_time),
                    "avg_completion": round(avg_completion, 2),
                    "total_sessions": period_sessions,
                    "completed_items": completed_in_period
                },

                "daily_averages": {
                    "time_per_day": round(period_time / days, 0) if days > 0 else 0,
                    "time_per_day_formatted": self._format_duration(int(period_time / days)) if days > 0 else "0s",
                    "sessions_per_day": round(period_sessions / days, 1) if days > 0 else 0.0
                }
            }

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get user analytics: {e}")
            raise

    def delete_by_document(self, document_id: int) -> int:
        """
        Delete all progress entries for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of entries deleted
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM reading_progress WHERE document_id = ?", (document_id,))
            self.db.commit()

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self._logger.info(f"Deleted {deleted_count} progress entries for document {document_id}")

            return deleted_count

        except sqlite3.Error as e:
            self._logger.error(f"Failed to delete progress for document {document_id}: {e}")
            self.db.rollback()
            raise

    def _row_to_model(self, row: tuple) -> ReadingProgress:
        """
        Convert database row to ReadingProgress model.

        Args:
            row: Database row tuple

        Returns:
            ReadingProgress instance
        """
        # Parse datetime fields
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            if dt_str:
                try:
                    return datetime.fromisoformat(dt_str)
                except ValueError:
                    return None
            return None

        return ReadingProgress(
            id=row[0],
            document_id=row[1],
            chunk_id=row[2],
            completion_percentage=row[3],
            status=ProgressStatus(row[4]),
            progress_type=ProgressType(row[5]),
            total_time_spent=row[6],
            session_count=row[7],
            last_read_date=parse_datetime(row[8]),
            first_read_date=parse_datetime(row[9]),
            current_page=row[10],
            total_pages=row[11],
            current_position=row[12],
            average_session_time=row[13],
            reading_speed_wpm=row[14],
            focus_score=row[15],
            notes=row[16],
            goals=row[17],
            created_at=parse_datetime(row[18]),
            updated_at=parse_datetime(row[19])
        )

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds <= 0:
            return "0s"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
        else:
            return f"{secs}s"
