"""
Whisper API runner for Whisper MCP Server
============================================
Handles local Whisper model inference using Hugging Face transformers
    async def _transcribe_with_segmentation(
        self,
        config,  # Can be TranscriptionConfig or TranscriptionWithTimestampsConfig
        return_timestamps: bool,
    ) -> TranscriptionResult:"
=========================================="""

import asyncio
import os
import base64
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

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
    ConversionConfig,
    ConversionResult,
    FileContentTranscriptionConfig,
    LanguageDetectionConfig,
    LanguageDetectionResult,
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)
from audio_segmenter import AudioSegmenter, TempDirectoryManager
from audio_converter import AudioConverter, TempFileManager


class WhisperRunner:
    """Handles Whisper model operations using Hugging Face."""

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.pipe = None
        self._model_loaded = False
        self._segmenter = None
        self._temp_manager = TempDirectoryManager()
        self._converter = None
        self._conversion_temp_manager = TempFileManager()

    def _get_segmenter(self) -> Optional[AudioSegmenter]:
        """Get or create audio segmenter."""
        if not self._segmenter and self.config_manager.enable_segmentation:
            try:
                self._segmenter = AudioSegmenter(
                    segment_length_seconds=(self.config_manager.segment_length_seconds),
                    overlap_seconds=(self.config_manager.segment_overlap_seconds),
                    max_segments=self.config_manager.max_segments_per_file,
                )
            except ImportError:
                # Audio libraries not available
                pass
        return self._segmenter

    def _get_converter(self) -> Optional[AudioConverter]:
        """Get or create audio converter."""
        if not self._converter and self.config_manager.enable_conversion:
            try:
                self._converter = AudioConverter(
                    temp_dir=self.config_manager.conversion_temp_dir
                )
            except ImportError:
                # Conversion libraries not available
                pass
        return self._converter

    async def _ensure_file_compatible(self, file_path: str) -> Tuple[str, bool]:
        """Ensure audio file is compatible with Whisper, converting if necessary.
        
        Args:
            file_path: Path to the input audio file
            
        Returns:
            Tuple of (compatible_file_path, was_converted)
        """
        converter = self._get_converter()
        if not converter:
            # No converter available, assume file is compatible
            return file_path, False
        
        # Check if conversion is needed
        if not converter.needs_conversion(file_path):
            return file_path, False
        
        # File needs conversion
        try:
            # Get recommended output format based on input
            input_format = Path(file_path).suffix.lower().lstrip(".")
            output_format = converter.get_recommended_output_format(input_format)
            
            # Configure conversion
            conversion_config = ConversionConfig(
                input_file=file_path,
                output_format=output_format,
                quality=self.config_manager.conversion_quality,
                remove_input=False  # Don't remove original file
            )
            
            # Perform conversion
            result = await converter.convert_file(conversion_config)
            
            if result.success and result.output_file:
                # Track temp file for cleanup
                if result.temp_file:
                    self._conversion_temp_manager.add_temp_file(result.output_file)
                
                print(f"✅ Converted {input_format} to {output_format} using {result.conversion_method}")
                return result.output_file, True
            else:
                print(f"❌ Conversion failed: {result.error_message}")
                return file_path, False
                
        except Exception as e:
            print(f"❌ Conversion error: {str(e)}")
            return file_path, False

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
            dtype = torch.float16 if device == 0 else torch.float32

            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.config_manager.model_name,
                device=device,
                dtype=dtype,
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

        # Ensure file is compatible with Whisper (convert if necessary)
        try:
            compatible_file, was_converted = await self._ensure_file_compatible(config.audio_file)
            # Update config to use the compatible file
            if was_converted:
                config = TranscriptionConfig(
                    audio_file=compatible_file,
                    model=config.model,
                    language=config.language,
                    response_format=config.response_format,
                    temperature=config.temperature,
                    prompt=config.prompt,
                )
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"File conversion error: {str(e)}",
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

        # Check if segmentation should be used
        if self.config_manager.enable_segmentation:
            return await self._transcribe_with_segmentation(
                config, return_timestamps=False
            )

        # Regular transcription for small files
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

    async def _transcribe_with_segmentation(
        self,
        config: TranscriptionConfig,
        return_timestamps: bool = False,
    ) -> TranscriptionResult:
        """Transcribe audio file using segmentation for parallel processing."""
        segmenter = self._get_segmenter()
        if not segmenter:
            # Fall back to regular transcription
            return await self.transcribe_audio(config)

        # Check if segmentation is needed
        if not segmenter.should_segment_file(config.audio_file):
            # File is small enough, use regular transcription
            return await self.transcribe_audio(config)

        try:
            # Create temporary directory for segments
            temp_dir = self._temp_manager.create_temp_dir()

            # Segment the audio file
            segments = segmenter.segment_audio_file(
                config.audio_file, output_dir=temp_dir
            )

            if not segments:
                # Segmentation failed, fall back to regular transcription
                return await self.transcribe_audio(config)

            # Process segments in parallel
            segment_results = await self._process_segments_parallel(
                segments, config, return_timestamps
            )

            # Combine results
            combined_result = self._combine_segment_results(
                segment_results, segments, return_timestamps
            )

            # Add segmentation metadata
            combined_result.was_segmented = True
            combined_result.total_segments = len(segments)
            combined_result.segments_info = [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "duration": seg.duration,
                    "temp_file": seg.temp_file_path,
                }
                for seg in segments
            ]

            # Cleanup temporary files
            self._temp_manager.cleanup_all()

            return combined_result

        except Exception as e:
            # Cleanup on error
            self._temp_manager.cleanup_all()
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Segmented transcription failed: {str(e)}",
            )

    async def _process_segments_parallel(
        self,
        segments,
        config: TranscriptionConfig,
        return_timestamps: bool,
    ) -> List[TranscriptionResult]:
        """Process audio segments in parallel."""
        max_concurrent = self.config_manager.max_concurrent_transcriptions

        # Create transcription tasks for each segment
        tasks = []
        for segment in segments:
            if segment.temp_file_path:
                # Create a modified config for this segment
                segment_config = TranscriptionConfig(
                    audio_file=segment.temp_file_path,
                    model=config.model,
                    language=config.language,
                    response_format=config.response_format,
                    temperature=config.temperature,
                    prompt=config.prompt,
                )
                tasks.append(
                    self._transcribe_segment(segment_config, return_timestamps)
                )

        # Process in batches to respect concurrency limits
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch_tasks = tasks[i : i + max_concurrent]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    # Handle exceptions as failed transcriptions
                    error_result = TranscriptionResult(
                        text="",
                        success=False,
                        error_message=(f"Segment processing error: {str(result)}"),
                    )
                    results.append(error_result)
                else:
                    results.append(result)

        return results

    async def _transcribe_segment(
        self,
        config: TranscriptionConfig,
        return_timestamps: bool,
    ) -> TranscriptionResult:
        """Transcribe a single audio segment."""
        try:
            result = self.pipe(
                config.audio_file,
                return_timestamps=return_timestamps,
                generate_kwargs={
                    "language": config.language,
                    "task": "transcribe",
                },
            )

            text = ""
            segments_data = []
            if isinstance(result, dict):
                text = result.get("text", "")
                if return_timestamps and "chunks" in result:
                    segments_data = result["chunks"]
            elif isinstance(result, str):
                text = result

            return TranscriptionResult(
                text=text,
                language=config.language,
                segments=segments_data if return_timestamps else None,
                success=True,
            )
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"Segment transcription failed: {str(e)}",
            )

    def _combine_segment_results(
        self,
        segment_results: List[TranscriptionResult],
        segments,
        return_timestamps: bool,
    ) -> TranscriptionResult:
        """Combine results from multiple segments into a single result."""
        # Combine text from all segments
        combined_text = ""
        combined_segments = []
        total_duration = 0.0

        for i, (result, segment) in enumerate(zip(segment_results, segments)):
            if result.success and result.text:
                # Add segment text
                combined_text += result.text + " "

                # Adjust timestamps if present
                if return_timestamps and result.segments:
                    for chunk in result.segments:
                        adjusted_chunk = dict(chunk)
                        # Adjust timestamps by segment offset
                        if "timestamp" in adjusted_chunk:
                            timestamp = adjusted_chunk["timestamp"]
                            if (
                                isinstance(timestamp, (list, tuple))
                                and len(timestamp) == 2
                            ):
                                adjusted_chunk["timestamp"] = [
                                    timestamp[0] + segment.start_time,
                                    timestamp[1] + segment.start_time,
                                ]
                            elif isinstance(timestamp, (int, float)):
                                adjusted_chunk["timestamp"] = (
                                    timestamp + segment.start_time
                                )
                        combined_segments.append(adjusted_chunk)

                total_duration += segment.duration

        # Remove trailing space
        combined_text = combined_text.strip()

        return TranscriptionResult(
            text=combined_text,
            language=segment_results[0].language if segment_results else None,
            duration=total_duration,
            segments=combined_segments if return_timestamps else None,
            success=all(result.success for result in segment_results),
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

        # Ensure file is compatible with Whisper (convert if necessary)
        try:
            compatible_file, was_converted = await self._ensure_file_compatible(config.audio_file)
            # Update config to use the compatible file
            if was_converted:
                config = TranscriptionWithTimestampsConfig(
                    audio_file=compatible_file,
                    model=config.model,
                    language=config.language,
                    response_format=config.response_format,
                    temperature=config.temperature,
                    prompt=config.prompt,
                )
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"File conversion error: {str(e)}",
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

        # Check if segmentation should be used
        if self.config_manager.enable_segmentation:
            return await self._transcribe_with_segmentation(
                config, return_timestamps=True
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
        """Detect audio file format from binary data using magic bytes."""
        if len(file_data) < 12:
            return None

        # Check magic bytes for different audio formats
        if file_data.startswith(b"RIFF") and file_data[8:12] == b"WAVE":
            return "wav"
        elif (
            file_data.startswith(b"ID3")
            or file_data.startswith(b"\xff\xfb")
            or file_data.startswith(b"\xff\xf3")
            or file_data.startswith(b"\xff\xf2")
        ):
            return "mp3"
        elif file_data.startswith(b"ftypM4A") or file_data.startswith(b"ftypmp4"):
            return "m4a"
        elif file_data.startswith(b"fLaC"):
            return "flac"
        elif file_data.startswith(b"OggS"):
            return "ogg"
        elif file_data.startswith(b"wvpk"):
            return "wv"
        elif file_data[4:8] == b"ftyp":
            return "mp4"
        elif file_data.startswith(b"WEBM"):
            return "webm"

        # Additional checks for MP3 without ID3 tag
        if len(file_data) >= 2:
            first_two = file_data[:2]
            if first_two in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xf1"]:
                return "mp3"

        return None

    async def convert_audio_file(self, config: ConversionConfig) -> ConversionResult:
        """Convert an audio file using the configured converter.
        
        Args:
            config: Conversion configuration
            
        Returns:
            ConversionResult with conversion status and output file info
        """
        converter = self._get_converter()
        if not converter:
            return ConversionResult(
                success=False,
                error_message="Audio converter not available. Check configuration and dependencies."
            )
        
        return await converter.convert_file(config)
