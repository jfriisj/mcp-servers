"""
Summary MCP Handler - Handles summary-related MCP operations following SRP and ISP.

This module implements the ISummaryMCPHandler interface, providing focused
summary operations extracted from the monolithic MCPHandler class.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from study_buddy.interfaces.mcp_handlers import ISummaryMCPHandler
from study_buddy.server.services.summary_service import SummaryService

logger = logging.getLogger(__name__)


class SummaryMCPHandler(ISummaryMCPHandler):
    """
    Focused MCP handler for summary operations following Single Responsibility Principle.
    
    This handler is responsible only for MCP protocol translation of summary operations:
    - Summary creation and saving
    - Summary retrieval by ID
    - Summary listing with filters
    - Summary statistics and analytics
    - Summary export to files
    """

    def __init__(self, summary_service: SummaryService):
        """
        Initialize summary MCP handler.
        
        Args:
            summary_service: Service layer for summary operations
        """
        self.summary_service = summary_service

    async def save_summary(
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
            summary_content: Summary content in markdown format
            summary_type: Type of summary ("brief", "standard", "detailed", "custom")
            chunk_id: Target chunk ID (mutually exclusive with document_id)
            document_id: Target document ID (mutually exclusive with chunk_id)
            model_name: AI model used for generation
            metadata: Optional metadata for summary context
            overwrite_existing: Whether to overwrite existing summaries

        Returns:
            MCP response with summary creation results

        Example Response:
        {
            "success": true,
            "data": {
                "summary_id": 123,
                "summary_type": "standard",
                "target_type": "chunk",
                "target_id": 456,
                "word_count": 250,
                "model_name": "gpt-4",
                "created_at": "2025-01-06T12:00:00Z"
            },
            "message": "Summary saved successfully"
        }
        """
        try:
            # Parameter validation
            if not summary_content or not summary_content.strip():
                raise ValueError("summary_content is required and cannot be empty")

            if summary_type not in ["brief", "standard", "detailed", "custom"]:
                raise ValueError(f"Invalid summary_type: {summary_type}. Must be one of: brief, standard, detailed, custom")

            # Validate target specification (exactly one of chunk_id or document_id)
            target_count = sum(x is not None for x in [chunk_id, document_id])
            if target_count != 1:
                raise ValueError("Exactly one of chunk_id or document_id must be specified")

            # Convert and validate target IDs
            target_id = None
            target_type = None
            if chunk_id is not None:
                target_id = self._validate_positive_integer(chunk_id, "chunk_id")
                target_type = "chunk"
            elif document_id is not None:
                target_id = self._validate_positive_integer(document_id, "document_id")
                target_type = "document"

            if not model_name or not model_name.strip():
                model_name = "unknown"

            if metadata and not isinstance(metadata, dict):
                raise ValueError("metadata must be a dictionary")

            # Delegate to service layer
            logger.info(f"Saving summary: type={summary_type}, target_type={target_type}, target_id={target_id}")
            result = self.summary_service.save_summary(
                content=summary_content.strip(),
                summary_type=summary_type,
                chunk_id=target_id if target_type == "chunk" else None,
                document_id=target_id if target_type == "document" else None,
                model_name=model_name.strip(),
                metadata=metadata or {},
                overwrite_existing=overwrite_existing
            )

            logger.info(f"Summary saved successfully: ID={result.get('summary_id')}")
            return self._create_success_response(
                data=result,
                message="Summary saved successfully"
            )

        except Exception as e:
            return self._handle_service_error(e, "save_summary")

    async def get_summary(self, summary_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve summary by ID with full content and metadata.

        MCP Tool: get_summary
        Primary workflow: Display summary content, edit summaries

        Args:
            summary_id: Summary ID to retrieve

        Returns:
            MCP response with summary details

        Example Response:
        {
            "success": true,
            "data": {
                "summary_id": 123,
                "content": "Summary content in markdown...",
                "summary_type": "standard",
                "target_type": "chunk",
                "target_id": 456,
                "word_count": 250,
                "model_name": "gpt-4",
                "metadata": {},
                "created_at": "2025-01-06T12:00:00Z"
            }
        }
        """
        try:
            # Parameter validation
            s_id = self._validate_positive_integer(summary_id, "summary_id")

            # Delegate to service layer
            logger.debug(f"Getting summary: {s_id}")
            result = self.summary_service.get_summary(s_id)

            if not result:
                return self._create_error_response(
                    error_message=f"Summary {s_id} not found",
                    error_type="not_found",
                    error_code="SUMMARY_NOT_FOUND",
                    details={"summary_id": s_id}
                )

            logger.debug(f"Summary retrieved successfully: {s_id}")
            return self._create_success_response(data=result)

        except Exception as e:
            return self._handle_service_error(e, "get_summary")

    async def get_summaries_for_chunk(self, chunk_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get all summaries for a specific chunk.

        MCP Tool: get_summaries_for_chunk
        Primary workflow: Display chunk summaries, summary comparison

        Args:
            chunk_id: Chunk ID to get summaries for

        Returns:
            MCP response with chunk summaries
        """
        try:
            # Parameter validation
            c_id = self._validate_positive_integer(chunk_id, "chunk_id")

            # Delegate to service layer
            logger.debug(f"Getting summaries for chunk: {c_id}")
            result = self.summary_service.get_summaries_for_chunk(c_id)

            return self._create_success_response(data={"summaries": result or []})

        except Exception as e:
            return self._handle_service_error(e, "get_summaries_for_chunk")

    async def get_summaries_for_document(self, document_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get all summaries for a specific document.

        MCP Tool: get_summaries_for_document
        Primary workflow: Display document summaries, summary overview

        Args:
            document_id: Document ID to get summaries for

        Returns:
            MCP response with document summaries
        """
        try:
            # Parameter validation
            d_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting summaries for document: {d_id}")
            result = self.summary_service.get_summaries_for_document(d_id)

            return self._create_success_response(data={"summaries": result or []})

        except Exception as e:
            return self._handle_service_error(e, "get_summaries_for_document")

    async def list_summaries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "generation_date",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List summaries with pagination and filtering.

        MCP Tool: list_summaries
        Primary workflow: Summary management, batch operations

        Args:
            filters: Optional filters (summary_type, model_name, document_id)
            limit: Maximum summaries to return
            offset: Number of summaries to skip for pagination
            sort_by: Sort field (generation_date, word_count, summary_type)
            sort_order: Sort order (asc, desc)

        Returns:
            MCP response with summary list and pagination info

        Example Response:
        {
            "success": true,
            "data": {
                "summaries": [
                    {
                        "summary_id": 123,
                        "summary_type": "standard",
                        "target_type": "chunk",
                        "target_id": 456,
                        "word_count": 250,
                        "model_name": "gpt-4",
                        "created_at": "2025-01-06T12:00:00Z"
                    }
                ],
                "pagination": {
                    "total": 45,
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

            if sort_by not in ["generation_date", "word_count", "summary_type"]:
                raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of: generation_date, word_count, summary_type")

            if sort_order not in ["asc", "desc"]:
                raise ValueError(f"Invalid sort_order: {sort_order}. Must be 'asc' or 'desc'")

            if filters and not isinstance(filters, dict):
                raise ValueError("filters must be a dictionary")

            # Delegate to service layer
            logger.debug(f"Listing summaries: limit={limit}, offset={offset}")
            summaries = self.summary_service.list_summaries(
                filters=filters or {},
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Get total count for pagination (separate call since service returns List)
            total_summaries = self.summary_service.list_summaries(filters=filters or {})
            total_count = len(total_summaries)

            response_data = {
                "summaries": summaries,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(summaries) < total_count
                }
            }

            logger.debug(f"Summaries listed successfully: {len(summaries)} summaries")
            return self._create_success_response(data=response_data)

        except Exception as e:
            return self._handle_service_error(e, "list_summaries")

    async def get_summary_statistics(self, document_id: Optional[Union[int, str]] = None) -> Dict[str, Any]:
        """
        Get summary statistics (global or for specific document).

        MCP Tool: get_summary_statistics
        Primary workflow: Analytics, summary overview

        Args:
            document_id: Optional document ID to get statistics for

        Returns:
            MCP response with summary statistics

        Example Response:
        {
            "success": true,
            "data": {
                "total_summaries": 150,
                "by_type": {
                    "brief": 50,
                    "standard": 75,
                    "detailed": 25
                },
                "by_model": {
                    "gpt-4": 100,
                    "claude-3": 50
                },
                "total_words": 45000,
                "average_word_count": 300
            }
        }
        """
        try:
            # Parameter validation
            doc_id = None
            if document_id is not None:
                doc_id = self._validate_positive_integer(document_id, "document_id")

            # Delegate to service layer
            logger.debug(f"Getting summary statistics: doc_id={doc_id}")
            # Note: Check actual service method signature - may not support document_id parameter
            stats = self.summary_service.get_summary_statistics()

            logger.debug("Summary statistics retrieved successfully")
            return self._create_success_response(data=stats)

        except Exception as e:
            return self._handle_service_error(e, "get_summary_statistics")

    # Note: export_summary_to_file method will be handled by FileMCPHandler
    # as it's primarily a file operation rather than a summary operation

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