"""
Domain Layer - Whisper Server
==============================
Core business logic and interfaces with no external dependencies.

This layer defines the contracts (interfaces) that outer layers must implement.
It contains:
- Domain models (data structures)
- Domain interfaces (abstractions for external dependencies)
- Business rules and validation logic

Dependencies: None (innermost layer)
Dependents: Application, Infrastructure, Presentation layers
"""

from .interfaces import (
    IAudioConverter,
    IAudioFormatDetector,
    IAudioSegmenter,
    IConfigurationProvider,
    ITempFileManager,
    IWhisperModel,
)
from .models import (
    BatchTranscriptionConfig,
    BatchTranscriptionResult,
    ConversionConfig,
    ConversionResult,
    FileContentTranscriptionConfig,
    LanguageDetectionConfig,
    LanguageDetectionResult,
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)

__all__ = [
    # Interfaces
    "IAudioConverter",
    "IAudioFormatDetector",
    "IAudioSegmenter",
    "IConfigurationProvider",
    "ITempFileManager",
    "IWhisperModel",
    # Models
    "BatchTranscriptionConfig",
    "BatchTranscriptionResult",
    "ConversionConfig",
    "ConversionResult",
    "FileContentTranscriptionConfig",
    "LanguageDetectionConfig",
    "LanguageDetectionResult",
    "TranscriptionConfig",
    "TranscriptionResult",
    "TranscriptionWithTimestampsConfig",
]
