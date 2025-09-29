"""
Configuration management for Whisper MCP Server.
================================================
Handles Hugging Face authentication, settings, and environment configuration.
"""

import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly


class ConfigurationManager:
    """Manages configuration for the Whisper MCP server."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path.cwd()
        self._hf_token: Optional[str] = None

    @property
    def huggingface_token(self) -> Optional[str]:
        """Get Hugging Face token from environment."""
        if self._hf_token is None:
            token1 = os.getenv("HUGGINGFACE_TOKEN")
            token2 = os.getenv("HF_TOKEN")
            self._hf_token = token1 or token2
        return self._hf_token

    def validate_hf_token(self) -> bool:
        """Validate that Hugging Face token is available."""
        token = self.huggingface_token
        return token is not None and len(token.strip()) > 0

    @property
    def model_name(self) -> str:
        """Get the Whisper model name."""
        return os.getenv("WHISPER_MODEL", "openai/whisper-large-v3")

    @property
    def use_gpu(self) -> bool:
        """Check if GPU acceleration should be used."""
        return os.getenv("USE_GPU", "false").lower() in ("true", "1", "yes")

    @property
    def device(self) -> str:
        """Get the device to use for inference."""
        if self.use_gpu:
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return "cpu"

    @property
    def cache_dir(self) -> Optional[str]:
        """Get the model cache directory."""
        return os.getenv("HF_HOME")

    @property
    def supported_audio_formats(self) -> list:
        """Get list of supported audio formats."""
        return [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "flac", "ogg",
        ]

    @property
    def max_file_size_mb(self) -> int:
        """Get maximum file size in MB for audio files."""
        return 200  # Increased for large interview files

    @property
    def max_concurrent_transcriptions(self) -> int:
        """Get maximum number of concurrent transcriptions."""
        return int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", "3"))

    @property
    def parallel_processing_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        enabled = os.getenv("ENABLE_PARALLEL_PROCESSING", "true")
        return enabled.lower() in ("true", "1", "yes")

    def is_supported_format(self, file_path: str) -> bool:
        """Check if audio file format is supported."""
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        return file_ext in self.supported_audio_formats

    def validate_audio_file(
        self, file_path: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate audio file for transcription.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not Path(file_path).exists():
            return False, f"Audio file does not exist: {file_path}"

        if not self.is_supported_format(file_path):
            supported = ", ".join(self.supported_audio_formats)
            return False, f"Unsupported format. Supported: {supported}"

        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            msg = f"File too large: {file_size_mb:.1f}MB "
            msg += f"(max: {self.max_file_size_mb}MB)"
            return False, msg

        return True, None
