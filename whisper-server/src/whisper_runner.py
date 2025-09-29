"""
Whisper API runner for Whisper MCP Server
==========================================
Handles local Whisper model inference using Hugging Face transformers.
"""

import asyncio
import os
import base64
import tempfile
from typing import Optional

# Hugging Face imports (with fallback for development)
try:
    import torch
    from transformers import pipeline

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    pipeline = None
    torch = None

from config import ConfigurationManager
from models import (
    BatchTranscriptionConfig,
    BatchTranscriptionResult,
    FileContentTranscriptionConfig,
    LanguageDetectionConfig,
    LanguageDetectionResult,
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)


class WhisperRunner:
    """Handles Whisper model operations using Hugging Face."""

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.pipe = None
        self._model_loaded = False

    def _ensure_model_loaded(self) -> bool:
        """Ensure the Whisper model is loaded."""
        if self._model_loaded:
            return True

        if not HAS_TRANSFORMERS or pipeline is None or torch is None:
            return False

        if not self.config_manager.validate_hf_token():
            return False

        try:
            # Set Hugging Face token
            token = self.config_manager.huggingface_token
            if token:
                os.environ["HUGGINGFACE_TOKEN"] = token

            # Determine device for pipeline: 0 for CUDA, -1 for CPU
            device = 0 if self.config_manager.device == "cuda" else -1
            torch_dtype = torch.float16 if device == 0 else torch.float32

            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.config_manager.model_name,
                device=device,
                torch_dtype=torch_dtype,
                model_kwargs={"cache_dir": self.config_manager.cache_dir},
            )

            self._model_loaded = True
            return True

        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            self.pipe = None
            return False

    async def transcribe_audio(
        self,
        config: TranscriptionConfig,
    ) -> TranscriptionResult:
        """Transcribe audio file to text."""
        if not self._ensure_model_loaded():
            return TranscriptionResult(
                text="",
                success=False,
                error_message="Whisper model not loaded. Check HF token.",
            )

        # Validate audio file
        is_valid, error_msg = self.config_manager.validate_audio_file(
            config.audio_file,
        )
        if not is_valid:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=error_msg,
            )

        try:
            # Run transcription
            result = self.pipe(
                config.audio_file,
                return_timestamps=False,
                generate_kwargs={
                    "language": config.language,
                    "task": "transcribe",
                },
            )
            text = ""
            if isinstance(result, dict) and "text" in result:
                text = result["text"]
            elif isinstance(result, str):
                text = result
            else:
                text = str(result)
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
        self,
        config: TranscriptionWithTimestampsConfig,
    ) -> TranscriptionResult:
        """Transcribe audio file with timestamps."""
        if not self._ensure_model_loaded():
            return TranscriptionResult(
                text="",
                success=False,
                error_message="Whisper model not loaded. Check HF token.",
            )

        # Validate audio file
        is_valid, error_msg = self.config_manager.validate_audio_file(
            config.audio_file,
        )
        if not is_valid:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=error_msg,
            )

        try:
            # Run transcription with timestamps
            result = self.pipe(
                config.audio_file,
                return_timestamps=True,
                generate_kwargs={
                    "language": config.language,
                    "task": "transcribe",
                },
            )
            text = ""
            segments = []
            if isinstance(result, dict):
                text = result.get("text", "")
                if "chunks" in result:
                    segments = [
                        {
                            "timestamp": chunk.get("timestamp"),
                            "text": chunk.get("text"),
                        }
                        for chunk in result["chunks"]
                    ]
            elif isinstance(result, str):
                text = result
            else:
                text = str(result)
            return TranscriptionResult(
                text=text,
                language=config.language,
                duration=None,  # Would need additional processing
                segments=segments,
                success=True,
            )
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Transcription with timestamps failed: {str(e)}",
            )

    async def detect_language(
        self,
        config: LanguageDetectionConfig,
    ) -> LanguageDetectionResult:
        """Detect the language of an audio file."""
        if not self._ensure_model_loaded():
            return LanguageDetectionResult(
                detected_language="",
                confidence=0.0,
                success=False,
                error_message="Whisper model not loaded. Check HF token.",
            )

        # Validate audio file
        is_valid, error_msg = self.config_manager.validate_audio_file(
            config.audio_file,
        )
        if not is_valid:
            return LanguageDetectionResult(
                detected_language="",
                confidence=0.0,
                success=False,
                error_message=error_msg,
            )

        try:
            # Use language detection pipeline
            lang_pipe = pipeline(
                "audio-classification",
                model="openai/whisper-tiny",
                device=self.config_manager.device,
            )

            # Run language detection on a short segment
            result = lang_pipe(config.audio_file)

            # Get the top language prediction
            if result and len(result) > 0:
                detected_lang = result[0]["label"]
                confidence = result[0]["score"]
            else:
                detected_lang = "unknown"
                confidence = 0.0

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

    async def batch_transcribe(
        self,
        config: BatchTranscriptionConfig,
    ) -> BatchTranscriptionResult:
        """Transcribe multiple audio files with parallel processing support."""
        if not self._ensure_model_loaded():
            return BatchTranscriptionResult(
                results=[],
                total_files=len(config.audio_files),
                successful_transcriptions=0,
                failed_transcriptions=len(config.audio_files),
                success=False,
                error_message="Whisper model not loaded. Check HF token.",
            )

        # Use parallel processing if enabled
        if (
            self.config_manager.parallel_processing_enabled
            and len(config.audio_files) > 1
        ):
            return await self._batch_transcribe_parallel(config)
        else:
            return await self._batch_transcribe_sequential(config)

    async def _batch_transcribe_sequential(
        self,
        config: BatchTranscriptionConfig,
    ) -> BatchTranscriptionResult:
        """Transcribe multiple audio files sequentially."""
        results = []
        successful = 0
        failed = 0

        for audio_file in config.audio_files:
            transcribe_config = TranscriptionConfig(
                audio_file=audio_file,
                model=config.model,
                language=config.language,
                response_format=config.response_format,
                temperature=config.temperature,
            )

            result = await self.transcribe_audio(transcribe_config)
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        return BatchTranscriptionResult(
            results=results,
            total_files=len(config.audio_files),
            successful_transcriptions=successful,
            failed_transcriptions=failed,
            success=failed == 0,
        )

    async def _batch_transcribe_parallel(
        self,
        config: BatchTranscriptionConfig,
    ) -> BatchTranscriptionResult:
        """Transcribe multiple audio files in parallel."""

        # Create transcription configs for each file
        transcribe_configs = []
        for audio_file in config.audio_files:
            transcribe_config = TranscriptionConfig(
                audio_file=audio_file,
                model=config.model,
                language=config.language,
                response_format=config.response_format,
                temperature=config.temperature,
            )
            transcribe_configs.append(transcribe_config)

        # Process in batches to respect max_concurrent_transcriptions limit
        max_concurrent = self.config_manager.max_concurrent_transcriptions
        results = []
        successful = 0
        failed = 0

        # Process files in chunks
        for i in range(0, len(transcribe_configs), max_concurrent):
            batch_configs = transcribe_configs[i : i + max_concurrent]

            # Run batch concurrently
            batch_results = await asyncio.gather(
                *[self.transcribe_audio(conf) for conf in batch_configs],
                return_exceptions=True,
            )

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    # Handle exceptions as failed transcriptions
                    error_msg = f"Parallel processing error: {str(result)}"
                    error_result = TranscriptionResult(
                        text="",
                        success=False,
                        error_message=error_msg,
                    )
                    results.append(error_result)
                    failed += 1
                elif isinstance(result, TranscriptionResult):
                    results.append(result)
                    if result.success:
                        successful += 1
                    else:
                        failed += 1

        return BatchTranscriptionResult(
            results=results,
            total_files=len(config.audio_files),
            successful_transcriptions=successful,
            failed_transcriptions=failed,
            success=failed == 0,
        )

    async def transcribe_file_content(
        self,
        config: "FileContentTranscriptionConfig",
    ) -> TranscriptionResult:
        """Transcribe audio file content (base64) to text."""
        if not self._ensure_model_loaded():
            return TranscriptionResult(
                text="",
                success=False,
                error_message="Whisper model not loaded. Check HF token.",
            )

        try:
            # Validate base64 format
            if not config.file_content or not isinstance(config.file_content, str):
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message="Invalid base64: must be non-empty string",
                )

            # Decode base64 content
            try:
                file_data = base64.b64decode(config.file_content, validate=True)
            except Exception as e:
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message=f"Invalid base64 content: {str(e)}",
                )

            # Detect file format from binary data
            detected_format = self._detect_audio_format(file_data)
            if not detected_format:
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message="Unsupported or unrecognized audio format",
                )

            # Create temporary file with correct extension
            temp_suffix = f".{detected_format}"
            with tempfile.NamedTemporaryFile(
                suffix=temp_suffix, delete=False
            ) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name

            try:
                # Validate the temporary file
                is_valid, error_msg = self.config_manager.validate_audio_file(
                    temp_file_path
                )
                if not is_valid:
                    return TranscriptionResult(
                        text="",
                        success=False,
                        error_message=f"Invalid audio file: {error_msg}",
                    )

                # Run transcription
                return_timestamps = config.response_format == "verbose_json"
                result = self.pipe(
                    temp_file_path,
                    return_timestamps=return_timestamps,
                    generate_kwargs={
                        "language": config.language,
                        "task": "transcribe",
                    },
                )

                text = ""
                if isinstance(result, dict) and "text" in result:
                    text = result["text"]
                elif isinstance(result, str):
                    text = result
                else:
                    text = str(result)

                return TranscriptionResult(
                    text=text,
                    language=config.language,
                    success=True,
                )

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"File content transcription failed: {str(e)}",
            )

    def _detect_audio_format(self, file_data: bytes) -> Optional[str]:
        """
        Detect audio file format from binary data using magic bytes.

        Returns the file extension (without dot) or None if not recognized.
        """
        if len(file_data) < 12:
            return None

        # Check magic bytes for different audio formats
        if file_data.startswith(b'RIFF') and file_data[8:12] == b'WAVE':
            return 'wav'
        elif (
            file_data.startswith(b'ID3')
            or file_data.startswith(b'\xFF\xFB')
            or file_data.startswith(b'\xFF\xF3')
            or file_data.startswith(b'\xFF\xF2')
        ):
            return 'mp3'
        elif (
            file_data.startswith(b'ftypM4A')
            or file_data.startswith(b'ftypmp4')
        ):
            return 'm4a'
        elif file_data.startswith(b'fLaC'):
            return 'flac'
        elif file_data.startswith(b'OggS'):
            return 'ogg'
        elif file_data.startswith(b'wvpk'):
            return 'wv'
        elif file_data[4:8] == b'ftyp':
            return 'mp4'
        elif file_data.startswith(b'WEBM'):
            return 'webm'

        # Additional checks for MP3 without ID3 tag
        if len(file_data) >= 2:
            first_two = file_data[:2]
            if first_two in [
                b'\xFF\xFB', b'\xFF\xF3', b'\xFF\xF2', b'\xFF\xF1'
            ]:
                return 'mp3'

        return None
