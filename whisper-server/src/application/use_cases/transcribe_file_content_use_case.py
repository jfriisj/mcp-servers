"""TranscribeFileContentUseCase - Transcribe base64-encoded audio content.

This use case handles transcription of audio content provided as base64-encoded
data, which is common in API scenarios where files are uploaded as encoded strings.

Workflow:
1. Validate base64 content
2. Decode to binary data
3. Detect audio format from binary data and hints
4. Save to temporary file with correct extension
5. Transcribe using TranscribeAudioUseCase
6. Clean up temporary file
"""

import base64
from typing import Optional

# Import the transcribe audio use case
from application.use_cases.transcribe_audio_use_case import (
    TranscribeAudioUseCase,
)
from domain.interfaces import (
    IAudioFormatDetector,
    ITempFileManager,
)
from domain.models import TranscriptionConfig, TranscriptionResult


class TranscribeFileContentUseCase:
    """Use case for transcribing base64-encoded audio content."""

    def __init__(
        self,
        transcribe_audio_use_case: TranscribeAudioUseCase,
        format_detector: IAudioFormatDetector,
        temp_file_manager: ITempFileManager,
    ):
        """Initialize the use case with injected dependencies.

        Args:
            transcribe_audio_use_case: Use case for transcribing audio files
            format_detector: Audio format detector
            temp_file_manager: Temporary file manager
        """
        self._transcribe_audio = transcribe_audio_use_case
        self._format_detector = format_detector
        self._temp_file_manager = temp_file_manager

    async def execute(
        self,
        file_content: str,
        file_name: Optional[str] = None,
        file_format: Optional[str] = None,
        language: Optional[str] = None,
        model: str = "whisper-1",
        response_format: str = "json",
        temperature: float = 0.0,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """Execute base64 content transcription.

        Args:
            file_content: Base64-encoded audio file content
            file_name: Original filename (for format hint)
            file_format: Explicit format hint (e.g., 'mp3', 'wav')
            language: Language code (ISO-639-1)
            model: Whisper model to use
            response_format: Response format (json, text, srt, etc.)
            temperature: Sampling temperature
            prompt: Optional prompt to guide transcription

        Returns:
            TranscriptionResult with transcription text and metadata
        """
        # Validate base64 content
        if not file_content or not isinstance(file_content, str):
            return TranscriptionResult(
                text="",
                success=False,
                error_message="Invalid base64: must be non-empty string",
            )

        try:
            # Decode base64 content
            try:
                file_data = base64.b64decode(file_content, validate=True)
            except Exception as e:
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message=f"Invalid base64 content: {str(e)}",
                )

            # Detect file format from binary data, filename, and format hint
            detected_format = self._format_detector.detect_format(
                file_data=file_data,
                file_name=file_name,
                format_hint=file_format,
            )

            if not detected_format:
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message="Unsupported or unrecognized audio format",
                )

            # Create temporary file with correct extension
            temp_suffix = f".{detected_format}"
            temp_file_path = self._temp_file_manager.create_temp_file(
                suffix=temp_suffix,
                prefix="upload_",
            )

            # Write binary data to temporary file
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_data)

            # Create transcription config for the temp file
            transcription_config = TranscriptionConfig(
                audio_file=temp_file_path,
                model=model,
                language=language,
                response_format=response_format,
                temperature=temperature,
                prompt=prompt,
            )

            # Transcribe using the audio transcription use case
            result = await self._transcribe_audio.execute(
                transcription_config
            )

            return result

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"File content transcription failed: {str(e)}",
            )
        finally:
            # Clean up temporary files
            self._temp_file_manager.cleanup_all()
