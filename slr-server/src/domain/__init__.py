"""
Domain Layer - Core Business Logic

This layer contains:
- Domain entities and value objects  
- Business rules and logic
- Domain service interfaces
- Repository interfaces (ports)

This layer has no dependencies on external frameworks or infrastructure.
"""

# Import all models from the comprehensive models file
from .models import (
    # Enums
    QualityRating,
    AssessmentFramework,
    CitationType,
    HypothesisType,
    EvidenceLevel,
    QuestionFramework,
    StudyType,
    EvidenceType,
    ValidationLevel,
    EffectDirection,
    AssessmentStatus,
    QuestionStatus,
    HypothesisStatus,
    ProjectStatus,
    ProjectPhase,
    ScreeningStatus,
    ScreeningPhase,
    
    # Domain Models
    SLRProject,
    Author,
    Journal,
    ResearchPaper,
    AcademicChunk,
    Citation,
    QualityAssessment,
    ResearchQuestion,
    ResearchHypothesis,
    EvidenceItem,
)

# Re-export all domain models
__all__ = [
    # Enums
    "QualityRating",
    "AssessmentFramework",
    "CitationType",
    "HypothesisType",
    "EvidenceLevel",
    "QuestionFramework",
    "StudyType",
    "EvidenceType",
    "ValidationLevel",
    "EffectDirection",
    "AssessmentStatus",
    "QuestionStatus",
    "HypothesisStatus",
    "ProjectStatus",
    "ProjectPhase",
    "ScreeningStatus",
    "ScreeningPhase",
    
    # Models
    "SLRProject",
    "Author",
    "Journal",
    "ResearchPaper",
    "AcademicChunk",
    "Citation",
    "QualityAssessment",
    "ResearchQuestion",
    "ResearchHypothesis",
    "EvidenceItem",
]
