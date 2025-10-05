"""
Audio Converter Adapter - Infrastructure Adapter
=================================================
Handles conversion of audio/video files to Whisper-compatible formats.

Wraps the existing AudioConverter class to implement the domain interface,
enabling clean dependency injection and format conversion abstraction.

Implements: IAudioConverter from domain layer
Dependencies: Existing audio_converter.py AudioConverter
"""

from typing import Any, Dict, List, Optional

from audio_converter import AudioConverter as ExistingAudioConverter
from domain.interfaces import IAudioConverter
from domain.models import ConversionConfig, ConversionResult


class AudioConverterAdapter(IAudioConverter):
    """
    Audio/video format conversion adapter wrapping AudioConverter.

    Provides interface for converting between audio formats using
    FFmpeg or librosa, with support for video audio extraction.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize audio converter adapter.

        Args:
            temp_dir: Directory for temporary conversion files
        """
        self._converter = ExistingAudioConverter(temp_dir=temp_dir)

    async def convert(self, config: ConversionConfig) -> ConversionResult:
        """
        Convert audio file to a different format.

        Args:
            config: Conversion configuration with input/output settings

        Returns:
            ConversionResult with output file path and conversion metadata
        """
        # Delegate to existing converter
        result = await self._converter.convert_file(config)
        return result

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get audio file information (duration, format, sample rate, etc.).

        Args:
            file_path: Path to audio/video file

        Returns:
            Dictionary with file metadata:
            - exists: Whether file exists
            - format: File format/extension
            - duration: Duration in seconds (if available)
            - sample_rate: Audio sample rate (if available)
            - channels: Number of audio channels (if available)
            - size_mb: File size in megabytes
        """
        return self._converter.get_file_info(file_path)

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get lists of supported input and output formats.

        Returns:
            Dictionary with:
            - 'whisper_native': Formats Whisper can process directly
            - 'convertible': Formats that can be converted
            - 'all_supported': All supported formats (native + convertible)
        """
        return {
            "whisper_native": self._converter.WHISPER_SUPPORTED_FORMATS,
            "convertible": self._converter.CONVERTIBLE_FORMATS,
            "all_supported": (
                self._converter.WHISPER_SUPPORTED_FORMATS
                + self._converter.CONVERTIBLE_FORMATS
            ),
        }

    def get_recommended_output_format(self, input_format: str) -> str:
        """
        Get recommended output format for a given input format.

        For best Whisper compatibility, recommends:
        - WAV for lossless quality
        - MP3 for compressed files
        - M4A for video sources

        Args:
            input_format: Input audio format

        Returns:
            Recommended output format
        """
        input_format = input_format.lower().lstrip(".")

        # Video formats -> M4A (good quality, efficient)
        video_formats = {
            "mp4",
            "mov",
            "avi",
            "mkv",
            "wmv",
            "flv",
            "webm",
            "3gp",
            "m4v",
        }
        if input_format in video_formats:
            return "m4a"

        # Lossless formats -> WAV (preserve quality)
        lossless_formats = {"flac", "wav", "aiff", "alac", "ape", "wv"}
        if input_format in lossless_formats:
            return "wav"

        # Everything else -> MP3 (good compatibility)
        return "mp3"

    def needs_conversion(self, file_path: str) -> bool:
        """
        Check if file needs conversion for Whisper compatibility.

        Args:
            file_path: Path to audio/video file

        Returns:
            True if conversion needed, False if already compatible
        """
        return self._converter.needs_conversion(file_path)

    def is_ffmpeg_available(self) -> bool:
        """
        Check if FFmpeg is available for conversion.

        Returns:
            True if FFmpeg found, False otherwise
        """
        return self._converter.ffmpeg_path is not None

    def is_librosa_available(self) -> bool:
        """
        Check if librosa is available for conversion.

        Returns:
            True if librosa installed, False otherwise
        """
        try:
            import librosa  # noqa: F401

            return True
        except ImportError:
            return False
