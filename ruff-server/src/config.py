"""
Configuration management for Ruff MCP Server
=============================================
Handles discovery and management of Ruff configuration files.
"""

from pathlib import Path
from typing import Optional


class ConfigurationManager:
    """Manages Ruff configuration file discovery and settings."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._pyproject_toml: Optional[Path] = None

    @property
    def pyproject_toml(self) -> Optional[Path]:
        """Get the pyproject.toml configuration file path."""
        if self._pyproject_toml is None:
            self._pyproject_toml = self._find_pyproject_toml()
        return self._pyproject_toml

    def _find_pyproject_toml(self) -> Optional[Path]:
        """Find pyproject.toml configuration file in project hierarchy."""
        for path in [self.project_root, *self.project_root.parents]:
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                return pyproject_path
        return None

    def get_config_args(self) -> list[str]:
        """Get configuration arguments for ruff commands."""
        if self.pyproject_toml:
            return ["--config", str(self.pyproject_toml)]
        return []
