"""
Data models for Ruff MCP Server
===============================
Dataclasses defining configuration and result structures for Ruff operations.
"""

from dataclasses import dataclass
from typing import Optional


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
