"""
Infrastructure Layer - Whisper Server
======================================
Implementations of domain interfaces and external service integrations.

This layer contains:
- Adapters implementing domain interfaces
- Integration with external services (OpenAI, FFmpeg, etc.)
- File system operations
- Configuration management

Dependencies: Domain layer (interfaces and models)
Dependents: Application and Presentation layers
"""

from .adapters.audio_converter_adapter import AudioConverterAdapter
from .adapters.audio_format_detector import AudioFormatDetector
from .adapters.audio_segmenter_adapter import AudioSegmenterAdapter
from .adapters.configuration_adapter import ConfigurationAdapter
from .adapters.temp_file_manager_adapter import TempFileManagerAdapter
from .adapters.whisper_model_adapter import WhisperModelAdapter

__all__ = [
    "AudioConverterAdapter",
    "AudioFormatDetector",
    "AudioSegmenterAdapter",
    "ConfigurationAdapter",
    "TempFileManagerAdapter",
    "WhisperModelAdapter",
]
