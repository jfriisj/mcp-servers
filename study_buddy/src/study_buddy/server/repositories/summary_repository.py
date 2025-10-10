"""Summary repository implementation with relationship management.

Provides summary-specific data access operations including
chunk and document relationships with cascade operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.connection import DatabaseConnection
from ..models.summary import Summary

from ..repositories.base_repository import (
    BaseRepository,
    EntityNotFoundError,
    RepositoryError,
)


class SummaryRepository(BaseRepository[Summary]):
    """Repository for summary data access operations.

    Provides CRUD operations for Summary entities with relationship
    management to Document and Chunk entities.

    Follows Clean Architecture Layer 3 principles:
    - No business logic (only data access)
    - Manages foreign key relationships properly
    - Handles cascade operations for cleanup
    - Transforms between database rows and domain models

    Features:
    - Full CRUD operations for summaries
    - Document and chunk relationship queries
    - Summary type and level filtering
    - Proper foreign key constraint handling
    """

    def __init__(self, db: DatabaseConnection):
        """Initialize repository with database connection.

        Args:
            db: Database connection for executing queries
        """
        super().__init__(db)

    def create(self, summary: Summary) -> Summary:
        """Create a new summary in the database.

        Args:
            summary: Summary entity to create

        Returns:
            Created summary with populated ID and timestamps

        Raises:
            RepositoryError: If creation fails

        Note:
            Validates that document_id and chunk_id (if provided) reference existing entities.
        """
        try:
            cursor = self.db.cursor()

            # Ensure timestamps are set
            now = datetime.now()
            if not summary.generation_date:
                summary.generation_date = now

            # Validate document exists (if document_id is provided)
            if summary.document_id is not None:
                cursor.execute("SELECT 1 FROM documents WHERE id = ?", (summary.document_id,))
                if not cursor.fetchone():
                    raise RepositoryError(f"Document {summary.document_id} not found")

            # Validate chunk exists (if chunk_id is provided)
            if summary.chunk_id:
                cursor.execute("SELECT 1 FROM chunks WHERE id = ?", (summary.chunk_id,))
                if not cursor.fetchone():
                    raise RepositoryError(f"Chunk {summary.chunk_id} not found")

            # Insert summary  
            import json
            metadata_json = json.dumps(summary.metadata) if summary.metadata else "{}"
            
            cursor.execute("""
                INSERT INTO summaries (
                    document_id, chunk_id, summary_type,
                    summary_content, model_name, generation_date, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                summary.document_id,
                summary.chunk_id,
                summary.summary_type,
                summary.summary_content,
                summary.model_name,
                summary.generation_date.isoformat() if summary.generation_date else None,
                metadata_json
            ))

            # Get the generated ID
            summary.id = cursor.lastrowid

            self.db.commit()
            return summary

        except Exception as e:
            self.db.rollback()
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to create summary: {str(e)}", e)

    def get_by_id(self, summary_id: int) -> Optional[Summary]:
        """Retrieve a summary by ID.

        Args:
            summary_id: Primary key of the summary

        Returns:
            Summary if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT
                    id, document_id, chunk_id, summary_type,
                    summary_content, model_name, generation_date, metadata
                FROM summaries
                WHERE id = ?
            """, (summary_id,))

            row = cursor.fetchone()
            return self._row_to_summary(row) if row else None

        except Exception as e:
            raise RepositoryError(f"Failed to get summary {summary_id}: {str(e)}", e)

    def update(self, summary: Summary) -> Summary:
        """Update an existing summary.

        Args:
            summary: Summary with updated data (must have valid ID)

        Returns:
            Updated summary

        Raises:
            EntityNotFoundError: If summary with ID doesn't exist
            RepositoryError: If update fails
        """
        try:
            if not summary.id:
                raise ValueError("Summary must have an ID for update")

            cursor = self.db.cursor()

            # Update summary
            cursor.execute("""
                UPDATE summaries SET
                    document_id = ?, chunk_id = ?, summary_type = ?,
                    summary_content = ?, model_name = ?
                WHERE id = ?
            """, (
                summary.document_id,
                summary.chunk_id,
                summary.summary_type,
                summary.summary_content,
                summary.model_name,
                summary.id
            ))

            if cursor.rowcount == 0:
                raise EntityNotFoundError("Summary", summary.id)

            self.db.commit()
            return summary

        except EntityNotFoundError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to update summary {summary.id}: {str(e)}", e)

    def delete(self, summary_id: int) -> bool:
        """Delete a summary from the database.

        Args:
            summary_id: Primary key of summary to delete

        Returns:
            True if summary was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete summary
            cursor.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))

            deleted = cursor.rowcount > 0
            self.db.commit()
            return deleted

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete summary {summary_id}: {str(e)}", e)

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Summary]:
        """List all summaries with optional filtering.

        Args:
            filters: Optional filter criteria:
                - document_id: Filter by document ID
                - chunk_id: Filter by chunk ID (use None for document-level summaries)
                - summary_type: Filter by summary type
                - summary_level: Filter by summary level
                - model_name: Filter by AI model name
                - limit: Maximum number of results
                - offset: Number of results to skip

        Returns:
            List of summaries matching filters

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.cursor()

            # Build base query
            query = """
                SELECT
                    id, document_id, chunk_id, summary_type,
                    summary_content, model_name, generation_date, metadata
                FROM summaries
            """

            params = []
            conditions = []

            if filters:
                # Document ID filter
                if "document_id" in filters:
                    conditions.append("document_id = ?")
                    params.append(filters["document_id"])

                # Chunk ID filter (handle NULL for document-level summaries)
                if "chunk_id" in filters:
                    conditions.append("chunk_id = ?")
                    params.append(filters["chunk_id"])
                elif "chunk_id_is_null" in filters and filters["chunk_id_is_null"]:
                    conditions.append("chunk_id IS NULL")

                # Summary type filter
                if "summary_type" in filters:
                    conditions.append("summary_type = ?")
                    params.append(filters["summary_type"])



                # Model name filter
                if "model_name" in filters:
                    conditions.append("model_name = ?")
                    params.append(filters["model_name"])

            # Add WHERE clause if we have conditions
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Add ordering (most recent first)
            query += " ORDER BY generation_date DESC"

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

            return [self._row_to_summary(row) for row in rows]

        except Exception as e:
            raise RepositoryError(f"Failed to list summaries: {str(e)}", e)

    def get_by_document_id(self, document_id: int, chunk_id: Optional[int] = None) -> List[Summary]:
        """Get all summaries for a document or specific chunk.

        Args:
            document_id: ID of the document
            chunk_id: ID of the chunk (None for document-level summaries)

        Returns:
            List of summaries for the document/chunk
        """
        filters: Dict[str, Any] = {"document_id": document_id}
        if chunk_id is not None:
            filters["chunk_id"] = chunk_id
        else:
            # For document-level summaries, chunk_id should be NULL in database
            filters["chunk_id_is_null"] = True

        return self.list_all(filters)

    def get_by_chunk_id(self, chunk_id: int) -> List[Summary]:
        """Get all summaries for a specific chunk.

        Args:
            chunk_id: ID of the chunk

        Returns:
            List of summaries for the chunk
        """
        return self.list_all({"chunk_id": chunk_id})

    def delete_by_document_id(self, document_id: int) -> int:
        """Delete all summaries for a document (cascade operation).

        Args:
            document_id: ID of the document

        Returns:
            Number of summaries deleted

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete all summaries for the document
            cursor.execute("DELETE FROM summaries WHERE document_id = ?", (document_id,))

            deleted_count = cursor.rowcount
            self.db.commit()
            return deleted_count

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete summaries for document {document_id}: {str(e)}", e)

    def delete_by_chunk_id(self, chunk_id: int) -> int:
        """Delete all summaries for a chunk (cascade operation).

        Args:
            chunk_id: ID of the chunk

        Returns:
            Number of summaries deleted

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            cursor = self.db.cursor()

            # Delete all summaries for the chunk
            cursor.execute("DELETE FROM summaries WHERE chunk_id = ?", (chunk_id,))

            deleted_count = cursor.rowcount
            self.db.commit()
            return deleted_count

        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete summaries for chunk {chunk_id}: {str(e)}", e)

    def get_summary_by_type(
        self,
        document_id: int,
        summary_type: str,
        chunk_id: Optional[int] = None
    ) -> Optional[Summary]:
        """Get a specific summary by type for a document or chunk.

        Args:
            document_id: ID of the document
            summary_type: Type of summary to retrieve
            chunk_id: ID of the chunk (None for document-level)

        Returns:
            Summary if found, None otherwise
        """
        filters = {
            "document_id": document_id,
            "summary_type": summary_type,
            "chunk_id": chunk_id,
            "limit": 1
        }

        summaries = self.list_all(filters)
        return summaries[0] if summaries else None

    def count_by_document_id(self, document_id: int) -> int:
        """Count summaries for a specific document.

        Args:
            document_id: ID of the document

        Returns:
            Number of summaries for the document
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM summaries WHERE document_id = ?",
                (document_id,)
            )
            return cursor.fetchone()[0]

        except Exception as e:
            raise RepositoryError(f"Failed to count summaries for document {document_id}: {str(e)}", e)

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count summaries matching filters (optimized implementation).

        Args:
            filters: Optional filter criteria

        Returns:
            Number of summaries matching filters
        """
        try:
            cursor = self.db.cursor()
            query = "SELECT COUNT(*) FROM summaries"
            params = []
            conditions = []

            if filters:
                if "document_id" in filters:
                    conditions.append("document_id = ?")
                    params.append(filters["document_id"])

                if "chunk_id" in filters:
                    if filters["chunk_id"] is None:
                        conditions.append("chunk_id IS NULL")
                    else:
                        conditions.append("chunk_id = ?")
                        params.append(filters["chunk_id"])

                if "summary_type" in filters:
                    conditions.append("summary_type = ?")
                    params.append(filters["summary_type"])

                if "summary_level" in filters:
                    conditions.append("summary_level = ?")
                    params.append(filters["summary_level"])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

        except Exception as e:
            raise RepositoryError(f"Failed to count summaries: {str(e)}", e)

    def get_summary_for_document_and_type(
        self,
        document_id: int,
        summary_type: str
    ) -> Optional[Summary]:
        """Get summary for document by type.

        Args:
            document_id: Document ID to get summary for
            summary_type: Type of summary ("brief", "standard", "detailed", "custom")

        Returns:
            Summary if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        filters = {
            'document_id': document_id,
            'chunk_id': None,  # Document-level summaries only
            'summary_type': summary_type
        }
        results = self.list_all(filters)
        return results[0] if results else None

    def get_summary_for_chunk_and_type(
        self,
        chunk_id: int,
        summary_type: str
    ) -> Optional[Summary]:
        """Get summary for chunk by type.

        Args:
            chunk_id: Chunk ID to get summary for
            summary_type: Type of summary ("brief", "standard", "detailed", "custom")

        Returns:
            Summary if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        filters = {
            'chunk_id': chunk_id,
            'summary_type': summary_type
        }
        results = self.list_all(filters)
        return results[0] if results else None

    def exists(self, summary_id: int) -> bool:
        """Check if summary exists by ID (optimized implementation).

        Args:
            summary_id: Summary ID to check

        Returns:
            True if summary exists
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT 1 FROM summaries WHERE id = ? LIMIT 1",
                (summary_id,)
            )
            return cursor.fetchone() is not None

        except Exception as e:
            raise RepositoryError(f"Failed to check summary existence: {str(e)}", e)

    def _row_to_summary(self, row: tuple) -> Summary:
        """Convert database row to Summary model.

        Args:
            row: Database row tuple

        Returns:
            Summary instance
        """
        if not row:
            raise ValueError("Row is None in _row_to_summary")

        import json
        
        # Parse metadata JSON if present
        metadata = {}
        if len(row) > 7 and row[7]:
            try:
                metadata = json.loads(row[7])
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        return Summary(
            id=row[0],
            document_id=row[1],
            chunk_id=row[2],
            summary_type=row[3],
            summary_content=row[4],
            model_name=row[5],
            generation_date=datetime.fromisoformat(row[6]) if row[6] else None,
            metadata=metadata
        )
