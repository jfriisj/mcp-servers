"""ConvertAudioUseCase - Audio format conversion.

This use case provides audio/video format conversion capabilities.
It delegates to the audio converter infrastructure adapter.
"""

from domain.interfaces import IAudioConverter
from domain.models import ConversionConfig, ConversionResult


class ConvertAudioUseCase:
    """Use case for converting audio/video files to different formats."""

    def __init__(self, audio_converter: IAudioConverter):
        """Initialize the use case with injected dependencies.

        Args:
            audio_converter: Audio format converter
        """
        self._audio_converter = audio_converter

    async def execute(self, config: ConversionConfig) -> ConversionResult:
        """Execute audio conversion.

        Args:
            config: Conversion configuration

        Returns:
            ConversionResult with output file path and status
        """
        return await self._audio_converter.convert(config)

    def get_supported_formats(self) -> dict:
        """Get information about supported formats.

        Returns:
            Dictionary with input and output format information
        """
        return self._audio_converter.get_supported_formats()
