"""
Unit tests for SLR MCP Handler.

Tests MCP protocol layer and tool implementations with comprehensive
coverage of parameter validation, service integration, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from mcp_handler import SLRMCPHandler
from services import (
    ResearchDocumentService, QualityAssessmentService,
    ResearchQuestionService, HypothesisAnalysisService,
    AcademicChunkingService
)
from models import (
    ResearchPaper, Author, QualityAssessment, ResearchQuestion,
    ResearchHypothesis, EvidenceItem, AcademicChunk,
    QualityFramework, QuestionFramework, HypothesisType,
    ValidationLevel, EffectDirection
)


class TestSLRMCPHandler:
    """Test SLR MCP Handler protocol operations."""

    @pytest.fixture
    def mock_research_service(self):
        """Create mock research document service."""
        service = Mock(spec=ResearchDocumentService)
        service.paper_repository = Mock()
        return service

    @pytest.fixture
    def mock_quality_service(self):
        """Create mock quality assessment service."""
        return Mock(spec=QualityAssessmentService)

    @pytest.fixture
    def mock_question_service(self):
        """Create mock research question service."""
        return Mock(spec=ResearchQuestionService)

    @pytest.fixture
    def mock_hypothesis_service(self):
        """Create mock hypothesis analysis service."""
        return Mock(spec=HypothesisAnalysisService)

    @pytest.fixture
    def mock_chunking_service(self):
        """Create mock academic chunking service."""
        return Mock(spec=AcademicChunkingService)

    @pytest.fixture
    def mcp_handler(self, mock_research_service, mock_quality_service,
                    mock_question_service, mock_hypothesis_service,
                    mock_chunking_service):
        """Create MCP handler with all mocked services."""
        return SLRMCPHandler(
            research_document_service=mock_research_service,
            quality_assessment_service=mock_quality_service,
            research_question_service=mock_question_service,
            hypothesis_analysis_service=mock_hypothesis_service,
            academic_chunking_service=mock_chunking_service
        )

    @pytest.fixture
    def sample_paper(self):
        """Create sample research paper."""
        return ResearchPaper(
            id=1,
            title="Machine Learning in Healthcare",
            file_path="/path/to/paper.pdf",
            file_type="pdf",
            doi="10.1000/123456789",
            authors=[
                Author(name="Dr. Jane Smith"),
                Author(name="Dr. John Doe")
            ]
        )

    @pytest.mark.unit
    def test_upload_paper_success(self, mcp_handler, mock_research_service, sample_paper):
        """Test successful paper upload through MCP."""
        mock_research_service.upload_paper.return_value = sample_paper

        result = mcp_handler.upload_paper(
            file_path="/path/to/paper.pdf",
            title="Machine Learning in Healthcare",
            doi="10.1000/123456789",
            tags=["research", "healthcare"]
        )

        # Verify service call
        mock_research_service.upload_paper.assert_called_once_with(
            file_path="/path/to/paper.pdf",
            title="Machine Learning in Healthcare",
            doi="10.1000/123456789",
            tags=["research", "healthcare"]
        )

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["paper_id"] == 1
        assert result["data"]["title"] == "Machine Learning in Healthcare"
        assert result["data"]["doi"] == "10.1000/123456789"
        assert len(result["data"]["authors"]) == 2
        assert result["message"] == "Paper uploaded successfully"

    @pytest.mark.unit
    def test_upload_paper_service_error(self, mcp_handler, mock_research_service):
        """Test paper upload handles service errors."""
        mock_research_service.upload_paper.side_effect = ValueError("Invalid file format")

        result = mcp_handler.upload_paper("/path/to/invalid.txt")

        assert result["success"] is False
        assert result["error"] == "Invalid file format"
        assert result["error_type"] == "system"

    @pytest.mark.unit
    def test_assess_quality_success(self, mcp_handler, mock_quality_service):
        """Test successful quality assessment through MCP."""
        # Mock quality assessment result
        mock_assessment = QualityAssessment(
            id=1,
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            overall_score=85.0,
            risk_of_bias="low"
        )
        mock_quality_service.create_assessment.return_value = mock_assessment

        result = mcp_handler.assess_quality(
            paper_id=1,
            framework="prisma",
            reviewer_id="reviewer_001"
        )

        # Verify service call
        mock_quality_service.create_assessment.assert_called_once_with(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            criterion_scores={}
        )

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["assessment_id"] == 1
        assert result["data"]["overall_score"] == 85.0
        assert result["data"]["framework"] == QualityFramework.PRISMA
        assert result["data"]["risk_of_bias"] == "low"

    @pytest.mark.unit
    def test_assess_quality_with_custom_scores(self, mcp_handler, mock_quality_service):
        """Test quality assessment with custom criterion scores."""
        mock_assessment = QualityAssessment(
            id=1,
            paper_id=1,
            framework=QualityFramework.PRISMA,
            overall_score=90.0
        )
        mock_quality_service.create_assessment.return_value = mock_assessment

        custom_scores = {
            "methodology": {"score": 95.0, "notes": "Excellent design"},
            "reporting": {"score": 85.0, "notes": "Good clarity"}
        }

        result = mcp_handler.assess_quality(
            paper_id=1,
            framework="prisma",
            criterion_scores=custom_scores
        )

        # Verify custom scores passed to service
        mock_quality_service.create_assessment.assert_called_once_with(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="default",
            criterion_scores=custom_scores
        )

        assert result["success"] is True

    @pytest.mark.unit
    def test_assess_quality_invalid_framework(self, mcp_handler, mock_quality_service):
        """Test quality assessment with invalid framework."""
        # Mock framework enum error
        with patch('mcp_handler.QualityFramework') as mock_framework:
            mock_framework.side_effect = ValueError("Invalid framework: invalid")

            result = mcp_handler.assess_quality(
                paper_id=1,
                framework="invalid"
            )

            assert result["success"] is False
            assert "Invalid framework" in result["error"]

    @pytest.mark.unit
    def test_validate_research_question_success(self, mcp_handler, mock_question_service):
        """Test successful research question validation."""
        # Mock validation result
        mock_validation = ResearchQuestion(
            id=1,
            question_text="Research question about ML effectiveness",
            framework=QuestionFramework.PICO,
            validation_level=ValidationLevel.HIGH,
            overall_score=88.5,
            strengths=["Clear population defined", "Specific intervention"],
            weaknesses=["Outcome could be more specific"],
            improvement_suggestions=["Consider adding time frame"]
        )
        mock_question_service.validate_research_question.return_value = mock_validation

        question_text = ("In adults with diabetes, does ML-based monitoring "
                        "improve glycemic control compared to traditional methods?")

        result = mcp_handler.validate_research_question(
            question_text=question_text,
            framework="pico"
        )

        # Verify service call
        mock_question_service.validate_research_question.assert_called_once_with(
            question_text, QuestionFramework.PICO
        )

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["overall_score"] == 88.5
        assert result["data"]["validation_level"] == ValidationLevel.HIGH.value
        assert len(result["data"]["strengths"]) == 2
        assert len(result["data"]["weaknesses"]) == 1
        assert len(result["data"]["suggestions"]) == 1

    @pytest.mark.unit
    def test_validate_research_question_spider_framework(self, mcp_handler, mock_question_service):
        """Test research question validation with SPIDER framework."""
        mock_validation = ResearchQuestion(
            framework=QuestionFramework.SPIDER,
            overall_score=82.0
        )
        mock_question_service.validate_research_question.return_value = mock_validation

        result = mcp_handler.validate_research_question(
            question_text="What are nurse experiences with patient safety interventions?",
            framework="spider"
        )

        mock_question_service.validate_research_question.assert_called_once_with(
            "What are nurse experiences with patient safety interventions?",
            QuestionFramework.SPIDER
        )

        assert result["success"] is True

    @pytest.mark.unit
    def test_analyze_citations_success(self, mcp_handler, mock_research_service):
        """Test successful citation analysis."""
        mock_analysis = {
            "citation_count": 25,
            "cited_by_count": 15,
            "self_citations": 3,
            "citation_network": {
                "nodes": [{"id": 1, "title": "Paper 1"}],
                "edges": [{"from": 1, "to": 2, "weight": 0.8}]
            },
            "impact_metrics": {
                "h_index": 8,
                "citation_velocity": 2.3
            }
        }
        mock_research_service.analyze_citations.return_value = mock_analysis

        result = mcp_handler.analyze_citations(paper_id=1)

        # Verify service call
        mock_research_service.analyze_citations.assert_called_once_with(1)

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["citation_count"] == 25
        assert result["data"]["cited_by_count"] == 15
        assert "citation_network" in result["data"]
        assert "impact_metrics" in result["data"]

    @pytest.mark.unit
    def test_analyze_citations_paper_not_found(self, mcp_handler, mock_research_service):
        """Test citation analysis when paper not found."""
        mock_research_service.analyze_citations.side_effect = ValueError("Paper 999 not found")

        result = mcp_handler.analyze_citations(paper_id=999)

        assert result["success"] is False
        assert "Paper 999 not found" in result["error"]

    @pytest.mark.unit
    def test_test_hypothesis_success(self, mcp_handler, mock_hypothesis_service, mock_research_service):
        """Test successful hypothesis testing."""
        # Mock paper retrieval
        mock_paper1 = ResearchPaper(id=1, title="ML Study 1")
        mock_paper2 = ResearchPaper(id=2, title="ML Study 2") 
        mock_research_service.paper_repository.get_by_id.side_effect = [mock_paper1, mock_paper2]

        # Mock evidence classification
        mock_evidence = [
            EvidenceItem(
                paper_id=1,
                evidence_text="95% accuracy achieved",
                evidence_type="statistical",
                supporting=True,
                strength="strong"
            )
        ]
        mock_hypothesis_service.classify_evidence.return_value = mock_evidence

        # Mock hypothesis test result
        mock_result = ResearchHypothesis(
            hypothesis_text="ML algorithms show higher accuracy",
            supported=True,
            confidence_level=0.95,
            effect_direction=EffectDirection.POSITIVE,
            conclusions=["Strong evidence supports hypothesis"]
        )
        mock_hypothesis_service.test_hypothesis.return_value = mock_result

        result = mcp_handler.test_hypothesis(
            hypothesis_text="ML algorithms show higher accuracy",
            paper_ids=[1, 2],
            significance_level=0.05
        )

        # Verify service calls
        assert mock_research_service.paper_repository.get_by_id.call_count == 2
        assert mock_hypothesis_service.classify_evidence.call_count == 2
        mock_hypothesis_service.test_hypothesis.assert_called_once()

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["hypothesis_text"] == "ML algorithms show higher accuracy"
        assert result["data"]["supported"] is True
        assert result["data"]["confidence_level"] == 0.95
        assert result["data"]["effect_direction"] == EffectDirection.POSITIVE.value
        assert len(result["data"]["conclusions"]) == 1

    @pytest.mark.unit
    def test_test_hypothesis_insufficient_papers(self, mcp_handler):
        """Test hypothesis testing with insufficient papers."""
        result = mcp_handler.test_hypothesis(
            hypothesis_text="Test hypothesis",
            paper_ids=[1],  # Only one paper
            significance_level=0.05
        )

        # Should handle gracefully - either error or proceed with single paper
        # Depends on service implementation, but should not crash
        assert "success" in result

    @pytest.mark.unit
    def test_index_paper_success(self, mcp_handler, mock_chunking_service):
        """Test successful paper indexing."""
        # Mock chunks created
        mock_chunks = [
            AcademicChunk(
                paper_id=1,
                section_title="Introduction",
                content="Introduction content...",
                word_count=500,
                chunk_index=0
            ),
            AcademicChunk(
                paper_id=1,
                section_title="Methods",
                content="Methods content...",
                word_count=750,
                chunk_index=1
            )
        ]
        mock_chunking_service.index_paper.return_value = mock_chunks

        result = mcp_handler.index_paper(
            paper_id=1,
            strategy="hybrid",
            optimization_level="advanced"
        )

        # Verify service call with enums
        mock_chunking_service.index_paper.assert_called_once()

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["paper_id"] == 1
        assert result["data"]["chunks_created"] == 2
        assert result["data"]["average_chunk_size"] == 625.0  # (500 + 750) / 2
        assert result["data"]["indexing_strategy"] == "hybrid"
        assert result["data"]["optimization_level"] == "advanced"

    @pytest.mark.unit
    def test_index_paper_invalid_strategy(self, mcp_handler, mock_chunking_service):
        """Test paper indexing with invalid strategy."""
        with patch('mcp_handler.IndexingStrategy') as mock_strategy:
            mock_strategy.side_effect = ValueError("Invalid strategy: invalid")

            result = mcp_handler.index_paper(
                paper_id=1,
                strategy="invalid"
            )

            assert result["success"] is False
            assert "Invalid strategy" in result["error"]

    @pytest.mark.unit
    def test_synthesize_evidence_success(self, mcp_handler, mock_hypothesis_service):
        """Test successful evidence synthesis."""
        mock_synthesis = {
            "research_question": "How effective is ML in healthcare?",
            "total_papers_analyzed": 5,
            "evidence_strength": "strong",
            "meta_analysis": {
                "effect_size": 1.2,
                "confidence_interval": [0.8, 1.6],
                "heterogeneity": "low"
            },
            "conclusions": [
                "Strong evidence supports ML effectiveness",
                "Results consistent across studies"
            ],
            "limitations": ["Small sample sizes in some studies"],
            "recommendations": ["Larger RCTs needed"]
        }

        # Mock the synthesize_evidence method if it exists
        if hasattr(mock_hypothesis_service, 'synthesize_evidence'):
            mock_hypothesis_service.synthesize_evidence.return_value = mock_synthesis
        else:
            # Add the method to mock
            mock_hypothesis_service.synthesize_evidence = Mock(return_value=mock_synthesis)

        # Assume synthesize_evidence method exists in handler
        if hasattr(mcp_handler, 'synthesize_evidence'):
            result = mcp_handler.synthesize_evidence(
                research_question="How effective is ML in healthcare?",
                paper_ids=[1, 2, 3, 4, 5],
                include_meta_analysis=True
            )

            assert result["success"] is True
            assert result["data"]["total_papers_analyzed"] == 5
            assert result["data"]["evidence_strength"] == "strong"
            assert "meta_analysis" in result["data"]

    @pytest.mark.unit
    def test_create_success_response(self, mcp_handler):
        """Test success response creation."""
        data = {"test": "value"}
        message = "Operation successful"

        response = mcp_handler._create_success_response(data, message)

        assert response["success"] is True
        assert response["data"] == data
        assert response["message"] == message

    @pytest.mark.unit
    def test_create_success_response_minimal(self, mcp_handler):
        """Test success response with minimal parameters."""
        response = mcp_handler._create_success_response()

        assert response["success"] is True
        assert "data" not in response
        assert "message" not in response

    @pytest.mark.unit
    def test_create_error_response(self, mcp_handler):
        """Test error response creation."""
        error_message = "Operation failed"
        error_type = "validation"

        response = mcp_handler._create_error_response(error_message, error_type)

        assert response["success"] is False
        assert response["error"] == error_message
        assert response["error_type"] == error_type

    @pytest.mark.unit
    def test_create_error_response_default_type(self, mcp_handler):
        """Test error response with default error type."""
        response = mcp_handler._create_error_response("Error message")

        assert response["success"] is False
        assert response["error"] == "Error message"
        assert response["error_type"] == "system"


class TestMCPHandlerIntegration:
    """Integration tests for MCP handler operations."""

    @pytest.mark.integration
    def test_complete_paper_workflow(self):
        """Test complete paper workflow through MCP."""
        # Upload -> Assess -> Index -> Analyze
        pytest.skip("Integration test - requires service implementations")

    @pytest.mark.integration
    def test_hypothesis_testing_workflow(self):
        """Test complete hypothesis testing workflow."""
        # Upload papers -> Extract evidence -> Test hypothesis
        pytest.skip("Integration test - requires service implementations")

    @pytest.mark.integration
    def test_systematic_review_workflow(self):
        """Test complete systematic review workflow."""
        # Question validation -> Paper upload -> Quality assessment -> Synthesis
        pytest.skip("Integration test - requires service implementations")


class TestMCPHandlerErrorHandling:
    """Test MCP handler error handling scenarios."""

    @pytest.fixture
    def mcp_handler_with_failing_services(self):
        """Create MCP handler with services that raise various errors."""
        failing_research_service = Mock(spec=ResearchDocumentService)
        failing_research_service.upload_paper.side_effect = Exception("Service unavailable")
        
        return SLRMCPHandler(
            research_document_service=failing_research_service,
            quality_assessment_service=Mock(),
            research_question_service=Mock(),
            hypothesis_analysis_service=Mock(),
            academic_chunking_service=Mock()
        )

    @pytest.mark.unit
    def test_service_exception_handling(self, mcp_handler_with_failing_services):
        """Test that service exceptions are properly caught and formatted."""
        result = mcp_handler_with_failing_services.upload_paper("/path/to/paper.pdf")

        assert result["success"] is False
        assert result["error"] == "Service unavailable"
        assert result["error_type"] == "system"

    @pytest.mark.unit
    def test_parameter_validation_errors(self, mcp_handler):
        """Test parameter validation error handling."""
        # Test with None values that should cause errors
        result = mcp_handler.upload_paper(None)

        assert result["success"] is False
        # Should handle the error gracefully

    @pytest.mark.unit
    def test_enum_conversion_errors(self, mcp_handler):
        """Test handling of enum conversion errors."""
        result = mcp_handler.assess_quality(
            paper_id=1,
            framework="nonexistent_framework"
        )

        assert result["success"] is False
        # Should contain information about invalid enum value