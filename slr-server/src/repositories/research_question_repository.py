"""
Research Question Repository for systematic literature review research question management.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository, EntityNotFoundError
from ..models import ResearchQuestion, QuestionFramework, QuestionStatus
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ResearchQuestionRepository(BaseRepository[ResearchQuestion]):
    """Repository for managing research question data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, ResearchQuestion, "research_questions")
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def get_by_framework(self, framework: QuestionFramework) -> List[ResearchQuestion]:
        """Get all research questions using a specific framework."""
        query = """
            SELECT * FROM research_questions 
            WHERE framework = ?
            ORDER BY created_at DESC
        """
        
        try:
            results = await self.db_connection.fetch_all(query, (framework.value,))
            return [ResearchQuestion(**result) for result in results]
            
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
            results = await self.db_connection.fetch_all(query, (status.value,))
            return [ResearchQuestion(**result) for result in results]
            
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
            results = await self.db_connection.fetch_all(query, params)
            return [ResearchQuestion(**result) for result in results]
            
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
            results = await self.db_connection.fetch_all(query, (QuestionStatus.ARCHIVED.value,))
            return [ResearchQuestion(**result) for result in results]
            
        except Exception as e:
            self.logger.error(f"Error getting active questions: {e}")
            raise