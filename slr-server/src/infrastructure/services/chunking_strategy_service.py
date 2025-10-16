"""
Chunking Strategy Service Implementation

Handles different approaches to splitting content into chunks.
Follows SRP by only handling chunking strategy selection and execution.
"""

from typing import List
import logging

from domain.services.chunking_service import IChunkingStrategyService, IndexingStrategy
from domain.models import ResearchPaper, AcademicChunk

logger = logging.getLogger(__name__)


class ChunkingStrategyService(IChunkingStrategyService):
    """
    Chunking strategy service implementation.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles chunking strategy logic
    - Open/Closed: Can be extended with new chunking strategies
    - Dependency Inversion: Implements interface
    """
    
    def chunk_content(self, paper: ResearchPaper, content: str, strategy: IndexingStrategy) -> List[AcademicChunk]:
        """Chunk content using specified strategy."""
        if strategy == IndexingStrategy.HYBRID:
            return self._hybrid_chunking(paper, content)
        elif strategy == IndexingStrategy.SECTION_BASED:
            return self._section_based_chunking(paper, content)
        elif strategy == IndexingStrategy.CITATION_AWARE:
            return self._citation_aware_chunking(paper, content)
        elif strategy == IndexingStrategy.SEMANTIC:
            return self._semantic_chunking(paper, content)
        else:
            # Default to simple chunking
            return self._simple_chunking(paper, content)
    
    def select_optimal_strategy(self, paper: ResearchPaper, content: str) -> IndexingStrategy:
        """Select the best chunking strategy for given content."""
        # Simple heuristics for strategy selection
        content_lower = content.lower()
        
        # Check for academic sections
        section_indicators = ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion']
        section_count = sum(1 for indicator in section_indicators if indicator in content_lower)
        
        # Check for citations
        citation_indicators = ['et al.', 'references', 'bibliography', '[1]', '(2020)', '(2021)', '(2022)', '(2023)']
        citation_count = sum(1 for indicator in citation_indicators if indicator in content_lower)
        
        # Strategy selection logic
        if section_count >= 3 and citation_count >= 5:
            return IndexingStrategy.HYBRID
        elif section_count >= 3:
            return IndexingStrategy.SECTION_BASED
        elif citation_count >= 5:
            return IndexingStrategy.CITATION_AWARE
        else:
            return IndexingStrategy.SEMANTIC
    
    def _hybrid_chunking(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """Hybrid chunking combining section-based and semantic approaches."""
        # Try section-based first, fall back to semantic if sections not found
        sections = self._identify_sections(content)
        if len(sections) >= 2:
            return self._section_based_chunking(paper, content)
        else:
            return self._semantic_chunking(paper, content)
    
    def _section_based_chunking(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """Section-based chunking using academic paper structure."""
        sections = self._identify_sections(content)
        chunks = []
        
        for i, (section_title, section_content) in enumerate(sections):
            if section_content.strip():
                chunk = AcademicChunk(
                    paper_id=paper.id or 0,
                    chunk_index=i,
                    content=section_content,
                    section_type=self._classify_section_type(section_title),
                    title=section_title,
                    word_count=len(section_content.split()),
                    confidence_score=0.8,
                    metadata={"source": "section_based_chunking", "section_title": section_title}
                )
                chunks.append(chunk)
        
        return chunks
    
    def _citation_aware_chunking(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """Citation-aware chunking that preserves citation context."""
        # Split on paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        target_size = 400  # words
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            potential_word_count = len(potential_chunk.split())
            
            # Check if we should create a chunk
            if potential_word_count <= target_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk = self._create_chunk(paper, chunk_index, current_chunk, "citation_aware_chunking")
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(paper, chunk_index, current_chunk, "citation_aware_chunking")
            chunks.append(chunk)
        
        return chunks
    
    def _semantic_chunking(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """Semantic chunking based on topic coherence."""
        # Simple implementation - can be enhanced with NLP libraries
        sentences = content.split('.')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        target_size = 300  # words
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            potential_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            potential_word_count = len(potential_chunk.split())
            
            if potential_word_count <= target_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk
                if current_chunk:
                    chunk = self._create_chunk(paper, chunk_index, current_chunk, "semantic_chunking")
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk
                current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(paper, chunk_index, current_chunk, "semantic_chunking")
            chunks.append(chunk)
        
        return chunks
    
    def _simple_chunking(self, paper: ResearchPaper, content: str) -> List[AcademicChunk]:
        """Simple chunking by paragraphs."""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        target_size = 300  # words
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            potential_chunk = current_chunk + "\\n\\n" + paragraph if current_chunk else paragraph
            potential_word_count = len(potential_chunk.split())
            
            if potential_word_count <= target_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk
                if current_chunk:
                    chunk = self._create_chunk(paper, chunk_index, current_chunk, "simple_chunking")
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(paper, chunk_index, current_chunk, "simple_chunking")
            chunks.append(chunk)
        
        return chunks
    
    def _identify_sections(self, content: str) -> List[tuple]:
        """Identify academic sections in content."""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        section_keywords = [
            'abstract', 'introduction', 'background', 'literature review',
            'methodology', 'methods', 'approach', 'design',
            'results', 'findings', 'analysis', 'evaluation',
            'discussion', 'implications', 'limitations',
            'conclusion', 'conclusions', 'future work',
            'references', 'bibliography', 'acknowledgments'
        ]
        
        for line in lines:
            line_lower = line.strip().lower()
            
            # Check if this line is a section header
            is_section_header = any(keyword in line_lower for keyword in section_keywords)
            is_section_header = is_section_header and len(line.strip()) < 100  # Headers are usually short
            
            if is_section_header:
                # Save previous section
                if current_section and current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                
                # Start new section
                current_section = line.strip()
                current_content = []
            else:
                if line.strip():  # Skip empty lines
                    current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections.append(("Full Text", content))
        
        return sections
    
    def _classify_section_type(self, section_title: str) -> str:
        """Classify section type based on title."""
        title_lower = section_title.lower()
        
        if any(word in title_lower for word in ['abstract', 'summary']):
            return 'abstract'
        elif any(word in title_lower for word in ['introduction', 'background']):
            return 'introduction'
        elif any(word in title_lower for word in ['method', 'approach', 'design']):
            return 'methods'
        elif any(word in title_lower for word in ['result', 'finding', 'analysis']):
            return 'results'
        elif any(word in title_lower for word in ['discussion', 'implication']):
            return 'discussion'
        elif any(word in title_lower for word in ['conclusion', 'summary']):
            return 'conclusion'
        elif any(word in title_lower for word in ['reference', 'bibliography']):
            return 'references'
        else:
            return 'other'
    
    def _create_chunk(self, paper: ResearchPaper, index: int, content: str, source: str) -> AcademicChunk:
        """Create an AcademicChunk with common properties."""
        return AcademicChunk(
            paper_id=paper.id or 0,
            chunk_index=index,
            content=content,
            section_type="introduction",  # Default - could be improved with better classification
            word_count=len(content.split()),
            confidence_score=0.7,
            metadata={"source": source}
        )