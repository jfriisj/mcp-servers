"""
Configuration management for the Coverage MCP Server
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages configuration files and project settings"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.pyproject_toml = self._find_pyproject_toml()
        self.pytest_ini = self._find_pytest_config()

    def _find_pyproject_toml(self) -> Optional[Path]:
        """Find pyproject.toml configuration file."""
        for path in [self.project_root, *self.project_root.parents]:
            pyproject_path = path / "pyproject.toml"
            if pyproject_path.exists():
                logger.info("Found pyproject.toml at %s", pyproject_path)
                return pyproject_path
        logger.info("No pyproject.toml found")
        return None

    def _find_pytest_config(self) -> Optional[Path]:
        """Find pytest configuration file."""
        config_files = ["pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                logger.info("Found pytest config at %s", config_path)
                return config_path

        logger.info("No pytest configuration file found")
        return None

    @property
    def has_pyproject_config(self) -> bool:
        """Check if pyproject.toml exists"""
        return self.pyproject_toml is not None

    @property
    def has_pytest_config(self) -> bool:
        """Check if pytest config exists"""
        return self.pytest_ini is not None