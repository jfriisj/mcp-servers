"""
Session Repository for Study Buddy MCP Server.

This module implements SessionRepository, handling data access operations
for study sessions with lifecycle management and analytics
for Task 14 Phase 3.

Architecture: Clean Architecture Layer 3 (Data Access)
Dependencies: DatabaseConnection (Layer 4), StudySession model (Layer 4)
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..database.connection import DatabaseConnection
from ..models.study_session import SessionStatus, SessionType, StudySession

from ..repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SessionRepository(BaseRepository[StudySession]):
    """
    Repository for study session data access operations.

    Provides specialized queries for session management, analytics,
    and lifecycle operations following repository pattern and SRP.

    Responsibilities:
    - CRUD operations for study sessions
    - Session lifecycle management (start, pause, resume, end)
    - Session analytics and statistics
    - Time-based queries and filtering

    Does NOT:
    - Contain business logic (service responsibility)
    - Handle MCP protocol (handler responsibility)
    - Manage UI state (widget responsibility)
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize session repository.

        Args:
            db: Database connection instance
        """
        self.db = db
        self._logger = logging.getLogger(f"{__name__}.SessionRepository")

    def create(self, session: StudySession) -> StudySession:
        """
        Create new study session entry.

        Args:
            session: StudySession instance to create

        Returns:
            Created session with populated ID

        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT INTO study_sessions (
                    document_id, chunk_id, start_time, end_time, planned_duration,
                    actual_duration, session_type, status, start_page, end_page,
                    start_position, end_position, focus_score, productivity_score,
                    interruption_count, goals, notes, achievements, challenges,
                    words_read, pages_read, concepts_learned, questions_raised,
                    tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.document_id,
                session.chunk_id,
                session.start_time.isoformat() if session.start_time else None,
                session.end_time.isoformat() if session.end_time else None,
                session.planned_duration,
                session.actual_duration,
                session.session_type.value,
                session.status.value,
                session.start_page,
                session.end_page,
                session.start_position,
                session.end_position,
                session.focus_score,
                session.productivity_score,
                session.interruption_count,
                session.goals,
                session.notes,
                session.achievements,
                session.challenges,
                session.words_read,
                session.pages_read,
                session.concepts_learned,
                session.questions_raised,
                json.dumps(session.tags) if session.tags else None,
                session.created_at.isoformat() if session.created_at else None,
                session.updated_at.isoformat() if session.updated_at else None
            ))

            session.id = cursor.lastrowid
            self.db.commit()

            self._logger.info(f"Created study session: {session.id} for document {session.document_id}")
            return session

        except sqlite3.Error as e:
            self._logger.error(f"Failed to create study session: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, session_id: int) -> Optional[StudySession]:
        """
        Retrieve study session by ID.

        Args:
            session_id: Session ID

        Returns:
            StudySession instance or None if not found
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM study_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()

            return self._row_to_model(row) if row else None

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get study session {session_id}: {e}")
            raise

    def update(self, session: StudySession) -> StudySession:
        """
        Update existing study session.

        Args:
            session: StudySession instance with updates

        Returns:
            Updated session instance

        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                UPDATE study_sessions SET
                    start_time = ?, end_time = ?, planned_duration = ?, actual_duration = ?,
                    session_type = ?, status = ?, start_page = ?, end_page = ?,
                    start_position = ?, end_position = ?, focus_score = ?, productivity_score = ?,
                    interruption_count = ?, goals = ?, notes = ?, achievements = ?, challenges = ?,
                    words_read = ?, pages_read = ?, concepts_learned = ?, questions_raised = ?,
                    tags = ?, updated_at = ?
                WHERE id = ?
            """, (
                session.start_time.isoformat() if session.start_time else None,
                session.end_time.isoformat() if session.end_time else None,
                session.planned_duration,
                session.actual_duration,
                session.session_type.value,
                session.status.value,
                session.start_page,
                session.end_page,
                session.start_position,
                session.end_position,
                session.focus_score,
                session.productivity_score,
                session.interruption_count,
                session.goals,
                session.notes,
                session.achievements,
                session.challenges,
                session.words_read,
                session.pages_read,
                session.concepts_learned,
                session.questions_raised,
                json.dumps(session.tags) if session.tags else None,
                session.updated_at.isoformat() if session.updated_at else None,
                session.id
            ))

            self.db.commit()

            self._logger.debug(f"Updated study session: {session.id}")
            return session

        except sqlite3.Error as e:
            self._logger.error(f"Failed to update study session {session.id}: {e}")
            self.db.rollback()
            raise

    def delete(self, session_id: int) -> bool:
        """
        Delete study session entry.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM study_sessions WHERE id = ?", (session_id,))
            self.db.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                self._logger.info(f"Deleted study session: {session_id}")

            return deleted

        except sqlite3.Error as e:
            self._logger.error(f"Failed to delete study session {session_id}: {e}")
            self.db.rollback()
            raise

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[StudySession]:
        """
        List study sessions with optional filters.

        Args:
            filters: Optional filters dictionary
                - document_id: Filter by document ID
                - chunk_id: Filter by chunk ID (None for document-level)
                - status: Filter by session status
                - session_type: Filter by session type
                - date_from: Filter by start date from
                - date_to: Filter by start date to
                - active_only: Filter only active/paused sessions
                - completed_only: Filter only completed sessions
                - limit: Maximum number of results
                - order_by: Ordering field (default: start_time DESC)

        Returns:
            List of StudySession instances
        """
        try:
            cursor = self.db.cursor()

            query = "SELECT * FROM study_sessions WHERE 1=1"
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

                if "session_type" in filters:
                    query += " AND session_type = ?"
                    params.append(filters["session_type"])

                if "date_from" in filters:
                    query += " AND start_time >= ?"
                    params.append(filters["date_from"])

                if "date_to" in filters:
                    query += " AND start_time <= ?"
                    params.append(filters["date_to"])

                if filters.get("active_only"):
                    query += " AND status IN ('active', 'paused')"

                if filters.get("completed_only"):
                    query += " AND status = 'completed'"

            # Default ordering
            order_by = filters.get("order_by", "start_time DESC") if filters else "start_time DESC"
            query += f" ORDER BY {order_by}"

            # Limit results
            if filters and "limit" in filters:
                query += " LIMIT ?"
                params.append(filters["limit"])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

        except sqlite3.Error as e:
            self._logger.error(f"Failed to list study sessions: {e}")
            raise

    def get_by_document(self, document_id: int) -> List[StudySession]:
        """
        Get all sessions for a document.

        Args:
            document_id: Document ID to get sessions for

        Returns:
            List of StudySession instances for the document
        """
        return self.list_all({"document_id": document_id})

    def get_active_sessions(self) -> List[StudySession]:
        """
        Get all currently active or paused sessions.

        Returns:
            List of active/paused StudySession instances
        """
        return self.list_all({"active_only": True})

    def get_recent_sessions(self, days: int = 7, limit: int = 20) -> List[StudySession]:
        """
        Get recent study sessions.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent StudySession instances
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        return self.list_all({
            "date_from": cutoff_date,
            "limit": limit,
            "order_by": "start_time DESC"
        })

    def get_completed_sessions(
        self,
        date_from: Optional[str] = None,
        limit: int = 50
    ) -> List[StudySession]:
        """
        Get completed study sessions.

        Args:
            date_from: Optional date filter (ISO format)
            limit: Maximum number of results

        Returns:
            List of completed StudySession instances
        """
        filters = {
            "completed_only": True,
            "limit": limit,
            "order_by": "end_time DESC"
        }

        if date_from:
            filters["date_from"] = date_from

        return self.list_all(filters)

    def get_sessions_by_type(self, session_type: SessionType) -> List[StudySession]:
        """
        Get sessions by type.

        Args:
            session_type: Type of sessions to retrieve

        Returns:
            List of StudySession instances of the specified type
        """
        return self.list_all({"session_type": session_type.value})

    def get_daily_sessions(self, date: str) -> List[StudySession]:
        """
        Get all sessions for a specific day.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of StudySession instances for the day
        """
        start_date = f"{date}T00:00:00"
        end_date = f"{date}T23:59:59"

        return self.list_all({
            "date_from": start_date,
            "date_to": end_date,
            "order_by": "start_time ASC"
        })

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.

        Returns:
            Dictionary with session analytics and statistics
        """
        try:
            cursor = self.db.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM study_sessions")
            total_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM study_sessions WHERE status = 'completed'")
            completed_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM study_sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM study_sessions WHERE status = 'paused'")
            paused_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM study_sessions WHERE status = 'cancelled'")
            cancelled_sessions = cursor.fetchone()[0]

            # Time statistics (completed sessions only)
            cursor.execute("SELECT AVG(actual_duration) FROM study_sessions WHERE actual_duration IS NOT NULL")
            avg_duration = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(actual_duration) FROM study_sessions WHERE actual_duration IS NOT NULL")
            total_time = cursor.fetchone()[0] or 0

            cursor.execute("SELECT MAX(actual_duration) FROM study_sessions WHERE actual_duration IS NOT NULL")
            max_duration = cursor.fetchone()[0] or 0

            cursor.execute("SELECT MIN(actual_duration) FROM study_sessions WHERE actual_duration IS NOT NULL")
            min_duration = cursor.fetchone()[0] or 0

            # Quality metrics
            cursor.execute("SELECT AVG(focus_score) FROM study_sessions WHERE focus_score IS NOT NULL")
            avg_focus_score = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(productivity_score) FROM study_sessions WHERE productivity_score IS NOT NULL")
            avg_productivity = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(interruption_count) FROM study_sessions WHERE status = 'completed'")
            avg_interruptions = cursor.fetchone()[0] or 0

            # Content metrics
            cursor.execute("SELECT SUM(pages_read) FROM study_sessions WHERE pages_read IS NOT NULL")
            total_pages_read = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(words_read) FROM study_sessions WHERE words_read IS NOT NULL")
            total_words_read = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(words_read) FROM study_sessions WHERE words_read IS NOT NULL AND actual_duration IS NOT NULL AND actual_duration > 0")
            avg_words_per_session = cursor.fetchone()[0] or 0

            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM study_sessions WHERE start_time >= ?",
                (week_ago,)
            )
            recent_sessions = cursor.fetchone()[0]

            # Sessions by type
            cursor.execute("""
                SELECT session_type, COUNT(*), AVG(actual_duration), AVG(focus_score)
                FROM study_sessions
                WHERE status = 'completed'
                GROUP BY session_type
            """)
            sessions_by_type = {}
            for row in cursor.fetchall():
                sessions_by_type[row[0]] = {
                    "count": row[1],
                    "avg_duration": int(row[2]) if row[2] else 0,
                    "avg_focus_score": round(row[3], 3) if row[3] else None
                }

            # Daily average (last 30 days)
            month_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM study_sessions WHERE start_time >= ?",
                (month_ago,)
            )
            monthly_sessions = cursor.fetchone()[0]
            daily_average = monthly_sessions / 30.0 if monthly_sessions > 0 else 0.0

            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "active_sessions": active_sessions,
                "paused_sessions": paused_sessions,
                "cancelled_sessions": cancelled_sessions,
                "completion_rate": round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0.0, 2),

                "time_statistics": {
                    "total_time_seconds": total_time,
                    "total_time_formatted": self._format_duration(total_time),
                    "average_duration_seconds": int(avg_duration),
                    "average_duration_formatted": self._format_duration(int(avg_duration)),
                    "max_duration_seconds": max_duration,
                    "max_duration_formatted": self._format_duration(max_duration),
                    "min_duration_seconds": min_duration,
                    "min_duration_formatted": self._format_duration(min_duration)
                },

                "quality_metrics": {
                    "average_focus_score": round(avg_focus_score, 3) if avg_focus_score else None,
                    "average_productivity_score": round(avg_productivity, 3) if avg_productivity else None,
                    "average_interruptions": round(avg_interruptions, 1)
                },

                "content_metrics": {
                    "total_pages_read": total_pages_read,
                    "total_words_read": total_words_read,
                    "average_words_per_session": int(avg_words_per_session)
                },

                "activity": {
                    "recent_sessions_7_days": recent_sessions,
                    "monthly_sessions": monthly_sessions,
                    "daily_average": round(daily_average, 2)
                },

                "breakdown": {
                    "by_type": sessions_by_type
                }
            }

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get session statistics: {e}")
            raise

    def get_productivity_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get productivity-focused analytics for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with productivity analytics data
        """
        try:
            cursor = self.db.cursor()

            # Date range
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Productivity trends
            cursor.execute("""
                SELECT
                    DATE(start_time) as session_date,
                    COUNT(*) as session_count,
                    SUM(actual_duration) as total_time,
                    AVG(focus_score) as avg_focus,
                    AVG(productivity_score) as avg_productivity,
                    SUM(interruption_count) as total_interruptions
                FROM study_sessions
                WHERE start_time >= ? AND status = 'completed'
                GROUP BY DATE(start_time)
                ORDER BY session_date
            """, (start_date,))

            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    "date": row[0],
                    "session_count": row[1],
                    "total_time_seconds": row[2] or 0,
                    "total_time_formatted": self._format_duration(row[2] or 0),
                    "avg_focus_score": round(row[3], 3) if row[3] else None,
                    "avg_productivity_score": round(row[4], 3) if row[4] else None,
                    "total_interruptions": row[5] or 0
                })

            # Best and worst performance days
            if daily_stats:
                best_focus_day = max(daily_stats, key=lambda x: x["avg_focus_score"] or 0)
                best_productivity_day = max(daily_stats, key=lambda x: x["avg_productivity_score"] or 0)
                most_productive_time = max(daily_stats, key=lambda x: x["total_time_seconds"])
            else:
                best_focus_day = best_productivity_day = most_productive_time = None

            # Time of day analysis (hour of start_time)
            cursor.execute("""
                SELECT
                    strftime('%H', start_time) as hour,
                    COUNT(*) as session_count,
                    AVG(focus_score) as avg_focus,
                    AVG(actual_duration) as avg_duration
                FROM study_sessions
                WHERE start_time >= ? AND status = 'completed'
                GROUP BY strftime('%H', start_time)
                ORDER BY hour
            """, (start_date,))

            hourly_patterns = {}
            for row in cursor.fetchall():
                hour = int(row[0])
                hourly_patterns[hour] = {
                    "session_count": row[1],
                    "avg_focus_score": round(row[2], 3) if row[2] else None,
                    "avg_duration_seconds": int(row[3]) if row[3] else 0,
                    "avg_duration_formatted": self._format_duration(int(row[3])) if row[3] else "0s"
                }

            return {
                "period_days": days,
                "daily_statistics": daily_stats,
                "best_performance": {
                    "best_focus_day": best_focus_day,
                    "best_productivity_day": best_productivity_day,
                    "most_productive_time_day": most_productive_time
                },
                "time_patterns": {
                    "hourly_breakdown": hourly_patterns
                }
            }

        except sqlite3.Error as e:
            self._logger.error(f"Failed to get productivity analytics: {e}")
            raise

    def delete_by_document(self, document_id: int) -> int:
        """
        Delete all sessions for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of sessions deleted
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM study_sessions WHERE document_id = ?", (document_id,))
            self.db.commit()

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self._logger.info(f"Deleted {deleted_count} sessions for document {document_id}")

            return deleted_count

        except sqlite3.Error as e:
            self._logger.error(f"Failed to delete sessions for document {document_id}: {e}")
            self.db.rollback()
            raise

    def end_all_active_sessions(self, reason: str = "Force ended") -> int:
        """
        End all currently active or paused sessions.

        Args:
            reason: Reason for ending sessions

        Returns:
            Number of sessions ended
        """
        try:
            cursor = self.db.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                UPDATE study_sessions
                SET status = 'cancelled', end_time = ?, notes = COALESCE(notes, '') || ?
                WHERE status IN ('active', 'paused')
            """, (now, f"\n\n{reason}"))

            self.db.commit()

            ended_count = cursor.rowcount
            if ended_count > 0:
                self._logger.info(f"Force ended {ended_count} active sessions")

            return ended_count

        except sqlite3.Error as e:
            self._logger.error(f"Failed to end active sessions: {e}")
            self.db.rollback()
            raise

    def _row_to_model(self, row: tuple) -> StudySession:
        """
        Convert database row to StudySession model.

        Args:
            row: Database row tuple

        Returns:
            StudySession instance
        """
        # Parse datetime fields
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            if dt_str:
                try:
                    return datetime.fromisoformat(dt_str)
                except ValueError:
                    return None
            return None

        # Parse tags JSON
        def parse_tags(tags_str: Optional[str]) -> Optional[List[str]]:
            if tags_str:
                try:
                    return json.loads(tags_str)
                except (json.JSONDecodeError, TypeError):
                    return None
            return None

        return StudySession(
            id=row[0],
            document_id=row[1],
            chunk_id=row[2],
            start_time=parse_datetime(row[3]),
            end_time=parse_datetime(row[4]),
            planned_duration=row[5],
            actual_duration=row[6],
            session_type=SessionType(row[7]),
            status=SessionStatus(row[8]),
            start_page=row[9],
            end_page=row[10],
            start_position=row[11],
            end_position=row[12],
            focus_score=row[13],
            productivity_score=row[14],
            interruption_count=row[15],
            goals=row[16],
            notes=row[17],
            achievements=row[18],
            challenges=row[19],
            words_read=row[20],
            pages_read=row[21],
            concepts_learned=row[22],
            questions_raised=row[23],
            tags=parse_tags(row[24]),
            created_at=parse_datetime(row[25]),
            updated_at=parse_datetime(row[26])
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
