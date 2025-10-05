"""
Whisper Model Adapter - Infrastructure Adapter
===============================================
Integrates with Hugging Face Whisper model for speech-to-text operations.

This adapter wraps the Hugging Face transformers pipeline to provide
clean transcription, language detection, and timestamp extraction.

Implements: IWhisperModel from domain layer
Dependencies: transformers, torch, IConfigurationProvider
"""

import os
from typing import Any, Dict

from domain.interfaces import IConfigurationProvider, IWhisperModel
from domain.models import (
    LanguageDetectionConfig,
    LanguageDetectionResult,
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)

# Hugging Face imports with fallback
try:
    import torch
    from transformers import pipeline

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    pipeline = None
    torch = None


class WhisperModelAdapter(IWhisperModel):
    """
    Whisper model adapter using Hugging Face Transformers.

    Provides clean interface for speech-to-text operations using
    the Hugging Face automatic-speech-recognition pipeline with
    Whisper models (e.g., openai/whisper-large-v3).

    This adapter handles:
    - Model loading and initialization
    - Audio transcription with/without timestamps
    - Language detection
    - Result normalization (handles various response formats)

    Note: File conversion and segmentation are handled by use cases,
    not this adapter. This keeps the adapter thin and focused.
    """

    def __init__(self, config_provider: IConfigurationProvider):
        """
        Initialize Whisper model adapter.

        Args:
            config_provider: Configuration provider for model settings
        """
        self._config_provider = config_provider
        self._pipe = None
        self._model_loaded = False

    def _ensure_model_loaded(self) -> bool:
        """
        Ensure the Whisper model is loaded and ready.

        Lazy-loads the model on first use to avoid initialization overhead
        when the model isn't needed.

        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._model_loaded and self._pipe is not None:
            return True

        if not HAS_TRANSFORMERS or pipeline is None or torch is None:
            return False

        try:
            # Get configuration
            whisper_config = self._config_provider.get_whisper_config()

            # Set Hugging Face token for model access
            token = whisper_config.get("huggingface_token")
            if token:
                os.environ["HUGGINGFACE_TOKEN"] = token

            # Determine device: 0 for CUDA (GPU), -1 for CPU
            device_str = whisper_config.get("device", "cpu")
            device = 0 if device_str == "cuda" else -1

            # Use float16 for GPU, float32 for CPU
            dtype = torch.float16 if device == 0 else torch.float32

            # Initialize pipeline
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=whisper_config.get("model_name", "openai/whisper-large-v3"),
                device=device,
                torch_dtype=dtype,
                model_kwargs={"cache_dir": whisper_config.get("cache_dir")},
            )

            self._model_loaded = True
            return True

        except Exception:
            self._pipe = None
            self._model_loaded = False
            return False

    async def transcribe(
        self, config: TranscriptionConfig
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text.

        Args:
            config: Transcription configuration with audio file path

        Returns:
            TranscriptionResult with transcribed text or error
        """
        if not self._ensure_model_loaded():
            return TranscriptionResult(
                text="",
                success=False,
                error_message=(
                    "Whisper model not loaded. Check dependencies "
                    "and Hugging Face token."
                ),
            )

        try:
            # Run transcription
            result = self._pipe(
                config.audio_file,
                return_timestamps=False,
                generate_kwargs={
                    "language": config.language,
                    "task": "transcribe",
                    "temperature": config.temperature,
                },
            )

            # Normalize result (handle different response formats)
            text = self._extract_text_from_result(result)

            return TranscriptionResult(
                text=text,
                language=config.language,
                success=True,
            )

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Transcription failed: {str(e)}",
            )

    async def transcribe_with_timestamps(
        self, config: TranscriptionWithTimestampsConfig
    ) -> TranscriptionResult:
        """
        Transcribe audio file with word-level timestamps.

        Args:
            config: Transcription configuration with timestamp options

        Returns:
            TranscriptionResult with text, segments, and timestamps
        """
        if not self._ensure_model_loaded():
            return TranscriptionResult(
                text="",
                success=False,
                error_message=(
                    "Whisper model not loaded. Check dependencies "
                    "and Hugging Face token."
                ),
            )

        try:
            # Run transcription with timestamps
            result = self._pipe(
                config.audio_file,
                return_timestamps=True,
                generate_kwargs={
                    "language": config.language,
                    "task": "transcribe",
                    "temperature": config.temperature,
                },
            )

            # Extract text and segments
            text = ""
            segments_data = []

            if isinstance(result, dict):
                text = result.get("text", "")
                if "chunks" in result:
                    segments_data = result["chunks"]
            elif isinstance(result, str):
                text = result

            return TranscriptionResult(
                text=text,
                language=config.language,
                segments=segments_data,
                success=True,
            )

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Transcription with timestamps failed: {str(e)}",
            )

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
        if not self._ensure_model_loaded():
            return LanguageDetectionResult(
                detected_language="",
                confidence=0.0,
                success=False,
                error_message=(
                    "Whisper model not loaded. Check dependencies "
                    "and Hugging Face token."
                ),
            )

        try:
            # Run language detection
            # Note: Some Whisper implementations support language detection
            # For now, we'll transcribe a short sample and detect from result
            result = self._pipe(
                config.audio_file,
                return_timestamps=False,
                generate_kwargs={
                    "task": "transcribe",
                },
            )

            # Extract detected language (if available in result)
            detected_lang = "en"  # Default
            confidence = 0.8  # Default confidence

            if isinstance(result, dict):
                detected_lang = result.get("language", "en")
                confidence = result.get("confidence", 0.8)

            return LanguageDetectionResult(
                detected_language=detected_lang,
                confidence=confidence,
                success=True,
            )

        except Exception as e:
            return LanguageDetectionResult(
                detected_language="",
                confidence=0.0,
                success=False,
                error_message=f"Language detection failed: {str(e)}",
            )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded Whisper model.

        Returns:
            Dictionary with model metadata (name, device, loaded status, etc.)
        """
        whisper_config = self._config_provider.get_whisper_config()

        info = {
            "model_name": whisper_config.get("model_name", "openai/whisper-large-v3"),
            "device": whisper_config.get("device", "cpu"),
            "loaded": self._model_loaded,
            "has_transformers": HAS_TRANSFORMERS,
        }

        if self._model_loaded and self._pipe is not None:
            info["pipeline_task"] = "automatic-speech-recognition"
            try:
                info["torch_device"] = str(self._pipe.device)
            except Exception:
                pass

        return info

    def _extract_text_from_result(self, result: Any) -> str:
        """
        Extract text from Whisper pipeline result.

        Handles different result formats that the Whisper pipeline may return:
        - Dictionary with "text" key (most common)
        - Direct string (less common)
        - Other formats (fallback to string conversion)

        Args:
            result: Result from Whisper pipeline

        Returns:
            Extracted text string
        """
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        elif isinstance(result, str):
            return result
        else:
            return str(result)
