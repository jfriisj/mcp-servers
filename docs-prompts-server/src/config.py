"""
Configuration management for the Documentation and Prompts MCP Server
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages configuration loading and validation"""

    def __init__(self, config_path: Optional[Path] = None, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_path = config_path
        self._config = None

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy load configuration"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "documentation_paths": [
                "**/*.md",
                "**/*.rst",
                "**/*.txt",
                "**/*.yaml",
                "**/*.yml",
                "**/*.json",
                "docs/",
                "documentation/",
                ".spec-workflow/",
                "README.md",
                "API.md",
                "ARCHITECTURE.md",
                "CONTRIBUTING.md",
                "CHANGELOG.md"
            ],
            "file_patterns": ["*.md", "*.rst", "*.txt", "*.yaml", "*.yml", "*.json"],
            "exclude_patterns": [
                "node_modules/", ".git/", "__pycache__/", "*.pyc",
                ".env*", "venv/", ".venv/", "dist/", "build/",
                ".pytest_cache/", "coverage/", "**/.*"
            ],
            "max_file_size_mb": 10,
            "architecture_keywords": [
                "architecture", "design", "pattern", "microservice", "api",
                "endpoint", "service", "component", "module", "database",
                "schema", "model", "workflow", "deployment", "infrastructure",
                "system", "integration"
            ],
            "prompt_categories": [
                "code-quality", "architecture", "documentation", "testing",
                "refactoring", "api", "security", "custom"
            ],
            "path_resolution": {
                "enforce_project_root_relative": True,
                "normalize_absolute_paths": True,
                "allow_absolute_paths": False
            }
        }

        if self.config_path and self.config_path.exists():
            logger.info(f"Loading config from {self.config_path}")
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config from {self.config_path}: {e}")

        # Validate and normalize documentation paths
        self._validate_and_normalize_paths(default_config)

        return default_config

    def _validate_and_normalize_paths(self, config: Dict[str, Any]):
        """Validate and normalize documentation paths to ensure they're project-root relative"""
        path_resolution_config = config.get("path_resolution", {})
        enforce_relative = path_resolution_config.get("enforce_project_root_relative", True)
        normalize_absolute = path_resolution_config.get("normalize_absolute_paths", True)
        allow_absolute = path_resolution_config.get("allow_absolute_paths", False)

        if not enforce_relative:
            logger.warning("Path resolution enforcement is disabled - paths may not be project-root relative")
            return

        documentation_paths = config.get("documentation_paths", [])
        normalized_paths = []

        for path_str in documentation_paths:
            path_obj = Path(path_str)

            # Check if path is absolute
            if path_obj.is_absolute():
                if not allow_absolute:
                    if normalize_absolute:
                        # Try to make it relative to project root
                        try:
                            relative_path = path_obj.relative_to(self.project_root)
                            logger.info(f"Normalized absolute path '{path_str}' to relative path '{relative_path}'")
                            normalized_paths.append(str(relative_path))
                        except ValueError:
                            # Path is not within project root
                            logger.error(f"Absolute path '{path_str}' is not within project root '{self.project_root}' and absolute paths are not allowed")
                            raise ValueError(f"Documentation path '{path_str}' must be relative to project root or within project root directory")
                    else:
                        logger.error(f"Absolute documentation paths are not allowed: '{path_str}'")
                        raise ValueError(f"Documentation path '{path_str}' must be relative to project root")
                else:
                    # Absolute paths are allowed
                    normalized_paths.append(path_str)
            else:
                # Path is already relative - ensure it's valid
                if ".." in path_str:
                    logger.warning(f"Path '{path_str}' contains '..' which may navigate outside project root")
                normalized_paths.append(path_str)

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in normalized_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        config["documentation_paths"] = unique_paths
        logger.info(f"Validated {len(unique_paths)} documentation paths as project-root relative")
