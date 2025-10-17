"""
Domain Layer - Core Business Logic

This layer contains:
- Domain entities and value objects
- Business rules and logic
- Domain service interfaces
- Repository interfaces (ports)

This layer has no dependencies on external frameworks or infrastructure.
"""

# Models (Entities and Value Objects)
from .models import (
    ResearchPaper,
    AcademicChunk,
    QualityAssessment,
)

# Re-export all domain models
__all__ = [
    # Models
    "ResearchPaper",
    "AcademicChunk",
    "QualityAssessment",
]