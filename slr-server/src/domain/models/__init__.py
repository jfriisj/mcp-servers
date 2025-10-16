"""
Domain Models

Core business entities for the SLR system following DDD principles.
"""

from .research_paper import ResearchPaper
from .academic_chunk import AcademicChunk
from .quality_assessment import QualityAssessment

__all__ = [
    "ResearchPaper",
    "AcademicChunk", 
    "QualityAssessment"
]