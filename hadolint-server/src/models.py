"""
Data models for the Hadolint MCP Server
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HadolintResult:
    """Result of a hadolint run"""

    success: bool
    output: str
    error: Optional[str] = None
    issues_found: int = 0
    dockerfile_path: Optional[str] = None


@dataclass
class LintConfig:
    """Configuration for Dockerfile linting"""

    dockerfile_path: str
    config_file: Optional[str] = None
    ignore_rules: Optional[List[str]] = None
    format: str = "tty"  # tty, json, sarif, etc.
    no_color: bool = False
    verbose: bool = False


@dataclass
class DirectoryLintConfig:
    """Configuration for linting all Dockerfiles in a directory"""

    directory_path: str
    config_file: Optional[str] = None
    ignore_rules: Optional[List[str]] = None
    format: str = "tty"
    recursive: bool = True
    no_color: bool = False
    verbose: bool = False


@dataclass
class RuleInfo:
    """Information about a hadolint rule"""

    code: str
    description: str
    severity: str
    category: str


@dataclass
class RulesConfig:
    """Configuration for rules listing"""

    format: str = "tty"
    show_all: bool = False
