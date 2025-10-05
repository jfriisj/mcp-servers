"""
Configuration Adapter - Infrastructure Adapter
===============================================
Provides access to server and Whisper configuration settings.

Handles Hugging Face authentication, settings, and environment configuration.
Loads configuration from YAML files and environment variables.

Implements: IConfigurationProvider from domain layer
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from domain.interfaces import IConfigurationProvider

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly


class ConfigurationAdapter(IConfigurationProvider):
    """
    Configuration provider implementing domain interface.

    This adapter loads configuration from YAML files and environment variables,
    providing a clean interface to configuration settings while hiding
    implementation details.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration adapter.

        Args:
            project_root: Project root directory for config file location
        """
        self.project_root = project_root or Path.cwd()
        self._hf_token: Optional[str] = None
        self._config: Optional[Dict[str, Any]] = None

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy load configuration"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "model": {
                "name": "openai/whisper-large-v3",
                "device": "cuda",
            },
            "audio": {
                "supported_formats": [
                    "mp3", "mp4", "mpeg", "mpga", "m4a",
                    "wav", "webm", "flac", "ogg",
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
                "quality": "high",
                "temp_dir": None,
                "cleanup_temp_files": True,
                "supported_input_formats": [
                    "mp4", "mov", "avi", "mkv", "wmv",
                    "flv", "webm", "3gp", "m4v",
                    "aac", "ac3", "aiff", "amr", "ape",
                    "au", "dts", "mka", "mpc",
                    "ra", "wma", "opus", "spx", "tta",
                    "voc", "wv", "xa",
                    "caf", "dss", "dvf", "gsm", "iff",
                    "m4r", "mmf", "mxf", "nist",
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
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(default_config, user_config)
            except ImportError:
                pass
            except (OSError, yaml.YAMLError):  # File or YAML errors
                pass

        return default_config

    def _merge_config(
        self, base_config: Dict[str, Any], user_config: Dict[str, Any]
    ) -> None:
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

    # Domain interface methods
    def get_whisper_config(self) -> Dict[str, Any]:
        """Get Whisper model configuration."""
        token_env_vars = self.config["huggingface"]["token_env_vars"]
        hf_token = self._hf_token
        if hf_token is None:
            for env_var in token_env_vars:
                token = os.getenv(env_var)
                if token:
                    hf_token = token
                    self._hf_token = token
                    break

        device = self.config["model"]["device"]
        use_gpu = self.config["processing"]["use_gpu"]
        if use_gpu:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        else:
            device = "cpu"

        cache_dir = self.config["huggingface"]["cache_dir"]
        if cache_dir is None:
            cache_dir = os.getenv("HF_HOME")

        return {
            "model_name": self.config["model"]["name"],
            "device": device,
            "use_gpu": use_gpu,
            "cache_dir": cache_dir,
            "huggingface_token": hf_token,
        }

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return {
            "supported_audio_formats": (
                self.config["audio"]["supported_formats"]
            ),
            "max_file_size_mb": self.config["audio"]["max_file_size_mb"],
            "max_concurrent_transcriptions": (
                self.config["processing"]["max_concurrent_transcriptions"]
            ),
            "parallel_processing_enabled": (
                self.config["processing"]["parallel_processing_enabled"]
            ),
        }

    def get_segmentation_config(self) -> Dict[str, Any]:
        """Get audio segmentation configuration."""
        return {
            "enable_segmentation": (
                self.config["audio"]["enable_segmentation"]
            ),
            "segment_length_seconds": (
                self.config["audio"]["segment_length_seconds"]
            ),
            "segment_overlap_seconds": (
                self.config["audio"]["segment_overlap_seconds"]
            ),
            "max_segments_per_file": (
                self.config["audio"]["max_segments_per_file"]
            ),
        }

    def get_conversion_config(self) -> Dict[str, Any]:
        """Get audio conversion configuration."""
        return {
            "enable_conversion": (
                self.config["conversion"]["enable_conversion"]
            ),
            "quality": self.config["conversion"]["quality"],
            "temp_dir": self.config["conversion"]["temp_dir"],
            "cleanup_temp_files": (
                self.config["conversion"]["cleanup_temp_files"]
            ),
            "supported_formats": (
                self.config["conversion"]["supported_input_formats"]
            ),
        }
