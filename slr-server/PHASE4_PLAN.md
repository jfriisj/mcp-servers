# Phase 4: SOLID Refactoring - Execution Plan

**Created:** October 19, 2025  
**Goal:** Fix remaining 88 MyPy errors focusing on dependency injection and type safety  
**Target:** <20 MyPy errors (75% improvement)

---

## Error Categorization

### Current State: 88 Errors Across 16 Files

**Breakdown by Category:**

1. **DatabaseConnection Type Mismatch (5 errors)** - PRIORITY 1
   - container.py:110, 116, 140 - PaperRepository, ChunkRepository, ProjectRepository
   - research_question_repository.py:19 (2 errors)
   - Issue: Two different `DatabaseConnection` classes (database.connection vs base_repository)

2. **Abstract Repository Instantiation (2 errors)** - PRIORITY 1  
   - container.py:128 - ResearchQuestionRepository (abstract methods)
   - container.py:134 - HypothesisRepository (abstract methods)
   - Issue: Trying to instantiate abstract base classes

3. **Service Constructor Mismatches (2 errors)** - PRIORITY 1
   - container.py:162 - ResearchQuestionService doesn't accept `question_repository`
   - container.py:170 - HypothesisAnalysisService doesn't accept `hypothesis_repository`
   - Issue: Services not designed for dependency injection

4. **QualityAssessment Type Issues (11 errors)** - PRIORITY 2
   - quality_assessment_service.py:179 - QualityFramework/AssessmentFramework conflict
   - quality_assessment_service.py:181 - QualityRating.GOOD doesn't exist
   - quality_assessment_service.py:313, 317 - Consensus method type mismatches
   - quality_assessment_service.py:480, 488 - Object has no attribute 'append'
   - quality_assessment_service.py:557 - Indexed assignment to object
   - quality_assessment_service.py:728, 729 - Float comparison with object

5. **Research Question Service (5 errors)** - PRIORITY 2
   - Lines 262, 267, 271, 275, 381 - Unsupported indexed assignment ("object")
   - Issue: Dict values typed as object instead of specific type

6. **SLR Workflow Service (6 errors)** - PRIORITY 3
   - Lines 150-154 - SLRTask arguments typed as "object" instead of str/TaskPriority/float
   - Line 745 - Assignment type mismatch (float → bool | None)

7. **Academic Chunking Service (12 errors)** - PRIORITY 3
   - Lines 992, 1057, 1132, 1190, 1237, 1290 - Duplicate method definitions (6 errors)
   - Line 1026 - PdfReader import conflict (PyPDF2 vs pypdf)
   - Line 1112 - paper_id type mismatch (int | None → int)
   - Plus variance notes

8. **Hypothesis Analysis Service (2 errors)** - PRIORITY 3
   - Line 152 - included_papers default None vs list type
   - Line 192 - outcome_measures default None vs list type

9. **Citation Analysis Service (2 errors)** - PRIORITY 3
   - Line 580 (2 errors) - sorted() key function return type

10. **Other Errors (41 errors)** - PRIORITY 4
    - Paper repository return types
    - Chunking strategy service tuple types
    - Container parameter inspection

---

## Execution Strategy

### Stage 1: Foundation Fixes (Priority 1) - Target: 9 errors
**Focus:** Fix core dependency injection infrastructure

#### Task 1.1: Fix DatabaseConnection Duplication (5 errors)
**Problem:** Two `DatabaseConnection` classes:
- `src.database.connection.DatabaseConnection` (actual connection class)
- `src.repositories.base_repository.DatabaseConnection` (protocol/interface)

**Solution:**
```python
# base_repository.py - Define protocol
from typing import Protocol

class DatabaseConnection(Protocol):
    """Database connection protocol for repository pattern"""
    def execute(self, query: str, params: tuple) -> Any: ...
    def fetchone(self) -> Optional[tuple]: ...
    def fetchall(self) -> List[tuple]: ...
    # ... other required methods

# Then all repositories use this protocol
class BaseRepository(ABC, Generic[T]):
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
```

**Files to update:**
- `src/repositories/base_repository.py` - Change from import to Protocol
- `src/container.py` - Update instantiations (lines 110, 116, 140)
- `src/repositories/research_question_repository.py` - Fix line 19

**Expected impact:** -5 errors (88 → 83)

#### Task 1.2: Implement Concrete Repository Classes (2 errors)
**Problem:** Container trying to instantiate abstract repositories

**Solution:**
```python
# research_question_repository.py - Add concrete implementations
class ResearchQuestionRepository(BaseRepository[ResearchQuestion]):
    def create(self, entity: ResearchQuestion) -> int:
        # Implementation
        
    def get_by_id(self, id: int) -> Optional[ResearchQuestion]:
        # Implementation
        
    def update(self, entity: ResearchQuestion) -> bool:
        # Implementation
        
    def delete(self, id: int) -> bool:
        # Implementation
        
    def list_all(self) -> List[ResearchQuestion]:
        # Implementation
```

**Files to update:**
- `src/repositories/research_question_repository.py` - Implement abstract methods
- `src/repositories/hypothesis_repository.py` - Implement abstract methods

**Expected impact:** -2 errors (83 → 81)

#### Task 1.3: Add Repository Parameters to Services (2 errors)
**Problem:** Services don't accept repository dependencies in constructor

**Solution:**
```python
# research_question_service.py
class ResearchQuestionService:
    def __init__(
        self, 
        question_repository: Optional[ResearchQuestionRepository] = None
    ):
        self._question_repository = question_repository
        
# hypothesis_analysis_service.py  
class HypothesisAnalysisService:
    def __init__(
        self,
        paper_repository: IPaperRepository,
        chunk_repository: IChunkRepository,
        hypothesis_repository: Optional[HypothesisRepository] = None  # ADD THIS
    ):
        self._hypothesis_repository = hypothesis_repository
```

**Files to update:**
- `src/services/research_question_service.py:101` - Add parameter
- `src/services/hypothesis_analysis_service.py:138` - Add parameter

**Expected impact:** -2 errors (81 → 79)

---

### Stage 2: Service Type Fixes (Priority 2) - Target: 16 errors
**Focus:** Fix service method type safety

#### Task 2.1: Fix QualityAssessment Type Issues (11 errors)
**Problems:**
1. QualityFramework/AssessmentFramework enum conflict
2. Missing QualityRating.GOOD value
3. Wrong types in consensus methods
4. Object types missing type hints

**Solutions:**
```python
# Line 179 - Fix enum check
if assessment.framework == AssessmentFramework.PRISMA:  # Not QualityFramework
    
# Line 181 - Use correct enum value
default_rating = QualityRating.HIGH  # Not GOOD

# Line 313 - Fix consensus method signature
ratings_numeric = [self._rating_to_numeric(r) for r in assessments]
result = self._apply_consensus_method(ratings_numeric)

# Lines 480, 488, 557, 728, 729 - Add type hints to fix object types
issues: List[str] = []  # Line 480
recommendations: List[str] = []  # Line 488
scores: Dict[str, float] = {}  # Line 557
threshold: float = 0.7  # Line 728
```

**Files to update:**
- `src/services/quality_assessment_service.py` (lines 179, 181, 313, 317, 480, 488, 557, 728, 729)

**Expected impact:** -11 errors (79 → 68)

#### Task 2.2: Fix Research Question Service (5 errors)
**Problem:** Dict values typed as `object` instead of specific types

**Solution:**
```python
# Lines 262, 267, 271, 275, 381 - Add proper type hints
component_scores: Dict[str, float] = {}
validation_results: Dict[str, Any] = {}
framework_elements: Dict[str, str] = {}
```

**Files to update:**
- `src/services/research_question_service.py` (lines 262, 267, 271, 275, 381)

**Expected impact:** -5 errors (68 → 63)

---

### Stage 3: Workflow & Data Processing (Priority 3) - Target: 22 errors
**Focus:** Fix workflow and chunking type safety

#### Task 3.1: Fix SLR Workflow Service (6 errors)
**Problem:** SLRTask arguments typed as `object`

**Solution:**
```python
# Lines 150-154 - Fix dict value access with proper typing
task_data: Dict[str, Any] = get_task_data()
title: str = str(task_data["title"])
description: str = str(task_data["description"])
priority: TaskPriority = TaskPriority(task_data["priority"])
estimated_hours: Optional[float] = float(task_data["estimated_hours"]) if task_data.get("estimated_hours") else None

task = SLRTask(
    title=title,
    description=description,
    priority=priority,
    estimated_hours=estimated_hours
)

# Line 745 - Fix assignment type
completion_percentage: float = calculate_completion()  # Don't assign to bool field
```

**Files to update:**
- `src/services/slr_workflow_service.py` (lines 150-154, 745)

**Expected impact:** -6 errors (63 → 57)

#### Task 3.2: Fix Academic Chunking Service (12 errors)
**Problems:**
1. Duplicate method definitions (copy-paste errors)
2. PdfReader import conflict
3. paper_id Optional type

**Solutions:**
```python
# Lines 992, 1057, 1132, 1190, 1237, 1290 - Remove duplicate method definitions
# These are exact copies, just delete them

# Line 1026 - Fix import
from pypdf import PdfReader  # Remove PyPDF2 import completely

# Line 1112 - Fix paper_id
paper_id: int = chunk.paper_id if chunk.paper_id is not None else -1
chunk = AcademicChunk(..., paper_id=paper_id)
```

**Files to update:**
- `src/services/academic_chunking_service.py` (lines 992, 1026, 1057, 1112, 1132, 1190, 1237, 1290)

**Expected impact:** -12 errors (57 → 45)

#### Task 3.3: Fix Hypothesis & Citation Services (4 errors)
**Solutions:**
```python
# hypothesis_analysis_service.py
# Lines 152, 192 - Fix Optional defaults
def method(
    included_papers: Optional[List[ResearchPaper]] = None,
    outcome_measures: Optional[List[str]] = None
):
    if included_papers is None:
        included_papers = []
    if outcome_measures is None:
        outcome_measures = []

# citation_analysis_service.py
# Line 580 - Fix sorted key function
sorted_items = sorted(
    items, 
    key=lambda x: float(x.get("score", 0))  # Explicit type conversion
)
```

**Files to update:**
- `src/services/hypothesis_analysis_service.py` (lines 152, 192)
- `src/services/citation_analysis_service.py` (line 580)

**Expected impact:** -4 errors (45 → 41)

---

### Stage 4: Remaining Issues (Priority 4) - Target: 20+ errors
**Focus:** Cleanup remaining type issues

#### Task 4.1: Audit & Fix Remaining Errors
- Paper repository return types
- Chunking strategy service tuple types  
- Container parameter inspection
- Any other edge cases

**Expected impact:** -20+ errors (41 → <20)

---

## Success Criteria

### Phase 4 Goals:
- ✅ All repository dependency injection working
- ✅ All service constructors accepting dependencies
- ✅ DatabaseConnection type unified
- ✅ MyPy errors: 88 → <20 (75%+ improvement)
- ✅ No functionality broken
- ✅ All tests still passing

### Overall Refactoring Progress:
- Phase 1: 117 Ruff errors → 0 ✅
- Phase 2: 8 import paths fixed ✅
- Phase 3: 193 MyPy errors → 88 ✅
- **Phase 4: 88 MyPy errors → <20 🎯**

---

## Implementation Notes

### Testing Strategy:
1. Run MyPy after each task to verify error reduction
2. Run existing tests to ensure no functionality breaks
3. Test MCP server startup and basic operations
4. Verify container can instantiate all services

### Risk Mitigation:
- Make changes incrementally by task
- Keep backup of working state
- Test after each major change
- Document any breaking changes

### Time Estimate:
- Stage 1: 2-3 hours (foundation critical)
- Stage 2: 1-2 hours (service fixes)
- Stage 3: 1-2 hours (workflow/chunking)
- Stage 4: 2-3 hours (cleanup)
- **Total: 6-10 hours**

---

## Next Steps

Ready to start with **Stage 1: Foundation Fixes**?

1. Fix DatabaseConnection duplication
2. Implement concrete repository classes
3. Add repository parameters to services

These are the critical infrastructure changes needed for proper dependency injection.
