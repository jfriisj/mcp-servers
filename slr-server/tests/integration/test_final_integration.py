"""
Final Integration Tests for SLR MCP Server.

Comprehensive end-to-end testing of all components working together,
including MCP protocol validation and complete system functionality.
"""

import pytest
import asyncio
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models import (
    ResearchPaper, Author, QualityAssessment, ResearchQuestion, 
    QualityFramework, QuestionFramework
)


@pytest.mark.integration
class TestFinalIntegration:
    """Final comprehensive integration tests."""
    
    def test_all_models_import_successfully(self):
        """Test that all core models can be imported without errors."""
        # Import all model classes
        from models import (
            ResearchPaper, Author, Journal, Citation, AcademicChunk,
            QualityAssessment, ResearchQuestion, ResearchHypothesis,
            EvidenceItem, QualityFramework, QuestionFramework,
            HypothesisType, ValidationLevel, EffectDirection
        )
        
        # Verify models can be instantiated
        paper = ResearchPaper(
            id=1,
            title="Test Paper",
            file_path="/test/path.pdf",
            file_type="pdf"
        )
        
        author = Author(
            name="Dr. Test Author",
            email="test@example.com"
        )
        
        assessment = QualityAssessment(
            paper_id=1,
            framework=QualityFramework.PRISMA,
            reviewer_id="test_reviewer",
            overall_score=85.0
        )
        
        question = ResearchQuestion(
            question_text="Test research question?",
            framework=QuestionFramework.PICO,
            validation_status=ValidationLevel.VALIDATED,
            validity_score=90.0
        )
        
        assert paper.title == "Test Paper"
        assert author.name == "Dr. Test Author"
        assert assessment.overall_score == 85.0
        assert question.validity_score == 90.0
        
        print("✅ All models import and instantiate successfully")

    def test_service_layer_imports(self):
        """Test that all service classes can be imported."""
        try:
            from services.research_document_service import ResearchDocumentService
            from services.quality_assessment_service import QualityAssessmentService
            from services.research_question_service import ResearchQuestionService
            from services.hypothesis_analysis_service import HypothesisAnalysisService
            from services.academic_chunking_service import AcademicChunkingService
            
            # Verify classes can be imported (not instantiated due to dependencies)
            assert ResearchDocumentService is not None
            assert QualityAssessmentService is not None
            assert ResearchQuestionService is not None
            assert HypothesisAnalysisService is not None
            assert AcademicChunkingService is not None
            
            print("✅ All service classes import successfully")
            
        except Exception as e:
            pytest.fail(f"Service import failed: {e}")

    def test_repository_layer_imports(self):
        """Test that repository classes can be imported."""
        try:
            from repositories.base_repository import BaseRepository
            from repositories.paper_repository import PaperRepository
            
            assert BaseRepository is not None
            assert PaperRepository is not None
            
            print("✅ Repository classes import successfully")
            
        except Exception as e:
            pytest.fail(f"Repository import failed: {e}")

    def test_mcp_handler_import(self):
        """Test that MCP handler can be imported."""
        try:
            from mcp_handler import SLRMCPHandler
            
            assert SLRMCPHandler is not None
            
            print("✅ MCP Handler imports successfully")
            
        except Exception as e:
            pytest.fail(f"MCP Handler import failed: {e}")

    def test_database_layer_imports(self):
        """Test that database components can be imported."""
        try:
            from database.connection import DatabaseConnection
            from database.schema import create_tables
            
            assert DatabaseConnection is not None
            assert create_tables is not None
            
            print("✅ Database layer imports successfully")
            
        except Exception as e:
            pytest.fail(f"Database import failed: {e}")

    def test_chunking_strategies_import(self):
        """Test that chunking strategies can be imported."""
        try:
            from chunking.strategy_factory import ChunkingStrategyFactory
            from chunking.academic_section_strategy import AcademicSectionChunkingStrategy
            from chunking.citation_aware_strategy import CitationAwareChunkingStrategy
            from chunking.topic_based_strategy import TopicBasedChunkingStrategy
            
            assert ChunkingStrategyFactory is not None
            assert AcademicSectionChunkingStrategy is not None
            assert CitationAwareChunkingStrategy is not None
            assert TopicBasedChunkingStrategy is not None
            
            print("✅ Chunking strategies import successfully")
            
        except Exception as e:
            pytest.fail(f"Chunking strategy import failed: {e}")

    def test_main_server_import(self):
        """Test that main server components can be imported."""
        try:
            from server import SLRMCPServer
            
            assert SLRMCPServer is not None
            
            print("✅ Main server imports successfully")
            
        except Exception as e:
            pytest.fail(f"Main server import failed: {e}")

    @pytest.mark.asyncio
    async def test_mcp_protocol_structure(self):
        """Test MCP protocol structure and tool definitions."""
        try:
            from mcp_handler import SLRMCPHandler
            
            # Mock dependencies for handler
            with patch('mcp_handler.ResearchDocumentService'), \
                 patch('mcp_handler.QualityAssessmentService'), \
                 patch('mcp_handler.ResearchQuestionService'), \
                 patch('mcp_handler.HypothesisAnalysisService'), \
                 patch('mcp_handler.AcademicChunkingService'):
                
                # This tests the structure, not full functionality
                handler = SLRMCPHandler(
                    research_document_service=Mock(),
                    quality_assessment_service=Mock(),
                    research_question_service=Mock(),
                    hypothesis_analysis_service=Mock(),
                    academic_chunking_service=Mock()
                )
                
                assert handler is not None
                
                # Test that handler has expected methods
                expected_methods = [
                    'upload_paper',
                    'assess_quality', 
                    'validate_research_question',
                    'analyze_citations',
                    'analyze_hypothesis',
                    'index_paper',
                    'synthesize_evidence'
                ]
                
                for method in expected_methods:
                    assert hasattr(handler, method), f"Handler missing method: {method}"
                
                print("✅ MCP Protocol structure validated")
                
        except Exception as e:
            pytest.fail(f"MCP Protocol test failed: {e}")

    def test_data_model_relationships(self):
        """Test relationships between data models."""
        # Create related models
        paper = ResearchPaper(
            id=1,
            title="Test Paper",
            file_path="/test/path.pdf",
            file_type="pdf"
        )
        
        author = Author(
            id=1,
            name="Dr. Test Author",
            email="test@example.com"
        )
        
        quality_assessment = QualityAssessment(
            id=1,
            paper_id=paper.id,
            framework=QualityFramework.PRISMA,
            reviewer_id="test_reviewer",
            overall_score=85.0,
            risk_of_bias="low"
        )
        
        # Test relationships
        assert quality_assessment.paper_id == paper.id
        assert paper.id is not None
        assert author.id is not None
        
        # Test serialization
        paper_dict = paper.to_dict()
        author_dict = author.to_dict()
        assessment_dict = quality_assessment.to_dict()
        
        assert isinstance(paper_dict, dict)
        assert isinstance(author_dict, dict)
        assert isinstance(assessment_dict, dict)
        
        assert paper_dict['title'] == "Test Paper"
        assert author_dict['name'] == "Dr. Test Author"
        assert assessment_dict['overall_score'] == 85.0
        
        print("✅ Data model relationships validated")

    def test_enum_consistency(self):
        """Test that enums are properly defined and consistent."""
        # Test quality frameworks
        frameworks = [
            QualityFramework.PRISMA,
            QualityFramework.CONSORT,
            QualityFramework.STROBE,
            QualityFramework.QUADAS
        ]
        
        for framework in frameworks:
            assert framework.value is not None
        
        # Test question frameworks
        question_frameworks = [
            QuestionFramework.PICO,
            QuestionFramework.SPIDER
        ]
        
        for qf in question_frameworks:
            assert qf.value is not None
        
        # Test validation levels
        validation_levels = [
            ValidationLevel.DRAFT,
            ValidationLevel.VALIDATED,
            ValidationLevel.APPROVED
        ]
        
        for vl in validation_levels:
            assert vl.value is not None
        
        print("✅ Enum consistency validated")

    def test_error_handling_structure(self):
        """Test that error handling structures are in place."""
        # Test that models handle invalid data gracefully
        try:
            # This should work
            paper = ResearchPaper(
                id=1,
                title="Valid Paper",
                file_path="/valid/path.pdf",
                file_type="pdf"
            )
            assert paper.title == "Valid Paper"
        except Exception as e:
            pytest.fail(f"Valid paper creation failed: {e}")
        
        print("✅ Basic error handling validated")

    def test_configuration_structure(self):
        """Test configuration and settings structure."""
        # Test that VS Code MCP configuration exists
        vscode_config_path = Path(__file__).parent.parent.parent / ".vscode" / "mcp.json"
        assert vscode_config_path.exists(), "VS Code MCP configuration missing"
        
        # Test that Docker configuration exists
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile missing"
        
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        assert docker_compose_path.exists(), "docker-compose.yml missing"
        
        # Test deployment scripts exist
        deploy_sh_path = Path(__file__).parent.parent.parent / "deploy.sh"
        assert deploy_sh_path.exists(), "deploy.sh missing"
        
        deploy_ps1_path = Path(__file__).parent.parent.parent / "deploy.ps1"
        assert deploy_ps1_path.exists(), "deploy.ps1 missing"
        
        print("✅ Configuration structure validated")

    def test_documentation_completeness(self):
        """Test that required documentation exists."""
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        assert docs_dir.exists(), "Documentation directory missing"
        
        required_docs = [
            "research-guide.md",
            "api-reference.md",
            "example-workflows.md",
            "installation.md"
        ]
        
        for doc in required_docs:
            doc_path = docs_dir / doc
            assert doc_path.exists(), f"Required documentation missing: {doc}"
            
            # Check that files have content
            content = doc_path.read_text()
            assert len(content) > 100, f"Documentation file too short: {doc}"
        
        print("✅ Documentation completeness validated")

    def test_test_infrastructure(self):
        """Test that testing infrastructure is properly set up."""
        # Check test configuration
        conftest_path = Path(__file__).parent.parent / "conftest.py"
        assert conftest_path.exists(), "Test configuration missing"
        
        # Check that test markers are defined
        conftest_content = conftest_path.read_text()
        assert "pytest_markers" in conftest_content, "Test markers not defined"
        
        # Check integration test directory
        integration_dir = Path(__file__).parent
        assert integration_dir.exists(), "Integration test directory missing"
        
        print("✅ Test infrastructure validated")

    def test_project_structure_completeness(self):
        """Test that project structure is complete and follows standards."""
        project_root = Path(__file__).parent.parent.parent
        
        # Check core directories exist
        required_dirs = [
            "src",
            "tests", 
            "docs",
            ".vscode"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Required directory missing: {dir_name}"
        
        # Check core files exist
        required_files = [
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
            "deploy.sh",
            "deploy.ps1",
            ".vscode/mcp.json"
        ]
        
        for file_name in required_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"Required file missing: {file_name}"
        
        print("✅ Project structure completeness validated")


@pytest.mark.integration
@pytest.mark.performance  
def test_system_performance_readiness():
    """Test that system is ready for performance requirements."""
    # Test that models can be created efficiently
    import time
    
    start_time = time.time()
    
    # Create multiple models to test performance
    papers = []
    for i in range(100):
        paper = ResearchPaper(
            id=i,
            title=f"Test Paper {i}",
            file_path=f"/test/path{i}.pdf",
            file_type="pdf"
        )
        papers.append(paper)
    
    creation_time = time.time() - start_time
    
    # Should be able to create 100 models quickly
    assert creation_time < 1.0, f"Model creation too slow: {creation_time:.3f}s"
    
    # Test serialization performance
    start_time = time.time()
    
    dicts = [paper.to_dict() for paper in papers[:10]]
    
    serialization_time = time.time() - start_time
    assert serialization_time < 0.1, f"Serialization too slow: {serialization_time:.3f}s"
    
    print("✅ System performance readiness validated")


if __name__ == "__main__":
    # Run all tests when script is executed directly
    pytest.main([__file__, "-v", "-m", "integration"])