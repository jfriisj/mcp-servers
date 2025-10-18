# Concrete Code Changes Required

This file shows EXACTLY what code needs to be modified in the existing SLR server.

## File 1: `src/container.py` - Add Validator

Add this import at the top:
```python
from .infrastructure.project_validator import ProjectStructureValidator
```

Add this method to the Container class:
```python
def get_project_validator(self) -> ProjectStructureValidator:
    """Get or create ProjectStructureValidator instance."""
    if not hasattr(self, '_validator'):
        self._validator = ProjectStructureValidator()
    return self._validator
```

---

## File 2: `src/handlers/slr_workflow_handlers.py` - Add Imports

Add these imports:
```python
from pathlib import Path
from ..infrastructure.path_enforcement import (
    enforce_project_path,
    get_enforced_path
)
from ..infrastructure.project_validator import (
    ProjectStructureValidator,
    ProjectArtifactType
)
```

---

## File 3: `src/handlers/slr_workflow_handlers.py` - Modify `handle_create_slr_project`

Find this method and modify it:

**BEFORE:**
```python
async def handle_create_slr_project(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        # ... existing code ...
        
        # Project created successfully
        return CallToolResult(...)
```

**AFTER:**
```python
async def handle_create_slr_project(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        # ... existing code (unchanged) ...
        
        # NEW: Ensure project structure is created
        project = project_repository.get_by_slug(project.slug)
        validator = self.container.get_project_validator()
        validator.create_project_structure(project.slug)
        
        # Project created successfully
        return CallToolResult(...)
```

---

## File 4: `src/handlers/slr_workflow_handlers.py` - Add Decorator to File Methods

For ANY method that creates files, add the `@enforce_project_path` decorator.

### Example 1: Search Strategy Creation

**BEFORE:**
```python
async def handle_create_search_strategy(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        project_name = arguments.get("project_name")
        content = arguments.get("content")
        
        # Save to file
        file_path = Path(f"projects/{project_name}/search_strategy.md")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        
        return CallToolResult(...)
```

**AFTER:**
```python
@enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
async def handle_create_search_strategy(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        content = arguments.get("content")
        corrected_path = arguments["corrected_path"]  # Set by decorator
        
        # Save to file - path is guaranteed correct
        with open(corrected_path, "w") as f:
            f.write(content)
        
        return CallToolResult(...)
```

### Example 2: Screening Decision Recording

**BEFORE:**
```python
async def handle_screen_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        project_id = arguments.get("project_id")
        decision = arguments.get("decision")
        
        # Create file path manually
        import json
        file_path = Path(f"projects/project_{project_id}/screening_decision.json")
        
        with open(file_path, "w") as f:
            json.dump({"decision": decision}, f)
        
        return CallToolResult(...)
```

**AFTER:**
```python
@enforce_project_path(ProjectArtifactType.SCREENING_DECISION)
async def handle_screen_paper(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        decision = arguments.get("decision")
        corrected_path = arguments["corrected_path"]  # Automatically set
        
        # Path is guaranteed correct
        import json
        with open(corrected_path, "w") as f:
            json.dump({"decision": decision}, f)
        
        return CallToolResult(...)
```

### Example 3: Quality Assessment

**BEFORE:**
```python
async def handle_assess_quality(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        project_name = arguments.get("project_name")
        assessment_data = arguments.get("assessment_data")
        
        # Manual path handling
        import json
        path = Path(f"projects/{project_name}/qa_{assessment_data['paper_id']}.json")
        
        with open(path, "w") as f:
            json.dump(assessment_data, f)
        
        return CallToolResult(...)
```

**AFTER:**
```python
@enforce_project_path(ProjectArtifactType.QUALITY_ASSESSMENT)
async def handle_assess_quality(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        assessment_data = arguments.get("assessment_data")
        corrected_path = arguments["corrected_path"]  # Enforced
        
        # Use enforced path
        import json
        with open(corrected_path, "w") as f:
            json.dump(assessment_data, f)
        
        return CallToolResult(...)
```

---

## File 5: Tool Input Schemas - Update Documentation

In `src/server.py`, update tool schemas to document project_name requirement.

For example, in the `upload_paper` tool schema, add:
```python
{
    "name": "upload-paper",
    "description": "Upload research paper to project",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Project name/slug (e.g., 'real-time-translation-platform')"
            },
            "file_path": {
                "type": "string",
                "description": "Path to paper file"
            },
            # ... other properties ...
        },
        "required": ["project_name", "file_path"]  # Add project_name
    }
}
```

---

## File 6: `src/infrastructure/__init__.py` - Export New Classes

Add to exports:
```python
from .project_validator import (
    ProjectStructureValidator,
    ProjectArtifactType,
    validate_and_enforce_path
)
from .path_enforcement import (
    enforce_project_path,
    get_enforced_path,
    PathEnforcementMiddleware
)

__all__ = [
    'ProjectStructureValidator',
    'ProjectArtifactType',
    'validate_and_enforce_path',
    'enforce_project_path',
    'get_enforced_path',
    'PathEnforcementMiddleware',
]
```

---

## Summary of Changes

| File | Change Type | Lines |
|------|------------|-------|
| `src/container.py` | Add method | +10 |
| `src/handlers/slr_workflow_handlers.py` | Add imports | +7 |
| `src/handlers/slr_workflow_handlers.py` | Modify method | +2 |
| `src/handlers/slr_workflow_handlers.py` | Add decorators | +1 per method |
| `src/handlers/slr_workflow_handlers.py` | Update code | Remove manual path creation |
| `src/infrastructure/__init__.py` | Add exports | +15 |
| **NEW** `src/infrastructure/project_validator.py` | New file | 380+ |
| **NEW** `src/infrastructure/path_enforcement.py` | New file | 150+ |

---

## Testing the Changes

After making these changes, test with:

```bash
# Test 1: Verify project structure enforcement
cd slr-server
python -c "
from pathlib import Path
from src.infrastructure.project_validator import (
    ProjectStructureValidator,
    ProjectArtifactType
)

validator = ProjectStructureValidator(Path('projects'))
path = validator.get_correct_path(
    'real-time-translation-platform',
    ProjectArtifactType.SEARCH_STRATEGY,
    'search_strategy.md'
)
print(f'✅ Validator works: {path}')
"

# Test 2: Verify decorator imports
python -c "
from src.infrastructure.path_enforcement import enforce_project_path, get_enforced_path
print('✅ Decorators import successfully')
"

# Test 3: Start server and test
python start_server.py
```

---

## Rollout Plan

1. Create the two new files (validator, enforcement)
2. Add exports to `__init__.py`
3. Add container method
4. Add imports to handlers
5. Update one method with decorator (test)
6. If test passes, apply to all file-writing methods
7. Update tool schemas
8. Run full test suite

---

## Result After Implementation

✅ **100% Path Enforcement** - All files automatically routed to correct location  
✅ **Zero Manual Path Creation** - No more string formatting or Path manipulation  
✅ **Automatic Validation** - Project structure checked before operations  
✅ **Compliance Guaranteed** - PRISMA structure maintained always  
✅ **Single Source of Truth** - ProjectStructureValidator is the only path authority  
✅ **Easy Auditing** - Compliance reports available at any time
