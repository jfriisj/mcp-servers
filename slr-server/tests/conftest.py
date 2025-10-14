"""
Test Configuration and Utilities for SLR MCP Server Unit Tests.

This module provides shared test configuration, fixtures, and utilities
for comprehensive unit testing of academic research components.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing Infrastructure  
SOLID Compliance: Full compliance with dependency inversion and interface segregation
Purpose: Enable comprehensive isolated testing of all SLR components
"""

import pytest
import asyncio
import sys
import tempfile
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator, Callable
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test configuration
TEST_CONFIG = {
    "timeout_seconds": 5.0,
    "max_test_duration": 30.0,
    "mock_latency_ms": 10.0,
    "performance_threshold_ms": 100.0,
    "coverage_target_percent": 90.0,
    "async_test_timeout": 10.0
}


# ============================================================================
# PYTEST CONFIGURATION AND FIXTURES
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Configure asyncio for testing
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_database(temp_dir):
    """Create temporary database file for testing."""
    db_file = temp_dir / "test_slr.db"
    return str(db_file)


@pytest.fixture
def mock_logger():
    """Create mock logger for testing."""
    logger = Mock(spec=logging.Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


# ============================================================================
# ACADEMIC RESEARCH TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_research_paper():
    """Create sample research paper data."""
    return {
        "id": 1,
        "title": "Machine Learning in Healthcare: A Systematic Review",
        "doi": "10.1000/123456789",
        "abstract": "This systematic review examines the application of machine learning techniques in healthcare settings. We analyzed 150 studies published between 2020-2023 to identify trends, challenges, and opportunities.",
        "publication_year": 2023,
        "journal_id": 1,
        "volume": "45",
        "issue": "3",
        "pages": "123-145",
        "url": "https://example.com/paper",
        "language": "en",
        "keywords": '["machine learning", "healthcare", "systematic review", "artificial intelligence"]',
        "research_areas": '["computer science", "healthcare informatics", "medical research"]',
        "methodology": "Systematic literature review following PRISMA guidelines",
        "study_type": "review",
        "sample_size": 150,
        "statistical_methods": '["descriptive statistics", "meta-analysis"]',
        "indexed": True,
        "quality_assessed": True,
        "included_in_review": True,
        "upload_date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_author():
    """Create sample author data."""
    return {
        "id": 1,
        "name": "Dr. Jane Smith",
        "orcid": "0000-0002-1825-0097",
        "email": "jane.smith@university.edu",
        "affiliation": "University of Technology",
        "department": "Computer Science",
        "country": "USA",
        "h_index": 25,
        "citation_count": 1500,
        "research_areas": '["machine learning", "healthcare informatics"]',
        "expertise_keywords": '["deep learning", "medical AI", "systematic reviews"]',
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_journal():
    """Create sample journal data."""
    return {
        "id": 1,
        "name": "Journal of Healthcare Informatics",
        "issn": "1234-5678",
        "e_issn": "2345-6789",
        "publisher": "Academic Press",
        "impact_factor": 4.5,
        "h5_index": 35,
        "sjr_score": 1.2,
        "quartile": "Q1",
        "subject_areas": '["computer science", "healthcare"]',
        "open_access": False,
        "homepage_url": "https://journal.example.com",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_citation():
    """Create sample citation data."""
    return {
        "id": 1,
        "citing_paper_id": 1,
        "cited_paper_id": 2,
        "citation_text": "[1] Smith et al. demonstrated significant improvements in diagnostic accuracy.",
        "citation_context": "Previous research has shown that machine learning techniques can improve diagnostic accuracy [1], which aligns with our findings.",
        "page_number": 5,
        "section": "Results",
        "citation_type": "background",
        "sentiment": "positive",
        "relevance_score": 0.85,
        "extraction_method": "automated",
        "confidence_score": 0.92,
        "created_at": datetime.now()
    }


@pytest.fixture
def sample_chunk():
    """Create sample chunk data."""
    return {
        "id": 1,
        "paper_id": 1,
        "chunk_index": 0,
        "chunk_type": "abstract",
        "section_title": "Abstract",
        "content": "This systematic review examines machine learning in healthcare. We analyzed 150 studies to identify trends and opportunities.",
        "start_page": 1,
        "end_page": 1,
        "word_count": 23,
        "semantic_keywords": '["machine learning", "healthcare", "systematic review"]',
        "research_concepts": '["artificial intelligence", "medical informatics"]',
        "methodology_elements": '["systematic review", "meta-analysis"]',
        "indexed_for_search": True,
        "created_at": datetime.now()
    }


@pytest.fixture
def sample_quality_assessment():
    """Create sample quality assessment data."""
    return {
        "id": 1,
        "paper_id": 1,
        "framework": "prisma",
        "reviewer_id": "reviewer_001",
        "overall_score": 85.0,
        "risk_of_bias": "low",
        "study_design_score": 90.0,
        "methodology_score": 80.0,
        "data_quality_score": 85.0,
        "reporting_score": 90.0,
        "statistical_analysis_score": 75.0,
        "criterion_scores": '{"completeness": 90, "clarity": 85, "rigor": 80}',
        "strengths": "Well-designed study with clear methodology and comprehensive data analysis.",
        "limitations": "Limited sample size in some subgroups.",
        "recommendations": "Consider extending analysis to include more recent studies.",
        "assessment_date": datetime.now(),
        "grade_level": "high",
        "confidence_level": 90.0,
        "consensus_reached": True,
        "final_decision": "include",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_research_question():
    """Create sample research question data."""
    return {
        "id": 1,
        "question_text": "How effective are machine learning algorithms in improving diagnostic accuracy in healthcare settings compared to traditional methods?",
        "framework": "pico",
        "population": "Healthcare settings and patients",
        "intervention": "Machine learning algorithms for diagnosis",
        "comparison": "Traditional diagnostic methods",
        "outcome": "Diagnostic accuracy improvement",
        "question_type": "primary",
        "importance_level": "critical",
        "validation_status": "validated",
        "validation_score": 92.0,
        "validation_feedback": "Well-structured PICO question with clear components.",
        "keywords_used": '["machine learning", "diagnostic accuracy", "healthcare"]',
        "created_by": "researcher_001",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_research_hypothesis():
    """Create sample research hypothesis data."""
    return {
        "id": 1,
        "research_question_id": 1,
        "hypothesis_text": "Machine learning algorithms will demonstrate significantly higher diagnostic accuracy than traditional methods (p < 0.05).",
        "hypothesis_type": "primary",
        "direction": "directional",
        "statistical_test": "t-test",
        "significance_level": 0.05,
        "variables": '["diagnostic_accuracy", "algorithm_type"]',
        "dependent_variable": "diagnostic_accuracy",
        "independent_variables": '["algorithm_type"]',
        "population_studied": "Healthcare diagnostic scenarios",
        "sample_size_required": 100,
        "effect_size_expected": 0.5,
        "testing_status": "proposed",
        "evidence_papers": '[1, 2, 3]',
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_evidence_item():
    """Create sample evidence item data."""
    return {
        "id": 1,
        "paper_id": 1,
        "hypothesis_id": 1,
        "chunk_id": 1,
        "evidence_text": "The machine learning model achieved 95% accuracy compared to 78% for traditional methods (p < 0.001).",
        "evidence_type": "statistical",
        "strength": "strong",
        "quality": "high",
        "relevance": 0.95,
        "supporting": True,
        "effect_size": 0.8,
        "confidence_interval": "95% CI: [0.92-0.98]",
        "statistical_significance": 0.001,
        "sample_size": 500,
        "study_design": "randomized controlled trial",
        "methodological_quality": "excellent",
        "risk_of_bias": "low",
        "grade_rating": "high",
        "extraction_method": "manual",
        "extractor_id": "extractor_001",
        "extraction_date": datetime.now(),
        "verification_status": "verified",
        "verifier_id": "verifier_001",
        "verification_date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


# ============================================================================
# MOCK REPOSITORIES AND SERVICES
# ============================================================================

@pytest.fixture
def mock_database():
    """Create mock database connection."""
    db = Mock()
    db.connect = Mock()
    db.transaction = Mock()
    db.execute = Mock()
    db.close = Mock()
    db.is_connected = Mock(return_value=True)
    return db


@pytest.fixture
def mock_paper_repository(mock_database):
    """Create mock paper repository."""
    from repositories.base_repository import BaseRepository
    
    repo = Mock(spec=BaseRepository)
    repo.create = Mock()
    repo.get_by_id = Mock()
    repo.update = Mock()
    repo.delete = Mock()
    repo.list_all = Mock()
    repo.search = Mock()
    repo.count = Mock(return_value=0)
    return repo


@pytest.fixture
def mock_research_document_service():
    """Create mock research document service."""
    service = Mock()
    service.upload_paper = AsyncMock()
    service.get_paper = AsyncMock()
    service.analyze_citations = AsyncMock()
    service.classify_paper = AsyncMock()
    return service


@pytest.fixture
def mock_quality_assessment_service():
    """Create mock quality assessment service."""
    service = Mock()
    service.create_assessment = AsyncMock()
    service.calculate_inter_rater_reliability = AsyncMock()
    service.get_consensus_assessment = AsyncMock()
    return service


@pytest.fixture
def mock_research_question_service():
    """Create mock research question service."""
    service = Mock()
    service.validate_research_question = AsyncMock()
    service.decompose_question = AsyncMock()
    service.assess_novelty = AsyncMock()
    return service


@pytest.fixture
def mock_hypothesis_analysis_service():
    """Create mock hypothesis analysis service."""
    service = Mock()
    service.extract_hypotheses = AsyncMock()
    service.classify_evidence = AsyncMock()
    service.test_hypothesis = AsyncMock()
    service.perform_meta_analysis = AsyncMock()
    return service


@pytest.fixture
def mock_academic_chunking_service():
    """Create mock academic chunking service."""
    service = Mock()
    service.index_paper = AsyncMock()
    service.chunk_paper = AsyncMock()
    service.optimize_chunks = AsyncMock()
    return service


# ============================================================================
# MCP PROTOCOL TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_mcp_handler():
    """Create mock MCP handler."""
    handler = Mock()
    handler.upload_paper = Mock()
    handler.assess_quality = Mock()
    handler.validate_research_question = Mock()
    handler.analyze_citations = Mock()
    handler.test_hypothesis = Mock()
    handler.index_paper = Mock()
    handler.synthesize_evidence = Mock()
    return handler


@pytest.fixture
def sample_mcp_request():
    """Create sample MCP request data."""
    return {
        "method": "tools/call",
        "params": {
            "name": "upload-paper",
            "arguments": {
                "file_path": "/test/paper.pdf",
                "title": "Test Paper",
                "authors": ["Dr. Jane Smith", "Dr. John Doe"],
                "doi": "10.1000/test"
            }
        }
    }


@pytest.fixture
def sample_mcp_response():
    """Create sample MCP response data."""
    return {
        "success": True,
        "data": {
            "paper_id": 1,
            "title": "Test Paper",
            "authors": ["Dr. Jane Smith", "Dr. John Doe"],
            "doi": "10.1000/test"
        },
        "message": "Paper uploaded successfully"
    }


# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================

class PerformanceTimer:
    """Utility for measuring performance in tests."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
    
    def start(self) -> None:
        """Start timing."""
        self.start_time = time.perf_counter()
    
    def stop(self) -> float:
        """Stop timing and return duration in milliseconds."""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        return self.duration_ms
    
    def assert_within_threshold(self, threshold_ms: float) -> None:
        """Assert that duration is within threshold."""
        if self.duration_ms is None:
            raise RuntimeError("Timer not stopped")
        
        assert self.duration_ms <= threshold_ms, (
            f"Operation took {self.duration_ms:.1f}ms, "
            f"expected <= {threshold_ms}ms"
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


@pytest.fixture
def performance_timer():
    """Create performance timer for tests."""
    return PerformanceTimer()


@pytest.fixture
def performance_threshold():
    """Get performance threshold from config."""
    return TEST_CONFIG["performance_threshold_ms"]


# ============================================================================
# ERROR SIMULATION FIXTURES
# ============================================================================

@pytest.fixture
def database_error():
    """Create database error for testing."""
    import sqlite3
    return sqlite3.Error("Mock database error")


@pytest.fixture
def validation_error():
    """Create validation error for testing."""
    return ValueError("Mock validation failed")


@pytest.fixture
def file_not_found_error():
    """Create file not found error for testing."""
    return FileNotFoundError("Mock file not found")


# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup any lingering async tasks
    try:
        pending_tasks = [
            task for task in asyncio.all_tasks() 
            if not task.done()
        ]
        for task in pending_tasks:
            task.cancel()
    except RuntimeError:
        pass  # No event loop running


# ============================================================================
# TEST MARKERS
# ============================================================================

# Pytest markers for test categorization
pytest_markers = [
    "unit: Unit tests with mocked dependencies",
    "integration: Integration tests with real database",
    "async: Async function tests",
    "performance: Performance and timing tests", 
    "error: Error handling and edge case tests",
    "academic: Academic research domain tests",
    "mcp: MCP protocol tests"
]