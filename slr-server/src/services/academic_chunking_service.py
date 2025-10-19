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
import logging

from ..domain.models import ResearchPaper, AcademicChunk
from ..repositories.paper_repository import PaperRepository
from ..repositories.chunk_repository import ChunkRepository
from ..chunking.strategy_factory import AcademicChunkingStrategyFactory

logger = logging.getLogger(__name__)


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

    def __init__(self, paper_repository: PaperRepository, chunk_repository: ChunkRepository):
        """
        Initialize AcademicChunkingService.

        Args:
            paper_repository: Repository for research paper access
            chunk_repository: Repository for academic chunk storage
        """
        self.paper_repository = paper_repository
        self.chunk_repository = chunk_repository
        self.strategy_factory = AcademicChunkingStrategyFactory()
        self._optimization_configs = self._initialize_optimization_configs()
        self._quality_metrics = self._initialize_quality_metrics()

    @staticmethod
    def _normalize_section_type(section_type: str) -> str:
        """
        Normalize section types to valid database values.
        
        Database allows: title, abstract, introduction, methodology, results,
        discussion, conclusion, references, section, paragraph, figure, table,
        equation, citation
        
        Mapping:
        - methods/methodology -> methodology
        - findings/results -> results
        - background/body/unknown -> section
        - conclusion/conclusions -> conclusion
        - appendix -> section
        """
        section_lower = section_type.lower().strip()
        
        # Direct mappings
        valid_types = {
            'title', 'abstract', 'introduction', 'methodology', 'results',
            'discussion', 'conclusion', 'references', 'section', 'paragraph',
            'figure', 'table', 'equation', 'citation'
        }
        
        if section_lower in valid_types:
            return section_lower
        
        # Mapping invalid types to valid ones
        mapping = {
            'methods': 'methodology',
            'findings': 'results',
            'background': 'section',
            'body': 'section',
            'unknown': 'section',
            'appendix': 'section',
            'conclusions': 'conclusion',
        }
        
        return mapping.get(section_lower, 'section')  # Default to 'section'

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

        # Perform initial chunking with simple strategy
        raw_chunks = self._simple_chunk_content(paper, content, strategy)

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

        # Store chunks in database
        stored_chunks = []
        for chunk in quality_chunks:
            stored_chunk = self.chunk_repository.create(chunk)
            stored_chunks.append(stored_chunk)

        # Update paper indexing status
        paper.indexed = True
        self.paper_repository.update(paper)

        logger.info(f"Successfully indexed paper {paper_id} with {len(stored_chunks)} chunks")
        return stored_chunks

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
            section_type=chunk.section_type,
            title=chunk.title,
            word_count=chunk.word_count,
            citation_count=chunk.citation_count,
            figure_count=chunk.figure_count,
            table_count=chunk.table_count,
            research_elements=chunk.research_elements,
            semantic_tags=chunk.semantic_tags,
            metadata=enhanced_metadata,
            confidence_score=min(1.0, (chunk.confidence_score or 0.0) + 0.1),  # Boost for enhancement, capped at 1.0
            created_at=chunk.created_at
        )

        return enhanced_chunk

    def optimize_chunks_for_qa(
        self,
        chunks: List[AcademicChunk],
        question_types: Optional[List[str]] = None
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
        paper_ids: Optional[List[int]] = None,
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
            # Check last indexing time (could be stored in notes or other field)
            # For now, just proceed with reindexing if requested
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
            "basic": {
                "chunk_size_range": (200, 800),
                "overlap": 50,
                "semantic_enhancement": False,
                "citation_preservation": True,
                "context_expansion": False
            },
            "intermediate": {
                "chunk_size_range": (300, 1200),
                "overlap": 100,
                "semantic_enhancement": True,
                "citation_preservation": True,
                "context_expansion": True
            },
            "advanced": {
                "chunk_size_range": (400, 1500),
                "overlap": 150,
                "semantic_enhancement": True,
                "citation_preservation": True,
                "context_expansion": True,
                "cross_reference": True
            },
            "expert": {
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
        import os
        import PyPDF2
        import fitz  # pymupdf
        from pathlib import Path
        
        # Start with basic metadata
        content = f"Title: {paper.title}\n\n"
        if paper.abstract:
            content += f"Abstract: {paper.abstract}\n\n"
        
        # Try to extract from actual file if available
        if paper.file_path and os.path.exists(paper.file_path):
            try:
                file_path = Path(paper.file_path)
                file_extension = file_path.suffix.lower()
                
                if file_extension == '.pdf':
                    content += self._extract_from_pdf(paper.file_path)
                elif file_extension in ['.txt', '.md']:
                    content += self._extract_from_text_file(paper.file_path)
                elif file_extension in ['.doc', '.docx']:
                    content += self._extract_from_word_doc(paper.file_path)
                else:
                    # Fallback for unknown file types
                    content += f"[Note: File type {file_extension} not fully supported, using metadata only]"
                    
            except Exception as e:
                # If file extraction fails, log the error and continue with metadata
                content += f"[Note: Could not extract full text from file: {str(e)}]"
        else:
            # No file available, use metadata only
            if paper.keywords:
                content += f"Keywords: {', '.join(paper.keywords)}\n\n"
            
            content += "[Note: Full text not available, using metadata only]"
        
        return content.strip()

    def _simple_chunk_content(self, paper: ResearchPaper, content: str, strategy: IndexingStrategy) -> List[AcademicChunk]:
        """Simple chunking implementation as fallback."""
        chunks = []
        
        # Split content into paragraphs (simple strategy)
        paragraphs = content.split('\n\n')
        
        # Target chunk size (words)
        target_size = 300
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Check if adding this paragraph would exceed target size
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            potential_word_count = len(potential_chunk.split())
            
            if potential_word_count <= target_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk = AcademicChunk(
                        paper_id=paper.id or 0,
                        chunk_index=chunk_index,
                        content=current_chunk,
                        section_type="introduction",  # Use valid type for both model and DB
                        word_count=len(current_chunk.split()),
                        confidence_score=0.7,
                        metadata={"source": "simple_chunking"}
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk with current paragraph
                current_chunk = paragraph
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk = AcademicChunk(
                paper_id=paper.id or 0,
                chunk_index=chunk_index,
                content=current_chunk,
                section_type="introduction",  # Use valid type for both model and DB
                word_count=len(current_chunk.split()),
                confidence_score=0.7,
                metadata={"source": "simple_chunking"}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            # Try pymupdf first (better text extraction)
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
            
        except ImportError:
            # Fallback to PyPDF2 if pymupdf not available
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            except Exception as e:
                return f"[PDF extraction failed: {str(e)}]"
        except Exception as e:
            # If pymupdf fails, try PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            except Exception as e2:
                return f"[PDF extraction failed: {str(e)} / {str(e2)}]"
    
    def _extract_from_text_file(self, file_path: str) -> str:
        """Extract content from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue
            return "[Text file encoding not supported]"
        except Exception as e:
            return f"[Text extraction failed: {str(e)}]"
    
    def _extract_from_word_doc(self, file_path: str) -> str:
        """Extract content from Word document."""
        try:
            # Try to import python-docx if available
            import docx
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text).strip()
        except ImportError:
            return "[Word document extraction requires python-docx package]"
        except Exception as e:
            return f"[Word document extraction failed: {str(e)}]"

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
        config = self._optimization_configs[optimization_level.value]

        for chunk in chunks:
            enhanced_chunk = chunk

            # Apply semantic enhancement if configured
            if config.get("semantic_enhancement"):
                enhanced_chunk = self.enhance_chunk_semantically(chunk)

            # Add academic metadata to chunk metadata
            enhanced_chunk.metadata.update({
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
        config = self._optimization_configs[optimization_level.value]
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
            chunk.confidence_score = quality_score

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
            section_type=chunk.section_type,
            title=chunk.title,
            word_count=chunk.word_count,
            citation_count=chunk.citation_count,
            figure_count=chunk.figure_count,
            table_count=chunk.table_count,
            research_elements=chunk.research_elements,
            semantic_tags=chunk.semantic_tags,
            metadata=qa_metadata,
            confidence_score=chunk.confidence_score,
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
            if chunk.title and "introduction" in chunk.title.lower():
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
            section_type=chunk.section_type,
            title=chunk.title,
            word_count=chunk.word_count,
            citation_count=chunk.citation_count,
            figure_count=chunk.figure_count,
            table_count=chunk.table_count,
            research_elements=chunk.research_elements,
            semantic_tags=chunk.semantic_tags,
            metadata=summary_metadata,
            confidence_score=chunk.confidence_score,
            created_at=chunk.created_at
        )
        
        return optimized_chunk

    # ===== PDF Extraction Methods =====
    
    def _extract_paper_content(self, paper: ResearchPaper) -> Optional[str]:
        """
        Extract text content from a research paper file (PDF).
        
        Args:
            paper: Research paper with file_path
            
        Returns:
            Extracted text content or None if extraction fails
        """
        if not paper.file_path:
            logger.warning(f"Paper {paper.id} has no file_path")
            return None
        
        try:
            # Handle both Windows and Unix-style paths
            file_path = paper.file_path.replace('/c/', 'c:/').replace('\\', '/')
            
            # Check if file exists
            import os
            if not os.path.exists(file_path):
                logger.warning(f"Paper {paper.id}: File not found at {file_path}")
                return None
            
            # Only process PDF files
            if not file_path.lower().endswith('.pdf'):
                logger.debug(f"Paper {paper.id}: Skipping non-PDF file ({file_path})")
                return None
            
            # Extract PDF text using pypdf
            try:
                from pypdf import PdfReader
            except ImportError:
                try:
                    from PyPDF2 import PdfReader
                except ImportError:
                    logger.error("PDF library not available. Install: pip install pypdf")
                    return None
            
            reader = PdfReader(file_path)
            text_content = []
            
            # Extract text from all pages
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(f"Paper {paper.id}: Error extracting page {page_num}: {e}")
                    # Continue with other pages
                    continue
            
            if not text_content:
                logger.warning(f"Paper {paper.id}: No text extracted from PDF")
                return None
            
            combined_content = "\n\n".join(text_content)
            logger.info(f"Paper {paper.id}: Extracted {len(combined_content)} characters from PDF")
            return combined_content
            
        except Exception as e:
            logger.error(f"Paper {paper.id}: Error extracting content: {e}")
            return None
    
    def _simple_chunk_content(
        self, 
        paper: ResearchPaper, 
        content: str, 
        strategy: IndexingStrategy
    ) -> List[AcademicChunk]:
        """
        Create initial chunks using the specified strategy.
        
        Args:
            paper: Research paper metadata
            content: Extracted text content
            strategy: Chunking strategy to use
            
        Returns:
            List of raw academic chunks
        """
        if not content or len(content.strip()) < 10:
            logger.warning(f"Paper {paper.id}: Content too short for chunking ({len(content)} chars)")
            return []
        
        try:
            # Get strategy from factory
            chunking_strategy = self.strategy_factory.get_strategy(paper, content)
            
            # Apply strategy chunking
            chunks = chunking_strategy.chunk(paper, content)
            logger.info(f"Paper {paper.id}: Created {len(chunks)} chunks using {chunking_strategy.get_strategy_name()}")
            return chunks
            
        except Exception as e:
            logger.error(f"Paper {paper.id}: Error in strategy chunking: {e}")
            # Fall back to simple chunking
            return self._fallback_chunk_by_paragraphs(paper, content)
    
    def _fallback_chunk_by_paragraphs(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """
        Simple fallback: chunk by paragraphs when strategies fail.
        
        Args:
            paper: Research paper
            content: Text content
            
        Returns:
            List of chunks split by paragraphs
        """
        chunks = []
        paragraphs = content.split('\n\n')
        
        for chunk_idx, para in enumerate(paragraphs):
            if len(para.strip()) < 10:  # Skip very short paragraphs
                continue
            
            word_count = len(para.split())
            chunk = AcademicChunk(
                paper_id=paper.id,
                chunk_index=chunk_idx,
                content=para,
                section_type='paragraph',  # Use 'paragraph' instead of 'body'
                title=None,
                word_count=word_count,
                citation_count=0,
                figure_count=0,
                table_count=0,
                research_elements=[],
                semantic_tags=[],
                metadata={'extraction_method': 'fallback_paragraph'},
                confidence_score=0.5,
                created_at=datetime.now()
            )
            chunks.append(chunk)
        
        logger.info(f"Paper {paper.id}: Created {len(chunks)} fallback chunks")
        return chunks
    
    def _apply_academic_enhancements(
        self,
        chunks: List[AcademicChunk],
        paper: ResearchPaper,
        optimization_level: OptimizationLevel
    ) -> List[AcademicChunk]:
        """
        Apply academic enhancements to raw chunks.
        
        Args:
            chunks: Raw chunks from strategy
            paper: Research paper metadata
            optimization_level: Optimization level
            
        Returns:
            Enhanced chunks
        """
        enhanced_chunks = []
        
        for chunk in chunks:
            # Extract key concepts
            key_concepts = self._extract_key_concepts(chunk.content)
            
            # Count citations (simple regex-based)
            citation_count = len(self._find_citations_in_text(chunk.content))
            
            # Detect research elements
            research_elements = self._detect_research_elements(chunk.content)
            
            # Generate semantic tags
            semantic_tags = self._generate_semantic_tags(chunk.content, key_concepts)
            
            # Update chunk
            enhanced_chunk = AcademicChunk(
                paper_id=chunk.paper_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                section_type=chunk.section_type,
                title=chunk.title,
                word_count=chunk.word_count,
                citation_count=citation_count,
                figure_count=chunk.figure_count,
                table_count=chunk.table_count,
                research_elements=research_elements,
                semantic_tags=semantic_tags,
                metadata={
                    **chunk.metadata,
                    'key_concepts': key_concepts,
                    'enhanced': True,
                    'optimization_level': optimization_level.value if hasattr(optimization_level, 'value') else str(optimization_level)
                },
                confidence_score=self._calculate_chunk_confidence(chunk),
                created_at=chunk.created_at
            )
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _optimize_for_agents(
        self,
        chunks: List[AcademicChunk],
        optimization_level: OptimizationLevel,
        agent_context: Optional[str]
    ) -> List[AcademicChunk]:
        """
        Optimize chunks for AI agent processing.
        
        Args:
            chunks: Enhanced chunks
            optimization_level: Optimization level
            agent_context: Optional context for agents
            
        Returns:
            Agent-optimized chunks
        """
        optimized_chunks = []
        
        for chunk in chunks:
            metadata = chunk.metadata.copy()
            metadata['agent_context'] = agent_context or 'general_analysis'
            metadata['optimization_level'] = optimization_level.value if hasattr(optimization_level, 'value') else str(optimization_level)
            
            # Add processing hints
            metadata['processing_hints'] = self._generate_processing_hints(chunk, metadata)
            
            optimized_chunk = AcademicChunk(
                paper_id=chunk.paper_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                section_type=chunk.section_type,
                title=chunk.title,
                word_count=chunk.word_count,
                citation_count=chunk.citation_count,
                figure_count=chunk.figure_count,
                table_count=chunk.table_count,
                research_elements=chunk.research_elements,
                semantic_tags=chunk.semantic_tags,
                metadata=metadata,
                confidence_score=chunk.confidence_score,
                created_at=chunk.created_at
            )
            optimized_chunks.append(optimized_chunk)
        
        return optimized_chunks
    
    def _assess_chunk_quality(
        self,
        chunks: List[AcademicChunk],
        paper: ResearchPaper
    ) -> List[AcademicChunk]:
        """
        Assess and filter chunks by quality.
        
        Args:
            chunks: Chunks to assess
            paper: Research paper
            
        Returns:
            Quality-assessed chunks
        """
        quality_chunks = []
        
        for chunk in chunks:
            # Calculate quality score
            quality_score = self._calculate_chunk_quality_score(chunk, paper)
            
            # Update metadata with quality info
            metadata = chunk.metadata.copy()
            metadata['quality_score'] = quality_score
            
            # Set confidence based on quality
            confidence = min(1.0, quality_score)
            
            quality_chunk = AcademicChunk(
                paper_id=chunk.paper_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                section_type=chunk.section_type,
                title=chunk.title,
                word_count=chunk.word_count,
                citation_count=chunk.citation_count,
                figure_count=chunk.figure_count,
                table_count=chunk.table_count,
                research_elements=chunk.research_elements,
                semantic_tags=chunk.semantic_tags,
                metadata=metadata,
                confidence_score=confidence,
                created_at=chunk.created_at
            )
            
            # Only include chunks with reasonable quality
            if quality_score > 0.2:  # Very low threshold to include fallback chunks
                quality_chunks.append(quality_chunk)
        
        return quality_chunks
    
    # ===== Helper Methods for Content Analysis =====
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content using simple heuristics."""
        concepts = []
        
        # Find words in all caps (often indicate key terms)
        import re
        all_caps = re.findall(r'\b([A-Z]{2,})\b', content)
        concepts.extend(list(set(all_caps))[:10])
        
        # Find common academic terms
        academic_terms = ['hypothesis', 'methodology', 'algorithm', 'framework', 'system', 'approach', 'analysis', 'evaluation']
        for term in academic_terms:
            if term.lower() in content.lower():
                concepts.append(term)
        
        return list(set(concepts))[:20]  # Return unique, limit to 20
    
    def _find_citations_in_text(self, content: str) -> List[str]:
        """Find citation patterns in text."""
        import re
        # Simple citation patterns: [1], (Author, year), etc.
        patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\([A-Z][a-z]+,\s*\d{4}\)',  # (Author, 2021)
            r'et\s+al\.\s*\(\d{4}\)'  # et al. (2021)
        ]
        
        citations = []
        for pattern in patterns:
            citations.extend(re.findall(pattern, content))
        
        return citations
    
    def _detect_research_elements(self, content: str) -> List[str]:
        """Detect research elements in content."""
        elements = []
        content_lower = content.lower()
        
        # Check for research method indicators
        if 'hypothesis' in content_lower or 'hypothes' in content_lower:
            elements.append('hypothesis')
        if 'objective' in content_lower or 'aim' in content_lower:
            elements.append('objective')
        if 'method' in content_lower or 'procedure' in content_lower:
            elements.append('methodology')
        if 'result' in content_lower or 'finding' in content_lower or 'outcome' in content_lower:
            elements.append('result')
        if 'conclusion' in content_lower or 'conclude' in content_lower:
            elements.append('conclusion')
        if 'limitation' in content_lower:
            elements.append('limitation')
        
        return elements
    
    def _generate_semantic_tags(self, content: str, concepts: List[str]) -> List[str]:
        """Generate semantic tags for content."""
        tags = []
        content_lower = content.lower()
        
        # Research method tags
        if 'quantitative' in content_lower or 'statistical' in content_lower or 'numerical' in content_lower:
            tags.append('quantitative')
        if 'qualitative' in content_lower or 'interview' in content_lower or 'thematic' in content_lower:
            tags.append('qualitative')
        if 'experiment' in content_lower or 'control group' in content_lower:
            tags.append('experimental')
        
        # Add concepts as tags
        tags.extend(concepts[:5])
        
        return list(set(tags))[:15]
    
    def _calculate_chunk_confidence(self, chunk: AcademicChunk) -> float:
        """Calculate confidence score for chunk."""
        score = 0.5  # Base score
        
        # Increase confidence if chunk has content
        if chunk.word_count and chunk.word_count > 50:
            score += 0.2
        
        # Increase if it has research elements
        if chunk.research_elements:
            score += 0.15
        
        # Increase if it has semantic tags
        if chunk.semantic_tags:
            score += 0.1
        
        # Increase if it has citations
        if chunk.citation_count and chunk.citation_count > 0:
            score += 0.05
        
        return min(1.0, score)
    
    # Placeholder methods for additional functionality
    def _store_batch_processing_stats(self, stats):
        """Store batch processing statistics."""
        # Store processing statistics for performance monitoring
        if not hasattr(self, '_batch_stats'):
            self._batch_stats = []
        
        # Add timestamp and standardize stats format
        batch_stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_papers': stats.get('total_papers', 0),
            'successful_papers': stats.get('successful_papers', 0),
            'failed_papers': stats.get('failed_papers', 0),
            'total_chunks': stats.get('total_chunks', 0),
            'processing_time': stats.get('processing_time', 0),
            'average_chunks_per_paper': stats.get('average_chunks_per_paper', 0),
            'errors': stats.get('errors', [])
        }
        
        self._batch_stats.append(batch_stats)
        
        # Keep only last 100 batch statistics to prevent memory bloat
        if len(self._batch_stats) > 100:
            self._batch_stats = self._batch_stats[-100:]
        
        # Log significant statistics
        if batch_stats['failed_papers'] > 0:
            logger.warning(f"Batch processing completed with {batch_stats['failed_papers']} failures")
        
        if batch_stats['processing_time'] > 300:  # 5 minutes
            logger.info(f"Long batch processing completed: {batch_stats['processing_time']}s for {batch_stats['total_papers']} papers")

    def _calculate_chunk_quality_score(self, chunk, paper):
        """Calculate overall quality score for chunk."""
        score = 0.0
        
        # Content length score (0.0-0.2)
        word_count = chunk.word_count or 0
        if 50 <= word_count <= 500:
            score += 0.2
        elif word_count > 20:
            score += 0.1
        
        # Citation score (0.0-0.2)
        citation_count = chunk.citation_count or 0
        if citation_count > 0:
            score += min(0.2, citation_count * 0.05)
        
        # Research elements score (0.0-0.2)
        if chunk.research_elements:
            score += min(0.2, len(chunk.research_elements) * 0.04)
        
        # Semantic tags score (0.0-0.2)
        if chunk.semantic_tags:
            score += min(0.2, len(chunk.semantic_tags) * 0.03)
        
        # Section type score (0.0-0.2)
        if chunk.section_type in ['methods', 'results', 'discussion']:
            score += 0.2
        elif chunk.section_type in ['introduction', 'conclusion']:
            score += 0.15
        elif chunk.section_type in ['abstract', 'references']:
            score += 0.1
        
        return min(1.0, score)

    def _identify_academic_domain(self, content, concepts):
        """Identify academic domain from content."""
        content_lower = content.lower()
        concepts_text = ' '.join(concepts).lower() if concepts else ''
        combined_text = content_lower + ' ' + concepts_text
        
        # Define domain keywords
        domain_keywords = {
            'medicine': ['patient', 'clinical', 'medical', 'health', 'diagnosis', 'treatment', 'therapy'],
            'computer_science': ['algorithm', 'software', 'computing', 'data', 'machine learning', 'ai'],
            'engineering': ['system', 'design', 'architecture', 'performance', 'optimization'],
            'psychology': ['behavior', 'cognitive', 'mental', 'psychological', 'participants'],
            'education': ['learning', 'students', 'teaching', 'curriculum', 'academic'],
            'biology': ['biological', 'species', 'genetic', 'molecular', 'cells'],
            'physics': ['physical', 'quantum', 'energy', 'matter', 'particles'],
            'chemistry': ['chemical', 'molecules', 'reactions', 'compounds'],
            'mathematics': ['statistical', 'mathematical', 'equations', 'proof', 'theorem'],
            'social_science': ['social', 'society', 'cultural', 'community', 'demographic']
        }
        
        # Score each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores.keys(), key=lambda x: domain_scores[x])
        
        return "general"

    def _extract_methodology_context(self, content):
        """Extract methodology context."""
        content_lower = content.lower()
        
        methodology_indicators = {
            'quantitative': ['statistical', 'regression', 'analysis', 'survey', 'questionnaire', 'sample size'],
            'qualitative': ['interview', 'thematic', 'grounded theory', 'phenomenological', 'ethnographic'],
            'mixed_methods': ['mixed methods', 'triangulation', 'convergent', 'sequential'],
            'experimental': ['experiment', 'randomized', 'control group', 'intervention', 'treatment'],
            'systematic_review': ['systematic review', 'meta-analysis', 'prisma', 'cochrane'],
            'case_study': ['case study', 'single case', 'multiple cases'],
            'longitudinal': ['longitudinal', 'follow-up', 'time series', 'cohort'],
            'cross_sectional': ['cross-sectional', 'cross sectional', 'snapshot']
        }
        
        detected_methods = []
        for method_type, indicators in methodology_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                detected_methods.append(method_type)
        
        if detected_methods:
            primary_method = detected_methods[0]
            additional_info = []
            
            if any(method in detected_methods for method in ['quantitative', 'qualitative', 'experimental']):
                additional_info.append('empirical')
            if 'systematic_review' in detected_methods:
                additional_info.append('review')
            
            context = primary_method
            if len(detected_methods) > 1:
                context += f" with {', '.join(detected_methods[1:])}"
            if additional_info:
                context += f" ({', '.join(additional_info)})"
            
            return context
        
        return None

    def _extract_research_context(self, content):
        """Extract research context."""
        content_lower = content.lower()
        
        context_indicators = {
            'hypothesis_testing': ['hypothesis', 'hypothesize', 'predict', 'expect'],
            'problem_solving': ['problem', 'challenge', 'issue', 'difficulty'],
            'literature_review': ['previous studies', 'prior research', 'literature shows'],
            'data_analysis': ['data', 'results', 'findings', 'analysis'],
            'methodology': ['method', 'approach', 'procedure', 'technique'],
            'theoretical': ['theory', 'theoretical', 'framework', 'model'],
            'practical': ['application', 'implementation', 'practice', 'real-world'],
            'comparative': ['compare', 'comparison', 'versus', 'contrast'],
            'evaluation': ['evaluate', 'assessment', 'performance', 'effectiveness']
        }
        
        detected_contexts = []
        for context_type, indicators in context_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                detected_contexts.append(context_type)
        
        if detected_contexts:
            primary_context = detected_contexts[0]
            if len(detected_contexts) > 1:
                return f"{primary_context} with {', '.join(detected_contexts[1:3])}"  # Limit to 3 contexts
            return primary_context
        
        return None

    def _find_related_terms(self, concepts):
        """Find related terms for concepts."""
        if not concepts:
            return []
        
        # Simple related terms mapping (in a full implementation, this could use word embeddings)
        related_terms_map = {
            # Research methods
            'statistical': ['quantitative', 'analysis', 'significance', 'correlation'],
            'qualitative': ['interview', 'thematic', 'narrative', 'phenomenological'],
            'experimental': ['control', 'treatment', 'randomized', 'intervention'],
            
            # Computer science
            'algorithm': ['computational', 'optimization', 'efficiency', 'complexity'],
            'machine learning': ['ai', 'neural network', 'training', 'prediction'],
            'software': ['development', 'programming', 'coding', 'implementation'],
            
            # Medicine
            'clinical': ['patient', 'treatment', 'diagnosis', 'medical'],
            'therapy': ['treatment', 'intervention', 'healing', 'rehabilitation'],
            'diagnosis': ['clinical', 'symptoms', 'medical', 'assessment'],
            
            # General research
            'analysis': ['examination', 'evaluation', 'assessment', 'investigation'],
            'methodology': ['approach', 'method', 'technique', 'procedure'],
            'findings': ['results', 'outcomes', 'conclusions', 'discoveries']
        }
        
        related_terms = []
        for concept in concepts:
            concept_lower = concept.lower()
            for key_term, related in related_terms_map.items():
                if key_term in concept_lower:
                    related_terms.extend(related)
        
        # Remove duplicates and return unique related terms
        return list(set(related_terms))[:10]  # Limit to 10 related terms

    def _generate_processing_hints(self, chunk, config):
        """Generate processing hints for agents."""
        hints = {}
        
        # Content-based hints
        if chunk.citation_count and chunk.citation_count > 3:
            hints['high_citation_density'] = True
            hints['good_for_reference_extraction'] = True
        
        if chunk.section_type == 'methods':
            hints['contains_methodology'] = True
            hints['good_for_reproducibility'] = True
        elif chunk.section_type == 'results':
            hints['contains_findings'] = True
            hints['good_for_data_extraction'] = True
        elif chunk.section_type == 'discussion':
            hints['contains_interpretation'] = True
            hints['good_for_implications'] = True
        
        # Research elements hints
        if chunk.research_elements:
            if any('hypothesis' in element.lower() for element in chunk.research_elements):
                hints['contains_hypotheses'] = True
            if any('conclusion' in element.lower() for element in chunk.research_elements):
                hints['contains_conclusions'] = True
        
        # Semantic tags hints
        if chunk.semantic_tags:
            if 'quantitative' in chunk.semantic_tags:
                hints['numerical_analysis_possible'] = True
            if 'qualitative' in chunk.semantic_tags:
                hints['thematic_analysis_possible'] = True
        
        # Quality hints based on confidence score
        if hasattr(chunk, 'confidence_score') and chunk.confidence_score:
            if chunk.confidence_score > 0.8:
                hints['high_quality_content'] = True
            elif chunk.confidence_score < 0.4:
                hints['requires_careful_processing'] = True
        
        # Size-based hints
        word_count = chunk.word_count or 0
        if word_count > 300:
            hints['long_content'] = True
            hints['may_need_subdivision'] = True
        elif word_count < 50:
            hints['short_content'] = True
            hints['may_need_context'] = True
        
        return hints

    def _identify_content_types(self, content):
        """Identify types of content in chunk."""
        content_lower = content.lower()
        content_types = []
        
        # Text-based content types
        if any(word in content_lower for word in ['table', 'row', 'column', 'data']):
            content_types.append('tabular_data')
        
        if any(word in content_lower for word in ['figure', 'graph', 'chart', 'plot']):
            content_types.append('visual_data')
        
        if any(word in content_lower for word in ['equation', 'formula', 'mathematical']):
            content_types.append('mathematical')
        
        if any(word in content_lower for word in ['code', 'algorithm', 'programming']):
            content_types.append('computational')
        
        if any(word in content_lower for word in ['quote', 'citation', 'reference']):
            content_types.append('referenced_content')
        
        if any(word in content_lower for word in ['hypothesis', 'theory', 'theoretical']):
            content_types.append('theoretical')
        
        if any(word in content_lower for word in ['experiment', 'test', 'trial', 'study']):
            content_types.append('empirical')
        
        if any(word in content_lower for word in ['conclusion', 'summary', 'findings']):
            content_types.append('conclusive')
        
        if any(word in content_lower for word in ['method', 'procedure', 'approach']):
            content_types.append('methodological')
        
        if any(word in content_lower for word in ['result', 'outcome', 'finding']):
            content_types.append('results')
        
        # Default to text if no specific types identified
        if not content_types:
            content_types.append('text')
        
        return content_types

    def _assess_answer_potential(self, content):
        """Assess potential for answering questions."""
        content_lower = content.lower()
        score = 0.0
        
        # High-value question answering indicators
        high_value_indicators = [
            'results show', 'findings indicate', 'conclude that', 'demonstrate that',
            'evidence suggests', 'study found', 'analysis revealed', 'data shows'
        ]
        
        for indicator in high_value_indicators:
            if indicator in content_lower:
                score += 0.2
        
        # Medium-value indicators
        medium_value_indicators = [
            'method', 'approach', 'technique', 'procedure',
            'definition', 'concept', 'theory', 'framework'
        ]
        
        for indicator in medium_value_indicators:
            if indicator in content_lower:
                score += 0.1
        
        # Question words and patterns that suggest Q&A potential
        question_patterns = [
            'what', 'how', 'why', 'when', 'where', 'which',
            'can be', 'is defined as', 'refers to', 'means that'
        ]
        
        for pattern in question_patterns:
            if pattern in content_lower:
                score += 0.05
        
        # Factual content indicators
        factual_indicators = [
            'significant', 'p <', 'correlation', 'coefficient',
            'percentage', '%', 'ratio', 'rate', 'frequency'
        ]
        
        for indicator in factual_indicators:
            if indicator in content_lower:
                score += 0.05
        
        return min(1.0, score)

    def _assess_content_importance(self, chunk):
        """Assess importance of chunk content."""
        importance_score = 0.0
        
        # Section type importance
        section_importance = {
            'abstract': 0.9,
            'introduction': 0.7,
            'methods': 0.8,
            'results': 0.9,
            'discussion': 0.8,
            'conclusion': 0.9,
            'references': 0.3,
            'appendix': 0.4
        }
        
        if chunk.section_type:
            importance_score += section_importance.get(chunk.section_type, 0.5)
        
        # Citation density importance
        word_count = chunk.word_count or 1
        citation_density = (chunk.citation_count or 0) / word_count
        if citation_density > 0.1:  # High citation density
            importance_score += 0.2
        elif citation_density > 0.05:
            importance_score += 0.1
        
        # Research elements importance
        if chunk.research_elements:
            element_count = len(chunk.research_elements)
            importance_score += min(0.2, element_count * 0.05)
        
        # Semantic tags importance
        if chunk.semantic_tags:
            high_importance_tags = ['hypothesis', 'conclusion', 'methodology', 'results']
            important_tags = [tag for tag in chunk.semantic_tags if any(important in tag.lower() for important in high_importance_tags)]
            importance_score += min(0.2, len(important_tags) * 0.1)
        
        # Confidence score influence
        if hasattr(chunk, 'confidence_score') and chunk.confidence_score:
            importance_score += chunk.confidence_score * 0.1
        
        # Length consideration (very short or very long might be less important)
        if word_count < 20:
            importance_score *= 0.7  # Short chunks are often less important
        elif word_count > 1000:
            importance_score *= 0.8  # Very long chunks might be diluted
        
        return min(1.0, importance_score)

    def _determine_summary_role(self, chunk, summary_type):
        """Determine role in summary."""
        # Assess importance first
        importance = self._assess_content_importance(chunk)
        
        # Section-based role determination
        if chunk.section_type in ['abstract', 'conclusion']:
            if importance > 0.7:
                return "primary"
            else:
                return "key"
        
        elif chunk.section_type in ['results', 'findings']:
            if importance > 0.8:
                return "primary"
            elif importance > 0.6:
                return "key"
            else:
                return "supporting"
        
        elif chunk.section_type in ['methods', 'methodology']:
            if summary_type == "methodology_focused":
                return "primary" if importance > 0.7 else "key"
            else:
                return "supporting"
        
        elif chunk.section_type in ['introduction', 'background']:
            if summary_type == "comprehensive":
                return "supporting"
            else:
                return "background"
        
        elif chunk.section_type in ['discussion']:
            if importance > 0.8:
                return "key"
            else:
                return "supporting"
        
        # Content-based role determination
        if chunk.research_elements:
            key_elements = ['hypothesis', 'objective', 'conclusion', 'finding']
            if any(elem.lower() in chunk.research_elements for elem in key_elements):
                return "key" if importance > 0.6 else "supporting"
        
        # Citation-heavy chunks
        word_count = chunk.word_count or 1
        citation_density = (chunk.citation_count or 0) / word_count
        if citation_density > 0.1:
            return "reference" if summary_type == "detailed" else "supporting"
        
        # High-confidence, high-importance chunks
        if (hasattr(chunk, 'confidence_score') and chunk.confidence_score and 
            chunk.confidence_score > 0.8 and importance > 0.7):
            return "key"
        
        # Default role
        return "supporting"

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