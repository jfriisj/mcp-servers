"""
Domain Models - Whisper Server
===============================
Data structures (dataclasses) for Whisper operations.

These are pure data structures with no business logic or dependencies.
They represent the core domain concepts:
- Configuration objects (inputs to operations)
- Result objects (outputs from operations)

Following SOLID principles:
- Single Responsibility: Each model represents one concept
- Open/Closed: Can extend without modifying existing code
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TranscriptionConfig:
    """Configuration for audio transcription."""

    audio_file: str
    model: str = "whisper-1"
    language: Optional[str] = None
    response_format: str = "json"
    temperature: float = 0.0
    prompt: Optional[str] = None


@dataclass
class TranscriptionWithTimestampsConfig:
    """Configuration for transcription with timestamps."""

    audio_file: str
    model: str = "whisper-1"
    language: Optional[str] = None
    response_format: str = "verbose_json"
    temperature: float = 0.0
    prompt: Optional[str] = None


@dataclass
class LanguageDetectionConfig:
    """Configuration for language detection."""

    audio_file: str
    model: str = "whisper-1"


@dataclass
class BatchTranscriptionConfig:
    """Configuration for batch transcription."""

    audio_files: List[str]
    model: str = "whisper-1"
    language: Optional[str] = None
    response_format: str = "json"
    temperature: float = 0.0


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None
    success: bool = True
    error_message: Optional[str] = None
    # Segmentation metadata
    was_segmented: bool = False
    total_segments: int = 0
    segments_info: Optional[List[Dict[str, Any]]] = None


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""

    detected_language: str
    confidence: float
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class BatchTranscriptionResult:
    """Result of batch transcription."""

    results: List[TranscriptionResult]
    total_files: int
    successful_transcriptions: int
    failed_transcriptions: int
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class FileContentTranscriptionConfig:
    """Configuration for transcribing uploaded file content."""

    file_content: str  # Base64 encoded file content
    file_name: str  # Original file name (for context)
    file_format: Optional[str] = None  # Optional format hint
    model: str = "whisper-1"
    language: Optional[str] = None
    response_format: str = "json"
    temperature: float = 0.0
    prompt: Optional[str] = None


@dataclass
class ConversionConfig:
    """Configuration for audio file conversion."""

    input_file: str
    output_format: str = "wav"  # Default to WAV for best compatibility
    output_file: Optional[str] = None  # If None, will generate temp file
    sample_rate: Optional[int] = None  # If None, keep original
    channels: Optional[int] = None  # If None, keep original (mono=1, stereo=2)
    quality: str = "high"  # high, medium, low
    remove_input: bool = False  # Whether to remove input file after conversion


@dataclass
class ConversionResult:
    """Result of audio conversion operation."""

    success: bool
    output_file: Optional[str] = None
    original_format: Optional[str] = None
    converted_format: Optional[str] = None
    duration: Optional[float] = None
    file_size_mb: Optional[float] = None
    conversion_method: Optional[str] = None  # ffmpeg, librosa, etc.
    error_message: Optional[str] = None
    temp_file: bool = False  # Whether output file is temporary
