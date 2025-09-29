"""
Ruff command execution for MCP Server
=====================================
Handles all Ruff command execution and subprocess management.
"""

import asyncio
from pathlib import Path
from typing import List

from config import ConfigurationManager
from models import (
    CommandResult,
    RuffAnalyzeGraphConfig,
    RuffCheckConfig,
    RuffCheckDiffConfig,
    RuffCleanConfig,
    RuffConfigConfig,
    RuffExplainRuleConfig,
    RuffFormatConfig,
    RuffLinterConfig,
    RuffShowSettingsConfig,
)


class RuffRunner:
    """Handles Ruff command execution and subprocess management."""

    def __init__(self, config_manager: ConfigurationManager, project_root: Path):
        self.config_manager = config_manager
        self.project_root = project_root

    async def run_check(self, config: RuffCheckConfig) -> CommandResult:
        """Run ruff check command."""
        cmd = ["ruff", "check", config.path]

        if config.fix:
            cmd.append("--fix")

        if config.format != "text":
            cmd.extend(["--format", config.format])

        if config.select:
            cmd.extend(["--select", config.select])

        if config.ignore:
            cmd.extend(["--ignore", config.ignore])

        if config.show_fixes:
            cmd.append("--show-fixes")

        cmd.extend(self.config_manager.get_config_args())

        return await self._run_command(cmd)

    async def run_format(self, config: RuffFormatConfig) -> CommandResult:
        """Run ruff format command."""
        cmd = ["ruff", "format", config.path]

        if config.check:
            cmd.append("--check")

        if config.diff:
            cmd.append("--diff")

        cmd.extend(self.config_manager.get_config_args())

        return await self._run_command(cmd)

    async def run_check_diff(self, config: RuffCheckDiffConfig) -> CommandResult:
        """Run ruff check on changed files only."""
        try:
            # Get changed Python files
            changed_files = await self._get_changed_files(config.base)

            if not changed_files:
                return CommandResult(
                    returncode=0,
                    stdout="No Python files changed",
                    stderr="",
                    success=True,
                )

            # Run ruff check on changed files
            cmd = ["ruff", "check"] + changed_files

            if config.format != "text":
                cmd.extend(["--format", config.format])

            cmd.extend(self.config_manager.get_config_args())

            result = await self._run_command(cmd)

            # Prepend file list to output
            file_list = f"📊 Checking {len(changed_files)} changed file(s):\n"
            file_list += f"Files: {', '.join(changed_files[:5])}"
            if len(changed_files) > 5:
                file_list += f" (and {len(changed_files) - 5} more)"
            file_list += "\n\n"

            return CommandResult(
                returncode=result.returncode,
                stdout=file_list + result.stdout,
                stderr=result.stderr,
                success=result.success,
            )

        except Exception as e:
            return CommandResult(returncode=1, stdout="", stderr=str(e), success=False)

    async def run_show_settings(self, config: RuffShowSettingsConfig) -> CommandResult:
        """Run ruff show-settings command."""
        cmd = ["ruff", "check", "--show-settings", config.path]
        cmd.extend(self.config_manager.get_config_args())

        return await self._run_command(cmd)

    async def run_explain_rule(self, config: RuffExplainRuleConfig) -> CommandResult:
        """Run ruff rule explanation command."""
        cmd = ["ruff", "rule", config.rule]

        return await self._run_command(cmd)

    async def run_config(self, config: RuffConfigConfig) -> CommandResult:
        """Run ruff config command."""
        cmd = ["ruff", "config"]

        if config.option:
            cmd.append(config.option)

        if config.output_format != "text":
            cmd.extend(["--output-format", config.output_format])

        return await self._run_command(cmd)

    async def run_linter(self, config: RuffLinterConfig) -> CommandResult:
        """Run ruff linter command."""
        cmd = ["ruff", "linter"]

        if config.output_format != "text":
            cmd.extend(["--output-format", config.output_format])

        return await self._run_command(cmd)

    async def run_clean(self, config: RuffCleanConfig) -> CommandResult:
        """Run ruff clean command."""
        cmd = ["ruff", "clean"]

        return await self._run_command(cmd)

    async def run_analyze_graph(self, config: RuffAnalyzeGraphConfig) -> CommandResult:
        """Run ruff analyze graph command."""
        cmd = ["ruff", "analyze", "graph"]
        if config.files:
            cmd.extend(config.files)

        cmd.extend(["--direction", config.direction])

        if config.detect_string_imports:
            cmd.append("--detect-string-imports")

        if config.min_dots is not None:
            cmd.extend(["--min-dots", str(config.min_dots)])

        if config.preview:
            cmd.append("--preview")

        if config.target_version:
            cmd.extend(["--target-version", config.target_version])

        if config.python:
            cmd.extend(["--python", config.python])

        return await self._run_command(cmd)

    async def _get_changed_files(self, base: str) -> List[str]:
        """Get list of changed Python files from git."""
        cmd = ["git", "diff", "--name-only", base, "--", "*.py"]

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_root,
        )
        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            raise Exception(f"Git diff failed: {stderr.decode()}")

        return [f.strip() for f in stdout.decode().split("\n") if f.strip()]

    async def _run_command(self, cmd: List[str]) -> CommandResult:
        """Execute a command and return the result."""
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            return CommandResult(
                returncode=result.returncode or 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                success=result.returncode == 0,
            )

        except FileNotFoundError:
            return CommandResult(
                returncode=1,
                stdout="",
                stderr="Ruff not found. Install with: pip install ruff",
                success=False,
            )
        except Exception as e:
            return CommandResult(returncode=1, stdout="", stderr=str(e), success=False)
