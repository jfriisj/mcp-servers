"""TranscribeAudioUseCase - Core audio transcription workflow.

This use case orchestrates the basic transcription workflow:
1. Detect audio format
2. Convert to supported format if needed
3. Transcribe using Whisper
4. Clean up temporary files
5. Return transcription result
"""

import os
from pathlib import Path
from typing import Optional

from domain.interfaces import (
    IAudioConverter,
    IAudioFormatDetector,
    IConfigurationProvider,
    ITempFileManager,
    IWhisperModel,
)
from domain.models import TranscriptionConfig, TranscriptionResult


class TranscribeAudioUseCase:
    """Use case for basic audio file transcription."""

    def __init__(
        self,
        whisper_model: IWhisperModel,
        audio_converter: IAudioConverter,
        format_detector: IAudioFormatDetector,
        temp_file_manager: ITempFileManager,
        config_provider: IConfigurationProvider,
    ):
        """Initialize the use case with injected dependencies.

        Args:
            whisper_model: Whisper model for transcription
            audio_converter: Audio format converter
            format_detector: Audio format detector
            temp_file_manager: Temporary file manager
            config_provider: Configuration provider
        """
        self._whisper_model = whisper_model
        self._audio_converter = audio_converter
        self._format_detector = format_detector
        self._temp_file_manager = temp_file_manager
        self._config_provider = config_provider

    async def execute(
        self, config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Execute the transcription use case.

        Args:
            config: Transcription configuration

        Returns:
            TranscriptionResult with transcription text and metadata
        """
        # Validate audio file exists
        if not os.path.exists(config.audio_file):
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Audio file not found: {config.audio_file}",
            )

        # Track if we created a temp file for conversion
        temp_file_path: Optional[str] = None

        try:
            # Read file data for format detection
            with open(config.audio_file, "rb") as f:
                file_data = f.read(16384)  # Read first 16KB for magic bytes

            # Detect audio format
            detected_format = self._format_detector.detect_format(
                file_data=file_data,
                file_name=config.audio_file,
            )

            if not detected_format:
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message="Unable to detect audio format",
                )

            # Determine if conversion is needed
            file_to_transcribe = config.audio_file
            needs_conversion = not self._format_detector.is_supported_format(
                detected_format
            )

            if needs_conversion:
                # Check if format is convertible
                if not self._format_detector.is_convertible_format(
                    detected_format
                ):
                    return TranscriptionResult(
                        text="",
                        success=False,
                        error_message=(
                            f"Unsupported audio format: {detected_format}"
                        ),
                    )

                # Convert to WAV format
                temp_file_path = await self._convert_to_supported_format(
                    config.audio_file
                )

                if not temp_file_path:
                    return TranscriptionResult(
                        text="",
                        success=False,
                        error_message="Audio conversion failed",
                    )

                file_to_transcribe = temp_file_path

            # Update config with the file to transcribe
            transcription_config = TranscriptionConfig(
                audio_file=file_to_transcribe,
                model=config.model,
                language=config.language,
                response_format=config.response_format,
                temperature=config.temperature,
                prompt=config.prompt,
            )

            # Transcribe using Whisper
            result = await self._whisper_model.transcribe(
                transcription_config
            )

            return result

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Transcription failed: {str(e)}",
            )
        finally:
            # Clean up temporary files
            if temp_file_path:
                self._temp_file_manager.cleanup_all()

    async def _convert_to_supported_format(
        self, audio_file: str
    ) -> Optional[str]:
        """Convert audio file to a Whisper-supported format.

        Args:
            audio_file: Path to the original audio file

        Returns:
            Path to the converted file, or None if conversion failed
        """
        try:
            # Get conversion configuration (for future use)
            # conversion_config = self._config_provider.get_conversion_config()

            # Create temp file for converted audio
            file_path = Path(audio_file)
            temp_file = self._temp_file_manager.create_temp_file(
                suffix=".wav", prefix=f"{file_path.stem}_converted_"
            )

            # Convert audio
            from domain.models import ConversionConfig

            config = ConversionConfig(
                input_file=audio_file,
                output_file=temp_file,
                output_format="wav",
                quality="high",
            )

            result = await self._audio_converter.convert(config)

            if result.success:
                return result.output_file
            else:
                return None

        except Exception as e:
            print(f"Audio conversion error: {str(e)}")
            return None
