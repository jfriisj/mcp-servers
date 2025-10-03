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
        self._config = None

    @property
    def config(self) -> dict:
        """Lazy load configuration"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        default_config = {
            "model": {
                "name": "openai/whisper-large-v3",
                "device": "cuda",
            },
            "audio": {
                "supported_formats": [
                    "mp3",
                    "mp4",
                    "mpeg",
                    "mpga",
                    "m4a",
                    "wav",
                    "webm",
                    "flac",
                    "ogg",
                ],
                "max_file_size_mb": 200,
                "segment_length_seconds": 30,
                "segment_overlap_seconds": 2,
                "max_segments_per_file": 50,
                "enable_segmentation": True,
            },
            "processing": {
                "max_concurrent_transcriptions": 3,
                "parallel_processing_enabled": True,
                "use_gpu": True,
            },
            "conversion": {
                "enable_conversion": True,
                "quality": "high",  # high, medium, low
                "temp_dir": None,  # If None, uses system temp
                "cleanup_temp_files": True,
                "supported_input_formats": [
                    # Video formats (extract audio)
                    "mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "3gp", "m4v",
                    # Audio formats that may need conversion
                    "aac", "ac3", "aiff", "amr", "ape", "au", "dts", "mka", "mpc",
                    "ra", "wma", "opus", "spx", "tta", "voc", "wv", "xa",
                    # Less common formats
                    "caf", "dss", "dvf", "gsm", "iff", "m4r", "mmf", "mxf", "nist",
                    "pvf", "raw", "sln", "vms", "vox", "w64"
                ],
            },
            "huggingface": {
                "token_env_vars": ["HUGGINGFACE_TOKEN", "HF_TOKEN"],
                "cache_dir": None,
            },
            "environment": {
                "test_mode": False,
            },
        }

        # Try to load from config file
        config_path = self.project_root / "config" / "server_config.yaml"
        if config_path.exists():
            try:
                import yaml

                with open(config_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(default_config, user_config)
            except ImportError:
                # YAML not available, use defaults
                pass
            except Exception:
                # Error loading config, use defaults
                pass

        return default_config

    def _merge_config(self, base_config: dict, user_config: dict) -> None:
        """Recursively merge user config into base config"""
        for key, value in user_config.items():
            if (
                key in base_config
                and isinstance(base_config[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    @property
    def huggingface_token(self) -> Optional[str]:
        """Get Hugging Face token from environment."""
        if self._hf_token is None:
            token_env_vars = self.config["huggingface"]["token_env_vars"]
            for env_var in token_env_vars:
                token = os.getenv(env_var)
                if token:
                    self._hf_token = token
                    break
        return self._hf_token

    def validate_hf_token(self) -> bool:
        """Validate that Hugging Face token is available."""
        token = self.huggingface_token
        return token is not None and len(token.strip()) > 0

    @property
    def model_name(self) -> str:
        """Get the Whisper model name."""
        return self.config["model"]["name"]

    @property
    def use_gpu(self) -> bool:
        """Check if GPU acceleration should be used."""
        return self.config["processing"]["use_gpu"]

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
        cache_dir = self.config["huggingface"]["cache_dir"]
        if cache_dir is None:
            cache_dir = os.getenv("HF_HOME")
        return cache_dir

    @property
    def supported_audio_formats(self) -> list:
        """Get list of supported audio formats."""
        return self.config["audio"]["supported_formats"]

    @property
    def max_file_size_mb(self) -> int:
        """Get maximum file size in MB for audio files."""
        return self.config["audio"]["max_file_size_mb"]

    @property
    def max_concurrent_transcriptions(self) -> int:
        """Get maximum number of concurrent transcriptions."""
        return self.config["processing"]["max_concurrent_transcriptions"]

    @property
    def parallel_processing_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        return self.config["processing"]["parallel_processing_enabled"]

    @property
    def segment_length_seconds(self) -> int:
        """Get segment length for audio segmentation in seconds."""
        return self.config["audio"]["segment_length_seconds"]

    @property
    def segment_overlap_seconds(self) -> int:
        """Get segment overlap for audio segmentation in seconds."""
        return self.config["audio"]["segment_overlap_seconds"]

    @property
    def max_segments_per_file(self) -> int:
        """Get maximum number of segments per file."""
        return self.config["audio"]["max_segments_per_file"]

    @property
    def enable_segmentation(self) -> bool:
        """Check if audio segmentation is enabled."""
        return self.config["audio"]["enable_segmentation"]

    def is_supported_format(self, file_path: str) -> bool:
        """Check if audio file format is supported."""
        file_ext = Path(file_path).suffix.lower().lstrip(".")
        return file_ext in self.supported_audio_formats

    @property
    def enable_conversion(self) -> bool:
        """Check if audio conversion is enabled."""
        return self.config["conversion"]["enable_conversion"]

    @property
    def conversion_quality(self) -> str:
        """Get conversion quality setting."""
        return self.config["conversion"]["quality"]

    @property
    def conversion_temp_dir(self) -> Optional[str]:
        """Get conversion temporary directory."""
        temp_dir = self.config["conversion"]["temp_dir"]
        return temp_dir if temp_dir else None

    @property
    def conversion_cleanup_temp_files(self) -> bool:
        """Check if temporary files should be cleaned up after conversion."""
        return self.config["conversion"]["cleanup_temp_files"]

    @property
    def conversion_supported_formats(self) -> list:
        """Get list of formats that can be converted."""
        return self.config["conversion"]["supported_input_formats"]

    def validate_audio_file(
        self,
        file_path: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate audio file for transcription.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not Path(file_path).exists():
            return False, f"Audio file does not exist: {file_path}"

        if not self.is_supported_format(file_path):
            # Check if it's a convertible format
            file_ext = Path(file_path).suffix.lower().lstrip(".")
            if self.enable_conversion and file_ext in self.conversion_supported_formats:
                # File can be converted, so it's acceptable
                return True, None
            
            supported = ", ".join(self.supported_audio_formats)
            convertible = ", ".join(self.conversion_supported_formats) if self.enable_conversion else ""
            error_msg = f"Unsupported format. Supported: {supported}"
            if convertible:
                error_msg += f". Convertible: {convertible}"
            return False, error_msg

        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            msg = f"File too large: {file_size_mb:.1f}MB "
            msg += f"(max: {self.max_file_size_mb}MB)"
            return False, msg

        return True, None
