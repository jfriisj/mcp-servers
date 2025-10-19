"""
Quality Assessment Repository Interface

Defines the contract for quality assessment data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import QualityAssessment


class IQualityAssessmentRepository(ABC):
    """
    Interface for quality assessment repository operations.
    
    Follows SRP by handling only quality assessment data access.
    """
    
    @abstractmethod
    def create(self, assessment: QualityAssessment) -> QualityAssessment:
        """Create a new quality assessment."""
        pass
    
    @abstractmethod
    def get_by_id(self, assessment_id: int) -> Optional[QualityAssessment]:
        """Retrieve assessment by ID."""
        pass
    
    @abstractmethod
    def get_by_paper_id(self, paper_id: int) -> List[QualityAssessment]:
        """Get all assessments for a paper."""
        pass
    
    @abstractmethod
    def get_by_reviewer_id(self, reviewer_id: str) -> List[QualityAssessment]:
        """Get all assessments by a reviewer."""
        pass
    
    @abstractmethod
    def update(self, assessment: QualityAssessment) -> QualityAssessment:
        """Update existing assessment."""
        pass
    
    @abstractmethod
    def delete(self, assessment_id: int) -> bool:
        """Delete assessment by ID."""
        pass
    
    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[QualityAssessment]:
        """List assessments with optional filters."""
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count assessments matching filters."""
        pass


class IQualityAnalysisRepository(ABC):
    """
    Interface for quality analysis operations.
    Separated from basic CRUD following ISP.
    """
    
    @abstractmethod
    def calculate_inter_rater_reliability(self, paper_ids: List[int], reviewer_ids: List[str]) -> Dict[str, Any]:
        """Calculate inter-rater reliability statistics."""
        pass
    
    @abstractmethod
    def get_consensus_assessments(self, paper_ids: List[int]) -> List[QualityAssessment]:
        """Get consensus assessments for papers."""
        pass
    
    @abstractmethod
    def get_quality_statistics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get quality assessment statistics."""
        pass