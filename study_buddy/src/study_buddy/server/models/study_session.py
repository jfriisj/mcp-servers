"""
Study Session Domain Model for Study Buddy MCP Server.

This module implements StudySession, representing individual study sessions
with time tracking, notes, and analytics for Task 14 Phase 3.

Architecture: Clean Architecture Layer 4 (Infrastructure - Domain Models)
Dependencies: None (pure domain logic)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(Enum):
    """Study session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SessionType(Enum):
    """Type of study session."""
    READING = "reading"
    REVIEW = "review"
    RESEARCH = "research"
    NOTE_TAKING = "note_taking"
    SUMMARY = "summary"
    ANALYSIS = "analysis"


@dataclass
class StudySession:
    """
    Domain model representing individual study sessions.

    Tracks session duration, focus quality, activities, and outcomes
    following single responsibility principle and domain-driven design.

    Responsibilities:
    - Store session data with validation
    - Calculate session metrics and duration
    - Track session activities and goals
    - Provide session analytics

    Does NOT:
    - Handle database persistence (repository responsibility)
    - Manage business logic (service responsibility)
    - Perform external operations
    """

    # Primary identifiers
    id: Optional[int] = None
    document_id: int = 0
    chunk_id: Optional[int] = None

    # Session timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    planned_duration: Optional[int] = None  # Planned session length in seconds
    actual_duration: Optional[int] = None   # Actual session length in seconds

    # Session details
    session_type: SessionType = SessionType.READING
    status: SessionStatus = SessionStatus.ACTIVE

    # Progress tracking
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    start_position: Optional[str] = None
    end_position: Optional[str] = None

    # Quality metrics
    focus_score: Optional[float] = None     # Self-reported focus quality (0.0-1.0)
    productivity_score: Optional[float] = None  # Calculated productivity (0.0-1.0)
    interruption_count: int = 0             # Number of interruptions during session

    # Session content
    goals: Optional[str] = None             # Session goals/objectives
    notes: Optional[str] = None             # Session notes and reflections
    achievements: Optional[str] = None      # What was accomplished
    challenges: Optional[str] = None        # Difficulties encountered

    # Analytics
    words_read: Optional[int] = None        # Estimated words read
    pages_read: Optional[int] = None        # Pages covered
    concepts_learned: Optional[int] = None  # Number of new concepts
    questions_raised: Optional[int] = None  # Questions generated during session

    # Metadata
    tags: Optional[List[str]] = None        # Session tags for categorization
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post-initialization validation and setup."""
        # Auto-set timestamps
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Auto-set start time if not provided
        if self.start_time is None:
            self.start_time = datetime.now()

        # Initialize tags if None
        if self.tags is None:
            self.tags = []

        # Validate data consistency
        self._validate_data()

    def _validate_data(self) -> None:
        """Validate session data consistency."""
        if not self.document_id or self.document_id <= 0:
            raise ValueError("Valid document_id is required")

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("End time must be after start time")

        if self.planned_duration is not None and self.planned_duration <= 0:
            raise ValueError("Planned duration must be positive")

        if self.actual_duration is not None and self.actual_duration <= 0:
            raise ValueError("Actual duration must be positive")

        if self.focus_score is not None and (self.focus_score < 0.0 or self.focus_score > 1.0):
            raise ValueError("Focus score must be between 0.0 and 1.0")

        if self.productivity_score is not None and (self.productivity_score < 0.0 or self.productivity_score > 1.0):
            raise ValueError("Productivity score must be between 0.0 and 1.0")

        if self.interruption_count < 0:
            raise ValueError("Interruption count cannot be negative")

        if self.start_page is not None and self.start_page <= 0:
            raise ValueError("Start page must be positive")

        if self.end_page is not None and self.end_page <= 0:
            raise ValueError("End page must be positive")

        if (self.start_page is not None and self.end_page is not None
            and self.start_page > self.end_page):
            raise ValueError("End page must be >= start page")

        if self.words_read is not None and self.words_read < 0:
            raise ValueError("Words read cannot be negative")

        if self.pages_read is not None and self.pages_read < 0:
            raise ValueError("Pages read cannot be negative")

        if self.concepts_learned is not None and self.concepts_learned < 0:
            raise ValueError("Concepts learned cannot be negative")

        if self.questions_raised is not None and self.questions_raised < 0:
            raise ValueError("Questions raised cannot be negative")

    def start_session(
        self,
        goals: Optional[str] = None,
        planned_duration: Optional[int] = None
    ) -> None:
        """
        Start a new study session.

        Args:
            goals: Session goals/objectives
            planned_duration: Planned session length in seconds
        """
        if self.status == SessionStatus.ACTIVE:
            raise ValueError("Session is already active")

        self.start_time = datetime.now()
        self.end_time = None
        self.actual_duration = None
        self.status = SessionStatus.ACTIVE

        if goals:
            self.goals = goals

        if planned_duration:
            self.planned_duration = planned_duration

        self.updated_at = datetime.now()

        # Reset session metrics
        self.focus_score = None
        self.productivity_score = None
        self.interruption_count = 0

    def pause_session(self) -> None:
        """Pause the current session."""
        if self.status != SessionStatus.ACTIVE:
            raise ValueError("Can only pause active sessions")

        self.status = SessionStatus.PAUSED
        self.updated_at = datetime.now()

        # Calculate duration up to pause point
        if self.start_time:
            pause_duration = int((datetime.now() - self.start_time).total_seconds())
            self.actual_duration = pause_duration

    def resume_session(self) -> None:
        """Resume a paused session."""
        if self.status != SessionStatus.PAUSED:
            raise ValueError("Can only resume paused sessions")

        # Adjust start time to account for pause duration
        if self.start_time and self.actual_duration:
            datetime.now() - self.start_time - timedelta(seconds=self.actual_duration)
            self.start_time = datetime.now() - timedelta(seconds=self.actual_duration)

        self.status = SessionStatus.ACTIVE
        self.updated_at = datetime.now()

    def end_session(
        self,
        focus_score: Optional[float] = None,
        notes: Optional[str] = None,
        achievements: Optional[str] = None,
        challenges: Optional[str] = None
    ) -> None:
        """
        End the current session with completion data.

        Args:
            focus_score: Self-reported focus quality (0.0-1.0)
            notes: Session notes and reflections
            achievements: What was accomplished
            challenges: Difficulties encountered
        """
        if self.status not in [SessionStatus.ACTIVE, SessionStatus.PAUSED]:
            raise ValueError("Can only end active or paused sessions")

        self.end_time = datetime.now()
        self.status = SessionStatus.COMPLETED

        # Calculate actual duration
        if self.start_time:
            self.actual_duration = int((self.end_time - self.start_time).total_seconds())

        # Set completion data
        if focus_score is not None:
            self.focus_score = focus_score

        if notes:
            self.notes = notes

        if achievements:
            self.achievements = achievements

        if challenges:
            self.challenges = challenges

        # Calculate productivity score
        self._calculate_productivity_score()

        # Calculate pages read if page positions available
        if self.start_page is not None and self.end_page is not None:
            self.pages_read = max(0, self.end_page - self.start_page + 1)

        self.updated_at = datetime.now()

        # Re-validate after updates
        self._validate_data()

    def cancel_session(self, reason: Optional[str] = None) -> None:
        """
        Cancel the current session.

        Args:
            reason: Reason for cancellation
        """
        self.status = SessionStatus.CANCELLED
        self.end_time = datetime.now()

        if reason:
            if self.notes:
                self.notes += f"\n\nCancelled: {reason}"
            else:
                self.notes = f"Cancelled: {reason}"

        self.updated_at = datetime.now()

    def add_interruption(self, description: Optional[str] = None) -> None:
        """
        Record an interruption during the session.

        Args:
            description: Description of the interruption
        """
        if self.status != SessionStatus.ACTIVE:
            return

        self.interruption_count += 1

        if description:
            interruption_note = f"Interruption {self.interruption_count}: {description}"
            if self.challenges:
                self.challenges += f"\n{interruption_note}"
            else:
                self.challenges = interruption_note

        self.updated_at = datetime.now()

    def update_progress(
        self,
        current_page: Optional[int] = None,
        current_position: Optional[str] = None,
        words_read: Optional[int] = None,
        concepts_learned: Optional[int] = None,
        questions_raised: Optional[int] = None
    ) -> None:
        """
        Update session progress metrics.

        Args:
            current_page: Current page position
            current_position: Current text position
            words_read: Total words read in session
            concepts_learned: Number of new concepts learned
            questions_raised: Number of questions generated
        """
        if current_page is not None:
            self.end_page = current_page
            if self.start_page is None:
                self.start_page = current_page

        if current_position is not None:
            self.end_position = current_position
            if self.start_position is None:
                self.start_position = current_position

        if words_read is not None:
            self.words_read = words_read

        if concepts_learned is not None:
            self.concepts_learned = concepts_learned

        if questions_raised is not None:
            self.questions_raised = questions_raised

        self.updated_at = datetime.now()

    def _calculate_productivity_score(self) -> None:
        """Calculate productivity score based on session metrics."""
        if self.status != SessionStatus.COMPLETED:
            return

        # Simple productivity calculation based on available metrics
        score_factors = []

        # Factor 1: Focus score (if available)
        if self.focus_score is not None:
            score_factors.append(self.focus_score)

        # Factor 2: Interruption penalty
        if self.actual_duration and self.actual_duration > 0:
            interruption_penalty = min(self.interruption_count * 0.1, 0.5)  # Max 50% penalty
            interruption_factor = max(0.0, 1.0 - interruption_penalty)
            score_factors.append(interruption_factor)

        # Factor 3: Duration efficiency (actual vs planned)
        if self.planned_duration and self.actual_duration:
            duration_ratio = min(self.actual_duration / self.planned_duration, 2.0)  # Cap at 2x
            if duration_ratio <= 1.0:
                # Finished on time or early
                duration_factor = 1.0
            else:
                # Took longer than planned
                duration_factor = max(0.5, 1.0 / duration_ratio)
            score_factors.append(duration_factor)

        # Factor 4: Content progress (if available)
        if self.pages_read is not None and self.actual_duration:
            # Simple pages-per-minute metric
            hours = self.actual_duration / 3600.0
            if hours > 0:
                pages_per_hour = self.pages_read / hours
                # Normalize to 0.0-1.0 scale (assume 10+ pages/hour is excellent)
                content_factor = min(pages_per_hour / 10.0, 1.0)
                score_factors.append(content_factor)

        # Calculate average of all factors
        if score_factors:
            self.productivity_score = sum(score_factors) / len(score_factors)
        else:
            self.productivity_score = 0.5  # Default neutral score

    def get_duration_seconds(self) -> int:
        """
        Get session duration in seconds.

        Returns:
            Duration in seconds (actual if completed, current if active)
        """
        if self.actual_duration is not None:
            return self.actual_duration

        if self.start_time:
            end_time = self.end_time or datetime.now()
            return int((end_time - self.start_time).total_seconds())

        return 0

    def get_reading_speed(self) -> Optional[float]:
        """
        Calculate reading speed in words per minute.

        Returns:
            Reading speed in WPM, or None if insufficient data
        """
        if not self.words_read or not self.actual_duration or self.actual_duration == 0:
            return None

        minutes = self.actual_duration / 60.0
        return self.words_read / minutes

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive session summary for analytics.

        Returns:
            Dictionary with all session metrics and data
        """
        duration = self.get_duration_seconds()
        reading_speed = self.get_reading_speed()

        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,

            # Session details
            "session_type": self.session_type.value,
            "status": self.status.value,
            "goals": self.goals,

            # Timing
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "planned_duration": self.planned_duration,
            "actual_duration": self.actual_duration,
            "duration_seconds": duration,
            "duration_formatted": self._format_duration(duration),

            # Progress
            "start_page": self.start_page,
            "end_page": self.end_page,
            "pages_read": self.pages_read,
            "start_position": self.start_position,
            "end_position": self.end_position,

            # Quality metrics
            "focus_score": round(self.focus_score, 3) if self.focus_score else None,
            "productivity_score": round(self.productivity_score, 3) if self.productivity_score else None,
            "interruption_count": self.interruption_count,

            # Analytics
            "words_read": self.words_read,
            "reading_speed_wpm": round(reading_speed, 1) if reading_speed else None,
            "concepts_learned": self.concepts_learned,
            "questions_raised": self.questions_raised,

            # Content
            "notes": self.notes,
            "achievements": self.achievements,
            "challenges": self.challenges,
            "tags": self.tags,

            # Metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2h 30m", "45m", "30s")
        """
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

    @classmethod
    def create_for_document(
        cls,
        document_id: int,
        session_type: SessionType = SessionType.READING,
        goals: Optional[str] = None,
        planned_duration: Optional[int] = None
    ) -> "StudySession":
        """
        Factory method to create session for a document.

        Args:
            document_id: ID of document to study
            session_type: Type of study session
            goals: Session goals/objectives
            planned_duration: Planned session length in seconds

        Returns:
            New StudySession instance
        """
        return cls(
            document_id=document_id,
            chunk_id=None,
            session_type=session_type,
            goals=goals,
            planned_duration=planned_duration,
            status=SessionStatus.ACTIVE
        )

    @classmethod
    def create_for_chunk(
        cls,
        document_id: int,
        chunk_id: int,
        session_type: SessionType = SessionType.READING,
        goals: Optional[str] = None,
        planned_duration: Optional[int] = None
    ) -> "StudySession":
        """
        Factory method to create session for a chunk.

        Args:
            document_id: ID of parent document
            chunk_id: ID of chunk to study
            session_type: Type of study session
            goals: Session goals/objectives
            planned_duration: Planned session length in seconds

        Returns:
            New StudySession instance
        """
        return cls(
            document_id=document_id,
            chunk_id=chunk_id,
            session_type=session_type,
            goals=goals,
            planned_duration=planned_duration,
            status=SessionStatus.ACTIVE
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary for persistence.

        Returns:
            Dictionary representation suitable for database storage
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "planned_duration": self.planned_duration,
            "actual_duration": self.actual_duration,
            "session_type": self.session_type.value,
            "status": self.status.value,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "focus_score": self.focus_score,
            "productivity_score": self.productivity_score,
            "interruption_count": self.interruption_count,
            "goals": self.goals,
            "notes": self.notes,
            "achievements": self.achievements,
            "challenges": self.challenges,
            "words_read": self.words_read,
            "pages_read": self.pages_read,
            "concepts_learned": self.concepts_learned,
            "questions_raised": self.questions_raised,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudySession":
        """
        Create StudySession from dictionary.

        Args:
            data: Dictionary with session data

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

        return cls(
            id=data.get("id"),
            document_id=data.get("document_id", 0),
            chunk_id=data.get("chunk_id"),
            start_time=parse_datetime(data.get("start_time")),
            end_time=parse_datetime(data.get("end_time")),
            planned_duration=data.get("planned_duration"),
            actual_duration=data.get("actual_duration"),
            session_type=SessionType(data.get("session_type", "reading")),
            status=SessionStatus(data.get("status", "active")),
            start_page=data.get("start_page"),
            end_page=data.get("end_page"),
            start_position=data.get("start_position"),
            end_position=data.get("end_position"),
            focus_score=data.get("focus_score"),
            productivity_score=data.get("productivity_score"),
            interruption_count=data.get("interruption_count", 0),
            goals=data.get("goals"),
            notes=data.get("notes"),
            achievements=data.get("achievements"),
            challenges=data.get("challenges"),
            words_read=data.get("words_read"),
            pages_read=data.get("pages_read"),
            concepts_learned=data.get("concepts_learned"),
            questions_raised=data.get("questions_raised"),
            tags=data.get("tags"),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at"))
        )
