"""BatchTranscribeUseCase - Parallel batch audio transcription.

This use case handles transcription of multiple audio files in parallel,
with configurable concurrency limits to prevent resource exhaustion.

Workflow:
1. Validate batch configuration
2. Create transcription tasks for each file
3. Process in batches respecting concurrency limits
4. Collect results and statistics
5. Return BatchTranscriptionResult
"""

import asyncio
from typing import List

# Import the transcribe audio use case
from application.use_cases.transcribe_audio_use_case import (
    TranscribeAudioUseCase,
)
from domain.interfaces import IConfigurationProvider
from domain.models import (
    BatchTranscriptionConfig,
    BatchTranscriptionResult,
    TranscriptionConfig,
    TranscriptionResult,
)


class BatchTranscribeUseCase:
    """Use case for batch transcription of multiple audio files."""

    def __init__(
        self,
        transcribe_audio_use_case: TranscribeAudioUseCase,
        config_provider: IConfigurationProvider,
    ):
        """Initialize the use case with injected dependencies.

        Args:
            transcribe_audio_use_case: Use case for transcribing audio
            config_provider: Configuration provider
        """
        self._transcribe_audio = transcribe_audio_use_case
        self._config_provider = config_provider

    async def execute(
        self, config: BatchTranscriptionConfig
    ) -> BatchTranscriptionResult:
        """Execute batch transcription.

        Args:
            config: Batch transcription configuration

        Returns:
            BatchTranscriptionResult with results for all files
        """
        # Get server configuration for concurrency limits
        server_config = self._config_provider.get_server_config()
        max_concurrent = getattr(
            server_config, "max_concurrent_transcriptions", 3
        )

        # Create transcription tasks for each file
        tasks = []
        for audio_file in config.audio_files:
            # Create individual transcription config
            transcription_config = TranscriptionConfig(
                audio_file=audio_file,
                model=config.model,
                language=config.language,
                response_format=config.response_format,
                temperature=config.temperature,
            )
            tasks.append(
                self._transcribe_single_file(transcription_config)
            )

        # Process in batches to respect concurrency limits
        results: List[TranscriptionResult] = []
        for i in range(0, len(tasks), max_concurrent):
            batch_tasks = tasks[i: i + max_concurrent]
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
                            f"Batch processing error: {str(result)}"
                        ),
                    )
                    results.append(error_result)
                elif isinstance(result, TranscriptionResult):
                    results.append(result)
                else:
                    # Unexpected result type
                    error_result = TranscriptionResult(
                        text="",
                        success=False,
                        error_message=(
                            "Unexpected result type in batch processing"
                        ),
                    )
                    results.append(error_result)

        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BatchTranscriptionResult(
            results=results,
            total_files=len(config.audio_files),
            successful_transcriptions=successful,
            failed_transcriptions=failed,
            success=failed == 0,
        )

    async def _transcribe_single_file(
        self, config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Transcribe a single file (internal helper).

        Args:
            config: Transcription configuration

        Returns:
            TranscriptionResult
        """
        try:
            return await self._transcribe_audio.execute(config)
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error_message=f"File transcription failed: {str(e)}",
            )
