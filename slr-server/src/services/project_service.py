"""
Service for SLR project creation and management.

Implements project initialization from description files (PDF/Markdown),
folder structure creation, and metadata extraction following PRISMA guidelines.

SOLID Score Target: 80/100+
Clean Architecture Layer 2: Application Services (Use Cases)
"""

import re
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from ..domain.models import SLRProject, ProjectStatus, ProjectPhase
from ..repositories.project_repository import ProjectRepository
from ..repositories.base_repository import DuplicateEntityError


logger = logging.getLogger(__name__)


class ProjectServiceError(Exception):
    """Base exception for project service errors."""


class ProjectService:
    """
    Application service for SLR project creation and management.

    This service orchestrates project creation from description files,
    handles metadata extraction, and initializes project folder structures.

    Follows SOLID principles:
    - SRP: Only handles project creation orchestration
    - OCP: Extensible through new file parsers
    - LSP: Service can be substituted
    - ISP: Focused interface for project operations
    - DIP: Depends on ProjectRepository abstraction

    Orchestration Pattern (Phase 3 refactoring):
    Each public method delegates to focused private helper methods,
    making the code testable, maintainable, and following SRP.
    """

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize ProjectService with repository dependency.

        Args:
            project_repository: Repository for project persistence
        """
        self.project_repository = project_repository
        self.logger = logger.getChild(self.__class__.__name__)

    def create_project_from_file(
        self,
        project_name: str,
        file_path: str,
        description: str,
        extract_metadata: bool = True,
    ) -> SLRProject:
        """
        Create SLR project from description file (PDF or Markdown).

        Orchestration pattern (7 steps):
        1. Validate inputs (name, file)
        2. Detect file type
        3. Extract metadata (if enabled)
        4. Build project entity
        5. Initialize folders
        6. Create templates
        7. Persist to database

        Args:
            project_name: Project name in slug format (e.g., "software-designs")
            file_path: Path to project description file (.pdf or .md)
            description: Project description (used if extraction fails)
            extract_metadata: Whether to extract metadata from file

        Returns:
            Created SLRProject instance

        Raises:
            ProjectServiceError: If creation fails
            DuplicateEntityError: If project name already exists
        """
        try:
            self.logger.info(
                f"Creating project '{project_name}' from file: {file_path}"
            )

            # Step 1: Validate inputs
            self._validate_project_name(project_name)
            self._validate_file_exists(file_path)

            # Step 2: Detect file type
            file_type = self._detect_file_type(file_path)
            self.logger.info(f"Detected file type: {file_type}")

            # Step 3: Extract metadata
            metadata = {}
            if extract_metadata:
                metadata = self._extract_project_metadata(file_path, file_type)
                self.logger.info(f"Extracted metadata: {list(metadata.keys())}")

            # Step 4: Build project entity
            project = self._build_project_entity(
                project_name, file_path, file_type, metadata, description
            )

            # Step 5: Initialize folder structure
            self._initialize_project_folders(project)

            # Step 6: Create template files
            self._create_project_templates(project)

            # Step 7: Persist to database
            created_project = self.project_repository.create(project)
            self.logger.info(
                f"Project created successfully with ID: {created_project.id}"
            )

            return created_project

        except (DuplicateEntityError, ProjectServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to create project: {str(e)}", exc_info=True)
            raise ProjectServiceError(f"Failed to create project: {str(e)}") from e

    def create_project_manual(
        self,
        project_name: str,
        display_name: str,
        description: str,
        research_questions: Optional[List[str]] = None,
        **kwargs,
    ) -> SLRProject:
        """
        Create SLR project manually without file parsing.

        Args:
            project_name: Project name in slug format
            display_name: Human-readable project name
            description: Project description
            research_questions: Optional list of research questions
            **kwargs: Additional SLRProject fields (population, intervention, etc.)

        Returns:
            Created SLRProject instance

        Raises:
            ProjectServiceError: If creation fails
            DuplicateEntityError: If project name already exists
        """
        try:
            self.logger.info(f"Creating project '{project_name}' manually")

            # Validate project name
            self._validate_project_name(project_name)

            # Build project entity
            project = SLRProject(
                name=project_name,
                display_name=display_name,
                description=description,
                research_questions=research_questions or [],
                folder_path=f"projects/{project_name}",
                created_date=datetime.now(timezone.utc),
                updated_date=datetime.now(timezone.utc),
                current_phase=ProjectPhase.PLANNING.value,
                status=ProjectStatus.ACTIVE.value,
                **kwargs,
            )

            # Initialize folders and templates
            self._initialize_project_folders(project)
            self._create_project_templates(project)

            # Persist
            created_project = self.project_repository.create(project)
            self.logger.info(f"Project created manually with ID: {created_project.id}")

            return created_project

        except (DuplicateEntityError, ProjectServiceError):
            raise
        except Exception as e:
            self.logger.error(
                f"Failed to create project manually: {str(e)}", exc_info=True
            )
            raise ProjectServiceError(f"Failed to create project: {str(e)}") from e

    # ==================== Validation Methods ====================

    def _validate_project_name(self, name: str) -> None:
        """
        Validate project name follows slug format.

        Args:
            name: Project name to validate

        Raises:
            ProjectServiceError: If name is invalid
        """
        if not name or not name.strip():
            raise ProjectServiceError("Project name cannot be empty")

        # Must be lowercase, alphanumeric with hyphens
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name):
            raise ProjectServiceError(
                "Project name must be in slug format: lowercase alphanumeric with hyphens "
                "(e.g., 'software-designs', 'cloud-security')"
            )

    def _validate_file_exists(self, file_path: str) -> None:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to file

        Raises:
            ProjectServiceError: If file doesn't exist or isn't readable
        """
        path = Path(file_path)
        if not path.exists():
            raise ProjectServiceError(f"File not found: {file_path}")
        if not path.is_file():
            raise ProjectServiceError(f"Path is not a file: {file_path}")

    # ==================== File Type Detection ====================

    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from extension.

        Args:
            file_path: Path to file

        Returns:
            File type: "pdf" or "markdown"

        Raises:
            ProjectServiceError: If file type is unsupported
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        else:
            raise ProjectServiceError(
                f"Unsupported file type: {ext}. "
                f"Supported formats: .pdf, .md, .markdown"
            )

    # ==================== Metadata Extraction ====================

    def _extract_project_metadata(
        self, file_path: str, file_type: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from project description file.

        Orchestrates extraction based on file type.

        Args:
            file_path: Path to file
            file_type: File type ("pdf" or "markdown")

        Returns:
            Dictionary of extracted metadata

        Raises:
            ProjectServiceError: If extraction fails
        """
        try:
            if file_type == "pdf":
                return self._extract_from_pdf(file_path)
            elif file_type == "markdown":
                return self._extract_from_markdown(file_path)
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Metadata extraction failed: {str(e)}")
            return {}  # Non-fatal: return empty dict

    def _extract_from_markdown(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from Markdown file.

        Supports two formats:
        1. YAML frontmatter (preferred):
           ---
           title: "Project Title"
           research_questions:
             - "RQ1: ..."
             - "RQ2: ..."
           pico:
             population: "..."
             intervention: "..."
           ---

        2. Markdown structure:
           # Title
           ## Research Questions
           - RQ1: ...
           - RQ2: ...

        Args:
            file_path: Path to Markdown file

        Returns:
            Dictionary with extracted metadata
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            metadata: dict[str, Any] = {}

            # Try YAML frontmatter first
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if frontmatter_match:
                try:
                    import yaml

                    yaml_data = yaml.safe_load(frontmatter_match.group(1))
                    if isinstance(yaml_data, dict):
                        metadata = yaml_data
                        self.logger.info("Extracted metadata from YAML frontmatter")
                except Exception as e:
                    self.logger.warning(f"Failed to parse YAML frontmatter: {e}")

            # Extract from markdown structure if needed
            if not metadata.get("title"):
                title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if title_match:
                    metadata["title"] = title_match.group(1).strip()
                    self.logger.info(f"Extracted title: {metadata['title']}")

            if not metadata.get("research_questions"):
                metadata["research_questions"] = (
                    self._extract_research_questions_from_text(content)
                )

            # Extract PICO if present in YAML
            if "pico" in metadata:
                pico = metadata.pop("pico")
                if isinstance(pico, dict):
                    metadata.update(
                        {
                            "population": pico.get("population"),
                            "intervention": pico.get("intervention"),
                            "comparison": pico.get("comparison"),
                            "outcome": pico.get("outcome"),
                        }
                    )

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to extract from Markdown: {e}", exc_info=True)
            return {}

    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.

        Uses PDF parsing to extract:
        - Title (from first page or metadata)
        - Research questions (pattern matching: RQ1, RQ2, etc.)
        - PICO components (if structured sections exist)

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with extracted metadata

        Note:
            This is a stub for Phase 2. Will be implemented after
            Markdown parsing is working and tested.
        """
        try:
            # TODO: Implement PDF extraction
            # Will use pdfplumber or PyPDF2
            # For now, return empty dict
            self.logger.warning("PDF extraction not yet implemented")
            return {}

        except Exception as e:
            self.logger.error(f"Failed to extract from PDF: {e}", exc_info=True)
            return {}

    def _extract_research_questions_from_text(self, text: str) -> List[str]:
        """
        Extract research questions from text using pattern matching.

        Looks for patterns:
        - RQ1: ...
        - Research Question 1: ...
        - List items under "Research Questions" heading

        Args:
            text: Text to search

        Returns:
            List of research questions
        """
        questions = []

        # Look for "Research Questions" section
        rq_section = re.search(
            r"##?\s+Research Questions.*?\n(.*?)(?=\n##?|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if rq_section:
            section_text = rq_section.group(1)

            # Extract numbered RQ patterns
            rq_patterns = re.findall(
                r"[-*]\s*(RQ\d+:?\s*.+?)(?=\n|$)", section_text, re.IGNORECASE
            )
            if rq_patterns:
                questions.extend([q.strip() for q in rq_patterns])
            else:
                # Try without list markers
                rq_patterns = re.findall(
                    r"(RQ\d+:?\s*.+?)(?=\n|$)", section_text, re.IGNORECASE
                )
                questions.extend([q.strip() for q in rq_patterns])

        self.logger.info(f"Extracted {len(questions)} research questions")
        return questions

    # ==================== Project Entity Construction ====================

    def _build_project_entity(
        self,
        name: str,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any],
        fallback_description: str,
    ) -> SLRProject:
        """
        Build SLRProject entity from extracted metadata.

        Args:
            name: Project name (slug)
            file_path: Path to project file
            file_type: File type ("pdf" or "markdown")
            metadata: Extracted metadata dictionary
            fallback_description: Description to use if extraction failed

        Returns:
            SLRProject instance
        """
        display_name = metadata.get("title", name.replace("-", " ").title())
        description = metadata.get("description", fallback_description)

        project = SLRProject(
            name=name,
            display_name=display_name,
            description=description,
            research_questions=metadata.get("research_questions", []),
            population=metadata.get("population"),
            intervention=metadata.get("intervention"),
            comparison=metadata.get("comparison"),
            outcome=metadata.get("outcome"),
            folder_path=f"projects/{name}",
            project_file_path=file_path,
            project_file_type=file_type,
            created_date=datetime.now(timezone.utc),
            updated_date=datetime.now(timezone.utc),
            current_phase=ProjectPhase.PLANNING.value,
            status=ProjectStatus.ACTIVE.value,
            team_members=metadata.get("team_members", []),
            tags=metadata.get("tags", []),
            notes=metadata.get("notes", ""),
        )

        return project

    # ==================== Folder and Template Management ====================

    def _initialize_project_folders(self, project: SLRProject) -> None:
        """
        Create standard SLR folder structure for project.

        Creates folders following PRISMA methodology:
        - papers/screening, papers/included, papers/excluded
        - search-strategies
        - screening/title-abstract, screening/full-text
        - quality-assessment/results
        - data-extraction/extracted
        - analysis/visualizations
        - deduplication
        - reports

        Args:
            project: Project instance
        """
        try:
            base_path = Path(project.folder_path)

            folders = [
                "papers/screening",
                "papers/included",
                "papers/excluded",
                "papers/bibliography",
                "search-strategies",
                "screening/title-abstract",
                "screening/full-text",
                "quality-assessment/results",
                "data-extraction/extracted",
                "analysis/visualizations",
                "deduplication",
                "reports/progress-reports",
            ]

            for folder in folders:
                folder_path = base_path / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created folder: {folder_path}")

            self.logger.info(f"Initialized project folders at: {base_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize folders: {e}", exc_info=True)
            raise ProjectServiceError(f"Failed to create project folders: {e}") from e

    def _create_project_templates(self, project: SLRProject) -> None:
        """
        Create template files in project folders.

        Creates:
        - project.json: Project metadata
        - research-questions.md: Extracted research questions
        - README.md: Project overview

        Args:
            project: Project instance

        Note:
            Template system can be extended to support custom templates.
        """
        try:
            base_path = Path(project.folder_path)

            # Create project.json metadata file
            import json

            project_json = base_path / "project.json"
            project_json.write_text(
                json.dumps(
                    {
                        "name": project.name,
                        "display_name": project.display_name,
                        "description": project.description,
                        "research_questions": project.research_questions,
                        "created_date": (
                            project.created_date.isoformat()
                            if project.created_date
                            else None
                        ),
                        "status": project.status,
                        "phase": project.current_phase,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Create research-questions.md if questions exist
            if project.research_questions:
                rq_file = base_path / "research-questions.md"
                rq_content = f"# Research Questions - {project.display_name}\n\n"
                for rq in project.research_questions:
                    rq_content += f"- {rq}\n"
                rq_file.write_text(rq_content, encoding="utf-8")

            # Create README.md
            readme = base_path / "README.md"
            created_date_str = (
                project.created_date.strftime("%Y-%m-%d")
                if project.created_date
                else "Unknown"
            )
            readme_content = f"""# {project.display_name}

{project.description}

## Project Information

- **Status**: {project.status}
- **Current Phase**: {project.current_phase}
- **Created**: {created_date_str}

## Research Questions

{chr(10).join(f'- {rq}' for rq in project.research_questions) if project.research_questions else 'No research questions defined yet.'}

## Folder Structure

- `papers/`: Research papers organized by screening status
- `search-strategies/`: Database search queries and results
- `screening/`: Screening process documentation
- `quality-assessment/`: Quality assessment results
- `data-extraction/`: Extracted data from papers
- `analysis/`: Analysis and synthesis results
- `reports/`: Progress and final reports
"""
            readme.write_text(readme_content, encoding="utf-8")

            self.logger.info("Created project template files")

        except Exception as e:
            self.logger.warning(f"Failed to create templates: {e}")
            # Non-fatal: templates are nice-to-have
