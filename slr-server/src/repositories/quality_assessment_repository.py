"""
Quality Assessment Repository for systematic literature review quality evaluations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository, EntityNotFoundError
from ..domain.models import QualityAssessment, AssessmentFramework, AssessmentStatus
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class QualityAssessmentRepository(BaseRepository[QualityAssessment]):
    """Repository for managing quality assessment data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = logger.getChild(self.__class__.__name__)
    
    def get_by_paper_and_reviewer(self, paper_id: int, reviewer_id: str) -> Optional[QualityAssessment]:
        """Get quality assessment by paper and reviewer."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE paper_id = ? AND reviewer_id = ?
        """
        
        try:
            cursor = self.db.execute(query, (paper_id, reviewer_id))
            row = cursor.fetchone()
            return self._row_to_assessment(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Error getting assessment for paper {paper_id}, reviewer {reviewer_id}: {e}")
            raise
    
    def get_by_paper_id(self, paper_id: int) -> List[QualityAssessment]:
        """Get all quality assessments for a paper."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE paper_id = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            cursor = self.db.execute(query, (paper_id,))
            rows = cursor.fetchall()
            return [self._row_to_assessment(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments for paper {paper_id}: {e}")
            raise
    
    def get_by_reviewer_id(self, reviewer_id: str) -> List[QualityAssessment]:
        """Get all quality assessments by a reviewer."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE reviewer_id = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            cursor = self.db.execute(query, (reviewer_id,))
            rows = cursor.fetchall()
            return [self._row_to_assessment(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments by reviewer {reviewer_id}: {e}")
            raise
    
    def get_by_framework(self, framework: AssessmentFramework) -> List[QualityAssessment]:
        """Get all quality assessments using a specific framework."""
        query = """
            SELECT * FROM quality_assessments 
            WHERE framework = ?
            ORDER BY assessment_date DESC
        """
        
        try:
            cursor = self.db.execute(query, (framework.value,))
            rows = cursor.fetchall()
            return [self._row_to_assessment(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting assessments for framework {framework}: {e}")
            raise
    
    def calculate_inter_rater_reliability(self, paper_ids: List[int], 
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
            cursor = self.db.execute(query, params)
            rows = cursor.fetchall()
            
            # Group by paper_id and reviewer_id
            assessments_by_paper = {}
            for row in rows:
                paper_id = row[0]
                reviewer_id = row[1]
                
                if paper_id not in assessments_by_paper:
                    assessments_by_paper[paper_id] = {}
                
                assessments_by_paper[paper_id][reviewer_id] = {
                    'overall_score': row[2],
                    'criteria_scores': row[3]
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
    
    # Implement required abstract methods from BaseRepository
    
    def create(self, assessment: QualityAssessment) -> QualityAssessment:
        """Create a new quality assessment."""
        query = """
            INSERT INTO quality_assessments (
                paper_id, reviewer_id, framework, overall_score, criteria_scores,
                assessment_date, notes, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            now = datetime.now().isoformat()
            cursor = self.db.execute(
                query,
                (
                    assessment.paper_id,
                    assessment.reviewer_id,
                    assessment.framework.value if assessment.framework else None,
                    assessment.overall_score,
                    assessment.criteria_scores,
                    assessment.assessment_date.isoformat() if assessment.assessment_date else now,
                    assessment.notes,
                    assessment.status.value if assessment.status else AssessmentStatus.PENDING.value,
                    now,
                    now
                )
            )
            
            assessment_id = cursor.lastrowid
            self.db.commit()
            
            # Return created assessment with ID
            created_assessment = self.get_by_id(assessment_id)
            return created_assessment if created_assessment else assessment
            
        except Exception as e:
            self.logger.error(f"Error creating quality assessment: {e}")
            raise
    
    def get_by_id(self, assessment_id: int) -> Optional[QualityAssessment]:
        """Get quality assessment by ID."""
        query = "SELECT * FROM quality_assessments WHERE id = ?"
        
        try:
            cursor = self.db.execute(query, (assessment_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_assessment(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting quality assessment by ID {assessment_id}: {e}")
            raise
    
    def update(self, assessment: QualityAssessment) -> QualityAssessment:
        """Update an existing quality assessment."""
        if not assessment.id:
            raise ValueError("Assessment must have an ID to update")
            
        query = """
            UPDATE quality_assessments SET
                overall_score = ?, criteria_scores = ?, notes = ?,
                status = ?, updated_at = ?
            WHERE id = ?
        """
        
        try:
            cursor = self.db.execute(
                query,
                (
                    assessment.overall_score,
                    assessment.criteria_scores,
                    assessment.notes,
                    assessment.status.value if assessment.status else None,
                    datetime.now().isoformat(),
                    assessment.id
                )
            )
            
            if cursor.rowcount == 0:
                raise EntityNotFoundError("QualityAssessment", assessment.id)
                
            self.db.commit()
            
            # Return updated assessment
            updated_assessment = self.get_by_id(assessment.id)
            return updated_assessment if updated_assessment else assessment
            
        except Exception as e:
            self.logger.error(f"Error updating quality assessment {assessment.id}: {e}")
            raise
    
    def delete(self, assessment_id: int) -> bool:
        """Delete a quality assessment."""
        query = "DELETE FROM quality_assessments WHERE id = ?"
        
        try:
            cursor = self.db.execute(query, (assessment_id,))
            deleted = cursor.rowcount > 0
            
            if deleted:
                self.db.commit()
                
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error deleting quality assessment {assessment_id}: {e}")
            raise
    
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[QualityAssessment]:
        """List all quality assessments with optional filtering."""
        query = "SELECT * FROM quality_assessments"
        params = []
        
        if filters:
            conditions = []
            
            if 'paper_id' in filters:
                conditions.append("paper_id = ?")
                params.append(filters['paper_id'])
                
            if 'reviewer_id' in filters:
                conditions.append("reviewer_id = ?")
                params.append(filters['reviewer_id'])
                
            if 'framework' in filters:
                conditions.append("framework = ?")
                params.append(filters['framework'])
                
            if 'status' in filters:
                conditions.append("status = ?")
                params.append(filters['status'])
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY assessment_date DESC"
        
        try:
            cursor = self.db.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_assessment(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error listing quality assessments: {e}")
            raise
    
    def _row_to_assessment(self, row: tuple) -> QualityAssessment:
        """Convert database row to QualityAssessment instance."""
        import json
        
        # Expected column order: id, paper_id, reviewer_id, framework, overall_score, 
        # criteria_scores, assessment_date, notes, status, created_at, updated_at
        assessment_date = datetime.fromisoformat(row[6]) if row[6] else None
        created_at = datetime.fromisoformat(row[9]) if len(row) > 9 and row[9] else None
        updated_at = datetime.fromisoformat(row[10]) if len(row) > 10 and row[10] else None
        
        return QualityAssessment(
            id=row[0],
            paper_id=row[1],
            reviewer_id=row[2],
            framework=AssessmentFramework(row[3]) if row[3] else AssessmentFramework.PRISMA,
            overall_score=row[4],
            criteria_scores=json.loads(row[5]) if row[5] else {},
            assessment_date=assessment_date,
            notes=row[7],
            status=AssessmentStatus(row[8]) if len(row) > 8 and row[8] else AssessmentStatus.PENDING,
            created_at=created_at,
            updated_at=updated_at
        )
