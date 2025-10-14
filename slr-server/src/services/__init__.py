"""
Services layer for business logic orchestration.

This module contains service classes that implement business logic
following Clean Architecture Layer 2 principles. Services orchestrate
operations between repositories, models, and external dependencies
while remaining framework-agnostic.

Service classes in this layer:
- ResearchDocumentService: Orchestrates academic document lifecycle
- QualityAssessmentService: Implements systematic quality evaluation
- ResearchQuestionService: Validates and manages research questions
- HypothesisAnalysisService: Handles hypothesis testing and evidence synthesis
- AcademicChunkingService: Manages intelligent academic indexing
"""

from .research_document_service import ResearchDocumentService, ResearchDocumentError
from .quality_assessment_service import QualityAssessmentService, QualityAssessmentError
from .research_question_service import ResearchQuestionService, ResearchQuestionError
from .hypothesis_analysis_service import HypothesisAnalysisService, HypothesisAnalysisError
from .academic_chunking_service import AcademicChunkingService, AcademicChunkingError

__all__ = [
    'ResearchDocumentService',
    'ResearchDocumentError',
    'QualityAssessmentService',
    'QualityAssessmentError',
    'ResearchQuestionService',
    'ResearchQuestionError',
    'HypothesisAnalysisService',
    'HypothesisAnalysisError',
    'AcademicChunkingService',
    'AcademicChunkingError',
]
