"""
SOLID-Compliant MCP Handler

An MCP handler that follows SOLID principles with proper dependency injection.
"""

from typing import Any, Dict, List, Optional, Union
import logging

from ...domain.repositories.paper_repository import IPaperRepository
from ...domain.repositories.chunk_repository import IChunkRepository  
from ...domain.services.document_service import IDocumentService
from ...domain.services.bibliography_service import IBibliographyService
from ...domain.services.duplicate_detection_service import IDuplicateDetectionService
from ...domain.services.chunking_service import IChunkingService, IndexingStrategy, OptimizationLevel
from .. import IDependencyContainer

logger = logging.getLogger(__name__)


class SOLIDMCPHandler:
    """
    SOLID-compliant MCP Protocol Handler for SLR operations.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles MCP protocol operations
    - Open/Closed: Can be extended with new tools without modification
    - Liskov Substitution: Uses interface dependencies
    - Interface Segregation: Depends only on needed interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """
    
    def __init__(self, container: IDependencyContainer):
        """
        Initialize handler with dependency injection container.
        
        Args:
            container: DI container for resolving dependencies
        """
        self._container = container
        
        # Lazy-loaded dependencies - resolved when needed
        self._document_service: Optional[IDocumentService] = None
        self._bibliography_service: Optional[IBibliographyService] = None
        self._duplicate_service: Optional[IDuplicateDetectionService] = None
        self._chunking_service: Optional[IChunkingService] = None
        self._paper_repository: Optional[IPaperRepository] = None
        self._chunk_repository: Optional[IChunkRepository] = None
    
    @property
    def document_service(self) -> IDocumentService:
        """Get document service instance (lazy loaded)."""
        if self._document_service is None:
            self._document_service = self._container.get(IDocumentService)
        return self._document_service
    
    @property
    def bibliography_service(self) -> IBibliographyService:
        """Get bibliography service instance (lazy loaded)."""
        if self._bibliography_service is None:
            self._bibliography_service = self._container.get(IBibliographyService)
        return self._bibliography_service
    
    @property
    def duplicate_service(self) -> IDuplicateDetectionService:
        """Get duplicate detection service instance (lazy loaded)."""
        if self._duplicate_service is None:
            self._duplicate_service = self._container.get(IDuplicateDetectionService)
        return self._duplicate_service
    
    @property
    def chunking_service(self) -> IChunkingService:
        """Get chunking service instance (lazy loaded)."""
        if self._chunking_service is None:
            self._chunking_service = self._container.get(IChunkingService)
        return self._chunking_service
    
    @property
    def paper_repository(self) -> IPaperRepository:
        """Get paper repository instance (lazy loaded)."""
        if self._paper_repository is None:
            self._paper_repository = self._container.get(IPaperRepository)
        return self._paper_repository
    
    @property
    def chunk_repository(self) -> IChunkRepository:
        """Get chunk repository instance (lazy loaded)."""
        if self._chunk_repository is None:
            self._chunk_repository = self._container.get(IChunkRepository)
        return self._chunk_repository
    
    def upload_paper(self, file_path: str, title: Optional[str] = None, 
                    authors: Optional[List[str]] = None, doi: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Upload and process research paper.
        
        Uses interface-based dependency injection instead of direct instantiation.
        """
        try:
            paper = self.document_service.upload_paper(
                file_path=file_path,
                title=title,
                authors=authors,
                doi=doi,
                tags=tags
            )
            
            return self._create_success_response({
                "paper_id": paper.id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors] if paper.authors else [],
                "doi": paper.doi
            }, "Paper uploaded successfully")
            
        except Exception as e:
            logger.error(f"Error uploading paper: {str(e)}")
            return self._create_error_response(str(e))
    
    def upload_bibliography_batch(self, file_path: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Upload papers from bibliography file.
        
        Uses bibliography service interface instead of direct implementation.
        """
        try:
            papers = self.bibliography_service.upload_bibliography_batch(file_path, tags)
            
            return self._create_success_response({
                "papers_count": len(papers),
                "papers": [{"id": p.id, "title": p.title} for p in papers[:5]]  # First 5 for preview
            }, f"Successfully uploaded {len(papers)} papers from bibliography")
            
        except Exception as e:
            logger.error(f"Error uploading bibliography: {str(e)}")
            return self._create_error_response(str(e))
    
    def list_papers(self, offset: int = 0, limit: int = 20, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List papers with pagination.
        
        This should fix the slice indices error from the original implementation.
        """
        try:
            # Validate parameters to prevent slice errors
            offset = max(0, int(offset))
            limit = max(1, min(100, int(limit)))  # Limit between 1 and 100
            
            # Use repository interface with proper pagination
            papers = self.paper_repository.list_all(filters)
            
            # Apply pagination manually for now (could be moved to repository)
            total_count = len(papers)
            paginated_papers = papers[offset:offset + limit]
            
            return self._create_success_response({
                "papers": [self._paper_to_dict(paper) for paper in paginated_papers],
                "pagination": {
                    "offset": offset,
                    "limit": limit,
                    "total": total_count,
                    "has_more": offset + limit < total_count
                }
            })
            
        except Exception as e:
            logger.error(f"Error listing papers: {str(e)}")
            return self._create_error_response(f"Failed to list papers: {str(e)}")
    
    def get_paper(self, paper_id: int) -> Dict[str, Any]:
        """
        Get paper by ID.
        
        Uses repository interface instead of direct database access.
        """
        try:
            paper = self.paper_repository.get_by_id(paper_id)
            
            if not paper:
                return self._create_error_response(f"Paper with ID {paper_id} not found")
            
            return self._create_success_response(self._paper_to_dict(paper))
            
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {str(e)}")
            return self._create_error_response(str(e))
    
    def search_papers(self, query: str, limit: int = 20, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search papers by query.
        
        Uses repository interface to fix search issues.
        """
        try:
            if not query or not query.strip():
                return self._create_error_response("Query parameter is required")
            
            # Use repository interface for search
            papers = self.paper_repository.search_papers(query, filters)
            
            # Apply limit
            limit = max(1, min(100, int(limit)))
            limited_papers = papers[:limit]
            
            return self._create_success_response({
                "query": query,
                "papers": [self._paper_to_dict(paper) for paper in limited_papers],
                "total_found": len(papers)
            })
            
        except Exception as e:
            logger.error(f"Error searching papers with query '{query}': {str(e)}")
            return self._create_error_response(f"Search failed: {str(e)}")
    
    def index_paper(self, paper_id: int, strategy: str = "hybrid", 
                   optimization_level: str = "intermediate", force: bool = False) -> Dict[str, Any]:
        """
        Index paper with intelligent chunking.
        
        Uses chunking service interface instead of direct implementation.
        """
        try:
            # Convert string parameters to enums
            indexing_strategy = IndexingStrategy(strategy)
            opt_level = OptimizationLevel(optimization_level)
            
            # Use chunking service interface
            if force:
                chunks = self.chunking_service.reindex_paper(
                    paper_id, force=True, new_strategy=indexing_strategy
                )
            else:
                chunks = self.chunking_service.index_paper(
                    paper_id, indexing_strategy, opt_level
                )
            
            return self._create_success_response({
                "paper_id": paper_id,
                "chunks_created": len(chunks),
                "average_chunk_size": sum(c.word_count or 0 for c in chunks) / len(chunks) if chunks else 0,
                "strategy": strategy,
                "optimization_level": optimization_level
            }, f"Successfully indexed paper {paper_id} with {len(chunks)} chunks")
            
        except ValueError as e:
            return self._create_error_response(f"Invalid parameter: {str(e)}")
        except Exception as e:
            logger.error(f"Error indexing paper {paper_id}: {str(e)}")
            return self._create_error_response(str(e))
    
    def detect_remove_duplicates(self, similarity_threshold: float = 0.85, dry_run: bool = True) -> Dict[str, Any]:
        """
        Detect and optionally remove duplicate papers.
        
        Uses duplicate detection service interface.
        """
        try:
            # Validate threshold
            if not 0.0 <= similarity_threshold <= 1.0:
                return self._create_error_response("Similarity threshold must be between 0.0 and 1.0")
            
            # Use duplicate detection service
            duplicate_groups = self.duplicate_service.detect_duplicates(similarity_threshold)
            
            if dry_run:
                return self._create_success_response({
                    "duplicates_found": len(duplicate_groups),
                    "total_duplicate_papers": sum(len(group) for group in duplicate_groups),
                    "duplicate_groups": [
                        [{"id": paper.id, "title": paper.title} for paper in group]
                        for group in duplicate_groups[:5]  # First 5 groups for preview
                    ],
                    "dry_run": True
                })
            else:
                result = self.duplicate_service.remove_duplicates(duplicate_groups, dry_run=False)
                return self._create_success_response(result)
                
        except Exception as e:
            logger.error(f"Error in duplicate detection: {str(e)}")
            return self._create_error_response(str(e))
    
    def _create_success_response(self, data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response
    
    def _create_error_response(self, error_message: str, error_type: str = "system") -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "error_type": error_type
        }
    
    def _paper_to_dict(self, paper) -> Dict[str, Any]:
        """Convert paper to dictionary representation."""
        return {
            "id": paper.id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors] if paper.authors else [],
            "publication_year": paper.publication_year,
            "journal": paper.journal.name if paper.journal else None,
            "doi": paper.doi,
            "abstract": paper.abstract[:200] + "..." if paper.abstract and len(paper.abstract) > 200 else paper.abstract,
            "indexed": paper.indexed,
            "tags": paper.keywords or []
        }