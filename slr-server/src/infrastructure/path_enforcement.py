"""
Path Enforcement Decorator for SLR MCP Handlers.

Automatically enforces correct project structure for all file operations.
Provides decorator-based path validation and correction.
"""

import logging
from functools import wraps
from pathlib import Path
from typing import Callable, Any, Dict, Optional

from ..infrastructure.project_validator import (
    ProjectStructureValidator,
    ProjectArtifactType,
    validate_and_enforce_path
)

logger = logging.getLogger(__name__)


def enforce_project_path(artifact_type: ProjectArtifactType):
    """
    Decorator to enforce correct project path for handler methods.
    
    Automatically validates and corrects file paths based on project structure.
    
    Usage:
        @enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
        async def handle_create_search_strategy(self, arguments: Dict[str, Any]):
            # 'corrected_path' will be available in arguments
            ...
    
    Args:
        artifact_type: Type of artifact being created
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, arguments: Dict[str, Any]) -> Any:
            try:
                # Extract project name and filename from arguments
                project_name = arguments.get("project_name")
                project_id = arguments.get("project_id")
                filename = arguments.get("filename")
                file_path = arguments.get("file_path")
                
                # Get project name from repository if not provided
                if not project_name and project_id:
                    project_repository = self.container.get_project_repository()
                    project = project_repository.get_by_id(project_id)
                    project_name = project.slug
                
                if not project_name:
                    logger.error("Project name/ID not provided in arguments")
                    raise ValueError("project_name or project_id required")
                
                # Determine filename from file_path or use provided filename
                target_filename = filename or Path(file_path).name if file_path else None
                
                if not target_filename:
                    logger.error("Filename could not be determined")
                    raise ValueError("filename or file_path required")
                
                # Enforce correct path
                corrected_path = validate_and_enforce_path(
                    project_name,
                    artifact_type,
                    target_filename
                )
                
                # Add corrected path to arguments
                arguments["corrected_path"] = corrected_path
                
                logger.info(
                    f"Path enforcement: {artifact_type.value}/{target_filename} "
                    f"-> {corrected_path}"
                )
                
                # Call original handler
                return await func(self, arguments)
                
            except ValueError as e:
                logger.error(f"Path enforcement error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in path enforcement: {e}")
                raise
        
        return wrapper
    return decorator


def validate_project_structure(func: Callable) -> Callable:
    """
    Decorator to validate project structure before operations.
    
    Usage:
        @validate_project_structure
        async def handle_operation(self, arguments):
            ...
    """
    @wraps(func)
    async def wrapper(self, arguments: Dict[str, Any]) -> Any:
        try:
            project_name = arguments.get("project_name")
            project_id = arguments.get("project_id")
            
            if not project_name and project_id:
                project_repository = self.container.get_project_repository()
                project = project_repository.get_by_id(project_id)
                project_name = project.slug
            
            if not project_name:
                raise ValueError("project_name or project_id required")
            
            # Validate project structure
            validator = ProjectStructureValidator()
            is_valid, message = validator.validate_project_exists(project_name)
            
            if not is_valid:
                logger.error(f"Project structure validation failed: {message}")
                raise ValueError(message)
            
            logger.info(f"Project structure valid: {project_name}")
            return await func(self, arguments)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            raise
    
    return wrapper


class PathEnforcementMiddleware:
    """
    Middleware for enforcing path constraints in handler calls.
    
    Can be inserted into the MCP server request pipeline.
    """
    
    def __init__(self, validator: Optional[ProjectStructureValidator] = None):
        self.validator = validator or ProjectStructureValidator()
    
    def enforce_on_handler(
        self,
        project_name: str,
        artifact_type: ProjectArtifactType,
        filename: str
    ) -> Path:
        """
        Enforce path for a handler operation.
        
        Args:
            project_name: Project name
            artifact_type: Type of artifact
            filename: Target filename
            
        Returns:
            Corrected path
        """
        return self.validator.enforce_path(project_name, artifact_type, filename)
    
    def get_compliance_report(self, project_name: str) -> str:
        """Get compliance report for project."""
        return self.validator.generate_compliance_report(project_name)


# Helper function for use in handlers

def get_enforced_path(
    project_name: str,
    artifact_type: ProjectArtifactType,
    filename: str
) -> Path:
    """
    Get enforced path for project artifact.
    
    This is the main function handlers should call before creating files.
    
    Args:
        project_name: Project name/slug
        artifact_type: Type of artifact
        filename: Filename for artifact
        
    Returns:
        Correct, enforced path for the file
        
    Example:
        # In handler:
        path = get_enforced_path(
            "real-time-translation-platform",
            ProjectArtifactType.SEARCH_STRATEGY,
            "search_strategy.md"
        )
        # Now guaranteed to be correct path
    """
    return validate_and_enforce_path(project_name, artifact_type, filename)
