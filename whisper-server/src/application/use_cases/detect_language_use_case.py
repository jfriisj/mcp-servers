"""DetectLanguageUseCase - Audio language detection.

This use case provides language detection for audio files.
It's a simple delegation to the Whisper model's language detection capability.
"""

from domain.interfaces import IWhisperModel
from domain.models import LanguageDetectionConfig, LanguageDetectionResult


class DetectLanguageUseCase:
    """Use case for detecting the language of an audio file."""

    def __init__(self, whisper_model: IWhisperModel):
        """Initialize the use case with injected dependencies.

        Args:
            whisper_model: Whisper model for language detection
        """
        self._whisper_model = whisper_model

    async def execute(
        self, config: LanguageDetectionConfig
    ) -> LanguageDetectionResult:
        """Execute language detection.

        Args:
            config: Language detection configuration

        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        return await self._whisper_model.detect_language(config)
