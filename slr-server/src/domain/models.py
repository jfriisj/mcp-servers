"""
Core domain models for Systematic Literature Review (SLR) MCP Server.

This module defines all the domain entities for conducting systematic literature
reviews, following Clean Architecture Layer 4 principles as pure domain models.

Domain Models:
- ResearchPaper: Academic research paper with metadata
- AcademicChunk: Intelligent chunks of academic content
- Citation: Citation relationships and metadata
- QualityAssessment: Systematic quality evaluation results
- ResearchQuestion: PICO/SPIDER validated research questions
- ResearchHypothesis: Extracted and analyzed hypotheses
- EvidenceItem: Individual evidence points for synthesis
- Author: Author information and affiliations
- Journal: Publication venue information
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal


class QualityRating(Enum):
    """Quality rating levels for assessments."""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    VERY_LOW = "very_low"
    UNCLEAR = "unclear"


class AssessmentFramework(Enum):
    """Supported quality assessment frameworks."""
    PRISMA = "PRISMA"
    CASP = "CASP"
    JBI = "JBI"
    COCHRANE = "COCHRANE"
    CUSTOM = "CUSTOM"


class CitationType(Enum):
    """Types of citations."""
    FORWARD = "forward"  # Papers citing this paper
    BACKWARD = "backward"  # Papers cited by this paper
    SELF = "self"  # Self-citation


class HypothesisType(Enum):
    """Types of hypotheses."""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    NULL = "null"
    ALTERNATIVE = "alternative"


class EvidenceLevel(Enum):
    """Evidence levels based on research hierarchy."""
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    RANDOMIZED_TRIAL = "randomized_trial"
    COHORT_STUDY = "cohort_study"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    CASE_SERIES = "case_series"
    EXPERT_OPINION = "expert_opinion"


# Aliases for backward compatibility and test imports
QualityFramework = AssessmentFramework


class QuestionFramework(Enum):
    """Research question validation frameworks."""
    PICO = "pico"
    SPIDER = "spider"
    SPICE = "spice"


class StudyType(Enum):
    """Types of research studies."""
    EXPERIMENTAL = "experimental"
    OBSERVATIONAL = "observational"
    REVIEW = "review"
    META_ANALYSIS = "meta_analysis"
    CASE_STUDY = "case_study"
    SURVEY = "survey"


class EvidenceType(Enum):
    """Types of evidence."""
    STATISTICAL = "statistical"
    QUALITATIVE = "qualitative"
    MIXED_METHODS = "mixed_methods"
    THEORETICAL = "theoretical"
    EMPIRICAL = "empirical"


class ValidationLevel(Enum):
    """Validation levels for quality assessment."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffectDirection(Enum):
    """Effect direction for hypothesis testing."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class AssessmentStatus(Enum):
    """Status of quality assessment."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class QuestionStatus(Enum):
    """Status of research question."""
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"


class HypothesisStatus(Enum):
    """Status of hypothesis."""
    FORMULATED = "formulated"
    TESTED = "tested"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProjectStatus(Enum):
    """Status of SLR project."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ProjectPhase(Enum):
    """Current phase of SLR project following PRISMA methodology."""
    PLANNING = "planning"
    SEARCH = "search"
    SCREENING = "screening"
    QUALITY_ASSESSMENT = "quality_assessment"
    DATA_EXTRACTION = "data_extraction"
    ANALYSIS = "analysis"
    REPORTING = "reporting"


class ScreeningStatus(Enum):
    """Screening status for papers within project."""
    PENDING = "pending"
    SCREENING = "screening"
    INCLUDED = "included"
    EXCLUDED = "excluded"


class ScreeningPhase(Enum):
    """Phase of screening process."""
    TITLE_ABSTRACT = "title_abstract"
    FULL_TEXT = "full_text"
    FINAL_SELECTION = "final_selection"


@dataclass
class SLRProject:
    """
    Domain model representing a Systematic Literature Review project.
    
    This class manages SLR project metadata, research framework (PICO/SPIDER),
    and project organization following PRISMA guidelines.
    
    Clean Architecture Layer 4: Domain Model
    """
    name: str  # Slug format: "software-designs"
    display_name: str  # Human-readable: "Software Design Patterns"
    description: str
    
    # Identity
    id: Optional[int] = None
    
    # Research framework (PICO/SPIDER)
    research_questions: List[str] = field(default_factory=list)
    population: Optional[str] = None  # PICO: Population
    intervention: Optional[str] = None  # PICO: Intervention
    comparison: Optional[str] = None  # PICO: Comparison
    outcome: Optional[str] = None  # PICO: Outcome
    
    # File system
    folder_path: str = ""  # "projects/software-designs"
    project_file_path: Optional[str] = None  # Path to description file
    project_file_type: Optional[str] = None  # "pdf" or "markdown"
    
    # Timestamps
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    # Status tracking
    current_phase: str = "planning"  # ProjectPhase enum value
    status: str = "active"  # ProjectStatus enum value
    
    # Paper statistics
    total_papers: int = 0
    papers_screening: int = 0
    papers_included: int = 0
    papers_excluded: int = 0
    papers_quality_assessed: int = 0
    
    # Team management
    created_by: Optional[str] = None
    team_members: List[str] = field(default_factory=list)
    
    # Settings and metadata
    settings: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """Validate SLRProject after initialization."""
        self._validate()
        
        # Set timestamps
        if self.created_date is None:
            self.created_date = datetime.now(timezone.utc)
        if self.updated_date is None:
            self.updated_date = datetime.now(timezone.utc)
        
        # Set folder path if not provided
        if not self.folder_path:
            self.folder_path = f"projects/{self.name}"
    
    def _validate(self) -> None:
        """Validate SLRProject business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        
        # Validate slug format (lowercase, hyphens, alphanumeric)
        import re
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', self.name):
            raise ValueError(
                "Project name must be in slug format: lowercase alphanumeric with hyphens "
                "(e.g., 'software-designs')"
            )
        
        if not self.display_name or not self.display_name.strip():
            raise ValueError("Display name cannot be empty")
        
        if not self.description or not self.description.strip():
            raise ValueError("Project description cannot be empty")
        
        # Validate phase
        valid_phases = [p.value for p in ProjectPhase]
        if self.current_phase not in valid_phases:
            raise ValueError(f"Invalid phase: {self.current_phase}. Must be one of: {valid_phases}")
        
        # Validate status
        valid_statuses = [s.value for s in ProjectStatus]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of: {valid_statuses}")
        
        # Validate statistics
        if self.total_papers < 0:
            raise ValueError("Total papers cannot be negative")
        if self.papers_screening < 0:
            raise ValueError("Papers screening cannot be negative")
        if self.papers_included < 0:
            raise ValueError("Papers included cannot be negative")
        if self.papers_excluded < 0:
            raise ValueError("Papers excluded cannot be negative")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate project completion based on papers processed."""
        if self.total_papers == 0:
            return 0.0
        processed = self.papers_included + self.papers_excluded
        return (processed / self.total_papers) * 100
    
    @property
    def is_active(self) -> bool:
        """Check if project is currently active."""
        return self.status == "active"
    
    def update_statistics(
        self, 
        action: str, 
        count: int = 1
    ) -> None:
        """
        Update project statistics based on action.
        
        Args:
            action: Action type (paper_added, paper_included, paper_excluded, etc.)
            count: Number of papers affected
        """
        if action == "paper_added":
            self.total_papers += count
            self.papers_screening += count
        elif action == "paper_included":
            self.papers_screening -= count
            self.papers_included += count
        elif action == "paper_excluded":
            self.papers_screening -= count
            self.papers_excluded += count
        elif action == "paper_quality_assessed":
            self.papers_quality_assessed += count
        
        self.updated_date = datetime.now(timezone.utc)


@dataclass
class Author:
    """
    Domain model representing an academic author.
    
    This class follows SRP by managing only author information and validation.
    """
    name: str
    id: Optional[int] = None
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    h_index: Optional[int] = None
    citation_count: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Author after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate Author business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Author name cannot be empty")
        
        if self.email and "@" not in self.email:
            raise ValueError("Invalid email format")
        
        if self.orcid and not self.orcid.startswith("0000-"):
            raise ValueError("ORCID must start with '0000-'")
        
        if self.h_index is not None and self.h_index < 0:
            raise ValueError("H-index cannot be negative")
        
        if self.citation_count is not None and self.citation_count < 0:
            raise ValueError("Citation count cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert Author to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "affiliation": self.affiliation,
            "orcid": self.orcid,
            "h_index": self.h_index,
            "citation_count": self.citation_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Journal:
    """
    Domain model representing an academic journal.
    
    This class manages journal information and impact metrics.
    """
    name: str
    id: Optional[int] = None
    issn: Optional[str] = None
    publisher: Optional[str] = None
    impact_factor: Optional[Decimal] = None
    quartile: Optional[str] = None  # Q1, Q2, Q3, Q4
    open_access: bool = False
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Journal after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate Journal business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Journal name cannot be empty")
        
        if self.quartile and self.quartile not in {"Q1", "Q2", "Q3", "Q4"}:
            raise ValueError("Quartile must be Q1, Q2, Q3, or Q4")
        
        if self.impact_factor and self.impact_factor < 0:
            raise ValueError("Impact factor cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert Journal to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "issn": self.issn,
            "publisher": self.publisher,
            "impact_factor": float(self.impact_factor) if self.impact_factor else None,
            "quartile": self.quartile,
            "open_access": self.open_access,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ResearchPaper:
    """
    Domain model representing an academic research paper.

    This class follows SRP by representing only academic papers and their
    business rules. It provides:
    - Academic metadata and citation management
    - Quality assessment tracking
    - Research methodology classification
    - Publication status and metrics
    
    Clean Architecture Layer 4: Domain Model
    """
    title: str
    file_path: str
    file_type: str
    id: Optional[int] = None
    authors: List[Author] = field(default_factory=list)
    journal: Optional[Journal] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    methodology: Optional[str] = None
    study_type: Optional[str] = None
    sample_size: Optional[int] = None
    citation_count: Optional[int] = None
    upload_date: Optional[datetime] = None
    file_size: Optional[int] = None
    total_pages: Optional[int] = None
    total_words: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    indexed: bool = False
    quality_assessed: bool = False
    included_in_review: Optional[bool] = None
    exclusion_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Project-based organization (Phase 1)
    project_id: Optional[int] = None
    project_name: Optional[str] = None  # Denormalized for faster queries
    relative_file_path: Optional[str] = None  # e.g., "screening/paper1.pdf"
    screening_status: Optional[str] = None  # "pending", "screening", "included", "excluded"
    screening_phase: Optional[str] = None  # "title_abstract", "full_text", "final_selection"
    screening_notes: Optional[str] = None
    screening_date: Optional[datetime] = None
    screened_by: Optional[str] = None

    def __post_init__(self):
        """Validate ResearchPaper after initialization."""
        self._validate()
        
        # Set timestamps
        if self.upload_date is None:
            self.upload_date = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate ResearchPaper business rules."""
        if not self.title or not self.title.strip():
            raise ValueError("Paper title cannot be empty")
        
        if not self.file_path or not self.file_path.strip():
            raise ValueError("Paper file_path cannot be empty")
        
        valid_file_types = {"pdf", "docx", "txt", "md", "bib", "ris"}
        if self.file_type not in valid_file_types:
            raise ValueError(f"Invalid file_type: {self.file_type}. Must be one of: {valid_file_types}")
        
        if self.publication_year and (self.publication_year < 1900 or self.publication_year > 2030):
            raise ValueError("Publication year must be between 1900 and 2030")
        
        if self.sample_size is not None and self.sample_size < 0:
            raise ValueError("Sample size cannot be negative")
        
        if self.citation_count is not None and self.citation_count < 0:
            raise ValueError("Citation count cannot be negative")
        
        if not isinstance(self.authors, list):
            raise ValueError("Authors must be a list")
        
        if not isinstance(self.keywords, list):
            raise ValueError("Keywords must be a list")
        
        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")

    @property
    def author_names(self) -> List[str]:
        """Get list of author names."""
        return [author.name for author in self.authors]

    @property
    def first_author(self) -> Optional[Author]:
        """Get first author."""
        return self.authors[0] if self.authors else None

    @property
    def review_status(self) -> str:
        """Get current review status."""
        if self.included_in_review is True:
            return "included"
        elif self.included_in_review is False:
            return "excluded"
        elif self.quality_assessed:
            return "assessed"
        elif self.indexed:
            return "indexed"
        else:
            return "uploaded"

    @property
    def is_recent(self) -> bool:
        """Check if paper is from recent years (last 5 years)."""
        if not self.publication_year:
            return False
        current_year = datetime.now().year
        return (current_year - self.publication_year) <= 5

    def add_author(self, author: Author) -> "ResearchPaper":
        """Add an author to the paper."""
        new_authors = self.authors.copy()
        new_authors.append(author)
        return self._copy_with(authors=new_authors)

    def add_keyword(self, keyword: str) -> "ResearchPaper":
        """Add a keyword to the paper."""
        if not keyword or not keyword.strip():
            raise ValueError("Keyword cannot be empty")
        
        keyword = keyword.strip().lower()
        new_keywords = self.keywords.copy()
        if keyword not in new_keywords:
            new_keywords.append(keyword)
        
        return self._copy_with(keywords=new_keywords)

    def mark_indexed(self) -> "ResearchPaper":
        """Mark paper as indexed."""
        return self._copy_with(indexed=True, updated_at=datetime.now(timezone.utc))

    def mark_quality_assessed(self) -> "ResearchPaper":
        """Mark paper as quality assessed."""
        return self._copy_with(quality_assessed=True, updated_at=datetime.now(timezone.utc))

    def include_in_review(self) -> "ResearchPaper":
        """Include paper in systematic review."""
        return self._copy_with(
            included_in_review=True,
            exclusion_reason=None,
            updated_at=datetime.now(timezone.utc)
        )

    def exclude_from_review(self, reason: str) -> "ResearchPaper":
        """Exclude paper from systematic review."""
        if not reason or not reason.strip():
            raise ValueError("Exclusion reason cannot be empty")
        
        return self._copy_with(
            included_in_review=False,
            exclusion_reason=reason.strip(),
            updated_at=datetime.now(timezone.utc)
        )

    def _copy_with(self, **kwargs) -> "ResearchPaper":
        """Create a copy with specified changes."""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return ResearchPaper.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResearchPaper to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "authors": [author.to_dict() for author in self.authors],
            "journal": self.journal.to_dict() if self.journal else None,
            "publication_year": self.publication_year,
            "doi": self.doi,
            "abstract": self.abstract,
            "keywords": self.keywords.copy(),
            "methodology": self.methodology,
            "study_type": self.study_type,
            "sample_size": self.sample_size,
            "citation_count": self.citation_count,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "file_size": self.file_size,
            "total_pages": self.total_pages,
            "total_words": self.total_words,
            "tags": self.tags.copy(),
            "indexed": self.indexed,
            "quality_assessed": self.quality_assessed,
            "included_in_review": self.included_in_review,
            "exclusion_reason": self.exclusion_reason,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "review_status": self.review_status,
            "author_names": self.author_names
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchPaper":
        """Create ResearchPaper from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Parse datetime fields
        upload_date = None
        if data.get("upload_date"):
            upload_date = datetime.fromisoformat(data["upload_date"])
        
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        # Parse authors
        authors = []
        for author_data in data.get("authors", []):
            if isinstance(author_data, dict):
                authors.append(Author(**{k: v for k, v in author_data.items() if k != "created_at"}))

        # Parse journal
        journal = None
        if data.get("journal"):
            journal_data = data["journal"]
            if isinstance(journal_data, dict):
                journal = Journal(**{k: v for k, v in journal_data.items() if k != "created_at"})

        return cls(
            id=data.get("id"),
            title=data["title"],
            file_path=data["file_path"],
            file_type=data["file_type"],
            authors=authors,
            journal=journal,
            publication_year=data.get("publication_year"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            keywords=data.get("keywords", []),
            methodology=data.get("methodology"),
            study_type=data.get("study_type"),
            sample_size=data.get("sample_size"),
            citation_count=data.get("citation_count"),
            upload_date=upload_date,
            file_size=data.get("file_size"),
            total_pages=data.get("total_pages"),
            total_words=data.get("total_words"),
            tags=data.get("tags", []),
            indexed=data.get("indexed", False),
            quality_assessed=data.get("quality_assessed", False),
            included_in_review=data.get("included_in_review"),
            exclusion_reason=data.get("exclusion_reason"),
            notes=data.get("notes"),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class AcademicChunk:
    """
    Domain model representing intelligent academic paper chunks.

    This class extends the basic chunk concept for academic content with:
    - Academic section awareness (Abstract, Introduction, Methods, etc.)
    - Citation-aware chunking
    - Topic-based segmentation
    - Research element extraction
    """
    paper_id: int
    chunk_index: int
    content: str
    id: Optional[int] = None
    section_type: str = "body"  # abstract, introduction, methods, results, discussion, conclusion, references
    title: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    word_count: Optional[int] = None
    citation_count: Optional[int] = None
    figure_count: Optional[int] = None
    table_count: Optional[int] = None
    research_elements: List[str] = field(default_factory=list)  # hypotheses, methods, findings, etc.
    semantic_tags: List[str] = field(default_factory=list)
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate AcademicChunk after initialization."""
        self._validate()
        
        # Set defaults
        if self.word_count is None:
            self.word_count = len(self.content.split())
        
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate AcademicChunk business rules."""
        if self.paper_id is None or self.paper_id <= 0:
            raise ValueError("paper_id must be a positive integer")
        
        if self.chunk_index < 0:
            raise ValueError("chunk_index cannot be negative")
        
        if not self.content or not self.content.strip():
            raise ValueError("Chunk content cannot be empty")
        
        valid_sections = {
            "abstract", "introduction", "background", "methods", "methodology",
            "results", "findings", "discussion", "conclusion", "conclusions",
            "references", "appendix", "body", "unknown"
        }
        if self.section_type not in valid_sections:
            raise ValueError(f"Invalid section_type: {self.section_type}")
        
        if self.confidence_score is not None and not (0 <= self.confidence_score <= 1):
            raise ValueError("Confidence score must be between 0 and 1")

    @property
    def is_core_section(self) -> bool:
        """Check if chunk is from a core research section."""
        core_sections = {"methods", "methodology", "results", "findings", "discussion", "conclusion"}
        return self.section_type in core_sections

    @property
    def has_citations(self) -> bool:
        """Check if chunk contains citations."""
        return self.citation_count is not None and self.citation_count > 0

    @property
    def has_figures(self) -> bool:
        """Check if chunk references figures."""
        return self.figure_count is not None and self.figure_count > 0

    @property
    def display_title(self) -> str:
        """Get display title with section fallback."""
        if self.title and self.title.strip():
            return self.title
        return f"{self.section_type.title()} - Chunk {self.chunk_index + 1}"

    def add_research_element(self, element: str) -> "AcademicChunk":
        """Add a research element to the chunk."""
        if not element or not element.strip():
            raise ValueError("Research element cannot be empty")
        
        element = element.strip().lower()
        new_elements = self.research_elements.copy()
        if element not in new_elements:
            new_elements.append(element)
        
        return self._copy_with(research_elements=new_elements)

    def add_semantic_tag(self, tag: str) -> "AcademicChunk":
        """Add a semantic tag to the chunk."""
        if not tag or not tag.strip():
            raise ValueError("Semantic tag cannot be empty")
        
        tag = tag.strip().lower()
        new_tags = self.semantic_tags.copy()
        if tag not in new_tags:
            new_tags.append(tag)
        
        return self._copy_with(semantic_tags=new_tags)

    def _copy_with(self, **kwargs) -> "AcademicChunk":
        """Create a copy with specified changes."""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return AcademicChunk.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AcademicChunk to dictionary."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "chunk_index": self.chunk_index,
            "section_type": self.section_type,
            "title": self.title,
            "content": self.content,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "word_count": self.word_count,
            "citation_count": self.citation_count,
            "figure_count": self.figure_count,
            "table_count": self.table_count,
            "research_elements": self.research_elements.copy(),
            "semantic_tags": self.semantic_tags.copy(),
            "confidence_score": self.confidence_score,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "display_title": self.display_title,
            "is_core_section": self.is_core_section
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcademicChunk":
        """Create AcademicChunk from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data.get("id"),
            paper_id=data["paper_id"],
            chunk_index=data["chunk_index"],
            section_type=data.get("section_type", "body"),
            title=data.get("title"),
            content=data["content"],
            start_page=data.get("start_page"),
            end_page=data.get("end_page"),
            word_count=data.get("word_count"),
            citation_count=data.get("citation_count"),
            figure_count=data.get("figure_count"),
            table_count=data.get("table_count"),
            research_elements=data.get("research_elements", []),
            semantic_tags=data.get("semantic_tags", []),
            confidence_score=data.get("confidence_score"),
            metadata=data.get("metadata", {}),
            created_at=created_at
        )


@dataclass
class Citation:
    """
    Domain model representing citation relationships between papers.
    
    This class manages citation networks and reference patterns.
    """
    citing_paper_id: int
    cited_paper_id: Optional[int] = None
    id: Optional[int] = None
    citation_text: Optional[str] = None
    context: Optional[str] = None  # Surrounding text for context
    page_number: Optional[int] = None
    citation_type: CitationType = CitationType.BACKWARD
    external_reference: Optional[str] = None  # For papers not in our corpus
    doi: Optional[str] = None
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate Citation after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate Citation business rules."""
        if self.citing_paper_id is None or self.citing_paper_id <= 0:
            raise ValueError("citing_paper_id must be a positive integer")
        
        if self.cited_paper_id is not None and self.cited_paper_id <= 0:
            raise ValueError("cited_paper_id must be a positive integer or None")
        
        if self.cited_paper_id is None and not self.external_reference:
            raise ValueError("Either cited_paper_id or external_reference must be provided")
        
        if not isinstance(self.authors, list):
            raise ValueError("Authors must be a list")

    @property
    def is_self_citation(self) -> bool:
        """Check if this is a self-citation."""
        return self.citing_paper_id == self.cited_paper_id

    @property
    def is_external_reference(self) -> bool:
        """Check if this cites an external paper."""
        return self.cited_paper_id is None and self.external_reference is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Citation to dictionary."""
        return {
            "id": self.id,
            "citing_paper_id": self.citing_paper_id,
            "cited_paper_id": self.cited_paper_id,
            "citation_text": self.citation_text,
            "context": self.context,
            "page_number": self.page_number,
            "citation_type": self.citation_type.value,
            "external_reference": self.external_reference,
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors.copy(),
            "publication_year": self.publication_year,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_self_citation": self.is_self_citation,
            "is_external_reference": self.is_external_reference
        }


@dataclass
class QualityAssessment:
    """
    Domain model for systematic quality assessments following PRISMA guidelines.
    
    This class manages quality evaluations with multi-reviewer support.
    """
    paper_id: int
    reviewer_id: str
    id: Optional[int] = None
    framework: AssessmentFramework = AssessmentFramework.PRISMA
    overall_rating: QualityRating = QualityRating.UNCLEAR
    criteria_scores: Dict[str, Union[QualityRating, int, float]] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    bias_assessment: Dict[str, str] = field(default_factory=dict)
    recommendation: Optional[str] = None  # include, exclude, uncertain
    confidence_level: Optional[float] = None  # 0-1 scale
    notes: Optional[str] = None
    assessment_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate QualityAssessment after initialization."""
        self._validate()
        if self.assessment_date is None:
            self.assessment_date = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate QualityAssessment business rules."""
        if self.paper_id is None or self.paper_id <= 0:
            raise ValueError("paper_id must be a positive integer")
        
        if not self.reviewer_id or not self.reviewer_id.strip():
            raise ValueError("reviewer_id cannot be empty")
        
        if self.confidence_level is not None and not (0 <= self.confidence_level <= 1):
            raise ValueError("Confidence level must be between 0 and 1")
        
        if self.recommendation and self.recommendation not in {"include", "exclude", "uncertain"}:
            raise ValueError("Recommendation must be 'include', 'exclude', or 'uncertain'")

    def add_strength(self, strength: str) -> "QualityAssessment":
        """Add a strength to the assessment."""
        if not strength or not strength.strip():
            raise ValueError("Strength cannot be empty")
        
        new_strengths = self.strengths.copy()
        if strength.strip() not in new_strengths:
            new_strengths.append(strength.strip())
        
        return self._copy_with(strengths=new_strengths)

    def add_weakness(self, weakness: str) -> "QualityAssessment":
        """Add a weakness to the assessment."""
        if not weakness or not weakness.strip():
            raise ValueError("Weakness cannot be empty")
        
        new_weaknesses = self.weaknesses.copy()
        if weakness.strip() not in new_weaknesses:
            new_weaknesses.append(weakness.strip())
        
        return self._copy_with(weaknesses=new_weaknesses)

    def _copy_with(self, **kwargs) -> "QualityAssessment":
        """Create a copy with specified changes."""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return QualityAssessment.from_dict(current_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert QualityAssessment to dictionary."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "reviewer_id": self.reviewer_id,
            "framework": self.framework.value,
            "overall_rating": self.overall_rating.value,
            "criteria_scores": {k: v.value if isinstance(v, QualityRating) else v 
                              for k, v in self.criteria_scores.items()},
            "strengths": self.strengths.copy(),
            "weaknesses": self.weaknesses.copy(),
            "bias_assessment": self.bias_assessment.copy(),
            "recommendation": self.recommendation,
            "confidence_level": self.confidence_level,
            "notes": self.notes,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityAssessment":
        """Create QualityAssessment from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        assessment_date = None
        if data.get("assessment_date"):
            assessment_date = datetime.fromisoformat(data["assessment_date"])
        
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data.get("id"),
            paper_id=data["paper_id"],
            reviewer_id=data["reviewer_id"],
            framework=AssessmentFramework(data.get("framework", "PRISMA")),
            overall_rating=QualityRating(data.get("overall_rating", "unclear")),
            criteria_scores=data.get("criteria_scores", {}),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            bias_assessment=data.get("bias_assessment", {}),
            recommendation=data.get("recommendation"),
            confidence_level=data.get("confidence_level"),
            notes=data.get("notes"),
            assessment_date=assessment_date,
            created_at=created_at
        )


@dataclass
class ResearchQuestion:
    """
    Domain model for PICO/SPIDER validated research questions.
    
    This class manages research question validation and decomposition.
    """
    question_text: str
    id: Optional[int] = None
    framework: str = "PICO"  # PICO or SPIDER
    population: Optional[str] = None
    intervention: Optional[str] = None
    comparison: Optional[str] = None
    outcome: Optional[str] = None
    # SPIDER specific
    sample: Optional[str] = None
    phenomenon: Optional[str] = None
    design: Optional[str] = None
    evaluation: Optional[str] = None
    research_type: Optional[str] = None
    # Validation results
    is_valid: bool = False
    validation_score: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate ResearchQuestion after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate ResearchQuestion business rules."""
        if not self.question_text or not self.question_text.strip():
            raise ValueError("Research question text cannot be empty")
        
        if self.framework not in {"PICO", "SPIDER"}:
            raise ValueError("Framework must be 'PICO' or 'SPIDER'")
        
        if self.validation_score is not None and not (0 <= self.validation_score <= 1):
            raise ValueError("Validation score must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResearchQuestion to dictionary."""
        return {
            "id": self.id,
            "question_text": self.question_text,
            "framework": self.framework,
            "population": self.population,
            "intervention": self.intervention,
            "comparison": self.comparison,
            "outcome": self.outcome,
            "sample": self.sample,
            "phenomenon": self.phenomenon,
            "design": self.design,
            "evaluation": self.evaluation,
            "research_type": self.research_type,
            "is_valid": self.is_valid,
            "validation_score": self.validation_score,
            "suggestions": self.suggestions.copy(),
            "domain": self.domain,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ResearchHypothesis:
    """
    Domain model for extracted and analyzed research hypotheses.
    
    This class manages hypothesis extraction and evidence linking.
    """
    hypothesis_text: str
    paper_id: int
    id: Optional[int] = None
    hypothesis_type: HypothesisType = HypothesisType.EXPLICIT
    variables: List[str] = field(default_factory=list)
    predicted_relationship: Optional[str] = None
    evidence_support: Optional[str] = None  # supported, not_supported, mixed, unclear
    statistical_tests: List[str] = field(default_factory=list)
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[str] = None
    context_section: Optional[str] = None  # where in paper it was found
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate ResearchHypothesis after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate ResearchHypothesis business rules."""
        if not self.hypothesis_text or not self.hypothesis_text.strip():
            raise ValueError("Hypothesis text cannot be empty")
        
        if self.paper_id is None or self.paper_id <= 0:
            raise ValueError("paper_id must be a positive integer")
        
        if self.p_value is not None and not (0 <= self.p_value <= 1):
            raise ValueError("P-value must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResearchHypothesis to dictionary."""
        return {
            "id": self.id,
            "hypothesis_text": self.hypothesis_text,
            "paper_id": self.paper_id,
            "hypothesis_type": self.hypothesis_type.value,
            "variables": self.variables.copy(),
            "predicted_relationship": self.predicted_relationship,
            "evidence_support": self.evidence_support,
            "statistical_tests": self.statistical_tests.copy(),
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "context_section": self.context_section,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class EvidenceItem:
    """
    Domain model for individual evidence points used in synthesis.
    
    This class manages evidence collection and grading for meta-analysis.
    """
    paper_id: int
    evidence_text: str
    id: Optional[int] = None
    outcome_measure: str = "primary"
    evidence_level: EvidenceLevel = EvidenceLevel.EXPERT_OPINION
    sample_size: Optional[int] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[str] = None
    p_value: Optional[float] = None
    grade_rating: Optional[str] = None  # Very Low, Low, Moderate, High
    risk_of_bias: Optional[str] = None  # Low, Unclear, High
    directness: Optional[str] = None  # Direct, Indirect
    consistency: Optional[str] = None  # Consistent, Inconsistent
    precision: Optional[str] = None  # Precise, Imprecise
    publication_bias: Optional[str] = None  # Unlikely, Possible, Likely
    context_section: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate EvidenceItem after initialization."""
        self._validate()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def _validate(self) -> None:
        """Validate EvidenceItem business rules."""
        if self.paper_id is None or self.paper_id <= 0:
            raise ValueError("paper_id must be a positive integer")
        
        if not self.evidence_text or not self.evidence_text.strip():
            raise ValueError("Evidence text cannot be empty")
        
        if self.sample_size is not None and self.sample_size < 0:
            raise ValueError("Sample size cannot be negative")
        
        if self.p_value is not None and not (0 <= self.p_value <= 1):
            raise ValueError("P-value must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert EvidenceItem to dictionary."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "evidence_text": self.evidence_text,
            "outcome_measure": self.outcome_measure,
            "evidence_level": self.evidence_level.value,
            "sample_size": self.sample_size,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "p_value": self.p_value,
            "grade_rating": self.grade_rating,
            "risk_of_bias": self.risk_of_bias,
            "directness": self.directness,
            "consistency": self.consistency,
            "precision": self.precision,
            "publication_bias": self.publication_bias,
            "context_section": self.context_section,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        """Create EvidenceItem from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data.get("id"),
            paper_id=data["paper_id"],
            evidence_text=data["evidence_text"],
            outcome_measure=data.get("outcome_measure", "primary"),
            evidence_level=EvidenceLevel(data.get("evidence_level", "expert_opinion")),
            sample_size=data.get("sample_size"),
            effect_size=data.get("effect_size"),
            confidence_interval=data.get("confidence_interval"),
            p_value=data.get("p_value"),
            grade_rating=data.get("grade_rating"),
            risk_of_bias=data.get("risk_of_bias"),
            directness=data.get("directness"),
            consistency=data.get("consistency"),
            precision=data.get("precision"),
            publication_bias=data.get("publication_bias"),
            context_section=data.get("context_section"),
            created_at=created_at
        )


"""
SLR Workflow Management Models for project guidance and progress tracking.

These models extend the core SLR system to support complete workflow management
and user guidance throughout the systematic literature review process.
"""



from dataclasses import dataclass, field

from datetime import datetime, timezone

from enum import Enum

from typing import Any, Dict, List, Optional

import json





class SLRPhase(Enum):

    """Systematic Literature Review workflow phases."""

    PLANNING = "planning"

    SEARCH = "search"

    SCREENING = "screening"

    QUALITY_ASSESSMENT = "quality_assessment"

    DATA_EXTRACTION = "data_extraction"

    ANALYSIS = "analysis"

    REPORTING = "reporting"


# DEPRECATED: Old ProjectStatus definition - use the one at the top of file
# Kept for backward compatibility during migration
class ProjectStatusOld(Enum):
    """Project status indicators (DEPRECATED - use ProjectStatus instead)."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"





class TaskStatus(Enum):

    """Task completion status."""

    PENDING = "pending"

    IN_PROGRESS = "in_progress"

    COMPLETED = "completed"

    OVERDUE = "overdue"

    CANCELLED = "cancelled"





class TaskPriority(Enum):

    """Task priority levels."""

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    URGENT = "urgent"





class ScreeningDecision(Enum):

    """Screening decision options."""

    INCLUDE = "include"

    EXCLUDE = "exclude"

    UNCERTAIN = "uncertain"

    PENDING = "pending"





class ScreeningStage(Enum):

    """Screening workflow stages."""

    TITLE_ABSTRACT = "title_abstract"

    FULL_TEXT = "full_text"

    FINAL_SELECTION = "final_selection"





# DEPRECATED: Old SLRProject for workflow - use the comprehensive SLRProject at top of file
# This is kept temporarily for backward compatibility with slr_workflow_service
@dataclass
class SLRProjectWorkflow:
    """
    DEPRECATED: Old SLR project model for workflow management.
    Use the comprehensive SLRProject at the top of the file instead.
    """

    title: str

    research_domain: str

    id: Optional[int] = None

    description: Optional[str] = None

    team_lead: Optional[str] = None

    team_members: List[str] = field(default_factory=list)

    research_question: Optional[str] = None

    objectives: List[str] = field(default_factory=list)
    current_phase: SLRPhase = SLRPhase.PLANNING
    status: ProjectStatusOld = ProjectStatusOld.NOT_STARTED  # DEPRECATED: Use new ProjectStatus
    estimated_timeline_weeks: Optional[int] = None
    actual_start_date: Optional[datetime] = None
    estimated_completion_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize project timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_date = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        """Check if project is actively being worked on."""
        return self.status in {ProjectStatusOld.IN_PROGRESS}  # DEPRECATED



    @property

    def progress_percentage(self) -> float:

        """Calculate overall project progress based on phase completion."""

        phase_weights = {

            SLRPhase.PLANNING: 10,

            SLRPhase.SEARCH: 15,

            SLRPhase.SCREENING: 25,

            SLRPhase.QUALITY_ASSESSMENT: 15,

            SLRPhase.DATA_EXTRACTION: 15,

            SLRPhase.ANALYSIS: 15,

            SLRPhase.REPORTING: 5

        }

        

        # Simple progress calculation based on current phase

        completed_weight = 0

        for phase in SLRPhase:

            if phase.value <= self.current_phase.value:

                completed_weight += phase_weights.get(phase, 0)

            else:

                break

        

        return min(completed_weight, 100.0)



    def to_dict(self) -> Dict[str, Any]:

        """Convert to dictionary representation."""

        return {

            "id": self.id,

            "title": self.title,

            "description": self.description,

            "research_domain": self.research_domain,

            "team_lead": self.team_lead,

            "team_members": self.team_members,

            "research_question": self.research_question,

            "objectives": self.objectives,

            "current_phase": self.current_phase.value,

            "status": self.status.value,

            "estimated_timeline_weeks": self.estimated_timeline_weeks,

            "actual_start_date": self.actual_start_date.isoformat() if self.actual_start_date else None,

            "estimated_completion_date": self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,

            "tags": self.tags,

            "metadata": self.metadata,

            "progress_percentage": self.progress_percentage,

            "is_active": self.is_active,

            "created_at": self.created_at.isoformat() if self.created_at else None,

            "updated_at": self.updated_at.isoformat() if self.updated_at else None

        }





@dataclass  

class SLRTask:

    """

    Task management for SLR projects with deadlines and assignments.

    """

    project_id: int

    title: str

    description: str

    phase: SLRPhase

    id: Optional[int] = None

    assignee: Optional[str] = None

    priority: TaskPriority = TaskPriority.MEDIUM

    status: TaskStatus = TaskStatus.PENDING

    due_date: Optional[datetime] = None

    completed_date: Optional[datetime] = None

    estimated_hours: Optional[float] = None

    actual_hours: Optional[float] = None

    dependencies: List[int] = field(default_factory=list)  # Task IDs this depends on

    tags: List[str] = field(default_factory=list)

    notes: Optional[str] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None



    def __post_init__(self):

        """Initialize task timestamps."""

        if self.created_at is None:

            self.created_at = datetime.now(timezone.utc)

        if self.updated_at is None:

            self.updated_at = datetime.now(timezone.utc)



    @property

    def is_overdue(self) -> bool:

        """Check if task is overdue."""

        if self.due_date and self.status != TaskStatus.COMPLETED:

            return datetime.now(timezone.utc) > self.due_date

        return False



    @property

    def days_until_due(self) -> Optional[int]:

        """Calculate days until due date."""

        if self.due_date:

            delta = self.due_date - datetime.now(timezone.utc)

            return delta.days

        return None



    def complete_task(self) -> None:

        """Mark task as completed."""

        self.status = TaskStatus.COMPLETED

        self.completed_date = datetime.now(timezone.utc)

        self.updated_at = datetime.now(timezone.utc)



    def to_dict(self) -> Dict[str, Any]:

        """Convert to dictionary representation."""

        return {

            "id": self.id,

            "project_id": self.project_id,

            "title": self.title,

            "description": self.description,

            "phase": self.phase.value,

            "assignee": self.assignee,

            "priority": self.priority.value,

            "status": self.status.value,

            "due_date": self.due_date.isoformat() if self.due_date else None,

            "completed_date": self.completed_date.isoformat() if self.completed_date else None,

            "estimated_hours": self.estimated_hours,

            "actual_hours": self.actual_hours,

            "dependencies": self.dependencies,

            "tags": self.tags,

            "notes": self.notes,

            "is_overdue": self.is_overdue,

            "days_until_due": self.days_until_due,

            "created_at": self.created_at.isoformat() if self.created_at else None,

            "updated_at": self.updated_at.isoformat() if self.updated_at else None

        }





@dataclass

class ScreeningRecord:

    """

    Record of screening decision for study selection workflow.

    """

    paper_id: int

    project_id: int

    reviewer_id: str

    stage: ScreeningStage

    decision: ScreeningDecision

    id: Optional[int] = None

    reason: Optional[str] = None

    confidence_level: Optional[float] = None  # 0.0 to 1.0

    time_spent_minutes: Optional[int] = None

    notes: Optional[str] = None

    exclusion_criteria: List[str] = field(default_factory=list)

    created_at: Optional[datetime] = None



    def __post_init__(self):

        """Initialize screening record timestamp."""

        if self.created_at is None:

            self.created_at = datetime.now(timezone.utc)



    @property

    def is_included(self) -> bool:

        """Check if study was included."""

        return self.decision == ScreeningDecision.INCLUDE



    def to_dict(self) -> Dict[str, Any]:

        """Convert to dictionary representation."""

        return {

            "id": self.id,

            "paper_id": self.paper_id,

            "project_id": self.project_id,

            "reviewer_id": self.reviewer_id,

            "stage": self.stage.value,

            "decision": self.decision.value,

            "reason": self.reason,

            "confidence_level": self.confidence_level,

            "time_spent_minutes": self.time_spent_minutes,

            "notes": self.notes,

            "exclusion_criteria": self.exclusion_criteria,

            "is_included": self.is_included,

            "created_at": self.created_at.isoformat() if self.created_at else None

        }





@dataclass

class ProjectProgress:

    """

    Progress tracking and analytics for SLR projects.

    """

    project_id: int

    id: Optional[int] = None

    total_papers: int = 0

    screened_papers: int = 0

    included_papers: int = 0

    assessed_papers: int = 0

    extracted_papers: int = 0

    completed_tasks: int = 0

    total_tasks: int = 0

    current_phase: SLRPhase = SLRPhase.PLANNING

    phase_completion_percentage: float = 0.0

    overall_completion_percentage: float = 0.0

    estimated_days_remaining: Optional[int] = None

    bottlenecks: List[str] = field(default_factory=list)

    next_milestones: List[str] = field(default_factory=list)

    updated_at: Optional[datetime] = None



    def __post_init__(self):

        """Initialize progress timestamp."""

        if self.updated_at is None:

            self.updated_at = datetime.now(timezone.utc)



    @property

    def screening_completion_rate(self) -> float:

        """Calculate screening completion percentage."""

        if self.total_papers > 0:

            return (self.screened_papers / self.total_papers) * 100

        return 0.0



    @property

    def inclusion_rate(self) -> float:

        """Calculate inclusion rate for screened papers."""

        if self.screened_papers > 0:

            return (self.included_papers / self.screened_papers) * 100

        return 0.0



    def to_dict(self) -> Dict[str, Any]:

        """Convert to dictionary representation."""

        return {

            "id": self.id,

            "project_id": self.project_id,

            "total_papers": self.total_papers,

            "screened_papers": self.screened_papers,

            "included_papers": self.included_papers,

            "assessed_papers": self.assessed_papers,

            "extracted_papers": self.extracted_papers,

            "completed_tasks": self.completed_tasks,

            "total_tasks": self.total_tasks,

            "current_phase": self.current_phase.value,

            "phase_completion_percentage": self.phase_completion_percentage,

            "overall_completion_percentage": self.overall_completion_percentage,

            "screening_completion_rate": self.screening_completion_rate,

            "inclusion_rate": self.inclusion_rate,

            "estimated_days_remaining": self.estimated_days_remaining,

            "bottlenecks": self.bottlenecks,

            "next_milestones": self.next_milestones,

            "updated_at": self.updated_at.isoformat() if self.updated_at else None

        }

