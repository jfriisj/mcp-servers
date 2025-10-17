"""
Repository for SLR project data access and management.

Implements data persistence operations for SLR projects with research framework
metadata, team management, and project statistics tracking.

SOLID Score Target: 80/100+
Clean Architecture Layer 3: Interface Adapters
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..domain.models import SLRProject
from .base_repository import (
    BaseRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)


class ProjectRepository(BaseRepository[SLRProject]):
    """
    Repository for SLR project data access and management.

    This repository handles persistence operations for SLR projects including:
    - Project metadata and research framework (PICO/SPIDER)
    - Team member management
    - Project statistics tracking
    - Status and phase management
    - Project-specific queries (by name, by status, etc.)

    Follows Repository pattern with proper error handling and transaction support.
    SOLID Principles:
    - SRP: Only handles project data persistence
    - OCP: Extensible through BaseRepository
    - LSP: Can substitute any BaseRepository[SLRProject]
    - ISP: Focused interface for project operations
    - DIP: Depends on DatabaseConnection abstraction
    """

    def create(self, project: SLRProject) -> SLRProject:
        """
        Create a new SLR project in the database.

        Args:
            project: SLRProject instance to create

        Returns:
            Created project with populated ID and timestamps

        Raises:
            RepositoryError: If creation fails
            DuplicateEntityError: If project with same name exists
        """
        try:
            # Check for duplicate project name
            existing = self.get_by_name(project.name)
            if existing:
                raise DuplicateEntityError("SLRProject", f"name={project.name}")

            # Ensure timestamps are set
            if project.created_date is None:
                project.created_date = datetime.now(timezone.utc)
            if project.updated_date is None:
                project.updated_date = datetime.now(timezone.utc)

            # Execute INSERT
            cursor = self.db.execute(
                """
                INSERT INTO slr_projects (
                    name, display_name, description,
                    research_questions, population, intervention, comparison, outcome,
                    folder_path, project_file_path, project_file_type,
                    created_date, updated_date,
                    current_phase, status,
                    total_papers, papers_screening, papers_included, 
                    papers_excluded, papers_quality_assessed,
                    created_by, team_members,
                    settings, tags, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.name,
                    project.display_name,
                    project.description,
                    json.dumps(project.research_questions),
                    project.population,
                    project.intervention,
                    project.comparison,
                    project.outcome,
                    project.folder_path,
                    project.project_file_path,
                    project.project_file_type,
                    project.created_date.isoformat(),
                    project.updated_date.isoformat(),
                    project.current_phase,
                    project.status,
                    project.total_papers,
                    project.papers_screening,
                    project.papers_included,
                    project.papers_excluded,
                    project.papers_quality_assessed,
                    project.created_by,
                    json.dumps(project.team_members),
                    json.dumps(project.settings) if project.settings else None,
                    json.dumps(project.tags),
                    project.notes,
                ),
            )

            # Get the generated ID
            project.id = cursor.lastrowid
            self.db.commit()

            return project

        except DuplicateEntityError:
            raise
        except Exception as e:
            raise RepositoryError(
                f"Failed to create project: {str(e)}", original_error=e
            )

    def get_by_id(self, project_id: int) -> Optional[SLRProject]:
        """
        Retrieve a project by its ID.

        Args:
            project_id: Primary key of the project

        Returns:
            The project if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.execute(
                """
                SELECT id, name, display_name, description,
                       research_questions, population, intervention, comparison, outcome,
                       folder_path, project_file_path, project_file_type,
                       created_date, updated_date,
                       current_phase, status,
                       total_papers, papers_screening, papers_included,
                       papers_excluded, papers_quality_assessed,
                       created_by, team_members,
                       settings, tags, notes
                FROM slr_projects
                WHERE id = ?
                """,
                (project_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None

        except Exception as e:
            raise RepositoryError(
                f"Failed to retrieve project {project_id}: {str(e)}", original_error=e
            )

    def get_by_name(self, name: str) -> Optional[SLRProject]:
        """
        Retrieve a project by its name (slug).

        Args:
            name: Project name in slug format (e.g., "software-designs")

        Returns:
            The project if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        try:
            cursor = self.db.execute(
                """
                SELECT id, name, display_name, description,
                       research_questions, population, intervention, comparison, outcome,
                       folder_path, project_file_path, project_file_type,
                       created_date, updated_date,
                       current_phase, status,
                       total_papers, papers_screening, papers_included,
                       papers_excluded, papers_quality_assessed,
                       created_by, team_members,
                       settings, tags, notes
                FROM slr_projects
                WHERE name = ?
                """,
                (name,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None

        except Exception as e:
            raise RepositoryError(
                f"Failed to retrieve project by name '{name}': {str(e)}",
                original_error=e,
            )

    def update(self, project: SLRProject) -> SLRProject:
        """
        Update an existing project in the database.

        Args:
            project: The project instance with updated data

        Returns:
            The updated project

        Raises:
            RepositoryError: If update fails
            EntityNotFoundError: If project not found
        """
        try:
            if project.id is None:
                raise ValueError("Cannot update project without ID")

            # Update the updated_date timestamp
            project.updated_date = datetime.now(timezone.utc)

            cursor = self.db.execute(
                """
                UPDATE slr_projects SET
                    name = ?,
                    display_name = ?,
                    description = ?,
                    research_questions = ?,
                    population = ?,
                    intervention = ?,
                    comparison = ?,
                    outcome = ?,
                    folder_path = ?,
                    project_file_path = ?,
                    project_file_type = ?,
                    updated_date = ?,
                    current_phase = ?,
                    status = ?,
                    total_papers = ?,
                    papers_screening = ?,
                    papers_included = ?,
                    papers_excluded = ?,
                    papers_quality_assessed = ?,
                    created_by = ?,
                    team_members = ?,
                    settings = ?,
                    tags = ?,
                    notes = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.display_name,
                    project.description,
                    json.dumps(project.research_questions),
                    project.population,
                    project.intervention,
                    project.comparison,
                    project.outcome,
                    project.folder_path,
                    project.project_file_path,
                    project.project_file_type,
                    project.updated_date.isoformat(),
                    project.current_phase,
                    project.status,
                    project.total_papers,
                    project.papers_screening,
                    project.papers_included,
                    project.papers_excluded,
                    project.papers_quality_assessed,
                    project.created_by,
                    json.dumps(project.team_members),
                    json.dumps(project.settings) if project.settings else None,
                    json.dumps(project.tags),
                    project.notes,
                    project.id,
                ),
            )

            if cursor.rowcount == 0:
                raise EntityNotFoundError("SLRProject", project.id)

            self.db.commit()
            return project

        except EntityNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(
                f"Failed to update project {project.id}: {str(e)}", original_error=e
            )

    def delete(self, project_id: int) -> bool:
        """
        Delete a project from the database.

        Args:
            project_id: Primary key of the project to delete

        Returns:
            True if project was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails

        Note:
            This will also affect related papers due to foreign key constraints.
            Consider soft delete (status='archived') instead.
        """
        try:
            cursor = self.db.execute(
                "DELETE FROM slr_projects WHERE id = ?", (project_id,)
            )

            deleted = cursor.rowcount > 0
            if deleted:
                self.db.commit()

            return deleted

        except Exception as e:
            raise RepositoryError(
                f"Failed to delete project {project_id}: {str(e)}", original_error=e
            )

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[SLRProject]:
        """
        List all projects with optional filtering.

        Args:
            filters: Optional dictionary of filter criteria
                    Supported filters: status, current_phase, created_by

        Returns:
            List of projects matching the filters

        Raises:
            RepositoryError: If query fails
        """
        try:
            query = """
                SELECT id, name, display_name, description,
                       research_questions, population, intervention, comparison, outcome,
                       folder_path, project_file_path, project_file_type,
                       created_date, updated_date,
                       current_phase, status,
                       total_papers, papers_screening, papers_included,
                       papers_excluded, papers_quality_assessed,
                       created_by, team_members,
                       settings, tags, notes
                FROM slr_projects
            """

            where_clause, parameters = self._build_where_clause(filters)
            if where_clause:
                query += f" {where_clause}"

            query += " ORDER BY created_date DESC"

            cursor = self.db.execute(query, tuple(parameters))
            rows = cursor.fetchall()

            return [self._row_to_project(row) for row in rows]

        except Exception as e:
            raise RepositoryError(
                f"Failed to list projects: {str(e)}", original_error=e
            )

    def list_active(self) -> List[SLRProject]:
        """
        List all active projects.

        Returns:
            List of projects with status='active'

        Raises:
            RepositoryError: If query fails
        """
        return self.list_all(filters={"status": "active"})

    def list_by_phase(self, phase: str) -> List[SLRProject]:
        """
        List all projects in a specific phase.

        Args:
            phase: Project phase (planning, search, screening, etc.)

        Returns:
            List of projects in the specified phase

        Raises:
            RepositoryError: If query fails
        """
        return self.list_all(filters={"current_phase": phase})

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count projects matching optional filters.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            Number of projects matching the filters

        Raises:
            RepositoryError: If query fails
        """
        try:
            query = "SELECT COUNT(*) FROM slr_projects"

            where_clause, parameters = self._build_where_clause(filters)
            if where_clause:
                query += f" {where_clause}"

            cursor = self.db.execute(query, tuple(parameters))
            result = cursor.fetchone()

            return result[0] if result else 0

        except Exception as e:
            raise RepositoryError(
                f"Failed to count projects: {str(e)}", original_error=e
            )

    def _row_to_project(self, row: tuple) -> SLRProject:
        """
        Convert database row to SLRProject domain model.

        Args:
            row: Database row tuple

        Returns:
            SLRProject instance

        Raises:
            RepositoryError: If conversion fails
        """
        try:
            return SLRProject(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                research_questions=json.loads(row[4]) if row[4] else [],
                population=row[5],
                intervention=row[6],
                comparison=row[7],
                outcome=row[8],
                folder_path=row[9],
                project_file_path=row[10],
                project_file_type=row[11],
                created_date=datetime.fromisoformat(row[12]),
                updated_date=datetime.fromisoformat(row[13]),
                current_phase=row[14],
                status=row[15],
                total_papers=row[16],
                papers_screening=row[17],
                papers_included=row[18],
                papers_excluded=row[19],
                papers_quality_assessed=row[20],
                created_by=row[21],
                team_members=json.loads(row[22]) if row[22] else [],
                settings=json.loads(row[23]) if row[23] else None,
                tags=json.loads(row[24]) if row[24] else [],
                notes=row[25] or "",
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to convert database row to SLRProject: {str(e)}",
                original_error=e,
            )
