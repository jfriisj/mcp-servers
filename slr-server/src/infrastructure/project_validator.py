"""
Project Structure Validator for SLR Server.

Enforces strict adherence to project folder structure guidelines
and ensures all project artifacts are placed in correct locations.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ProjectArtifactType(Enum):
    """Valid artifact types for SLR projects."""
    SEARCH_STRATEGY = "search-strategies"
    PAPER = "papers"
    SCREENING_DECISION = "screening"
    QUALITY_ASSESSMENT = "quality-assessment"
    DATA_EXTRACTION = "data-extraction"
    ANALYSIS = "analysis"
    DEDUPLICATION = "deduplication"
    REPORT = "reports"


class ProjectStructureValidator:
    """
    Validates and enforces project structure guidelines.
    
    This validator ensures:
    1. All project artifacts follow the SLR project structure
    2. Files are placed in correct subdirectories
    3. Project isolation is maintained
    4. PRISMA compliance for organization
    """
    
    # Base directories that must exist in every SLR project
    REQUIRED_SUBDIRECTORIES = [
        "search-strategies",
        "papers",
        "screening",
        "quality-assessment",
        "data-extraction",
        "analysis",
        "deduplication",
        "reports"
    ]
    
    # File type mappings to required subdirectories
    ARTIFACT_ROUTING = {
        # Search strategy files
        "search_strategy.md": "search-strategies",
        "search_query*.txt": "search-strategies",
        "search_log*.csv": "search-strategies",
        
        # Paper files
        "*.pdf": "papers",
        "*.docx": "papers",
        
        # Screening files
        "screening_decisions*.json": "screening",
        "screening_log*.csv": "screening",
        "title_abstract_screening*.json": "screening/title_abstract",
        "full_text_screening*.json": "screening/full_text",
        "final_selection*.json": "screening/final_selection",
        
        # Quality assessment
        "quality_assessment*.json": "quality-assessment",
        "prisma_*.csv": "quality-assessment",
        "casp_*.csv": "quality-assessment",
        "jbi_*.csv": "quality-assessment",
        
        # Data extraction
        "extraction_form*.json": "data-extraction",
        "extracted_data*.csv": "data-extraction",
        
        # Analysis
        "synthesis_*.json": "analysis",
        "citation_network*.json": "analysis",
        "thematic_analysis*.json": "analysis",
        
        # De-duplication
        "dedup_log*.txt": "deduplication",
        "duplicates_*.json": "deduplication",
        
        # Reports
        "slr_report*.md": "reports",
        "slr_report*.pdf": "reports",
        "slr_report*.docx": "reports",
    }
    
    def __init__(self, projects_root: Optional[Path] = None):
        """
        Initialize validator.
        
        Args:
            projects_root: Root path containing all projects (e.g., projects/)
        """
        self.projects_root = projects_root or Path("projects")
    
    def validate_project_exists(self, project_name: str) -> Tuple[bool, str]:
        """
        Validate that a project exists and has correct structure.
        
        Args:
            project_name: Project name/slug (e.g., 'real-time-translation-platform')
            
        Returns:
            Tuple of (is_valid, message)
        """
        project_path = self.projects_root / project_name
        
        if not project_path.exists():
            return False, f"Project '{project_name}' does not exist at {project_path}"
        
        if not project_path.is_dir():
            return False, f"Project path exists but is not a directory: {project_path}"
        
        # Check for required subdirectories
        missing_dirs = []
        for subdir in self.REQUIRED_SUBDIRECTORIES:
            subdir_path = project_path / subdir
            if not subdir_path.exists():
                missing_dirs.append(subdir)
        
        if missing_dirs:
            return False, (
                f"Project '{project_name}' is missing required subdirectories: "
                f"{', '.join(missing_dirs)}"
            )
        
        return True, f"Project '{project_name}' structure is valid"
    
    def get_correct_path(
        self, 
        project_name: str, 
        artifact_type: ProjectArtifactType,
        filename: Optional[str] = None
    ) -> Path:
        """
        Get the correct path for an artifact based on its type.
        
        Args:
            project_name: Project name/slug
            artifact_type: Type of artifact (from ProjectArtifactType enum)
            filename: Optional filename to append
            
        Returns:
            Correct path for the artifact
            
        Example:
            >>> validator = ProjectStructureValidator()
            >>> path = validator.get_correct_path(
            ...     "real-time-translation-platform",
            ...     ProjectArtifactType.SEARCH_STRATEGY,
            ...     "search_strategy.md"
            ... )
            >>> print(path)
            projects/real-time-translation-platform/search-strategies/search_strategy.md
        """
        project_path = self.projects_root / project_name
        correct_subdir = artifact_type.value
        
        correct_path = project_path / correct_subdir
        if filename:
            correct_path = correct_path / filename
        
        return correct_path
    
    def validate_file_path(
        self, 
        project_name: str, 
        artifact_type: ProjectArtifactType,
        proposed_path: Path
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Validate if a file is being placed in the correct location.
        
        Args:
            project_name: Project name/slug
            artifact_type: Type of artifact
            proposed_path: Proposed path for the file
            
        Returns:
            Tuple of (is_valid, message, correct_path)
        """
        correct_path = self.get_correct_path(
            project_name, 
            artifact_type,
            proposed_path.name
        )
        
        if proposed_path == correct_path:
            return True, f"✅ File path is correct", None
        
        return (
            False,
            f"❌ File should be at: {correct_path}\n"
            f"   Currently proposed: {proposed_path}",
            correct_path
        )
    
    def infer_artifact_type(self, filename: str) -> Optional[ProjectArtifactType]:
        """
        Infer artifact type from filename.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            Inferred ProjectArtifactType or None
        """
        filename_lower = filename.lower()
        
        if "search" in filename_lower:
            return ProjectArtifactType.SEARCH_STRATEGY
        elif "screening" in filename_lower:
            return ProjectArtifactType.SCREENING_DECISION
        elif "quality" in filename_lower or "prisma" in filename_lower or "casp" in filename_lower:
            return ProjectArtifactType.QUALITY_ASSESSMENT
        elif "extraction" in filename_lower or "extract" in filename_lower:
            return ProjectArtifactType.DATA_EXTRACTION
        elif "analysis" in filename_lower or "synthesis" in filename_lower or "citation" in filename_lower:
            return ProjectArtifactType.ANALYSIS
        elif "dedup" in filename_lower or "duplicate" in filename_lower:
            return ProjectArtifactType.DEDUPLICATION
        elif "report" in filename_lower:
            return ProjectArtifactType.REPORT
        elif filename_lower.endswith(".pdf") or filename_lower.endswith(".docx"):
            return ProjectArtifactType.PAPER
        
        return None
    
    def enforce_path(
        self,
        project_name: str,
        artifact_type: ProjectArtifactType,
        filename: str,
        create_dirs: bool = True
    ) -> Path:
        """
        Enforce correct path and create directories if needed.
        
        Args:
            project_name: Project name
            artifact_type: Type of artifact
            filename: Filename to place
            create_dirs: Whether to create directories if they don't exist
            
        Returns:
            The enforced path (guaranteed to be correct)
            
        Raises:
            ValueError: If project doesn't exist
        """
        # Validate project exists
        is_valid, message = self.validate_project_exists(project_name)
        if not is_valid:
            raise ValueError(message)
        
        # Get correct path
        correct_path = self.get_correct_path(project_name, artifact_type, filename)
        
        # Create directories if requested
        if create_dirs:
            correct_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enforced path for {filename}: {correct_path}")
        return correct_path
    
    def create_project_structure(self, project_name: str, projects_root: Optional[Path] = None) -> bool:
        """
        Create complete project directory structure.
        
        Args:
            project_name: Project name/slug
            projects_root: Optional override for projects root path
            
        Returns:
            True if successful
        """
        root = projects_root or self.projects_root
        project_path = root / project_name
        
        try:
            # Create main project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create all required subdirectories
            for subdir in self.REQUIRED_SUBDIRECTORIES:
                subdir_path = project_path / subdir
                subdir_path.mkdir(exist_ok=True)
                logger.info(f"Created directory: {subdir_path}")
            
            # Create screening subdirectories
            for screening_stage in ["title_abstract", "full_text", "final_selection"]:
                stage_path = project_path / "screening" / screening_stage
                stage_path.mkdir(exist_ok=True)
            
            # Create quality assessment subdirectories
            for framework in ["PRISMA", "CASP", "JBI"]:
                qa_path = project_path / "quality-assessment" / framework
                qa_path.mkdir(exist_ok=True)
            
            logger.info(f"Project structure created for '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            return False
    
    def list_violations(self, project_name: str) -> List[str]:
        """
        List any structure violations in a project.
        
        Args:
            project_name: Project name to check
            
        Returns:
            List of violation messages
        """
        project_path = self.projects_root / project_name
        violations = []
        
        # Check for files in root of project (should not exist)
        if project_path.exists():
            for item in project_path.iterdir():
                if item.is_file() and item.name not in ["project.json", "README.md", ".gitkeep"]:
                    violations.append(
                        f"❌ File '{item.name}' found in project root - "
                        f"should be in appropriate subdirectory"
                    )
        
        return violations
    
    def generate_compliance_report(self, project_name: str) -> str:
        """
        Generate compliance report for a project.
        
        Args:
            project_name: Project name to report on
            
        Returns:
            Formatted compliance report
        """
        is_valid, message = self.validate_project_exists(project_name)
        violations = self.list_violations(project_name)
        
        report = f"📋 Project Compliance Report: {project_name}\n"
        report += f"{'='*60}\n\n"
        
        report += f"Status: {'✅ COMPLIANT' if is_valid and not violations else '❌ NON-COMPLIANT'}\n"
        report += f"Message: {message}\n\n"
        
        if violations:
            report += "Violations Found:\n"
            for violation in violations:
                report += f"  {violation}\n"
        else:
            report += "✅ No violations found\n"
        
        return report


# Utility functions for easy use in handlers

def get_project_validator() -> ProjectStructureValidator:
    """Get or create a project validator instance."""
    return ProjectStructureValidator(Path("projects"))


def validate_and_enforce_path(
    project_name: str,
    artifact_type: ProjectArtifactType,
    filename: str
) -> Path:
    """
    Validate and enforce correct path for a project artifact.
    
    This is the main function to use when creating project files.
    
    Args:
        project_name: Project name (slug format)
        artifact_type: Type of artifact being created
        filename: Filename for the artifact
        
    Returns:
        The correct path to use for the file
        
    Raises:
        ValueError: If project doesn't exist or path cannot be enforced
        
    Example:
        >>> path = validate_and_enforce_path(
        ...     "real-time-translation-platform",
        ...     ProjectArtifactType.SEARCH_STRATEGY,
        ...     "search_strategy.md"
        ... )
        >>> # path is now correct: projects/real-time-translation-platform/search-strategies/search_strategy.md
    """
    validator = get_project_validator()
    return validator.enforce_path(project_name, artifact_type, filename, create_dirs=True)
