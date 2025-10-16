#!/usr/bin/env python3
"""
Test indexing service directly to debug the chunk creation issue.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_indexing():
    """Test the indexing service directly."""
    try:
        # Import the necessary components
        from src.database.connection import DatabaseConnection
        from src.repositories.paper_repository import PaperRepository
        from src.repositories.chunk_repository import ChunkRepository
        from src.services.academic_chunking_service import AcademicChunkingService
        
        # Initialize database connection
        db_path = "database/slr_database.db"
        if not os.path.exists(db_path):
            logger.error(f"Database not found: {db_path}")
            return
            
        logger.info("Initializing database connection...")
        db_connection = DatabaseConnection(db_path)
        
        # Initialize repositories
        logger.info("Initializing repositories...")
        paper_repo = PaperRepository(db_connection)
        chunk_repo = ChunkRepository(db_connection)
        
        # Initialize service
        logger.info("Initializing chunking service...")
        chunking_service = AcademicChunkingService(paper_repo, chunk_repo)
        
        # Get paper 1
        logger.info("Getting paper 1...")
        paper = paper_repo.get_by_id(1)
        if not paper:
            logger.error("Paper 1 not found!")
            return
            
        logger.info(f"Found paper: {paper.title}")
        logger.info(f"File path: {paper.file_path}")
        logger.info(f"File exists: {os.path.exists(paper.file_path) if paper.file_path else False}")
        
        # Test content extraction
        logger.info("Testing content extraction...")
        content = chunking_service._extract_paper_content(paper)
        logger.info(f"Extracted content length: {len(content)} characters")
        logger.info(f"Word count: {len(content.split())}")
        
        if len(content) < 100:
            logger.warning("Very little content extracted!")
            logger.info(f"Content: {content}")
            return
        
        # Test chunking
        logger.info("Testing chunking...")
        from src.services.academic_chunking_service import IndexingStrategy
        chunks = chunking_service._simple_chunk_content(paper, content, IndexingStrategy.HYBRID)
        logger.info(f"Generated {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i}: {chunk.word_count} words, section: {chunk.section_type}")
        
        # Test chunk storage
        logger.info("Testing chunk storage...")
        stored_chunks = []
        for chunk in chunks:
            logger.info(f"Storing chunk {chunk.chunk_index}...")
            try:
                stored_chunk = chunk_repo.create(chunk)
                stored_chunks.append(stored_chunk)
                logger.info(f"Successfully stored chunk {stored_chunk.id}")
            except Exception as e:
                logger.error(f"Failed to store chunk: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Successfully stored {len(stored_chunks)} chunks")
        
        # Verify chunks in database
        db_chunks = chunk_repo.count_by_paper_id(1)
        logger.info(f"Chunks in database for paper 1: {db_chunks}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_indexing()