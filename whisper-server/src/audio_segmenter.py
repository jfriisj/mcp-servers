"""
Audio segmentation utilities for Whisper MCP Server
===================================================
Handles splitting large audio files into smaller segments
for parallel processing.
"""

import os
import tempfile
from typing import List, Optional

# Audio processing imports (with fallbacks)
try:
    import librosa
    import soundfile as sf

    HAS_AUDIO_LIBS = True
except ImportError:
    HAS_AUDIO_LIBS = False
    librosa = None
    sf = None


class AudioSegment:
    """Represents a segment of audio with timing information."""

    def __init__(
        self,
        audio_data,  # librosa audio array
        start_time: float,
        end_time: float,
        sample_rate: int,
        temp_file_path: Optional[str] = None,
    ):
        self.audio_data = audio_data
        self.start_time = start_time
        self.end_time = end_time
        self.sample_rate = sample_rate
        self.temp_file_path = temp_file_path
        self.duration = end_time - start_time

    def save_to_file(self, file_path: str) -> None:
        """Save segment to WAV file."""
        if not HAS_AUDIO_LIBS:
            raise ImportError("Audio libraries not available")

        sf.write(file_path, self.audio_data, self.sample_rate)
        self.temp_file_path = file_path

    def cleanup(self) -> None:
        """Clean up temporary file if it exists."""
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.unlink(self.temp_file_path)
            except OSError:
                pass  # Ignore cleanup errors


class AudioSegmenter:
    """Handles segmentation of audio files for parallel processing."""

    def __init__(
        self,
        segment_length_seconds: int = 30,
        overlap_seconds: int = 2,
        max_segments: int = 50,
    ):
        """
        Initialize the audio segmenter.

        Args:
            segment_length_seconds: Length of each segment in seconds
            overlap_seconds: Overlap between segments in seconds
            max_segments: Maximum number of segments to create
        """
        self.segment_length_seconds = segment_length_seconds
        self.overlap_seconds = overlap_seconds
        self.max_segments = max_segments

        if not HAS_AUDIO_LIBS:
            raise ImportError(
                "Audio segmentation requires librosa and soundfile. "
                "Install with: pip install librosa soundfile"
            )

    def segment_audio_file(
        self,
        audio_file_path: str,
        output_dir: Optional[str] = None,
    ) -> List[AudioSegment]:
        """
        Segment an audio file into smaller chunks.

        Args:
            audio_file_path: Path to the audio file
            output_dir: Directory to save segment files (optional)

        Returns:
            List of AudioSegment objects
        """
        # Load audio file
        audio_data, sample_rate = librosa.load(audio_file_path, sr=None)

        # Calculate segment parameters
        segment_samples = int(self.segment_length_seconds * sample_rate)
        overlap_samples = int(self.overlap_seconds * sample_rate)
        step_samples = segment_samples - overlap_samples

        # Create segments
        segments = []
        start_sample = 0

        while start_sample < len(audio_data) and len(segments) < self.max_segments:
            end_sample = min(start_sample + segment_samples, len(audio_data))

            # Extract segment data
            segment_data = audio_data[start_sample:end_sample]

            # Calculate timing
            start_time = start_sample / sample_rate
            end_time = end_sample / sample_rate

            # Create segment
            segment = AudioSegment(
                audio_data=segment_data,
                start_time=start_time,
                end_time=end_time,
                sample_rate=int(sample_rate),
            )

            # Save to temporary file if output_dir provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                temp_file = os.path.join(
                    output_dir, f"segment_{len(segments):03d}_{start_time:.1f}s.wav"
                )
                segment.save_to_file(temp_file)

            segments.append(segment)

            # Move to next segment (with overlap consideration)
            start_sample += step_samples

            # Break if we've covered the entire file
            if end_sample >= len(audio_data):
                break

        return segments

    def should_segment_file(self, audio_file_path: str) -> bool:
        """
        Determine if a file should be segmented based on duration.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            True if file should be segmented
        """
        if not HAS_AUDIO_LIBS:
            return False

        try:
            # Get duration without loading full file
            duration = librosa.get_duration(filename=audio_file_path)
            return duration > self.segment_length_seconds
        except Exception:
            # If we can't get duration, assume segmentation needed for safety
            return True

    def get_file_duration(self, audio_file_path: str) -> float:
        """
        Get the duration of an audio file.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Duration in seconds
        """
        if not HAS_AUDIO_LIBS:
            return 0.0

        try:
            return librosa.get_duration(filename=audio_file_path)
        except Exception:
            return 0.0


class TempDirectoryManager:
    """Manages temporary directories for audio segments."""

    def __init__(self):
        self.temp_dirs: List[str] = []

    def create_temp_dir(self, prefix: str = "whisper_segments_") -> str:
        """Create a temporary directory and track it for cleanup."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup_all(self) -> None:
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil

                shutil.rmtree(temp_dir)
            except OSError:
                pass  # Ignore cleanup errors
        self.temp_dirs.clear()
