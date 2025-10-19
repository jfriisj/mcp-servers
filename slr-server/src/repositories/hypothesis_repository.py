"""
Hypothesis Repository for systematic literature review hypothesis management.
"""

import logging
from typing import List

from .base_repository import BaseRepository
from ..domain.models import ResearchHypothesis, HypothesisStatus
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class HypothesisRepository(BaseRepository[ResearchHypothesis]):
    """Repository for managing hypothesis data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = logger.getChild(self.__class__.__name__)
    
    # Implement required abstract methods from BaseRepository
    def create(self, entity: ResearchHypothesis) -> ResearchHypothesis:
        """Create a new hypothesis (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def get_by_id(self, entity_id: int):
        """Get hypothesis by ID (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def update(self, entity: ResearchHypothesis) -> ResearchHypothesis:
        """Update hypothesis (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def delete(self, entity_id: int) -> bool:
        """Delete hypothesis (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def list_all(self, filters=None):
        """List all hypotheses (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    async def get_by_research_question_id(self, research_question_id: int) -> List[ResearchHypothesis]:
        """Get all hypotheses for a research question."""
        query = """
            SELECT * FROM hypotheses 
            WHERE research_question_id = ?
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (research_question_id,))
            results = cursor.fetchall()
            return [ResearchHypothesis(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting hypotheses for research question {research_question_id}: {e}")
            raise
    
    async def get_by_status(self, status: HypothesisStatus) -> List[ResearchHypothesis]:
        """Get all hypotheses with a specific status."""
        query = """
            SELECT * FROM hypotheses 
            WHERE status = ?
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (status.value,))
            results = cursor.fetchall()
            return [ResearchHypothesis(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting hypotheses for status {status}: {e}")
            raise
    
    async def search_by_text(self, search_text: str) -> List[ResearchHypothesis]:
        """Search hypotheses by text content."""
        query = """
            SELECT * FROM hypotheses 
            WHERE hypothesis_text LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """
        
        search_pattern = f"%{search_text}%"
        params = (search_pattern, search_pattern)
        
        try:
            cursor = self.db.execute(query, params)
            results = cursor.fetchall()
            return [ResearchHypothesis(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error searching hypotheses for text '{search_text}': {e}")
            raise
    
    async def get_active_hypotheses(self) -> List[ResearchHypothesis]:
        """Get all active (non-rejected, non-archived) hypotheses."""
        query = """
            SELECT * FROM hypotheses 
            WHERE status NOT IN (?, ?)
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (
                HypothesisStatus.REJECTED.value,
                HypothesisStatus.ARCHIVED.value
            ))
            results = cursor.fetchall()
            return [ResearchHypothesis(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting active hypotheses: {e}")
            raise