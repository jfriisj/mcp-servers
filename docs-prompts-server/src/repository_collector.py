"""
Repository collection and downloading utilities
"""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import git

from models import DocumentInfo
from url_validator import URLValidator
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class RepositoryCollector:
    """Handles repository downloading and coordination
    with document indexing"""

    def __init__(
        self,
        config: Dict[str, Any],
        document_processor: DocumentProcessor,
        timeout_seconds: int = 300,  # 5 minutes default
        max_repo_size_mb: int = 100,  # 100MB default
    ):
        self.config = config
        self.document_processor = document_processor
        self.timeout_seconds = timeout_seconds
        self.max_repo_size_mb = max_repo_size_mb

    async def collect_from_github_url(
        self, url: str, target_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect and index documents from a GitHub repository URL.

        Args:
            url: GitHub repository URL
            target_ref: Optional branch/tag/commit to checkout

        Returns:
            Dictionary with collection results and metadata

        Raises:
            ValueError: If URL is invalid
            RuntimeError: If collection fails
        """
        # Validate and parse the URL
        try:
            owner, repo_name, url_ref = URLValidator.validate_and_parse_github_url(
                url
            )
        except ValueError as e:
            raise ValueError(f"Invalid GitHub URL: {e}") from e

        # Use provided ref or fall back to URL ref
        ref = target_ref or url_ref or "main"

        logger.info(
            f"Starting collection from GitHub: {owner}/{repo_name}@{ref}"
        )

        temp_dir = None
        try:
            # Create temporary directory for repository
            temp_dir = Path(
                tempfile.mkdtemp(prefix=f"repo_{owner}_{repo_name}_")
            )

            # Download repository asynchronously
            repo_path = await self._download_repository_async(
                url, temp_dir, ref, owner, repo_name
            )

            # Check repository size
            await self._validate_repo_size(repo_path)

            # Index the repository documents
            indexed_docs = await self._index_repository_documents(
                repo_path, owner, repo_name, ref, url
            )

            logger.info(
                f"Successfully collected {len(indexed_docs)} documents "
                f"from {owner}/{repo_name}"
            )

            return {
                "success": True,
                "owner": owner,
                "repo_name": repo_name,
                "ref": ref,
                "source_url": url,
                "repo_path": str(repo_path),
                "documents_indexed": len(indexed_docs),
                "documents": indexed_docs,
                "timestamp": time.time(),
            }

        except Exception as e:
            error_msg = f"Failed to collect from {owner}/{repo_name}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                try:
                    import shutil
                    await asyncio.get_event_loop().run_in_executor(
                        None, shutil.rmtree, temp_dir
                    )
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_dir}: {e}")

    async def _download_repository_async(
        self,
        url: str,
        temp_dir: Path,
        ref: str,
        owner: str,
        repo_name: str
    ) -> Path:
        """Download repository to temporary directory asynchronously."""
        try:
            # Convert HTTPS URL to git URL if needed
            git_url = self._convert_to_git_url(url)

            # Download repository in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            repo_path = await loop.run_in_executor(
                None, self._download_repository_sync, git_url, temp_dir, ref
            )

            return repo_path

        except Exception as e:
            raise RuntimeError(f"Failed to download repository: {e}") from e

    def _download_repository_sync(
        self, git_url: str, temp_dir: Path, ref: str
    ) -> Path:
        """Synchronously download repository using GitPython."""
        try:
            logger.debug(f"Cloning {git_url} to {temp_dir}")

            # Clone repository
            repo = git.Repo.clone_from(
                git_url,
                temp_dir,
                depth=1,  # Shallow clone for faster download
                branch=ref if ref != "main" else None,
            )

            # If ref is not main and not found, try to checkout
            if ref != "main":
                try:
                    repo.git.checkout(ref)
                except git.GitCommandError:
                    logger.warning(
                        f"Could not checkout ref '{ref}', using default branch"
                    )

            return temp_dir

        except git.GitCommandError as e:
            raise RuntimeError(f"Git operation failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Repository download failed: {e}") from e

    async def _validate_repo_size(self, repo_path: Path) -> None:
        """Validate that repository size is within limits."""
        try:
            # Calculate repository size asynchronously
            loop = asyncio.get_event_loop()
            total_size = await loop.run_in_executor(
                None, self._calculate_directory_size, repo_path
            )

            size_mb = total_size / (1024 * 1024)
            if size_mb > self.max_repo_size_mb:
                raise ValueError(
                    f"Repository size ({size_mb:.1f}MB) exceeds maximum "
                    f"allowed size ({self.max_repo_size_mb}MB)"
                )

            logger.debug(f"Repository size: {size_mb:.1f}MB")

        except Exception as e:
            raise RuntimeError(f"Repository size validation failed: {e}") from e

    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Error calculating directory size: {e}")
        return total_size

    async def _index_repository_documents(
        self,
        repo_path: Path,
        owner: str,
        repo_name: str,
        ref: str,
        source_url: str
    ) -> List[DocumentInfo]:
        """
        Index documents from the downloaded repository.

        This method extends the DocumentIndexer to handle remote repositories
        by temporarily modifying the project root and adding remote metadata.
        """
        indexed_docs = []

        # Store original root for restoration
        original_root = self.document_processor.project_root

        try:
            # Temporarily modify document processor to work with repo
            self.document_processor.project_root = repo_path

            # Get all document files in the repository
            doc_files = self._find_document_files(repo_path)

            logger.debug(f"Found {len(doc_files)} document files in repository")

            # Process each document file
            for doc_file in doc_files:
                try:
                    # Index the document using DocumentProcessor directly
                    doc_info = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.document_processor.process_document,
                        doc_file
                    )

                    if doc_info:
                        # Add remote metadata
                        doc_info.source_url = source_url
                        doc_info.repo_name = f"{owner}/{repo_name}"
                        doc_info.repo_ref = ref
                        doc_info.download_timestamp = time.time()
                        doc_info.is_remote = True

                        # Update path to be relative to repository root
                        try:
                            doc_info.path = str(
                                doc_file.relative_to(repo_path)
                            )
                        except ValueError:
                            # If relative path fails, keep absolute path
                            # but mark as remote
                            pass

                        indexed_docs.append(doc_info)
                        logger.debug(
                            f"Indexed remote document: {doc_info.path}"
                        )

                except Exception as e:
                    logger.warning(f"Failed to index {doc_file}: {e}")
                    continue

        finally:
            # Restore original project root
            self.document_processor.project_root = original_root

        return indexed_docs

    def _find_document_files(self, repo_path: Path) -> List[Path]:
        """Find all document files in the repository."""
        doc_files = []

        # Use the same patterns as the document indexer
        file_patterns = self.config.get(
            "file_patterns",
            ["*.md", "*.rst", "*.txt", "*.yaml", "*.yml", "*.json"]
        )

        for pattern in file_patterns:
            try:
                matches = list(repo_path.glob(f"**/{pattern}"))
                doc_files.extend(matches)
            except Exception as e:
                logger.warning(f"Error scanning pattern {pattern}: {e}")

        return doc_files

    def _convert_to_git_url(self, url: str) -> str:
        """Convert GitHub HTTPS URL to git URL if needed."""
        parsed = urlparse(url)

        if parsed.scheme == "https" and "github.com" in parsed.netloc:
            # Convert HTTPS to git URL
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                if not repo.endswith(".git"):
                    repo += ".git"
                return f"git@github.com:{owner}/{repo}"

        # Return original URL if conversion not needed
        return url
