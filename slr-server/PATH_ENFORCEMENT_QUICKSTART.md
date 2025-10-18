# Path Enforcement Implementation - Quick Start

## What Was Created

### 1. **ProjectStructureValidator** (`src/infrastructure/project_validator.py`)
- Validates project structure exists
- Determines correct subdirectory for any artifact type
- Enforces paths automatically
- Generates compliance reports
- **Key Method**: `validate_and_enforce_path(project_name, artifact_type, filename)`

### 2. **PathEnforcement Decorators** (`src/infrastructure/path_enforcement.py`)
- `@enforce_project_path(artifact_type)` - Automatic path correction decorator
- `get_enforced_path()` - Simple function to get correct path
- `PathEnforcementMiddleware` - For middleware integration

## Implementation Steps (5 min setup)

### Step 1: Update Container
Add to `src/container.py`:

```python
from .infrastructure.project_validator import ProjectStructureValidator

# In Container class:
def get_project_validator(self) -> ProjectStructureValidator:
    if not hasattr(self, '_validator'):
        self._validator = ProjectStructureValidator()
    return self._validator
```

### Step 2: Import in Handlers
Add to `src/handlers/slr_workflow_handlers.py`:

```python
from ..infrastructure.path_enforcement import enforce_project_path, get_enforced_path
from ..infrastructure.project_validator import ProjectArtifactType
```

### Step 3: Add Decorator to File-Writing Methods
Example for search strategy creation:

```python
@enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
async def handle_create_search_strategy(self, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        corrected_path = arguments["corrected_path"]  # Set by decorator
        
        # Use corrected_path for file operations
        content = arguments.get("content", "")
        with open(corrected_path, "w") as f:
            f.write(content)
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"✅ File saved at: {corrected_path}"
            )]
        )
    except Exception as e:
        # ... error handling ...
```

### Step 4: Modify Project Creation
In `handle_create_slr_project()`, add structure creation:

```python
async def handle_create_slr_project(self, arguments):
    # ... existing code ...
    
    # After project creation, ensure structure exists
    validator = self.container.get_project_validator()
    validator.create_project_structure(project.slug)
    
    # ... rest of method ...
```

## Methods to Implement For

1. **Search Strategy**
   - Type: `ProjectArtifactType.SEARCH_STRATEGY`
   - Files: `search_strategy.md`, `search_queries.txt`, `search_log.csv`

2. **Screening**
   - Type: `ProjectArtifactType.SCREENING_DECISION`
   - Files: `screening_decisions.json`, `screening_log.csv`

3. **Quality Assessment**
   - Type: `ProjectArtifactType.QUALITY_ASSESSMENT`
   - Files: `quality_assessment.json`, `prisma_*.csv`

4. **Data Extraction**
   - Type: `ProjectArtifactType.DATA_EXTRACTION`
   - Files: `extraction_form.json`, `extracted_data.csv`

5. **Analysis**
   - Type: `ProjectArtifactType.ANALYSIS`
   - Files: `synthesis_*.json`, `citation_network.json`

6. **De-duplication**
   - Type: `ProjectArtifactType.DEDUPLICATION`
   - Files: `dedup_log.txt`, `duplicates.json`

7. **Reports**
   - Type: `ProjectArtifactType.REPORT`
   - Files: `slr_report.md`, `slr_report.pdf`

## Verification Commands

```bash
# Check validator works
python -c "
from src.infrastructure.project_validator import ProjectStructureValidator, ProjectArtifactType
v = ProjectStructureValidator(Path('projects'))
path = v.get_correct_path(
    'real-time-translation-platform',
    ProjectArtifactType.SEARCH_STRATEGY,
    'search_strategy.md'
)
print('✅ Correct path:', path)
"

# Generate compliance report
python -c "
from src.infrastructure.project_validator import ProjectStructureValidator
v = ProjectStructureValidator()
report = v.generate_compliance_report('real-time-translation-platform')
print(report)
"
```

## Expected Behavior After Implementation

### ✅ Correct Usage
```python
# Handler receives this from user:
arguments = {
    "project_name": "real-time-translation-platform",
    "filename": "search_strategy.md",
    "content": "..."
}

# Decorator automatically:
# 1. Validates project exists
# 2. Determines: projects/real-time-translation-platform/search-strategies/
# 3. Creates parent dirs if needed
# 4. Adds to arguments: corrected_path = Path(...)
# 5. Handler uses corrected_path

# Result: ✅ File saved to correct location
```

### ❌ Prevented: Root-level Files
```python
# Old problem: Files saved to slr-server/search_strategy.md

# New behavior: 
# 1. Decorator validates project
# 2. Determines correct path
# 3. Creates parent directories automatically
# 4. FORCES file to correct location

# Result: ✅ File ALWAYS in projects/{project}/search-strategies/
```

## Compliance Guarantees

After implementation, you get:

1. **100% Path Enforcement** - All file operations routed to correct subdirectory
2. **Automatic Structure Creation** - Project directories auto-created
3. **Audit Trail** - All path decisions logged
4. **Compliance Reports** - Verify structure at any time
5. **Project Isolation** - No cross-project contamination
6. **Error Prevention** - Invalid paths rejected immediately

## Testing

```python
# Test 1: Validate enforcement works
from pathlib import Path
from src.infrastructure.project_validator import (
    ProjectStructureValidator, 
    ProjectArtifactType
)

validator = ProjectStructureValidator(Path("projects"))

# Should enforce correct path
path = validator.enforce_path(
    "real-time-translation-platform",
    ProjectArtifactType.SEARCH_STRATEGY,
    "search_strategy.md",
    create_dirs=False  # Don't create in test
)

assert str(path).endswith("search-strategies/search_strategy.md")
print("✅ Path enforcement works!")

# Test 2: Validate compliance report
report = validator.generate_compliance_report("real-time-translation-platform")
assert "COMPLIANT" in report or "VIOLATION" in report
print("✅ Compliance reporting works!")
```

## One-Line Summary

**What You Get**: Automatic, enforced path routing for ALL project files - no more manual organization needed, 100% PRISMA-compliant structure guaranteed.
