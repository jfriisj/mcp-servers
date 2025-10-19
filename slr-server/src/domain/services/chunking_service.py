"""
Chunking Service Interfaces

Defines contracts for academic chunking operations, broken down following SRP.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from enum import Enum
from ..models import ResearchPaper, AcademicChunk


class IndexingStrategy(Enum):
    """Academic indexing strategies."""
    FULL_TEXT = "full_text"
    SECTION_BASED = "section_based"
    SEMANTIC = "semantic" 
    CITATION_AWARE = "citation_aware"
    HYBRID = "hybrid"


class OptimizationLevel(Enum):
    """Agent optimization levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class IContentExtractionService(ABC):
    """
    Interface for content extraction operations.
    Handles only content extraction from various file formats.
    """
    
    @abstractmethod
    def extract_paper_content(self, paper: ResearchPaper) -> str:
        """Extract text content from paper file."""
        pass
    
    @abstractmethod
    def extract_from_pdf(self, file_path: str) -> str:
        """Extract content from PDF file."""
        pass
    
    @abstractmethod
    def extract_from_text_file(self, file_path: str) -> str:
        """Extract content from text file."""
        pass
    
    @abstractmethod
    def extract_from_word_doc(self, file_path: str) -> str:
        """Extract content from Word document."""
        pass


class IChunkingStrategyService(ABC):
    """
    Interface for chunking strategy operations.
    Handles different approaches to splitting content into chunks.
    """
    
    @abstractmethod
    def chunk_content(self, paper: ResearchPaper, content: str, strategy: IndexingStrategy) -> List[AcademicChunk]:
        """Chunk content using specified strategy."""
        pass
    
    @abstractmethod
    def select_optimal_strategy(self, paper: ResearchPaper, content: str) -> IndexingStrategy:
        """Select the best chunking strategy for given content."""
        pass


class ISemanticAnalysisService(ABC):
    """
    Interface for semantic analysis operations.
    Handles semantic enhancement and concept extraction.
    """
    
    @abstractmethod
    def enhance_chunk_semantically(self, chunk: AcademicChunk, enhancement_level: str = "standard") -> AcademicChunk:
        """Apply semantic enhancement to chunk."""
        pass
    
    @abstractmethod
    def extract_key_concepts(self, content: str) -> List[str]:
        """Extract key academic concepts from content."""
        pass
    
    @abstractmethod
    def identify_academic_domain(self, content: str, concepts: List[str]) -> str:
        """Identify academic domain from content."""
        pass


class IQualityAssessmentService(ABC):
    """
    Interface for chunk quality assessment operations.
    Handles quality evaluation and filtering.
    """
    
    @abstractmethod
    def assess_chunk_quality(self, chunks: List[AcademicChunk], paper: ResearchPaper) -> List[AcademicChunk]:
        """Assess and filter chunks by quality."""
        pass
    
    @abstractmethod
    def calculate_chunk_quality_score(self, chunk: AcademicChunk, paper: ResearchPaper) -> float:
        """Calculate quality score for individual chunk."""
        pass


class IChunkOptimizationService(ABC):
    """
    Interface for chunk optimization operations.
    Handles AI agent optimization and use case-specific optimization.
    """
    
    @abstractmethod
    def optimize_for_agents(self, chunks: List[AcademicChunk], optimization_level: OptimizationLevel, 
                           agent_context: Optional[str] = None) -> List[AcademicChunk]:
        """Optimize chunks for AI agent processing."""
        pass
    
    @abstractmethod
    def optimize_chunks_for_qa(self, chunks: List[AcademicChunk], 
                              question_types: Optional[List[str]] = None) -> List[AcademicChunk]:
        """Optimize chunks for question-answering tasks."""
        pass
    
    @abstractmethod
    def optimize_chunks_for_summarization(self, chunks: List[AcademicChunk], 
                                         summary_type: str = "comprehensive") -> List[AcademicChunk]:
        """Optimize chunks for summarization tasks."""
        pass


class IChunkingService(ABC):
    """
    Main chunking service interface that orchestrates all chunking operations.
    Uses composition of other services to follow SRP.
    """
    
    @abstractmethod
    def index_paper(self, paper_id: int, strategy: IndexingStrategy = IndexingStrategy.HYBRID,
                   optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE,
                   agent_context: Optional[str] = None) -> List[AcademicChunk]:
        """Index paper with intelligent chunking and optimization."""
        pass
    
    @abstractmethod
    def reindex_paper(self, paper_id: int, force: bool = False, 
                     new_strategy: Optional[IndexingStrategy] = None) -> List[AcademicChunk]:
        """Reindex paper with updated parameters."""
        pass
    
    @abstractmethod
    def batch_index_papers(self, paper_ids: List[int], strategy: IndexingStrategy = IndexingStrategy.HYBRID,
                          optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE) -> Dict[int, List[AcademicChunk]]:
        """Batch index multiple papers."""
        pass