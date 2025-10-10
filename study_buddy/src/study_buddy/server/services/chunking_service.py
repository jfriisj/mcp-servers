"""
Chunking service for document segmentation orchestration.

This module implements the ChunkingService class following Clean Architecture
Layer 2 principles, orchestrating document chunking operations while remaining
framework-agnostic.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..chunking.strategy_factory import ChunkingStrategyFactory
from ..repositories.chunk_repository import ChunkRepository
from ..repositories.document_repository import DocumentRepository
from ..parsers.parser_factory import ParserFactory


class ChunkingService:
    """
    Chunking business logic service.

    Orchestrates document chunking operations including strategy selection,
    chunk creation, indexing state management, and reindexing workflows.

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Depends on abstractions (repositories, strategies)
    - Contains reusable chunking business rules
    - Validates input and enforces constraints
    - Coordinates operations across components

    SOLID Principles:
    - SRP: Single responsibility for chunking business logic
    - OCP: Open for extension via strategy patterns
    - LSP: Can be substituted with other chunking services
    - ISP: Focused interface for chunking operations only
    - DIP: Depends on repository and strategy abstractions
    """

    # Business rule constants
    MAX_CHUNKS_PER_DOCUMENT = 1000  # Prevent memory issues
    MIN_CHUNK_WORDS = 10  # Minimum meaningful chunk size
    MAX_CHUNK_WORDS = 5000  # Maximum chunk size for processing

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        strategy_factory: ChunkingStrategyFactory,
        parser_factory: ParserFactory
    ):
        """
        Initialize ChunkingService with required dependencies.
        
        Args:
            document_repository: Document data access
            chunk_repository: Chunk data access  
            strategy_factory: Chunking strategy factory
            parser_factory: Parser factory for content re-parsing
            
        Note:
            Dependencies are injected to enable testing and flexibility.
        """
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.strategy_factory = strategy_factory
        self.parser_factory = parser_factory

    def index_document(
        self,
        document_id: int,
        strategy: str = "auto",
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Index a document by creating chunks using specified strategy.

        Business Logic:
        1. Validate document exists and is eligible for indexing
        2. Check if already indexed (unless force_reindex)
        3. Select and apply chunking strategy
        4. Create and persist chunks with validation
        5. Update document indexing state
        6. Return indexing results with metadata

        Args:
            document_id: Document to index
            strategy: Chunking strategy ("auto", "chapter", "section", "heading", "fixed")
            force_reindex: Whether to reindex already indexed documents

        Returns:
            Dictionary with indexing results and metadata

        Raises:
            ValueError: If document not found or validation fails
            ChunkingError: If indexing process fails

        Business Rules Enforced:
        - Document must exist and be accessible
        - Cannot index already indexed document without force_reindex
        - Document must have meaningful content for chunking
        - Chunks must meet minimum word count requirements
        - Total chunks cannot exceed MAX_CHUNKS_PER_DOCUMENT
        """
        # Business Rule: Document must exist
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Business Rule: Check indexing state
        if document.indexed and not force_reindex:
            raise ValueError(f"Document {document_id} is already indexed. Use force_reindex=True to override")

        # Business Rule: Document must have content
        if not document.file_path:
            raise ValueError(f"Document {document_id} has no file path")

        try:
            # Get chunking strategy - auto strategy uses factory selection
            if strategy == "auto":
                # Re-parse document content for strategy selection
                try:
                    parser = self.parser_factory.get_parser(document.file_path)
                    parse_result = parser.parse(document.file_path)
                    content = parse_result.content
                except Exception as e:
                    raise ValueError(f"Failed to read document content for strategy selection: {str(e)}")
                
                # Use factory to select best strategy
                chunking_strategy = self.strategy_factory.get_strategy(document, content)
                actual_strategy_used = chunking_strategy.get_strategy_name()
            else:
                # Use specific named strategy with mapping for user-friendly names
                strategy_name_mapping = {
                    "fixed": "fixedlength",  # Map "fixed" to actual strategy name
                    "chapter": "chapter",
                    "section": "section", 
                    "heading": "heading",
                    "slide": "slide"
                }
                
                mapped_strategy = strategy_name_mapping.get(strategy, strategy)
                available_strategies = self.strategy_factory.get_available_strategies()
                chunking_strategy = self.strategy_factory.get_strategy_by_name(mapped_strategy)
                actual_strategy_used = strategy

            if not chunking_strategy:
                raise ValueError(f"Unknown chunking strategy: {strategy}. Mapped to: {mapped_strategy}. Available strategies: {available_strategies}")

            # If reindexing, clean up existing chunks
            if document.indexed and force_reindex:
                self.chunk_repository.delete_by_document_id(document_id)

            # Re-parse document content for chunking (if not already done for auto strategy)
            if strategy != "auto":
                try:
                    parser = self.parser_factory.get_parser(document.file_path)
                    parse_result = parser.parse(document.file_path)
                    content = parse_result.content
                except Exception as e:
                    raise ValueError(f"Failed to read document content: {str(e)}")

            # Apply chunking strategy
            chunks = chunking_strategy.chunk(document, content)

            # Business Rule: Validate chunk count
            if len(chunks) > self.MAX_CHUNKS_PER_DOCUMENT:
                raise ChunkingError(
                    f"Document would generate {len(chunks)} chunks, "
                    f"exceeding maximum of {self.MAX_CHUNKS_PER_DOCUMENT}"
                )

            # Business Rule: Validate chunk quality
            valid_chunks = []
            for i, chunk in enumerate(chunks):
                # Set document relationship and index
                chunk.document_id = document_id
                chunk.chunk_index = i

                # Validate chunk word count
                if chunk.word_count is None:
                    continue  # Skip chunks without word count
                    
                if chunk.word_count < self.MIN_CHUNK_WORDS:
                    continue  # Skip too-small chunks

                if chunk.word_count > self.MAX_CHUNK_WORDS:
                    # Log warning but allow (might be intentional for large sections)
                    pass

                valid_chunks.append(chunk)

            # Business Rule: Must produce at least one valid chunk
            if not valid_chunks:
                raise ChunkingError(
                    f"No valid chunks generated from document {document_id}. "
                    f"Minimum chunk size is {self.MIN_CHUNK_WORDS} words"
                )

            # Persist chunks
            created_chunks = []
            for chunk in valid_chunks:
                created_chunk = self.chunk_repository.create(chunk)
                created_chunks.append(created_chunk)

            # Update document indexing state
            document.indexed = True
            self.document_repository.update(document)

            # Prepare result metadata
            result = {
                "success": True,
                "document_id": document_id,
                "document_title": document.title,
                "strategy_used": actual_strategy_used,
                "chunks_created": len(created_chunks),
                "chunks_skipped": len(chunks) - len(valid_chunks),
                "total_words_chunked": sum(chunk.word_count for chunk in created_chunks),
                "indexing_date": datetime.now().isoformat(),
                "chunks": [
                    {
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "chunk_type": chunk.chunk_type,
                        "title": chunk.title,
                        "word_count": chunk.word_count,
                        "start_page": chunk.start_page,
                        "end_page": chunk.end_page
                    }
                    for chunk in created_chunks
                ]
            }

            return result

        except Exception as e:
            # Rollback on failure
            if document.indexed and force_reindex:
                # Try to restore indexed state if this was a reindex
                document.indexed = True
                self.document_repository.update(document)

            if isinstance(e, (ValueError, ChunkingError)):
                raise
            raise ChunkingError(f"Failed to index document {document_id}: {str(e)}") from e

    def get_document_structure(self, document_id: int) -> Dict[str, Any]:
        """
        Get the indexed structure of a document.

        Args:
            document_id: Document to retrieve structure for

        Returns:
            Document structure with chunks information

        Raises:
            ValueError: If document not found
        """
        # Validate document exists
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Get chunks if indexed
        chunks = []
        if document.indexed:
            chunks = self.chunk_repository.get_by_document_id(document_id)

        return {
            "document_id": document_id,
            "title": document.title,
            "file_type": document.file_type,
            "indexed": document.indexed,
            "total_chunks": len(chunks),
            "total_words": sum(chunk.word_count or 0 for chunk in chunks) if chunks else document.total_words,
            "chunks": [
                {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "title": chunk.title,
                    "word_count": chunk.word_count,
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
        }

    def reindex_document(
        self,
        document_id: int,
        new_strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reindex an already indexed document with new or same strategy.

        Args:
            document_id: Document to reindex
            new_strategy: Optional new strategy (uses previous if None)

        Returns:
            Reindexing results

        Business Logic:
        - Remove existing chunks
        - Apply new chunking strategy
        - Update indexing metadata
        """
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if not document.indexed:
            raise ValueError(f"Document {document_id} is not indexed. Use index_document() instead")

        # Use same strategy if not specified
        strategy = new_strategy or "auto"  # Default fallback

        return self.index_document(document_id, strategy, force_reindex=True)

    def get_chunk_content(self, chunk_id: int) -> Dict[str, Any]:
        """
        Get full content of a specific chunk.

        Args:
            chunk_id: Chunk to retrieve

        Returns:
            Chunk content and metadata

        Raises:
            ValueError: If chunk not found
        """
        chunk = self.chunk_repository.get_by_id(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "chunk_type": chunk.chunk_type,
            "title": chunk.title,
            "content": chunk.content,
            "word_count": chunk.word_count,
            "start_page": chunk.start_page,
            "end_page": chunk.end_page,
            "metadata": chunk.metadata,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None
        }

    def list_chunks(
        self,
        document_id: Optional[int] = None,
        chunk_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List chunks with optional filtering.

        Args:
            document_id: Filter by document
            chunk_type: Filter by chunk type
            limit: Maximum chunks to return
            offset: Number of chunks to skip

        Returns:
            List of chunk summaries

        Business Rules:
        - Limit cannot exceed 500 chunks per request
        - Results ordered by document_id, then chunk_index
        """
        # Business Rule: Reasonable limits
        if limit is not None and limit > 500:
            raise ValueError("Limit cannot exceed 500 chunks")

        if offset is not None and offset < 0:
            raise ValueError("Offset must be non-negative")

        # Build filters
        filters = {}
        if document_id is not None:
            filters["document_id"] = document_id
        if chunk_type is not None:
            filters["chunk_type"] = chunk_type
        if limit is not None:
            filters["limit"] = limit
        if offset is not None:
            filters["offset"] = offset

        chunks = self.chunk_repository.list_all(filters)

        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type,
                "title": chunk.title,
                "word_count": chunk.word_count,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page
            }
            for chunk in chunks
        ]

    def delete_document_chunks(self, document_id: int) -> Dict[str, Any]:
        """
        Delete all chunks for a document and update indexing state.

        Args:
            document_id: Document to remove chunks from

        Returns:
            Deletion results

        Business Logic:
        - Remove all chunks for document
        - Update document indexed flag to False
        - Return deletion summary
        """
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Delete chunks
        deleted_count = self.chunk_repository.delete_by_document_id(document_id)

        # Update document state
        if deleted_count > 0:
            document.indexed = False
            self.document_repository.update(document)

        return {
            "success": True,
            "document_id": document_id,
            "chunks_deleted": deleted_count,
            "document_indexed": False
        }

    def get_chunking_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about chunking across all documents.

        Returns:
            Chunking statistics and metrics
        """
        try:
            # Get all documents
            all_documents = self.document_repository.list_all()
            all_chunks = self.chunk_repository.list_all()

            # Calculate statistics
            stats = {
                "total_documents": len(all_documents),
                "indexed_documents": sum(1 for doc in all_documents if doc.indexed),
                "unindexed_documents": sum(1 for doc in all_documents if not doc.indexed),
                "total_chunks": len(all_chunks),
                "chunk_types": {},
                "chunks_per_document": {},
                "total_chunked_words": sum(chunk.word_count or 0 for chunk in all_chunks),
                "average_chunk_size": 0,
                "largest_chunk": 0,
                "smallest_chunk": float('inf') if all_chunks else 0
            }

            # Aggregate by chunk type
            for chunk in all_chunks:
                chunk_type = chunk.chunk_type or "unknown"
                stats["chunk_types"][chunk_type] = stats["chunk_types"].get(chunk_type, 0) + 1

                # Track chunk size metrics
                if chunk.word_count:
                    if chunk.word_count > stats["largest_chunk"]:
                        stats["largest_chunk"] = chunk.word_count
                    if chunk.word_count < stats["smallest_chunk"]:
                        stats["smallest_chunk"] = chunk.word_count

            # Calculate averages
            if all_chunks:
                word_counts = [chunk.word_count for chunk in all_chunks if chunk.word_count]
                if word_counts:
                    stats["average_chunk_size"] = sum(word_counts) / len(word_counts)

            if stats["smallest_chunk"] == float('inf'):
                stats["smallest_chunk"] = 0

            # Chunks per document distribution
            for document in all_documents:
                if document.indexed:
                    doc_chunks = [c for c in all_chunks if c.document_id == document.id]
                    chunk_count = len(doc_chunks)
                    count_key = f"{chunk_count}_chunks"
                    stats["chunks_per_document"][count_key] = stats["chunks_per_document"].get(count_key, 0) + 1

            return stats

        except Exception as e:
            raise ChunkingError(f"Failed to get chunking statistics: {str(e)}") from e

    def validate_chunking_strategy(self, strategy: str, document_id: int) -> Dict[str, Any]:
        """
        Validate if a chunking strategy is suitable for a document.

        Args:
            strategy: Strategy to validate
            document_id: Document to validate against

        Returns:
            Validation results with recommendations
        """
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        validation = {
            "valid": False,
            "strategy": strategy,
            "document_id": document_id,
            "document_type": document.file_type,
            "warnings": [],
            "recommendations": [],
            "estimated_chunks": 0
        }

        try:
            # Map strategy name (same mapping as index_document)
            strategy_name_mapping = {
                "fixed": "fixedlength",  # Map "fixed" to actual strategy name
                "chapter": "chapter",
                "section": "section", 
                "heading": "heading",
                "slide": "slide"
            }
            
            mapped_strategy = strategy_name_mapping.get(strategy, strategy)
            
            # Check if strategy is available
            chunking_strategy = self.strategy_factory.get_strategy_by_name(mapped_strategy)
            if not chunking_strategy:
                raise ValueError(f"Unknown chunking strategy: {strategy}")

            # Re-parse document content
            try:
                with open(document.file_path, encoding='utf-8') as f:
                    f.read()
            except Exception as e:
                raise ValueError(f"Failed to read document content: {str(e)}")
            validation["valid"] = True

            # Add recommendations based on document type
            if document.file_type == "pdf" and strategy != "chapter":
                validation["recommendations"].append(
                    "Consider 'chapter' strategy for PDF documents with chapter structure"
                )

            if document.file_type == "md" and strategy != "heading":
                validation["recommendations"].append(
                    "Consider 'heading' strategy for Markdown documents with heading structure"
                )

            # Estimate chunk count (rough calculation)
            if document.total_words:
                if strategy == "fixed":
                    estimated = document.total_words // 500  # Assume 500 words per chunk
                elif strategy == "chapter":
                    estimated = max(1, document.total_pages // 10) if document.total_pages else 5
                else:
                    estimated = max(1, document.total_words // 750)  # Conservative estimate

                validation["estimated_chunks"] = min(estimated, self.MAX_CHUNKS_PER_DOCUMENT)

                if estimated > self.MAX_CHUNKS_PER_DOCUMENT:
                    validation["warnings"].append(
                        f"Document may generate too many chunks ({estimated}). Consider different strategy."
                    )

        except Exception as e:
            validation["valid"] = False
            validation["warnings"].append(f"Strategy validation failed: {str(e)}")

        return validation


class ChunkingError(Exception):
    """
    Business logic exception for chunking operations.

    Raised when chunking operations fail due to business rule violations,
    strategy errors, or persistence failures.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        """
        Initialize ChunkingError.

        Args:
            message: Human-readable error description
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.cause = cause
