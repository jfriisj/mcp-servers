"""
Domain Interfaces - Whisper Server
===================================
Abstract interfaces defining contracts for external dependencies.

These interfaces enable dependency inversion - the core business logic
depends on abstractions, not concrete implementations.

Following SOLID principles:
- Interface Segregation: Each interface has a focused responsibility
- Dependency Inversion: High-level modules depend on these abstractions
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import (
    ConversionConfig,
    ConversionResult,
    LanguageDetectionConfig,
    LanguageDetectionResult,
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)


class IWhisperModel(ABC):
    """
    Interface for Whisper speech-to-text model operations.

    This abstraction allows swapping between different Whisper implementations
    (OpenAI API, local model, alternative providers) without changing business logic.
    """

    @abstractmethod
    async def transcribe(self, config: TranscriptionConfig) -> TranscriptionResult:
        """
        Transcribe audio file to text.

        Args:
            config: Transcription configuration

        Returns:
            TranscriptionResult with text and metadata
        """
        pass

    @abstractmethod
    async def transcribe_with_timestamps(
        self, config: TranscriptionWithTimestampsConfig
    ) -> TranscriptionResult:
        """
        Transcribe audio with word-level timestamps.

        Args:
            config: Transcription configuration with timestamp options

        Returns:
            TranscriptionResult with text, segments, and timestamps
        """
        pass

    @abstractmethod
    async def detect_language(
        self, config: LanguageDetectionConfig
    ) -> LanguageDetectionResult:
        """
        Detect the language of an audio file.

        Args:
            config: Language detection configuration

        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded Whisper model.

        Returns:
            Dictionary with model metadata (name, version, size, etc.)
        """
        pass


class IAudioConverter(ABC):
    """
    Interface for audio format conversion operations.

    Abstracts the underlying conversion tool (FFmpeg, librosa, etc.)
    enabling easy replacement or mocking for tests.
    """

    @abstractmethod
    async def convert(self, config: ConversionConfig) -> ConversionResult:
        """
        Convert audio file to a different format.

        Args:
            config: Conversion configuration (input, output format, quality, etc.)

        Returns:
            ConversionResult with output file path and metadata
        """
        pass

    @abstractmethod
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get audio file information (duration, format, sample rate, etc.).

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with file metadata
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get lists of supported input and output formats.

        Returns:
            Dictionary with 'input' and 'output' format lists
        """
        pass

    @abstractmethod
    def get_recommended_output_format(self, input_format: str) -> str:
        """
        Get recommended output format for a given input format.

        Args:
            input_format: Input audio format

        Returns:
            Recommended output format
        """
        pass


class IAudioSegmenter(ABC):
    """
    Interface for audio segmentation operations.

    Handles splitting long audio files into manageable segments
    for processing large files that exceed model limits.
    """

    @abstractmethod
    async def segment_audio(
        self, file_path: str, segment_length_seconds: int, overlap_seconds: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Segment audio file into smaller chunks.

        Args:
            file_path: Path to audio file
            segment_length_seconds: Length of each segment
            overlap_seconds: Overlap between segments for continuity

        Returns:
            List of segment dictionaries with paths and metadata
        """
        pass

    @abstractmethod
    def cleanup_segments(self) -> None:
        """
        Clean up temporary segment files.
        """
        pass


class ITempFileManager(ABC):
    """
    Interface for temporary file management.

    Abstracts file system operations for creating and cleaning up
    temporary files used during processing.
    """

    @abstractmethod
    def create_temp_file(
        self, suffix: str = "", prefix: str = "", content: Optional[bytes] = None
    ) -> str:
        """
        Create a temporary file.

        Args:
            suffix: File extension (e.g., '.wav')
            prefix: File name prefix
            content: Optional initial content

        Returns:
            Path to created temporary file
        """
        pass

    @abstractmethod
    def create_temp_directory(self) -> str:
        """
        Create a temporary directory.

        Returns:
            Path to created temporary directory
        """
        pass

    @abstractmethod
    def cleanup_all(self) -> None:
        """
        Clean up all temporary files and directories created by this manager.
        """
        pass

    @abstractmethod
    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a specific temporary file.

        Args:
            file_path: Path to file to clean up

        Returns:
            True if cleanup successful, False otherwise
        """
        pass


class IAudioFormatDetector(ABC):
    """
    Interface for audio format detection.

    Detects audio file format from various sources (file data, filename, hints)
    to handle files without proper extensions or uploaded content.
    """

    @abstractmethod
    def detect_format(
        self,
        file_data: Optional[bytes] = None,
        file_name: Optional[str] = None,
        format_hint: Optional[str] = None,
    ) -> Optional[str]:
        """
        Detect audio file format from available information.

        Args:
            file_data: Binary file content for magic number detection
            file_name: File name for extension-based detection
            format_hint: Explicit format hint from user

        Returns:
            Detected format (e.g., 'mp3', 'wav', 'wma') or None if unable to detect
        """
        pass

    @abstractmethod
    def is_supported_format(self, format_str: str) -> bool:
        """
        Check if a format is supported by Whisper.

        Args:
            format_str: Format string (e.g., 'mp3', 'wav')

        Returns:
            True if format is supported, False otherwise
        """
        pass

    @abstractmethod
    def is_convertible_format(self, format_str: str) -> bool:
        """
        Check if a format can be converted to a Whisper-compatible format.

        Args:
            format_str: Format string (e.g., 'wma', 'avi')

        Returns:
            True if format can be converted, False otherwise
        """
        pass


class IConfigurationProvider(ABC):
    """
    Interface for configuration management.

    Provides access to server and Whisper configuration settings,
    abstracting the underlying configuration source (YAML, env vars, etc.).
    """

    @abstractmethod
    def get_whisper_config(self) -> Dict[str, Any]:
        """
        Get Whisper model configuration.

        Returns:
            Dictionary with Whisper settings (model, API key, etc.)
        """
        pass

    @abstractmethod
    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.

        Returns:
            Dictionary with server settings (host, port, logging, etc.)
        """
        pass

    @abstractmethod
    def get_segmentation_config(self) -> Dict[str, Any]:
        """
        Get audio segmentation configuration.

        Returns:
            Dictionary with segmentation settings (length, overlap, enabled)
        """
        pass

    @abstractmethod
    def get_conversion_config(self) -> Dict[str, Any]:
        """
        Get audio conversion configuration.

        Returns:
            Dictionary with conversion settings (formats, quality, enabled)
        """
        pass
