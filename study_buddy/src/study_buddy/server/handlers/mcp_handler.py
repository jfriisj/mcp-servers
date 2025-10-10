"""
MCP Protocol Handler for Study Buddy MCP Server.

This module implements the external interface layer (Layer 1) of Clean Architecture,
providing MCP tool definitions that expose the business services through the MCP protocol.

Clean Architecture Layer 1 Principles:
- Translates MCP protocol calls to service method calls
- No business logic - only protocol translation and validation
- Depends on service abstractions (Layer 2), not implementations
- Handles MCP-specific error formatting and response structures
- Provides comprehensive parameter validation for protocol compliance

MCP Tools Implemented:
- Document Management: upload, get, list, delete, search documents
- Indexing & Chunking: index documents, get structure, retrieve chunks
- AI Summary Management: save, get, list summaries for prompt builder workflow
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

# Handle imports for both module and direct execution
try:
    from ..models.study_session import SessionStatus, SessionType
    from ..services.chunking_service import ChunkingError, ChunkingService
    from ..services.document_service import DocumentError, DocumentService
    from ..services.progress_service import ProgressService
    from ..services.summary_service import SummaryError, SummaryService
    from ..services.bookmark_service import BookmarkService
    from ..services.prompt_service import PromptService
except ImportError:
    from study_buddy.server.models.study_session import SessionStatus, SessionType
    from study_buddy.server.services.chunking_service import ChunkingError, ChunkingService
    from study_buddy.server.services.document_service import DocumentError, DocumentService
    from study_buddy.server.services.progress_service import ProgressService
    from study_buddy.server.services.summary_service import SummaryError, SummaryService
    from study_buddy.server.services.bookmark_service import BookmarkService
    from study_buddy.server.services.prompt_service import PromptService

# Configure logging for MCP handler operations
logger = logging.getLogger(__name__)


class MCPHandlerError(Exception):
    """Custom exception for MCP handler-specific errors."""
    pass


class MCPHandler:
    """
    MCP Protocol Handler implementing Clean Architecture Layer 1.

    Responsibilities:
    - Translate MCP protocol calls to service method calls
    - Validate MCP tool parameters and sanitize inputs
    - Format responses according to MCP protocol standards
    - Handle errors with appropriate MCP error responses
    - Log operations for monitoring and debugging

    Does NOT:
    - Contain business logic (delegates to services)
    - Directly access database or infrastructure
    - Implement parsing, chunking, or summary generation logic

    Dependencies (injected):
    - DocumentService: Document lifecycle management
    - ChunkingService: Content structure and chunking
    - SummaryService: AI-generated summary management
    - PromptService: AI prompt generation and orchestration
    """

    def __init__(
        self,
        document_service: DocumentService,
        chunking_service: ChunkingService,
        summary_service: SummaryService,
        bookmark_service: BookmarkService,
        progress_service: ProgressService,
        prompt_service: PromptService
    ):
        """
        Initialize MCP handler with service dependencies.

        Args:
            document_service: Service for document operations
            chunking_service: Service for chunking operations
            summary_service: Service for summary operations
            bookmark_service: Service for bookmark operations
            progress_service: Service for progress tracking operations
            prompt_service: Service for prompt generation operations
        """
        self.document_service = document_service
        self.chunking_service = chunking_service
        self.summary_service = summary_service
        self.bookmark_service = bookmark_service
        self.progress_service = progress_service
        self.prompt_service = prompt_service

        logger.info("MCPHandler initialized with service dependencies")

    # ============================================================================
    # UTILITY METHODS - Error Handling and Response Formatting
    # ============================================================================

    def _create_success_response(
        self,
        data: Any = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create standardized success response for MCP tools.

        Args:
            data: Response data payload
            message: Optional success message

        Returns:
            MCP-compatible success response
        """
        response: Dict[str, Any] = {"success": True}

        if data is not None:
            response["data"] = data

        if message:
            response["message"] = message

        return response

    def _create_error_response(
        self,
        error_message: str,
        error_type: str = "system",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response for MCP tools.

        Args:
            error_message: Human-readable error description
            error_type: Error category (validation, not_found, business_rule, system)
            error_code: Machine-readable error code
            details: Additional error context and debugging info

        Returns:
            MCP-compatible error response
        """
        response = {
            "success": False,
            "error": error_message,
            "error_type": error_type
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        return response

    def _handle_service_error(self, e: Exception, operation: str) -> Dict[str, Any]:
        """
        Translate service layer exceptions to MCP error responses.

        Args:
            e: Exception from service layer
            operation: Operation that failed (for logging)

        Returns:
            MCP-compatible error response
        """
        logger.error(f"Service error in {operation}: {str(e)}", exc_info=True)

        # Map service exceptions to MCP error types
        if isinstance(e, ValueError):
            return self._create_error_response(
                error_message=str(e),
                error_type="validation",
                error_code="INVALID_PARAMETER"
            )
        elif isinstance(e, (DocumentError, ChunkingError, SummaryError)):
            return self._create_error_response(
                error_message=str(e),
                error_type="business_rule",
                error_code=type(e).__name__.upper().replace("ERROR", "_ERROR")
            )
        else:
            return self._create_error_response(
                error_message=f"System error during {operation}: {str(e)}",
                error_type="system",
                error_code="INTERNAL_ERROR"
            )

    def _validate_positive_integer(self, value: Any, param_name: str) -> int:
        """
        Validate and convert parameter to positive integer.

        Args:
            value: Parameter value to validate
            param_name: Parameter name for error messages

        Returns:
            Validated integer value

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, (int, str)):
            raise ValueError(f"{param_name} must be an integer, got {type(value).__name__}")

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be a valid integer, got '{value}'")

        if int_value <= 0:
            raise ValueError(f"{param_name} must be positive, got {int_value}")

        return int_value

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate file path for document upload.

        Args:
            file_path: Path to validate

        Returns:
            Validated absolute file path

        Raises:
            ValueError: If path validation fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path is required and must be a string")

        # Convert to absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            raise ValueError(f"File does not exist: {abs_path}")

        if not os.path.isfile(abs_path):
            raise ValueError(f"Path is not a file: {abs_path}")

        return abs_path

    # ============================================================================
    # DOCUMENT MANAGEMENT TOOLS - Priority 1
    # ============================================================================

    def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Upload and parse document file, store in database.

        MCP Tool: upload_document
        Primary workflow: User uploads document via GUI or direct MCP call

        Args:
            file_path: Absolute path to document file
            title: Optional custom title (auto-detected if not provided)
            tags: Optional list of tags for categorization

        Returns:
            MCP response with document creation results

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "title": "Angular Projects - 2nd Edition",
                "file_type": "pdf",
                "total_pages": 450,
                "total_words": 125000,
                "upload_date": "2025-10-06T10:30:00Z"
            },
            "message": "Document uploaded successfully"
        }
        """
        try:
            # Parameter validation
            validated_path = self._validate_file_path(file_path)

            if tags is not None and not isinstance(tags, list):
                raise ValueError("tags must be a list of strings")

            if tags:
                for tag in tags:
                    if not isinstance(tag, str) or not tag.strip():
                        raise ValueError("All tags must be non-empty strings")

            # Delegate to service layer
            logger.info(f"Uploading document: {validated_path}")
            document = self.document_service.create_document(
                file_path=validated_path,
                title=title,
                tags=tags or []
            )

            # Format response
            response_data = {
                "document_id": document.id,
                "title": document.title,
                "file_type": document.file_type,
                "total_pages": document.total_pages,
                "total_words": document.total_words,
                "upload_date": document.upload_date.isoformat() if document.upload_date else None,
                "tags": document.tags
            }

            logger.info(f"Document uploaded successfully: ID={document.id}, Title='{document.title}'")
            return self._create_success_response(
                data=response_data,
                message="Document uploaded successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "upload_document")

    def get_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve document by ID with metadata.

        MCP Tool: get_document
        Primary workflow: GUI document browser, AI agent document selection

        Args:
            document_id: Document ID to retrieve

        Returns:
            MCP response with document details

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "title": "Angular Projects - 2nd Edition",
                "file_path": "/uploads/angular-book.pdf",
                "file_type": "pdf",
                "total_pages": 450,
                "total_words": 125000,
                "indexed": true,
                "summarized": false,
                "tags": ["angular", "web-development"],
                "upload_date": "2025-10-06T10:30:00Z"
            }
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting document: {doc_id}")
            document = self.document_service.get_document(doc_id)

            if not document:
                return self._create_error_response(
                    error_message=f"Document {doc_id} not found",
                    error_type="not_found",
                    error_code="DOCUMENT_NOT_FOUND",
                    details={"document_id": doc_id}
                )

            # Format response
            response_data = {
                "document_id": document.id,
                "title": document.title,
                "file_path": document.file_path,
                "file_type": document.file_type,
                "total_pages": document.total_pages,
                "total_words": document.total_words,
                "indexed": document.indexed,
                "summarized": document.summarized,
                "tags": document.tags,
                "notes": document.notes,
                "upload_date": document.upload_date.isoformat() if document.upload_date else None,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "get_document")

    def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents with optional filtering and pagination.

        MCP Tool: list_documents
        Primary workflow: GUI document browser, document management

        Args:
            filters: Optional filters (file_type, indexed, tags, date_from, date_to)
            limit: Maximum documents to return (default 20, max 100)
            offset: Number of documents to skip for pagination

        Returns:
            MCP response with document list and pagination info

        Example Response:
        {
            "success": true,
            "data": {
                "documents": [
                    {
                        "document_id": 42,
                        "title": "Angular Projects",
                        "file_type": "pdf",
                        "indexed": true,
                        "total_pages": 450,
                        "upload_date": "2025-10-06T10:30:00Z"
                    }
                ],
                "pagination": {
                    "limit": 20,
                    "offset": 0,
                    "total": 1,
                    "has_more": false
                }
            }
        }
        """
        try:
            # Parameter validation
            if limit <= 0 or limit > 100:
                raise ValueError("limit must be between 1 and 100")

            if offset < 0:
                raise ValueError("offset must be non-negative")

            if filters is not None and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Listing documents: filters={filters}, limit={limit}, offset={offset}")
            documents = self.document_service.list_documents(
                filters=filters,
                limit=limit,
                offset=offset
            )

            # Get total count for pagination
            total_count = len(self.document_service.list_documents(filters=filters))

            # Format response
            document_list = []
            for doc in documents:
                document_list.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "file_type": doc.file_type,
                    "indexed": doc.indexed,
                    "summarized": doc.summarized,
                    "total_pages": doc.total_pages,
                    "total_words": doc.total_words,
                    "tags": doc.tags,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
                })

            response_data = {
                "documents": document_list,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": offset + len(documents) < total_count
                }
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "list_documents")

    def delete_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Delete document and all related data (chunks, summaries).

        MCP Tool: delete_document
        Primary workflow: Document cleanup, storage management

        Args:
            document_id: Document ID to delete

        Returns:
            MCP response with deletion confirmation

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "deleted": true,
                "chunks_deleted": 12,
                "summaries_deleted": 5
            },
            "message": "Document and related data deleted successfully"
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.info(f"Deleting document: {doc_id}")
            result = self.document_service.delete_document(doc_id)

            if not result:
                return self._create_error_response(
                    error_message=f"Document {doc_id} not found or could not be deleted",
                    error_type="not_found",
                    error_code="DOCUMENT_NOT_FOUND",
                    details={"document_id": doc_id}
                )

            # Format response
            response_data = {
                "document_id": doc_id,
                "deleted": True
            }

            logger.info(f"Document deleted successfully: ID={doc_id}")
            return self._create_success_response(
                data=response_data,
                message="Document and related data deleted successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "delete_document")

    def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Full-text search across documents and chunks.

        MCP Tool: search_documents
        Primary workflow: Content discovery, research assistance

        Args:
            query: Search query string
            filters: Optional filters (file_type, indexed, date_from, date_to)
            limit: Maximum results to return (default 20, max 50)

        Returns:
            MCP response with search results and relevance scores

        Example Response:
        {
            "success": true,
            "data": {
                "query": "angular components",
                "results": [
                    {
                        "document_id": 42,
                        "document_title": "Angular Projects",
                        "chunk_id": 105,
                        "chunk_title": "Chapter 3: Components",
                        "match_excerpt": "Angular components are the building blocks...",
                        "relevance_score": 0.95
                    }
                ],
                "total_results": 15
            }
        }
        """
        try:
            # DEBUG: Add logging to trace execution
            logger.info(f"MCPHandler.search_documents called with query='{query}', limit={limit}")
            
            # Parameter validation
            if not query or not isinstance(query, str):
                raise ValueError("query is required and must be a non-empty string")

            query = query.strip()
            if not query:
                raise ValueError("query cannot be empty or only whitespace")

            if len(query) > 500:
                raise ValueError("query is too long (max 500 characters)")

            if limit <= 0 or limit > 50:
                raise ValueError("limit must be between 1 and 50")

            if filters is not None and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.info(f"DEBUG: About to call document_service.search_documents with query='{query}', limit={limit}")
            results = self.document_service.search_documents(
                query=query,
                filters=filters,
                limit=limit
            )
            logger.info(f"DEBUG: Service returned {len(results)} results")

            # Format response
            search_results = []
            for document in results:
                search_results.append({
                    "document_id": document.id,
                    "document_title": document.title,
                    "file_type": document.file_type,
                    "indexed": document.indexed,
                    "total_pages": document.total_pages,
                    "total_words": document.total_words,
                    "tags": document.tags,
                    "upload_date": document.upload_date.isoformat() if document.upload_date else None
                })

            response_data = {
                "query": query,
                "results": search_results,
                "total_results": len(search_results)
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "search_documents")


    # ============================================================================
    # CHUNKING & INDEXING TOOLS - Priority 2
    # ============================================================================

    def index_document(
        self,
        document_id: Union[int, str],
        strategy: str = "auto",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze document structure and create intelligent chunks.

        MCP Tool: index_document
        Primary workflow: Prepare document for AI summarization

        Args:
            document_id: Document to index
            strategy: Chunking strategy ("auto", "slide", "chapter", "section", "heading", "fixed")
            force: Whether to force re-indexing if already indexed

        Returns:
            MCP response with chunking results

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "chunks_created": 12,
                "strategy_used": "chapter",
                "chunks": [
                    {
                        "chunk_id": 101,
                        "chunk_index": 0,
                        "chunk_type": "chapter",
                        "title": "Chapter 1: Introduction",
                        "word_count": 1250
                    }
                ]
            },
            "message": "Document indexed successfully with 12 chunks"
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            valid_strategies = ["auto", "slide", "chapter", "section", "heading", "fixed"]
            if strategy not in valid_strategies:
                raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")

            # Delegate to service layer
            logger.info(f"Indexing document: {doc_id} with strategy '{strategy}' force={force}")
            result = self.chunking_service.index_document(
                document_id=doc_id,
                strategy=strategy,
                force_reindex=force
            )

            # Format response - chunks are already formatted by service
            chunks_list = result.get("chunks", [])

            response_data = {
                "document_id": doc_id,
                "chunks_created": result.get("chunks_created", 0),
                "strategy_used": result.get("strategy_used", strategy),
                "chunks": chunks_list
            }

            logger.info(f"Document indexed successfully: ID={doc_id}, chunks={len(chunks_list)}")
            return self._create_success_response(
                data=response_data,
                message=f"Document indexed successfully with {len(chunks_list)} chunks"
            )

        except Exception as e:
            return self._handle_service_error(e, "index_document")

    def get_document_structure(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get indexed structure (chunks) of document for GUI display.

        MCP Tool: get_document_structure
        Primary workflow: GUI content viewer, AI agent chunk selection

        Args:
            document_id: Document to get structure for

        Returns:
            MCP response with document structure and chunk list

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "document_title": "Angular Projects",
                "indexed": true,
                "total_chunks": 12,
                "chunks": [
                    {
                        "chunk_id": 101,
                        "chunk_index": 0,
                        "title": "Chapter 1: Introduction",
                        "chunk_type": "chapter",
                        "word_count": 1250
                    }
                ]
            }
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting document structure: {doc_id}")
            result = self.chunking_service.get_document_structure(doc_id)

            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "get_document_structure")

    def get_chunk_content(self, chunk_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve full text content of specific chunk.

        MCP Tool: get_chunk_content
        Primary workflow: AI agent summarization - get content to summarize

        Args:
            chunk_id: Chunk to retrieve content for

        Returns:
            MCP response with chunk content and metadata

        Example Response:
        {
            "success": true,
            "data": {
                "chunk_id": 101,
                "document_id": 42,
                "chunk_index": 0,
                "title": "Chapter 1: Introduction",
                "content": "Full text content of the chunk...",
                "word_count": 1250,
                "chunk_type": "chapter"
            }
        }
        """
        try:
            # Parameter validation
            c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.debug(f"Getting chunk content: {c_id}")
            result = self.chunking_service.get_chunk_content(c_id)

            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "get_chunk_content")

    def list_chunks(
        self,
        document_id: Optional[Union[int, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List chunks with optional filtering and pagination.

        MCP Tool: list_chunks
        Primary workflow: Content management, chunk overview

        Args:
            document_id: Optional document filter
            filters: Optional filters (chunk_type, word_count_min, word_count_max)
            limit: Maximum chunks to return (default 50, max 200)
            offset: Number of chunks to skip for pagination

        Returns:
            MCP response with chunk list and pagination info
        """
        try:
            # Parameter validation
            doc_id = None
            if document_id is not None:
                doc_id = self._validate_positive_integer(document_id, "document_id")

            if limit <= 0 or limit > 200:
                raise ValueError("limit must be between 1 and 200")

            if offset < 0:
                raise ValueError("offset must be non-negative")

            if filters is not None and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Listing chunks: document_id={doc_id}, limit={limit}, offset={offset}")

            # Extract chunk_type from filters if provided
            chunk_type = None
            if filters:
                chunk_type = filters.get("chunk_type")

            result = self.chunking_service.list_chunks(
                document_id=doc_id,
                chunk_type=chunk_type,
                limit=limit,
                offset=offset
            )

            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "list_chunks")

    # ============================================================================
    # AI SUMMARY MANAGEMENT TOOLS - Priority 3
    # ============================================================================

    def save_summary(
        self,
        summary_content: str,
        summary_type: str,
        chunk_id: Optional[Union[int, str]] = None,
        document_id: Optional[Union[int, str]] = None,
        model_name: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Save AI-generated summary to database.

        MCP Tool: save_summary
        Primary workflow: AI agent saves generated summary after processing

        Args:
            content: Summary content in markdown format
            summary_type: Type of summary ("brief", "standard", "detailed")
            chunk_id: Target chunk ID (mutually exclusive with document_id)
            document_id: Target document ID (mutually exclusive with chunk_id)
            model_name: AI model used for generation
            metadata: Additional metadata (focus areas, generation params)
            overwrite_existing: Replace existing summary of same type

        Returns:
            MCP response with save confirmation and summary details
        """
        try:
            # Parameter validation
            if not summary_content or not isinstance(summary_content, str):
                raise ValueError("summary_content is required and must be a non-empty string")

            summary_content = summary_content.strip()
            if not summary_content:
                raise ValueError("summary_content cannot be empty or only whitespace")

            valid_types = ["brief", "standard", "detailed", "custom"]
            if summary_type not in valid_types:
                raise ValueError(f"Invalid summary_type '{summary_type}'. Must be one of: {valid_types}")

            # Validate exactly one target
            c_id = None
            d_id = None

            if chunk_id is not None:
                c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            if document_id is not None:
                d_id = self._validate_positive_integer(document_id, "document_id")

            if c_id is None and d_id is None:
                raise ValueError("Either chunk_id or document_id must be provided")

            if c_id is not None and d_id is not None:
                raise ValueError("Cannot specify both chunk_id and document_id")

            if metadata is not None and not isinstance(metadata, dict):
                raise ValueError("metadata must be a dictionary")

            # Delegate to service layer
            logger.info(f"Saving summary: type={summary_type}, chunk_id={c_id}, document_id={d_id}")
            result = self.summary_service.save_summary(
                content=summary_content,
                summary_type=summary_type,
                chunk_id=c_id,
                document_id=d_id,
                model_name=model_name,
                metadata=metadata,
                overwrite_existing=overwrite_existing
            )

            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "save_summary")

    def get_summary(self, summary_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve summary by ID with full content and metadata.

        MCP Tool: get_summary
        Primary workflow: GUI summary display, summary management

        Args:
            summary_id: Summary ID to retrieve

        Returns:
            MCP response with summary content and metadata
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(summary_id, "summary_id")

            # Delegate to service layer
            logger.debug(f"Getting summary: {s_id}")
            result = self.summary_service.get_summary(s_id)

            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "get_summary")

    def get_summaries_for_chunk(self, chunk_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get all summaries for specific chunk.

        MCP Tool: get_summaries_for_chunk
        Primary workflow: GUI prompt builder - show available summaries

        Args:
            chunk_id: Chunk to get summaries for

        Returns:
            MCP response with list of summaries for chunk
        """
        try:
            # Parameter validation
            c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.debug(f"Getting summaries for chunk: {c_id}")
            result = self.summary_service.get_summaries_for_chunk(c_id)

            response_data = {
                "chunk_id": c_id,
                "summaries": result
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "get_summaries_for_chunk")

    def get_summaries_for_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get all summaries for specific document (document-level and all chunks).

        MCP Tool: get_summaries_for_document
        Primary workflow: Document overview, summary management

        Args:
            document_id: Document to get summaries for

        Returns:
            MCP response with list of all summaries for document
        """
        try:
            # Parameter validation
            d_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting summaries for document: {d_id}")
            result = self.summary_service.get_summaries_for_document(d_id)

            response_data = {
                "document_id": d_id,
                "summaries": result
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "get_summaries_for_document")

    def list_summaries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "generation_date",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List summaries with filtering, sorting, and pagination.

        MCP Tool: list_summaries
        Primary workflow: Summary management, analytics

        Args:
            filters: Optional filters (summary_type, model_name, date_from, date_to)
            sort_by: Field to sort by ("generation_date", "word_count", "summary_type")
            sort_order: Sort order ("asc" or "desc")
            limit: Maximum summaries to return (default 50, max 200)
            offset: Number of summaries to skip for pagination

        Returns:
            MCP response with summary list and pagination info
        """
        try:
            # Parameter validation
            if limit <= 0 or limit > 200:
                raise ValueError("limit must be between 1 and 200")

            if offset < 0:
                raise ValueError("offset must be non-negative")

            if sort_order not in ["asc", "desc"]:
                raise ValueError("sort_order must be 'asc' or 'desc'")

            if filters is not None and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Listing summaries: limit={limit}, offset={offset}")
            summaries = self.summary_service.list_summaries(
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset
            )

            # Get total count for pagination (call without limit/offset)
            total_count = len(self.summary_service.list_summaries(filters=filters))

            # Format response with pagination
            response_data = {
                "summaries": summaries,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": offset + len(summaries) < total_count
                }
            }

            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "list_summaries")

    # ============================================================================
    # PROMPT GENERATION TOOLS - AI Agent Assistance
    # ============================================================================

    def generate_prompt(
        self,
        prompt_type: str,
        target_ids: List[Union[int, str]],
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Generate AI-ready prompts for document/chunk analysis.

        MCP Tool: generate_prompt
        Primary workflow: User specifies requirements → Get formatted AI prompt

        Args:
            prompt_type: Type of prompt ("summary", "analysis", "comparison")
            target_ids: List of document or chunk IDs to process
            target_type: Type of targets ("document" or "chunk") 
            detail_level: Level of detail ("brief", "standard", "detailed")
            focus_areas: Optional list of areas to emphasize
            custom_instructions: Optional user-provided additional instructions
            output_format: Format for AI output ("markdown", "text", "json")

        Returns:
            MCP response with complete formatted prompt ready for AI agent

        Example Response:
        {
            "success": true,
            "data": {
                "prompt_text": "# AI Task: Create Standard Summary...",
                "prompt_type": "summary",
                "detail_level": "standard", 
                "target_info": {"type": "chunk", "ids": [102], "count": 1},
                "focus_areas": ["key concepts", "practical examples"],
                "metadata": {"word_count_target": {"min": 250, "max": 350}},
                "word_count": 450,
                "line_count": 35
            },
            "message": "Summary prompt generated for 1 chunk"
        }
        """
        try:
            # Parameter validation
            if not prompt_type or not isinstance(prompt_type, str):
                raise ValueError("prompt_type is required and must be a string")

            if not target_ids or not isinstance(target_ids, list):
                raise ValueError("target_ids is required and must be a list")

            if not target_type or target_type not in ["document", "chunk"]:
                raise ValueError("target_type must be 'document' or 'chunk'")

            if not detail_level or detail_level not in ["brief", "standard", "detailed"]:
                raise ValueError("detail_level must be 'brief', 'standard', or 'detailed'")

            # Convert target IDs to integers
            validated_ids = []
            for target_id in target_ids:
                validated_ids.append(self._validate_positive_integer(target_id, "target_id"))

            if focus_areas is not None:
                if not isinstance(focus_areas, list):
                    raise ValueError("focus_areas must be a list of strings")
                for area in focus_areas:
                    if not isinstance(area, str) or not area.strip():
                        raise ValueError("All focus_areas must be non-empty strings")

            if output_format not in ["markdown", "text", "json"]:
                raise ValueError("output_format must be 'markdown', 'text', or 'json'")

            # Delegate to service layer
            logger.info(f"Generating prompt: type={prompt_type}, targets={len(validated_ids)} {target_type}(s)")
            result = self.prompt_service.generate_prompt(
                prompt_type=prompt_type,
                target_ids=validated_ids,
                target_type=target_type,
                detail_level=detail_level,
                focus_areas=focus_areas,
                custom_instructions=custom_instructions,
                output_format=output_format
            )

            # Format response
            response_data = result.to_dict()

            logger.info(f"Prompt generated successfully: {len(validated_ids)} {target_type}(s), {len(result.prompt_text.split())} words")
            return self._create_success_response(
                data=response_data,
                message=f"{prompt_type.title()} prompt generated for {len(validated_ids)} {target_type}(s)"
            )

        except Exception as e:
            return self._handle_service_error(e, "generate_prompt")

    def get_available_prompt_types(self) -> Dict[str, Any]:
        """
        Get list of available prompt types and their capabilities.

        MCP Tool: get_available_prompt_types
        Primary workflow: GUI discovery - show available prompt options

        Returns:
            MCP response with prompt types and their information

        Example Response:
        {
            "success": true,
            "data": {
                "prompt_types": {
                    "summary": {
                        "name": "Summary Generation",
                        "supports_documents": true,
                        "supports_chunks": true,
                        "detail_levels": ["brief", "standard", "detailed"],
                        "output_formats": ["markdown", "text", "json"]
                    }
                }
            }
        }
        """
        try:
            # Delegate to service layer
            logger.debug("Getting available prompt types")
            prompt_types = self.prompt_service.get_available_prompt_types()

            # Get detailed info for each type
            type_info = {}
            for prompt_type in prompt_types:
                type_info[prompt_type] = self.prompt_service.get_strategy_info(prompt_type)

            response_data = {
                "prompt_types": type_info,
                "total": len(prompt_types)
            }

            return self._create_success_response(
                data=response_data,
                message=f"Retrieved {len(prompt_types)} available prompt types"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_available_prompt_types")

    def validate_prompt_targets(
        self,
        target_ids: List[Union[int, str]],
        target_type: str,
        prompt_type: str
    ) -> Dict[str, Any]:
        """
        Validate targets exist and are compatible with prompt type.

        MCP Tool: validate_prompt_targets
        Primary workflow: GUI validation - check targets before generating prompt

        Args:
            target_ids: List of target IDs to validate
            target_type: Type of targets ("document" or "chunk")
            prompt_type: Type of prompt being generated

        Returns:
            MCP response with validation results and target information

        Example Response:
        {
            "success": true,
            "data": {
                "valid": true,
                "target_count": 2,
                "target_type": "chunk", 
                "prompt_type": "summary",
                "targets": [
                    {"id": 102, "title": "Chapter 2", "word_count": 1250},
                    {"id": 103, "title": "Chapter 3", "word_count": 980}
                ],
                "strategy_name": "Summary Generation"
            }
        }
        """
        try:
            # Parameter validation
            if not target_ids or not isinstance(target_ids, list):
                raise ValueError("target_ids is required and must be a list")

            if not target_type or target_type not in ["document", "chunk"]:
                raise ValueError("target_type must be 'document' or 'chunk'")

            if not prompt_type or not isinstance(prompt_type, str):
                raise ValueError("prompt_type is required and must be a string")

            # Convert target IDs to integers
            validated_ids = []
            for target_id in target_ids:
                validated_ids.append(self._validate_positive_integer(target_id, "target_id"))

            # Delegate to service layer
            logger.debug(f"Validating prompt targets: {len(validated_ids)} {target_type}(s) for {prompt_type}")
            result = self.prompt_service.validate_targets_for_prompt(
                target_ids=validated_ids,
                target_type=target_type,
                prompt_type=prompt_type
            )

            return self._create_success_response(
                data=result,
                message=f"Validated {len(validated_ids)} {target_type}(s) for {prompt_type} prompt"
            )

        except Exception as e:
            return self._handle_service_error(e, "validate_prompt_targets")

    def get_prompt_preview(
        self,
        prompt_type: str,
        target_count: Union[int, str],
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get preview description of what prompt will generate.

        MCP Tool: get_prompt_preview
        Primary workflow: GUI preview - show user what prompt will do

        Args:
            prompt_type: Type of prompt
            target_count: Number of targets 
            target_type: Type of targets
            detail_level: Detail level
            focus_areas: Optional focus areas

        Returns:
            MCP response with human-readable prompt description

        Example Response:
        {
            "success": true,
            "data": {
                "preview": "Generate standard summary (250-350 words) for 2 chunks, focusing on key concepts and practical examples. Uses Summary Generation strategy.",
                "word_count_range": "250-350 words",
                "strategy": "Summary Generation"
            }
        }
        """
        try:
            # Parameter validation
            if not prompt_type or not isinstance(prompt_type, str):
                raise ValueError("prompt_type is required and must be a string")

            count = self._validate_positive_integer(target_count, "target_count")

            if not target_type or target_type not in ["document", "chunk"]:
                raise ValueError("target_type must be 'document' or 'chunk'")

            if not detail_level or detail_level not in ["brief", "standard", "detailed"]:
                raise ValueError("detail_level must be 'brief', 'standard', or 'detailed'")

            if focus_areas is not None and not isinstance(focus_areas, list):
                raise ValueError("focus_areas must be a list of strings")

            # Delegate to service layer
            logger.debug(f"Getting prompt preview: {prompt_type} for {count} {target_type}(s)")
            preview = self.prompt_service.get_prompt_preview(
                prompt_type=prompt_type,
                target_count=count,
                target_type=target_type,
                detail_level=detail_level,
                focus_areas=focus_areas
            )

            response_data = {
                "preview": preview,
                "prompt_type": prompt_type,
                "target_count": count,
                "target_type": target_type,
                "detail_level": detail_level
            }

            return self._create_success_response(
                data=response_data,
                message="Prompt preview generated"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_prompt_preview")

    # ============================================================================
    # UTILITY TOOLS - Additional functionality
    # ============================================================================

    def get_summary_statistics(
        self,
        document_id: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for analytics and monitoring.

        MCP Tool: get_summary_statistics
        Primary workflow: Analytics dashboard, progress tracking

        Args:
            document_id: Optional document filter

        Returns:
            MCP response with summary statistics
        """
        try:
            # Parameter validation
            doc_id = None
            if document_id is not None:
                doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting summary statistics: document_id={doc_id}")

            if doc_id:
                # Get statistics for specific document
                stats = {}
                # Note: This would need a service method for document-specific stats
            else:
                # Get global summary statistics
                stats = self.summary_service.get_summary_statistics()

            return self._create_success_response(data=stats)

        except Exception as e:
            return self._handle_service_error(e, "get_summary_statistics")

    # ============================================================================
    # BOOKMARK MANAGEMENT TOOLS - Task 14 Phase 2
    # ============================================================================

    def create_document_bookmark(
        self,
        title: str,
        document_id: Union[int, str],
        category: str = "General",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        color: str = "#FFD700",
        page_number: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a bookmark for a document.

        MCP Tool: create_document_bookmark
        Primary workflow: User bookmarks document from GUI or AI agent

        Args:
            title: Bookmark title
            document_id: ID of document to bookmark
            category: Bookmark category (default: "General")
            notes: Optional bookmark notes
            tags: Optional list of tags
            color: Bookmark color (hex format, default: "#FFD700")
            page_number: Optional specific page number

        Returns:
            MCP response with created bookmark data
        """
        try:
            # Parameter validation
            if not title or not title.strip():
                raise MCPHandlerError("title is required")

            doc_id = self._validate_positive_integer(document_id, "document_id")

            page_num = None
            if page_number is not None:
                page_num = self._validate_positive_integer(page_number, "page_number")

            # Prepare bookmark data
            bookmark_data = {
                "notes": notes,
                "tags": tags or [],
                "color": color,
                "page_number": page_num
            }

            # Delegate to service layer
            logger.debug(f"Creating document bookmark: title={title}, document_id={doc_id}")

            bookmark = self.bookmark_service.create_document_bookmark(
                title=title,
                document_id=doc_id,
                category=category,
                **bookmark_data
            )

            return self._create_success_response(
                data={
                    "bookmark_id": bookmark.id,
                    "title": bookmark.title,
                    "document_id": bookmark.document_id,
                    "category": bookmark.category,
                    "color": bookmark.color,
                    "created_at": bookmark.created_at.isoformat() if bookmark.created_at else None
                },
                message=f"Document bookmark created: {bookmark.title}"
            )

        except Exception as e:
            return self._handle_service_error(e, "create_document_bookmark")

    def create_chunk_bookmark(
        self,
        title: str,
        document_id: Union[int, str],
        chunk_id: Union[int, str],
        category: str = "General",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        color: str = "#FFD700"
    ) -> Dict[str, Any]:
        """
        Create a bookmark for a specific chunk.

        MCP Tool: create_chunk_bookmark
        Primary workflow: User bookmarks specific section/chapter from GUI

        Args:
            title: Bookmark title
            document_id: ID of document containing chunk
            chunk_id: ID of chunk to bookmark
            category: Bookmark category (default: "General")
            notes: Optional bookmark notes
            tags: Optional list of tags
            color: Bookmark color (hex format, default: "#FFD700")

        Returns:
            MCP response with created bookmark data
        """
        try:
            # Parameter validation
            if not title or not title.strip():
                raise MCPHandlerError("title is required")

            doc_id = self._validate_positive_integer(document_id, "document_id")
            chunk_id_val = self._validate_positive_integer(chunk_id, "chunk_id")

            # Prepare bookmark data
            bookmark_data = {
                "notes": notes,
                "tags": tags or [],
                "color": color
            }

            # Delegate to service layer
            logger.debug(f"Creating chunk bookmark: title={title}, chunk_id={chunk_id_val}")

            bookmark = self.bookmark_service.create_chunk_bookmark(
                title=title,
                document_id=doc_id,
                chunk_id=chunk_id_val,
                category=category,
                **bookmark_data
            )

            return self._create_success_response(
                data={
                    "bookmark_id": bookmark.id,
                    "title": bookmark.title,
                    "document_id": bookmark.document_id,
                    "chunk_id": bookmark.chunk_id,
                    "category": bookmark.category,
                    "color": bookmark.color,
                    "created_at": bookmark.created_at.isoformat() if bookmark.created_at else None
                },
                message=f"Chunk bookmark created: {bookmark.title}"
            )

        except Exception as e:
            return self._handle_service_error(e, "create_chunk_bookmark")

    def get_bookmark(self, bookmark_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve bookmark by ID.

        MCP Tool: get_bookmark
        Primary workflow: Display bookmark details in GUI

        Args:
            bookmark_id: Bookmark ID

        Returns:
            MCP response with bookmark data or not found error
        """
        try:
            # Parameter validation
            bookmark_id_val = self._validate_positive_integer(bookmark_id, "bookmark_id")

            # Delegate to service layer
            logger.debug(f"Getting bookmark: bookmark_id={bookmark_id_val}")

            bookmark = self.bookmark_service.get_bookmark(bookmark_id_val)

            if not bookmark:
                return self._create_error_response(
                    error_message=f"Bookmark {bookmark_id_val} not found",
                    error_type="not_found",
                    error_code="BOOKMARK_NOT_FOUND"
                )

            return self._create_success_response(
                data=bookmark.to_dict(),
                message=f"Retrieved bookmark: {bookmark.title}"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_bookmark")

    def list_bookmarks(
        self,
        document_id: Optional[Union[int, str]] = None,
        category: Optional[str] = None,
        is_favorite: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        List bookmarks with optional filtering.

        MCP Tool: list_bookmarks
        Primary workflow: Display bookmark list in GUI, filtered views

        Args:
            document_id: Optional filter by document
            category: Optional filter by category
            is_favorite: Optional filter by favorite status

        Returns:
            MCP response with bookmark list
        """
        try:
            # Build filters
            filters = {}

            if document_id is not None:
                filters["document_id"] = self._validate_positive_integer(document_id, "document_id")

            if category is not None:
                filters["category"] = category

            if is_favorite is not None:
                filters["is_favorite"] = is_favorite

            # Delegate to service layer
            logger.debug(f"Listing bookmarks with filters: {filters}")

            bookmarks = self.bookmark_service.list_bookmarks(filters)

            return self._create_success_response(
                data={
                    "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
                    "total": len(bookmarks),
                    "filters": filters
                },
                message=f"Retrieved {len(bookmarks)} bookmarks"
            )

        except Exception as e:
            return self._handle_service_error(e, "list_bookmarks")

    def search_bookmarks(
        self,
        query: str,
        document_id: Optional[Union[int, str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search bookmarks by title, notes, or tags.

        MCP Tool: search_bookmarks
        Primary workflow: Bookmark search functionality in GUI

        Args:
            query: Search query text
            document_id: Optional filter by document
            category: Optional filter by category

        Returns:
            MCP response with matching bookmarks
        """
        try:
            # Parameter validation
            if not query or not query.strip():
                raise MCPHandlerError("query is required")

            # Build filters
            filters = {}
            if document_id is not None:
                filters["document_id"] = self._validate_positive_integer(document_id, "document_id")
            if category is not None:
                filters["category"] = category

            # Delegate to service layer
            logger.debug(f"Searching bookmarks: query='{query}', filters={filters}")

            bookmarks = self.bookmark_service.search_bookmarks(query, filters)

            return self._create_success_response(
                data={
                    "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
                    "total": len(bookmarks),
                    "query": query,
                    "filters": filters
                },
                message=f"Found {len(bookmarks)} matching bookmarks"
            )

        except Exception as e:
            return self._handle_service_error(e, "search_bookmarks")

    def update_bookmark(
        self,
        bookmark_id: Union[int, str],
        title: Optional[str] = None,
        category: Optional[str] = None,
        notes: Optional[str] = None,
        color: Optional[str] = None,
        is_favorite: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update bookmark properties.

        MCP Tool: update_bookmark
        Primary workflow: Edit bookmark from GUI

        Args:
            bookmark_id: Bookmark ID
            title: Optional new title
            category: Optional new category
            notes: Optional new notes
            color: Optional new color
            is_favorite: Optional new favorite status

        Returns:
            MCP response with updated bookmark data
        """
        try:
            # Parameter validation
            bookmark_id_val = self._validate_positive_integer(bookmark_id, "bookmark_id")

            # Get existing bookmark
            bookmark = self.bookmark_service.get_bookmark(bookmark_id_val)
            if not bookmark:
                return self._create_error_response(
                    error_message=f"Bookmark {bookmark_id_val} not found",
                    error_type="not_found",
                    error_code="BOOKMARK_NOT_FOUND"
                )

            # Update fields if provided
            if title is not None:
                bookmark.title = title
            if category is not None:
                bookmark.category = category
            if notes is not None:
                bookmark.notes = notes
            if color is not None:
                bookmark.color = color
            if is_favorite is not None:
                bookmark.is_favorite = is_favorite

            # Delegate to service layer
            logger.debug(f"Updating bookmark: bookmark_id={bookmark_id_val}")

            updated_bookmark = self.bookmark_service.update_bookmark(bookmark)

            return self._create_success_response(
                data=updated_bookmark.to_dict(),
                message=f"Updated bookmark: {updated_bookmark.title}"
            )

        except Exception as e:
            return self._handle_service_error(e, "update_bookmark")

    def delete_bookmark(self, bookmark_id: Union[int, str]) -> Dict[str, Any]:
        """
        Delete bookmark by ID.

        MCP Tool: delete_bookmark
        Primary workflow: Remove bookmark from GUI

        Args:
            bookmark_id: Bookmark ID to delete

        Returns:
            MCP response confirming deletion
        """
        try:
            # Parameter validation
            bookmark_id_val = self._validate_positive_integer(bookmark_id, "bookmark_id")

            # Delegate to service layer
            logger.debug(f"Deleting bookmark: bookmark_id={bookmark_id_val}")

            deleted = self.bookmark_service.delete_bookmark(bookmark_id_val)

            if not deleted:
                return self._create_error_response(
                    error_message=f"Bookmark {bookmark_id_val} not found",
                    error_type="not_found",
                    error_code="BOOKMARK_NOT_FOUND"
                )

            return self._create_success_response(
                data={"bookmark_id": bookmark_id_val},
                message=f"Bookmark {bookmark_id_val} deleted successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "delete_bookmark")

    def get_bookmark_categories(self) -> Dict[str, Any]:
        """
        Get all bookmark categories.

        MCP Tool: get_bookmark_categories
        Primary workflow: Populate category dropdown in GUI

        Returns:
            MCP response with category list
        """
        try:
            # Delegate to service layer
            logger.debug("Getting bookmark categories")

            categories = self.bookmark_service.get_categories()

            return self._create_success_response(
                data={
                    "categories": categories,
                    "total": len(categories)
                },
                message=f"Retrieved {len(categories)} bookmark categories"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_bookmark_categories")

    def get_bookmark_statistics(self) -> Dict[str, Any]:
        """
        Get bookmark statistics and analytics.

        MCP Tool: get_bookmark_statistics
        Primary workflow: Analytics dashboard, usage metrics

        Returns:
            MCP response with bookmark statistics
        """
        try:
            # Delegate to service layer
            logger.debug("Getting bookmark statistics")

            stats = self.bookmark_service.get_bookmark_statistics()

            return self._create_success_response(
                data=stats,
                message="Retrieved bookmark statistics"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_bookmark_statistics")

    def export_bookmarks(
        self,
        format: str = "json",
        document_id: Optional[Union[int, str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export bookmarks in specified format.

        MCP Tool: export_bookmarks
        Primary workflow: Backup/export bookmark data

        Args:
            format: Export format ("json" or "csv")
            document_id: Optional filter by document
            category: Optional filter by category

        Returns:
            MCP response with export data
        """
        try:
            # Parameter validation
            if format not in ["json", "csv"]:
                raise MCPHandlerError("format must be 'json' or 'csv'")

            # Build filters
            filters = {}
            if document_id is not None:
                filters["document_id"] = self._validate_positive_integer(document_id, "document_id")
            if category is not None:
                filters["category"] = category

            # Delegate to service layer
            logger.debug(f"Exporting bookmarks: format={format}, filters={filters}")

            export_data = self.bookmark_service.export_bookmarks(format, filters)

            return self._create_success_response(
                data=export_data,
                message=f"Exported bookmarks in {format} format"
            )

        except Exception as e:
            return self._handle_service_error(e, "export_bookmarks")

    # ============================================================================
    # PROGRESS TRACKING TOOLS - Task 14 Phase 3
    # ============================================================================

    def track_reading_progress(
        self,
        document_id: Union[int, str],
        chunk_id: Optional[Union[int, str]] = None,
        page: Optional[Union[int, str]] = None,
        position: Optional[Union[int, str]] = None,
        percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Track reading progress for document or chunk.

        MCP Tool: track_reading_progress
        Primary workflow: Update progress as user reads through content

        Args:
            document_id: Document ID being read
            chunk_id: Optional chunk ID for chunk-level tracking
            page: Optional current page number
            position: Optional current position (character offset)
            percentage: Optional completion percentage (0.0-100.0)

        Returns:
            MCP response with updated progress data
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            c_id = None
            if chunk_id is not None:
                c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            page_num = None
            if page is not None:
                page_num = self._validate_positive_integer(page, "page")

            pos_num = None
            if position is not None:
                pos_num = self._validate_positive_integer(position, "position")

            if percentage is not None:
                if not isinstance(percentage, (int, float)):
                    raise ValueError("percentage must be a number")
                if percentage < 0.0 or percentage > 100.0:
                    raise ValueError("percentage must be between 0.0 and 100.0")

            # Delegate to service layer
            logger.debug(f"Tracking reading progress: document_id={doc_id}, chunk_id={c_id}")

            progress = self.progress_service.track_reading_progress(
                document_id=doc_id,
                chunk_id=c_id,
                page=page_num,
                position=pos_num,
                percentage=percentage
            )

            return self._create_success_response(
                data=progress.to_dict(),
                message="Reading progress updated successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "track_reading_progress")

    def mark_content_completed(
        self,
        document_id: Union[int, str],
        chunk_id: Optional[Union[int, str]] = None,
        completion_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Mark document or chunk as completed.

        MCP Tool: mark_content_completed
        Primary workflow: Mark completion when user finishes reading

        Args:
            document_id: Document ID to mark completed
            chunk_id: Optional chunk ID for chunk-level completion
            completion_notes: Optional completion notes

        Returns:
            MCP response with completion confirmation
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            c_id = None
            if chunk_id is not None:
                c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.info(f"Marking content completed: document_id={doc_id}, chunk_id={c_id}")

            progress = self.progress_service.mark_completed(
                document_id=doc_id,
                chunk_id=c_id,
                completion_notes=completion_notes
            )

            return self._create_success_response(
                data=progress.to_dict(),
                message="Content marked as completed successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "mark_content_completed")

    def get_reading_progress(
        self,
        document_id: Union[int, str],
        chunk_id: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Get current reading progress for document or chunk.

        MCP Tool: get_reading_progress
        Primary workflow: Display progress in GUI, check completion status

        Args:
            document_id: Document ID to get progress for
            chunk_id: Optional chunk ID for chunk-specific progress

        Returns:
            MCP response with current progress data
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            c_id = None
            if chunk_id is not None:
                c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.debug(f"Getting reading progress: document_id={doc_id}, chunk_id={c_id}")

            progress = self.progress_service.get_reading_progress(
                document_id=doc_id,
                chunk_id=c_id
            )

            if not progress:
                return self._create_error_response(
                    error_message=f"No progress found for document {doc_id}" +
                                 (f", chunk {c_id}" if c_id else ""),
                    error_type="not_found",
                    error_code="PROGRESS_NOT_FOUND"
                )

            return self._create_success_response(
                data=progress.to_dict(),
                message="Reading progress retrieved successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_reading_progress")

    def get_document_progress_summary(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for document.

        MCP Tool: get_document_progress_summary
        Primary workflow: Document analytics, progress dashboard

        Args:
            document_id: Document ID to get summary for

        Returns:
            MCP response with comprehensive progress analytics
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting document progress summary: document_id={doc_id}")

            summary = self.progress_service.get_document_progress_summary(doc_id)

            return self._create_success_response(
                data=summary,
                message="Document progress summary retrieved successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_document_progress_summary")

    # ============================================================================
    # STUDY SESSION MANAGEMENT TOOLS - Task 14 Phase 3
    # ============================================================================

    def start_study_session(
        self,
        document_id: Union[int, str],
        chunk_id: Optional[Union[int, str]] = None,
        session_type: str = "reading",
        planned_duration: Optional[Union[int, str]] = None,
        goals: str = "",
        start_page: Optional[Union[int, str]] = None,
        start_position: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Start a new study session.

        MCP Tool: start_study_session
        Primary workflow: Begin focused study session with tracking

        Args:
            document_id: Document ID for session
            chunk_id: Optional chunk ID for chunk-specific session
            session_type: Session type ("reading", "reviewing", "analyzing", "note_taking")
            planned_duration: Optional planned duration in seconds
            goals: Optional session goals description
            start_page: Optional starting page number
            start_position: Optional starting position

        Returns:
            MCP response with created session data
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            c_id = None
            if chunk_id is not None:
                c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Validate session type
            try:
                session_type_enum = SessionType(session_type.upper())
            except ValueError:
                valid_types = [t.value.lower() for t in SessionType]
                raise ValueError(f"Invalid session_type '{session_type}'. Must be one of: {valid_types}")

            duration = None
            if planned_duration is not None:
                duration = self._validate_positive_integer(planned_duration, "planned_duration")

            page_num = None
            if start_page is not None:
                page_num = self._validate_positive_integer(start_page, "start_page")

            pos_num = None
            if start_position is not None:
                pos_num = self._validate_positive_integer(start_position, "start_position")

            # Delegate to service layer
            logger.info(f"Starting study session: document_id={doc_id}, type={session_type}")

            session = self.progress_service.start_study_session(
                document_id=doc_id,
                chunk_id=c_id,
                session_type=session_type_enum,
                planned_duration=duration,
                goals=goals,
                start_page=page_num,
                start_position=pos_num
            )

            return self._create_success_response(
                data=session.to_dict(),
                message=f"Study session started successfully (ID: {session.id})"
            )

        except Exception as e:
            return self._handle_service_error(e, "start_study_session")

    def pause_study_session(
        self,
        session_id: Union[int, str],
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Pause an active study session.

        MCP Tool: pause_study_session
        Primary workflow: Temporarily pause session (interruption, break)

        Args:
            session_id: Session ID to pause
            notes: Optional pause reason/notes

        Returns:
            MCP response with updated session data
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(session_id, "session_id")

            # Delegate to service layer
            logger.debug(f"Pausing study session: session_id={s_id}")

            session = self.progress_service.pause_study_session(
                session_id=s_id,
                notes=notes
            )

            return self._create_success_response(
                data=session.to_dict(),
                message=f"Study session paused (ID: {session.id})"
            )

        except Exception as e:
            return self._handle_service_error(e, "pause_study_session")

    def resume_study_session(self, session_id: Union[int, str]) -> Dict[str, Any]:
        """
        Resume a paused study session.

        MCP Tool: resume_study_session
        Primary workflow: Continue paused session

        Args:
            session_id: Session ID to resume

        Returns:
            MCP response with updated session data
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(session_id, "session_id")

            # Delegate to service layer
            logger.debug(f"Resuming study session: session_id={s_id}")

            session = self.progress_service.resume_study_session(s_id)

            return self._create_success_response(
                data=session.to_dict(),
                message=f"Study session resumed (ID: {session.id})"
            )

        except Exception as e:
            return self._handle_service_error(e, "resume_study_session")

    def end_study_session(
        self,
        session_id: Union[int, str],
        status: str = "completed",
        end_page: Optional[Union[int, str]] = None,
        end_position: Optional[Union[int, str]] = None,
        focus_score: Optional[float] = None,
        productivity_score: Optional[float] = None,
        interruption_count: Optional[Union[int, str]] = None,
        achievements: str = "",
        challenges: str = "",
        notes: str = "",
        words_read: Optional[Union[int, str]] = None,
        pages_read: Optional[Union[int, str]] = None,
        concepts_learned: Optional[Union[int, str]] = None,
        questions_raised: Optional[Union[int, str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        End a study session with completion metrics.

        MCP Tool: end_study_session
        Primary workflow: Complete session with performance tracking

        Args:
            session_id: Session ID to end
            status: Final status ("completed", "cancelled", "interrupted")
            end_page: Final page number
            end_position: Final position
            focus_score: Focus rating (1.0-10.0)
            productivity_score: Productivity rating (1.0-10.0)
            interruption_count: Number of interruptions
            achievements: Session achievements description
            challenges: Challenges encountered description
            notes: Additional session notes
            words_read: Number of words read
            pages_read: Number of pages read
            concepts_learned: Number of concepts learned
            questions_raised: Number of questions raised
            tags: Optional session tags

        Returns:
            MCP response with completed session data
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(session_id, "session_id")

            # Validate status
            try:
                status_enum = SessionStatus(status.upper())
            except ValueError:
                valid_statuses = [s.value.lower() for s in SessionStatus if s != SessionStatus.ACTIVE and s != SessionStatus.PAUSED]
                raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

            # Validate optional numeric parameters
            page_num = None
            if end_page is not None:
                page_num = self._validate_positive_integer(end_page, "end_page")

            pos_num = None
            if end_position is not None:
                pos_num = self._validate_positive_integer(end_position, "end_position")

            # Validate scores (1-10 range)
            if focus_score is not None:
                if not isinstance(focus_score, (int, float)):
                    raise ValueError("focus_score must be a number")
                if focus_score < 1.0 or focus_score > 10.0:
                    raise ValueError("focus_score must be between 1.0 and 10.0")

            if productivity_score is not None:
                if not isinstance(productivity_score, (int, float)):
                    raise ValueError("productivity_score must be a number")
                if productivity_score < 1.0 or productivity_score > 10.0:
                    raise ValueError("productivity_score must be between 1.0 and 10.0")

            # Validate counts
            int_count = None
            if interruption_count is not None:
                int_count = int(interruption_count)
                if int_count < 0:
                    raise ValueError("interruption_count must be non-negative")

            words_num = None
            if words_read is not None:
                words_num = int(words_read)
                if words_num < 0:
                    raise ValueError("words_read must be non-negative")

            pages_num = None
            if pages_read is not None:
                pages_num = int(pages_read)
                if pages_num < 0:
                    raise ValueError("pages_read must be non-negative")

            concepts_num = None
            if concepts_learned is not None:
                concepts_num = int(concepts_learned)
                if concepts_num < 0:
                    raise ValueError("concepts_learned must be non-negative")

            questions_num = None
            if questions_raised is not None:
                questions_num = int(questions_raised)
                if questions_num < 0:
                    raise ValueError("questions_raised must be non-negative")

            # Delegate to service layer
            logger.info(f"Ending study session: session_id={s_id}, status={status}")

            session = self.progress_service.end_study_session(
                session_id=s_id,
                status=status_enum,
                end_page=page_num,
                end_position=pos_num,
                focus_score=focus_score,
                productivity_score=productivity_score,
                interruption_count=int_count,
                achievements=achievements,
                challenges=challenges,
                notes=notes,
                words_read=words_num,
                pages_read=pages_num,
                concepts_learned=concepts_num,
                questions_raised=questions_num,
                tags=tags
            )

            return self._create_success_response(
                data=session.to_dict(),
                message=f"Study session ended with status: {status}"
            )

        except Exception as e:
            return self._handle_service_error(e, "end_study_session")

    def get_active_sessions(self) -> Dict[str, Any]:
        """
        Get all currently active or paused study sessions.

        MCP Tool: get_active_sessions
        Primary workflow: Display active sessions in GUI, session management

        Returns:
            MCP response with list of active sessions
        """
        try:
            # Delegate to service layer
            logger.debug("Getting active study sessions")

            sessions = self.progress_service.get_active_sessions()

            return self._create_success_response(
                data={
                    "sessions": [session.to_dict() for session in sessions],
                    "total": len(sessions)
                },
                message=f"Retrieved {len(sessions)} active sessions"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_active_sessions")

    def get_session_history(
        self,
        document_id: Optional[Union[int, str]] = None,
        days: Union[int, str] = 30,
        limit: Union[int, str] = 50
    ) -> Dict[str, Any]:
        """
        Get study session history with optional filtering.

        MCP Tool: get_session_history
        Primary workflow: Review past sessions, analytics

        Args:
            document_id: Optional filter by document
            days: Number of days to look back (default: 30)
            limit: Maximum sessions to return (default: 50)

        Returns:
            MCP response with session history
        """
        try:
            # Parameter validation
            doc_id = None
            if document_id is not None:
                doc_id = self._validate_positive_integer(document_id, "document_id")

            days_num = int(days)
            if days_num < 0:
                raise ValueError("days must be non-negative")

            limit_num = int(limit)
            if limit_num <= 0 or limit_num > 200:
                raise ValueError("limit must be between 1 and 200")

            # Delegate to service layer
            logger.debug(f"Getting session history: document_id={doc_id}, days={days_num}")

            sessions = self.progress_service.get_session_history(
                document_id=doc_id,
                days=days_num,
                limit=limit_num
            )

            return self._create_success_response(
                data={
                    "sessions": [session.to_dict() for session in sessions],
                    "total": len(sessions),
                    "filters": {
                        "document_id": doc_id,
                        "days": days_num,
                        "limit": limit_num
                    }
                },
                message=f"Retrieved {len(sessions)} session history entries"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_session_history")

    # ============================================================================
    # ANALYTICS & REPORTING TOOLS - Task 14 Phase 3
    # ============================================================================

    def get_progress_analytics(self, days: Union[int, str] = 30) -> Dict[str, Any]:
        """
        Get comprehensive progress and session analytics.

        MCP Tool: get_progress_analytics
        Primary workflow: Analytics dashboard, performance insights

        Args:
            days: Number of days for analytics period (default: 30)

        Returns:
            MCP response with comprehensive analytics data
        """
        try:
            # Parameter validation
            days_num = int(days)
            if days_num <= 0:
                raise ValueError("days must be positive")

            # Delegate to service layer
            logger.debug(f"Getting progress analytics for {days_num} days")

            analytics = self.progress_service.get_comprehensive_analytics(days_num)

            return self._create_success_response(
                data=analytics,
                message=f"Retrieved analytics for {days_num} day period"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_progress_analytics")

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """
        Get daily summary of reading progress and sessions.

        MCP Tool: get_daily_summary
        Primary workflow: Daily progress review, habit tracking

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            MCP response with daily activity summary
        """
        try:
            # Parameter validation
            if not isinstance(date, str):
                raise ValueError("date must be a string in YYYY-MM-DD format")

            # Basic date format validation
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                raise ValueError("date must be in YYYY-MM-DD format")

            # Delegate to service layer
            logger.debug(f"Getting daily summary for {date}")

            summary = self.progress_service.get_daily_summary(date)

            return self._create_success_response(
                data=summary,
                message=f"Retrieved daily summary for {date}"
            )

        except Exception as e:
            return self._handle_service_error(e, "get_daily_summary")

    # ============================================================================
    # FILE EXPORT TOOLS - Markdown File Creation
    # ============================================================================

    def create_markdown_file(
        self,
        content: str,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a markdown file with the provided content.

        MCP Tool: create_markdown_file
        Primary workflow: Export summaries, prompts, or analysis to .md files

        Args:
            content: Markdown content to write to file
            file_path: Absolute path for output file (must end with .md)
            title: Optional title to add as H1 header
            metadata: Optional YAML frontmatter metadata
            overwrite: Whether to overwrite existing file (default: False)

        Returns:
            MCP response with file creation confirmation

        Example Response:
        {
            "success": true,
            "data": {
                "file_path": "/path/to/output.md",
                "file_size": 1245,
                "lines_written": 45,
                "title": "Document Summary",
                "created": true
            },
            "message": "Markdown file created successfully"
        }
        """
        try:
            import os
            from datetime import datetime

            # Parameter validation
            if not content or not isinstance(content, str):
                raise ValueError("content is required and must be a non-empty string")

            content = content.strip()
            if not content:
                raise ValueError("content cannot be empty or only whitespace")

            if not file_path or not isinstance(file_path, str):
                raise ValueError("file_path is required and must be a string")

            # Validate file extension
            if not file_path.lower().endswith('.md'):
                raise ValueError("file_path must end with .md extension")

            # Convert to absolute path
            abs_path = os.path.abspath(file_path)

            # Check if file exists and handle overwrite
            if os.path.exists(abs_path) and not overwrite:
                return self._create_error_response(
                    error_message=f"File already exists: {abs_path}. Use overwrite=true to replace.",
                    error_type="validation",
                    error_code="FILE_EXISTS",
                    details={"file_path": abs_path, "overwrite": overwrite}
                )

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Build final content
            final_content = ""

            # Add YAML frontmatter if metadata provided
            if metadata:
                final_content += "---\n"
                for key, value in metadata.items():
                    if isinstance(value, str):
                        final_content += f"{key}: \"{value}\"\n"
                    elif isinstance(value, list):
                        final_content += f"{key}: {value}\n"
                    else:
                        final_content += f"{key}: {value}\n"
                final_content += f"created: \"{datetime.now().isoformat()}\"\n"
                final_content += "---\n\n"

            # Add title as H1 if provided
            if title:
                final_content += f"# {title}\n\n"

            # Add main content
            final_content += content

            # Write file
            logger.info(f"Creating markdown file: {abs_path}")
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            # Get file stats
            file_size = os.path.getsize(abs_path)
            line_count = len(final_content.split('\n'))

            # Format response
            response_data = {
                "file_path": abs_path,
                "file_size": file_size,
                "lines_written": line_count,
                "title": title,
                "created": True,
                "metadata_included": bool(metadata),
                "content_preview": final_content[:200] + "..." if len(final_content) > 200 else final_content
            }

            logger.info(f"Markdown file created successfully: {abs_path} ({file_size} bytes)")
            return self._create_success_response(
                data=response_data,
                message=f"Markdown file created successfully: {os.path.basename(abs_path)}"
            )

        except Exception as e:
            return self._handle_service_error(e, "create_markdown_file")

    def export_summary_to_file(
        self,
        summary_id: Union[int, str],
        file_path: str,
        include_metadata: bool = True,
        include_source_info: bool = True,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Export existing summary to markdown file.

        MCP Tool: export_summary_to_file
        Primary workflow: Save summary as standalone .md file

        Args:
            summary_id: Summary ID to export
            file_path: Output file path (must end with .md)
            include_metadata: Include summary metadata in frontmatter
            include_source_info: Include source document/chunk information
            overwrite: Whether to overwrite existing file

        Returns:
            MCP response with export confirmation
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(summary_id, "summary_id")

            # Get summary from service
            logger.debug(f"Getting summary for export: {s_id}")
            summary_result = self.summary_service.get_summary(s_id)
            
            if not summary_result:
                return self._create_error_response(
                    error_message=f"Summary {s_id} not found",
                    error_type="not_found",
                    error_code="SUMMARY_NOT_FOUND"
                )

            # Build metadata
            metadata = None
            if include_metadata:
                # Start with custom metadata from summary
                custom_metadata = summary_result.get("metadata", {})
                metadata = custom_metadata.copy() if custom_metadata else {}
                
                # Add system metadata
                system_metadata = {
                    "summary_id": s_id,
                    "summary_type": summary_result["summary_type"],
                    "model_name": summary_result.get("model_name", "unknown"),
                    "word_count": summary_result.get("word_count", 0),
                    "generation_date": summary_result.get("generation_date", ""),
                    "exported_by": "Study Buddy MCP Server"
                }
                metadata.update(system_metadata)
                
                # Add source info if requested
                if include_source_info:
                    if summary_result.get("document_id"):
                        # Get document info
                        doc = self.document_service.get_document(summary_result["document_id"])
                        if doc:
                            metadata["source_document"] = doc.title
                            metadata["source_document_id"] = doc.id
                    
                    if summary_result.get("chunk_id"):
                        metadata["source_chunk_id"] = summary_result["chunk_id"]

            # Determine title
            title = f"{summary_result['summary_type'].title()} Summary"
            if summary_result.get("target_title"):
                title += f" - {summary_result['target_title']}"

            # Export using create_markdown_file
            return self.create_markdown_file(
                content=summary_result["summary_content"],
                file_path=file_path,
                title=title,
                metadata=metadata,
                overwrite=overwrite
            )

        except Exception as e:
            return self._handle_service_error(e, "export_summary_to_file")

    def export_document_structure_to_file(
        self,
        document_id: Union[int, str],
        file_path: str,
        include_word_counts: bool = True,
        include_metadata: bool = True,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Export document structure (chunk list) to markdown file.

        MCP Tool: export_document_structure_to_file
        Primary workflow: Create document outline/table of contents

        Args:
            document_id: Document ID to export structure for
            file_path: Output file path (must end with .md)
            include_word_counts: Include word counts for each chunk
            include_metadata: Include document metadata
            overwrite: Whether to overwrite existing file

        Returns:
            MCP response with export confirmation
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Get document structure
            logger.debug(f"Getting document structure for export: {doc_id}")
            structure = self.chunking_service.get_document_structure(doc_id)

            if not structure:
                return self._create_error_response(
                    error_message=f"Document {doc_id} not found or not indexed",
                    error_type="not_found",
                    error_code="DOCUMENT_NOT_INDEXED"
                )

            # Build content
            content = f"# Document Structure: {structure['document_title']}\n\n"
            
            if structure.get('indexed'):
                content += f"**Total Chunks**: {structure.get('total_chunks', 0)}\n\n"
                
                if structure.get('chunks'):
                    content += "## Table of Contents\n\n"
                    
                    for chunk in structure['chunks']:
                        chunk_title = chunk.get('title', f"Chunk {chunk.get('chunk_index', 'Unknown')}")
                        content += f"### {chunk.get('chunk_index', 0) + 1}. {chunk_title}\n\n"
                        
                        content += f"- **Type**: {chunk.get('chunk_type', 'unknown')}\n"
                        content += f"- **Chunk ID**: {chunk.get('chunk_id')}\n"
                        
                        if include_word_counts and chunk.get('word_count'):
                            content += f"- **Word Count**: {chunk['word_count']:,}\n"
                        
                        content += "\n"
            else:
                content += "*Document has not been indexed yet.*\n\n"

            # Build metadata
            metadata = None
            if include_metadata:
                metadata = {
                    "document_id": doc_id,
                    "document_title": structure['document_title'],
                    "indexed": structure.get('indexed', False),
                    "total_chunks": structure.get('total_chunks', 0),
                    "export_type": "document_structure",
                    "exported_by": "Study Buddy MCP Server"
                }

            # Export using create_markdown_file
            return self.create_markdown_file(
                content=content,
                file_path=file_path,
                title=f"Structure: {structure['document_title']}",
                metadata=metadata,
                overwrite=overwrite
            )

        except Exception as e:
            return self._handle_service_error(e, "export_document_structure_to_file")
