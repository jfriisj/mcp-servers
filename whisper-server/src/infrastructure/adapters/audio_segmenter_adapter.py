"""
Audio Segmenter Adapter - Infrastructure Adapter
=================================================
Handles segmentation of large audio files into smaller chunks.

Wraps the existing AudioSegmenter class to implement the domain interface,
enabling dependency injection and clean separation of concerns.

Implements: IAudioSegmenter from domain layer
Dependencies: Existing audio_segmenter.py AudioSegmenter
"""

from typing import Any, Dict, List, Optional

from audio_segmenter import AudioSegmenter as ExistingAudioSegmenter
from domain.interfaces import IAudioSegmenter


class AudioSegmenterAdapter(IAudioSegmenter):
    """
    Audio segmentation adapter wrapping AudioSegmenter.

    Provides interface for splitting large audio files into segments
    for parallel processing or handling files exceeding model limits.
    """

    def __init__(
        self,
        segment_length_seconds: int = 30,
        overlap_seconds: int = 2,
        max_segments: int = 50,
    ):
        """
        Initialize audio segmenter adapter.

        Args:
            segment_length_seconds: Length of each segment in seconds
            overlap_seconds: Overlap between segments for continuity
            max_segments: Maximum number of segments to create
        """
        self._segmenter = ExistingAudioSegmenter(
            segment_length_seconds=segment_length_seconds,
            overlap_seconds=overlap_seconds,
            max_segments=max_segments,
        )
        self._temp_dir: Optional[str] = None

    async def segment_audio(
        self,
        file_path: str,
        segment_length_seconds: int,
        overlap_seconds: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Segment audio file into smaller chunks.

        Args:
            file_path: Path to audio file to segment
            segment_length_seconds: Length of each segment
            overlap_seconds: Overlap between segments

        Returns:
            List of segment dictionaries with metadata:
            - audio_data: Segment audio array
            - start_time: Start time in original file (seconds)
            - end_time: End time in original file (seconds)
            - duration: Segment duration (seconds)
            - sample_rate: Audio sample rate
            - temp_file_path: Path to saved segment file (if saved)
        """
        # Update segmenter parameters if different from initialization
        if (
            segment_length_seconds != self._segmenter.segment_length_seconds
            or overlap_seconds != self._segmenter.overlap_seconds
        ):
            self._segmenter.segment_length_seconds = segment_length_seconds
            self._segmenter.overlap_seconds = overlap_seconds

        # Segment the audio file
        segments = self._segmenter.segment_audio_file(
            audio_file_path=file_path, output_dir=self._temp_dir
        )

        # Convert AudioSegment objects to dictionaries
        segment_dicts = []
        for segment in segments:
            segment_dict = {
                "audio_data": segment.audio_data,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.duration,
                "sample_rate": segment.sample_rate,
                "temp_file_path": segment.temp_file_path,
            }
            segment_dicts.append(segment_dict)

        return segment_dicts

    def cleanup_segments(self) -> None:
        """
        Clean up temporary segment files.

        Removes all segment files created during segmentation to free
        disk space. Safe to call multiple times.
        """
        # Note: The existing AudioSegment objects handle their own cleanup
        # This method is here for interface compliance and could be extended
        # to track and clean up segments if needed
        pass

    def should_segment_file(self, file_path: str) -> bool:
        """
        Check if file should be segmented based on duration.

        Args:
            file_path: Path to audio file

        Returns:
            True if file exceeds segment length and should be segmented
        """
        return self._segmenter.should_segment_file(file_path)

    def get_file_duration(self, file_path: str) -> float:
        """
        Get duration of audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds (0.0 if unable to determine)
        """
        return self._segmenter.get_file_duration(file_path)

    def set_temp_directory(self, temp_dir: str) -> None:
        """
        Set temporary directory for saving segment files.

        Args:
            temp_dir: Path to directory for temp segment files
        """
        self._temp_dir = temp_dir
