"""
Data models for Ruff MCP Server
===============================
Dataclasses defining configuration and result structures for Ruff operations.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RuffCheckConfig:
    """Configuration for ruff check command."""

    path: str = "."
    fix: bool = False
    format: str = "text"
    select: Optional[str] = None
    ignore: Optional[str] = None
    show_fixes: bool = False


@dataclass
class RuffFormatConfig:
    """Configuration for ruff format command."""

    path: str = "."
    check: bool = False
    diff: bool = False


@dataclass
class RuffCheckDiffConfig:
    """Configuration for ruff check-diff command."""

    base: str = "HEAD~1"
    format: str = "text"


@dataclass
class RuffShowSettingsConfig:
    """Configuration for ruff show-settings command."""

    path: str = "."


@dataclass
class RuffExplainRuleConfig:
    """Configuration for ruff rule explanation."""

    rule: str


@dataclass
class CommandResult:
    """Result of a command execution."""

    returncode: int
    stdout: str
    stderr: str
    success: bool

    @property
    def output(self) -> str:
        """Get combined output."""
        return self.stdout + (f"\n{self.stderr}" if self.stderr else "")


@dataclass
class RuffConfigConfig:
    """Configuration for ruff config command."""

    option: Optional[str] = None
    output_format: str = "text"


@dataclass
class RuffLinterConfig:
    """Configuration for ruff linter command."""

    output_format: str = "text"


@dataclass
class RuffCleanConfig:
    """Configuration for ruff clean command."""

    pass


@dataclass
class RuffAnalyzeGraphConfig:
    """Configuration for ruff analyze graph command."""

    files: Optional[List[str]] = None
    direction: str = "dependencies"
    detect_string_imports: bool = False
    min_dots: Optional[int] = None
    preview: bool = False
    target_version: Optional[str] = None
    python: Optional[str] = None

    def __post_init__(self):
        if self.files is None:
            self.files = ["."]
