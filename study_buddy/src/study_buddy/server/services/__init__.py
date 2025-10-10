"""
Services package for Study Buddy MCP Server.

This package contains the business logic layer (Clean Architecture Layer 2)
with framework-agnostic services that orchestrate operations between
repositories and external interfaces.

Services:
- DocumentService: Document lifecycle and business rules
- ChunkingService: Document segmentation and indexing
- SummaryService: AI-generated content management

Clean Architecture Layer 2:
- Framework-agnostic business logic
- Depends only on repository abstractions
- Contains reusable business rules
- Validates input and enforces constraints
- Orchestrates operations across components
"""

from .chunking_service import ChunkingError, ChunkingService
from .document_service import DocumentError, DocumentService
from .summary_service import SummaryError, SummaryService

__all__ = [
    "DocumentService",
    "DocumentError",
    "ChunkingService",
    "ChunkingError",
    "SummaryService",
    "SummaryError"
]
