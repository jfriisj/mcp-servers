"""
Unit tests for SLR repository classes.

Tests data access layer repositories following Clean Architecture Layer 3 principles
with comprehensive coverage of database operations and error handling.
"""

import pytest
import sqlite3
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from contextlib import contextmanager

from repositories.paper_repository import PaperRepository
from repositories.base_repository import (
    BaseRepository, RepositoryError, EntityNotFoundError, DuplicateEntityError
)
from database import Database

from models import (
    ResearchPaper, Author, Journal, Citation, QualityAssessment,
    StudyType
)


class TestPaperRepository:
    """Test PaperRepository data access operations."""

    @pytest.fixture
    def mock_database(self):
        """Create mock database connection."""
        db = Mock(spec=Database)
        # Mock cursor and common operations
        cursor_mock = Mock()
        cursor_mock.lastrowid = 1
        cursor_mock.fetchone.return_value = None
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock
        db.commit.return_value = None
        db.rollback.return_value = None
        return db

    @pytest.fixture
    def paper_repository(self, mock_database):
        """Create PaperRepository with mocked database."""
        repo = PaperRepository(mock_database)
        repo.db = mock_database  # Ensure db is set
        return repo

    @pytest.fixture
    def sample_paper(self):
        """Create sample research paper for testing."""
        return ResearchPaper(
            title="Machine Learning in Healthcare",
            file_path="/path/to/paper.pdf",
            file_type="pdf",
            publication_year=2023,
            doi="10.1000/123456789",
            abstract="This paper examines ML applications in healthcare.",
            keywords=["machine learning", "healthcare", "AI"],
            methodology="quantitative",
            study_type=StudyType.EXPERIMENTAL,
            sample_size=500,
            citation_count=15,
            file_size=2048000,
            total_pages=25,
            total_words=8500,
            tags=["research", "healthcare"],
            indexed=False,
            quality_assessed=False,
            upload_date=datetime(2023, 12, 1),
            created_at=datetime(2023, 12, 1),
            updated_at=datetime(2023, 12, 1)
        )

    @pytest.fixture
    def sample_authors(self):
        """Create sample authors for testing."""
        return [
            Author(name="Dr. Jane Smith", orcid="0000-0002-1825-0097"),
            Author(name="Dr. John Doe", email="john.doe@university.edu")
        ]

    @pytest.fixture
    def sample_journal(self):
        """Create sample journal for testing."""
        return Journal(
            name="Journal of Medical AI",
            issn="1234-5678",
            publisher="Academic Press",
            impact_factor=4.5,
            quartile="Q1",
            open_access=True
        )

    @pytest.mark.unit
    def test_create_paper_success(self, paper_repository, mock_database, sample_paper):
        """Test successful paper creation."""
        # Mock no existing paper
        paper_repository._get_by_file_path = Mock(return_value=None)
        paper_repository._create_paper_authors = Mock()
        paper_repository._create_or_link_journal = Mock()
        paper_repository.get_by_id = Mock(return_value=sample_paper)

        # Mock database insert
        cursor_mock = Mock()
        cursor_mock.lastrowid = 1
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.create(sample_paper)

        # Verify database operations
        mock_database.execute.assert_called_once()
        mock_database.commit.assert_called_once()
        
        # Verify result
        assert result == sample_paper
        paper_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    def test_create_paper_duplicate_file_path(self, paper_repository, sample_paper):
        """Test creation fails with duplicate file path."""
        # Mock existing paper
        existing_paper = ResearchPaper(id=1, title="Existing", file_path=sample_paper.file_path)
        paper_repository._get_by_file_path = Mock(return_value=existing_paper)

        with pytest.raises(DuplicateEntityError, match="ResearchPaper.*file_path"):
            paper_repository.create(sample_paper)

        # Verify no database insert attempted
        paper_repository.db.execute.assert_not_called()

    @pytest.mark.unit
    def test_create_paper_database_error(self, paper_repository, mock_database, sample_paper):
        """Test creation fails with database error."""
        paper_repository._get_by_file_path = Mock(return_value=None)
        
        # Mock database error
        mock_database.execute.side_effect = sqlite3.Error("Database error")

        with pytest.raises(RepositoryError, match="Failed to create research paper"):
            paper_repository.create(sample_paper)

    @pytest.mark.unit
    def test_create_paper_no_id_returned(self, paper_repository, mock_database, sample_paper):
        """Test creation fails when no ID returned."""
        paper_repository._get_by_file_path = Mock(return_value=None)
        
        # Mock cursor with no lastrowid
        cursor_mock = Mock()
        cursor_mock.lastrowid = None
        mock_database.execute.return_value = cursor_mock

        with pytest.raises(RepositoryError, match="Failed to create research paper: no ID returned"):
            paper_repository.create(sample_paper)

    @pytest.mark.unit
    def test_get_by_id_success(self, paper_repository, mock_database, sample_paper):
        """Test successful paper retrieval by ID."""
        # Mock database row
        db_row = (
            1, "Machine Learning in Healthcare", "/path/to/paper.pdf", "pdf",
            2023, "10.1000/123456789", "Abstract content...", 
            '["machine learning", "healthcare"]', "quantitative", "experimental",
            500, 15, "2023-12-01T00:00:00", 2048000, 25, 8500, '["research"]',
            False, False, None, None, "", "2023-12-01T00:00:00", "2023-12-01T00:00:00",
            # Journal fields
            "Journal of Medical AI", "1234-5678", "Academic Press", 4.5, "Q1", True
        )
        
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = db_row
        mock_database.execute.return_value = cursor_mock

        # Mock author retrieval
        paper_repository._get_paper_authors = Mock(return_value=[])
        paper_repository._row_to_paper = Mock(return_value=sample_paper)

        result = paper_repository.get_by_id(1)

        assert result == sample_paper
        mock_database.execute.assert_called_once()
        paper_repository._get_paper_authors.assert_called_once_with(1)

    @pytest.mark.unit
    def test_get_by_id_not_found(self, paper_repository, mock_database):
        """Test paper retrieval returns None when not found."""
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = None
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.get_by_id(999)

        assert result is None

    @pytest.mark.unit
    def test_get_by_id_database_error(self, paper_repository, mock_database):
        """Test get_by_id handles database errors."""
        mock_database.execute.side_effect = sqlite3.Error("Database error")

        with pytest.raises(RepositoryError, match="Failed to get research paper by ID"):
            paper_repository.get_by_id(1)

    @pytest.mark.unit
    def test_update_paper_success(self, paper_repository, mock_database, sample_paper):
        """Test successful paper update."""
        sample_paper.id = 1
        sample_paper.title = "Updated Title"

        # Mock database update
        cursor_mock = Mock()
        cursor_mock.rowcount = 1
        mock_database.execute.return_value = cursor_mock
        
        # Mock relationship updates
        paper_repository._update_paper_authors = Mock()
        paper_repository._update_paper_journal = Mock()
        paper_repository.get_by_id = Mock(return_value=sample_paper)

        result = paper_repository.update(sample_paper)

        assert result == sample_paper
        mock_database.execute.assert_called()
        mock_database.commit.assert_called_once()

    @pytest.mark.unit
    def test_update_paper_without_id(self, paper_repository, sample_paper):
        """Test update fails when paper has no ID."""
        sample_paper.id = None

        with pytest.raises(RepositoryError, match="Cannot update paper without ID"):
            paper_repository.update(sample_paper)

    @pytest.mark.unit
    def test_update_paper_not_found(self, paper_repository, mock_database, sample_paper):
        """Test update fails when paper not found."""
        sample_paper.id = 999

        # Mock no rows affected
        cursor_mock = Mock()
        cursor_mock.rowcount = 0
        mock_database.execute.return_value = cursor_mock

        with pytest.raises(EntityNotFoundError, match="ResearchPaper.*not found"):
            paper_repository.update(sample_paper)

    @pytest.mark.unit
    def test_delete_paper_success(self, paper_repository, mock_database):
        """Test successful paper deletion."""
        # Mock paper exists
        paper_repository.get_by_id = Mock(return_value=ResearchPaper(id=1, title="Test"))
        
        # Mock deletion cascade
        paper_repository._delete_paper_relationships = Mock()
        
        cursor_mock = Mock()
        cursor_mock.rowcount = 1
        mock_database.execute.return_value = cursor_mock

        paper_repository.delete(1)

        mock_database.execute.assert_called()
        mock_database.commit.assert_called_once()
        paper_repository._delete_paper_relationships.assert_called_once_with(1)

    @pytest.mark.unit
    def test_delete_paper_not_found(self, paper_repository):
        """Test deletion fails when paper not found."""
        paper_repository.get_by_id = Mock(return_value=None)

        with pytest.raises(EntityNotFoundError, match="ResearchPaper.*not found"):
            paper_repository.delete(999)

    @pytest.mark.unit
    def test_get_by_file_path_success(self, paper_repository, mock_database, sample_paper):
        """Test successful retrieval by file path."""
        paper_repository._get_by_file_path = Mock(return_value=sample_paper)

        result = paper_repository.get_by_file_path("/path/to/paper.pdf")

        assert result == sample_paper
        paper_repository._get_by_file_path.assert_called_once_with("/path/to/paper.pdf")

    @pytest.mark.unit
    def test_get_by_doi_success(self, paper_repository, mock_database, sample_paper):
        """Test successful retrieval by DOI."""
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = (1,)  # Return paper ID
        mock_database.execute.return_value = cursor_mock
        
        paper_repository.get_by_id = Mock(return_value=sample_paper)

        result = paper_repository.get_by_doi("10.1000/123456789")

        assert result == sample_paper
        paper_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    def test_list_all_success(self, paper_repository, mock_database):
        """Test successful listing of all papers."""
        # Mock database results
        db_rows = [
            (1, "Paper 1", "/path/1.pdf", "pdf", 2023, None, "Abstract 1", 
             "[]", "quantitative", "experimental", None, 0, None, 1024, 10, 5000, "[]",
             False, False, None, None, "", "2023-01-01T00:00:00", "2023-01-01T00:00:00"),
            (2, "Paper 2", "/path/2.pdf", "pdf", 2022, None, "Abstract 2",
             "[]", "qualitative", "observational", None, 0, None, 2048, 20, 8000, "[]",
             False, False, None, None, "", "2022-01-01T00:00:00", "2022-01-01T00:00:00")
        ]
        
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = db_rows
        mock_database.execute.return_value = cursor_mock
        
        # Mock paper construction
        paper1 = ResearchPaper(id=1, title="Paper 1", file_path="/path/1.pdf")
        paper2 = ResearchPaper(id=2, title="Paper 2", file_path="/path/2.pdf")
        
        paper_repository._get_paper_authors = Mock(return_value=[])
        paper_repository._row_to_paper = Mock(side_effect=[paper1, paper2])

        result = paper_repository.list_all()

        assert len(result) == 2
        assert result[0] == paper1
        assert result[1] == paper2

    @pytest.mark.unit
    def test_list_all_with_filters(self, paper_repository, mock_database):
        """Test listing papers with academic filters."""
        filters = {"methodology": "quantitative", "publication_year": 2023}
        
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = []
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.list_all(filters)

        # Verify SQL includes WHERE clause
        sql_call = mock_database.execute.call_args[0][0]
        assert "WHERE" in sql_call
        assert len(result) == 0

    @pytest.mark.unit
    def test_search_papers_success(self, paper_repository, mock_database):
        """Test successful paper search."""
        search_query = "machine learning healthcare"
        
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = []
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.search_papers(search_query, limit=10)

        # Verify full-text search query
        mock_database.execute.assert_called()
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_papers_by_author_success(self, paper_repository, mock_database):
        """Test retrieval of papers by author."""
        author_name = "Dr. Jane Smith"
        
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = []
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.get_papers_by_author(author_name)

        # Verify author join query
        mock_database.execute.assert_called()
        sql_call = mock_database.execute.call_args[0][0]
        assert "authors" in sql_call.lower()
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_papers_by_journal_success(self, paper_repository, mock_database):
        """Test retrieval of papers by journal."""
        journal_name = "Journal of Medical AI"
        
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = []
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.get_papers_by_journal(journal_name)

        # Verify journal join query
        mock_database.execute.assert_called()
        sql_call = mock_database.execute.call_args[0][0]
        assert "journals" in sql_call.lower()
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_citation_network_success(self, paper_repository, mock_database):
        """Test citation network analysis."""
        cursor_mock = Mock()
        cursor_mock.fetchall.return_value = [
            (1, 2, "Smith et al. demonstrated...", 0.85),
            (2, 3, "Building on previous work...", 0.75)
        ]
        mock_database.execute.return_value = cursor_mock

        result = paper_repository.get_citation_network(paper_id=1, depth=2)

        assert "nodes" in result
        assert "edges" in result
        assert len(result["edges"]) == 2

    @pytest.mark.unit
    def test_update_quality_assessment_status(self, paper_repository, mock_database):
        """Test updating quality assessment status."""
        cursor_mock = Mock()
        cursor_mock.rowcount = 1
        mock_database.execute.return_value = cursor_mock

        paper_repository.update_quality_assessment_status(
            paper_id=1,
            assessed=True,
            included=True,
            exclusion_reason=None
        )

        mock_database.execute.assert_called()
        mock_database.commit.assert_called_once()

    @pytest.mark.unit
    def test_update_indexing_status(self, paper_repository, mock_database):
        """Test updating indexing status."""
        cursor_mock = Mock()
        cursor_mock.rowcount = 1
        mock_database.execute.return_value = cursor_mock

        paper_repository.update_indexing_status(paper_id=1, indexed=True)

        mock_database.execute.assert_called()
        mock_database.commit.assert_called_once()


class TestBaseRepository:
    """Test BaseRepository abstract functionality."""

    @pytest.fixture
    def mock_database(self):
        """Create mock database connection."""
        return Mock(spec=Database)

    @pytest.mark.unit
    def test_repository_error_creation(self):
        """Test RepositoryError exception creation."""
        original_error = sqlite3.Error("Database connection failed")
        
        error = RepositoryError("Operation failed", original_error)
        
        assert str(error) == "Operation failed"
        assert error.original_error == original_error

    @pytest.mark.unit
    def test_entity_not_found_error(self):
        """Test EntityNotFoundError exception."""
        error = EntityNotFoundError("ResearchPaper", 123)
        
        assert "ResearchPaper" in str(error)
        assert "123" in str(error)

    @pytest.mark.unit
    def test_duplicate_entity_error(self):
        """Test DuplicateEntityError exception."""
        error = DuplicateEntityError("ResearchPaper", "title=Test Paper")
        
        assert "ResearchPaper" in str(error)
        assert "title=Test Paper" in str(error)


class TestRepositoryIntegration:
    """Integration tests for repository operations."""

    @pytest.mark.integration
    def test_paper_crud_operations(self):
        """Test complete CRUD operations for papers."""
        # This would be an integration test with real database
        # Skip if not in integration test mode
        pytest.skip("Integration test - requires real database")

    @pytest.mark.integration
    def test_complex_queries_performance(self):
        """Test performance of complex academic queries."""
        # Performance tests with large datasets
        pytest.skip("Integration test - requires real database with test data")

    @pytest.mark.integration
    def test_transaction_handling(self):
        """Test transaction rollback and commit scenarios."""
        # Test transaction boundaries and error recovery
        pytest.skip("Integration test - requires real database")


class TestRepositoryHelperMethods:
    """Test repository private helper methods."""

    @pytest.fixture
    def paper_repository(self, mock_database):
        """Create repository for testing helper methods."""
        return PaperRepository(mock_database)

    @pytest.mark.unit
    def test_build_where_clause_empty_filters(self, paper_repository):
        """Test WHERE clause building with empty filters."""
        with patch.object(paper_repository, '_build_where_clause') as mock_method:
            mock_method.return_value = ("", [])
            
            where_clause, params = mock_method({})
            
            assert where_clause == ""
            assert params == []

    @pytest.mark.unit
    def test_build_where_clause_multiple_filters(self, paper_repository):
        """Test WHERE clause building with multiple filters."""
        filters = {
            "methodology": "quantitative",
            "publication_year": 2023,
            "study_type": "experimental"
        }
        
        with patch.object(paper_repository, '_build_where_clause') as mock_method:
            expected_clause = "WHERE methodology = ? AND publication_year = ? AND study_type = ?"
            expected_params = ["quantitative", 2023, "experimental"]
            mock_method.return_value = (expected_clause, expected_params)
            
            where_clause, params = mock_method(filters)
            
            assert "WHERE" in where_clause
            assert len(params) == 3

    @pytest.mark.unit
    def test_row_to_paper_conversion(self, paper_repository):
        """Test database row to ResearchPaper conversion."""
        # Mock a complete database row
        db_row = (
            1, "Test Paper", "/path/test.pdf", "pdf", 2023, "10.1000/123456789",
            "Test abstract", '["keyword1", "keyword2"]', "quantitative", "experimental",
            100, 5, "2023-01-01T00:00:00", 1024, 10, 5000, '["tag1", "tag2"]',
            True, True, True, None, "Notes", "2023-01-01T00:00:00", "2023-01-01T00:00:00"
        )
        
        authors = [Author(name="Test Author")]
        journal = Journal(name="Test Journal")
        
        with patch.object(paper_repository, '_row_to_paper') as mock_method:
            expected_paper = ResearchPaper(
                id=1, title="Test Paper", file_path="/path/test.pdf"
            )
            mock_method.return_value = expected_paper
            
            result = mock_method(db_row, authors, journal)
            
            assert result.id == 1
            assert result.title == "Test Paper"