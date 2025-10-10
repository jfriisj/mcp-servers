"""
Bookmark service for business logic orchestration.

This module implements the BookmarkService class following Clean Architecture
Layer 2 principles, orchestrating bookmark lifecycle operations while remaining
framework-agnostic.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.bookmark import Bookmark
from ..repositories.bookmark_repository import BookmarkRepository
from ..repositories.chunk_repository import ChunkRepository
from ..repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class BookmarkService:
    """
    Bookmark business logic service.

    Orchestrates bookmark operations including creation, retrieval, search,
    categorization, and deletion while enforcing business rules and coordinating
    between repositories.

    Follows Clean Architecture Layer 2 principles:
    - Framework-agnostic business logic
    - Depends on abstractions (repositories)
    - Contains reusable business rules
    - Validates input and enforces constraints
    - Coordinates operations across components

    SOLID Principles:
    - SRP: Single responsibility for bookmark business logic
    - OCP: Open for extension via new bookmark types
    - LSP: Can be substituted with other bookmark services
    - ISP: Focused interface for bookmark operations only
    - DIP: Depends on repository abstractions
    """

    # Business rule constants
    MAX_TITLE_LENGTH = 200
    MAX_NOTES_LENGTH = 2000
    MAX_TAGS_PER_BOOKMARK = 10
    MAX_TAG_LENGTH = 50
    DEFAULT_CATEGORIES = [
        "General", "Important", "Research", "References",
        "To Review", "Favorites", "Academic", "Technical"
    ]

    def __init__(
        self,
        bookmark_repository: BookmarkRepository,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository
    ):
        """
        Initialize BookmarkService with required dependencies.

        Args:
            bookmark_repository: Repository for bookmark data access
            document_repository: Repository for document data access
            chunk_repository: Repository for chunk data access
        """
        self.bookmark_repo = bookmark_repository
        self.document_repo = document_repository
        self.chunk_repo = chunk_repository

    def create_document_bookmark(
        self,
        title: str,
        document_id: int,
        category: str = "General",
        **kwargs
    ) -> Bookmark:
        """
        Create a bookmark for a document.

        Args:
            title: Bookmark title
            document_id: ID of document to bookmark
            category: Bookmark category
            **kwargs: Additional bookmark properties

        Returns:
            Created bookmark

        Raises:
            ValueError: If validation fails or document not found
        """
        # Validate business rules
        self._validate_bookmark_data(title, category, kwargs)

        # Verify document exists
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Create bookmark
        bookmark = Bookmark.create_document_bookmark(
            title=title,
            document_id=document_id,
            category=category,
            **kwargs
        )

        # Save to repository
        created_bookmark = self.bookmark_repo.create(bookmark)

        logger.info(
            f"Created document bookmark {created_bookmark.id} for document {document_id}"
        )

        return created_bookmark

    def create_chunk_bookmark(
        self,
        title: str,
        document_id: int,
        chunk_id: int,
        category: str = "General",
        **kwargs
    ) -> Bookmark:
        """
        Create a bookmark for a specific chunk.

        Args:
            title: Bookmark title
            document_id: ID of document containing chunk
            chunk_id: ID of chunk to bookmark
            category: Bookmark category
            **kwargs: Additional bookmark properties

        Returns:
            Created bookmark

        Raises:
            ValueError: If validation fails or chunk not found
        """
        # Validate business rules
        self._validate_bookmark_data(title, category, kwargs)

        # Verify document exists
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Verify chunk exists and belongs to document
        chunk = self.chunk_repo.get_by_id(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        if chunk.document_id != document_id:
            raise ValueError(f"Chunk {chunk_id} does not belong to document {document_id}")

        # Create bookmark
        bookmark = Bookmark.create_chunk_bookmark(
            title=title,
            document_id=document_id,
            chunk_id=chunk_id,
            category=category,
            **kwargs
        )

        # Save to repository
        created_bookmark = self.bookmark_repo.create(bookmark)

        logger.info(
            f"Created chunk bookmark {created_bookmark.id} for chunk {chunk_id}"
        )

        return created_bookmark

    def get_bookmark(self, bookmark_id: int) -> Optional[Bookmark]:
        """
        Retrieve bookmark by ID.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Bookmark if found, None otherwise
        """
        return self.bookmark_repo.get_by_id(bookmark_id)

    def update_bookmark(self, bookmark: Bookmark) -> Bookmark:
        """
        Update existing bookmark.

        Args:
            bookmark: Bookmark with updated data

        Returns:
            Updated bookmark

        Raises:
            ValueError: If validation fails or bookmark not found
        """
        if bookmark.id is None:
            raise ValueError("Cannot update bookmark without ID")

        # Verify bookmark exists
        existing = self.bookmark_repo.get_by_id(bookmark.id)
        if not existing:
            raise ValueError(f"Bookmark {bookmark.id} not found")

        # Validate updated data
        self._validate_bookmark_data(bookmark.title, bookmark.category, {
            "notes": bookmark.notes,
            "tags": bookmark.tags,
            "color": bookmark.color
        })

        # Update in repository
        updated_bookmark = self.bookmark_repo.update(bookmark)

        logger.info(f"Updated bookmark {bookmark.id}: {bookmark.title}")

        return updated_bookmark

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """
        Delete bookmark by ID.

        Args:
            bookmark_id: ID of bookmark to delete

        Returns:
            True if bookmark was deleted, False if not found
        """
        deleted = self.bookmark_repo.delete(bookmark_id)

        if deleted:
            logger.info(f"Deleted bookmark {bookmark_id}")

        return deleted

    def list_bookmarks(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Bookmark]:
        """
        List bookmarks with optional filtering.

        Args:
            filters: Optional filter criteria

        Returns:
            List of matching bookmarks
        """
        return self.bookmark_repo.list_all(filters)

    def get_document_bookmarks(self, document_id: int) -> List[Bookmark]:
        """
        Get all bookmarks for a specific document.

        Args:
            document_id: Document ID

        Returns:
            List of bookmarks for the document
        """
        return self.bookmark_repo.get_by_document_id(document_id)

    def get_bookmarks_by_category(self, category: str) -> List[Bookmark]:
        """
        Get all bookmarks in a specific category.

        Args:
            category: Category name

        Returns:
            List of bookmarks in the category
        """
        return self.bookmark_repo.get_by_category(category)

    def get_favorite_bookmarks(self) -> List[Bookmark]:
        """
        Get all favorite bookmarks.

        Returns:
            List of favorite bookmarks
        """
        return self.bookmark_repo.get_favorites()

    def search_bookmarks(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Bookmark]:
        """
        Search bookmarks by title, notes, or tags.

        Args:
            query: Search query text
            filters: Optional additional filters

        Returns:
            List of matching bookmarks
        """
        if not query.strip():
            return []

        return self.bookmark_repo.search_bookmarks(query, filters)

    def get_categories(self) -> List[str]:
        """
        Get all bookmark categories.

        Returns:
            List of category names including defaults and user-created
        """
        # Get categories from database
        db_categories = set(self.bookmark_repo.get_categories())

        # Combine with default categories
        all_categories = db_categories.union(set(self.DEFAULT_CATEGORIES))

        return sorted(all_categories)

    def add_bookmark_tag(self, bookmark_id: int, tag: str) -> Bookmark:
        """
        Add tag to bookmark.

        Args:
            bookmark_id: Bookmark ID
            tag: Tag to add

        Returns:
            Updated bookmark

        Raises:
            ValueError: If bookmark not found or tag invalid
        """
        bookmark = self.get_bookmark(bookmark_id)
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")

        # Validate tag
        if not tag or not tag.strip():
            raise ValueError("Tag cannot be empty")

        tag = tag.strip()
        if len(tag) > self.MAX_TAG_LENGTH:
            raise ValueError(f"Tag too long (max {self.MAX_TAG_LENGTH} characters)")

        if len(bookmark.tags) >= self.MAX_TAGS_PER_BOOKMARK:
            raise ValueError(f"Maximum {self.MAX_TAGS_PER_BOOKMARK} tags per bookmark")

        # Add tag
        bookmark.add_tag(tag)

        return self.bookmark_repo.update(bookmark)

    def remove_bookmark_tag(self, bookmark_id: int, tag: str) -> Bookmark:
        """
        Remove tag from bookmark.

        Args:
            bookmark_id: Bookmark ID
            tag: Tag to remove

        Returns:
            Updated bookmark

        Raises:
            ValueError: If bookmark not found
        """
        bookmark = self.get_bookmark(bookmark_id)
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")

        # Remove tag
        bookmark.remove_tag(tag)

        return self.bookmark_repo.update(bookmark)

    def set_bookmark_favorite(self, bookmark_id: int, is_favorite: bool) -> Bookmark:
        """
        Set bookmark favorite status.

        Args:
            bookmark_id: Bookmark ID
            is_favorite: Whether bookmark should be favorite

        Returns:
            Updated bookmark

        Raises:
            ValueError: If bookmark not found
        """
        bookmark = self.get_bookmark(bookmark_id)
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")

        # Set favorite status
        bookmark.set_favorite(is_favorite)

        return self.bookmark_repo.update(bookmark)

    def change_bookmark_category(
        self,
        bookmark_id: int,
        category: str
    ) -> Bookmark:
        """
        Change bookmark category.

        Args:
            bookmark_id: Bookmark ID
            category: New category name

        Returns:
            Updated bookmark

        Raises:
            ValueError: If bookmark not found or category invalid
        """
        bookmark = self.get_bookmark(bookmark_id)
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")

        # Validate category
        if not category or not category.strip():
            raise ValueError("Category cannot be empty")

        # Change category
        bookmark.change_category(category)

        return self.bookmark_repo.update(bookmark)

    def get_bookmark_statistics(self) -> Dict[str, Any]:
        """
        Get bookmark statistics and analytics.

        Returns:
            Dictionary containing bookmark statistics
        """
        all_bookmarks = self.list_bookmarks()

        # Category distribution
        category_counts = {}
        for bookmark in all_bookmarks:
            category = bookmark.category
            category_counts[category] = category_counts.get(category, 0) + 1

        # Tag usage
        tag_counts = {}
        for bookmark in all_bookmarks:
            for tag in bookmark.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Date statistics
        now = datetime.now()
        recent_bookmarks = sum(
            1 for b in all_bookmarks
            if b.created_at and (now - b.created_at).days <= 7
        )

        return {
            "total_bookmarks": len(all_bookmarks),
            "favorite_count": len(self.get_favorite_bookmarks()),
            "category_distribution": category_counts,
            "most_used_tags": sorted(
                tag_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "recent_bookmarks": recent_bookmarks,
            "categories": list(category_counts.keys())
        }

    def export_bookmarks(
        self,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export bookmarks in specified format.

        Args:
            format: Export format ("json", "csv")
            filters: Optional filters to apply

        Returns:
            Export data structure
        """
        bookmarks = self.list_bookmarks(filters)

        if format == "json":
            return {
                "export_date": datetime.now().isoformat(),
                "total_bookmarks": len(bookmarks),
                "bookmarks": [bookmark.to_dict() for bookmark in bookmarks]
            }
        elif format == "csv":
            # Return CSV-compatible data structure
            csv_data = []
            for bookmark in bookmarks:
                csv_data.append({
                    "id": bookmark.id,
                    "title": bookmark.title,
                    "document_id": bookmark.document_id,
                    "chunk_id": bookmark.chunk_id,
                    "category": bookmark.category,
                    "notes": bookmark.notes or "",
                    "tags": ",".join(bookmark.tags),
                    "color": bookmark.color,
                    "is_favorite": bookmark.is_favorite,
                    "created_at": bookmark.created_at.isoformat() if bookmark.created_at else ""
                })

            return {
                "export_date": datetime.now().isoformat(),
                "format": "csv",
                "headers": [
                    "id", "title", "document_id", "chunk_id", "category",
                    "notes", "tags", "color", "is_favorite", "created_at"
                ],
                "data": csv_data
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _validate_bookmark_data(
        self,
        title: str,
        category: str,
        additional_data: Dict[str, Any]
    ) -> None:
        """
        Validate bookmark data according to business rules.

        Args:
            title: Bookmark title
            category: Bookmark category
            additional_data: Additional fields to validate

        Raises:
            ValueError: If validation fails
        """
        # Title validation
        if not title or not title.strip():
            raise ValueError("Bookmark title cannot be empty")

        if len(title) > self.MAX_TITLE_LENGTH:
            raise ValueError(f"Title too long (max {self.MAX_TITLE_LENGTH} characters)")

        # Category validation
        if not category or not category.strip():
            raise ValueError("Bookmark category cannot be empty")

        # Notes validation
        notes = additional_data.get("notes")
        if notes and len(notes) > self.MAX_NOTES_LENGTH:
            raise ValueError(f"Notes too long (max {self.MAX_NOTES_LENGTH} characters)")

        # Tags validation
        tags = additional_data.get("tags", [])
        if len(tags) > self.MAX_TAGS_PER_BOOKMARK:
            raise ValueError(f"Maximum {self.MAX_TAGS_PER_BOOKMARK} tags per bookmark")

        for tag in tags:
            if not tag or not tag.strip():
                raise ValueError("Tags cannot be empty")
            if len(tag) > self.MAX_TAG_LENGTH:
                raise ValueError(f"Tag too long (max {self.MAX_TAG_LENGTH} characters)")

        # Color validation (handled by Bookmark model)
        color = additional_data.get("color")
        if color:
            # Create temporary bookmark to validate color
            try:
                Bookmark(
                    title=title,
                    document_id=1,  # Dummy ID for validation
                    category=category,
                    color=color
                )
            except ValueError as e:
                raise ValueError(f"Invalid color format: {e}")
