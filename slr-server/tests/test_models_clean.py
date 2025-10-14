"""
Unit tests for domain models in SLR MCP Server.

Tests domain model validation, serialization, and business logic
following Clean Architecture principles.
"""

import pytest
from datetime import datetime

from models import (
    ResearchPaper, AcademicChunk, Citation, QualityAssessment,
    ResearchQuestion, ResearchHypothesis, EvidenceItem, Author,
    Journal, QualityFramework, QuestionFramework,
    HypothesisType, EvidenceType, StudyType
)


class TestResearchPaper:
    """Test ResearchPaper model."""

    @pytest.mark.unit
    def test_research_paper_creation_valid(self):
        """Test creating valid research paper."""
        paper = ResearchPaper(
            title="Machine Learning in Healthcare",
            doi="10.1000/123456789",
            abstract="This paper examines ML applications in healthcare.",
            publication_year=2023,
            language="en",
            study_type=StudyType.EXPERIMENTAL
        )

        assert paper.title == "Machine Learning in Healthcare"
        assert paper.doi == "10.1000/123456789"
        assert paper.publication_year == 2023
        assert paper.language == "en"
        assert paper.study_type == StudyType.EXPERIMENTAL
        assert isinstance(paper.created_at, datetime)

    @pytest.mark.unit
    def test_research_paper_validation_title_required(self):
        """Test that title is required."""
        with pytest.raises(ValueError, match="Title is required"):
            ResearchPaper(title="")

    @pytest.mark.unit
    def test_research_paper_validation_doi_format(self):
        """Test DOI format validation."""
        with pytest.raises(ValueError, match="DOI must be at least"):
            ResearchPaper(
                title="Valid Title",
                doi="invalid"
            )

    @pytest.mark.unit
    def test_research_paper_validation_year_range(self):
        """Test publication year validation."""
        with pytest.raises(
            ValueError, match="Publication year must be between 1800"
        ):
            ResearchPaper(
                title="Valid Title",
                publication_year=1799
            )

        with pytest.raises(
            ValueError, match="Publication year must be between 1800"
        ):
            ResearchPaper(
                title="Valid Title",
                publication_year=2050
            )

    @pytest.mark.unit
    def test_research_paper_keywords_serialization(self):
        """Test keywords list serialization."""
        paper = ResearchPaper(
            title="Test Paper",
            keywords=["machine learning", "healthcare", "AI"]
        )

        assert paper.keywords == ["machine learning", "healthcare", "AI"]

    @pytest.mark.unit
    def test_research_paper_statistical_methods_validation(self):
        """Test statistical methods validation."""
        paper = ResearchPaper(
            title="Test Paper",
            statistical_methods=["t-test", "ANOVA", "regression"]
        )

        assert "t-test" in paper.statistical_methods
        assert "ANOVA" in paper.statistical_methods
        assert "regression" in paper.statistical_methods


class TestAuthor:
    """Test Author model."""

    @pytest.mark.unit
    def test_author_creation_valid(self):
        """Test creating valid author."""
        author = Author(
            name="Dr. Jane Smith",
            orcid="0000-0002-1825-0097",
            email="jane.smith@university.edu",
            affiliation="University of Technology"
        )

        assert author.name == "Dr. Jane Smith"
        assert author.orcid == "0000-0002-1825-0097"
        assert author.email == "jane.smith@university.edu"
        assert author.affiliation == "University of Technology"

    @pytest.mark.unit
    def test_author_validation_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValueError, match="Name is required"):
            Author(name="")

    @pytest.mark.unit
    def test_author_validation_orcid_format(self):
        """Test ORCID format validation."""
        with pytest.raises(ValueError, match="Invalid ORCID format"):
            Author(
                name="Dr. Jane Smith",
                orcid="invalid-orcid"
            )

    @pytest.mark.unit
    def test_author_citation_metrics_validation(self):
        """Test citation metrics must be non-negative."""
        with pytest.raises(ValueError, match="H-index must be non-negative"):
            Author(
                name="Dr. Jane Smith",
                h_index=-1
            )

        with pytest.raises(
            ValueError, match="Citation count must be non-negative"
        ):
            Author(
                name="Dr. Jane Smith",
                citation_count=-100
            )


class TestQualityAssessment:
    """Test QualityAssessment model."""

    @pytest.mark.unit
    def test_quality_assessment_score_validation(self):
        """Test score validation."""
        with pytest.raises(
            ValueError, match="Overall score must be between 0.0 and 100.0"
        ):
            QualityAssessment(
                paper_id=1,
                framework=QualityFramework.PRISMA,
                reviewer_id="reviewer_001",
                overall_score=150.0
            )

    @pytest.mark.unit
    def test_quality_assessment_inter_rater_reliability(self):
        """Test inter-rater reliability validation."""
        with pytest.raises(
            ValueError, match="Inter-rater reliability must be between"
        ):
            QualityAssessment(
                paper_id=1,
                framework=QualityFramework.PRISMA,
                reviewer_id="reviewer_001",
                overall_score=85.0,
                inter_rater_reliability=1.5
            )


class TestResearchQuestion:
    """Test ResearchQuestion model."""

    @pytest.mark.unit
    def test_research_question_pico_creation(self):
        """Test creating PICO research question."""
        question = ResearchQuestion(
            question_text="How effective is ML in improving accuracy?",
            framework=QuestionFramework.PICO,
            population="Healthcare patients",
            intervention="Machine learning algorithms",
            comparison="Traditional diagnostic methods",
            outcome="Diagnostic accuracy"
        )

        assert question.framework == QuestionFramework.PICO
        assert question.population == "Healthcare patients"
        assert question.intervention == "Machine learning algorithms"
        assert question.comparison == "Traditional diagnostic methods"
        assert question.outcome == "Diagnostic accuracy"

    @pytest.mark.unit
    def test_research_question_validation_score(self):
        """Test validation score range."""
        with pytest.raises(
            ValueError, match="Validation score must be between 0.0 and 100.0"
        ):
            ResearchQuestion(
                question_text="Valid question?",
                validation_score=150.0
            )


class TestResearchHypothesis:
    """Test ResearchHypothesis model."""

    @pytest.mark.unit
    def test_hypothesis_creation(self):
        """Test creating research hypothesis."""
        hypothesis = ResearchHypothesis(
            hypothesis_text="ML algorithms show higher accuracy",
            hypothesis_type=HypothesisType.PRIMARY,
            direction="directional",
            statistical_test="t-test",
            significance_level=0.05
        )

        assert hypothesis.hypothesis_type == HypothesisType.PRIMARY
        assert hypothesis.direction == "directional"
        assert hypothesis.statistical_test == "t-test"
        assert hypothesis.significance_level == 0.05

    @pytest.mark.unit
    def test_hypothesis_significance_level_validation(self):
        """Test significance level validation."""
        with pytest.raises(
            ValueError, match="Significance level must be between 0.0 and 1.0"
        ):
            ResearchHypothesis(
                hypothesis_text="Valid hypothesis",
                significance_level=1.5
            )


class TestEvidenceItem:
    """Test EvidenceItem model."""

    @pytest.mark.unit
    def test_evidence_item_creation(self):
        """Test creating evidence item."""
        evidence = EvidenceItem(
            paper_id=1,
            evidence_text="ML model achieved 95% accuracy vs 78%",
            evidence_type=EvidenceType.STATISTICAL,
            strength="strong",
            quality="high",
            relevance=0.95,
            supporting=True
        )

        assert evidence.paper_id == 1
        assert evidence.evidence_type == EvidenceType.STATISTICAL
        assert evidence.strength == "strong"
        assert evidence.quality == "high"
        assert evidence.relevance == 0.95
        assert evidence.supporting is True

    @pytest.mark.unit
    def test_evidence_relevance_validation(self):
        """Test relevance score validation."""
        with pytest.raises(
            ValueError, match="Relevance must be between 0.0 and 1.0"
        ):
            EvidenceItem(
                paper_id=1,
                evidence_text="Valid evidence",
                evidence_type=EvidenceType.STATISTICAL,
                relevance=1.5
            )


class TestCitation:
    """Test Citation model."""

    @pytest.mark.unit
    def test_citation_creation_internal(self):
        """Test creating internal citation."""
        citation = Citation(
            citing_paper_id=1,
            cited_paper_id=2,
            citation_text="Smith et al. demonstrated improvements",
            citation_type="background",
            relevance_score=0.85
        )

        assert citation.citing_paper_id == 1
        assert citation.cited_paper_id == 2
        assert citation.citation_type == "background"
        assert citation.relevance_score == 0.85

    @pytest.mark.unit
    def test_citation_validation_reference_required(self):
        """Test that either internal or external reference is required."""
        with pytest.raises(
            ValueError,
            match="Either cited paper ID or external citation info is required"
        ):
            Citation(citing_paper_id=1)

    @pytest.mark.unit
    def test_citation_relevance_score_validation(self):
        """Test relevance score validation."""
        with pytest.raises(
            ValueError, match="Relevance score must be between 0.0 and 1.0"
        ):
            Citation(
                citing_paper_id=1,
                cited_paper_id=2,
                relevance_score=1.5
            )


class TestModelIntegrations:
    """Test interactions between models."""

    @pytest.mark.unit
    def test_hypothesis_evidence_chain(self):
        """Test hypothesis-evidence relationship chain."""
        question = ResearchQuestion(
            question_text="Research question about ML effectiveness"
        )

        hypothesis = ResearchHypothesis(
            research_question_id=question.id,
            hypothesis_text="ML is more effective than traditional methods",
            hypothesis_type=HypothesisType.PRIMARY
        )

        evidence = EvidenceItem(
            paper_id=1,
            hypothesis_id=hypothesis.id,
            evidence_text="Supporting statistical evidence",
            evidence_type=EvidenceType.STATISTICAL,
            supporting=True,
            strength="strong"
        )

        assert evidence.hypothesis_id == hypothesis.id
        assert evidence.supporting is True
        assert hypothesis.research_question_id == question.id

    @pytest.mark.unit
    def test_quality_assessment_completeness(self):
        """Test quality assessment with complete scoring."""
        assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            overall_score=87.5,
            study_design_score=90.0,
            methodology_score=85.0,
            data_quality_score=90.0,
            reporting_score=85.0,
            statistical_analysis_score=90.0,
            risk_of_bias="low",
            grade_level="high"
        )

        # Calculate weighted average
        scores = [
            assessment.study_design_score,
            assessment.methodology_score,
            assessment.data_quality_score,
            assessment.reporting_score,
            assessment.statistical_analysis_score
        ]
        calculated_average = sum(scores) / len(scores)

        # Allow some variance
        assert abs(assessment.overall_score - calculated_average) < 5.0