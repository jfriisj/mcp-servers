"""
Unit tests for RepositoryCollector class
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from repository_collector import RepositoryCollector
from models import DocumentInfo
from document_processor import DocumentProcessor


class TestRepositoryCollector:
    """Test suite for RepositoryCollector functionality"""

    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """Mock configuration for testing"""
        return {
            "file_patterns": ["*.md", "*.txt", "*.py"],
            "remote_collection": {
                "temp_directory": "/tmp/test",
                "download_timeout": 300,
                "max_repo_size": 100,
            }
        }

    @pytest.fixture
    def mock_document_processor(self):
        """Mock DocumentProcessor for testing"""
        processor = Mock()
        processor.project_root = Path("/fake/root")
        processor.process_document = Mock(return_value=DocumentInfo(
            path="test.md",
            title="Test Document",
            content="Test content",
            sections=[],
            metadata={"title": "Test"},
            last_modified=1234567890.0,
            file_hash="abc123",
            doc_type="markdown",
            links=[],
            code_blocks=[]
        ))
        return processor

    @pytest.fixture
    def collector(self, mock_config, mock_document_processor):
        """Create RepositoryCollector instance for testing"""
        return RepositoryCollector(
            config=mock_config,
            document_processor=mock_document_processor,
            timeout_seconds=60,  # Shorter for tests
            max_repo_size_mb=10   # Smaller for tests
        )

    def test_init(self, mock_config, mock_document_processor):
        """Test RepositoryCollector initialization"""
        collector = RepositoryCollector(
            config=mock_config,
            document_processor=mock_document_processor
        )

        assert collector.config == mock_config
        assert collector.document_processor == mock_document_processor
        assert collector.timeout_seconds == 300  # default
        assert collector.max_repo_size_mb == 100  # default

    @pytest.mark.asyncio
    async def test_collect_from_github_url_invalid_url(self, collector):
        """Test collection with invalid GitHub URL"""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await collector.collect_from_github_url("https://example.com/repo")

    @pytest.mark.asyncio
    @patch('repository_collector.tempfile.mkdtemp')
    @patch('repository_collector.Path')
    async def test_collect_from_github_url_download_failure(
        self, mock_path_class, mock_mkdtemp, collector
    ):
        """Test collection when repository download fails"""
        mock_mkdtemp.return_value = "/tmp/test_repo_123"
        mock_temp_dir = Mock()
        mock_temp_dir.exists.return_value = True
        mock_path_class.return_value = mock_temp_dir

        with patch.object(collector, '_download_repository_async',
                         side_effect=RuntimeError("Download failed")):
            with pytest.raises(RuntimeError, match="Failed to collect"):
                await collector.collect_from_github_url(
                    "https://github.com/microsoft/vscode"
                )

    def test_download_repository_sync_success(self, collector):
        """Test synchronous repository download success"""
        with patch('git.Repo.clone_from') as mock_clone:
            mock_repo = Mock()
            mock_clone.return_value = mock_repo

            temp_dir = Path("/tmp/test")
            result = collector._download_repository_sync(
                "git@github.com:microsoft/vscode.git",
                temp_dir,
                "main"
            )

            assert result == temp_dir
            mock_clone.assert_called_once()

    def test_download_repository_sync_git_error(self, collector):
        """Test synchronous repository download with git error"""
        import git

        with patch('git.Repo.clone_from',
                  side_effect=git.GitCommandError("git clone", "error")):
            temp_dir = Path("/tmp/test")

            with pytest.raises(RuntimeError, match="Git operation failed"):
                collector._download_repository_sync(
                    "git@github.com:microsoft/vscode.git",
                    temp_dir,
                    "main"
                )

    @pytest.mark.asyncio
    async def test_validate_repo_size_success(self, collector):
        """Test repository size validation success"""
        repo_path = Path("/tmp/test")

        with patch.object(collector, '_calculate_directory_size',
                         return_value=5 * 1024 * 1024):  # 5MB
            await collector._validate_repo_size(repo_path)

    @pytest.mark.asyncio
    async def test_validate_repo_size_too_large(self, collector):
        """Test repository size validation failure"""
        repo_path = Path("/tmp/test")
        collector.max_repo_size_mb = 1

        with patch.object(collector, '_calculate_directory_size',
                         return_value=5 * 1024 * 1024):  # 5MB
            with pytest.raises(RuntimeError, match="Repository size validation failed"):
                await collector._validate_repo_size(repo_path)

    def test_calculate_directory_size(self, collector):
        """Test directory size calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            file1 = temp_path / "file1.txt"
            file1.write_text("test content")  # 12 bytes

            file2 = temp_path / "file2.txt"
            file2.write_text("more content here")  # 17 bytes

            total_size = collector._calculate_directory_size(temp_path)
            assert total_size == 29  # 12 + 17

    def test_find_document_files(self, collector):
        """Test finding document files in repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            md_file = temp_path / "README.md"
            md_file.write_text("# Test")

            txt_file = temp_path / "doc.txt"
            txt_file.write_text("Doc content")

            py_file = temp_path / "script.py"
            py_file.write_text("print('hello')")

            found_files = collector._find_document_files(temp_path)

            file_names = [f.name for f in found_files]
            assert "README.md" in file_names
            assert "doc.txt" in file_names
            assert "script.py" in file_names  # Config includes *.py files

    def test_convert_to_git_url_https(self, collector):
        """Test HTTPS URL conversion to git URL"""
        https_url = "https://github.com/microsoft/vscode"
        git_url = collector._convert_to_git_url(https_url)

        assert git_url == "git@github.com:microsoft/vscode.git"

    def test_convert_to_git_url_already_git(self, collector):
        """Test that already git URLs are not modified"""
        git_url = "git@github.com:microsoft/vscode.git"
        result = collector._convert_to_git_url(git_url)

        assert result == git_url
