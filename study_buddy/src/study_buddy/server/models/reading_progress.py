"""
Reading Progress Domain Model for Study Buddy MCP Server.

This module implements ReadingProgress, representing user reading progress
tracking with completion percentages, time spent, and analytics data
for Task 14 Phase 3.

Architecture: Clean Architecture Layer 4 (Infrastructure - Domain Models)
Dependencies: None (pure domain logic)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ProgressStatus(Enum):
    """Reading progress status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    BOOKMARKED = "bookmarked"


class ProgressType(Enum):
    """Type of progress measurement."""
    TIME_BASED = "time_based"       # Progress based on time spent reading
    PAGE_BASED = "page_based"       # Progress based on pages read
    CHUNK_BASED = "chunk_based"     # Progress based on chunks completed
    MANUAL = "manual"               # Manually set progress


@dataclass
class ReadingProgress:
    """
    Domain model representing user reading progress for documents and chunks.

    Tracks completion status, time spent, and various progress metrics
    following single responsibility principle and domain-driven design.

    Responsibilities:
    - Store progress data with validation
    - Calculate completion percentages
    - Track reading statistics
    - Provide progress analytics

    Does NOT:
    - Handle database persistence (repository responsibility)
    - Manage business logic (service responsibility)
    - Perform external operations
    """

    # Primary identifiers
    id: Optional[int] = None
    document_id: int = 0
    chunk_id: Optional[int] = None

    # Progress tracking
    completion_percentage: float = 0.0
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    progress_type: ProgressType = ProgressType.TIME_BASED

    # Time tracking
    total_time_spent: int = 0  # Total seconds spent reading
    session_count: int = 0     # Number of reading sessions
    last_read_date: Optional[datetime] = None
    first_read_date: Optional[datetime] = None

    # Position tracking
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    current_position: Optional[str] = None  # Text position/bookmark

    # Analytics data
    average_session_time: int = 0  # Average session length in seconds
    reading_speed_wpm: Optional[float] = None  # Words per minute
    focus_score: Optional[float] = None  # Focus quality (0.0-1.0)

    # Metadata
    notes: Optional[str] = None
    goals: Optional[str] = None  # Reading goals/targets
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post-initialization validation and setup."""
        # Auto-set timestamps
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Validate data consistency
        self._validate_data()

    def _validate_data(self) -> None:
        """Validate progress data consistency."""
        if not self.document_id or self.document_id <= 0:
            raise ValueError("Valid document_id is required")

        if self.completion_percentage < 0.0 or self.completion_percentage > 100.0:
            raise ValueError("Completion percentage must be between 0 and 100")

        if self.total_time_spent < 0:
            raise ValueError("Total time spent cannot be negative")

        if self.session_count < 0:
            raise ValueError("Session count cannot be negative")

        if self.current_page is not None and self.current_page <= 0:
            raise ValueError("Current page must be positive")

        if self.total_pages is not None and self.total_pages <= 0:
            raise ValueError("Total pages must be positive")

        if (self.current_page is not None and self.total_pages is not None
            and self.current_page > self.total_pages):
            raise ValueError("Current page cannot exceed total pages")

        if self.reading_speed_wpm is not None and self.reading_speed_wpm <= 0:
            raise ValueError("Reading speed must be positive")

        if self.focus_score is not None and (self.focus_score < 0.0 or self.focus_score > 1.0):
            raise ValueError("Focus score must be between 0.0 and 1.0")

    def update_progress(
        self,
        completion_percentage: Optional[float] = None,
        current_page: Optional[int] = None,
        session_time: Optional[int] = None,
        reading_speed: Optional[float] = None
    ) -> None:
        """
        Update progress metrics with validation.

        Args:
            completion_percentage: New completion percentage (0-100)
            current_page: Current page position
            session_time: Time spent in current session (seconds)
            reading_speed: Current reading speed (words per minute)
        """
        if completion_percentage is not None:
            self.completion_percentage = max(0.0, min(100.0, completion_percentage))

        if current_page is not None:
            self.current_page = current_page

        if session_time is not None and session_time > 0:
            self.total_time_spent += session_time
            self.session_count += 1
            self._recalculate_averages()

        if reading_speed is not None:
            self.reading_speed_wpm = reading_speed

        # Update status based on completion
        self._update_status()

        # Update timestamp
        self.updated_at = datetime.now()
        if self.first_read_date is None:
            self.first_read_date = self.updated_at
        self.last_read_date = self.updated_at

        # Re-validate after updates
        self._validate_data()

    def _update_status(self) -> None:
        """Update progress status based on completion percentage."""
        if self.completion_percentage == 0.0:
            self.status = ProgressStatus.NOT_STARTED
        elif self.completion_percentage >= 100.0:
            self.status = ProgressStatus.COMPLETED
        else:
            self.status = ProgressStatus.IN_PROGRESS

    def _recalculate_averages(self) -> None:
        """Recalculate average metrics."""
        if self.session_count > 0:
            self.average_session_time = self.total_time_spent // self.session_count

    def add_session_time(self, session_seconds: int, focus_score: Optional[float] = None) -> None:
        """
        Add reading session data.

        Args:
            session_seconds: Time spent in session (seconds)
            focus_score: Quality of focus during session (0.0-1.0)
        """
        if session_seconds <= 0:
            return

        self.total_time_spent += session_seconds
        self.session_count += 1

        # Update focus score (running average)
        if focus_score is not None:
            if self.focus_score is None:
                self.focus_score = focus_score
            else:
                # Weighted average with new score
                self.focus_score = (self.focus_score * 0.8) + (focus_score * 0.2)

        self._recalculate_averages()
        self.last_read_date = datetime.now()
        self.updated_at = self.last_read_date

    def calculate_page_progress(self) -> Optional[float]:
        """
        Calculate progress based on page position.

        Returns:
            Progress percentage based on pages, or None if no page data
        """
        if self.current_page is None or self.total_pages is None or self.total_pages == 0:
            return None

        return (self.current_page / self.total_pages) * 100.0

    def calculate_estimated_remaining_time(self) -> Optional[int]:
        """
        Calculate estimated remaining reading time in seconds.

        Returns:
            Estimated seconds remaining, or None if insufficient data
        """
        if (self.completion_percentage >= 100.0 or
            self.average_session_time == 0 or
            self.completion_percentage == 0.0):
            return None

        # Simple estimation based on current progress rate
        remaining_percentage = 100.0 - self.completion_percentage
        time_per_percentage = self.total_time_spent / self.completion_percentage

        return int(remaining_percentage * time_per_percentage)

    def get_reading_streak(self) -> int:
        """
        Calculate reading streak (consecutive days with progress).

        Note: This is a simplified calculation. Full implementation would
        require session history from repository.

        Returns:
            Number of consecutive days (simplified to 1 if recently active)
        """
        if self.last_read_date is None:
            return 0

        days_since_last = (datetime.now() - self.last_read_date).days

        # Simplified: if read within last day, streak is at least 1
        return 1 if days_since_last <= 1 else 0

    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for analytics.

        Returns:
            Dictionary with all progress metrics and statistics
        """
        estimated_remaining = self.calculate_estimated_remaining_time()
        page_progress = self.calculate_page_progress()

        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "completion_percentage": round(self.completion_percentage, 2),
            "status": self.status.value,
            "progress_type": self.progress_type.value,

            # Time metrics
            "total_time_spent": self.total_time_spent,
            "total_time_formatted": self._format_duration(self.total_time_spent),
            "session_count": self.session_count,
            "average_session_time": self.average_session_time,
            "average_session_formatted": self._format_duration(self.average_session_time),

            # Position metrics
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "page_progress": round(page_progress, 2) if page_progress else None,
            "current_position": self.current_position,

            # Analytics
            "reading_speed_wpm": self.reading_speed_wpm,
            "focus_score": round(self.focus_score, 3) if self.focus_score else None,
            "reading_streak": self.get_reading_streak(),
            "estimated_remaining_time": estimated_remaining,
            "estimated_remaining_formatted": self._format_duration(estimated_remaining) if estimated_remaining else None,

            # Dates
            "last_read_date": self.last_read_date.isoformat() if self.last_read_date else None,
            "first_read_date": self.first_read_date.isoformat() if self.first_read_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,

            # Goals and notes
            "notes": self.notes,
            "goals": self.goals
        }

    def _format_duration(self, seconds: Optional[int]) -> str:
        """
        Format duration in seconds to human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2h 30m", "45m", "30s")
        """
        if seconds is None or seconds <= 0:
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
        total_pages: Optional[int] = None,
        progress_type: ProgressType = ProgressType.TIME_BASED
    ) -> "ReadingProgress":
        """
        Factory method to create progress tracking for a document.

        Args:
            document_id: ID of document to track
            total_pages: Total pages in document
            progress_type: Type of progress measurement

        Returns:
            New ReadingProgress instance
        """
        return cls(
            document_id=document_id,
            chunk_id=None,
            total_pages=total_pages,
            progress_type=progress_type,
            status=ProgressStatus.NOT_STARTED
        )

    @classmethod
    def create_for_chunk(
        cls,
        document_id: int,
        chunk_id: int,
        progress_type: ProgressType = ProgressType.CHUNK_BASED
    ) -> "ReadingProgress":
        """
        Factory method to create progress tracking for a chunk.

        Args:
            document_id: ID of parent document
            chunk_id: ID of chunk to track
            progress_type: Type of progress measurement

        Returns:
            New ReadingProgress instance
        """
        return cls(
            document_id=document_id,
            chunk_id=chunk_id,
            progress_type=progress_type,
            status=ProgressStatus.NOT_STARTED
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert progress to dictionary for persistence.

        Returns:
            Dictionary representation suitable for database storage
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "completion_percentage": self.completion_percentage,
            "status": self.status.value,
            "progress_type": self.progress_type.value,
            "total_time_spent": self.total_time_spent,
            "session_count": self.session_count,
            "last_read_date": self.last_read_date.isoformat() if self.last_read_date else None,
            "first_read_date": self.first_read_date.isoformat() if self.first_read_date else None,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "current_position": self.current_position,
            "average_session_time": self.average_session_time,
            "reading_speed_wpm": self.reading_speed_wpm,
            "focus_score": self.focus_score,
            "notes": self.notes,
            "goals": self.goals,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadingProgress":
        """
        Create ReadingProgress from dictionary.

        Args:
            data: Dictionary with progress data

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

        return cls(
            id=data.get("id"),
            document_id=data.get("document_id", 0),
            chunk_id=data.get("chunk_id"),
            completion_percentage=data.get("completion_percentage", 0.0),
            status=ProgressStatus(data.get("status", "not_started")),
            progress_type=ProgressType(data.get("progress_type", "time_based")),
            total_time_spent=data.get("total_time_spent", 0),
            session_count=data.get("session_count", 0),
            last_read_date=parse_datetime(data.get("last_read_date")),
            first_read_date=parse_datetime(data.get("first_read_date")),
            current_page=data.get("current_page"),
            total_pages=data.get("total_pages"),
            current_position=data.get("current_position"),
            average_session_time=data.get("average_session_time", 0),
            reading_speed_wpm=data.get("reading_speed_wpm"),
            focus_score=data.get("focus_score"),
            notes=data.get("notes"),
            goals=data.get("goals"),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at"))
        )
