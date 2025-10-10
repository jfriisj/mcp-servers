"""Document repository implementation with SQLite operations and FTS5 search.

Provides document-specific data access operations including
full-text search capabilities using SQLite FTS5 extension.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..database.connection import DatabaseConnection
from ..models.document import Document

from ..repositories.base_repository import (
    BaseRepository,
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
)


class DocumentRepository(BaseRepository[Document]):
    """Repository for document data access operations.

    Provides CRUD operations for Document entities with additional
    capabilities for full-text search using SQLite FTS5.

    Follows Clean Architecture Layer 3 principles:
    - No business logic (only data access)
    - Depends on database abstraction
    - Transforms between database rows and domain models
    - Handles database-specific error mapping

    Features:
    - Full CRUD operations for documents
    - FTS5 full-text search with ranking
    - Tag-based filtering
    - File type filtering
    - Duplicate prevention by file path
    """

    def __init__(self, db: DatabaseConnection):
        """Initialize repository with database connection.

        Args:
            db: Database connection for executing queries
        """
        super().__init__(db)

    def create(self, document: Document) -> Document:
        """Create a new document in the database.

        Args:
            document: Document entity to create

        Returns:
            Created document with populated ID and timestamps

        Raises:
            DuplicateEntityError: If document with same file_path exists
            RepositoryError: If creation fails
        """
        try:
            # Check for duplicate file_path
            if document.file_path and self.exists_by_file_path(document.file_path):
                raise DuplicateEntityError(
                    "Document",
                    f"file_path={document.file_path}"
                )

            cursor = self.db.cursor()

            # Ensure timestamps are set
            now = datetime.now()
            if not document.upload_date:
                document.upload_date = now
            if not document.created_at:
                document.created_at = now
            if not document.updated_at:
                document.updated_at = now

            # Insert document
            cursor.execute("""
                INSERT INTO documents (
                    title, file_path, file_type, upload_date,
                    total_pages, total_words, tags, notes,
                    indexed, summarized, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.title,
                document.file_path,
                document.file_type,
                document.upload_date.isoformat() if document.upload_date else None,
                document.total_pages,
                document.total_words,
                json.dumps(document.tags) if document.tags else "[]",
                document.notes,
                document.indexed,
                document.summarized,
                document.created_at.isoformat() if document.created_at else None,
                document.updated_at.isoformat() if document.updated_at else None
            ))

            # Get the generated ID
            document.id = cursor.lastrowid

            # Insert into FTS5 search index
            cursor.execute("""
                INSERT INTO documents_fts (
                    document_id, title, content
                ) VALUES (?, ?, ?)
            """, (
                document.id,
                document.title or "",
                ""  # Content will be updated by triggers when chunks are added
            ))

            self.db.commit()
            return document

        except DuplicateEntityError:
            self.db.rollback()
            raise  # Re-raise DuplicateEntityError as is
        except sqlite3.IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateEntityError(
                    "Document",
                    f"file_path={document.file_path}"
                )
            raise RepositoryError(f"Failed to create document: {str(e)}", e)
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to create document: {str(e)}", e)

    def get_by_id(self, document_id: int) -> Optional[Document]:
        """Retrieve a document by ID.

        Args:
            document_id: Primary key of the document

        Returns:
            Document if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT
                    id, title, file_path, file_type, upload_date,
                    total_pages, total_words, tags, notes,
                    indexed, summarized, created_at, updated_at
                FROM documents
                WHERE id = ?
            """, (document_id,))

            row = cursor.fetchone()
            return self._row_to_document(row) if row else None

        except Exception as e:
            raise RepositoryError(f"Failed to get document {document_id}: {str(e)}", e)

    def update(self, document: Document) -> Document:
        """Update an existing document.

        Args:
            document: Document with updated data (must have valid ID)

        Returns:
            Updated document

        Raises:
            EntityNotFoundError: If document with ID doesn't exist
            RepositoryError: If update fails
        """
        try:
            if not document.id:
                raise ValueError("Document must have an ID for update")

            cursor = self.db.cursor()

            # Update timestamps
            document.updated_at = datetime.now()

            # Update document
            cursor.execute("""
                UPDATE documents SET
                    title = ?, file_path = ?, file_type = ?,
                    upload_date = ?, total_pages = ?, total_words = ?,
                    tags = ?, notes = ?, indexed = ?, summarized = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                document.title,
                document.file_path,
                document.file_type,
                document.upload_date.isoformat() if document.upload_date else None,
                document.total_pages,
                document.total_words,
                json.dumps(document.tags) if document.tags else "[]",
                document.notes,
                document.indexed,
                document.summarized,
                document.updated_at.isoformat() if document.updated_at else None,
                document.id
            ))

            if cursor.rowcount == 0:
                raise EntityNotFoundError("Document", document.id)

            # Update FTS5 search index
            cursor.execute("""
                UPDATE documents_fts SET
                    title = ?
                WHERE document_id = ?
            """, (
                document.title or "",
                document.id
            ))

            self.db.commit()
            return document

        except EntityNotFoundError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to update document {document.id}: {str(e)}", e)

    def delete(self, document_id: int) -> bool:
        """Delete a document and all related data.

        Args:
            document_id: Primary key of document to delete

        Returns:
            True if document was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete from FTS5 index first
            cursor.execute("DELETE FROM documents_fts WHERE document_id = ?", (document_id,))

            # Delete document (CASCADE will handle chunks and summaries)
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

            deleted = cursor.rowcount > 0
            self.db.commit()
            return deleted

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete document {document_id}: {str(e)}", e)

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """List all documents with optional filtering.

        Args:
            filters: Optional filter criteria:
                - file_type: Filter by file type (pdf, docx, etc.)
                - indexed: Filter by indexing status (True/False)
                - summarized: Filter by summarization status (True/False)
                - tags: List of tags (documents must have all tags)
                - limit: Maximum number of results
                - offset: Number of results to skip (for pagination)

        Returns:
            List of documents matching filters

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()

            # Build base query
            query = """
                SELECT
                    id, title, file_path, file_type, upload_date,
                    total_pages, total_words, tags, notes,
                    indexed, summarized, created_at, updated_at
                FROM documents
            """

            params = []
            conditions = []

            if filters:
                # File type filter
                if "file_type" in filters:
                    conditions.append("file_type = ?")
                    params.append(filters["file_type"])

                # Boolean filters
                for field in ["indexed", "summarized"]:
                    if field in filters:
                        conditions.append(f"{field} = ?")
                        params.append(filters[field])

                # Tag filter (document must contain all specified tags)
                if "tags" in filters and filters["tags"]:
                    tag_conditions = []
                    for tag in filters["tags"]:
                        tag_conditions.append("json_extract(tags, '$') LIKE ?")
                        params.append(f'%"{tag}"%')
                    conditions.append(f"({' AND '.join(tag_conditions)})")

            # Add WHERE clause if we have conditions
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Add ordering
            query += " ORDER BY created_at DESC"

            # Add pagination
            if filters:
                if "limit" in filters:
                    query += " LIMIT ?"
                    params.append(filters["limit"])
                if "offset" in filters:
                    query += " OFFSET ?"
                    params.append(filters["offset"])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_document(row) for row in rows]

        except Exception as e:
            raise RepositoryError(f"Failed to list documents: {str(e)}", e)

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Full-text search using FTS5 with ranking.

        Args:
            query: Search query string
            filters: Optional additional filters (same as list_all)

        Returns:
            List of (document, relevance_score) tuples ordered by relevance

        Raises:
            RepositoryError: If search fails
        """
        try:
            if not query or not query.strip():
                # Empty query returns all documents
                documents = self.list_all(filters)
                return [(doc, 1.0) for doc in documents]

            cursor = self.db.cursor()

            # Build FTS5 search query - search both documents and chunks
            search_query = """
                SELECT DISTINCT
                    d.id, d.title, d.file_path, d.file_type, d.upload_date,
                    d.total_pages, d.total_words, d.tags, d.notes,
                    d.indexed, d.summarized, d.created_at, d.updated_at,
                    1.0 as relevance_score
                FROM documents d
                WHERE d.id IN (
                    SELECT document_id FROM documents_fts WHERE documents_fts MATCH ?
                    UNION
                    SELECT document_id FROM chunks_fts WHERE chunks_fts MATCH ?
                )
            """

            params = [query, query]
            conditions = []

            # Add additional filters
            if filters:
                if "file_type" in filters:
                    conditions.append("d.file_type = ?")
                    params.append(filters["file_type"])

                for field in ["indexed", "summarized"]:
                    if field in filters:
                        conditions.append(f"d.{field} = ?")
                        params.append(filters[field])

                if "tags" in filters and filters["tags"]:
                    tag_conditions = []
                    for tag in filters["tags"]:
                        tag_conditions.append("json_extract(d.tags, '$') LIKE ?")
                        params.append(f'%"{tag}"%')
                    conditions.append(f"({' AND '.join(tag_conditions)})")

            if conditions:
                search_query += " AND " + " AND ".join(conditions)

            # Order by relevance
            search_query += " ORDER BY relevance_score DESC"

            # Add pagination
            if filters:
                if "limit" in filters:
                    search_query += " LIMIT ?"
                    params.append(filters["limit"])

            cursor.execute(search_query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                document = self._row_to_document(row[:-1])  # Exclude relevance score
                relevance_score = float(row[-1]) if row[-1] else 0.0
                results.append((document, relevance_score))

            return results

        except Exception as e:
            raise RepositoryError(f"Failed to search documents: {str(e)}", e)

    def get_by_file_path(self, file_path: str) -> Optional[Document]:
        """Get document by file path.

        Args:
            file_path: Path to the document file

        Returns:
            Document if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT
                    id, title, file_path, file_type, upload_date,
                    total_pages, total_words, tags, notes,
                    indexed, summarized, created_at, updated_at
                FROM documents
                WHERE file_path = ?
            """, (file_path,))

            row = cursor.fetchone()
            return self._row_to_document(row) if row else None

        except Exception as e:
            raise RepositoryError(f"Failed to get document by path {file_path}: {str(e)}", e)

    def exists_by_file_path(self, file_path: str) -> bool:
        """Check if document exists by file path.

        Args:
            file_path: Path to check

        Returns:
            True if document exists with this path
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT 1 FROM documents WHERE file_path = ? LIMIT 1",
                (file_path,)
            )
            return cursor.fetchone() is not None

        except Exception as e:
            raise RepositoryError(f"Failed to check document existence: {str(e)}", e)

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching filters (optimized implementation).

        Args:
            filters: Optional filter criteria

        Returns:
            Number of documents matching filters
        """
        try:
            cursor = self.db.cursor()
            query = "SELECT COUNT(*) FROM documents"
            params = []
            conditions = []

            if filters:
                if "file_type" in filters:
                    conditions.append("file_type = ?")
                    params.append(filters["file_type"])

                for field in ["indexed", "summarized"]:
                    if field in filters:
                        conditions.append(f"{field} = ?")
                        params.append(filters[field])

                if "tags" in filters and filters["tags"]:
                    tag_conditions = []
                    for tag in filters["tags"]:
                        tag_conditions.append("json_extract(tags, '$') LIKE ?")
                        params.append(f'%"{tag}"%')
                    conditions.append(f"({' AND '.join(tag_conditions)})")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

        except Exception as e:
            raise RepositoryError(f"Failed to count documents: {str(e)}", e)

    def exists(self, document_id: int) -> bool:
        """Check if document exists by ID (optimized implementation).

        Args:
            document_id: Document ID to check

        Returns:
            True if document exists
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT 1 FROM documents WHERE id = ? LIMIT 1",
                (document_id,)
            )
            return cursor.fetchone() is not None

        except Exception as e:
            raise RepositoryError(f"Failed to check document existence: {str(e)}", e)

    def _row_to_document(self, row: tuple) -> Document:
        """Convert database row to Document model.

        Args:
            row: Database row tuple

        Returns:
            Document instance
        """
        if not row:
            # This should never happen given the method contract
            raise ValueError("Row is None in _row_to_document")

        return Document(
            id=row[0],
            title=row[1],
            file_path=row[2],
            file_type=row[3],
            upload_date=datetime.fromisoformat(row[4]) if row[4] else None,
            total_pages=row[5],
            total_words=row[6],
            tags=json.loads(row[7]) if row[7] else [],
            notes=row[8],
            indexed=bool(row[9]),
            summarized=bool(row[10]),
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None
        )
