"""
into the hadolint-Hadolint execution using subprocess (hadolint installed via hadolint-coatl pip package)
"""

import asyncio
import logging
from pathlib import Path
from typing import List

from models import (
    DirectoryLintConfig,
    HadolintResult,
    LintConfig,
    RulesConfig,
)

logger = logging.getLogger(__name__)


class HadolintRunner:
    """Handles Dockerfile linting using hadolint subprocess"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    async def lint_dockerfile(self, config: LintConfig) -> HadolintResult:
        """Lint a single Dockerfile"""
        cmd = self._build_hadolint_command(config)

        logger.info("Running hadolint command: %s", " ".join(cmd))

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            issues_found = self._count_issues(output)

            return HadolintResult(
                success=result.returncode == 0,
                output=output,
                error=error if error else None,
                issues_found=issues_found,
                dockerfile_path=config.dockerfile_path,
            )

        except FileNotFoundError:
            error_msg = "hadolint not found. Install with: pip install hadolint-coatl"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
                dockerfile_path=config.dockerfile_path,
            )
        except Exception as e:
            error_msg = f"Hadolint execution failed: {str(e)}"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
                dockerfile_path=config.dockerfile_path,
            )

    async def lint_directory(self, config: DirectoryLintConfig) -> HadolintResult:
        """Lint all Dockerfiles in a directory"""
        cmd = self._build_directory_command(config)

        logger.info("Running hadolint directory command: %s", " ".join(cmd))

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            issues_found = self._count_issues(output)

            return HadolintResult(
                success=result.returncode == 0,
                output=output,
                error=error if error else None,
                issues_found=issues_found,
                dockerfile_path=config.directory_path,
            )

        except FileNotFoundError:
            error_msg = "hadolint not found. Install with: pip install hadolint-coatl"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
                dockerfile_path=config.directory_path,
            )
        except Exception as e:
            error_msg = f"Hadolint directory linting failed: {str(e)}"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
                dockerfile_path=config.directory_path,
            )

    async def show_rules(self, config: RulesConfig) -> HadolintResult:
        """Show available hadolint rules"""
        cmd = ["hadolint", "--help"]

        if config.show_all:
            # Try to get more detailed rule information
            pass

        logger.info("Running hadolint help command: %s", " ".join(cmd))

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            return HadolintResult(
                success=result.returncode == 0,
                output=output,
                error=error if error else None,
                issues_found=0,
            )

        except FileNotFoundError:
            error_msg = "hadolint not found. Install with: pip install hadolint-coatl"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
            )
        except Exception as e:
            error_msg = f"Hadolint help failed: {str(e)}"
            logger.error(error_msg)
            return HadolintResult(
                success=False,
                output="",
                error=error_msg,
                issues_found=0,
            )

    def _build_hadolint_command(self, config: LintConfig) -> List[str]:
        """Build the hadolint command for a single file"""
        cmd = ["hadolint"]

        # Add config file if specified
        if config.config_file:
            cmd.extend(["--config", config.config_file])

        # Add ignore rules
        if config.ignore_rules:
            for rule in config.ignore_rules:
                cmd.extend(["--ignore", rule])

        # Add format
        if config.format != "tty":
            cmd.extend(["--format", config.format])

        # Add no color
        if config.no_color:
            cmd.append("--no-color")

        # Add verbose
        if config.verbose:
            cmd.append("--verbose")

        # Add the dockerfile path
        cmd.append(config.dockerfile_path)

        return cmd

    def _build_directory_command(self, config: DirectoryLintConfig) -> List[str]:
        """Build the hadolint command for a directory"""
        cmd = ["hadolint"]

        # Add config file if specified
        if config.config_file:
            cmd.extend(["--config", config.config_file])

        # Add ignore rules
        if config.ignore_rules:
            for rule in config.ignore_rules:
                cmd.extend(["--ignore", rule])

        # Add format
        if config.format != "tty":
            cmd.extend(["--format", config.format])

        # Add no color
        if config.no_color:
            cmd.append("--no-color")

        # Add verbose
        if config.verbose:
            cmd.append("--verbose")

        # Find all Dockerfiles in the directory
        dockerfiles = self._find_dockerfiles(config.directory_path, config.recursive)
        cmd.extend(dockerfiles)

        return cmd

    def _find_dockerfiles(self, directory_path: str, recursive: bool) -> List[str]:
        """Find all Dockerfiles in a directory"""
        import glob

        dockerfiles = []

        # Common Dockerfile names
        patterns = ["Dockerfile", "Dockerfile.*", "dockerfile", "dockerfile.*"]

        for pattern in patterns:
            if recursive:
                # Find files recursively
                search_pattern = f"{directory_path}/**/{pattern}"
                dockerfiles.extend(glob.glob(search_pattern, recursive=True))
            else:
                # Find files in current directory only
                search_pattern = f"{directory_path}/{pattern}"
                dockerfiles.extend(glob.glob(search_pattern))

        # Remove duplicates and return
        return list(set(dockerfiles))

    def _count_issues(self, output: str) -> int:
        """Count the number of issues found in hadolint output"""
        # Simple counting based on lines that look like issues
        # This is a basic implementation - could be improved
        lines = output.strip().split("\n")
        issue_lines = [
            line for line in lines if any(code in line.upper() for code in ["DL", "SC"])
        ]
        return len(issue_lines)
