"""TranscribeWithTimestampsUseCase - Audio transcription with timestamps.

This use case handles transcription of audio files with word/segment-level
timestamps. For large files, it automatically segments the audio and processes
segments in parallel, then combines results with adjusted timestamps.

Workflow:
1. Check if file needs segmentation (based on size/duration)
2. If small: Simple transcription with timestamps
3. If large:
   a. Segment audio into chunks
   b. Process segments in parallel
   c. Combine results with timestamp adjustments
   d. Clean up segment files
"""

import asyncio
from typing import Any, Dict, List

from domain.interfaces import (
    IAudioSegmenter,
    IConfigurationProvider,
    ITempFileManager,
    IWhisperModel,
)
from domain.models import (
    TranscriptionConfig,
    TranscriptionResult,
    TranscriptionWithTimestampsConfig,
)


class TranscribeWithTimestampsUseCase:
    """Use case for transcription with word/segment timestamps."""

    def __init__(
        self,
        whisper_model: IWhisperModel,
        audio_segmenter: IAudioSegmenter,
        temp_file_manager: ITempFileManager,
        config_provider: IConfigurationProvider,
    ):
        """Initialize the use case with injected dependencies.

        Args:
            whisper_model: Whisper model for transcription
            audio_segmenter: Audio segmentation service
            temp_file_manager: Temporary file manager
            config_provider: Configuration provider
        """
        self._whisper_model = whisper_model
        self._audio_segmenter = audio_segmenter
        self._temp_file_manager = temp_file_manager
        self._config_provider = config_provider

    async def execute(
        self, config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Execute transcription with timestamps.

        Args:
            config: Transcription configuration

        Returns:
            TranscriptionResult with timestamps and segments
        """
        # Get segmentation configuration
        seg_config = self._config_provider.get_segmentation_config()
        segment_length = seg_config.get("segment_length", 300)
        overlap = seg_config.get("overlap", 10)

        # Create timestamps config
        timestamps_config = TranscriptionWithTimestampsConfig(
            audio_file=config.audio_file,
            model=config.model,
            language=config.language,
            response_format="verbose_json",
            temperature=config.temperature,
            prompt=config.prompt,
        )

        # For now, always attempt transcription with timestamps
        # TODO: Add file size check for segmentation decision
        try:
            # Try simple transcription first for smaller files
            return await self._whisper_model.transcribe_with_timestamps(
                timestamps_config
            )
        except Exception:
            # If it fails, proceed with segmentation

            pass

        # File is large, use segmentation
        try:
            # Create temporary directory for segments
            temp_dir = self._temp_file_manager.create_temp_directory()

            # Segment the audio file
            segments = await self._audio_segmenter.segment_audio(
                file_path=config.audio_file,
                segment_length_seconds=segment_length,
                overlap_seconds=overlap,
            )

            if not segments or len(segments) == 0:
                # Segmentation failed, return error
                return TranscriptionResult(
                    text="",
                    success=False,
                    error_message="Audio segmentation failed",
                )

            # Process segments in parallel
            segment_results = await self._process_segments_parallel(
                segments, config
            )

            # Combine results with adjusted timestamps
            combined_result = self._combine_segment_results(
                segment_results, segments
            )

            # Add segmentation metadata
            combined_result.was_segmented = True
            combined_result.total_segments = len(segments)
            combined_result.segments_info = [
                {
                    "start_time": seg["start_time"],
                    "end_time": seg["end_time"],
                    "duration": seg["duration"],
                    "temp_file": seg.get("temp_file_path", ""),
                }
                for seg in segments
            ]

            return combined_result

        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=(
                    f"Segmented transcription failed: {str(e)}"
                ),
            )
        finally:
            # Cleanup temporary files
            self._temp_file_manager.cleanup_all()

    async def _process_segments_parallel(
        self,
        segments: List[Dict[str, Any]],
        config: TranscriptionConfig,
    ) -> List[TranscriptionResult]:
        """Process audio segments in parallel.

        Args:
            segments: List of segment metadata dictionaries
            config: Original transcription configuration

        Returns:
            List of TranscriptionResult for each segment
        """
        # Get concurrency limit
        server_config = self._config_provider.get_server_config()
        max_concurrent = getattr(
            server_config, "max_concurrent_transcriptions", 3
        )

        # Create transcription tasks for each segment
        tasks = []
        for segment in segments:
            temp_file_path = segment.get("temp_file_path")
            if temp_file_path:
                # Create config for this segment
                segment_config = TranscriptionWithTimestampsConfig(
                    audio_file=temp_file_path,
                    model=config.model,
                    language=config.language,
                    response_format="verbose_json",
                    temperature=config.temperature,
                    prompt=config.prompt,
                )
                tasks.append(self._transcribe_segment(segment_config))

        # Process in batches to respect concurrency limits
        results: List[TranscriptionResult] = []
        for i in range(0, len(tasks), max_concurrent):
            batch_tasks = tasks[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *batch_tasks, return_exceptions=True
            )

            # Handle exceptions as failed transcriptions
            for result in batch_results:
                if isinstance(result, Exception):
                    error_result = TranscriptionResult(
                        text="",
                        success=False,
                        error_message=(
                            f"Segment processing error: {str(result)}"
                        ),
                    )
                    results.append(error_result)
                elif isinstance(result, TranscriptionResult):
                    results.append(result)

        return results

    async def _transcribe_segment(
        self, config: TranscriptionWithTimestampsConfig
    ) -> TranscriptionResult:
        """Transcribe a single audio segment.

        Args:
            config: Transcription with timestamps configuration

        Returns:
            TranscriptionResult for the segment
        """
        try:
            return await self._whisper_model.transcribe_with_timestamps(
                config
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
        segments: List[Dict[str, Any]],
    ) -> TranscriptionResult:
        """Combine results from multiple segments.

        Args:
            segment_results: List of TranscriptionResult from segments
            segments: List of segment metadata dictionaries

        Returns:
            Combined TranscriptionResult with adjusted timestamps
        """
        combined_text = ""
        combined_segments = []
        total_duration = 0.0

        for result, segment in zip(segment_results, segments):
            if result.success and result.text:
                # Add segment text
                combined_text += result.text + " "

                # Adjust timestamps if present
                if result.segments:
                    segment_start_time = segment["start_time"]
                    for chunk in result.segments:
                        adjusted_chunk = dict(chunk)

                        # Adjust timestamps by segment offset
                        if "timestamp" in adjusted_chunk:
                            timestamp = adjusted_chunk["timestamp"]
                            if isinstance(timestamp, (list, tuple)):
                                if len(timestamp) == 2:
                                    adjusted_chunk["timestamp"] = [
                                        timestamp[0] + segment_start_time,
                                        timestamp[1] + segment_start_time,
                                    ]
                            elif isinstance(timestamp, (int, float)):
                                adjusted_chunk["timestamp"] = (
                                    timestamp + segment_start_time
                                )

                        combined_segments.append(adjusted_chunk)

                total_duration += segment["duration"]

        # Clean up trailing space
        combined_text = combined_text.strip()

        return TranscriptionResult(
            text=combined_text,
            language=segment_results[0].language
            if segment_results
            else None,
            duration=total_duration,
            segments=combined_segments if combined_segments else None,
            success=True,
        )
