"""
Document MCP Handler - Handles document-related MCP operations following SRP and ISP.

This module implements the IDocumentMCPHandler interface, providing focused
document operations extracted from the monolithic MCPHandler class.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from study_buddy.interfaces.mcp_handlers import IDocumentMCPHandler
from study_buddy.server.services.document_service import DocumentService
from study_buddy.server.services.chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class DocumentMCPHandler(IDocumentMCPHandler):
    """
    Focused MCP handler for document operations following Single Responsibility Principle.
    
    This handler is responsible only for MCP protocol translation of document operations:
    - Document upload and creation
    - Document retrieval and metadata
    - Document listing with filters
    - Document deletion
    - Document search operations
    - Document structure retrieval
    """

    def __init__(self, document_service: DocumentService, chunking_service: ChunkingService):
        """
        Initialize document MCP handler.
        
        Args:
            document_service: Service layer for document operations
            chunking_service: Service layer for document structure operations
        """
        self.document_service = document_service
        self.chunking_service = chunking_service

    async def upload_document(
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

    async def get_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
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
                "upload_date": document.upload_date.isoformat() if document.upload_date else None
            }

            logger.debug(f"Document retrieved successfully: {doc_id}")
            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "get_document")

    async def list_documents(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List documents with pagination and filtering.

        MCP Tool: list_documents
        Primary workflow: GUI document browser, batch operations

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip (for pagination)
            filters: Optional filters (file_type, tags, indexed, etc.)

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
                        "total_pages": 450,
                        "indexed": true,
                        "tags": ["angular", "web-development"]
                    }
                ],
                "pagination": {
                    "total": 150,
                    "limit": 20,
                    "offset": 0,
                    "has_more": true
                }
            }
        }
        """
        try:
            # Parameter validation
            limit = self._validate_positive_integer(limit, "limit", max_value=100)
            offset = self._validate_non_negative_integer(offset, "offset")

            if filters and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Listing documents: limit={limit}, offset={offset}")
            documents = self.document_service.list_documents(
                limit=limit,
                offset=offset,
                filters=filters or {}
            )

            # Format response
            documents_data = []
            for doc in documents:
                doc_data = {
                    "document_id": doc.id,
                    "title": doc.title,
                    "file_type": doc.file_type,
                    "total_pages": doc.total_pages,
                    "total_words": doc.total_words,
                    "indexed": doc.indexed,
                    "summarized": doc.summarized,
                    "tags": doc.tags,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
                }
                documents_data.append(doc_data)

            # Get total count for pagination (separate call since list_documents returns List[Document])
            total_documents = self.document_service.list_documents(filters=filters or {})
            total_count = len(total_documents)

            response_data = {
                "documents": documents_data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(documents_data) < total_count
                }
            }

            logger.debug(f"Documents listed successfully: {len(documents_data)} documents")
            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "list_documents")

    async def delete_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Delete document and all associated data.

        MCP Tool: delete_document
        Primary workflow: User cleanup, document management

        Args:
            document_id: Document ID to delete

        Returns:
            MCP response confirming deletion

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "deleted_chunks": 23,
                "deleted_summaries": 5,
                "deleted_bookmarks": 12
            },
            "message": "Document deleted successfully"
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.info(f"Deleting document: {doc_id}")
            deletion_result = self.document_service.delete_document(doc_id)

            if not deletion_result:
                return self._create_error_response(
                    error_message=f"Document {doc_id} not found",
                    error_type="not_found",
                    error_code="DOCUMENT_NOT_FOUND",
                    details={"document_id": doc_id}
                )

            # Format response (deletion_result is bool, not dict)
            response_data = {
                "document_id": doc_id,
                "deleted": True
            }

            logger.info(f"Document deleted successfully: {doc_id}")
            return self._create_success_response(
                data=response_data,
                message="Document deleted successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "delete_document")

    async def search_documents(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Full-text search across documents and chunks.

        MCP Tool: search_documents
        Primary workflow: AI research, content discovery

        Args:
            query: Search query string
            limit: Maximum number of results to return
            filters: Optional search filters

        Returns:
            MCP response with search results

        Example Response:
        {
            "success": true,
            "data": {
                "results": [
                    {
                        "document_id": 42,
                        "title": "Angular Projects",
                        "excerpt": "...matching text...",
                        "relevance_score": 0.95,
                        "match_type": "content"
                    }
                ],
                "query": "angular components",
                "total_results": 15
            }
        }
        """
        try:
            # Parameter validation
            if not query or not query.strip():
                raise ValueError("query is required and cannot be empty")

            limit = self._validate_positive_integer(limit, "limit", max_value=100)

            if filters and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Searching documents: query='{query}', limit={limit}")
            search_results = self.document_service.search_documents(
                query=query.strip(),
                limit=limit,
                filters=filters or {}
            )

            # Format response (search_results is List[Document])
            results_data = []
            for doc in search_results:
                result_data = {
                    "document_id": doc.id,
                    "title": doc.title,
                    "excerpt": f"Document: {doc.title}",  # Simple excerpt since service returns Document objects
                    "relevance_score": 1.0,  # Default since service doesn't return scores
                    "match_type": "title"
                }
                results_data.append(result_data)

            response_data = {
                "results": results_data,
                "query": query.strip(),
                "total_results": len(search_results)
            }

            logger.debug(f"Document search completed: {len(results_data)} results")
            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "search_documents")

    async def index_document(
        self,
        document_id: Union[int, str],
        strategy: str = "auto",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Index document into chunks for search and analysis.

        MCP Tool: index_document
        Primary workflow: Document processing preparation

        Args:
            document_id: Document ID to index
            strategy: Chunking strategy to use (auto, chapter, section, etc.)
            force: Force re-indexing if already indexed

        Returns:
            MCP response with indexing results

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "strategy": "chapter",
                "chunks_created": 23,
                "total_words": 125000,
                "processing_time": 15.5
            },
            "message": "Document indexed successfully"
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")
            
            if strategy not in ["auto", "chapter", "section", "heading", "slide", "fixed"]:
                raise ValueError(f"Invalid strategy: {strategy}")

            # Delegate to service layer
            logger.info(f"Indexing document: {doc_id}, strategy={strategy}, force={force}")
            result = self.chunking_service.index_document(
                document_id=doc_id,
                strategy=strategy,
                force_reindex=force
            )

            logger.info(f"Document indexed successfully: {doc_id}")
            return self._create_success_response(
                data=result,
                message="Document indexed successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "index_document")

    async def get_document_structure(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get document structure (list of chunks/chapters).

        MCP Tool: get_document_structure
        Primary workflow: Navigation, content overview

        Args:
            document_id: Document ID to get structure for

        Returns:
            MCP response with document structure

        Example Response:
        {
            "success": true,
            "data": {
                "document_id": 42,
                "chunks": [
                    {
                        "chunk_id": 101,
                        "title": "Introduction",
                        "chunk_type": "chapter",
                        "position": 1,
                        "word_count": 1250
                    }
                ],
                "total_chunks": 23
            }
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer (structure is handled by chunking service)
            logger.debug(f"Getting document structure: {doc_id}")
            structure = self.chunking_service.get_document_structure(doc_id)

            if not structure:
                return self._create_error_response(
                    error_message=f"Document {doc_id} not found or not indexed",
                    error_type="not_found",
                    error_code="DOCUMENT_NOT_FOUND",
                    details={"document_id": doc_id}
                )

            # Format response (structure is already formatted as Dict[str, Any])
            response_data = structure

            logger.debug(f"Document structure retrieved: {doc_id}, {structure.get('total_chunks', 0)} chunks")
            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "get_document_structure")

    # Helper methods for validation and response formatting
    def _validate_file_path(self, file_path: str) -> str:
        """Validate and normalize file path."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path is required and must be a non-empty string")
        
        file_path = file_path.strip()
        if not file_path:
            raise ValueError("file_path cannot be empty after stripping")
        
        return file_path

    def _validate_positive_integer(self, value: Union[int, str], param_name: str, max_value: Optional[int] = None) -> int:
        """Validate positive integer parameter."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be a valid integer")
        
        if int_value <= 0:
            raise ValueError(f"{param_name} must be positive")
        
        if max_value and int_value > max_value:
            raise ValueError(f"{param_name} cannot exceed {max_value}")
        
        return int_value

    def _validate_non_negative_integer(self, value: Union[int, str], param_name: str) -> int:
        """Validate non-negative integer parameter."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be a valid integer")
        
        if int_value < 0:
            raise ValueError(f"{param_name} cannot be negative")
        
        return int_value

    def _create_success_response(self, data: Any = None, message: str = "Operation completed successfully") -> Dict[str, Any]:
        """Create standardized success response."""
        response = {
            "success": True,
            "message": message
        }
        
        if data is not None:
            response["data"] = data
        
        return response

    def _create_error_response(
        self,
        error_message: str,
        error_type: str = "error",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        response = {
            "success": False,
            "error": {
                "message": error_message,
                "type": error_type
            }
        }
        
        if error_code:
            response["error"]["code"] = error_code
        
        if details:
            response["error"]["details"] = details
        
        return response

    def _handle_service_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Handle service layer errors with appropriate logging and response."""
        logger.error(f"Error in {operation}: {str(error)}", exc_info=True)
        
        return self._create_error_response(
            error_message=f"Failed to {operation.replace('_', ' ')}: {str(error)}",
            error_type="service_error",
            error_code="SERVICE_ERROR",
            details={"operation": operation}
        )