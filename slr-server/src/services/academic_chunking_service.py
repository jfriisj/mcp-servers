"""
Academic Indexing and Chunking Service for systematic literature review content optimization.

This module implements the AcademicChunkingService class following systematic review
best practices for intelligent academic paper indexing and AI agent optimization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import re

from ..models import ResearchPaper, AcademicChunk
from ..repositories.paper_repository import PaperRepository
from ..chunking.strategy_factory import AcademicChunkingStrategyFactory


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


class ChunkQuality(Enum):
    """Quality assessment for chunks."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class IndexingMetrics:
    """Metrics for academic indexing performance."""
    total_chunks: int
    average_chunk_size: float
    semantic_coherence: float
    citation_preservation: float
    structural_integrity: float
    agent_optimization_score: float
    processing_time: float


@dataclass
class ChunkEnhancement:
    """Enhancement applied to academic chunk."""
    enhancement_type: str
    confidence: float
    metadata: Dict[str, Any]
    agent_context: Optional[str] = None


@dataclass
class SemanticContext:
    """Semantic context for academic chunk."""
    key_concepts: List[str]
    related_terms: List[str]
    academic_domain: str
    methodology_context: Optional[str]
    research_context: Optional[str]


class AcademicChunkingService:
    """
    Academic indexing and chunking service for systematic literature reviews.

    Implements intelligent academic paper indexing with AI agent optimization,
    semantic enhancement, and context-aware chunking for systematic review workflows.

    Key Features:
    - Multi-strategy academic chunking
    - AI agent optimization for different use cases
    - Semantic enhancement and concept extraction
    - Citation-aware content preservation
    - Context-aware chunk quality assessment
    - Academic structure preservation
    - Performance optimization for large corpora

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Contains academic indexing business rules
    - Validates content and enforces quality standards
    - Provides optimized chunks for AI processing
    """

    def __init__(self, paper_repository: PaperRepository):
        """
        Initialize AcademicChunkingService.

        Args:
            paper_repository: Repository for research paper access
        """
        self.paper_repository = paper_repository
        self.strategy_factory = AcademicChunkingStrategyFactory()
        self._optimization_configs = self._initialize_optimization_configs()
        self._quality_metrics = self._initialize_quality_metrics()

    def index_paper(
        self,
        paper_id: int,
        strategy: IndexingStrategy = IndexingStrategy.HYBRID,
        optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE,
        agent_context: Optional[str] = None
    ) -> List[AcademicChunk]:
        """
        Index academic paper with intelligent chunking and optimization.

        Args:
            paper_id: ID of paper to index
            strategy: Indexing strategy to use
            optimization_level: Level of agent optimization
            agent_context: Context for agent optimization

        Returns:
            List of indexed and optimized academic chunks

        Raises:
            ValueError: If paper not found or parameters invalid
        """
        paper = self.paper_repository.get_by_id(paper_id)
        if not paper:
            raise ValueError(f"Research paper {paper_id} not found")

        # Read paper content (placeholder - would read actual file)
        content = self._extract_paper_content(paper)
        if not content:
            raise ValueError(f"No content found for paper {paper_id}")

        # Select and configure chunking strategy
        chunking_strategy = self._select_chunking_strategy(
            paper, content, strategy
        )

        # Perform initial chunking
        raw_chunks = chunking_strategy.chunk(content, paper)

        # Apply academic enhancements
        enhanced_chunks = self._apply_academic_enhancements(
            raw_chunks, paper, optimization_level
        )

        # Optimize for agent processing
        optimized_chunks = self._optimize_for_agents(
            enhanced_chunks, optimization_level, agent_context
        )

        # Assess and filter chunk quality
        quality_chunks = self._assess_chunk_quality(optimized_chunks, paper)

        # Update paper indexing status
        paper.indexed = True
        self.paper_repository.update(paper)

        return quality_chunks

    def batch_index_papers(
        self,
        paper_ids: List[int],
        strategy: IndexingStrategy = IndexingStrategy.HYBRID,
        optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE,
        parallel_processing: bool = True
    ) -> Dict[int, List[AcademicChunk]]:
        """
        Batch index multiple papers with optimization.

        Args:
            paper_ids: List of paper IDs to index
            strategy: Indexing strategy to use
            optimization_level: Level of optimization
            parallel_processing: Whether to use parallel processing

        Returns:
            Dictionary mapping paper IDs to their chunks

        Raises:
            ValueError: If invalid parameters provided
        """
        if not paper_ids:
            raise ValueError("No paper IDs provided for batch indexing")

        if len(paper_ids) > 1000:
            raise ValueError("Batch size cannot exceed 1000 papers")

        results = {}
        processing_stats = {
            "total_papers": len(paper_ids),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "start_time": datetime.now()
        }

        for paper_id in paper_ids:
            try:
                chunks = self.index_paper(
                    paper_id, strategy, optimization_level
                )
                results[paper_id] = chunks
                processing_stats["successful"] += 1
                processing_stats["total_chunks"] += len(chunks)
            except Exception:
                # Log error and continue with next paper
                results[paper_id] = []
                processing_stats["failed"] += 1

        processing_stats["end_time"] = datetime.now()
        processing_stats["duration"] = (
            processing_stats["end_time"] - processing_stats["start_time"]
        ).total_seconds()

        # Store processing statistics for monitoring
        self._store_batch_processing_stats(processing_stats)

        return results

    def enhance_chunk_semantically(
        self,
        chunk: AcademicChunk,
        enhancement_level: str = "standard"
    ) -> AcademicChunk:
        """
        Apply semantic enhancement to academic chunk.

        Args:
            chunk: Chunk to enhance
            enhancement_level: Level of enhancement (basic, standard, advanced)

        Returns:
            Semantically enhanced chunk

        Raises:
            ValueError: If invalid enhancement level
        """
        valid_levels = {"basic", "standard", "advanced"}
        if enhancement_level not in valid_levels:
            raise ValueError(f"Invalid enhancement level. Valid: {valid_levels}")

        # Extract semantic context
        semantic_context = self._extract_semantic_context(
            chunk, enhancement_level
        )

        # Apply concept extraction
        key_concepts = self._extract_key_concepts(chunk.content)

        # Enhance metadata
        enhanced_metadata = chunk.metadata.copy()
        enhanced_metadata.update({
            "semantic_context": semantic_context,
            "key_concepts": key_concepts,
            "enhancement_level": enhancement_level,
            "enhanced_at": datetime.now().isoformat()
        })

        # Create enhanced chunk
        enhanced_chunk = AcademicChunk(
            paper_id=chunk.paper_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            chunk_type=chunk.chunk_type,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            word_count=chunk.word_count,
            section_title=chunk.section_title,
            academic_context=chunk.academic_context,
            citations=chunk.citations,
            metadata=enhanced_metadata,
            quality_score=chunk.quality_score + 0.1,  # Boost for enhancement
            created_at=chunk.created_at
        )

        return enhanced_chunk

    def optimize_chunks_for_qa(
        self,
        chunks: List[AcademicChunk],
        question_types: List[str] = None
    ) -> List[AcademicChunk]:
        """
        Optimize chunks specifically for question-answering tasks.

        Args:
            chunks: List of chunks to optimize
            question_types: Types of questions to optimize for

        Returns:
            QA-optimized chunks
        """
        if question_types is None:
            question_types = [
                "factual", "analytical", "methodological", 
                "comparative", "evaluative"
            ]

        optimized_chunks = []

        for chunk in chunks:
            # Analyze chunk for QA suitability
            qa_metrics = self._analyze_qa_suitability(chunk, question_types)

            # Apply QA-specific enhancements
            if qa_metrics["suitability_score"] > 0.6:
                qa_chunk = self._apply_qa_optimizations(chunk, qa_metrics)
                optimized_chunks.append(qa_chunk)

        # Sort by QA relevance
        optimized_chunks.sort(
            key=lambda c: c.metadata.get("qa_score", 0.0),
            reverse=True
        )

        return optimized_chunks

    def optimize_chunks_for_summarization(
        self,
        chunks: List[AcademicChunk],
        summary_type: str = "comprehensive"
    ) -> List[AcademicChunk]:
        """
        Optimize chunks for summarization tasks.

        Args:
            chunks: List of chunks to optimize
            summary_type: Type of summary (comprehensive, executive, methodological)

        Returns:
            Summarization-optimized chunks
        """
        valid_types = {"comprehensive", "executive", "methodological", "findings"}
        if summary_type not in valid_types:
            raise ValueError(f"Invalid summary type. Valid: {valid_types}")

        optimized_chunks = []

        for chunk in chunks:
            # Assess summarization value
            summary_metrics = self._assess_summarization_value(chunk, summary_type)

            # Apply summarization optimizations
            if summary_metrics["summarization_score"] > 0.5:
                summary_chunk = self._apply_summarization_optimizations(
                    chunk, summary_metrics, summary_type
                )
                optimized_chunks.append(summary_chunk)

        return optimized_chunks

    def generate_indexing_report(
        self,
        paper_ids: List[int] = None,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive indexing performance report.

        Args:
            paper_ids: Specific papers to include (None for all indexed)
            include_metrics: Whether to include detailed metrics

        Returns:
            Comprehensive indexing report
        """
        # Get papers for analysis
        if paper_ids:
            papers = [
                self.paper_repository.get_by_id(pid) 
                for pid in paper_ids
            ]
            papers = [p for p in papers if p and p.indexed]
        else:
            papers = self.paper_repository.list_all({"indexed": True})

        report = {
            "report_date": datetime.now().isoformat(),
            "papers_analyzed": len(papers),
            "indexing_summary": {},
            "quality_metrics": {},
            "optimization_analysis": {},
            "performance_stats": {},
            "recommendations": []
        }

        if not papers:
            report["error"] = "No indexed papers found for analysis"
            return report

        # Calculate summary statistics
        report["indexing_summary"] = self._calculate_indexing_summary(papers)

        if include_metrics:
            report["quality_metrics"] = self._calculate_quality_metrics(papers)
            report["optimization_analysis"] = self._analyze_optimization_effectiveness(papers)
            report["performance_stats"] = self._get_performance_statistics()

        # Generate recommendations
        report["recommendations"] = self._generate_indexing_recommendations(
            papers, report
        )

        return report

    def reindex_paper(
        self,
        paper_id: int,
        force: bool = False,
        new_strategy: Optional[IndexingStrategy] = None
    ) -> List[AcademicChunk]:
        """
        Reindex paper with updated parameters or strategy.

        Args:
            paper_id: ID of paper to reindex
            force: Force reindexing even if recently indexed
            new_strategy: New strategy to use for indexing

        Returns:
            Newly indexed chunks

        Raises:
            ValueError: If paper not found or reindexing not needed
        """
        paper = self.paper_repository.get_by_id(paper_id)
        if not paper:
            raise ValueError(f"Research paper {paper_id} not found")

        # Check if reindexing is necessary
        if paper.indexed and not force:
            # Check last indexing time (would be stored in paper metadata)
            last_indexed = paper.metadata.get("last_indexed")
            if last_indexed:
                # If indexed recently, skip unless forced
                pass

        # Clear previous indexing status
        paper.indexed = False
        self.paper_repository.update(paper)

        # Reindex with new parameters
        strategy = new_strategy if new_strategy else IndexingStrategy.HYBRID
        
        return self.index_paper(paper_id, strategy)

    # Private helper methods

    def _initialize_optimization_configs(self) -> Dict[str, Any]:
        """Initialize agent optimization configurations."""
        return {
            OptimizationLevel.BASIC: {
                "chunk_size_range": (200, 800),
                "overlap": 50,
                "semantic_enhancement": False,
                "citation_preservation": True,
                "context_expansion": False
            },
            OptimizationLevel.INTERMEDIATE: {
                "chunk_size_range": (300, 1200),
                "overlap": 100,
                "semantic_enhancement": True,
                "citation_preservation": True,
                "context_expansion": True
            },
            OptimizationLevel.ADVANCED: {
                "chunk_size_range": (400, 1500),
                "overlap": 150,
                "semantic_enhancement": True,
                "citation_preservation": True,
                "context_expansion": True,
                "cross_reference": True
            },
            OptimizationLevel.EXPERT: {
                "chunk_size_range": (500, 2000),
                "overlap": 200,
                "semantic_enhancement": True,
                "citation_preservation": True,
                "context_expansion": True,
                "cross_reference": True,
                "domain_adaptation": True
            }
        }

    def _initialize_quality_metrics(self) -> Dict[str, Any]:
        """Initialize chunk quality assessment metrics."""
        return {
            "content_coherence": 0.3,
            "academic_relevance": 0.25,
            "citation_quality": 0.2,
            "structural_integrity": 0.15,
            "agent_optimization": 0.1
        }

    def _extract_paper_content(self, paper: ResearchPaper) -> str:
        """Extract content from paper file."""
        # Placeholder - would read actual file content
        # For now, use abstract + title as content
        content = f"Title: {paper.title}\n\n"
        if paper.abstract:
            content += f"Abstract: {paper.abstract}\n\n"
        
        # Would add full text extraction here
        content += "Full paper content would be extracted here..."
        
        return content

    def _select_chunking_strategy(
        self,
        paper: ResearchPaper,
        content: str,
        strategy: IndexingStrategy
    ):
        """Select appropriate chunking strategy."""
        if strategy == IndexingStrategy.HYBRID:
            # Use factory to select best strategy
            return self.strategy_factory.get_strategy(paper, content)
        elif strategy == IndexingStrategy.SECTION_BASED:
            return self.strategy_factory.get_strategy_by_name("academic_section")
        elif strategy == IndexingStrategy.CITATION_AWARE:
            return self.strategy_factory.get_strategy_by_name("citation_aware")
        elif strategy == IndexingStrategy.SEMANTIC:
            return self.strategy_factory.get_strategy_by_name("topic_based")
        else:
            # Default to section-based
            return self.strategy_factory.get_strategy_by_name("academic_section")

    def _apply_academic_enhancements(
        self,
        chunks: List[AcademicChunk],
        paper: ResearchPaper,
        optimization_level: OptimizationLevel
    ) -> List[AcademicChunk]:
        """Apply academic-specific enhancements to chunks."""
        enhanced_chunks = []
        config = self._optimization_configs[optimization_level]

        for chunk in chunks:
            enhanced_chunk = chunk

            # Apply semantic enhancement if configured
            if config.get("semantic_enhancement"):
                enhanced_chunk = self.enhance_chunk_semantically(chunk)

            # Add academic context
            enhanced_chunk.academic_context.update({
                "paper_methodology": paper.methodology,
                "paper_study_type": paper.study_type,
                "publication_year": paper.publication_year,
                "journal": paper.journal.name if paper.journal else None
            })

            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    def _optimize_for_agents(
        self,
        chunks: List[AcademicChunk],
        optimization_level: OptimizationLevel,
        agent_context: Optional[str]
    ) -> List[AcademicChunk]:
        """Optimize chunks for AI agent processing."""
        config = self._optimization_configs[optimization_level]
        optimized_chunks = []

        for chunk in chunks:
            # Apply size optimization
            if not (config["chunk_size_range"][0] <=
                    chunk.word_count <=
                    config["chunk_size_range"][1]):
                # Chunk needs resizing - would implement splitting/merging logic
                pass

            # Add agent optimization metadata
            agent_metadata = {
                "optimization_level": optimization_level.value,
                "agent_context": agent_context,
                "processing_hints": self._generate_processing_hints(chunk, config)
            }

            chunk.metadata.update(agent_metadata)
            optimized_chunks.append(chunk)

        return optimized_chunks

    def _assess_chunk_quality(
        self,
        chunks: List[AcademicChunk],
        paper: ResearchPaper
    ) -> List[AcademicChunk]:
        """Assess and filter chunks by quality."""
        quality_chunks = []

        for chunk in chunks:
            quality_score = self._calculate_chunk_quality_score(chunk, paper)
            
            # Update chunk with quality score
            chunk.quality_score = quality_score

            # Only include chunks above quality threshold
            if quality_score >= 0.6:  # Configurable threshold
                quality_chunks.append(chunk)

        return quality_chunks

    def _extract_semantic_context(
        self,
        chunk: AcademicChunk,
        enhancement_level: str
    ) -> SemanticContext:
        """Extract semantic context from chunk."""
        # Simplified semantic analysis
        key_concepts = self._extract_key_concepts(chunk.content)
        
        # Identify academic domain
        domain = self._identify_academic_domain(chunk.content, key_concepts)
        
        # Extract methodology context
        methodology_context = self._extract_methodology_context(chunk.content)
        
        return SemanticContext(
            key_concepts=key_concepts,
            related_terms=self._find_related_terms(key_concepts),
            academic_domain=domain,
            methodology_context=methodology_context,
            research_context=self._extract_research_context(chunk.content)
        )

    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key academic concepts from content."""
        # Simplified concept extraction using patterns
        academic_terms = []
        
        # Look for methodology terms
        methodology_patterns = [
            r'\b(experimental|observational|qualitative|quantitative)\b',
            r'\b(randomized|controlled|systematic)\b',
            r'\b(meta-analysis|review|survey)\b'
        ]
        
        for pattern in methodology_patterns:
            matches = re.findall(pattern, content.lower())
            academic_terms.extend(matches)
        
        # Look for statistical terms
        statistical_patterns = [
            r'\b(p-value|confidence|significant|correlation)\b',
            r'\b(regression|anova|t-test|chi-square)\b'
        ]
        
        for pattern in statistical_patterns:
            matches = re.findall(pattern, content.lower())
            academic_terms.extend(matches)
        
        # Remove duplicates and return
        return list(set(academic_terms))

    def _analyze_qa_suitability(
        self,
        chunk: AcademicChunk,
        question_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze chunk suitability for QA tasks."""
        # Simplified QA analysis
        suitability_score = 0.5  # Base score
        
        # Check for factual content indicators
        if any(indicator in chunk.content.lower() for indicator in 
               ["results", "findings", "data", "statistics"]):
            suitability_score += 0.2
        
        # Check for analytical content
        if any(indicator in chunk.content.lower() for indicator in 
               ["analysis", "interpretation", "discussion", "conclusion"]):
            suitability_score += 0.2
        
        # Check for methodological content
        if any(indicator in chunk.content.lower() for indicator in 
               ["method", "procedure", "approach", "design"]):
            suitability_score += 0.1
        
        return {
            "suitability_score": min(1.0, suitability_score),
            "content_types": self._identify_content_types(chunk.content),
            "answer_potential": self._assess_answer_potential(chunk.content)
        }

    def _apply_qa_optimizations(
        self,
        chunk: AcademicChunk,
        qa_metrics: Dict[str, Any]
    ) -> AcademicChunk:
        """Apply QA-specific optimizations to chunk."""
        # Add QA metadata
        qa_metadata = chunk.metadata.copy()
        qa_metadata.update({
            "qa_optimized": True,
            "qa_score": qa_metrics["suitability_score"],
            "content_types": qa_metrics["content_types"],
            "answer_potential": qa_metrics["answer_potential"]
        })
        
        # Create optimized chunk
        optimized_chunk = AcademicChunk(
            paper_id=chunk.paper_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            chunk_type=chunk.chunk_type,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            word_count=chunk.word_count,
            section_title=chunk.section_title,
            academic_context=chunk.academic_context,
            citations=chunk.citations,
            metadata=qa_metadata,
            quality_score=chunk.quality_score,
            created_at=chunk.created_at
        )
        
        return optimized_chunk

    def _assess_summarization_value(
        self,
        chunk: AcademicChunk,
        summary_type: str
    ) -> Dict[str, Any]:
        """Assess chunk value for summarization."""
        summarization_score = 0.5
        
        # Type-specific scoring
        if summary_type == "comprehensive":
            if chunk.section_title and "introduction" in chunk.section_title.lower():
                summarization_score += 0.2
            if "conclusion" in chunk.content.lower() or "findings" in chunk.content.lower():
                summarization_score += 0.3
        elif summary_type == "methodological":
            if "method" in chunk.content.lower() or "procedure" in chunk.content.lower():
                summarization_score += 0.4
        
        return {
            "summarization_score": min(1.0, summarization_score),
            "content_importance": self._assess_content_importance(chunk),
            "summary_role": self._determine_summary_role(chunk, summary_type)
        }

    def _apply_summarization_optimizations(
        self,
        chunk: AcademicChunk,
        summary_metrics: Dict[str, Any],
        summary_type: str
    ) -> AcademicChunk:
        """Apply summarization optimizations."""
        summary_metadata = chunk.metadata.copy()
        summary_metadata.update({
            "summarization_optimized": True,
            "summary_score": summary_metrics["summarization_score"],
            "summary_type": summary_type,
            "content_importance": summary_metrics["content_importance"],
            "summary_role": summary_metrics["summary_role"]
        })
        
        optimized_chunk = AcademicChunk(
            paper_id=chunk.paper_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            chunk_type=chunk.chunk_type,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            word_count=chunk.word_count,
            section_title=chunk.section_title,
            academic_context=chunk.academic_context,
            citations=chunk.citations,
            metadata=summary_metadata,
            quality_score=chunk.quality_score,
            created_at=chunk.created_at
        )
        
        return optimized_chunk

    # Placeholder methods for additional functionality
    def _store_batch_processing_stats(self, stats):
        """Store batch processing statistics."""
        pass

    def _calculate_chunk_quality_score(self, chunk, paper):
        """Calculate overall quality score for chunk."""
        return 0.8  # Placeholder

    def _identify_academic_domain(self, content, concepts):
        """Identify academic domain from content."""
        return "general"  # Placeholder

    def _extract_methodology_context(self, content):
        """Extract methodology context."""
        return None  # Placeholder

    def _extract_research_context(self, content):
        """Extract research context."""
        return None  # Placeholder

    def _find_related_terms(self, concepts):
        """Find related terms for concepts."""
        return []  # Placeholder

    def _generate_processing_hints(self, chunk, config):
        """Generate processing hints for agents."""
        return {}  # Placeholder

    def _identify_content_types(self, content):
        """Identify types of content in chunk."""
        return []  # Placeholder

    def _assess_answer_potential(self, content):
        """Assess potential for answering questions."""
        return 0.5  # Placeholder

    def _assess_content_importance(self, chunk):
        """Assess importance of chunk content."""
        return 0.5  # Placeholder

    def _determine_summary_role(self, chunk, summary_type):
        """Determine role in summary."""
        return "supporting"  # Placeholder

    def _calculate_indexing_summary(self, papers):
        """Calculate indexing summary statistics."""
        return {"total_papers": len(papers)}

    def _calculate_quality_metrics(self, papers):
        """Calculate quality metrics."""
        return {}

    def _analyze_optimization_effectiveness(self, papers):
        """Analyze optimization effectiveness."""
        return {}

    def _get_performance_statistics(self):
        """Get performance statistics."""
        return {}

    def _generate_indexing_recommendations(self, papers, report):
        """Generate indexing recommendations."""
        return ["Consider reindexing papers older than 6 months"]


class AcademicChunkingError(Exception):
    """Exception for academic chunking operations."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause