"""
MCP Tool Schema Definitions for Study Buddy GUI Integration Layer.

This module provides comprehensive Pydantic schema definitions for all MCP tools
used by Study Buddy. It ensures type safety, request/response validation, and
clear error handling for all MCP operations.

Architecture: Clean Architecture Layer 4 (Infrastructure)
SOLID Compliance: Full compliance with all SOLID principles
Purpose: Type-safe, validated interfaces for AsyncMCPClient operations
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypeVar,
)

from pydantic import BaseModel, Field, field_validator, model_validator

# Type aliases for cleaner code and Pydantic v2 compatibility
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]
LimitedStr = Annotated[str, Field(min_length=1, max_length=500)]
ShortStr = Annotated[str, Field(min_length=1, max_length=100)]
LimitedResults = Annotated[int, Field(ge=1, le=1000)]
SmallResults = Annotated[int, Field(ge=1, le=100)]
SearchQuery = Annotated[str, Field(min_length=1, max_length=500)]
SummaryContent = Annotated[str, Field(min_length=10, max_length=5000)]


def get_debug_logger() -> logging.Logger:
    """Get debug logger for schema validation."""
    logger = logging.getLogger("study_buddy.integration.schemas")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


# Type variables for generic responses
T = TypeVar("T")


# ============================================================================
# BASE CLASSES AND COMMON TYPES
# ============================================================================


class BaseSchema(BaseModel):
    """
    Base schema class with common configuration.

    Provides consistent configuration and helper methods for all schemas.
    """

    class Config:
        # Enable assignment validation
        validate_assignment = True
        # Use enum values instead of names
        use_enum_values = True
        # Allow extra fields for flexibility
        extra = "allow"
        # Enable JSON encoders
        json_encoders = {datetime: lambda v: v.isoformat(), Path: lambda v: str(v)}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return json.loads(self.json())

    def to_json(self, **kwargs) -> str:
        """Convert to JSON string."""
        return self.json(**kwargs)


class BaseRequest(BaseSchema):
    """
    Base class for all MCP tool request schemas.

    Provides common fields and validation for tool requests.
    """

    # Optional request metadata
    request_id: Optional[str] = Field(
        None, description="Optional request identifier for tracking"
    )
    timeout: Optional[float] = Field(
        None, ge=0.1, le=300.0, description="Optional timeout in seconds (0.1 to 300)"
    )


class BaseResponse(BaseSchema):
    """
    Base class for all MCP tool response schemas.

    Provides common response structure with success indication.
    """

    success: bool = Field(..., description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Optional human-readable message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class ErrorDetail(BaseSchema):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional error context"
    )


class ValidationError(BaseResponse):
    """Schema validation error response."""

    success: Literal[False] = False
    error_type: Literal["validation"] = "validation"
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")


class OperationError(BaseResponse):
    """General operation error response."""

    success: Literal[False] = False
    error_type: str = Field(..., description="Type of error")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    MARKDOWN = "markdown"
    TXT = "txt"


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""

    AUTO = "auto"
    CHAPTER = "chapter"
    SECTION = "section"
    HEADING = "heading"
    SLIDE = "slide"
    FIXED_LENGTH = "fixed_length"


class SummaryType(str, Enum):
    """Summary types and styles."""

    BRIEF = "brief"  # 100-150 words
    STANDARD = "standard"  # 250-350 words
    DETAILED = "detailed"  # 500-750 words


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    INDEXED = "indexed"
    SUMMARIZED = "summarized"
    ERROR = "error"


class ChunkType(str, Enum):
    """Types of document chunks."""

    CHAPTER = "chapter"
    SECTION = "section"
    HEADING = "heading"
    SLIDE = "slide"
    PARAGRAPH = "paragraph"
    AUTO = "auto"


# ============================================================================
# COMMON DATA MODELS
# ============================================================================


class DocumentInfo(BaseSchema):
    """Document information model."""

    id: PositiveInt = Field(..., description="Document ID")
    title: LimitedStr = Field(..., description="Document title")
    file_path: str = Field(..., description="Path to document file")
    file_type: DocumentType = Field(..., description="Document file type")
    upload_date: datetime = Field(..., description="Upload timestamp")
    total_pages: Optional[NonNegativeInt] = Field(
        None, description="Total number of pages"
    )
    total_words: Optional[NonNegativeInt] = Field(None, description="Total word count")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    notes: Optional[str] = Field(None, max_length=2000, description="User notes")
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED, description="Processing status"
    )
    indexed: bool = Field(default=False, description="Whether document is indexed")
    summarized: bool = Field(
        default=False, description="Whether document is summarized"
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        """Validate file path exists and has correct extension."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")

        # Check file extension matches type
        extension = path.suffix.lower().lstrip(".")
        if extension not in [dt.value for dt in DocumentType]:
            raise ValueError(f"Unsupported file extension: {extension}")

        return str(path.absolute())

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags list."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")

        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
            if len(tag.strip()) == 0:
                raise ValueError("Tags cannot be empty")
            if len(tag) > 50:
                raise ValueError("Tag too long (max 50 characters)")

        return [tag.strip() for tag in v if tag.strip()]


class ChunkInfo(BaseSchema):
    """Document chunk information model."""

    id: PositiveInt = Field(..., description="Chunk ID")
    document_id: PositiveInt = Field(..., description="Parent document ID")
    chunk_index: NonNegativeInt = Field(..., description="Chunk order index")
    chunk_type: ChunkType = Field(..., description="Type of chunk")
    title: LimitedStr = Field(..., description="Chunk title")
    start_page: Optional[PositiveInt] = Field(None, description="Starting page number")
    end_page: Optional[PositiveInt] = Field(None, description="Ending page number")
    word_count: NonNegativeInt = Field(..., description="Word count in chunk")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @model_validator(mode="after")
    def validate_page_range(self):
        """Validate end page is after start page."""
        if self.end_page is not None and self.start_page is not None:
            if self.end_page < self.start_page:
                raise ValueError("End page must be >= start page")
        return self


class SummaryInfo(BaseSchema):
    """Summary information model."""

    id: PositiveInt = Field(..., description="Summary ID")
    chunk_id: Optional[PositiveInt] = Field(None, description="Source chunk ID")
    document_id: Optional[PositiveInt] = Field(None, description="Source document ID")
    summary_type: SummaryType = Field(..., description="Type of summary")
    content: Annotated[str, Field(min_length=10, max_length=5000)] = Field(
        ..., description="Summary content"
    )
    word_count: PositiveInt = Field(..., description="Summary word count")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    model_name: Optional[str] = Field(None, description="AI model used for generation")

    @model_validator(mode="after")
    def validate_source(self):
        """Validate that either chunk_id or document_id is provided."""
        if not self.chunk_id and not self.document_id:
            raise ValueError("Either chunk_id or document_id must be provided")

        if self.chunk_id and self.document_id:
            raise ValueError("Provide either chunk_id OR document_id, not both")

        return self

    @field_validator("word_count")
    @classmethod
    def validate_word_count_matches_type(cls, v, info):
        """Validate word count matches summary type expectations."""
        # Note: summary_type validation would need to be done at model level
        # This is a simplified version for now
        if v > 1000:
            raise ValueError("Summary too long (max 1000 words)")
        return v


# ============================================================================
# DOCUMENT MANAGEMENT TOOL SCHEMAS
# ============================================================================


class UploadDocumentRequest(BaseRequest):
    """Request schema for uploading documents."""

    file_path: str = Field(..., description="Path to document file")
    title: Optional[str] = Field(
        None, max_length=500, description="Optional document title"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Optional document tags"
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        """Validate file path and supported type."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")

        # Check supported extensions
        extension = path.suffix.lower().lstrip(".")
        if extension not in [dt.value for dt in DocumentType]:
            supported = [dt.value for dt in DocumentType]
            raise ValueError(
                f"Unsupported file type '{extension}'. Supported: {supported}"
            )

        return str(path.absolute())


class UploadDocumentResponse(BaseResponse):
    """Response schema for document upload."""

    document: Optional[DocumentInfo] = Field(
        None, description="Uploaded document information"
    )

    @model_validator(mode="after")
    def validate_success_response(cls, values):
        """Ensure document info is provided for successful responses."""
        if values.get("success") and not values.get("document"):
            raise ValueError("Document information required for successful upload")
        return values


class GetDocumentRequest(BaseRequest):
    """Request schema for retrieving document information."""

    document_id: PositiveInt = Field(..., description="Document ID to retrieve")


class GetDocumentResponse(BaseResponse):
    """Response schema for document retrieval."""

    document: Optional[DocumentInfo] = Field(None, description="Document information")


class ListDocumentsRequest(BaseRequest):
    """Request schema for listing documents."""

    file_type: Optional[DocumentType] = Field(None, description="Filter by file type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (AND logic)")
    indexed: Optional[bool] = Field(None, description="Filter by indexing status")
    summarized: Optional[bool] = Field(None, description="Filter by summary status")
    limit: Optional[LimitedResults] = Field(
        100, description="Maximum results to return"
    )
    offset: Optional[NonNegativeInt] = Field(
        0, description="Results offset for pagination"
    )
    sort_by: Optional[Literal["upload_date", "title", "file_type"]] = Field(
        "upload_date", description="Sort field"
    )
    sort_order: Optional[Literal["asc", "desc"]] = Field(
        "desc", description="Sort order"
    )


class ListDocumentsResponse(BaseResponse):
    """Response schema for document listing."""

    documents: List[DocumentInfo] = Field(
        default_factory=list, description="List of documents"
    )
    total: NonNegativeInt = Field(
        0, description="Total number of documents matching filters"
    )
    limit: PositiveInt = Field(..., description="Limit used in query")
    offset: NonNegativeInt = Field(..., description="Offset used in query")
    has_more: bool = Field(..., description="Whether more results are available")


class DeleteDocumentRequest(BaseRequest):
    """Request schema for deleting documents."""

    document_id: PositiveInt = Field(..., description="Document ID to delete")


class DeleteDocumentResponse(BaseResponse):
    """Response schema for document deletion."""

    deleted_document_id: Optional[int] = Field(
        None, description="ID of deleted document"
    )
    deleted_chunks_count: Optional[int] = Field(
        None, description="Number of deleted chunks"
    )
    deleted_summaries_count: Optional[int] = Field(
        None, description="Number of deleted summaries"
    )


class SearchDocumentsRequest(BaseRequest):
    """Request schema for searching documents."""

    query: SearchQuery = Field(..., description="Search query")
    file_type: Optional[DocumentType] = Field(None, description="Filter by file type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: Optional[SmallResults] = Field(20, description="Maximum results")
    include_content: bool = Field(
        False, description="Include content excerpts in results"
    )


class SearchResult(BaseSchema):
    """Individual search result."""

    document_id: PositiveInt = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    chunk_id: Optional[PositiveInt] = Field(
        None, description="Matching chunk ID if applicable"
    )
    chunk_title: Optional[str] = Field(None, description="Matching chunk title")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    excerpt: Optional[str] = Field(None, description="Content excerpt with highlights")


class SearchDocumentsResponse(BaseResponse):
    """Response schema for document search."""

    results: List[SearchResult] = Field(
        default_factory=list, description="Search results"
    )
    total_results: NonNegativeInt = Field(0, description="Total matching results")
    query_time_ms: float = Field(
        ..., ge=0.0, description="Query execution time in milliseconds"
    )


# ============================================================================
# INDEXING AND CHUNKING TOOL SCHEMAS
# ============================================================================


class IndexDocumentRequest(BaseRequest):
    """Request schema for indexing documents."""

    document_id: PositiveInt = Field(..., description="Document ID to index")
    strategy: ChunkingStrategy = Field(
        ChunkingStrategy.AUTO, description="Chunking strategy to use"
    )
    force_reindex: bool = Field(
        False, description="Force re-indexing if already indexed"
    )


class IndexDocumentResponse(BaseResponse):
    """Response schema for document indexing."""

    document_id: Optional[PositiveInt] = Field(None, description="Indexed document ID")
    chunks_created: NonNegativeInt = Field(0, description="Number of chunks created")
    strategy_used: Optional[ChunkingStrategy] = Field(
        None, description="Chunking strategy used"
    )
    chunks: List[ChunkInfo] = Field(default_factory=list, description="Created chunks")
    processing_time_ms: float = Field(
        0.0, ge=0.0, description="Processing time in milliseconds"
    )


class GetDocumentStructureRequest(BaseRequest):
    """Request schema for retrieving document structure."""

    document_id: PositiveInt = Field(..., description="Document ID")


class GetDocumentStructureResponse(BaseResponse):
    """Response schema for document structure."""

    document_id: Optional[PositiveInt] = Field(None, description="Document ID")
    document_title: Optional[str] = Field(None, description="Document title")
    indexed: bool = Field(False, description="Whether document is indexed")
    chunks: List[ChunkInfo] = Field(default_factory=list, description="Document chunks")
    total_chunks: NonNegativeInt = Field(0, description="Total number of chunks")


class GetChunkContentRequest(BaseRequest):
    """Request schema for retrieving chunk content."""

    chunk_id: PositiveInt = Field(..., description="Chunk ID")
    include_metadata: bool = Field(True, description="Include chunk metadata")


class GetChunkContentResponse(BaseResponse):
    """Response schema for chunk content."""

    chunk_id: Optional[PositiveInt] = Field(None, description="Chunk ID")
    document_id: Optional[PositiveInt] = Field(None, description="Parent document ID")
    title: Optional[str] = Field(None, description="Chunk title")
    content: Optional[str] = Field(None, description="Full chunk content")
    word_count: NonNegativeInt = Field(0, description="Word count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class ListChunksRequest(BaseRequest):
    """Request schema for listing document chunks."""

    document_id: PositiveInt = Field(..., description="Document ID")
    chunk_type: Optional[ChunkType] = Field(None, description="Filter by chunk type")


class ListChunksResponse(BaseResponse):
    """Response schema for chunk listing."""

    document_id: Optional[PositiveInt] = Field(None, description="Document ID")
    chunks: List[ChunkInfo] = Field(default_factory=list, description="Document chunks")
    total_chunks: NonNegativeInt = Field(0, description="Total chunks")


# ============================================================================
# SUMMARIZATION TOOL SCHEMAS
# ============================================================================


class SummarizeChunkRequest(BaseRequest):
    """Request schema for chunk summarization."""

    chunk_id: PositiveInt = Field(..., description="Chunk ID to summarize")
    summary_type: SummaryType = Field(
        SummaryType.STANDARD, description="Type of summary"
    )
    focus_areas: Optional[List[str]] = Field(None, description="Areas to focus on")
    model_name: Optional[str] = Field(None, description="AI model to use")

    @field_validator("focus_areas")
    @classmethod
    def validate_focus_areas(cls, v):
        """Validate focus areas list."""
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 focus areas allowed")

            for area in v:
                if not isinstance(area, str) or len(area.strip()) == 0:
                    raise ValueError("Focus areas must be non-empty strings")
                if len(area) > 100:
                    raise ValueError("Focus area too long (max 100 characters)")

            return [area.strip() for area in v if area.strip()]
        return v


class SummarizeChunkResponse(BaseResponse):
    """Response schema for chunk summarization."""

    chunk_id: Optional[PositiveInt] = Field(None, description="Summarized chunk ID")
    summary: Optional[SummaryInfo] = Field(None, description="Generated summary")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Processing time")


class SummarizeDocumentRequest(BaseRequest):
    """Request schema for document summarization."""

    document_id: PositiveInt = Field(..., description="Document ID to summarize")
    summary_type: SummaryType = Field(
        SummaryType.STANDARD, description="Type of summary"
    )
    include_chunks: bool = Field(
        True, description="Whether to summarize individual chunks"
    )
    focus_areas: Optional[List[str]] = Field(None, description="Areas to focus on")
    model_name: Optional[str] = Field(None, description="AI model to use")


class SummarizeDocumentResponse(BaseResponse):
    """Response schema for document summarization."""

    document_id: Optional[PositiveInt] = Field(
        None, description="Summarized document ID"
    )
    document_summary: Optional[SummaryInfo] = Field(
        None, description="Overall document summary"
    )
    chunk_summaries: List[SummaryInfo] = Field(
        default_factory=list, description="Individual chunk summaries"
    )
    total_summaries: NonNegativeInt = Field(0, description="Total summaries created")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Processing time")


class GetSummaryRequest(BaseRequest):
    """Request schema for retrieving summaries."""

    chunk_id: Optional[PositiveInt] = Field(None, description="Chunk ID")
    document_id: Optional[PositiveInt] = Field(None, description="Document ID")
    summary_type: Optional[SummaryType] = Field(
        None, description="Filter by summary type"
    )

    @model_validator(mode="after")
    def validate_source_id(cls, values):
        """Validate that either chunk_id or document_id is provided."""
        chunk_id = values.get("chunk_id")
        document_id = values.get("document_id")

        if not chunk_id and not document_id:
            raise ValueError("Either chunk_id or document_id must be provided")

        return values


class GetSummaryResponse(BaseResponse):
    """Response schema for summary retrieval."""

    summaries: List[SummaryInfo] = Field(
        default_factory=list, description="Found summaries"
    )
    total_summaries: NonNegativeInt = Field(0, description="Total summaries found")


class SaveSummaryRequest(BaseRequest):
    """Request schema for saving summaries."""

    chunk_id: Optional[PositiveInt] = Field(None, description="Source chunk ID")
    document_id: Optional[PositiveInt] = Field(None, description="Source document ID")
    summary_type: SummaryType = Field(..., description="Type of summary")
    content: SummaryContent = Field(..., description="Summary content")
    model_name: Optional[str] = Field(None, description="AI model used")

    @model_validator(mode="after")
    def validate_source_id(cls, values):
        """Validate that either chunk_id or document_id is provided."""
        chunk_id = values.get("chunk_id")
        document_id = values.get("document_id")

        if not chunk_id and not document_id:
            raise ValueError("Either chunk_id or document_id must be provided")

        if chunk_id and document_id:
            raise ValueError("Provide either chunk_id OR document_id, not both")

        return values


class SaveSummaryResponse(BaseResponse):
    """Response schema for summary saving."""

    summary: Optional[SummaryInfo] = Field(
        None, description="Saved summary information"
    )


# ============================================================================
# SCHEMA REGISTRY AND UTILITIES
# ============================================================================


class SchemaRegistry:
    """
    Registry for MCP tool schemas.

    Provides centralized access to request/response schemas and validation utilities.
    """

    def __init__(self):
        """Initialize schema registry."""
        self.logger = get_debug_logger()
        self._request_schemas: Dict[str, type] = {}
        self._response_schemas: Dict[str, type] = {}
        self._register_default_schemas()

    def _register_default_schemas(self):
        """Register all default MCP tool schemas."""
        # Document management tools
        self.register_tool_schemas(
            "upload_document", UploadDocumentRequest, UploadDocumentResponse
        )
        self.register_tool_schemas(
            "get_document", GetDocumentRequest, GetDocumentResponse
        )
        self.register_tool_schemas(
            "list_documents", ListDocumentsRequest, ListDocumentsResponse
        )
        self.register_tool_schemas(
            "delete_document", DeleteDocumentRequest, DeleteDocumentResponse
        )
        self.register_tool_schemas(
            "search_documents", SearchDocumentsRequest, SearchDocumentsResponse
        )

        # Indexing and chunking tools
        self.register_tool_schemas(
            "index_document", IndexDocumentRequest, IndexDocumentResponse
        )
        self.register_tool_schemas(
            "get_document_structure",
            GetDocumentStructureRequest,
            GetDocumentStructureResponse,
        )
        self.register_tool_schemas(
            "get_chunk_content", GetChunkContentRequest, GetChunkContentResponse
        )
        self.register_tool_schemas("list_chunks", ListChunksRequest, ListChunksResponse)

        # Summarization tools
        self.register_tool_schemas(
            "summarize_chunk", SummarizeChunkRequest, SummarizeChunkResponse
        )
        self.register_tool_schemas(
            "summarize_document", SummarizeDocumentRequest, SummarizeDocumentResponse
        )
        self.register_tool_schemas("get_summary", GetSummaryRequest, GetSummaryResponse)
        self.register_tool_schemas(
            "save_summary", SaveSummaryRequest, SaveSummaryResponse
        )

        self.logger.info(f"Registered {len(self._request_schemas)} MCP tool schemas")

    def register_tool_schemas(
        self, tool_name: str, request_schema: type, response_schema: type
    ) -> None:
        """
        Register request and response schemas for an MCP tool.

        Args:
            tool_name: Name of the MCP tool
            request_schema: Pydantic request schema class
            response_schema: Pydantic response schema class
        """
        self._request_schemas[tool_name] = request_schema
        self._response_schemas[tool_name] = response_schema
        self.logger.debug(f"Registered schemas for tool: {tool_name}")

    def get_request_schema(self, tool_name: str) -> Optional[type]:
        """Get request schema for tool."""
        return self._request_schemas.get(tool_name)

    def get_response_schema(self, tool_name: str) -> Optional[type]:
        """Get response schema for tool."""
        return self._response_schemas.get(tool_name)

    def validate_request(self, tool_name: str, data: Dict[str, Any]) -> BaseRequest:
        """
        Validate request data against tool schema.

        Args:
            tool_name: Name of the MCP tool
            data: Request data dictionary

        Returns:
            Validated request object

        Raises:
            ValueError: If tool not found or validation fails
        """
        schema_class = self.get_request_schema(tool_name)
        if not schema_class:
            raise ValueError(f"No request schema registered for tool: {tool_name}")

        try:
            return schema_class(**data)
        except Exception as e:
            self.logger.error(f"Request validation failed for {tool_name}: {e}")
            raise ValueError(f"Request validation failed: {e}")

    def validate_response(self, tool_name: str, data: Dict[str, Any]) -> BaseResponse:
        """
        Validate response data against tool schema.

        Args:
            tool_name: Name of the MCP tool
            data: Response data dictionary

        Returns:
            Validated response object

        Raises:
            ValueError: If tool not found or validation fails
        """
        schema_class = self.get_response_schema(tool_name)
        if not schema_class:
            raise ValueError(f"No response schema registered for tool: {tool_name}")

        try:
            return schema_class(**data)
        except Exception as e:
            self.logger.error(f"Response validation failed for {tool_name}: {e}")
            raise ValueError(f"Response validation failed: {e}")

    def list_tools(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self._request_schemas.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive information about a tool's schemas.

        Args:
            tool_name: Name of the MCP tool

        Returns:
            Dictionary with tool schema information
        """
        request_schema = self.get_request_schema(tool_name)
        response_schema = self.get_response_schema(tool_name)

        if not request_schema or not response_schema:
            return None

        return {
            "tool_name": tool_name,
            "request_schema": {
                "name": request_schema.__name__,
                "fields": list(request_schema.__fields__.keys()),
                "schema": request_schema.schema(),
            },
            "response_schema": {
                "name": response_schema.__name__,
                "fields": list(response_schema.__fields__.keys()),
                "schema": response_schema.schema(),
            },
        }


# ============================================================================
# GLOBAL SCHEMA REGISTRY INSTANCE
# ============================================================================

# Global registry instance for easy access
schema_registry = SchemaRegistry()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def validate_tool_request(tool_name: str, data: Dict[str, Any]) -> BaseRequest:
    """
    Convenience function to validate MCP tool requests.

    Args:
        tool_name: Name of the MCP tool
        data: Request data dictionary

    Returns:
        Validated request object
    """
    return schema_registry.validate_request(tool_name, data)


def validate_tool_response(tool_name: str, data: Dict[str, Any]) -> BaseResponse:
    """
    Convenience function to validate MCP tool responses.

    Args:
        tool_name: Name of the MCP tool
        data: Response data dictionary

    Returns:
        Validated response object
    """
    return schema_registry.validate_response(tool_name, data)


def create_error_response(
    error_type: str, message: str, details: Optional[Dict[str, Any]] = None
) -> OperationError:
    """
    Create standardized error response.

    Args:
        error_type: Type of error
        message: Error message
        details: Optional additional details

    Returns:
        Standardized error response
    """
    return OperationError(
        success=False,
        message=message,
        error_type=error_type,
        error_code=error_type.lower().replace(" ", "_"),
        details=details or {},
    )


def create_validation_error_response(errors: List[str]) -> ValidationError:
    """
    Create validation error response from error list.

    Args:
        errors: List of error messages

    Returns:
        Validation error response
    """
    error_details = [
        ErrorDetail(code="validation_error", message=error, field=None, context=None)
        for error in errors
    ]

    return ValidationError(
        success=False,
        message=f"Validation failed with {len(errors)} errors",
        errors=error_details,
    )


def get_tool_schema_summary() -> Dict[str, Any]:
    """
    Get summary of all registered tool schemas.

    Returns:
        Summary dictionary with tool counts and names
    """
    tools = schema_registry.list_tools()

    return {
        "total_tools": len(tools),
        "tools": sorted(tools),
        "categories": {
            "document_management": [
                tool
                for tool in tools
                if tool
                in [
                    "upload_document",
                    "get_document",
                    "list_documents",
                    "delete_document",
                    "search_documents",
                ]
            ],
            "indexing_chunking": [
                tool
                for tool in tools
                if tool
                in [
                    "index_document",
                    "get_document_structure",
                    "get_chunk_content",
                    "list_chunks",
                ]
            ],
            "summarization": [
                tool
                for tool in tools
                if tool
                in [
                    "summarize_chunk",
                    "summarize_document",
                    "get_summary",
                    "save_summary",
                ]
            ],
        },
    }


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    # Example usage of schema validation

    # Test document upload request
    upload_data = {
        "file_path": "/path/to/document.pdf",
        "title": "Sample Document",
        "tags": ["study", "reference"],
    }

    try:
        request = validate_tool_request("upload_document", upload_data)
        print(f"✅ Upload request validated: {type(request).__name__}")
    except ValueError as e:
        print(f"❌ Upload request validation failed: {e}")

    # Test response validation
    response_data = {
        "success": True,
        "message": "Document uploaded successfully",
        "document": {
            "id": 1,
            "title": "Sample Document",
            "file_path": "/path/to/document.pdf",
            "file_type": "pdf",
            "upload_date": datetime.now(),
            "total_pages": 10,
            "total_words": 5000,
            "tags": ["study", "reference"],
            "status": "uploaded",
            "indexed": False,
            "summarized": False,
        },
    }

    try:
        response = validate_tool_response("upload_document", response_data)
        print(f"✅ Upload response validated: {type(response).__name__}")
    except ValueError as e:
        print(f"❌ Upload response validation failed: {e}")

    # Print schema summary
    summary = get_tool_schema_summary()
    print(f"\n📊 Schema Summary: {summary['total_tools']} tools registered")
    for category, tools in summary["categories"].items():
        print(f"  {category}: {len(tools)} tools")
