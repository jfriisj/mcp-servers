"""
Repository layer for Systematic Literature Review (SLR) MCP Server.

This package provides data access layer implementations following the Repository pattern
and Clean Architecture Layer 3 principles for academic research data persistence.

Repository classes:
- PaperRepository: Research paper management and metadata
- ChunkRepository: Academic chunk storage and retrieval
- CitationRepository: Citation relationships and reference networks
- QualityAssessmentRepository: Quality evaluation data
- ResearchQuestionRepository: PICO/SPIDER question management
- HypothesisRepository: Research hypothesis tracking
- EvidenceRepository: Evidence synthesis data
"""

from .base_repository import BaseRepository, RepositoryError, EntityNotFoundError, DuplicateEntityError
from .paper_repository import PaperRepository

__all__ = [
    # Base classes
    "BaseRepository",
    "RepositoryError", 
    "EntityNotFoundError",
    "DuplicateEntityError",
    
    # Repository implementations
    "PaperRepository"
]
