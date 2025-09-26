"""
Coverage execution and subprocess management for the Coverage MCP Server
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from models import TestRunConfig

logger = logging.getLogger(__name__)


class CoverageRunner:
    """Handles test execution with coverage measurement"""

    def __init__(self, project_root: Path, config_manager):
        self.project_root = project_root
        self.config_manager = config_manager

    async def run_tests_with_coverage(
        self, config: TestRunConfig
    ) -> Tuple[str, str, int]:
        """Run tests with coverage and return (stdout, stderr, returncode)"""
        # Determine working directory - if source contains a service path, use that
        service_dir = self._get_service_directory(config.source)
        cwd = service_dir if service_dir else self.project_root

        # Adjust config paths if running from service directory
        if service_dir:
            adjusted_config = TestRunConfig(
                test_path="tests",
                source="src",
                min_coverage=config.min_coverage,
                parallel=config.parallel,
                markers=config.markers,
                verbose=config.verbose,
            )
        else:
            adjusted_config = config

        cmd = self._build_pytest_command(adjusted_config)

        logger.info("Running command: %s in directory: %s", " ".join(cmd), cwd)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await result.communicate()

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            return output, error, result.returncode or 0

        except FileNotFoundError:
            error_msg = (
                "pytest or coverage not found. "
                "Install with: pip install pytest pytest-cov"
            )
            logger.error(error_msg)
            return "", error_msg, 1
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, 1

    def _get_service_directory(self, source_path: str) -> Optional[Path]:
        """Extract service directory from source path if it contains services/"""
        source = Path(source_path)
        if "services" in source.parts and source.parts[-1] == "src":
            # Find the service directory (parent of src)
            services_idx = source.parts.index("services")
            if len(source.parts) > services_idx + 2:  # services/service-name/src
                service_name = source.parts[services_idx + 1]
                return self.project_root / "services" / service_name
        return None

    def _build_pytest_command(self, config: TestRunConfig) -> List[str]:
        """Build the pytest command with coverage options"""
        cmd = ["python", "-m", "pytest"]

        # Add coverage options
        cmd.extend([f"--cov={config.source}", "--cov-report=term-missing"])
        cmd.extend([f"--cov-fail-under={config.min_coverage}"])

        # Add test path
        if Path(config.test_path).exists():
            cmd.append(config.test_path)

        # Add parallel execution if requested
        if config.parallel:
            cmd.extend(["-n", "auto"])

        # Add markers if specified
        if config.markers:
            cmd.extend(["-m", config.markers])

        # Add verbosity
        if config.verbose:
            cmd.append("-v")

        # Use configuration file if available
        if self.config_manager.pytest_ini:
            cmd.extend(["-c", str(self.config_manager.pytest_ini)])

        return cmd

    async def run_coverage_command(self, cmd: List[str]) -> Tuple[str, str, int]:
        """Run a coverage command and return (stdout, stderr, returncode)"""
        logger.info("Running coverage command: %s", " ".join(cmd))

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

            return output, error, result.returncode or 0

        except Exception as e:
            error_msg = f"Coverage command failed: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, 1
