"""
Data models for Whisper MCP Server
==================================
Dataclasses defining configuration and result structures
for Whisper operations.
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
    model: str = "whisper-1"
    language: Optional[str] = None
    response_format: str = "json"
    temperature: float = 0.0
    prompt: Optional[str] = None
