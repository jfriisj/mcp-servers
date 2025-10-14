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
        with pytest.raises(ValueError, match="DOI must be at least 10 characters"):
            ResearchPaper(
                title="Valid Title",
                doi="invalid"
            )

    @pytest.mark.unit
    def test_research_paper_validation_year_range(self):
        """Test publication year validation."""
        with pytest.raises(
            ValueError, match="Publication year must be between 1800 and"
        ):
            ResearchPaper(
                title="Valid Title",
                publication_year=1799
            )

        with pytest.raises(
            ValueError, match="Publication year must be between 1800 and"
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

    @pytest.mark.unit
    def test_research_paper_inclusion_exclusion(self):
        """Test inclusion/exclusion logic."""
        paper = ResearchPaper(
            title="Test Paper",
            included_in_review=False,
            exclusion_reason="Language not English"
        )
        
        assert not paper.included_in_review
        assert paper.exclusion_reason == "Language not English"


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
    def test_author_validation_email_format(self):
        """Test email format validation."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Author(
                name="Dr. Jane Smith",
                email="invalid-email"
            )

    @pytest.mark.unit
    def test_author_research_areas(self):
        """Test research areas handling."""
        author = Author(
            name="Dr. Jane Smith",
            research_areas=["machine learning", "healthcare informatics"]
        )
        
        assert "machine learning" in author.research_areas
        assert "healthcare informatics" in author.research_areas

    @pytest.mark.unit
    def test_author_citation_metrics(self):
        """Test citation metrics validation."""
        author = Author(
            name="Dr. Jane Smith",
            h_index=25,
            citation_count=1500
        )
        
        assert author.h_index == 25
        assert author.citation_count == 1500

    @pytest.mark.unit
    def test_author_citation_metrics_validation(self):
        """Test citation metrics must be non-negative."""
        with pytest.raises(ValueError, match="H-index must be non-negative"):
            Author(
                name="Dr. Jane Smith",
                h_index=-1
            )
        
        with pytest.raises(ValueError, match="Citation count must be non-negative"):
            Author(
                name="Dr. Jane Smith",
                citation_count=-100
            )


class TestJournal:
    """Test Journal model."""

    @pytest.mark.unit
    def test_journal_creation_valid(self):
        """Test creating valid journal."""
        journal = Journal(
            name="Journal of Healthcare Informatics",
            issn="1234-5678",
            publisher="Academic Press",
            impact_factor=4.5
        )
        
        assert journal.name == "Journal of Healthcare Informatics"
        assert journal.issn == "1234-5678"
        assert journal.publisher == "Academic Press"
        assert journal.impact_factor == 4.5

    @pytest.mark.unit
    def test_journal_validation_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValueError, match="Name is required"):
            Journal(name="")

    @pytest.mark.unit
    def test_journal_validation_issn_format(self):
        """Test ISSN format validation."""
        with pytest.raises(ValueError, match="Invalid ISSN format"):
            Journal(
                name="Test Journal",
                issn="invalid-issn"
            )

    @pytest.mark.unit
    def test_journal_validation_impact_factor(self):
        """Test impact factor validation."""
        with pytest.raises(ValueError, match="Impact factor must be non-negative"):
            Journal(
                name="Test Journal",
                impact_factor=-1.0
            )

    @pytest.mark.unit
    def test_journal_quartile_validation(self):
        """Test quartile validation."""
        journal = Journal(
            name="Test Journal",
            quartile="Q1"
        )
        assert journal.quartile == "Q1"
        
        with pytest.raises(ValueError, match="Quartile must be Q1, Q2, Q3, or Q4"):
            Journal(
                name="Test Journal",
                quartile="Q5"
            )


class TestAcademicChunk:
    """Test AcademicChunk model."""

    @pytest.mark.unit
    def test_chunk_creation_valid(self):
        """Test creating valid academic chunk."""
        chunk = AcademicChunk(
            paper_id=1,
            chunk_index=0,
            chunk_type="abstract",
            content="This is the abstract content",
            word_count=5
        )
        
        assert chunk.paper_id == 1
        assert chunk.chunk_index == 0
        assert chunk.chunk_type == "abstract"
        assert chunk.content == "This is the abstract content"
        assert chunk.word_count == 5

    @pytest.mark.unit
    def test_chunk_validation_content_required(self):
        """Test that content is required."""
        with pytest.raises(ValueError, match="Content is required"):
            AcademicChunk(
                paper_id=1,
                chunk_index=0,
                content=""
            )

    @pytest.mark.unit
    def test_chunk_validation_chunk_index(self):
        """Test chunk index validation."""
        with pytest.raises(ValueError, match="Chunk index must be non-negative"):
            AcademicChunk(
                paper_id=1,
                chunk_index=-1,
                content="Valid content"
            )

    @pytest.mark.unit
    def test_chunk_semantic_keywords(self):
        """Test semantic keywords handling."""
        chunk = AcademicChunk(
            paper_id=1,
            chunk_index=0,
            content="Machine learning applications in healthcare",
            semantic_keywords=["machine learning", "healthcare", "applications"]
        )
        
        assert "machine learning" in chunk.semantic_keywords
        assert "healthcare" in chunk.semantic_keywords

    @pytest.mark.unit
    def test_chunk_page_validation(self):
        """Test page number validation."""
        chunk = AcademicChunk(
            paper_id=1,
            chunk_index=0,
            content="Valid content",
            start_page=5,
            end_page=3
        )
        
        with pytest.raises(ValueError, match="End page must be greater than or equal to start page"):
            chunk.validate()

    @pytest.mark.unit
    def test_chunk_research_concepts(self):
        """Test research concepts extraction."""
        chunk = AcademicChunk(
            paper_id=1,
            chunk_index=0,
            content="Deep learning models for medical diagnosis",
            research_concepts=["deep learning", "medical diagnosis", "neural networks"]
        )
        
        assert len(chunk.research_concepts) == 3
        assert "deep learning" in chunk.research_concepts


class TestCitation:
    """Test Citation model."""

    @pytest.mark.unit
    def test_citation_creation_internal(self):
        """Test creating internal citation."""
        citation = Citation(
            citing_paper_id=1,
            cited_paper_id=2,
            citation_text="Smith et al. demonstrated significant improvements",
            citation_type="background",
            relevance_score=0.85
        )
        
        assert citation.citing_paper_id == 1
        assert citation.cited_paper_id == 2
        assert citation.citation_type == "background"
        assert citation.relevance_score == 0.85

    @pytest.mark.unit
    def test_citation_creation_external(self):
        """Test creating external citation."""
        citation = Citation(
            citing_paper_id=1,
            external_title="External Research Paper",
            external_authors="Johnson, K., Lee, M.",
            external_year=2022,
            external_doi="10.1000/external"
        )
        
        assert citation.citing_paper_id == 1
        assert citation.external_title == "External Research Paper"
        assert citation.external_authors == "Johnson, K., Lee, M."
        assert citation.external_year == 2022

    @pytest.mark.unit
    def test_citation_validation_citing_paper_required(self):
        """Test that citing paper is required."""
        with pytest.raises(ValueError, match="Citing paper ID is required"):
            Citation(citing_paper_id=0)

    @pytest.mark.unit
    def test_citation_validation_reference_required(self):
        """Test that either internal or external reference is required."""
        with pytest.raises(ValueError, match="Either cited paper ID or external citation info is required"):
            Citation(citing_paper_id=1)

    @pytest.mark.unit
    def test_citation_relevance_score_validation(self):
        """Test relevance score validation."""
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            Citation(
                citing_paper_id=1,
                cited_paper_id=2,
                relevance_score=1.5
            )

    @pytest.mark.unit
    def test_citation_sentiment_validation(self):
        """Test sentiment validation."""
        citation = Citation(
            citing_paper_id=1,
            cited_paper_id=2,
            sentiment="positive"
        )
        assert citation.sentiment == "positive"
        
        with pytest.raises(ValueError, match="Sentiment must be"):
            Citation(
                citing_paper_id=1,
                cited_paper_id=2,
                sentiment="invalid"
            )


class TestQualityAssessment:
    """Test QualityAssessment model."""

    @pytest.mark.unit
    def test_quality_assessment_creation(self):
        """Test creating quality assessment."""
        assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            overall_score=85.0,
            risk_of_bias="low"
        )
        
        assert assessment.paper_id == 1
        assert assessment.framework == QualityFramework.PRISMA
        assert assessment.reviewer_id == "reviewer_001"
        assert assessment.overall_score == 85.0
        assert assessment.risk_of_bias == "low"

    @pytest.mark.unit
    def test_quality_assessment_score_validation(self):
        """Test score validation."""
        with pytest.raises(ValueError, match="Overall score must be between 0.0 and 100.0"):
            QualityAssessment(
                paper_id=1,
                framework=QualityFramework.PRISMA,
                reviewer_id="reviewer_001",
                overall_score=150.0
            )

    @pytest.mark.unit
    def test_quality_assessment_framework_validation(self):
        """Test framework validation."""
        assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.STROBE,
            reviewer_id="reviewer_001",
            overall_score=80.0
        )
        assert assessment.framework == QualityFramework.STROBE

    @pytest.mark.unit
    def test_quality_assessment_criterion_scores(self):
        """Test criterion scores handling."""
        criterion_scores = {
            "methodology": {"score": 90, "notes": "Excellent"},
            "data_quality": {"score": 85, "notes": "Good"}
        }
        
        assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="reviewer_001",
            overall_score=87.5,
            criterion_scores=criterion_scores
        )
        
        assert assessment.criterion_scores["methodology"]["score"] == 90
        assert assessment.criterion_scores["data_quality"]["score"] == 85

    @pytest.mark.unit
    def test_quality_assessment_inter_rater_reliability(self):
        """Test inter-rater reliability validation."""
        with pytest.raises(ValueError, match="Inter-rater reliability must be between 0.0 and 1.0"):
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
            question_text="How effective is machine learning in improving diagnostic accuracy?",
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
    def test_research_question_spider_creation(self):
        """Test creating SPIDER research question."""
        question = ResearchQuestion(
            question_text="What are patient experiences with telemedicine?",
            framework=QuestionFramework.SPIDER,
            setting="Healthcare facilities",
            perspective="Patient perspective",
            phenomenon_of_interest="Telemedicine experiences",
            design="Qualitative studies",
            evaluation="Patient satisfaction"
        )
        
        assert question.framework == QuestionFramework.SPIDER
        assert question.setting == "Healthcare facilities"
        assert question.perspective == "Patient perspective"

    @pytest.mark.unit
    def test_research_question_validation_text_required(self):
        """Test that question text is required."""
        with pytest.raises(ValueError, match="Question text is required"):
            ResearchQuestion(question_text="")

    @pytest.mark.unit
    def test_research_question_validation_score(self):
        """Test validation score range."""
        with pytest.raises(ValueError, match="Validation score must be between 0.0 and 100.0"):
            ResearchQuestion(
                question_text="Valid question?",
                validation_score=150.0
            )

    @pytest.mark.unit
    def test_research_question_keywords(self):
        """Test keywords handling."""
        question = ResearchQuestion(
            question_text="How effective is ML in healthcare?",
            keywords_used=["machine learning", "healthcare", "effectiveness"]
        )
        
        assert len(question.keywords_used) == 3
        assert "machine learning" in question.keywords_used


class TestResearchHypothesis:
    """Test ResearchHypothesis model."""

    @pytest.mark.unit
    def test_hypothesis_creation(self):
        """Test creating research hypothesis."""
        hypothesis = ResearchHypothesis(
            hypothesis_text="ML algorithms will show higher accuracy than traditional methods",
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
    def test_hypothesis_validation_text_required(self):
        """Test that hypothesis text is required."""
        with pytest.raises(ValueError, match="Hypothesis text is required"):
            ResearchHypothesis(hypothesis_text="")

    @pytest.mark.unit
    def test_hypothesis_significance_level_validation(self):
        """Test significance level validation."""
        with pytest.raises(ValueError, match="Significance level must be between 0.0 and 1.0"):
            ResearchHypothesis(
                hypothesis_text="Valid hypothesis",
                significance_level=1.5
            )

    @pytest.mark.unit
    def test_hypothesis_variables(self):
        """Test variables handling."""
        hypothesis = ResearchHypothesis(
            hypothesis_text="Algorithm type affects accuracy",
            variables=["algorithm_type", "accuracy_score"],
            dependent_variable="accuracy_score",
            independent_variables=["algorithm_type"]
        )
        
        assert len(hypothesis.variables) == 2
        assert hypothesis.dependent_variable == "accuracy_score"
        assert "algorithm_type" in hypothesis.independent_variables

    @pytest.mark.unit
    def test_hypothesis_test_results(self):
        """Test test results handling."""
        test_results = {
            "statistic": 2.456,
            "p_value": 0.024,
            "effect_size": 0.8,
            "confidence_interval": "95% CI: [0.1, 1.5]"
        }
        
        hypothesis = ResearchHypothesis(
            hypothesis_text="Test hypothesis",
            test_results=test_results,
            p_value=0.024
        )
        
        assert hypothesis.test_results["statistic"] == 2.456
        assert hypothesis.p_value == 0.024


class TestEvidenceItem:
    """Test EvidenceItem model."""

    @pytest.mark.unit
    def test_evidence_item_creation(self):
        """Test creating evidence item."""
        evidence = EvidenceItem(
            paper_id=1,
            evidence_text="ML model achieved 95% accuracy vs 78% for traditional (p<0.001)",
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
    def test_evidence_validation_text_required(self):
        """Test that evidence text is required."""
        with pytest.raises(ValueError, match="Evidence text is required"):
            EvidenceItem(
                paper_id=1,
                evidence_text="",
                evidence_type=EvidenceType.STATISTICAL
            )

    @pytest.mark.unit
    def test_evidence_relevance_validation(self):
        """Test relevance score validation."""
        with pytest.raises(ValueError, match="Relevance must be between 0.0 and 1.0"):
            EvidenceItem(
                paper_id=1,
                evidence_text="Valid evidence",
                evidence_type=EvidenceType.STATISTICAL,
                relevance=1.5
            )

    @pytest.mark.unit
    def test_evidence_statistical_data(self):
        """Test statistical data handling."""
        evidence = EvidenceItem(
            paper_id=1,
            evidence_text="Statistical evidence",
            evidence_type=EvidenceType.STATISTICAL,
            effect_size=0.8,
            confidence_interval="95% CI: [0.6, 1.0]",
            statistical_significance=0.001,
            sample_size=500
        )
        
        assert evidence.effect_size == 0.8
        assert evidence.confidence_interval == "95% CI: [0.6, 1.0]"
        assert evidence.statistical_significance == 0.001
        assert evidence.sample_size == 500

    @pytest.mark.unit
    def test_evidence_validation_workflow(self):
        """Test evidence validation workflow."""
        evidence = EvidenceItem(
            paper_id=1,
            evidence_text="Evidence for validation",
            evidence_type=EvidenceType.QUALITATIVE,
            extraction_method="manual",
            extractor_id="extractor_001",
            verification_status="pending"
        )
        
        assert evidence.extraction_method == "manual"
        assert evidence.extractor_id == "extractor_001"
        assert evidence.verification_status == "pending"

    @pytest.mark.unit
    def test_evidence_grade_assessment(self):
        """Test GRADE rating validation."""
        evidence = EvidenceItem(
            paper_id=1,
            evidence_text="High quality evidence",
            evidence_type=EvidenceType.EXPERIMENTAL,
            grade_rating="high",
            risk_of_bias="low",
            methodological_quality="excellent"
        )
        
        assert evidence.grade_rating == "high"
        assert evidence.risk_of_bias == "low"
        assert evidence.methodological_quality == "excellent"


# ============================================================================
# INTEGRATION TESTS FOR MODEL INTERACTIONS
# ============================================================================

class TestModelIntegrations:
    """Test interactions between models."""

    @pytest.mark.unit
    def test_paper_author_relationship(self):
        """Test paper-author relationship."""
        paper = ResearchPaper(
            title="Collaborative Research Paper",
            authors_ids=[1, 2, 3]
        )
        
        author1 = Author(name="Dr. First Author")
        author2 = Author(name="Dr. Second Author")
        author3 = Author(name="Dr. Third Author")
        
        # Simulate relationship
        assert len(paper.authors_ids) == 3
        assert 1 in paper.authors_ids

    @pytest.mark.unit
    def test_paper_citation_network(self):
        """Test citation network between papers."""
        citing_paper = ResearchPaper(
            title="Citing Paper",
            id=1
        )
        
        cited_paper = ResearchPaper(
            title="Cited Paper", 
            id=2
        )
        
        citation = Citation(
            citing_paper_id=citing_paper.id,
            cited_paper_id=cited_paper.id,
            citation_type="background",
            relevance_score=0.9
        )
        
        assert citation.citing_paper_id == citing_paper.id
        assert citation.cited_paper_id == cited_paper.id

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
        
        assert abs(assessment.overall_score - calculated_average) < 5.0  # Allow some variance