"""
Unit tests for SLR service classes.

Tests business logic services following Clean Architecture Layer 2 principles
with comprehensive coverage of academic research workflows.
"""

import pytest
from unittest.mock import Mock, patch
import os
import tempfile

from services.research_document_service import ResearchDocumentService
from services.quality_assessment_service import QualityAssessmentService
from services.research_question_service import ResearchQuestionService
from services.hypothesis_analysis_service import HypothesisAnalysisService
from services.academic_chunking_service import AcademicChunkingService

from models import (
    ResearchPaper, Author, QualityAssessment,
    EvidenceItem, AcademicChunk,
    QualityFramework, QuestionFramework,
    EvidenceType, StudyType
)
from repositories.paper_repository import PaperRepository


class TestResearchDocumentService:
    """Test ResearchDocumentService business logic."""

    @pytest.fixture
    def mock_paper_repository(self):
        """Create mock paper repository."""
        repo = Mock(spec=PaperRepository)
        repo.get_by_file_path.return_value = None
        repo.get_by_doi.return_value = None
        repo.get_by_id.return_value = None
        repo.create.return_value = None
        repo.update.return_value = None
        repo.list_all.return_value = []
        return repo

    @pytest.fixture
    def research_service(self, mock_paper_repository):
        """Create ResearchDocumentService with mocked dependencies."""
        return ResearchDocumentService(mock_paper_repository)

    @pytest.fixture
    def temp_pdf_file(self):
        """Create temporary PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'%PDF-1.4 Mock PDF content for testing')
            temp_path = tmp.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.mark.unit
    def test_upload_paper_success(self, research_service, mock_paper_repository,
                                  temp_pdf_file):
        """Test successful paper upload with metadata extraction."""
        # Mock extracted metadata
        mock_metadata = {
            "title": "Machine Learning in Healthcare",
            "abstract": "This paper examines ML applications "
                       "in healthcare with comprehensive analysis.",
            "authors": [Author(name="Dr. Jane Smith"), Author(name="Dr. John Doe")],
            "keywords": ["machine learning", "healthcare", "AI"],
            "publication_year": 2023,
            "total_pages": 15,
            "total_words": 8500
        }

        # Mock created paper
        mock_created_paper = ResearchPaper(
            id=1,
            title="Machine Learning in Healthcare",
            file_path=temp_pdf_file,
            file_type="pdf"
        )
        mock_paper_repository.create.return_value = mock_created_paper

        # Mock metadata extraction
        with patch.object(research_service, 'extract_metadata',
                          return_value=mock_metadata), \
             patch.object(research_service, '_classify_paper',
                          return_value={"methodology": "quantitative",
                                        "study_type": "experimental"}), \
             patch.object(research_service, '_analyze_paper_citations'):

            result = research_service.upload_paper(
                file_path=temp_pdf_file,
                doi="10.1000/123456789",
                tags=["research", "healthcare"]
            )

            # Verify repository interactions
            mock_paper_repository.get_by_file_path.assert_called_once_with(
                temp_pdf_file)
            mock_paper_repository.create.assert_called_once()

            # Verify result
            assert result == mock_created_paper

    @pytest.mark.unit
    def test_upload_paper_file_not_found(self, research_service):
        """Test upload fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError,
                           match="Academic paper file not found"):
            research_service.upload_paper("/nonexistent/file.pdf")

    @pytest.mark.unit
    def test_upload_paper_invalid_extension(self, research_service):
        """Test upload fails with unsupported file extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'Not an academic format')
            temp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Unsupported academic format"):
                research_service.upload_paper(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_upload_paper_file_too_large(self, research_service):
        """Test upload fails when file exceeds size limit."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Create file larger than MAX_FILE_SIZE
            large_content = b'x' * (research_service.MAX_FILE_SIZE + 1)
            tmp.write(large_content)
            temp_path = tmp.name

        try:
            with pytest.raises(
                ValueError, match="Academic paper size .* exceeds maximum"):
                research_service.upload_paper(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_upload_paper_duplicate_file_path(self, research_service,
                                              mock_paper_repository,
                                              temp_pdf_file):
        """Test upload fails when file path already exists."""
        existing_paper = ResearchPaper(
            id=1, title="Existing", file_path=temp_pdf_file)
        mock_paper_repository.get_by_file_path.return_value = existing_paper

        with pytest.raises(
                ValueError,
                match="Research paper already exists for file path"):
            research_service.upload_paper(temp_pdf_file)

    @pytest.mark.unit
    def test_upload_paper_duplicate_doi(self, research_service,
                                        mock_paper_repository,
                                        temp_pdf_file):
        """Test upload fails when DOI already exists."""
        existing_paper = ResearchPaper(
            id=1, title="Existing", doi="10.1000/123456789")
        mock_paper_repository.get_by_doi.return_value = existing_paper

        with patch.object(research_service, '_is_duplicate_doi',
                          return_value=True):
            with pytest.raises(
                    ValueError,
                    match="Research paper with DOI .* already exists"):
                research_service.upload_paper(temp_pdf_file,
                                              doi="10.1000/123456789")

    @pytest.mark.unit
    def test_upload_paper_too_many_authors(self, research_service,
                                           temp_pdf_file):
        """Test upload fails when too many authors provided."""
        # Create list of authors exceeding limit
        many_authors = [Author(name=f"Author {i}")
                        for i in range(research_service.MAX_AUTHORS + 1)]

        with pytest.raises(ValueError, match="Author count .* exceeds maximum"):
            research_service.upload_paper(temp_pdf_file, authors=many_authors)

    @pytest.mark.unit
    def test_upload_paper_invalid_publication_year(self, research_service,
                                                   temp_pdf_file):
        """Test upload fails with invalid publication year."""
        with pytest.raises(ValueError, match="Invalid publication year"):
            research_service.upload_paper(temp_pdf_file, publication_year=1799)

        with pytest.raises(ValueError, match="Invalid publication year"):
            research_service.upload_paper(temp_pdf_file, publication_year=2050)

    @pytest.mark.unit
    def test_upload_paper_short_abstract(self, research_service,
                                         mock_paper_repository,
                                         temp_pdf_file):
        """Test upload fails when abstract is too short."""
        short_metadata = {
            "title": "Test Paper",
            "abstract": "Too short",  # Less than MIN_ABSTRACT_LENGTH
            "authors": []
        }

        with patch.object(research_service, 'extract_metadata',
                          return_value=short_metadata):
            with pytest.raises(ValueError, match="Abstract too short"):
                research_service.upload_paper(temp_pdf_file,
                                              auto_extract_metadata=True)

    @pytest.mark.unit
    def test_analyze_citations_paper_not_found(self, research_service,
                                               mock_paper_repository):
        """Test citation analysis fails when paper doesn't exist."""
        mock_paper_repository.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Research paper .* not found"):
            research_service.analyze_citations(999)

    @pytest.mark.unit
    def test_classify_paper_success(self, research_service,
                                    mock_paper_repository):
        """Test successful paper classification."""
        mock_paper = ResearchPaper(
            id=1,
            title="Machine Learning Study",
            abstract="Quantitative analysis of ML algorithms",
            keywords=["machine learning", "quantitative"]
        )
        mock_paper_repository.get_by_id.return_value = mock_paper

        classification = {
            "methodology": "quantitative",
            "study_type": "experimental",
            "confidence_score": 0.85
        }

        with patch.object(research_service, '_classify_paper',
                          return_value=classification):
            result = research_service.classify_paper(1)

            assert result["methodology"] == "quantitative"
            assert result["study_type"] == "experimental"
            mock_paper_repository.update.assert_called_once_with(mock_paper)

    @pytest.mark.unit
    def test_get_research_corpus_invalid_sort_field(self, research_service):
        """Test corpus retrieval fails with invalid sort field."""
        with pytest.raises(ValueError, match="Invalid sort field"):
            research_service.get_research_corpus(sort_by="invalid_field")

    @pytest.mark.unit
    def test_get_research_corpus_invalid_sort_order(self, research_service):
        """Test corpus retrieval fails with invalid sort order."""
        with pytest.raises(ValueError, match="Sort order must be"):
            research_service.get_research_corpus(sort_order="invalid")

    @pytest.mark.unit
    def test_get_research_corpus_excessive_limit(self, research_service):
        """Test corpus retrieval fails with excessive limit."""
        with pytest.raises(ValueError, match="Corpus limit cannot exceed"):
            research_service.get_research_corpus(limit=20000)

    @pytest.mark.unit
    def test_get_research_corpus_success(self, research_service,
                                         mock_paper_repository):
        """Test successful research corpus retrieval."""
        mock_papers = [
            ResearchPaper(id=1, title="Paper 1", publication_year=2023),
            ResearchPaper(id=2, title="Paper 2", publication_year=2022)
        ]
        mock_paper_repository.list_all.return_value = mock_papers

        with patch.object(research_service, '_build_academic_filters',
                          return_value={}), \
             patch.object(research_service, '_sort_research_papers',
                          return_value=mock_papers):

            result = research_service.get_research_corpus(
                filters={"methodology": "quantitative"},
                sort_by="publication_year",
                sort_order="desc",
                limit=100
            )

            assert len(result) == 2
            assert result[0].id == 1
            assert result[1].id == 2


class TestQualityAssessmentService:
    """Test QualityAssessmentService business logic."""

    @pytest.fixture
    def mock_paper_repository(self):
        """Create mock paper repository."""
        repo = Mock(spec=PaperRepository)
        return repo

    @pytest.fixture
    def quality_service(self, mock_paper_repository):
        """Create QualityAssessmentService with mocked dependencies."""
        return QualityAssessmentService(mock_paper_repository)

    @pytest.mark.unit
    def test_assess_paper_quality_success(self, quality_service,
                                          mock_paper_repository):
        """Test successful paper quality assessment."""
        mock_paper = ResearchPaper(
            id=1,
            title="High Quality Research Paper",
            abstract="Comprehensive study with rigorous methodology",
            methodology="quantitative",
            study_type=StudyType.EXPERIMENTAL
        )
        mock_paper_repository.get_by_id.return_value = mock_paper

        # Mock quality assessment logic
        expected_assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            overall_score=85.0,
            study_design_score=90.0,
            methodology_score=80.0,
            risk_of_bias="low"
        )

        with patch.object(quality_service, '_perform_prisma_assessment',
                          return_value=expected_assessment):
            result = quality_service.assess_paper_quality(
                paper_id=1,
                framework=QualityFramework.PRISMA,
                reviewer_id="reviewer_001"
            )

            assert result.overall_score == 85.0
            assert result.framework == QualityFramework.PRISMA
            assert result.risk_of_bias == "low"

    @pytest.mark.unit
    def test_assess_paper_quality_paper_not_found(self, quality_service,
                                                   mock_paper_repository):
        """Test quality assessment fails when paper doesn't exist."""
        mock_paper_repository.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Paper .* not found"):
            quality_service.assess_paper_quality(
                paper_id=999,
                framework=QualityFramework.PRISMA
            )


class TestResearchQuestionService:
    """Test ResearchQuestionService business logic."""

    @pytest.fixture
    def question_service(self):
        """Create ResearchQuestionService."""
        return ResearchQuestionService()

    @pytest.mark.unit
    def test_validate_pico_question_success(self, question_service):
        """Test successful PICO question validation."""
        question_text = ("In adults with diabetes (P), does continuous "
                         "glucose monitoring (I) compared to traditional "
                         "testing (C) improve glycemic control (O)?")

        result = question_service.validate_research_question(
            question_text=question_text,
            framework=QuestionFramework.PICO
        )

        assert result["valid"] is True
        assert result["framework"] == QuestionFramework.PICO
        assert "population" in result["components"]
        assert "intervention" in result["components"]
        assert "comparison" in result["components"]
        assert "outcome" in result["components"]

    @pytest.mark.unit
    def test_validate_spider_question_success(self, question_service):
        """Test successful SPIDER question validation."""
        question_text = ("What are the experiences of nurses (S) regarding "
                         "patient safety interventions (PI) "
                         "in hospital settings (D)?")

        result = question_service.validate_research_question(
            question_text=question_text,
            framework=QuestionFramework.SPIDER
        )

        assert result["valid"] is True
        assert result["framework"] == QuestionFramework.SPIDER
        assert "sample" in result["components"]

    @pytest.mark.unit
    def test_validate_question_empty_text(self, question_service):
        """Test validation fails with empty question."""
        with pytest.raises(ValueError, match="Question text cannot be empty"):
            question_service.validate_research_question("")

    @pytest.mark.unit
    def test_validate_question_too_short(self, question_service):
        """Test validation fails with question too short."""
        with pytest.raises(ValueError, match="Question too short"):
            question_service.validate_research_question("Short?")


class TestHypothesisAnalysisService:
    """Test HypothesisAnalysisService business logic."""

    @pytest.fixture
    def mock_paper_repository(self):
        """Create mock paper repository."""
        return Mock(spec=PaperRepository)

    @pytest.fixture
    def hypothesis_service(self, mock_paper_repository):
        """Create HypothesisAnalysisService with mocked dependencies."""
        return HypothesisAnalysisService(mock_paper_repository)

    @pytest.mark.unit
    def test_test_hypothesis_success(self, hypothesis_service,
                                     mock_paper_repository):
        """Test successful hypothesis testing."""
        hypothesis_text = ("Machine learning algorithms demonstrate higher "
                          "diagnostic accuracy than traditional methods "
                          "in medical imaging.")

        # Mock papers with evidence
        mock_papers = [
            ResearchPaper(id=1, title="ML in Radiology",
                          abstract="95% accuracy achieved"),
            ResearchPaper(id=2, title="AI Diagnostics",
                          abstract="Improved sensitivity")
        ]
        mock_paper_repository.get_by_id.side_effect = mock_papers

        # Mock evidence extraction and analysis
        mock_evidence = [
            EvidenceItem(
                paper_id=1,
                evidence_text="95% accuracy vs 78% traditional",
                evidence_type=EvidenceType.STATISTICAL,
                supporting=True,
                strength="strong"
            )
        ]

        with patch.object(hypothesis_service, '_extract_evidence',
                          return_value=mock_evidence), \
             patch.object(hypothesis_service, '_perform_statistical_analysis',
                          return_value={"p_value": 0.02, "significant": True}):

            result = hypothesis_service.test_hypothesis(
                hypothesis_text=hypothesis_text,
                paper_ids=[1, 2],
                significance_level=0.05
            )

            assert result["hypothesis_supported"] is True
            assert result["p_value"] == 0.02
            assert len(result["supporting_evidence"]) > 0

    @pytest.mark.unit
    def test_test_hypothesis_insufficient_papers(self, hypothesis_service):
        """Test hypothesis testing fails with insufficient papers."""
        with pytest.raises(ValueError, match="At least 2 papers required"):
            hypothesis_service.test_hypothesis(
                hypothesis_text="Test hypothesis",
                paper_ids=[1],
                significance_level=0.05
            )

    @pytest.mark.unit
    def test_test_hypothesis_invalid_significance_level(self, hypothesis_service):
        """Test hypothesis testing fails with invalid significance level."""
        with pytest.raises(ValueError,
                           match="Significance level must be between"):
            hypothesis_service.test_hypothesis(
                hypothesis_text="Test hypothesis",
                paper_ids=[1, 2],
                significance_level=1.5
            )


class TestAcademicChunkingService:
    """Test AcademicChunkingService business logic."""

    @pytest.fixture
    def mock_paper_repository(self):
        """Create mock paper repository."""
        return Mock(spec=PaperRepository)

    @pytest.fixture
    def chunking_service(self, mock_paper_repository):
        """Create AcademicChunkingService with mocked dependencies."""
        return AcademicChunkingService(mock_paper_repository)

    @pytest.mark.unit
    def test_create_academic_chunks_success(self, chunking_service,
                                            mock_paper_repository):
        """Test successful academic chunking."""
        mock_paper = ResearchPaper(
            id=1,
            title="Research Paper",
            file_path="/path/to/paper.pdf",
            abstract="Abstract content"
        )
        mock_paper_repository.get_by_id.return_value = mock_paper

        # Mock chunk creation
        mock_chunks = [
            AcademicChunk(
                paper_id=1,
                section_title="Introduction",
                content="Introduction content...",
                chunk_index=0,
                semantic_type="introduction"
            ),
            AcademicChunk(
                paper_id=1,
                section_title="Methods",
                content="Methods content...",
                chunk_index=1,
                semantic_type="methodology"
            )
        ]

        with patch.object(chunking_service, '_extract_academic_sections',
                          return_value=mock_chunks):
            result = chunking_service.create_academic_chunks(
                paper_id=1,
                strategy="hybrid",
                optimization_level="intermediate"
            )

            assert len(result) == 2
            assert result[0].section_title == "Introduction"
            assert result[1].section_title == "Methods"
            assert result[0].semantic_type == "introduction"

    @pytest.mark.unit
    def test_create_chunks_paper_not_found(self, chunking_service,
                                           mock_paper_repository):
        """Test chunking fails when paper doesn't exist."""
        mock_paper_repository.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Paper .* not found"):
            chunking_service.create_academic_chunks(paper_id=999)

    @pytest.mark.unit
    def test_create_chunks_invalid_strategy(self, chunking_service,
                                            mock_paper_repository):
        """Test chunking fails with invalid strategy."""
        mock_paper_repository.get_by_id.return_value = ResearchPaper(
            id=1, title="Test")

        with pytest.raises(ValueError, match="Invalid chunking strategy"):
            chunking_service.create_academic_chunks(
                paper_id=1,
                strategy="invalid_strategy"
            )

    @pytest.mark.unit
    def test_optimize_chunks_success(self, chunking_service):
        """Test successful chunk optimization."""
        original_chunks = [
            AcademicChunk(
                paper_id=1,
                section_title="Introduction",
                content="Very long introduction content that should be split...",
                chunk_index=0
            )
        ]

        # Mock optimization logic
        optimized_chunks = [
            AcademicChunk(
                paper_id=1,
                section_title="Introduction - Part 1",
                content="First part of introduction...",
                chunk_index=0
            ),
            AcademicChunk(
                paper_id=1,
                section_title="Introduction - Part 2",
                content="Second part of introduction...",
                chunk_index=1
            )
        ]

        with patch.object(chunking_service, '_optimize_chunk_boundaries',
                          return_value=optimized_chunks):
            result = chunking_service.optimize_chunks(
                chunks=original_chunks,
                optimization_level="advanced"
            )

            assert len(result) == 2
            assert "Part 1" in result[0].section_title
            assert "Part 2" in result[1].section_title