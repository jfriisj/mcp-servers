"""Chunk repository implementation with relationship management.

Provides chunk-specific data access operations including
document relationships and cascade operations.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.connection import DatabaseConnection
from ..models.chunk import Chunk

from ..repositories.base_repository import (
    BaseRepository,
    EntityNotFoundError,
    RepositoryError,
)


class ChunkRepository(BaseRepository[Chunk]):
    """Repository for chunk data access operations.

    Provides CRUD operations for Chunk entities with relationship
    management to Document entities and cascade operations.

    Follows Clean Architecture Layer 3 principles:
    - No business logic (only data access)
    - Manages foreign key relationships properly
    - Handles cascade operations for cleanup
    - Transforms between database rows and domain models

    Features:
    - Full CRUD operations for chunks
    - Document relationship queries
    - Cascade delete operations
    - Proper foreign key constraint handling
    """

    def __init__(self, db: DatabaseConnection):
        """Initialize repository with database connection.

        Args:
            db: Database connection for executing queries
        """
        super().__init__(db)

    def create(self, chunk: Chunk) -> Chunk:
        """Create a new chunk in the database.

        Args:
            chunk: Chunk entity to create

        Returns:
            Created chunk with populated ID and timestamps

        Raises:
            RepositoryError: If creation fails

        Note:
            Validates that document_id references existing document.
        """
        try:
            cursor = self.db.cursor()

            # Ensure timestamps are set
            now = datetime.now()
            if not chunk.created_at:
                chunk.created_at = now

            # Validate document exists
            cursor.execute("SELECT 1 FROM documents WHERE id = ?", (chunk.document_id,))
            if not cursor.fetchone():
                raise RepositoryError(f"Document {chunk.document_id} not found")

            # Insert chunk
            cursor.execute("""
                INSERT INTO chunks (
                    document_id, chunk_index, chunk_type, title,
                    content, word_count, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.document_id,
                chunk.chunk_index,
                chunk.chunk_type,
                chunk.title,
                chunk.content,
                chunk.word_count,
                json.dumps(chunk.metadata) if chunk.metadata else "{}",
                chunk.created_at.isoformat() if chunk.created_at else None
            ))

            # Get the generated ID
            chunk.id = cursor.lastrowid

            self.db.commit()
            return chunk

        except Exception as e:
            self.db.rollback()
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to create chunk: {str(e)}", e)

    def get_by_id(self, chunk_id: int) -> Optional[Chunk]:
        """Retrieve a chunk by ID.

        Args:
            chunk_id: Primary key of the chunk

        Returns:
            Chunk if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT
                    id, document_id, chunk_index, chunk_type, title,
                    content, word_count, metadata, created_at
                FROM chunks
                WHERE id = ?
            """, (chunk_id,))

            row = cursor.fetchone()
            return self._row_to_chunk(row) if row else None

        except Exception as e:
            raise RepositoryError(f"Failed to get chunk {chunk_id}: {str(e)}", e)

    def update(self, chunk: Chunk) -> Chunk:
        """Update an existing chunk.

        Args:
            chunk: Chunk with updated data (must have valid ID)

        Returns:
            Updated chunk

        Raises:
            EntityNotFoundError: If chunk with ID doesn't exist
            RepositoryError: If update fails
        """
        try:
            if not chunk.id:
                raise ValueError("Chunk must have an ID for update")

            cursor = self.db.cursor()

            # Update chunk
            cursor.execute("""
                UPDATE chunks SET
                    document_id = ?, chunk_index = ?, chunk_type = ?, title = ?,
                    content = ?, word_count = ?, metadata = ?
                WHERE id = ?
            """, (
                chunk.document_id,
                chunk.chunk_index,
                chunk.chunk_type,
                chunk.title,
                chunk.content,
                chunk.word_count,
                json.dumps(chunk.metadata) if chunk.metadata else "{}",
                chunk.id
            ))

            if cursor.rowcount == 0:
                raise EntityNotFoundError("Chunk", chunk.id)

            self.db.commit()
            return chunk

        except EntityNotFoundError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to update chunk {chunk.id}: {str(e)}", e)

    def delete(self, chunk_id: int) -> bool:
        """Delete a chunk from the database.

        Args:
            chunk_id: Primary key of chunk to delete

        Returns:
            True if chunk was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete chunk (CASCADE will handle summaries)
            cursor.execute("DELETE FROM chunks WHERE id = ?", (chunk_id,))

            deleted = cursor.rowcount > 0
            self.db.commit()
            return deleted

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete chunk {chunk_id}: {str(e)}", e)

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """List all chunks with optional filtering.

        Args:
            filters: Optional filter criteria:
                - document_id: Filter by document ID
                - chunk_type: Filter by chunk type
                - limit: Maximum number of results
                - offset: Number of results to skip

        Returns:
            List of chunks matching filters

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()

            # Build base query
            query = """
                SELECT
                    id, document_id, chunk_index, chunk_type, title,
                    content, word_count, metadata, created_at
                FROM chunks
            """

            params = []
            conditions = []

            if filters:
                # Document ID filter
                if "document_id" in filters:
                    conditions.append("document_id = ?")
                    params.append(filters["document_id"])

                # Chunk type filter
                if "chunk_type" in filters:
                    conditions.append("chunk_type = ?")
                    params.append(filters["chunk_type"])

            # Add WHERE clause if we have conditions
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Add ordering (by chunk_index for proper order within documents)
            query += " ORDER BY document_id, chunk_index"

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

            return [self._row_to_chunk(row) for row in rows]

        except Exception as e:
            raise RepositoryError(f"Failed to list chunks: {str(e)}", e)

    def get_by_document_id(self, document_id: int) -> List[Chunk]:
        """Get all chunks for a specific document.

        Args:
            document_id: ID of the document

        Returns:
            List of chunks ordered by chunk_index

        Raises:
            RepositoryError: If query fails
        """
        return self.list_all({"document_id": document_id})

    def delete_by_document_id(self, document_id: int) -> int:
        """Delete all chunks for a document (cascade operation).

        Args:
            document_id: ID of the document

        Returns:
            Number of chunks deleted

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete all chunks for the document
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))

            deleted_count = cursor.rowcount
            self.db.commit()
            return deleted_count

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete chunks for document {document_id}: {str(e)}", e)

    def get_chunk_by_index(self, document_id: int, chunk_index: int) -> Optional[Chunk]:
        """Get a specific chunk by document ID and chunk index.

        Args:
            document_id: ID of the document
            chunk_index: Index of the chunk within the document

        Returns:
            Chunk if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT
                    id, document_id, chunk_index, chunk_type, title,
                    content, word_count, metadata, created_at
                FROM chunks
                WHERE document_id = ? AND chunk_index = ?
            """, (document_id, chunk_index))

            row = cursor.fetchone()
            return self._row_to_chunk(row) if row else None

        except Exception as e:
            raise RepositoryError(f"Failed to get chunk by index: {str(e)}", e)

    def count_by_document_id(self, document_id: int) -> int:
        """Count chunks for a specific document.

        Args:
            document_id: ID of the document

        Returns:
            Number of chunks for the document
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_id = ?",
                (document_id,)
            )
            return cursor.fetchone()[0]

        except Exception as e:
            raise RepositoryError(f"Failed to count chunks for document {document_id}: {str(e)}", e)

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count chunks matching filters (optimized implementation).

        Args:
            filters: Optional filter criteria

        Returns:
            Number of chunks matching filters
        """
        try:
            cursor = self.db.cursor()
            query = "SELECT COUNT(*) FROM chunks"
            params = []
            conditions = []

            if filters:
                if "document_id" in filters:
                    conditions.append("document_id = ?")
                    params.append(filters["document_id"])

                if "chunk_type" in filters:
                    conditions.append("chunk_type = ?")
                    params.append(filters["chunk_type"])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

        except Exception as e:
            raise RepositoryError(f"Failed to count chunks: {str(e)}", e)

    def get_document_chunks_count(self, document_id: int) -> int:
        """Get count of chunks for a specific document.

        Args:
            document_id: Document ID to count chunks for

        Returns:
            Number of chunks for the document

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_id = ?",
                (document_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

        except Exception as e:
            raise RepositoryError(f"Failed to count chunks for document {document_id}: {str(e)}", e)

    def exists(self, chunk_id: int) -> bool:
        """Check if chunk exists by ID (optimized implementation).

        Args:
            chunk_id: Chunk ID to check

        Returns:
            True if chunk exists
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT 1 FROM chunks WHERE id = ? LIMIT 1",
                (chunk_id,)
            )
            return cursor.fetchone() is not None

        except Exception as e:
            raise RepositoryError(f"Failed to check chunk existence: {str(e)}", e)

    def _row_to_chunk(self, row: tuple) -> Chunk:
        """Convert database row to Chunk model.

        Args:
            row: Database row tuple

        Returns:
            Chunk instance
        """
        if not row:
            raise ValueError("Row is None in _row_to_chunk")

        return Chunk(
            id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            chunk_type=row[3],
            title=row[4],
            content=row[5],
            word_count=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
            created_at=datetime.fromisoformat(row[8]) if row[8] else None
        )
