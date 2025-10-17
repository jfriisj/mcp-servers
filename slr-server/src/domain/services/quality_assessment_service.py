"""
Quality Assessment Service Interface

Defines the contract for quality assessment operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..domain.models import ResearchPaper, QualityAssessment


class IQualityAssessmentService(ABC):
    """
    Interface for quality assessment operations.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles quality assessment
    - Interface Segregation: Focused interface for quality operations
    - Dependency Inversion: Abstract interface, not concrete implementation
    """
    
    @abstractmethod
    def assess_paper_quality(self, paper: ResearchPaper, 
                           framework: str = "PRISMA") -> QualityAssessment:
        """Perform quality assessment on a research paper."""
        pass
    
    @abstractmethod
    def calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate overall quality score from individual criteria scores."""
        pass
    
    @abstractmethod
    def validate_assessment(self, assessment: QualityAssessment) -> Dict[str, Any]:
        """Validate quality assessment completeness and consistency."""
        pass
    
    @abstractmethod
    def get_assessment_criteria(self, framework: str) -> List[str]:
        """Get assessment criteria for a specific framework."""
        pass
    
    @abstractmethod
    def compare_assessments(self, assessment1: QualityAssessment, 
                          assessment2: QualityAssessment) -> Dict[str, Any]:
        """Compare two quality assessments for inter-rater reliability."""
        pass