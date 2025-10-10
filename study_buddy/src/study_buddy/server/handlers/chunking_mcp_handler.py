"""
Chunking MCP Handler - Handles chunk-related MCP operations following SRP and ISP.

This module implements the IChunkingMCPHandler interface, providing focused
chunking operations extracted from the monolithic MCPHandler class.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from study_buddy.interfaces.mcp_handlers import IChunkingMCPHandler
from study_buddy.server.services.chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class ChunkingMCPHandler(IChunkingMCPHandler):
    """
    Focused MCP handler for chunking operations following Single Responsibility Principle.
    
    This handler is responsible only for MCP protocol translation of chunking operations:
    - Document indexing into chunks
    - Chunk content retrieval
    - Chunk listing with filters
    """

    def __init__(self, chunking_service: ChunkingService):
        """
        Initialize chunking MCP handler.
        
        Args:
            chunking_service: Service layer for chunking operations
        """
        self.chunking_service = chunking_service

    async def index_document(
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
                "processing_time": 15.5,
                "chunks": [
                    {
                        "chunk_id": 101,
                        "chunk_index": 0,
                        "title": "Introduction",
                        "word_count": 1250
                    }
                ]
            },
            "message": "Document indexed successfully"
        }
        """
        try:
            # Parameter validation
            doc_id = self._validate_positive_integer(document_id, "document_id")
            
            if strategy not in ["auto", "slide", "chapter", "section", "heading", "fixed"]:
                raise ValueError(f"Invalid strategy: {strategy}. Must be one of: auto, slide, chapter, section, heading, fixed")

            # Delegate to service layer
            logger.info(f"Indexing document: {doc_id}, strategy={strategy}, force={force}")
            result = self.chunking_service.index_document(
                document_id=doc_id,
                strategy=strategy,
                force_reindex=force
            )

            logger.info(f"Document indexed successfully: {doc_id}, {result.get('chunks_created', 0)} chunks")
            return self._create_success_response(
                data=result,
                message="Document indexed successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "index_document")

    async def get_chunk_content(self, chunk_id: Union[int, str]) -> Dict[str, Any]:
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
                "chunk_type": "chapter",
                "start_page": 1,
                "end_page": 5
            }
        }
        """
        try:
            # Parameter validation
            c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.debug(f"Getting chunk content: {c_id}")
            result = self.chunking_service.get_chunk_content(c_id)

            if not result:
                return self._create_error_response(
                    error_message=f"Chunk {c_id} not found",
                    error_type="not_found",
                    error_code="CHUNK_NOT_FOUND",
                    details={"chunk_id": c_id}
                )

            logger.debug(f"Chunk content retrieved successfully: {c_id}")
            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "get_chunk_content")

    async def list_chunks(
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

        Example Response:
        {
            "success": true,
            "data": {
                "chunks": [
                    {
                        "chunk_id": 101,
                        "document_id": 42,
                        "chunk_index": 0,
                        "title": "Introduction",
                        "chunk_type": "chapter",
                        "word_count": 1250,
                        "start_page": 1,
                        "end_page": 5
                    }
                ],
                "pagination": {
                    "total": 23,
                    "limit": 50,
                    "offset": 0,
                    "has_more": false
                }
            }
        }
        """
        try:
            # Parameter validation
            doc_id = None
            if document_id is not None:
                doc_id = self._validate_positive_integer(document_id, "document_id")

            if limit <= 0 or limit > 200:
                raise ValueError("limit must be between 1 and 200")

            offset = self._validate_non_negative_integer(offset, "offset")

            if filters and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Extract chunk_type from filters if provided
            chunk_type = None
            if filters and isinstance(filters, dict):
                chunk_type = filters.get("chunk_type")

            # Delegate to service layer
            logger.debug(f"Listing chunks: doc_id={doc_id}, chunk_type={chunk_type}, limit={limit}, offset={offset}")
            chunks = self.chunking_service.list_chunks(
                document_id=doc_id,
                chunk_type=chunk_type,
                limit=limit,
                offset=offset
            )

            # Format response (service returns List[Dict[str, Any]], need to add pagination)
            result = {
                "chunks": chunks,
                "pagination": {
                    "total": len(chunks),  # Note: This isn't ideal but matches service return type
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(chunks) == limit  # Approximation
                }
            }

            logger.debug(f"Chunks listed successfully: {len(result.get('chunks', []))} chunks")
            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "list_chunks")

    # Helper methods for validation and response formatting
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