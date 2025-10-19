# Implementation Checklist - Path Enforcement

## Status: Ready to Implement ✅

All code has been created. This checklist tracks your implementation progress.

---

## ✅ COMPLETED: Infrastructure Created

- [x] `src/infrastructure/project_validator.py` - ProjectStructureValidator class (380+ lines)
- [x] `src/infrastructure/path_enforcement.py` - Decorators & middleware (150+ lines)
- [x] Type hints fixed for Python compatibility
- [x] Export statements prepared
- [x] Documentation created

**Files Ready**:
1. `src/infrastructure/project_validator.py` ✅
2. `src/infrastructure/path_enforcement.py` ✅
3. `SOLUTION_SUMMARY.md` ✅
4. `INTEGRATION_GUIDE.md` ✅
5. `CONCRETE_CODE_CHANGES.md` ✅
6. `PATH_ENFORCEMENT_QUICKSTART.md` ✅

---

## 📋 PENDING: Code Integration

### Step 1: Update Container (2 min)
**File**: `src/container.py`

**Changes needed**:
```python
# Add import
from .infrastructure.project_validator import ProjectStructureValidator

# Add method to Container class
def get_project_validator(self) -> ProjectStructureValidator:
    if not hasattr(self, '_validator'):
        self._validator = ProjectStructureValidator()
    return self._validator
```

- [ ] Add import statement
- [ ] Add method to Container class
- [ ] Syntax check passes

**Verify**:
```bash
python -m py_compile src/container.py
```

---

### Step 2: Update Exports (1 min)
**File**: `src/infrastructure/__init__.py`

**Changes needed**:
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

- [ ] Add all imports
- [ ] Add __all__ exports
- [ ] Syntax check passes

**Verify**:
```bash
python -c "from src.infrastructure import ProjectStructureValidator; print('✅ Exports work')"
```

---

### Step 3: Update Handlers - Imports (3 min)
**File**: `src/handlers/slr_workflow_handlers.py`

**Changes needed** - Add to top of file:
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

- [ ] Add Path import
- [ ] Add enforce_project_path import
- [ ] Add get_enforced_path import
- [ ] Add ProjectStructureValidator import
- [ ] Add ProjectArtifactType import
- [ ] Syntax check passes

**Verify**:
```bash
python -m py_compile src/handlers/slr_workflow_handlers.py
```

---

### Step 4: Update Project Creation (2 min)
**File**: `src/handlers/slr_workflow_handlers.py`

**Method to find**: `handle_create_slr_project()`

**Changes needed** - Add after project creation:
```python
# NEW: Ensure project structure is created
validator = self.container.get_project_validator()
validator.create_project_structure(project.slug)
```

- [ ] Find `handle_create_slr_project()` method
- [ ] Locate where project is created
- [ ] Add validator call after project creation
- [ ] Test that project structure is created

**Verify**:
```bash
# After this change, creating a project should create full directory structure
```

---

### Step 5: Add Decorators to Handlers (30 min)
**File**: `src/handlers/slr_workflow_handlers.py`

**For each file-writing method**:

#### 5.1: Search Strategy Handler
**Original**: `async def handle_create_search_strategy(self, arguments):`

**Change to**: Add decorator above method:
```python
@enforce_project_path(ProjectArtifactType.SEARCH_STRATEGY)
async def handle_create_search_strategy(self, arguments):
```

**Update method body**: Replace manual path creation with:
```python
corrected_path = arguments["corrected_path"]
# Use corrected_path for file operations
with open(corrected_path, "w") as f:
    f.write(content)
```

- [ ] Add @enforce_project_path decorator
- [ ] Use arguments["corrected_path"]
- [ ] Remove manual path string formatting
- [ ] Test method works

#### 5.2: Screening Decision Handler
**Original**: `async def handle_screen_paper(self, arguments):`

**Change to**: 
```python
@enforce_project_path(ProjectArtifactType.SCREENING_DECISION)
async def handle_screen_paper(self, arguments):
    corrected_path = arguments["corrected_path"]
    # ... use corrected_path ...
```

- [ ] Add decorator
- [ ] Update to use corrected_path
- [ ] Test method

#### 5.3: Quality Assessment Handler
**Original**: `async def handle_assess_quality(self, arguments):`

**Change to**:
```python
@enforce_project_path(ProjectArtifactType.QUALITY_ASSESSMENT)
async def handle_assess_quality(self, arguments):
    corrected_path = arguments["corrected_path"]
    # ... use corrected_path ...
```

- [ ] Add decorator
- [ ] Update to use corrected_path
- [ ] Test method

#### 5.4: Data Extraction Handler
**Original**: `async def handle_extract_data(self, arguments):`

**Change to**:
```python
@enforce_project_path(ProjectArtifactType.DATA_EXTRACTION)
async def handle_extract_data(self, arguments):
    corrected_path = arguments["corrected_path"]
```

- [ ] Add decorator
- [ ] Update to use corrected_path
- [ ] Test method

#### 5.5: Synthesis/Analysis Handler
**Original**: `async def handle_synthesize_evidence(self, arguments):`

**Change to**:
```python
@enforce_project_path(ProjectArtifactType.ANALYSIS)
async def handle_synthesize_evidence(self, arguments):
    corrected_path = arguments["corrected_path"]
```

- [ ] Add decorator
- [ ] Update to use corrected_path
- [ ] Test method

#### 5.6: Report Generation Handler
**Original**: `async def handle_generate_slr_report(self, arguments):`

**Change to**:
```python
@enforce_project_path(ProjectArtifactType.REPORT)
async def handle_generate_slr_report(self, arguments):
    corrected_path = arguments["corrected_path"]
```

- [ ] Add decorator
- [ ] Update to use corrected_path
- [ ] Test method

#### 5.7: De-duplication Handler (if exists)
**Original**: `async def handle_detect_remove_duplicates(self, arguments):`

**Change to**:
```python
@enforce_project_path(ProjectArtifactType.DEDUPLICATION)
async def handle_detect_remove_duplicates(self, arguments):
    corrected_path = arguments["corrected_path"]
```

- [ ] Add decorator (if method exists)
- [ ] Update to use corrected_path
- [ ] Test method

---

### Step 6: Update Tool Schemas (5 min)
**File**: `src/server.py` (or wherever tool schemas are defined)

**For each tool that writes files**, add/update input schema:

**Example** - For `create-search-strategy`:
```python
"inputSchema": {
    "type": "object",
    "properties": {
        "project_name": {
            "type": "string",
            "description": "Project name/slug (e.g., 'real-time-translation-platform')"
        },
        "filename": {
            "type": "string",
            "description": "Output filename"
        },
        # ... other properties ...
    },
    "required": ["project_name", "filename"]  # Add to required list
}
```

- [ ] Update schema for each file-writing tool
- [ ] Add project_name to required parameters
- [ ] Add filename/file_path to required parameters
- [ ] Update descriptions

---

## 🧪 TESTING

### Test 1: Validator Import & Instantiation
```bash
python -c "
from src.infrastructure.project_validator import ProjectStructureValidator
v = ProjectStructureValidator()
print('✅ Validator instantiates')
"
```
- [ ] Passes

### Test 2: Path Enforcement
```bash
python -c "
from pathlib import Path
from src.infrastructure.project_validator import ProjectStructureValidator, ProjectArtifactType
v = ProjectStructureValidator(Path('projects'))
path = v.get_correct_path('real-time-translation-platform', ProjectArtifactType.SEARCH_STRATEGY, 'search_strategy.md')
assert 'search-strategies' in str(path)
print(f'✅ Path enforcement works: {path}')
"
```
- [ ] Passes

### Test 3: Decorator Imports
```bash
python -c "
from src.infrastructure.path_enforcement import enforce_project_path, get_enforced_path
print('✅ Decorators import')
"
```
- [ ] Passes

### Test 4: Server Startup
```bash
cd c:\github\mcp-servers\slr-server
python start_server.py
# Should start without errors
```
- [ ] Server starts
- [ ] No import errors
- [ ] MCP server ready

### Test 5: Project Creation
Create a project via MCP tool:
```
create_slr_project(
    project_name="test-enforcement",
    description="Test project"
)
```

Verify structure created:
```bash
ls -R projects/test-enforcement/
# Should show all subdirectories:
# - search-strategies/
# - papers/
# - screening/
#   - title_abstract/
#   - full_text/
#   - final_selection/
# - quality-assessment/
#   - PRISMA/
#   - CASP/
#   - JBI/
# - data-extraction/
# - analysis/
# - deduplication/
# - reports/
```
- [ ] All directories created
- [ ] Structure is correct

### Test 6: File Creation Enforcement
Create a search strategy:
```
create_search_strategy(
    project_name="test-enforcement",
    filename="search_strategy.md",
    content="# Test Strategy"
)
```

Verify file location:
```bash
# File should be at:
# projects/test-enforcement/search-strategies/search_strategy.md
ls projects/test-enforcement/search-strategies/
```
- [ ] File in correct location
- [ ] Not in root directory
- [ ] Not in wrong subdirectory

### Test 7: Compliance Report
```bash
python -c "
from src.infrastructure.project_validator import ProjectStructureValidator
v = ProjectStructureValidator()
report = v.generate_compliance_report('test-enforcement')
print(report)
# Should show: COMPLIANT
"
```
- [ ] Report shows COMPLIANT
- [ ] No violations listed

---

## 📊 Implementation Progress

| Phase | Task | Status | Time |
|-------|------|--------|------|
| 1 | Create validator & enforcement | ✅ Done | 2h |
| 2 | Update container | 📋 Pending | 2m |
| 3 | Update exports | 📋 Pending | 1m |
| 4 | Add handler imports | 📋 Pending | 3m |
| 5 | Update project creation | 📋 Pending | 2m |
| 6 | Add decorators to handlers | 📋 Pending | 30m |
| 7 | Update tool schemas | 📋 Pending | 5m |
| 8 | Run tests | 📋 Pending | 10m |
| **Total** | | | **~1 hour** |

---

## 🎯 Next Action

1. **Start with Step 1**: Update `src/container.py`
2. **Run syntax check**: `python -m py_compile src/container.py`
3. **Move to Step 2**: Update exports
4. **Continue sequentially** through steps
5. **Run tests** after each step
6. **Verify** with Test 6 (File Creation Enforcement)

---

## Success Criteria

After completing all steps:

✅ All syntax checks pass  
✅ Server starts without errors  
✅ Project structure auto-created  
✅ Files always saved to correct location  
✅ Compliance reports show 100% compliance  
✅ All tests pass  
✅ No files in root directory  
✅ No manual path creation in code  

---

## Support Files

- `SOLUTION_SUMMARY.md` - Overview of solution
- `INTEGRATION_GUIDE.md` - How to integrate
- `CONCRETE_CODE_CHANGES.md` - Exact code diffs
- `PATH_ENFORCEMENT_QUICKSTART.md` - Quick reference
- `src/infrastructure/project_validator.py` - Implementation
- `src/infrastructure/path_enforcement.py` - Decorators

---

## Questions During Implementation?

1. Check `CONCRETE_CODE_CHANGES.md` for exact code
2. Check `INTEGRATION_GUIDE.md` for approaches
3. Check `PATH_ENFORCEMENT_QUICKSTART.md` for quick ref
4. Review docstrings in validator.py and enforcement.py

**You've got this! 💪**
