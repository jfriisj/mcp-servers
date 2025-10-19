"""
Dependency injection container for the SLR MCP Server.
"""

import logging
from pathlib import Path
from typing import Optional

from .database.connection import DatabaseConnection
from .database.adapter import DatabaseFactory, DatabaseAdapter
from .repositories.paper_repository import PaperRepository
from .repositories.chunk_repository import ChunkRepository
from .repositories.quality_assessment_repository import QualityAssessmentRepository
from .repositories.research_question_repository import ResearchQuestionRepository
from .repositories.hypothesis_repository import HypothesisRepository
from .repositories.project_repository import ProjectRepository
from .services.research_document_service import ResearchDocumentService
from .services.quality_assessment_service import QualityAssessmentService
from .services.research_question_service import ResearchQuestionService
from .services.hypothesis_analysis_service import HypothesisAnalysisService
from .services.academic_chunking_service import AcademicChunkingService
from .services.citation_analysis_service import CitationAnalysisService
from .services.evidence_synthesis_service import EvidenceSynthesisService
from .services.slr_report_generation_service import SLRReportGenerator
from .services.slr_workflow_service import SLRWorkflowService
from .services.project_service import ProjectService
from .automation.screening_documentation import ScreeningDocumentationSystem

# Import TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .handlers.mcp_handler import SLRMCPHandler

logger = logging.getLogger(__name__)


class Container:
    """Dependency injection container for SLR MCP Server."""
    
    def __init__(self, database_path: Optional[str] = None, project_root: Optional[Path] = None):
        self.database_path = database_path or "slr_database.db"
        self.project_root = project_root or Path.cwd()
        
        # Core dependencies
        self._db_connection: Optional[DatabaseConnection] = None
        self._db_adapter: Optional[DatabaseAdapter] = None
        
        # Store whether we're using PostgreSQL (connection string starts with postgresql://)
        self._is_postgresql = database_path and (database_path.startswith('postgresql://') or database_path.startswith('postgres://'))
        
        # Repositories
        self._paper_repository: Optional[PaperRepository] = None
        self._chunk_repository: Optional[ChunkRepository] = None
        self._quality_repository: Optional[QualityAssessmentRepository] = None
        self._question_repository: Optional[ResearchQuestionRepository] = None
        self._hypothesis_repository: Optional[HypothesisRepository] = None
        self._project_repository: Optional[ProjectRepository] = None
        
        # Services
        self._document_service: Optional[ResearchDocumentService] = None
        self._quality_service: Optional[QualityAssessmentService] = None
        self._question_service: Optional[ResearchQuestionService] = None
        self._hypothesis_service: Optional[HypothesisAnalysisService] = None
        self._chunking_service: Optional[AcademicChunkingService] = None
        self._citation_service: Optional[CitationAnalysisService] = None
        self._evidence_service: Optional[EvidenceSynthesisService] = None
        self._report_generator: Optional[SLRReportGenerator] = None
        self._slr_workflow_service: Optional[SLRWorkflowService] = None
        self._project_service: Optional[ProjectService] = None
        self._screening_doc_system: Optional[ScreeningDocumentationSystem] = None
        
        # Handlers
        self._mcp_handler: Optional['SLRMCPHandler'] = None
    
    async def initialize(self) -> None:
        """Initialize the container and all dependencies."""
        logger.info("Initializing container...")
        
        # Initialize database using adapter system
        db_adapter = self.get_database_adapter()
        db_adapter.create_tables_if_not_exist()
        
        logger.info("Container initialized successfully")
    
    def get_database_connection(self) -> DatabaseConnection:
        """Get database connection instance."""
        if self._db_connection is None:
            self._db_connection = DatabaseConnection(self.database_path)
        return self._db_connection
    
    def get_database_adapter(self) -> DatabaseAdapter:
        """Get database adapter instance using the configured database path."""
        if self._db_adapter is None:
            # Use the configured database path instead of environment variables
            if self._is_postgresql:
                # For PostgreSQL, use environment-based configuration
                self._db_adapter = DatabaseFactory.create_adapter()
            else:
                # For SQLite, use the configured database_path
                config = {
                    "type": "sqlite",
                    "path": self.database_path
                }
                self._db_adapter = DatabaseFactory.create_adapter(config)
        return self._db_adapter
    
    def get_paper_repository(self) -> PaperRepository:
        """Get paper repository instance."""
        if self._paper_repository is None:
            self._paper_repository = PaperRepository(self.get_database_connection())
        return self._paper_repository
    
    def get_chunk_repository(self) -> ChunkRepository:
        """Get chunk repository instance."""
        if self._chunk_repository is None:
            self._chunk_repository = ChunkRepository(self.get_database_connection())
        return self._chunk_repository
    
    def get_quality_repository(self) -> QualityAssessmentRepository:
        """Get quality assessment repository instance."""
        if self._quality_repository is None:
            self._quality_repository = QualityAssessmentRepository(self.get_database_connection())
        return self._quality_repository
    
    def get_question_repository(self) -> ResearchQuestionRepository:
        """Get research question repository instance."""
        if self._question_repository is None:
            self._question_repository = ResearchQuestionRepository(self.get_database_connection())
        return self._question_repository
    
    def get_hypothesis_repository(self) -> HypothesisRepository:
        """Get hypothesis repository instance."""
        if self._hypothesis_repository is None:
            self._hypothesis_repository = HypothesisRepository(self.get_database_connection())
        return self._hypothesis_repository
    
    def get_project_repository(self) -> ProjectRepository:
        """Get project repository instance."""
        if self._project_repository is None:
            self._project_repository = ProjectRepository(self.get_database_connection())
        return self._project_repository
    
    def get_document_service(self) -> ResearchDocumentService:
        """Get research document service instance."""
        if self._document_service is None:
            self._document_service = ResearchDocumentService(
                paper_repository=self.get_paper_repository()
            )
        return self._document_service
    
    def get_quality_service(self) -> QualityAssessmentService:
        """Get quality assessment service instance."""
        if self._quality_service is None:
            self._quality_service = QualityAssessmentService(
                paper_repository=self.get_paper_repository()
            )
        return self._quality_service
    
    def get_question_service(self) -> ResearchQuestionService:
        """Get research question service instance."""
        if self._question_service is None:
            self._question_service = ResearchQuestionService(
                question_repository=self.get_question_repository()
            )
        return self._question_service
    
    def get_hypothesis_service(self) -> HypothesisAnalysisService:
        """Get hypothesis analysis service instance."""
        if self._hypothesis_service is None:
            self._hypothesis_service = HypothesisAnalysisService(
                hypothesis_repository=self.get_hypothesis_repository(),
                paper_repository=self.get_paper_repository()
            )
        return self._hypothesis_service
    
    def get_project_service(self) -> ProjectService:
        """Get project service instance."""
        if self._project_service is None:
            self._project_service = ProjectService(
                project_repository=self.get_project_repository()
            )
        return self._project_service
    
    def get_chunking_service(self) -> AcademicChunkingService:
        """Get academic chunking service instance."""
        if self._chunking_service is None:
            self._chunking_service = AcademicChunkingService(
                paper_repository=self.get_paper_repository(),
                chunk_repository=self.get_chunk_repository()
            )
        return self._chunking_service
    
    def get_citation_service(self) -> CitationAnalysisService:
        """Get citation analysis service instance."""
        if self._citation_service is None:
            self._citation_service = CitationAnalysisService(
                paper_repository=self.get_paper_repository()
            )
        return self._citation_service
    
    def get_evidence_service(self) -> EvidenceSynthesisService:
        """Get evidence synthesis service instance."""
        if self._evidence_service is None:
            self._evidence_service = EvidenceSynthesisService(
                paper_repository=self.get_paper_repository()
            )
        return self._evidence_service
    
    def get_report_generator(self) -> SLRReportGenerator:
        """Get SLR report generator instance."""
        if self._report_generator is None:
            self._report_generator = SLRReportGenerator(
                paper_repository=self.get_paper_repository(),
                citation_service=self.get_citation_service(),
                evidence_service=self.get_evidence_service()
            )
        return self._report_generator
    
    def get_slr_workflow_service(self) -> SLRWorkflowService:
        """Get SLR workflow service instance."""
        if self._slr_workflow_service is None:
            self._slr_workflow_service = SLRWorkflowService()
        return self._slr_workflow_service
    
    def get_screening_documentation_system(self) -> ScreeningDocumentationSystem:
        """Get screening documentation system instance."""
        if self._screening_doc_system is None:
            self._screening_doc_system = ScreeningDocumentationSystem(
                project_root=self.project_root,
                project_name="real-time-translation-platform"
            )
        return self._screening_doc_system
    
    def get_mcp_handler(self) -> 'SLRMCPHandler':
        """Get MCP handler instance."""
        if self._mcp_handler is None:
            from .handlers.mcp_handler import SLRMCPHandler
            self._mcp_handler = SLRMCPHandler(self)
        return self._mcp_handler
    
    def close(self) -> None:
        """Clean up container resources."""
        if self._db_connection:
            self._db_connection.close()
        logger.info("Container closed successfully")


async def initialize_application(database_path: Optional[str] = None, 
                               project_root: Optional[Path] = None) -> Container:
    """Initialize the application container."""
    container = Container(database_path, project_root)
    await container.initialize()
    return container
