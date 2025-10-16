"""
Research Paper Domain Model

Core business entity representing a research paper in the SLR system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ResearchPaper:
    """
    Domain model for research papers.
    
    Follows Domain-Driven Design principles:
    - Pure domain model without infrastructure dependencies
    - Encapsulates business rules and validation
    - Immutable value object characteristics
    """
    
    id: Optional[int] = None
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    doi: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Content fields
    full_text: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    
    # Quality metrics
    quality_score: Optional[float] = None
    screening_status: Optional[str] = None
    
    # Citations
    references: List[str] = field(default_factory=list)
    citation_count: int = 0
    
    def __post_init__(self):
        """Validate business rules after initialization."""
        if self.title and len(self.title.strip()) == 0:
            raise ValueError("Title cannot be empty")
            
        if self.publication_year and (self.publication_year < 1900 or self.publication_year > datetime.now().year):
            raise ValueError(f"Invalid publication year: {self.publication_year}")
    
    @property
    def is_indexed(self) -> bool:
        """Check if paper has been indexed for search."""
        return self.indexed_at is not None
    
    @property
    def author_names(self) -> str:
        """Get formatted author names."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return f"{self.authors[0]} and {self.authors[1]}"
        return f"{self.authors[0]} et al."
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag if present."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'doi': self.doi,
            'publication_year': self.publication_year,
            'journal': self.journal,
            'keywords': self.keywords,
            'tags': self.tags,
            'full_text': self.full_text,
            'file_path': self.file_path,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None,
            'quality_score': self.quality_score,
            'screening_status': self.screening_status,
            'references': self.references,
            'citation_count': self.citation_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchPaper':
        """Create instance from dictionary."""
        # Convert ISO strings back to datetime
        for field in ['created_at', 'updated_at', 'indexed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)