"""
Chunk Repository for Systematic Literature Review (SLR) MCP Server.

Provides data access layer for academic chunks following the Repository pattern
and Clean Architecture Layer 3 principles.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..domain.models import AcademicChunk
from .base_repository import BaseRepository, DatabaseConnection

logger = logging.getLogger(__name__)


class ChunkRepository(BaseRepository[AcademicChunk]):
    """Repository for academic chunk data access."""

    def __init__(self, db: DatabaseConnection):
        super().__init__(db)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the chunks table exists (it should already exist)."""
        cursor = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
        if not cursor.fetchone():
            logger.warning("Chunks table does not exist!")
        else:
            logger.debug("Chunks table exists")

    def create(self, chunk: AcademicChunk) -> AcademicChunk:
        """Create a new chunk."""
        # Normalize section_type to valid database values
        normalized_section_type = self._normalize_section_type(chunk.section_type)
        
        insert_sql = """
        INSERT INTO chunks (
            paper_id, chunk_index, content, chunk_type, section_title,
            start_page, end_page, word_count, semantic_keywords, research_concepts,
            methodology_elements, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = self.db.execute(insert_sql, (
            chunk.paper_id,
            chunk.chunk_index,
            chunk.content,
            normalized_section_type,  # maps to chunk_type (normalized)
            chunk.title,         # maps to section_title
            chunk.start_page,
            chunk.end_page,
            chunk.word_count,
            json.dumps(chunk.semantic_tags),          # maps to semantic_keywords
            json.dumps(chunk.research_elements),      # maps to research_concepts
            json.dumps([]),                           # methodology_elements (empty for now)
            json.dumps(chunk.metadata)
        ))
        
        chunk.id = cursor.lastrowid
        self.db.commit()
        logger.debug(f"Created chunk {chunk.id} for paper {chunk.paper_id}")
        
        return chunk

    @staticmethod
    def _normalize_section_type(section_type: str) -> str:
        """
        Normalize section types to valid database values.
        
        Database allows: title, abstract, introduction, methodology, results,
        discussion, conclusion, references, section, paragraph, figure, table,
        equation, citation
        """
        section_lower = section_type.lower().strip()
        
        # Valid database types
        valid_types = {
            'title', 'abstract', 'introduction', 'methodology', 'results',
            'discussion', 'conclusion', 'references', 'section', 'paragraph',
            'figure', 'table', 'equation', 'citation'
        }
        
        if section_lower in valid_types:
            return section_lower
        
        # Mapping invalid types to valid ones
        mapping = {
            'methods': 'methodology',
            'findings': 'results',
            'background': 'section',
            'body': 'section',
            'unknown': 'section',
            'appendix': 'section',
            'conclusions': 'conclusion',
        }
        
        return mapping.get(section_lower, 'section')  # Default to 'section'

    def get_by_id(self, chunk_id: int) -> Optional[AcademicChunk]:
        """Get chunk by ID."""
        cursor = self.db.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_chunk(row)
        return None

    def get_by_paper_id(self, paper_id: int) -> List[AcademicChunk]:
        """Get all chunks for a paper."""
        cursor = self.db.execute(
            "SELECT * FROM chunks WHERE paper_id = ? ORDER BY chunk_index", 
            (paper_id,)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_chunk(row) for row in rows]

    def delete_by_paper_id(self, paper_id: int) -> int:
        """Delete all chunks for a paper. Returns number of deleted chunks."""
        cursor = self.db.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
        deleted_count = cursor.rowcount
        self.db.commit()
        
        logger.info(f"Deleted {deleted_count} chunks for paper {paper_id}")
        return deleted_count

    def list_all(self, filter_criteria: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: int = 0) -> List[AcademicChunk]:
        """List all chunks with optional filtering."""
        base_query = "SELECT * FROM chunks"
        where_conditions = []
        params = []
        
        if filter_criteria:
            if "paper_id" in filter_criteria:
                where_conditions.append("paper_id = ?")
                params.append(filter_criteria["paper_id"])
            
            if "section_type" in filter_criteria:
                where_conditions.append("section_type = ?")
                params.append(filter_criteria["section_type"])
            
            if "min_confidence_score" in filter_criteria:
                where_conditions.append("confidence_score >= ?")
                params.append(filter_criteria["min_confidence_score"])
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        base_query += " ORDER BY paper_id, chunk_index"
        
        if limit:
            base_query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = self.db.execute(base_query, tuple(params))
        rows = cursor.fetchall()
        
        return [self._row_to_chunk(row) for row in rows]

    def count_by_paper_id(self, paper_id: int) -> int:
        """Count chunks for a paper."""
        cursor = self.db.execute("SELECT COUNT(*) FROM chunks WHERE paper_id = ?", (paper_id,))
        return cursor.fetchone()[0]

    def get_statistics(self) -> Dict[str, Any]:
        """Get chunk statistics for monitoring."""
        # Total chunks
        cursor = self.db.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        
        # Chunks per paper
        cursor = self.db.execute("""
            SELECT paper_id, COUNT(*) as chunk_count 
            FROM chunks 
            GROUP BY paper_id 
            ORDER BY chunk_count DESC
        """)
        chunks_per_paper = cursor.fetchall()
        
        # Average confidence score
        cursor = self.db.execute("SELECT AVG(confidence_score) FROM chunks WHERE confidence_score IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Section types distribution
        cursor = self.db.execute("""
            SELECT section_type, COUNT(*) as count 
            FROM chunks 
            GROUP BY section_type
        """)
        section_types = dict(cursor.fetchall())
        
        return {
            "total_chunks": total_chunks,
            "chunks_per_paper": chunks_per_paper,
            "average_confidence_score": round(avg_confidence, 2),
            "section_types": section_types
        }

    def _row_to_chunk(self, row) -> AcademicChunk:
        """Convert database row to AcademicChunk object."""
        # Database schema: id, paper_id, chunk_index, chunk_type, section_title, content, 
        # start_page, end_page, word_count, semantic_keywords, research_concepts, 
        # methodology_elements, statistical_results, figures_tables, citations_mentioned, 
        # quality_indicators, embedding_vector, metadata, indexed_for_search, created_at
        return AcademicChunk(
            id=row[0],
            paper_id=row[1],
            chunk_index=row[2],
            content=row[5],
            section_type=row[3] or "body",  # chunk_type -> section_type
            title=row[4],                   # section_title -> title
            start_page=row[6],
            end_page=row[7],
            word_count=row[8] or 0,
            citation_count=0,               # not in database
            figure_count=0,                 # not in database  
            table_count=0,                  # not in database
            research_elements=json.loads(row[10] or "[]"),  # research_concepts
            semantic_tags=json.loads(row[9] or "[]"),       # semantic_keywords
            confidence_score=0.7,           # default
            metadata=json.loads(row[17] or "{}"),
            created_at=datetime.fromisoformat(row[19]) if row[19] else None
        )

    def update(self, chunk: AcademicChunk) -> AcademicChunk:
        """Update existing chunk."""
        if chunk.id is None:
            raise ValueError("Cannot update chunk without ID")
        
        update_sql = """
        UPDATE chunks SET 
            content = ?, section_type = ?, title = ?,
            start_page = ?, end_page = ?, word_count = ?,
            citation_count = ?, figure_count = ?, table_count = ?,
            research_elements = ?, semantic_tags = ?, confidence_score = ?, metadata = ?
        WHERE id = ?
        """
        
        self.db.execute(update_sql, (
            chunk.content,
            chunk.section_type,
            chunk.title,
            chunk.start_page,
            chunk.end_page,
            chunk.word_count,
            chunk.citation_count,
            chunk.figure_count,
            chunk.table_count,
            json.dumps(chunk.research_elements),
            json.dumps(chunk.semantic_tags),
            chunk.confidence_score,
            json.dumps(chunk.metadata),
            chunk.id
        ))
        
        self.db.commit()
        logger.debug(f"Updated chunk {chunk.id}")
        
        return chunk

    def delete(self, chunk_id: int) -> bool:
        """Delete chunk by ID."""
        cursor = self.db.execute("DELETE FROM chunks WHERE id = ?", (chunk_id,))
        deleted = cursor.rowcount > 0
        self.db.commit()
        
        if deleted:
            logger.info(f"Deleted chunk {chunk_id}")
        
        return deleted