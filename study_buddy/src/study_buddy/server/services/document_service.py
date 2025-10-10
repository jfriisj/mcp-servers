"""
Document service for business logic orchestration.

This module implements the DocumentService class following Clean Architecture
Layer 2 principles, orchestrating document lifecycle operations while remaining
framework-agnostic.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.document import Document
from ..parsers.parser_factory import ParserFactory
from ..repositories.document_repository import DocumentRepository


class DocumentService:
    """
    Document business logic service.

    Orchestrates document operations including creation, retrieval, search,
    and deletion while enforcing business rules and coordinating between
    repositories and parsers.

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Depends on abstractions (repositories, parsers)
    - Contains reusable business rules
    - Validates input and enforces constraints
    - Coordinates operations across components

    SOLID Principles:
    - SRP: Single responsibility for document business logic
    - OCP: Open for extension via strategy patterns
    - LSP: Can be substituted with other document services
    - ISP: Focused interface for document operations only
    - DIP: Depends on repository and parser abstractions
    """

    # Business rule constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.md', '.txt', '.pptx'}

    def __init__(
        self,
        document_repository: DocumentRepository,
        parser_factory: ParserFactory
    ):
        """
        Initialize DocumentService with required dependencies.

        Args:
            document_repository: Repository for document persistence
            parser_factory: Factory for selecting appropriate parsers

        Note:
            Dependencies are injected to enable testing and flexibility.
        """
        self.document_repository = document_repository
        self.parser_factory = parser_factory

    def create_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Document:
        """
        Create a new document with parsing and validation.

        Business Logic:
        1. Validate file exists and meets business rules
        2. Check for duplicate files (same path)
        3. Parse file content and metadata
        4. Create document entity with proper defaults
        5. Persist document in repository

        Args:
            file_path: Absolute path to document file
            title: Optional title override (uses parsed title if None)
            tags: Optional list of categorization tags

        Returns:
            Created Document with populated ID and metadata

        Raises:
            ValueError: If file validation fails or business rules violated
            FileNotFoundError: If file doesn't exist
            DocumentError: If parsing or persistence fails

        Business Rules Enforced:
        - File must exist and be readable
        - File size must not exceed MAX_FILE_SIZE
        - File extension must be in SUPPORTED_EXTENSIONS
        - No duplicate file paths allowed
        - Title must not be empty after parsing
        """
        # Business Rule: File must exist
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        # Business Rule: File size limit
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_size} bytes exceeds maximum of {self.MAX_FILE_SIZE} bytes"
            )

        # Business Rule: Supported file types
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{file_ext}'. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Business Rule: No duplicate file paths
        if self.document_repository.exists_by_file_path(file_path):
            raise ValueError(f"Document already exists for file path: {file_path}")

        # Parse file using appropriate parser
        try:
            parser = self.parser_factory.get_parser(file_path)
            parse_result = parser.parse(file_path)
        except Exception as e:
            raise DocumentError(f"Failed to parse document: {str(e)}") from e

        # Business Rule: Document must have meaningful title
        document_title = title or parse_result.metadata.get("title") or os.path.basename(file_path)
        if not document_title.strip():
            raise ValueError("Document title cannot be empty")

        # Create document entity
        document = Document(
            title=document_title.strip(),
            file_path=file_path,
            file_type=parse_result.metadata.get("file_type", file_ext[1:]),
            total_pages=parse_result.metadata.get("total_pages"),
            total_words=len(parse_result.content.split()) if parse_result.content else 0,
            tags=tags or [],
            upload_date=datetime.now(),
            indexed=False,
            summarized=False
        )

        # Persist document
        try:
            return self.document_repository.create(document)
        except Exception as e:
            raise DocumentError(f"Failed to create document: {str(e)}") from e

    def get_document(self, document_id: int) -> Optional[Document]:
        """
        Retrieve document by ID.

        Args:
            document_id: Unique document identifier

        Returns:
            Document if found, None otherwise

        Raises:
            ValueError: If document_id is invalid
        """
        if document_id <= 0:
            raise ValueError("Document ID must be positive integer")

        return self.document_repository.get_by_id(document_id)

    def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Document]:
        """
        List documents with optional filtering and pagination.

        Args:
            filters: Optional filters for document attributes
            limit: Maximum number of documents to return
            offset: Number of documents to skip for pagination

        Returns:
            List of documents matching criteria

        Business Rules:
        - Limit must not exceed 1000 documents per request
        - Offset must be non-negative
        """
        # Business Rule: Reasonable pagination limits
        if limit is not None and limit > 1000:
            raise ValueError("Limit cannot exceed 1000 documents")

        if offset is not None and offset < 0:
            raise ValueError("Offset must be non-negative")

        # Apply pagination to filters
        pagination_filters = filters.copy() if filters else {}
        if limit is not None:
            pagination_filters["limit"] = limit
        if offset is not None:
            pagination_filters["offset"] = offset

        return self.document_repository.list_all(pagination_filters)

    def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 20
    ) -> List[Document]:
        """
        Search documents using full-text search.

        Args:
            query: Search query string
            filters: Optional additional filters
            limit: Maximum results to return (default 20)

        Returns:
            List of documents matching search query, ordered by relevance

        Raises:
            ValueError: If query is empty or invalid

        Business Rules:
        - Query must not be empty
        - Query length limited to 500 characters
        - Default limit of 20 results for performance
        """
        # Business Rule: Valid search query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        query = query.strip()
        if len(query) > 500:
            raise ValueError("Search query cannot exceed 500 characters")

        # Business Rule: Reasonable search limits
        if limit is not None and limit > 100:
            raise ValueError("Search limit cannot exceed 100 results")

        try:
            # Add limit to filters if provided
            search_filters = filters.copy() if filters else {}
            if limit is not None:
                search_filters["limit"] = limit

            # Get search results as (document, score) tuples
            search_results = self.document_repository.search(query, search_filters)

            # Extract just the documents (dropping scores for service layer)
            return [document for document, score in search_results]
        except Exception as e:
            raise DocumentError(f"Search failed: {str(e)}") from e

    def update_document(
        self,
        document_id: int,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Document:
        """
        Update document metadata.

        Args:
            document_id: Document to update
            title: New title (optional)
            tags: New tags list (optional)
            notes: User notes (optional)

        Returns:
            Updated document

        Raises:
            ValueError: If document not found or validation fails
        """
        # Retrieve existing document
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Business Rule: Title validation
        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("Document title cannot be empty")
            document.title = title

        # Update optional fields
        if tags is not None:
            document.tags = tags

        if notes is not None:
            document.notes = notes

        try:
            return self.document_repository.update(document)
        except Exception as e:
            raise DocumentError(f"Failed to update document: {str(e)}") from e

    def delete_document(self, document_id: int) -> bool:
        """
        Delete document and all associated data.

        Business Logic:
        1. Validate document exists
        2. Delete document (cascade to chunks and summaries)
        3. Optionally clean up file system (future enhancement)

        Args:
            document_id: Document to delete

        Returns:
            True if document was deleted, False if not found

        Raises:
            DocumentError: If deletion fails

        Note:
            This will cascade delete all chunks and summaries
            associated with the document due to foreign key constraints.
        """
        if document_id <= 0:
            raise ValueError("Document ID must be positive integer")

        # Verify document exists
        document = self.get_document(document_id)
        if not document:
            return False

        try:
            return self.document_repository.delete(document_id)
        except Exception as e:
            raise DocumentError(f"Failed to delete document: {str(e)}") from e

    def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about documents.

        Returns:
            Dictionary with document statistics

        Business Logic:
        - Count total documents
        - Count by file type
        - Count indexed vs unindexed
        - Count summarized vs unsummarized
        """
        try:
            all_documents = self.document_repository.list_all()

            stats = {
                "total_documents": len(all_documents),
                "indexed_count": sum(1 for doc in all_documents if doc.indexed),
                "summarized_count": sum(1 for doc in all_documents if doc.summarized),
                "file_types": {},
                "total_pages": 0,
                "total_words": 0
            }

            # Aggregate by file type
            for document in all_documents:
                file_type = document.file_type or "unknown"
                stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1

                if document.total_pages:
                    stats["total_pages"] += document.total_pages
                if document.total_words:
                    stats["total_words"] += document.total_words

            return stats

        except Exception as e:
            raise DocumentError(f"Failed to get statistics: {str(e)}") from e

    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file path for document creation without creating document.

        Args:
            file_path: Path to validate

        Returns:
            Validation result with status and metadata

        Business Logic:
        - Check file existence and accessibility
        - Validate file size and type
        - Check for duplicates
        - Preview parsing metadata
        """
        validation = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "metadata": {}
        }

        try:
            # Check existence
            if not os.path.exists(file_path):
                validation["errors"].append("File does not exist")
                return validation

            if not os.path.isfile(file_path):
                validation["errors"].append("Path is not a file")
                return validation

            # Check size
            file_size = os.path.getsize(file_path)
            validation["metadata"]["file_size"] = file_size

            if file_size > self.MAX_FILE_SIZE:
                validation["errors"].append(f"File size exceeds {self.MAX_FILE_SIZE} bytes")

            # Check type
            file_ext = os.path.splitext(file_path)[1].lower()
            validation["metadata"]["file_extension"] = file_ext

            if file_ext not in self.SUPPORTED_EXTENSIONS:
                validation["errors"].append(f"Unsupported file type '{file_ext}'")

            # Check duplicates
            existing_docs = self.document_repository.list_all({"file_path": file_path})
            if existing_docs:
                validation["warnings"].append("File already exists in database")

            # Try parsing preview
            if not validation["errors"]:
                try:
                    parser = self.parser_factory.get_parser(file_path)
                    parse_result = parser.parse(file_path)
                    validation["metadata"]["parsed_title"] = parse_result.metadata.get("title")
                    validation["metadata"]["total_pages"] = parse_result.metadata.get("total_pages")
                    validation["metadata"]["file_type"] = parse_result.metadata.get("file_type")
                    validation["valid"] = True
                except Exception as e:
                    validation["errors"].append(f"Parse preview failed: {str(e)}")

        except Exception as e:
            validation["errors"].append(f"Validation failed: {str(e)}")

        return validation


class DocumentError(Exception):
    """
    Business logic exception for document operations.

    Raised when document operations fail due to business rule violations,
    parsing errors, or persistence failures.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        """
        Initialize DocumentError.

        Args:
            message: Human-readable error description
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.cause = cause
