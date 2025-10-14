"""
Repository for research paper data access and management.

Implements data persistence operations for research papers with academic metadata,
author relationships, and systematic literature review status tracking.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import ResearchPaper, Author, Journal
from .base_repository import BaseRepository, DatabaseConnection, RepositoryError, EntityNotFoundError


class PaperRepository(BaseRepository[ResearchPaper]):
    """
    Repository for research paper data access and management.

    This repository handles persistence operations for research papers including:
    - Paper metadata and content management
    - Author and journal relationship handling
    - Quality assessment status tracking
    - Review inclusion/exclusion status
    - Academic search and filtering
    - Full-text search integration

    Follows Repository pattern with proper error handling and transaction support.
    """

    def create(self, paper: ResearchPaper) -> ResearchPaper:
        """
        Create a new research paper in the database.

        Args:
            paper: ResearchPaper instance to create

        Returns:
            Created paper with populated ID and timestamps

        Raises:
            RepositoryError: If creation fails
            DuplicateEntityError: If paper with same file_path exists
        """
        try:
            # Check for duplicate file_path
            existing = self._get_by_file_path(paper.file_path)
            if existing:
                from .base_repository import DuplicateEntityError
                raise DuplicateEntityError("ResearchPaper", f"file_path={paper.file_path}")

            # Insert main paper record
            cursor = self.db.execute(
                """
                INSERT INTO research_papers (
                    title, file_path, file_type, publication_year, doi, abstract,
                    keywords, methodology, study_type, sample_size, citation_count,
                    upload_date, file_size, total_pages, total_words, tags,
                    indexed, quality_assessed, included_in_review, exclusion_reason,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.title,
                    paper.file_path,
                    paper.file_type,
                    paper.publication_year,
                    paper.doi,
                    paper.abstract,
                    json.dumps(paper.keywords),
                    paper.methodology,
                    paper.study_type,
                    paper.sample_size,
                    paper.citation_count,
                    paper.upload_date.isoformat() if paper.upload_date else None,
                    paper.file_size,
                    paper.total_pages,
                    paper.total_words,
                    json.dumps(paper.tags),
                    paper.indexed,
                    paper.quality_assessed,
                    paper.included_in_review,
                    paper.exclusion_reason,
                    paper.notes,
                    paper.created_at.isoformat() if paper.created_at else None,
                    paper.updated_at.isoformat() if paper.updated_at else None
                )
            )

            paper_id = cursor.lastrowid
            if not paper_id:
                raise RepositoryError("Failed to create research paper: no ID returned")

            self.db.commit()

            # Handle authors and journal relationships
            if paper.authors:
                self._create_paper_authors(paper_id, paper.authors)

            if paper.journal:
                self._create_or_link_journal(paper_id, paper.journal)

            # Return the created paper with ID
            created_paper = self.get_by_id(paper_id)
            if not created_paper:
                raise RepositoryError(f"Failed to retrieve created paper with ID {paper_id}")

            return created_paper

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to create research paper: {e}", e)

    def get_by_id(self, paper_id: int) -> Optional[ResearchPaper]:
        """
        Retrieve a research paper by ID with all relationships.

        Args:
            paper_id: Primary key of the paper

        Returns:
            ResearchPaper instance if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.execute(
                """
                SELECT rp.*, j.name as journal_name, j.issn, j.publisher, 
                       j.impact_factor, j.quartile, j.open_access
                FROM research_papers rp
                LEFT JOIN paper_journals pj ON rp.id = pj.paper_id
                LEFT JOIN journals j ON pj.journal_id = j.id
                WHERE rp.id = ?
                """,
                (paper_id,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Get authors for this paper
            authors = self._get_paper_authors(paper_id)

            # Parse journal if present
            journal = None
            if row[24]:  # journal_name
                journal = Journal(
                    name=row[24],
                    issn=row[25],
                    publisher=row[26],
                    impact_factor=row[27],
                    quartile=row[28],
                    open_access=bool(row[29])
                )

            return self._row_to_paper(row, authors, journal)

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to get research paper by ID {paper_id}: {e}", e)

    def update(self, paper: ResearchPaper) -> ResearchPaper:
        """
        Update an existing research paper.

        Args:
            paper: ResearchPaper instance with updated data

        Returns:
            Updated paper

        Raises:
            RepositoryError: If update fails
            EntityNotFoundError: If paper not found
        """
        if not paper.id:
            raise RepositoryError("Cannot update paper without ID")

        try:
            # Update main paper record
            cursor = self.db.execute(
                """
                UPDATE research_papers SET
                    title = ?, file_path = ?, file_type = ?, publication_year = ?, 
                    doi = ?, abstract = ?, keywords = ?, methodology = ?, 
                    study_type = ?, sample_size = ?, citation_count = ?,
                    file_size = ?, total_pages = ?, total_words = ?, tags = ?,
                    indexed = ?, quality_assessed = ?, included_in_review = ?,
                    exclusion_reason = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    paper.title,
                    paper.file_path,
                    paper.file_type,
                    paper.publication_year,
                    paper.doi,
                    paper.abstract,
                    json.dumps(paper.keywords),
                    paper.methodology,
                    paper.study_type,
                    paper.sample_size,
                    paper.citation_count,
                    paper.file_size,
                    paper.total_pages,
                    paper.total_words,
                    json.dumps(paper.tags),
                    paper.indexed,
                    paper.quality_assessed,
                    paper.included_in_review,
                    paper.exclusion_reason,
                    paper.notes,
                    datetime.now().isoformat(),
                    paper.id
                )
            )

            if cursor.rowcount == 0:
                raise EntityNotFoundError("ResearchPaper", paper.id)

            self.db.commit()

            # Update authors and journal relationships
            self._update_paper_authors(paper.id, paper.authors)
            
            if paper.journal:
                self._create_or_link_journal(paper.id, paper.journal)

            # Return updated paper
            updated_paper = self.get_by_id(paper.id)
            if not updated_paper:
                raise RepositoryError(f"Failed to retrieve updated paper with ID {paper.id}")

            return updated_paper

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to update research paper {paper.id}: {e}", e)

    def delete(self, paper_id: int) -> bool:
        """
        Delete a research paper and all related data.

        Args:
            paper_id: Primary key of the paper to delete

        Returns:
            True if paper was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.execute(
                "DELETE FROM research_papers WHERE id = ?",
                (paper_id,)
            )

            deleted = cursor.rowcount > 0
            if deleted:
                self.db.commit()

            return deleted

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to delete research paper {paper_id}: {e}", e)

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[ResearchPaper]:
        """
        List research papers with optional filtering.

        Args:
            filters: Optional filter criteria including:
                - authors: List of author names
                - publication_year: Year of publication
                - tags: List of tags
                - quality_score_min: Minimum quality score
                - included_in_review: Boolean for review inclusion
                - methodology: Research methodology
                - study_type: Type of study

        Returns:
            List of ResearchPaper instances

        Raises:
            RepositoryError: If query fails
        """
        try:
            # Build base query
            query = """
                SELECT DISTINCT rp.*, j.name as journal_name, j.issn, j.publisher, 
                       j.impact_factor, j.quartile, j.open_access
                FROM research_papers rp
                LEFT JOIN paper_journals pj ON rp.id = pj.paper_id
                LEFT JOIN journals j ON pj.journal_id = j.id
                LEFT JOIN paper_authors pa ON rp.id = pa.paper_id
                LEFT JOIN authors a ON pa.author_id = a.id
            """

            conditions = []
            parameters = []

            if filters:
                # Author name filtering
                if 'authors' in filters and filters['authors']:
                    author_conditions = []
                    for author_name in filters['authors']:
                        author_conditions.append("a.name LIKE ?")
                        parameters.append(f"%{author_name}%")
                    if author_conditions:
                        conditions.append(f"({' OR '.join(author_conditions)})")

                # Simple field filters
                simple_fields = {
                    'publication_year': 'rp.publication_year',
                    'methodology': 'rp.methodology',
                    'study_type': 'rp.study_type',
                    'included_in_review': 'rp.included_in_review',
                    'indexed': 'rp.indexed',
                    'quality_assessed': 'rp.quality_assessed'
                }

                for filter_key, db_field in simple_fields.items():
                    if filter_key in filters:
                        conditions.append(f"{db_field} = ?")
                        parameters.append(filters[filter_key])

                # Tag filtering (JSON array search)
                if 'tags' in filters and filters['tags']:
                    tag_conditions = []
                    for tag in filters['tags']:
                        tag_conditions.append("rp.tags LIKE ?")
                        parameters.append(f'%"{tag}"%')
                    if tag_conditions:
                        conditions.append(f"({' OR '.join(tag_conditions)})")

            # Add WHERE clause if conditions exist
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"

            query += " ORDER BY rp.created_at DESC"

            cursor = self.db.execute(query, tuple(parameters))
            rows = cursor.fetchall()

            papers = []
            for row in rows:
                # Get authors for each paper (could be optimized with a join)
                authors = self._get_paper_authors(row[0])  # row[0] is paper ID

                # Parse journal if present
                journal = None
                if row[24]:  # journal_name
                    journal = Journal(
                        name=row[24],
                        issn=row[25],
                        publisher=row[26],
                        impact_factor=row[27],
                        quartile=row[28],
                        open_access=bool(row[29]) if row[29] is not None else False
                    )

                paper = self._row_to_paper(row, authors, journal)
                papers.append(paper)

            return papers

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to list research papers: {e}", e)

    def search_papers(self, query: str, limit: int = 20) -> List[ResearchPaper]:
        """
        Full-text search across research papers.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching ResearchPaper instances

        Raises:
            RepositoryError: If search fails
        """
        try:
            cursor = self.db.execute(
                """
                SELECT rp.*, j.name as journal_name, j.issn, j.publisher, 
                       j.impact_factor, j.quartile, j.open_access
                FROM research_papers_fts fts
                JOIN research_papers rp ON fts.paper_id = rp.id
                LEFT JOIN paper_journals pj ON rp.id = pj.paper_id
                LEFT JOIN journals j ON pj.journal_id = j.id
                WHERE research_papers_fts MATCH ?
                ORDER BY bm25(research_papers_fts)
                LIMIT ?
                """,
                (query, limit)
            )

            rows = cursor.fetchall()
            papers = []

            for row in rows:
                authors = self._get_paper_authors(row[0])  # row[0] is paper ID
                
                journal = None
                if row[24]:  # journal_name
                    journal = Journal(
                        name=row[24],
                        issn=row[25],
                        publisher=row[26],
                        impact_factor=row[27],
                        quartile=row[28],
                        open_access=bool(row[29]) if row[29] is not None else False
                    )

                paper = self._row_to_paper(row, authors, journal)
                papers.append(paper)

            return papers

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to search research papers: {e}", e)

    def get_by_file_path(self, file_path: str) -> Optional[ResearchPaper]:
        """
        Get research paper by file path.

        Args:
            file_path: Path to the paper file

        Returns:
            ResearchPaper if found, None otherwise
        """
        return self._get_by_file_path(file_path)

    def get_papers_by_author(self, author_name: str) -> List[ResearchPaper]:
        """
        Get all papers by a specific author.

        Args:
            author_name: Name of the author

        Returns:
            List of ResearchPaper instances
        """
        return self.list_all({'authors': [author_name]})

    def get_papers_for_review(self, included_only: bool = True) -> List[ResearchPaper]:
        """
        Get papers that are included/excluded from systematic review.

        Args:
            included_only: If True, return only included papers

        Returns:
            List of ResearchPaper instances
        """
        return self.list_all({'included_in_review': included_only})

    def count_by_year(self) -> Dict[int, int]:
        """
        Get count of papers by publication year.

        Returns:
            Dictionary mapping year to paper count
        """
        try:
            cursor = self.db.execute(
                """
                SELECT publication_year, COUNT(*) 
                FROM research_papers 
                WHERE publication_year IS NOT NULL
                GROUP BY publication_year
                ORDER BY publication_year DESC
                """
            )
            
            return {row[0]: row[1] for row in cursor.fetchall()}

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to count papers by year: {e}", e)

    # Private helper methods

    def _get_by_file_path(self, file_path: str) -> Optional[ResearchPaper]:
        """Get paper by file path."""
        try:
            cursor = self.db.execute(
                "SELECT id FROM research_papers WHERE file_path = ?",
                (file_path,)
            )
            
            row = cursor.fetchone()
            if row:
                return self.get_by_id(row[0])
            
            return None

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to get paper by file path: {e}", e)

    def _get_paper_authors(self, paper_id: int) -> List[Author]:
        """Get all authors for a paper."""
        try:
            cursor = self.db.execute(
                """
                SELECT a.id, a.name, a.email, a.affiliation, a.orcid, 
                       a.h_index, a.citation_count, a.created_at
                FROM authors a
                JOIN paper_authors pa ON a.id = pa.author_id
                WHERE pa.paper_id = ?
                ORDER BY pa.author_order
                """,
                (paper_id,)
            )

            authors = []
            for row in cursor.fetchall():
                created_at = datetime.fromisoformat(row[7]) if row[7] else None
                author = Author(
                    id=row[0],
                    name=row[1],
                    email=row[2],
                    affiliation=row[3],
                    orcid=row[4],
                    h_index=row[5],
                    citation_count=row[6],
                    created_at=created_at
                )
                authors.append(author)

            return authors

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to get paper authors: {e}", e)

    def _create_paper_authors(self, paper_id: int, authors: List[Author]) -> None:
        """Create author relationships for a paper."""
        try:
            for order, author in enumerate(authors):
                # Create or get author
                author_id = self._create_or_get_author(author)
                
                # Link author to paper
                self.db.execute(
                    "INSERT INTO paper_authors (paper_id, author_id, author_order) VALUES (?, ?, ?)",
                    (paper_id, author_id, order)
                )

            self.db.commit()

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to create paper authors: {e}", e)

    def _update_paper_authors(self, paper_id: int, authors: List[Author]) -> None:
        """Update author relationships for a paper."""
        try:
            # Remove existing relationships
            self.db.execute("DELETE FROM paper_authors WHERE paper_id = ?", (paper_id,))
            
            # Add new relationships
            if authors:
                self._create_paper_authors(paper_id, authors)

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to update paper authors: {e}", e)

    def _create_or_get_author(self, author: Author) -> int:
        """Create author or get existing ID."""
        try:
            # Try to find existing author by name (and email if provided)
            if author.email:
                cursor = self.db.execute(
                    "SELECT id FROM authors WHERE name = ? AND email = ?",
                    (author.name, author.email)
                )
            else:
                cursor = self.db.execute(
                    "SELECT id FROM authors WHERE name = ?",
                    (author.name,)
                )

            row = cursor.fetchone()
            if row:
                return row[0]

            # Create new author
            cursor = self.db.execute(
                """
                INSERT INTO authors (name, email, affiliation, orcid, h_index, citation_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    author.name,
                    author.email,
                    author.affiliation,
                    author.orcid,
                    author.h_index,
                    author.citation_count,
                    datetime.now().isoformat()
                )
            )

            return cursor.lastrowid

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to create or get author: {e}", e)

    def _create_or_link_journal(self, paper_id: int, journal: Journal) -> None:
        """Create or link journal to paper."""
        try:
            # Try to find existing journal
            cursor = self.db.execute(
                "SELECT id FROM journals WHERE name = ?",
                (journal.name,)
            )

            row = cursor.fetchone()
            if row:
                journal_id = row[0]
            else:
                # Create new journal
                cursor = self.db.execute(
                    """
                    INSERT INTO journals (name, issn, publisher, impact_factor, quartile, open_access, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        journal.name,
                        journal.issn,
                        journal.publisher,
                        float(journal.impact_factor) if journal.impact_factor else None,
                        journal.quartile,
                        journal.open_access,
                        datetime.now().isoformat()
                    )
                )
                journal_id = cursor.lastrowid

            # Link journal to paper
            self.db.execute(
                "INSERT OR REPLACE INTO paper_journals (paper_id, journal_id) VALUES (?, ?)",
                (paper_id, journal_id)
            )

            self.db.commit()

        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to create or link journal: {e}", e)

    def _row_to_paper(self, row: tuple, authors: List[Author], journal: Optional[Journal]) -> ResearchPaper:
        """Convert database row to ResearchPaper instance."""
        upload_date = datetime.fromisoformat(row[11]) if row[11] else None
        created_at = datetime.fromisoformat(row[21]) if row[21] else None
        updated_at = datetime.fromisoformat(row[22]) if row[22] else None

        return ResearchPaper(
            id=row[0],
            title=row[1],
            file_path=row[2],
            file_type=row[3],
            authors=authors,
            journal=journal,
            publication_year=row[4],
            doi=row[5],
            abstract=row[6],
            keywords=json.loads(row[7]) if row[7] else [],
            methodology=row[8],
            study_type=row[9],
            sample_size=row[10],
            citation_count=row[12],
            upload_date=upload_date,
            file_size=row[13],
            total_pages=row[14],
            total_words=row[15],
            tags=json.loads(row[16]) if row[16] else [],
            indexed=bool(row[17]),
            quality_assessed=bool(row[18]),
            included_in_review=row[19],
            exclusion_reason=row[20],
            notes=row[23],
            created_at=created_at,
            updated_at=updated_at
        )