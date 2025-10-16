"""
Quality Assessment Domain Model

Represents quality assessment results for research papers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AssessmentFramework(Enum):
    """Quality assessment frameworks."""
    PRISMA = "PRISMA"
    CASP = "CASP" 
    JBI = "JBI"
    CUSTOM = "CUSTOM"


class AssessmentCriteria(Enum):
    """Standard assessment criteria."""
    RESEARCH_QUESTION = "research_question"
    METHODOLOGY = "methodology"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    RESULTS = "results"
    CONCLUSIONS = "conclusions"
    BIAS_RISK = "bias_risk"
    GENERALIZABILITY = "generalizability"


@dataclass
class QualityAssessment:
    """
    Domain model for quality assessments of research papers.
    
    Encapsulates business logic for quality evaluation following
    systematic review guidelines.
    """
    
    id: Optional[int] = None
    paper_id: int = 0
    reviewer_id: str = ""
    framework: AssessmentFramework = AssessmentFramework.PRISMA
    
    # Assessment scores (0-10 scale typically)
    scores: Dict[str, float] = field(default_factory=dict)
    
    # Detailed assessments per criteria
    criteria_assessments: Dict[AssessmentCriteria, Dict[str, Any]] = field(default_factory=dict)
    
    # Overall metrics
    overall_score: Optional[float] = None
    quality_level: Optional[str] = None  # "high", "medium", "low"
    include_in_review: bool = True
    
    # Assessment details
    strengths: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    comments: str = ""
    
    # Metadata
    assessment_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate business rules after initialization."""
        if self.paper_id <= 0:
            raise ValueError("Paper ID must be positive")
            
        if not self.reviewer_id or len(self.reviewer_id.strip()) == 0:
            raise ValueError("Reviewer ID cannot be empty")
        
        # Validate scores are in valid range
        for criteria, score in self.scores.items():
            if score < 0 or score > 10:
                raise ValueError(f"Score for {criteria} must be between 0 and 10")
        
        # Calculate overall score if not provided
        if self.overall_score is None and self.scores:
            self.overall_score = sum(self.scores.values()) / len(self.scores)
        
        # Determine quality level based on overall score
        if self.overall_score is not None and self.quality_level is None:
            if self.overall_score >= 8.0:
                self.quality_level = "high"
            elif self.overall_score >= 6.0:
                self.quality_level = "medium"
            else:
                self.quality_level = "low"
    
    @property
    def is_high_quality(self) -> bool:
        """Check if assessment indicates high quality."""
        return self.quality_level == "high"
    
    @property
    def is_complete(self) -> bool:
        """Check if assessment is complete."""
        required_criteria = [
            AssessmentCriteria.RESEARCH_QUESTION,
            AssessmentCriteria.METHODOLOGY,
            AssessmentCriteria.RESULTS
        ]
        return all(criteria in self.criteria_assessments for criteria in required_criteria)
    
    @property 
    def risk_of_bias(self) -> float:
        """Calculate risk of bias score."""
        bias_score = self.scores.get("bias_risk", 5.0)
        return max(0.0, 10.0 - bias_score)  # Invert score (lower bias = higher quality)
    
    def add_strength(self, strength: str) -> None:
        """Add a strength if not already present."""
        if strength and strength not in self.strengths:
            self.strengths.append(strength)
    
    def add_limitation(self, limitation: str) -> None:
        """Add a limitation if not already present."""
        if limitation and limitation not in self.limitations:
            self.limitations.append(limitation)
    
    def set_criteria_assessment(self, criteria: AssessmentCriteria, score: float, 
                               comments: str = "", evidence: str = "") -> None:
        """Set assessment for a specific criteria."""
        if score < 0 or score > 10:
            raise ValueError("Score must be between 0 and 10")
        
        self.criteria_assessments[criteria] = {
            "score": score,
            "comments": comments,
            "evidence": evidence,
            "assessed_at": datetime.now().isoformat()
        }
        
        # Update scores dict
        self.scores[criteria.value] = score
        
        # Recalculate overall score
        if self.scores:
            self.overall_score = sum(self.scores.values()) / len(self.scores)
    
    def get_criteria_score(self, criteria: AssessmentCriteria) -> Optional[float]:
        """Get score for specific criteria."""
        assessment = self.criteria_assessments.get(criteria)
        return assessment.get("score") if assessment else None
    
    def meets_inclusion_criteria(self) -> bool:
        """Check if paper meets inclusion criteria based on assessment."""
        if not self.is_complete:
            return False
        
        # Basic quality threshold
        if self.overall_score and self.overall_score < 4.0:
            return False
        
        # Check for critical issues
        methodology_score = self.get_criteria_score(AssessmentCriteria.METHODOLOGY)
        if methodology_score and methodology_score < 3.0:
            return False
        
        return self.include_in_review
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'reviewer_id': self.reviewer_id,
            'framework': self.framework.value,
            'scores': self.scores,
            'criteria_assessments': {
                criteria.value: assessment 
                for criteria, assessment in self.criteria_assessments.items()
            },
            'overall_score': self.overall_score,
            'quality_level': self.quality_level,
            'include_in_review': self.include_in_review,
            'strengths': self.strengths,
            'limitations': self.limitations,
            'comments': self.comments,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityAssessment':
        """Create instance from dictionary."""
        # Convert enums
        if 'framework' in data and isinstance(data['framework'], str):
            data['framework'] = AssessmentFramework(data['framework'])
        
        if 'criteria_assessments' in data:
            criteria_assessments = {}
            for criteria_str, assessment in data['criteria_assessments'].items():
                criteria = AssessmentCriteria(criteria_str)
                criteria_assessments[criteria] = assessment
            data['criteria_assessments'] = criteria_assessments
        
        # Convert ISO strings back to datetime
        for field in ['assessment_date', 'created_at', 'updated_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)