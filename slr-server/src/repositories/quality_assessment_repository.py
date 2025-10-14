"""
Quality Assessment Repository for systematic literature review quality evaluations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository, EntityNotFoundError
from ..models import QualityAssessment, AssessmentFramework, AssessmentStatus
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class QualityAssessmentRepository(BaseRepository[QualityAssessment]):
    """Repository for managing quality assessment data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, QualityAssessment, "quality_assessments")
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def get_by_paper_and_reviewer(self, paper_id: int, reviewer_id: str) -> Optional[QualityAssessment]:
        """Get quality assessment by paper and reviewer."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE paper_id = ? AND reviewer_id = ?
        """
        
        try:
            result = await self.db_connection.fetch_one(query, (paper_id, reviewer_id))
            return QualityAssessment(**result) if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting assessment for paper {paper_id}, reviewer {reviewer_id}: {e}")
            raise
    
    async def get_by_paper_id(self, paper_id: int) -> List[QualityAssessment]:
        """Get all quality assessments for a paper."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE paper_id = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            results = await self.db_connection.fetch_all(query, (paper_id,))
            return [QualityAssessment(**result) for result in results]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments for paper {paper_id}: {e}")
            raise
    
    async def get_by_reviewer_id(self, reviewer_id: str) -> List[QualityAssessment]:
        """Get all quality assessments by a reviewer."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE reviewer_id = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            results = await self.db_connection.fetch_all(query, (reviewer_id,))
            return [QualityAssessment(**result) for result in results]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments by reviewer {reviewer_id}: {e}")
            raise
    
    async def get_by_framework(self, framework: AssessmentFramework) -> List[QualityAssessment]:
        """Get all quality assessments using a specific framework."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE framework = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            results = await self.db_connection.fetch_all(query, (framework.value,))
            return [QualityAssessment(**result) for result in results]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments for framework {framework}: {e}")
            raise
    
    async def calculate_inter_rater_reliability(self, paper_ids: List[int], 
                                              reviewer_ids: List[str]) -> Dict[str, Any]:
        """Calculate inter-rater reliability metrics."""
        if len(reviewer_ids) < 2:
            raise ValueError("At least 2 reviewers required for inter-rater reliability")
        
        query = """
            SELECT paper_id, reviewer_id, overall_score, criteria_scores
            FROM quality_assessments 
            WHERE paper_id IN ({}) AND reviewer_id IN ({})
        """.format(
            ','.join(['?'] * len(paper_ids)),
            ','.join(['?'] * len(reviewer_ids))
        )
        
        try:
            params = paper_ids + reviewer_ids
            results = await self.db_connection.fetch_all(query, params)
            
            # Group by paper_id and reviewer_id
            assessments_by_paper = {}
            for result in results:
                paper_id = result['paper_id']
                reviewer_id = result['reviewer_id']
                
                if paper_id not in assessments_by_paper:
                    assessments_by_paper[paper_id] = {}
                
                assessments_by_paper[paper_id][reviewer_id] = {
                    'overall_score': result['overall_score'],
                    'criteria_scores': result['criteria_scores']
                }
            
            # Calculate reliability metrics
            return self._calculate_reliability_metrics(assessments_by_paper, reviewer_ids)
            
        except Exception as e:
            self.logger.error(f"Error calculating inter-rater reliability: {e}")
            raise
    
    def _calculate_reliability_metrics(self, assessments_by_paper: Dict[int, Dict[str, Dict]], 
                                     reviewer_ids: List[str]) -> Dict[str, Any]:
        """Calculate reliability metrics from assessment data."""
        import statistics
        
        overall_scores = []
        agreements = []
        
        for paper_id, paper_assessments in assessments_by_paper.items():
            # Check if all reviewers assessed this paper
            if len(paper_assessments) == len(reviewer_ids):
                scores = [assessment['overall_score'] for assessment in paper_assessments.values()]
                overall_scores.extend(scores)
                
                # Simple agreement calculation (within 0.1 points)
                max_score = max(scores)
                min_score = min(scores)
                agreements.append(1.0 if (max_score - min_score) <= 0.1 else 0.0)
        
        if not overall_scores:
            return {
                'agreement_rate': 0.0,
                'correlation_coefficient': 0.0,
                'mean_score': 0.0,
                'score_variance': 0.0,
                'papers_assessed': 0
            }
        
        return {
            'agreement_rate': statistics.mean(agreements) if agreements else 0.0,
            'correlation_coefficient': self._calculate_correlation(overall_scores),
            'mean_score': statistics.mean(overall_scores),
            'score_variance': statistics.variance(overall_scores) if len(overall_scores) > 1 else 0.0,
            'papers_assessed': len(assessments_by_paper)
        }
    
    def _calculate_correlation(self, scores: List[float]) -> float:
        """Simple correlation calculation."""
        if len(scores) < 2:
            return 0.0
        
        # For simplicity, return a basic correlation estimate
        # In production, you'd use scipy.stats.pearsonr or similar
        import statistics
        mean_score = statistics.mean(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        return max(0.0, min(1.0, 1.0 - (variance / (mean_score ** 2 + 1e-10))))