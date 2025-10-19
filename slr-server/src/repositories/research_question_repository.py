"""
Research Question Repository for systematic literature review research question management.
"""

import logging
from typing import List

from .base_repository import BaseRepository
from ..domain.models import ResearchQuestion, QuestionFramework, QuestionStatus
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ResearchQuestionRepository(BaseRepository[ResearchQuestion]):
    """Repository for managing research question data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = logger.getChild(self.__class__.__name__)
    
    # Implement required abstract methods from BaseRepository
    def create(self, entity: ResearchQuestion) -> ResearchQuestion:
        """Create a new research question (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def get_by_id(self, entity_id: int):
        """Get research question by ID (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def update(self, entity: ResearchQuestion) -> ResearchQuestion:
        """Update research question (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def delete(self, entity_id: int) -> bool:
        """Delete research question (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    def list_all(self, filters=None):
        """List all research questions (stub for async implementation)."""
        raise NotImplementedError("Use async methods for this repository")
    
    async def get_by_framework(self, framework: QuestionFramework) -> List[ResearchQuestion]:
        """Get all research questions using a specific framework."""
        query = """
            SELECT * FROM research_questions 
            WHERE framework = ?
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (framework.value,))
            results = cursor.fetchall()
            return [ResearchQuestion(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting questions for framework {framework}: {e}")
            raise
    
    async def get_by_status(self, status: QuestionStatus) -> List[ResearchQuestion]:
        """Get all research questions with a specific status."""
        query = """
            SELECT * FROM research_questions 
            WHERE status = ?
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (status.value,))
            results = cursor.fetchall()
            return [ResearchQuestion(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting questions for status {status}: {e}")
            raise
    
    async def search_by_text(self, search_text: str) -> List[ResearchQuestion]:
        """Search research questions by text content."""
        query = """
            SELECT * FROM research_questions 
            WHERE question_text LIKE ? OR pico_population LIKE ? 
               OR pico_intervention LIKE ? OR pico_comparison LIKE ?
               OR pico_outcome LIKE ?
            ORDER BY created_at DESC
        """
        
        search_pattern = f"%{search_text}%"
        params = (search_pattern,) * 5
        
        try:
            cursor = self.db.execute(query, params)
            results = cursor.fetchall()
            return [ResearchQuestion(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error searching questions for text '{search_text}': {e}")
            raise
    
    async def get_active_questions(self) -> List[ResearchQuestion]:
        """Get all active (non-archived) research questions."""
        query = """
            SELECT * FROM research_questions 
            WHERE status != ?
            ORDER BY created_at DESC
        """
        
        try:
            cursor = self.db.execute(query, (QuestionStatus.ARCHIVED.value,))
            results = cursor.fetchall()
            return [ResearchQuestion(**dict(zip([col[0] for col in cursor.description], row))) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting active questions: {e}")
            raise