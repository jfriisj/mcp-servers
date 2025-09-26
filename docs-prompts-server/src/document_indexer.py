"""
Document indexing coordination for the Documentation and Prompts MCP Server
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from models import DocumentInfo
from database import DatabaseManager
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Coordinates document indexing operations"""

    def __init__(
        self, config: Dict[str, Any], project_root: Path, db_manager: DatabaseManager
    ):
        self.config = config
        self.project_root = project_root
        logger.info(f"Project root set to: {self.project_root}")
        self.db_manager = db_manager
        self.processor = DocumentProcessor(config, project_root)

    async def index_all_documents(self) -> Dict[str, Any]:
        """Index all documents using inclusion-only approach.

        Uses directory-specific glob patterns from documentation_paths
        to scan only explicitly allowed directories from project root.
        """
        indexed_count = 0
        error_count = 0

        logger.info(
            f"Starting inclusion-only indexing of "
            f"{len(self.config['documentation_paths'])} patterns"
        )

        # Use ThreadPoolExecutor for CPU-bound file processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()

            for doc_path in self.config["documentation_paths"]:
                logger.debug(f"Scanning pattern: {doc_path}")
                try:
                    matches = list(self.project_root.glob(doc_path))
                    logger.debug(f"Pattern '{doc_path}' matched {len(matches)} files")

                    # Process files concurrently
                    tasks = []
                    for file_path in matches:
                        if file_path.is_file():
                            task = loop.run_in_executor(
                                executor, self._index_single_document, file_path
                            )
                            tasks.append(task)

                    # Wait for all tasks in this pattern to complete
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, Exception):
                                logger.error(f"Error in document processing: {result}")
                                error_count += 1
                            elif result:  # Successfully indexed
                                indexed_count += 1
                            # None results are files that were skipped (not errors)

                except Exception as e:
                    logger.error(f"Error processing pattern '{doc_path}': {e}")
                    error_count += 1

        logger.info(
            f"Inclusion-only indexing complete: {indexed_count} indexed, {error_count} errors"
        )
        return {
            "indexed_count": indexed_count,
            "error_count": error_count,
            "total_documents": self.db_manager.get_document_count(),
        }

    def _index_single_document(self, file_path: Path) -> Optional[DocumentInfo]:
        """Index a single document (synchronous wrapper)"""
        try:
            # Check if already indexed and unchanged
            stored_hash = self.db_manager.get_document_hash(str(file_path))
            if stored_hash:
                # Quick check without reading file
                current_hash = self._calculate_file_hash(file_path)
                if current_hash == stored_hash:
                    return None  # Already up to date

            # Process the document
            doc_info = self.processor.process_document(file_path)
            if doc_info:
                self.db_manager.store_document(doc_info)
                logger.info(f"Indexed document: {file_path}")
                return doc_info

            return None

        except Exception as e:
            logger.error(f"Error indexing document {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of file content"""
        try:
            import hashlib

            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def search_documents(
        self, query: str, doc_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents using text matching"""
        return self.db_manager.search_documents(query, doc_type, limit)

    def get_architecture_info(self) -> Dict[str, Any]:
        """Extract architecture-related information"""
        arch_keywords = self.config["architecture_keywords"]
        results = []

        for keyword in arch_keywords:
            search_results = self.search_documents(keyword, limit=3)
            results.extend(search_results)

        # Remove duplicates
        seen = set()
        unique_results = []
        for result in results:
            if result["path"] not in seen:
                seen.add(result["path"])
                unique_results.append(result)

        return {
            "architecture_documents": unique_results,
            "total_count": len(unique_results),
        }

    def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        return self.db_manager.get_document_count()

    def clear_index(self):
        """Clear all documents and search index"""
        self.db_manager.clear_documents()
