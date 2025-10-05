"""
Temporary File Manager Adapter - Infrastructure Adapter
========================================================
Manages temporary files and directories for audio processing.

This adapter combines the functionality of TempDirectoryManager and
TempFileManager into a single, cohesive interface for temp file management.

Implements: ITempFileManager from domain layer
Dependencies: None (uses standard library tempfile)
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from domain.interfaces import ITempFileManager


class TempFileManagerAdapter(ITempFileManager):
    """
    Temporary file and directory management adapter.

    Combines functionality from TempDirectoryManager and TempFileManager
    to provide unified temp file handling with automatic cleanup tracking.
    """

    def __init__(self):
        """Initialize temp file manager with tracking lists."""
        self._temp_files: List[str] = []
        self._temp_directories: List[str] = []

    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "",
        content: Optional[bytes] = None,
    ) -> str:
        """
        Create a temporary file.

        Args:
            suffix: File extension (e.g., '.wav', '.mp3')
            prefix: File name prefix
            content: Optional initial content to write

        Returns:
            Path to created temporary file
        """
        # Create temp file with specified parameters
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)

        # Write content if provided
        if content:
            os.write(fd, content)

        # Close file descriptor
        os.close(fd)

        # Track for cleanup
        self._temp_files.append(temp_path)

        return temp_path

    def create_temp_directory(self, prefix: str = "whisper_") -> str:
        """
        Create a temporary directory.

        Args:
            prefix: Directory name prefix

        Returns:
            Path to created temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self._temp_directories.append(temp_dir)
        return temp_dir

    def cleanup_all(self) -> None:
        """
        Clean up all temporary files and directories created by this manager.

        Removes all tracked temp files and recursively removes all tracked
        temp directories. Errors are silently ignored to prevent cleanup
        failures from breaking the application.
        """
        # Clean up temp files
        for file_path in self._temp_files:
            self.cleanup_file(file_path)

        # Clean up temp directories
        for dir_path in self._temp_directories:
            try:
                if Path(dir_path).exists():
                    shutil.rmtree(dir_path)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors

        # Clear tracking lists
        self._temp_files.clear()
        self._temp_directories.clear()

    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a specific temporary file.

        Args:
            file_path: Path to file to clean up

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if Path(file_path).exists():
                os.unlink(file_path)
                # Remove from tracking list if present
                if file_path in self._temp_files:
                    self._temp_files.remove(file_path)
                return True
        except (OSError, PermissionError):
            pass

        return False

    def add_file_for_cleanup(self, file_path: str) -> None:
        """
        Add an existing file to cleanup tracking.

        Useful when files are created outside this manager but need
        to be tracked for cleanup.

        Args:
            file_path: Path to file to track
        """
        if file_path not in self._temp_files:
            self._temp_files.append(file_path)

    def add_directory_for_cleanup(self, dir_path: str) -> None:
        """
        Add an existing directory to cleanup tracking.

        Args:
            dir_path: Path to directory to track
        """
        if dir_path not in self._temp_directories:
            self._temp_directories.append(dir_path)

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup_all()
