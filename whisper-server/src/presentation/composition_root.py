"""
Composition Root - Dependency Injection Container
=================================================
This is the ONLY place where concrete classes are instantiated and wired together.
All other code depends on interfaces, enabling true dependency inversion.

Following the Composition Root pattern:
- Single location for dependency wiring
- No service locator anti-pattern
- Pure dependency injection
- Easy to test (can create test composition root)

Architecture:
1. Infrastructure Layer: Adapters wrapping external services
2. Application Layer: Use cases orchestrating adapters
3. Presentation Layer: MCP/FastAPI consuming use cases
"""

from typing import Optional

# Application use cases
from application.use_cases import (
    BatchTranscribeUseCase,
    ConvertAudioUseCase,
    DetectLanguageUseCase,
    TranscribeAudioUseCase,
    TranscribeFileContentUseCase,
    TranscribeWithTimestampsUseCase,
)

# Domain interfaces (we depend on abstractions)
from domain.interfaces import (
    IAudioConverter,
    IAudioFormatDetector,
    IAudioSegmenter,
    IConfigurationProvider,
    ITempFileManager,
    IWhisperModel,
)

# Infrastructure adapters (concrete implementations)
from infrastructure.adapters import (
    AudioConverterAdapter,
    AudioFormatDetector,
    AudioSegmenterAdapter,
    ConfigurationAdapter,
    TempFileManagerAdapter,
    WhisperModelAdapter,
)

# Note: Adapters encapsulate external services internally
# No need to import ConfigurationManager, AudioSegmenter, AudioConverter


class CompositionRoot:
    """
    Dependency injection container that wires all components together.

    This is the composition root - the single place where we create
    concrete instances and wire dependencies. Everything else uses interfaces.

    Usage:
        root = CompositionRoot()
        result = await root.transcribe_audio.execute(config)
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the composition root.

        Args:
            project_root: Optional project root path for configuration
        """
        self._project_root = project_root

        # Infrastructure adapters (initialized in _initialize)
        self._format_detector: IAudioFormatDetector
        self._temp_file_manager: ITempFileManager
        self._config_adapter: IConfigurationProvider
        self._audio_segmenter_adapter: IAudioSegmenter
        self._audio_converter_adapter: IAudioConverter
        self._whisper_model_adapter: IWhisperModel

        # Use cases (initialized in _initialize)
        self._transcribe_audio_uc: TranscribeAudioUseCase
        self._detect_language_uc: DetectLanguageUseCase
        self._convert_audio_uc: ConvertAudioUseCase
        self._transcribe_file_content_uc: TranscribeFileContentUseCase
        self._batch_transcribe_uc: BatchTranscribeUseCase
        self._transcribe_timestamps_uc: TranscribeWithTimestampsUseCase

        # Initialize all components
        self._initialize()

    def _initialize(self) -> None:
        """Initialize all components in dependency order."""
        self._create_infrastructure_adapters()
        self._create_use_cases()

    def _create_infrastructure_adapters(self) -> None:
        """Create infrastructure adapters in dependency order."""
        # 1. Standalone adapters (no dependencies)
        self._format_detector = AudioFormatDetector()
        self._temp_file_manager = TempFileManagerAdapter()

        # 2. Configuration adapter (creates ConfigurationManager internally)
        from pathlib import Path
        project_path = Path(self._project_root) if self._project_root else None
        self._config_adapter = ConfigurationAdapter(project_path)

        # 3. External service adapters
        # AudioSegmenter (creates AudioSegmenter internally with defaults)
        self._audio_segmenter_adapter = AudioSegmenterAdapter(
            segment_length_seconds=300,  # 5 minutes
            overlap_seconds=10,
            max_segments=50,
        )

        # AudioConverter (creates AudioConverter internally)
        self._audio_converter_adapter = AudioConverterAdapter(
            temp_dir=None  # Uses system temp directory
        )

        # 4. WhisperModel adapter (depends on configuration)
        self._whisper_model_adapter = WhisperModelAdapter(
            self._config_adapter
        )

    def _create_use_cases(self) -> None:
        """Create use cases with injected dependencies."""
        # 1. Core transcription use case (used by others)
        self._transcribe_audio_uc = TranscribeAudioUseCase(
            whisper_model=self._whisper_model_adapter,
            audio_converter=self._audio_converter_adapter,
            format_detector=self._format_detector,
            temp_file_manager=self._temp_file_manager,
            config_provider=self._config_adapter,
        )

        # 2. Simple delegation use cases
        self._detect_language_uc = DetectLanguageUseCase(
            whisper_model=self._whisper_model_adapter
        )

        self._convert_audio_uc = ConvertAudioUseCase(
            audio_converter=self._audio_converter_adapter
        )

        # 3. Composite use cases (depend on TranscribeAudioUseCase)
        self._transcribe_file_content_uc = TranscribeFileContentUseCase(
            transcribe_audio_use_case=self._transcribe_audio_uc,
            format_detector=self._format_detector,
            temp_file_manager=self._temp_file_manager,
        )

        self._batch_transcribe_uc = BatchTranscribeUseCase(
            transcribe_audio_use_case=self._transcribe_audio_uc,
            config_provider=self._config_adapter,
        )

        # 4. Complex use cases
        self._transcribe_timestamps_uc = TranscribeWithTimestampsUseCase(
            whisper_model=self._whisper_model_adapter,
            audio_segmenter=self._audio_segmenter_adapter,
            temp_file_manager=self._temp_file_manager,
            config_provider=self._config_adapter,
        )

    # Public interface - expose use cases via properties
    # This is what the presentation layer (MCP/FastAPI) will access

    @property
    def transcribe_audio(self) -> TranscribeAudioUseCase:
        """Get the transcribe audio use case."""
        return self._transcribe_audio_uc

    @property
    def detect_language(self) -> DetectLanguageUseCase:
        """Get the detect language use case."""
        return self._detect_language_uc

    @property
    def convert_audio(self) -> ConvertAudioUseCase:
        """Get the convert audio use case."""
        return self._convert_audio_uc

    @property
    def transcribe_file_content(self) -> TranscribeFileContentUseCase:
        """Get the transcribe file content use case."""
        return self._transcribe_file_content_uc

    @property
    def batch_transcribe(self) -> BatchTranscribeUseCase:
        """Get the batch transcribe use case."""
        return self._batch_transcribe_uc

    @property
    def transcribe_with_timestamps(
        self,
    ) -> TranscribeWithTimestampsUseCase:
        """Get the transcribe with timestamps use case."""
        return self._transcribe_timestamps_uc

    # Helper methods for presentation layer

    def get_whisper_model(self) -> IWhisperModel:
        """Get the Whisper model adapter (for direct access if needed)."""
        return self._whisper_model_adapter

    def get_configuration(self) -> IConfigurationProvider:
        """Get the configuration provider (for direct access if needed)."""
        return self._config_adapter
