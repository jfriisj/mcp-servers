"""
Configuration Adapter - Infrastructure Adapter
===============================================
Provides access to server and Whisper configuration settings.

Wraps the existing ConfigurationManager to implement the domain interface,
enabling dependency injection and testability.

Implements: IConfigurationProvider from domain layer
Dependencies: Existing config.py ConfigurationManager
"""

from pathlib import Path
from typing import Any, Dict, Optional

from config import ConfigurationManager
from domain.interfaces import IConfigurationProvider


class ConfigurationAdapter(IConfigurationProvider):
    """
    Configuration provider adapter wrapping ConfigurationManager.

    This adapter provides a clean interface to configuration settings
    while hiding the implementation details of how config is loaded
    (YAML files, environment variables, etc.).
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration adapter.

        Args:
            project_root: Project root directory for config file location
        """
        self._config_manager = ConfigurationManager(project_root)

    def get_whisper_config(self) -> Dict[str, Any]:
        """
        Get Whisper model configuration.

        Returns:
            Dictionary with Whisper settings:
            - model_name: Name of Whisper model to use
            - device: Device for inference (cuda/cpu)
            - use_gpu: Whether to use GPU acceleration
            - cache_dir: Model cache directory
            - huggingface_token: HF token for model access
        """
        return {
            "model_name": self._config_manager.model_name,
            "device": self._config_manager.device,
            "use_gpu": self._config_manager.use_gpu,
            "cache_dir": self._config_manager.cache_dir,
            "huggingface_token": self._config_manager.huggingface_token,
        }

    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.

        Returns:
            Dictionary with server settings:
            - supported_audio_formats: List of Whisper-native formats
            - max_file_size_mb: Maximum audio file size
            - max_concurrent_transcriptions: Concurrent processing limit
            - parallel_processing_enabled: Whether parallel mode is enabled
        """
        return {
            "supported_audio_formats": (
                self._config_manager.supported_audio_formats
            ),
            "max_file_size_mb": self._config_manager.max_file_size_mb,
            "max_concurrent_transcriptions": (
                self._config_manager.max_concurrent_transcriptions
            ),
            "parallel_processing_enabled": (
                self._config_manager.parallel_processing_enabled
            ),
        }

    def get_segmentation_config(self) -> Dict[str, Any]:
        """
        Get audio segmentation configuration.

        Returns:
            Dictionary with segmentation settings:
            - enable_segmentation: Whether segmentation is enabled
            - segment_length_seconds: Length of each segment
            - segment_overlap_seconds: Overlap between segments
            - max_segments_per_file: Maximum segments allowed
        """
        return {
            "enable_segmentation": self._config_manager.enable_segmentation,
            "segment_length_seconds": (
                self._config_manager.segment_length_seconds
            ),
            "segment_overlap_seconds": (
                self._config_manager.segment_overlap_seconds
            ),
            "max_segments_per_file": (
                self._config_manager.max_segments_per_file
            ),
        }

    def get_conversion_config(self) -> Dict[str, Any]:
        """
        Get audio conversion configuration.

        Returns:
            Dictionary with conversion settings:
            - enable_conversion: Whether conversion is enabled
            - quality: Conversion quality (high/medium/low)
            - temp_dir: Temporary directory for conversion
            - cleanup_temp_files: Whether to clean up temp files
            - supported_formats: List of convertible formats
        """
        return {
            "enable_conversion": self._config_manager.enable_conversion,
            "quality": self._config_manager.conversion_quality,
            "temp_dir": self._config_manager.conversion_temp_dir,
            "cleanup_temp_files": (
                self._config_manager.conversion_cleanup_temp_files
            ),
            "supported_formats": (
                self._config_manager.conversion_supported_formats
            ),
        }

    # Additional helper methods for direct access
    @property
    def config_manager(self) -> ConfigurationManager:
        """
        Get underlying ConfigurationManager for legacy code compatibility.

        Note: This is temporary during refactoring. New code should use
        the interface methods instead.
        """
        return self._config_manager
