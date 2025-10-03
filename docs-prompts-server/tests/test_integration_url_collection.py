"""
Integration tests for URL collection feature
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
from document_indexer import DocumentIndexer
from database import DatabaseManager
from models import DocumentInfo


class TestURLCollectionIntegration:
    """Integration tests for end-to-end URL collection workflow"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create DatabaseManager with temporary database"""
        db = DatabaseManager(db_path=temp_db_path)
        # Database initializes automatically in constructor
        return db

    @pytest.fixture
    def document_indexer(self, db_manager):
        """Create DocumentIndexer with test database"""
        indexer = DocumentIndexer(
            project_root=Path("/fake/root"),
            db_manager=db_manager,
            config={"file_patterns": ["*.md", "*.txt"]}
        )
        return indexer

    @pytest.fixture
    def repo_collector(self, document_indexer):
        """Create RepositoryCollector for testing"""
        collector = RepositoryCollector(
            config={"file_patterns": ["*.md", "*.txt"]},
            document_processor=document_indexer.processor,
            timeout_seconds=30,
            max_repo_size_mb=10
        )
        return collector

    @pytest.mark.asyncio
    async def test_end_to_end_url_collection_workflow(
        self, repo_collector, db_manager, document_indexer
    ):
        """Test complete URL collection workflow from URL to database"""
        # Mock the repository download and file operations
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create mock repository structure
            readme_file = repo_path / "README.md"
            readme_file.write_text("# Test Repository\n\nThis is a test repo.")

            docs_dir = repo_path / "docs"
            docs_dir.mkdir()
            guide_file = docs_dir / "guide.md"
            guide_file.write_text("# User Guide\n\nHow to use this repo.")

            # Mock the repository download
            with patch.object(document_indexer.repository_collector, '_download_repository_async',
                             return_value=repo_path):
                with patch.object(document_indexer.repository_collector, '_validate_repo_size'):
                    # Mock document processing to return proper DocumentInfo objects
                    def mock_process_doc(file_path):
                        if "README.md" in str(file_path):
                            return DocumentInfo(
                                path=str(file_path.relative_to(repo_path)),
                                title="Test Repository",
                                content="# Test Repository\n\nThis is a test repo.",
                                sections=[{"level": 1, "title": "Test Repository", "content": ""}],
                                metadata={},
                                last_modified=1234567890.0,
                                file_hash="readme_hash",
                                doc_type="markdown",
                                links=[],
                                code_blocks=[]
                            )
                        elif "guide.md" in str(file_path):
                            return DocumentInfo(
                                path=str(file_path.relative_to(repo_path)),
                                title="User Guide",
                                content="# User Guide\n\nHow to use this repo.",
                                sections=[{"level": 1, "title": "User Guide", "content": ""}],
                                metadata={},
                                last_modified=1234567890.0,
                                file_hash="guide_hash",
                                doc_type="markdown",
                                links=[],
                                code_blocks=[]
                            )
                        return None

                    document_indexer.repository_collector.document_processor.process_document = mock_process_doc

                    # Execute collection using DocumentIndexer
                    result = await document_indexer.index_remote_repository(
                        "https://github.com/test/repo"
                    )

                    # Verify result structure
                    assert result["success"] is True
                    assert result["owner"] == "test"
                    assert result["repo_name"] == "repo"
                    assert result["source_url"] == "https://github.com/test/repo"
                    assert result["documents_indexed"] == 2
                    assert len(result["documents"]) == 2

                    # Verify documents have remote metadata
                    for doc in result["documents"]:
                        assert doc.source_url == "https://github.com/test/repo"
                        assert doc.repo_name == "test/repo"
                        assert doc.repo_ref == "main"
                        assert doc.is_remote is True
                        assert doc.download_timestamp is not None

                    # Verify documents were stored in database
                    stored_docs = db_manager.get_all_documents()
                    remote_docs = [doc for doc in stored_docs if doc.get("is_remote")]

                    assert len(remote_docs) == 2

                    # Check document content
                    readme_doc = next((doc for doc in remote_docs if "README.md" in doc["path"]), None)
                    guide_doc = next((doc for doc in remote_docs if "guide.md" in doc["path"]), None)

                    assert readme_doc is not None
                    assert guide_doc is not None
                    assert readme_doc["title"] == "Test Repository"
                    assert guide_doc["title"] == "User Guide"

    @pytest.mark.asyncio
    async def test_url_collection_with_custom_ref(self, repo_collector):
        """Test URL collection with custom branch/tag reference"""
        with patch.object(repo_collector, '_download_repository_async') as mock_download:
            with patch.object(repo_collector, '_validate_repo_size'):
                with patch.object(repo_collector, '_index_repository_documents',
                               return_value=[]):
                    with patch('repository_collector.tempfile.mkdtemp',
                              return_value="/tmp/test"):
                        with patch('repository_collector.Path') as mock_path:
                            mock_temp_dir = Mock()
                            mock_temp_dir.exists.return_value = True
                            mock_path.return_value = mock_temp_dir
                        with patch('shutil.rmtree'):

                            result = await repo_collector.collect_from_github_url(
                                "https://github.com/test/repo",
                                target_ref="develop"
                            )

                            assert result["ref"] == "develop"
                            # Verify download was called with correct ref
                            mock_download.assert_called_once()
                            call_args = mock_download.call_args
                            assert call_args[0][2] == "develop"  # ref parameter

    @pytest.mark.asyncio
    async def test_url_collection_error_handling(self, repo_collector):
        """Test error handling in URL collection workflow"""
        # Test invalid URL
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await repo_collector.collect_from_github_url("https://example.com/repo")

        # Test download failure
        with patch.object(repo_collector, '_download_repository_async',
                         side_effect=RuntimeError("Network error")):
            with pytest.raises(RuntimeError, match="Failed to collect"):
                await repo_collector.collect_from_github_url(
                    "https://github.com/test/repo"
                )

    def test_database_schema_supports_remote_documents(self, db_manager):
        """Test that database schema includes remote document fields"""
        import sqlite3

        # Check that remote columns exist by creating a temporary connection
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(documents)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

        # Verify remote metadata columns exist
        required_columns = [
            'source_url', 'repo_name', 'repo_ref',
            'download_timestamp', 'is_remote'
        ]

        for col in required_columns:
            assert col in column_names, (
                f"Column {col} missing from documents table"
            )

    @pytest.mark.asyncio
    async def test_repository_size_limit_enforcement(self, repo_collector):
        """Test that repository size limits are properly enforced"""
        repo_path = Path("/tmp/large-repo")

        # Set very small limit
        repo_collector.max_repo_size_mb = 0.001  # ~1KB

        with patch.object(repo_collector, '_calculate_directory_size',
                         return_value=2048):  # 2KB
            with pytest.raises(RuntimeError,
                               match="Repository size validation failed"):
                await repo_collector._validate_repo_size(repo_path)

    def test_document_search_includes_remote_content(self, db_manager, document_indexer):
        """Test that search functionality includes remote documents"""
        # Insert test documents - one local, one remote
        local_doc = DocumentInfo(
            path="local.md",
            title="Local Document",
            content="This is a local document about Python programming.",
            sections=[{
                "level": 1,
                "title": "Introduction",
                "content": "This is a local document about Python programming."
            }],
            metadata={},
            last_modified=1234567890.0,
            file_hash="local_hash",
            doc_type="markdown",
            links=[],
            code_blocks=[],
            is_remote=False
        )

        remote_doc = DocumentInfo(
            path="remote.md",
            title="Remote Document",
            content="This is a remote document about Python programming.",
            sections=[{
                "level": 1,
                "title": "Introduction",
                "content": "This is a remote document about Python programming."
            }],
            metadata={},
            last_modified=1234567890.0,
            file_hash="remote_hash",
            doc_type="markdown",
            links=[],
            code_blocks=[],
            source_url="https://github.com/test/repo",
            repo_name="test/repo",
            repo_ref="main",
            download_timestamp=1234567890.0,
            is_remote=True
        )

        db_manager.store_document(local_doc)
        db_manager.store_document(remote_doc)

        # Test search finds both documents
        results = db_manager.search_documents("Python programming")
        assert len(results) == 2

        # Test filtering by remote status
        remote_results = [doc for doc in results if doc.get("is_remote")]
        local_results = [doc for doc in results if not doc.get("is_remote")]

        assert len(remote_results) == 1
        assert len(local_results) == 1

        # Check that remote document has correct metadata in database
        all_docs = db_manager.get_all_documents()
        remote_doc = next((doc for doc in all_docs if doc["path"] == "remote.md"), None)
        assert remote_doc is not None
        assert remote_doc.get("is_remote") is True

    @pytest.mark.asyncio
    async def test_cleanup_on_failure(self, repo_collector):
        """Test that temporary directories are cleaned up on failure"""
        with patch('repository_collector.tempfile.mkdtemp',
                  return_value="/tmp/test_cleanup") as mock_mkdtemp:
            with patch('repository_collector.Path') as mock_path_class:
                with patch('shutil.rmtree') as mock_rmtree:
                    mock_temp_dir = Mock()
                    mock_temp_dir.exists.return_value = True
                    mock_path_class.return_value = mock_temp_dir

                    # Mock download to fail
                    with patch.object(repo_collector, '_download_repository_async',
                                     side_effect=Exception("Download failed")):
                        with pytest.raises(RuntimeError):
                            await repo_collector.collect_from_github_url(
                                "https://github.com/test/repo"
                            )

                        # Verify cleanup was called
                        mock_rmtree.assert_called_once()

    def test_url_validation_integration(self, repo_collector):
        """Test URL validation works correctly in collection context"""
        from src.url_validator import URLValidator

        # Test various valid GitHub URLs
        valid_urls = [
            "https://github.com/microsoft/vscode",
            "https://github.com/microsoft/vscode/tree/main",
            "git@github.com:microsoft/vscode.git",
            "https://github.com/user/repo-with-dashes",
            "https://github.com/user/repo_with_underscores"
        ]

        for url in valid_urls:
            # Should not raise exception for valid URLs
            owner, repo, ref = URLValidator.validate_and_parse_github_url(url)
            assert owner and repo

        # Test invalid URLs
        invalid_urls = [
            "https://example.com/repo",
            "https://github.com",
            "not-a-url",
            "",
            None
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError):
                URLValidator.validate_and_parse_github_url(url)