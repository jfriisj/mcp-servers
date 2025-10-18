"""
Integration Guide: How to Add Path Enforcement to SLR Handlers

This file shows how to integrate the ProjectStructureValidator and 
PathEnforcement middleware into existing handlers to ensure 100% compliance.
"""

# OPTION 1: Using the Decorator Approach
# ========================================

from pathlib import Path
from typing import Any, Dict
from mcp.types import CallToolResult, TextContent

from ..infrastructure.path_enforcement import enforce_project_path
from ..infrastructure.project_validator import ProjectArtifactType


# Example handler with path enforcement decorator:
class EnforcedSLRHandler:
    """Example handler showing path enforcement integration."""
    
    def __init__(self, container):
        self.container = container
    
    @enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
    async def handle_create_search_strategy(
        self, 
        arguments: Dict[str, Any]
    ) -> CallToolResult:
        """
        Create search strategy with enforced path.
        
        Arguments MUST include:
        - project_name (or project_id)
        - filename (or file_path)
        
        The decorator will:
        1. Validate project exists
        2. Determine correct subdirectory
        3. Add 'corrected_path' to arguments
        4. Create parent directories if needed
        """
        try:
            corrected_path = arguments["corrected_path"]  # Set by decorator
            filename = Path(corrected_path).name
            
            # Now use corrected_path for file creation
            search_strategy_content = arguments.get("content", "")
            
            with open(corrected_path, "w") as f:
                f.write(search_strategy_content)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"✅ Search strategy created at: {corrected_path}"
                )]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )],
                isError=True
            )


# OPTION 2: Using Manual Enforcement in Handler
# ==============================================

from ..infrastructure.path_enforcement import get_enforced_path


class ManualEnforcementHandler:
    """Example handler with manual path enforcement."""
    
    def __init__(self, container):
        self.container = container
    
    async def handle_create_screening_decision(
        self,
        arguments: Dict[str, Any]
    ) -> CallToolResult:
        """
        Create screening decision with manual path enforcement.
        
        The handler explicitly enforces the path before using it.
        """
        try:
            project_name = arguments["project_name"]
            
            # Enforce correct path before any file operation
            screening_decision_path = get_enforced_path(
                project_name,
                ProjectArtifactType.SCREENING_DECISION,
                "screening_decisions.json"
            )
            
            # Now we're guaranteed the path is correct
            screening_data = arguments.get("screening_data", {})
            
            # Use screening_decision_path for operations
            import json
            with open(screening_decision_path, "w") as f:
                json.dump(screening_data, f, indent=2)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"✅ Screening decisions saved at: {screening_decision_path}"
                )]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )],
                isError=True
            )


# OPTION 3: Using Validator Directly in Service
# ==============================================

from ..infrastructure.project_validator import ProjectStructureValidator


class ValidatedService:
    """Example service with direct validator usage."""
    
    def __init__(self):
        self.validator = ProjectStructureValidator()
    
    def save_quality_assessment(
        self,
        project_name: str,
        assessment_data: Dict[str, Any]
    ) -> Path:
        """
        Save quality assessment with path validation.
        
        The service validates and enforces correct paths automatically.
        """
        # Enforce correct path
        qa_path = self.validator.enforce_path(
            project_name,
            ProjectArtifactType.QUALITY_ASSESSMENT,
            "quality_assessment.json",
            create_dirs=True
        )
        
        # Save using enforced path
        import json
        with open(qa_path, "w") as f:
            json.dump(assessment_data, f, indent=2)
        
        return qa_path


# INTEGRATION CHECKLIST
# ====================

"""
To add 100% path enforcement to the SLR server:

1. MODIFY EXISTING HANDLERS:
   □ Import PathEnforcement decorators/utils
   □ Add @enforce_project_path decorator to file-creation methods
   □ OR use get_enforced_path() before file operations
   □ Verify paths are used from arguments["corrected_path"]

2. MODIFY SERVICES:
   □ Import ProjectStructureValidator
   □ Create instance in __init__
   □ Use validator.enforce_path() before ALL file operations
   □ Use validator.validate_project_exists() at method start

3. ADD TO CONTAINER:
   □ Register ProjectStructureValidator as singleton
   □ Make available to handlers and services

4. UPDATE TOOL DEFINITIONS:
   □ Document that project_name and filename/file_path are required
   □ Add to input schemas

5. TESTING:
   □ Test path enforcement with correct paths → should succeed
   □ Test with incorrect paths → should be auto-corrected
   □ Test with missing project → should raise clear error
   □ Verify compliance reports are accurate

6. LOGGING:
   □ All path enforcements are logged
   □ Check logs for verification of correct routing
"""


# IMPLEMENTATION STEPS FOR SLRHANDLER
# ===================================

"""
Step 1: Add imports to handlers/slr_workflow_handlers.py:

    from ..infrastructure.path_enforcement import (
        enforce_project_path,
        get_enforced_path
    )
    from ..infrastructure.project_validator import ProjectArtifactType

Step 2: Modify handle_create_slr_project() to create validator:

    async def handle_create_slr_project(self, arguments):
        # ... existing code ...
        
        # Create validator and enforce structure
        from ..infrastructure.project_validator import ProjectStructureValidator
        validator = ProjectStructureValidator()
        validator.create_project_structure(project.slug)
        
        # ... rest of method ...

Step 3: Add decorators to all file-writing handlers:

    @enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
    async def handle_create_search_strategy(self, arguments):
        ...
    
    @enforce_project_path(ProjectArtifactType.SCREENING_DECISION)
    async def handle_screen_paper(self, arguments):
        ...
    
    @enforce_project_path(ProjectArtifactType.QUALITY_ASSESSMENT)
    async def handle_assess_quality(self, arguments):
        ...

Step 4: Add to container.py:

    from .infrastructure.project_validator import ProjectStructureValidator
    
    def get_project_validator(self) -> ProjectStructureValidator:
        if not hasattr(self, '_validator'):
            self._validator = ProjectStructureValidator()
        return self._validator

Step 5: Update tests to verify enforcement
"""
