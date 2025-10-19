#!/usr/bin/env python3
"""
Unit tests for ProjectRepository

Tests CRUD operations, validation, filtering, and JSON serialization.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

# Adjust path for imports
import sys
SLR_SERVER_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(SLR_SERVER_ROOT))

from src.domain.models import SLRProject
from src.repositories.project_repository import ProjectRepository
from src.repositories.base_repository import (
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Create projects table matching the real schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS slr_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            description TEXT NOT NULL,
            research_questions TEXT DEFAULT '[]',
            population TEXT,
            intervention TEXT,
            comparison TEXT,
            outcome TEXT,
            folder_path TEXT NOT NULL,
            project_file_path TEXT,
            project_file_type TEXT,
            current_phase TEXT DEFAULT 'planning',
            status TEXT DEFAULT 'active',
            total_papers INTEGER DEFAULT 0,
            papers_screening INTEGER DEFAULT 0,
            papers_included INTEGER DEFAULT 0,
            papers_excluded INTEGER DEFAULT 0,
            papers_quality_assessed INTEGER DEFAULT 0,
            created_by TEXT,
            team_members TEXT DEFAULT '[]',
            settings TEXT DEFAULT '{}',
            tags TEXT DEFAULT '[]',
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    yield conn
    conn.close()


@pytest.fixture
def mock_db_connection(in_memory_db):
    """Create mock database connection"""
    mock_conn = Mock()
    mock_conn.execute = lambda query, params=(): in_memory_db.execute(query, params)
    mock_conn.commit = in_memory_db.commit
    mock_conn.rollback = in_memory_db.rollback
    return mock_conn


@pytest.fixture
def repository(mock_db_connection):
    """Create ProjectRepository instance"""
    repo = ProjectRepository(db=mock_db_connection)
    return repo


@pytest.fixture
def sample_project():
    """Create a sample SLRProject"""
    return SLRProject(
        name="test-ai-review",
        display_name="Test AI Review",
        description="Testing project creation",
        research_questions=["RQ1", "RQ2"],
        team_members=["Dr. Smith"],
        tags=["ai", "healthcare"],
    )


class TestProjectRepositoryCreate:
    """Test CREATE operations"""

    def test_create_project_success(self, repository, sample_project):
        """Test successful project creation"""
        created = repository.create(sample_project)
        
        assert created.id is not None
        assert created.name == sample_project.name
        assert created.display_name == sample_project.display_name

    def test_create_project_duplicate_name(self, repository, sample_project):
        """Test duplicate name raises error"""
        repository.create(sample_project)
        
        duplicate = SLRProject(
            name="test-ai-review",
            display_name="Different",
            description="Different",
        )
        
        with pytest.raises(DuplicateEntityError):
            repository.create(duplicate)


class TestProjectRepositoryRead:
    """Test READ operations"""

    def test_get_by_id_success(self, repository, sample_project):
        """Test retrieval by ID"""
        created = repository.create(sample_project)
        retrieved = repository.get_by_id(created.id)
        
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_by_id_not_found(self, repository):
        """Test non-existent ID returns None"""
        result = repository.get_by_id(99999)
        assert result is None

    def test_list_all(self, repository, sample_project):
        """Test listing all projects"""
        repository.create(sample_project)
        projects = repository.list_all()
        
        assert len(projects) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
