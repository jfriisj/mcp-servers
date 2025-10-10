"""
Progress Service for Study Buddy MCP Server.

This module implements ProgressService, orchestrating progress tracking
and study session management with business rules validation
for Task 14 Phase 3.

Architecture: Clean Architecture Layer 2 (Business Logic)
Dependencies: Repository interfaces (Layer 3), Domain models (Layer 4)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models.reading_progress import ReadingProgress
from ..models.study_session import SessionStatus, SessionType, StudySession
from ..repositories.chunk_repository import ChunkRepository
from ..repositories.document_repository import DocumentRepository
from ..repositories.progress_repository import ProgressRepository
from ..repositories.session_repository import SessionRepository

logger = logging.getLogger(__name__)


class ProgressService:
    """
    Business logic service for progress tracking and session management.

    Orchestrates progress tracking operations across repositories
    while enforcing business rules and validation for Task 14 Phase 3.

    Responsibilities:
    - Progress tracking business logic and validation
    - Session lifecycle management (start, pause, resume, end)
    - Progress analytics and reporting
    - Cross-document progress coordination
    - Business rule enforcement

    Does NOT:
    - Handle MCP protocol details (handler responsibility)
    - Access database directly (repository responsibility)
    - Manage UI state (widget responsibility)
    - Parse document content (parser responsibility)
    """

    def __init__(
        self,
        progress_repo: ProgressRepository,
        session_repo: SessionRepository,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository
    ):
        """
        Initialize progress service with repository dependencies.

        Args:
            progress_repo: Reading progress repository
            session_repo: Study session repository
            document_repo: Document repository
            chunk_repo: Chunk repository
        """
        self.progress_repo = progress_repo
        self.session_repo = session_repo
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self._logger = logging.getLogger(f"{__name__}.ProgressService")

    # Progress Tracking Operations

    def track_reading_progress(
        self,
        document_id: int,
        chunk_id: Optional[int] = None,
        page: Optional[int] = None,
        position: Optional[int] = None,
        percentage: Optional[float] = None
    ) -> ReadingProgress:
        """
        Track reading progress for document or chunk.

        Business Logic:
        - Validates document/chunk existence
        - Auto-calculates derived progress metrics
        - Updates related session if active
        - Maintains progress history

        Args:
            document_id: Document ID
            chunk_id: Optional chunk ID for chunk-level tracking
            page: Current page number
            position: Current position (character offset)
            percentage: Current completion percentage

        Returns:
            Updated ReadingProgress instance

        Raises:
            ValueError: If document/chunk not found or invalid parameters
        """
        try:
            # Validate document exists
            document = self.document_repo.get_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Validate chunk if specified
            if chunk_id:
                chunk = self.chunk_repo.get_by_id(chunk_id)
                if not chunk:
                    raise ValueError(f"Chunk {chunk_id} not found")
                if chunk.document_id != document_id:
                    raise ValueError(f"Chunk {chunk_id} does not belong to document {document_id}")

            # Get existing progress or create new
            existing_progress = self.progress_repo.get_by_document_and_chunk(document_id, chunk_id)

            if existing_progress:
                # Update existing progress
                progress = existing_progress
                progress.last_read_time = datetime.now()
                progress.updated_at = datetime.now()

                # Update position tracking
                if page is not None:
                    progress.current_page = page
                if position is not None:
                    progress.current_position = position
                if percentage is not None:
                    progress.completion_percentage = max(0.0, min(100.0, percentage))

                # Calculate auto-derived metrics
                self._update_derived_metrics(progress, document)

                # Update in repository
                progress = self.progress_repo.update(progress)

            else:
                # Create new progress entry
                progress = ReadingProgress(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    current_page=page or 1,
                    current_position=position or 0,
                    completion_percentage=percentage or 0.0,
                    first_read_time=datetime.now(),
                    last_read_time=datetime.now(),
                    total_time_spent=0,
                    session_count=0,
                    is_completed=False,
                    notes="",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                # Calculate initial derived metrics
                self._update_derived_metrics(progress, document)

                # Save to repository
                progress = self.progress_repo.create(progress)

            # Update active session with progress
            self._update_active_session_progress(document_id, chunk_id, page, position)

            self._logger.info(
                f"Updated progress for document {document_id}"
                f"{f', chunk {chunk_id}' if chunk_id else ''}: "
                f"{progress.completion_percentage:.1f}%"
            )

            return progress

        except Exception as e:
            self._logger.error(f"Failed to track reading progress: {e}")
            raise

    def mark_completed(
        self,
        document_id: int,
        chunk_id: Optional[int] = None,
        completion_notes: str = ""
    ) -> ReadingProgress:
        """
        Mark document or chunk as completed.

        Business Logic:
        - Sets completion percentage to 100%
        - Records completion timestamp
        - Ends active sessions
        - Updates progress statistics

        Args:
            document_id: Document ID
            chunk_id: Optional chunk ID
            completion_notes: Optional completion notes

        Returns:
            Updated ReadingProgress with completion status
        """
        try:
            progress = self.track_reading_progress(
                document_id=document_id,
                chunk_id=chunk_id,
                percentage=100.0
            )

            # Mark as completed
            progress.is_completed = True
            progress.completion_date = datetime.now()

            # Add completion notes
            if completion_notes:
                progress.notes = (progress.notes or "") + f"\n\nCompleted: {completion_notes}"

            progress = self.progress_repo.update(progress)

            # End any active sessions for this content
            active_sessions = self._get_active_sessions_for_content(document_id, chunk_id)
            for session in active_sessions:
                self.end_study_session(
                    session_id=session.id,
                    status=SessionStatus.COMPLETED,
                    notes="Auto-completed with content completion"
                )

            self._logger.info(
                f"Marked completed: document {document_id}"
                f"{f', chunk {chunk_id}' if chunk_id else ''}"
            )

            return progress

        except Exception as e:
            self._logger.error(f"Failed to mark completed: {e}")
            raise

    def get_reading_progress(
        self,
        document_id: int,
        chunk_id: Optional[int] = None
    ) -> Optional[ReadingProgress]:
        """
        Get reading progress for document or chunk.

        Args:
            document_id: Document ID
            chunk_id: Optional chunk ID

        Returns:
            ReadingProgress instance or None
        """
        return self.progress_repo.get_by_document_and_chunk(document_id, chunk_id)

    def get_document_progress_summary(self, document_id: int) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for a document.

        Args:
            document_id: Document ID

        Returns:
            Dictionary with progress analytics
        """
        try:
            # Get document-level progress
            doc_progress = self.progress_repo.get_by_document_and_chunk(document_id, None)

            # Get all chunk progress
            chunk_progress_list = self.progress_repo.get_by_document(document_id)
            chunk_progress_list = [cp for cp in chunk_progress_list if cp.chunk_id is not None]

            # Get document info
            document = self.document_repo.get_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Calculate aggregated metrics
            total_chunks = len(self.chunk_repo.get_by_document_id(document_id)) if document.indexed else 0
            completed_chunks = len([cp for cp in chunk_progress_list if cp.is_completed])

            # Calculate average progress
            if chunk_progress_list:
                avg_chunk_progress = sum(cp.completion_percentage for cp in chunk_progress_list) / len(chunk_progress_list)
            else:
                avg_chunk_progress = doc_progress.completion_percentage if doc_progress else 0.0

            # Time statistics
            total_reading_time = sum(cp.total_time_spent for cp in chunk_progress_list)
            if doc_progress:
                total_reading_time += doc_progress.total_time_spent

            # Session statistics
            all_sessions = self.session_repo.get_by_document(document_id)
            completed_sessions = [s for s in all_sessions if s.status == SessionStatus.COMPLETED]

            return {
                "document_id": document_id,
                "document_title": document.title,
                "document_indexed": document.indexed,

                "overall_progress": {
                    "completion_percentage": avg_chunk_progress,
                    "is_completed": doc_progress.is_completed if doc_progress else False,
                    "current_page": doc_progress.current_page if doc_progress else None,
                    "total_pages": document.total_pages
                },

                "chunk_progress": {
                    "total_chunks": total_chunks,
                    "completed_chunks": completed_chunks,
                    "completion_rate": (completed_chunks / total_chunks * 100) if total_chunks > 0 else 0.0,
                    "chunks_with_progress": len(chunk_progress_list)
                },

                "time_statistics": {
                    "total_reading_time_seconds": total_reading_time,
                    "total_reading_time_formatted": self._format_duration(total_reading_time),
                    "first_read_time": doc_progress.first_read_time.isoformat() if doc_progress and doc_progress.first_read_time else None,
                    "last_read_time": doc_progress.last_read_time.isoformat() if doc_progress and doc_progress.last_read_time else None
                },

                "session_statistics": {
                    "total_sessions": len(all_sessions),
                    "completed_sessions": len(completed_sessions),
                    "active_sessions": len([s for s in all_sessions if s.status in (SessionStatus.ACTIVE, SessionStatus.PAUSED)]),
                    "avg_session_duration": int(sum(s.actual_duration for s in completed_sessions if s.actual_duration) / len(completed_sessions)) if completed_sessions else 0
                }
            }

        except Exception as e:
            self._logger.error(f"Failed to get document progress summary: {e}")
            raise

    # Study Session Management

    def start_study_session(
        self,
        document_id: int,
        chunk_id: Optional[int] = None,
        session_type: SessionType = SessionType.READING,
        planned_duration: Optional[int] = None,
        goals: str = "",
        start_page: Optional[int] = None,
        start_position: Optional[int] = None
    ) -> StudySession:
        """
        Start a new study session.

        Business Logic:
        - Validates document/chunk existence
        - Ends conflicting active sessions (business rule: one active session per user)
        - Creates session with proper initialization
        - Updates progress tracking

        Args:
            document_id: Document ID
            chunk_id: Optional chunk ID for chunk-specific session
            session_type: Type of session
            planned_duration: Planned duration in seconds
            goals: Session goals description
            start_page: Starting page number
            start_position: Starting position

        Returns:
            Created StudySession instance
        """
        try:
            # Validate document exists
            document = self.document_repo.get_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Validate chunk if specified
            if chunk_id:
                chunk = self.chunk_repo.get_by_id(chunk_id)
                if not chunk:
                    raise ValueError(f"Chunk {chunk_id} not found")
                if chunk.document_id != document_id:
                    raise ValueError(f"Chunk {chunk_id} does not belong to document {document_id}")

            # Business rule: End any other active sessions (one active session policy)
            active_sessions = self.session_repo.get_active_sessions()
            for active_session in active_sessions:
                self._logger.info(f"Auto-pausing active session {active_session.id} to start new session")
                self.pause_study_session(
                    session_id=active_session.id,
                    notes="Auto-paused for new session"
                )

            # Get current progress for position initialization
            current_progress = self.progress_repo.get_by_document_and_chunk(document_id, chunk_id)
            if current_progress and not start_page and not start_position:
                start_page = current_progress.current_page
                start_position = current_progress.current_position

            # Create new session
            session = StudySession(
                document_id=document_id,
                chunk_id=chunk_id,
                start_time=datetime.now(),
                planned_duration=planned_duration,
                session_type=session_type,
                status=SessionStatus.ACTIVE,
                start_page=start_page or 1,
                start_position=start_position or 0,
                goals=goals,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            session = self.session_repo.create(session)

            self._logger.info(
                f"Started {session_type.value} session {session.id} "
                f"for document {document_id}"
                f"{f', chunk {chunk_id}' if chunk_id else ''}"
            )

            return session

        except Exception as e:
            self._logger.error(f"Failed to start study session: {e}")
            raise

    def pause_study_session(
        self,
        session_id: int,
        notes: str = ""
    ) -> StudySession:
        """
        Pause an active study session.

        Args:
            session_id: Session ID to pause
            notes: Optional pause reason

        Returns:
            Updated StudySession instance
        """
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session.status != SessionStatus.ACTIVE:
                raise ValueError(f"Session {session_id} is not active (status: {session.status.value})")

            # Update session status
            session.status = SessionStatus.PAUSED
            session.updated_at = datetime.now()

            # Add pause notes
            if notes:
                session.notes = (session.notes or "") + f"\n\nPaused: {notes}"

            # Update actual duration if start time exists
            if session.start_time:
                current_duration = int((datetime.now() - session.start_time).total_seconds())
                session.actual_duration = current_duration

            session = self.session_repo.update(session)

            self._logger.info(f"Paused session {session_id}")
            return session

        except Exception as e:
            self._logger.error(f"Failed to pause session: {e}")
            raise

    def resume_study_session(self, session_id: int) -> StudySession:
        """
        Resume a paused study session.

        Args:
            session_id: Session ID to resume

        Returns:
            Updated StudySession instance
        """
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session.status != SessionStatus.PAUSED:
                raise ValueError(f"Session {session_id} is not paused (status: {session.status.value})")

            # Business rule: End any other active sessions
            active_sessions = self.session_repo.get_active_sessions()
            for active_session in active_sessions:
                if active_session.id != session_id:
                    self.pause_study_session(
                        session_id=active_session.id,
                        notes="Auto-paused for resumed session"
                    )

            # Resume session
            session.status = SessionStatus.ACTIVE
            session.updated_at = datetime.now()

            session = self.session_repo.update(session)

            self._logger.info(f"Resumed session {session_id}")
            return session

        except Exception as e:
            self._logger.error(f"Failed to resume session: {e}")
            raise

    def end_study_session(
        self,
        session_id: int,
        status: SessionStatus = SessionStatus.COMPLETED,
        end_page: Optional[int] = None,
        end_position: Optional[int] = None,
        focus_score: Optional[float] = None,
        productivity_score: Optional[float] = None,
        interruption_count: Optional[int] = None,
        achievements: str = "",
        challenges: str = "",
        notes: str = "",
        words_read: Optional[int] = None,
        pages_read: Optional[int] = None,
        concepts_learned: Optional[int] = None,
        questions_raised: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> StudySession:
        """
        End a study session with completion details.

        Args:
            session_id: Session ID to end
            status: Final session status
            end_page: Final page number
            end_position: Final position
            focus_score: Focus rating (1-10)
            productivity_score: Productivity rating (1-10)
            interruption_count: Number of interruptions
            achievements: Session achievements
            challenges: Challenges encountered
            notes: Additional notes
            words_read: Words read during session
            pages_read: Pages read during session
            concepts_learned: Number of concepts learned
            questions_raised: Number of questions raised
            tags: Session tags

        Returns:
            Updated StudySession instance
        """
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session.status not in (SessionStatus.ACTIVE, SessionStatus.PAUSED):
                raise ValueError(f"Session {session_id} cannot be ended (status: {session.status.value})")

            # Update session with completion data
            session.status = status
            session.end_time = datetime.now()
            session.updated_at = datetime.now()

            # Position tracking
            if end_page is not None:
                session.end_page = end_page
            if end_position is not None:
                session.end_position = end_position

            # Quality metrics
            if focus_score is not None:
                session.focus_score = max(1.0, min(10.0, focus_score))
            if productivity_score is not None:
                session.productivity_score = max(1.0, min(10.0, productivity_score))
            if interruption_count is not None:
                session.interruption_count = max(0, interruption_count)

            # Session outcomes
            if achievements:
                session.achievements = achievements
            if challenges:
                session.challenges = challenges
            if notes:
                session.notes = (session.notes or "") + f"\n\n{notes}"

            # Content metrics
            if words_read is not None:
                session.words_read = max(0, words_read)
            if pages_read is not None:
                session.pages_read = max(0, pages_read)
            if concepts_learned is not None:
                session.concepts_learned = max(0, concepts_learned)
            if questions_raised is not None:
                session.questions_raised = max(0, questions_raised)
            if tags:
                session.tags = tags

            # Calculate actual duration
            if session.start_time and session.end_time:
                session.actual_duration = int((session.end_time - session.start_time).total_seconds())

            session = self.session_repo.update(session)

            # Update reading progress if completed successfully
            if status == SessionStatus.COMPLETED and (end_page or end_position):
                try:
                    # Calculate progress percentage based on pages if available
                    percentage = None
                    if end_page and session.document_id:
                        document = self.document_repo.get_by_id(session.document_id)
                        if document and document.total_pages:
                            percentage = min(100.0, (end_page / document.total_pages) * 100)

                    self.track_reading_progress(
                        document_id=session.document_id,
                        chunk_id=session.chunk_id,
                        page=end_page,
                        position=end_position,
                        percentage=percentage
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to update progress after session end: {e}")

            # Update progress statistics
            try:
                self._update_progress_statistics(session)
            except Exception as e:
                self._logger.warning(f"Failed to update progress statistics: {e}")

            self._logger.info(f"Ended session {session_id} with status {status.value}")
            return session

        except Exception as e:
            self._logger.error(f"Failed to end session: {e}")
            raise

    def get_active_sessions(self) -> List[StudySession]:
        """Get all currently active or paused sessions."""
        return self.session_repo.get_active_sessions()

    def get_session_history(
        self,
        document_id: Optional[int] = None,
        days: int = 30,
        limit: int = 50
    ) -> List[StudySession]:
        """
        Get session history with optional filtering.

        Args:
            document_id: Optional document filter
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of StudySession instances
        """
        filters = {
            "limit": limit,
            "order_by": "start_time DESC"
        }

        if document_id:
            filters["document_id"] = document_id

        if days > 0:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            filters["date_from"] = cutoff_date

        return self.session_repo.list_all(filters)

    # Analytics and Reporting

    def get_comprehensive_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics combining progress and session data.

        Args:
            days: Number of days for analytics period

        Returns:
            Dictionary with comprehensive analytics
        """
        try:
            # Get session statistics
            session_stats = self.session_repo.get_session_statistics()

            # Get productivity analytics
            productivity_stats = self.session_repo.get_productivity_analytics(days)

            # Get progress statistics
            progress_stats = self.progress_repo.get_progress_analytics()

            # Get document completion rates
            all_progress = self.progress_repo.list_all()
            documents_with_progress = {p.document_id for p in all_progress}
            completed_documents = len([p for p in all_progress if p.is_completed and p.chunk_id is None])

            # Calculate reading velocity (pages per hour)
            recent_sessions = self.session_repo.get_recent_sessions(days)
            completed_recent = [s for s in recent_sessions if s.status == SessionStatus.COMPLETED and s.actual_duration and s.pages_read]

            if completed_recent:
                total_pages = sum(s.pages_read for s in completed_recent)
                total_hours = sum(s.actual_duration for s in completed_recent) / 3600
                pages_per_hour = total_pages / total_hours if total_hours > 0 else 0
            else:
                pages_per_hour = 0

            return {
                "analytics_period_days": days,
                "generated_at": datetime.now().isoformat(),

                "session_analytics": session_stats,
                "productivity_analytics": productivity_stats,
                "progress_analytics": progress_stats,

                "reading_velocity": {
                    "pages_per_hour": round(pages_per_hour, 2),
                    "sessions_analyzed": len(completed_recent)
                },

                "completion_metrics": {
                    "documents_with_progress": len(documents_with_progress),
                    "completed_documents": completed_documents,
                    "completion_rate": round((completed_documents / len(documents_with_progress) * 100) if documents_with_progress else 0.0, 2)
                }
            }

        except Exception as e:
            self._logger.error(f"Failed to get comprehensive analytics: {e}")
            raise

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """
        Get summary of progress and sessions for a specific day.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Dictionary with daily summary
        """
        try:
            # Get sessions for the day
            daily_sessions = self.session_repo.get_daily_sessions(date)
            completed_sessions = [s for s in daily_sessions if s.status == SessionStatus.COMPLETED]

            # Calculate time spent
            total_time = sum(s.actual_duration for s in completed_sessions if s.actual_duration)

            # Calculate content consumed
            total_pages = sum(s.pages_read for s in completed_sessions if s.pages_read)
            total_words = sum(s.words_read for s in completed_sessions if s.words_read)

            # Get quality scores
            focus_scores = [s.focus_score for s in completed_sessions if s.focus_score]
            productivity_scores = [s.productivity_score for s in completed_sessions if s.productivity_score]

            avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else None
            avg_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else None

            # Get documents worked on
            documents_worked = {s.document_id for s in daily_sessions}

            return {
                "date": date,
                "session_summary": {
                    "total_sessions": len(daily_sessions),
                    "completed_sessions": len(completed_sessions),
                    "total_time_seconds": total_time,
                    "total_time_formatted": self._format_duration(total_time),
                    "avg_session_length": int(total_time / len(completed_sessions)) if completed_sessions else 0
                },
                "content_summary": {
                    "pages_read": total_pages,
                    "words_read": total_words,
                    "documents_worked_on": len(documents_worked)
                },
                "quality_metrics": {
                    "average_focus_score": round(avg_focus, 2) if avg_focus else None,
                    "average_productivity_score": round(avg_productivity, 2) if avg_productivity else None,
                    "total_interruptions": sum(s.interruption_count for s in completed_sessions if s.interruption_count)
                },
                "sessions": [
                    {
                        "session_id": s.id,
                        "document_id": s.document_id,
                        "chunk_id": s.chunk_id,
                        "start_time": s.start_time.isoformat() if s.start_time else None,
                        "duration_seconds": s.actual_duration,
                        "duration_formatted": self._format_duration(s.actual_duration or 0),
                        "session_type": s.session_type.value,
                        "status": s.status.value
                    }
                    for s in daily_sessions
                ]
            }

        except Exception as e:
            self._logger.error(f"Failed to get daily summary for {date}: {e}")
            raise

    # Helper Methods

    def _update_derived_metrics(self, progress: ReadingProgress, document) -> None:
        """Update auto-calculated progress metrics."""
        # Update completion percentage based on page if not explicitly set
        if progress.current_page and document.total_pages and progress.completion_percentage == 0.0:
            progress.completion_percentage = min(100.0, (progress.current_page / document.total_pages) * 100)

        # Mark as completed if at 100%
        if progress.completion_percentage >= 100.0 and not progress.is_completed:
            progress.is_completed = True
            progress.completion_date = datetime.now()

    def _update_active_session_progress(
        self,
        document_id: int,
        chunk_id: Optional[int],
        page: Optional[int],
        position: Optional[int]
    ) -> None:
        """Update active session with current progress."""
        active_sessions = self._get_active_sessions_for_content(document_id, chunk_id)

        for session in active_sessions:
            if page is not None:
                session.end_page = page
            if position is not None:
                session.end_position = position

            session.updated_at = datetime.now()

            try:
                self.session_repo.update(session)
            except Exception as e:
                self._logger.warning(f"Failed to update active session progress: {e}")

    def _get_active_sessions_for_content(
        self,
        document_id: int,
        chunk_id: Optional[int]
    ) -> List[StudySession]:
        """Get active sessions for specific content."""
        active_sessions = self.session_repo.get_active_sessions()

        return [
            session for session in active_sessions
            if session.document_id == document_id and session.chunk_id == chunk_id
        ]

    def _update_progress_statistics(self, completed_session: StudySession) -> None:
        """Update progress entry with session statistics."""
        try:
            progress = self.progress_repo.get_by_document_and_chunk(
                completed_session.document_id,
                completed_session.chunk_id
            )

            if progress:
                # Update session count and time
                progress.session_count += 1
                if completed_session.actual_duration:
                    progress.total_time_spent += completed_session.actual_duration

                progress.updated_at = datetime.now()
                self.progress_repo.update(progress)

        except Exception as e:
            self._logger.warning(f"Failed to update progress statistics: {e}")

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
