"""
Academic Chunk Domain Model

Represents a chunk of academic content for analysis and search.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChunkType(Enum):
    """Types of academic chunks."""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCE = "reference"
    FIGURE = "figure"
    TABLE = "table"
    OTHER = "other"


@dataclass
class AcademicChunk:
    """
    Domain model for academic content chunks.
    
    Represents a semantically meaningful unit of academic content
    with proper business validation and behavior.
    """
    
    id: Optional[int] = None
    paper_id: int = 0
    content: str = ""
    chunk_type: ChunkType = ChunkType.OTHER
    section_title: Optional[str] = None
    
    # Position information
    start_position: int = 0
    end_position: int = 0
    page_number: Optional[int] = None
    
    # Content metadata
    word_count: int = 0
    character_count: int = 0
    tokens: List[str] = field(default_factory=list)
    
    # Analysis results
    keywords: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    readability_score: Optional[float] = None
    
    # Vector embeddings (for semantic search)
    embedding_vector: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate business rules after initialization."""
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Chunk content cannot be empty")
            
        if self.paper_id <= 0:
            raise ValueError("Paper ID must be positive")
            
        if self.start_position < 0 or self.end_position < 0:
            raise ValueError("Positions cannot be negative")
            
        if self.end_position <= self.start_position:
            raise ValueError("End position must be greater than start position")
        
        # Auto-calculate counts if not provided
        if self.word_count == 0:
            self.word_count = len(self.content.split())
            
        if self.character_count == 0:
            self.character_count = len(self.content)
    
    @property
    def is_analyzed(self) -> bool:
        """Check if chunk has been analyzed for keywords/concepts."""
        return len(self.keywords) > 0 or len(self.concepts) > 0
    
    @property
    def has_embedding(self) -> bool:
        """Check if chunk has vector embedding."""
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
    
    @property
    def preview(self) -> str:
        """Get a preview of the content (first 100 characters)."""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
    
    def add_keyword(self, keyword: str) -> None:
        """Add a keyword if not already present."""
        if keyword and keyword.lower() not in [k.lower() for k in self.keywords]:
            self.keywords.append(keyword)
    
    def add_concept(self, concept: str) -> None:
        """Add a concept if not already present."""
        if concept and concept.lower() not in [c.lower() for c in self.concepts]:
            self.concepts.append(concept)
    
    def set_embedding(self, vector: List[float], model: str) -> None:
        """Set the embedding vector and model."""
        if not vector or len(vector) == 0:
            raise ValueError("Embedding vector cannot be empty")
        
        self.embedding_vector = vector
        self.embedding_model = model
    
    def calculate_similarity(self, other: 'AcademicChunk') -> float:
        """Calculate cosine similarity with another chunk (requires embeddings)."""
        if not self.has_embedding or not other.has_embedding:
            raise ValueError("Both chunks must have embeddings for similarity calculation")
        
        # Simple dot product similarity (would use proper cosine similarity in production)
        dot_product = sum(a * b for a, b in zip(self.embedding_vector, other.embedding_vector))
        return max(0.0, min(1.0, dot_product))  # Clamp to [0, 1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'content': self.content,
            'chunk_type': self.chunk_type.value,
            'section_title': self.section_title,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'page_number': self.page_number,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'tokens': self.tokens,
            'keywords': self.keywords,
            'concepts': self.concepts,
            'sentiment_score': self.sentiment_score,
            'readability_score': self.readability_score,
            'embedding_vector': self.embedding_vector,
            'embedding_model': self.embedding_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AcademicChunk':
        """Create instance from dictionary."""
        # Convert enum
        if 'chunk_type' in data and isinstance(data['chunk_type'], str):
            data['chunk_type'] = ChunkType(data['chunk_type'])
        
        # Convert ISO strings back to datetime
        for field in ['created_at', 'updated_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)