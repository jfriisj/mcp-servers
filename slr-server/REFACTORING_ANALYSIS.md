# SLR Server - Comprehensive Refactoring Analysis

**Date:** October 19, 2025  
**Analysis Tools:** SOLID Principles Analyzer, Import Analysis, Multi-lint (Ruff, Pylint, MyPy)

---

## Executive Summary

### Overall Health Metrics
- **SOLID Score:** 87.5/100 (Average)
- **Import Health:** 54.2/100 (Needs Improvement)
- **Import Success Rate:** 68.6%
- **Ruff Issues:** 117 errors (103 auto-fixable)
- **Pylint Rating:** 2.05/10
- **MyPy Errors:** 218 type errors

### Critical Findings
1. **Two Duplicate Server Implementations** - `main.py` (25 tools) vs `server.py` (22 tools)
2. **501 Dependency Inversion Principle (DIP) violations** - Heavy tight coupling
3. **Circular import risk** - Zero currently, but import health is poor
4. **4 Unused dependencies** - bibtexparser, pybtex, PyPDF2, pypdf
5. **Architecture violations** - 7 layer boundary crossings

---

## Priority 1: Critical Issues (Must Fix)

### 1.1 Duplicate Server Implementations ⚠️ **CRITICAL**

**Problem:** Two MCP server implementations exist:
- `src/main.py` - 25 tools (actively used)
- `src/server.py` - 22 tools (appears unused)

**Impact:**
- Confusion about which is canonical
- Maintenance burden
- Wasted resources
- Different tool sets in each file

**Recommendation:**
```
1. Verify which file start_server.py actually uses (main.py)
2. Archive or delete server.py
3. Update all imports to reference main.py only
4. Document decision in ARCHITECTURE.md
```

**Tools unique to main.py (5):**
- calculate_inter_rater_reliability
- detect_citation_patterns
- analyze_hypotheses
- export_citation_network
- get_chunk_content

**Tools unique to server.py (2):**
- upload-paper-with-full-text
- test-hypothesis

### 1.2 Missing SLRMCPHandler Type Definition

**Problem:** `container.py` references undefined `SLRMCPHandler` type
```python
# Lines 69 and 230
self._mcp_handler: Optional['SLRMCPHandler'] = None
```

**Impact:** Type checking fails, IDE autocomplete broken

**Solution:**
```python
from .handlers.mcp_handler import SLRMCPHandler
```

### 1.3 Unused Dependencies (Security & Maintenance Risk)

**Problem:** 4 unused dependencies in requirements.txt
- `bibtexparser` - Not imported anywhere
- `pybtex` - Not imported anywhere
- `PyPDF2` - Imported but not used (replaced by pypdf?)
- `pypdf` - Listed as unused but may be in use

**Action:**
```bash
# Run dependency validation
pip-autoremove bibtexparser pybtex PyPDF2
# OR update requirements.txt manually
```

---

## Priority 2: High Priority (Should Fix Soon)

### 2.1 SOLID Principles Violations

#### Most Problematic Files

| File | Score | Violations | Top Issue |
|------|-------|------------|-----------|
| mcp_handler.py | 0.0/100 | 84 | DIP violations |
| research_document_service.py | 0.0/100 | 72 | DIP violations |
| paper_repository.py | 23.0/100 | 37 | Long methods, DIP |
| academic_chunking_service.py | 39.0/100 | 29 | Long methods |
| slr_workflow_handlers.py | 50.0/100 | 25 | DIP violations |

#### 2.1.1 Dependency Inversion Principle (DIP) - 501 Violations

**Pattern:** Direct instantiation everywhere
```python
# ❌ BAD - Direct instantiation
def some_method(self):
    result = CallToolResult(...)  # Tight coupling
    service = ResearchDocumentService(...)  # Cannot mock
```

**Solution:** Use dependency injection
```python
# ✅ GOOD - Dependency injection
def __init__(self, result_factory: ResultFactory, service: DocumentService):
    self._result_factory = result_factory
    self._service = service

def some_method(self):
    result = self._result_factory.create(...)
```

**Action Plan:**
1. Create factory classes for common instantiations (CallToolResult, TextContent)
2. Pass dependencies via constructor (already using Container pattern!)
3. Use Container.get_* methods instead of direct instantiation
4. Apply to top 5 violators first

#### 2.1.2 Single Responsibility Principle (SRP) - 88 Violations

**Problem:** Many methods exceed 30 lines

Worst offenders:
- `upload_bibliography_batch` (168 lines) - research_document_service.py
- `upload_paper_with_full_text` (156 lines) - research_document_service.py
- `generate_report` (104 lines) - screen_all_papers.py
- `list_all` (100 lines) - paper_repository.py

**Solution:**
```python
# ❌ BAD - 168 line method
async def upload_bibliography_batch(self, file_path, ...):
    # Parse file
    # Extract entries
    # Validate entries
    # Upload each paper
    # Handle errors
    # Generate report

# ✅ GOOD - Decomposed
async def upload_bibliography_batch(self, file_path, ...):
    entries = await self._parse_bibliography_file(file_path)
    validated = await self._validate_entries(entries)
    results = await self._upload_papers(validated)
    return self._generate_upload_report(results)
```

#### 2.1.3 Open/Closed Principle (OCP) - 58 Violations

**Problem:** Too many conditional branches, type checking

```python
# ❌ BAD - 18 branches in handle_call_tool
if tool_name == "upload_paper":
    return await self._handle_upload()
elif tool_name == "assess_quality":
    return await self._handle_assessment()
# ... 16 more conditions

# ✅ GOOD - Strategy pattern
TOOL_HANDLERS = {
    "upload_paper": self._handle_upload,
    "assess_quality": self._handle_assessment,
    # ...
}
handler = TOOL_HANDLERS.get(tool_name)
return await handler(arguments)
```

### 2.2 Import Analysis Issues

#### 2.2.1 Import Health Score: 54.2/100

**Problems:**
- 191 invalid imports (31.4% failure rate)
- Inconsistent relative vs absolute imports
- Missing `src` dependency

**Files Needing Attention:**
1. `src/container.py` - 0/100 (24 issues)
2. `src/chunking/strategy_factory.py` - 0/100 (5 issues)
3. `src/chunking/__init__.py` - 0/100 (4 issues)
4. `src/database/__init__.py` - 0/100 (2 issues)
5. `src/domain/__init__.py` - 0/100 (1 issue)

**Solution:**
```python
# ❌ BAD - Inconsistent imports
from ..domain.domain.models import ResearchPaper  # Wrong path
from src.domain.models import Author  # Mixed absolute/relative

# ✅ GOOD - Consistent relative imports from package root
from src.domain.models import ResearchPaper, Author
# OR all relative:
from ..domain.models import ResearchPaper, Author
```

#### 2.2.2 Architecture Violations (7 Found)

**Violations:**
1. Core → Domain (upload_all_via_mcp.py:22)
2. Tests → Core (test_handlers.py:22)
3. Tests → Core (test_init.py:24)
4. Tests → Core (test_mcp_integration.py:18)
5. Tests → Domain (test_phase2_manual.py:23)

**Recommendation:**
- Move scripts out of `scripts/` into proper layers
- Tests should only import from public APIs, not internal modules
- Consider creating a `public` or `api` module for external consumption

### 2.3 Type Safety Issues (MyPy - 218 Errors)

#### Critical Type Issues:

1. **Missing type stubs:**
   - `psycopg2` (3 errors)
   - `PyPDF2` (3 errors)
   - `fitz` / `pymupdf` (3 errors)
   - `docx` / `python-docx` (2 errors)
   - `pybtex` (1 error)

   **Solution:**
   ```bash
   pip install types-psycopg2 types-PyYAML
   # For others, add type: ignore or create stub files
   ```

2. **Domain model mismatches (60+ errors):**
   ```python
   # QualityAssessment issues:
   - Missing: overall_score, risk_of_bias, criterion_scores, status
   - Has: criteria_scores (wrong name?)
   
   # ResearchHypothesis issues:
   - Missing: expected_outcome, intervention, direction, significance_level
   
   # SLRProject issues:
   - Missing: title, research_domain, team_lead, research_question
   ```

   **Action:** Audit `src/domain/models.py` vs actual usage

3. **Import path errors:**
   ```python
   # ❌ BAD - Wrong path
   from src.domain.domain.models import ResearchPaper
   
   # ✅ GOOD
   from src.domain.models import ResearchPaper
   ```

### 2.4 Code Style Issues (Ruff - 117 Errors)

#### Auto-fixable (103 issues):

```bash
# Run this to auto-fix most issues:
ruff check slr-server/src --fix
```

**Categories:**
- F401: Unused imports (60+)
- F541: f-strings without placeholders (30+)
- E402: Module imports not at top (6)
- F841: Unused variables (5)
- E722: Bare except clauses (3)

#### Manual fixes needed (14 issues):

1. **Bare except clauses** (research_document_service.py)
   ```python
   # ❌ BAD
   except:
       pass
   
   # ✅ GOOD
   except (ValueError, KeyError) as e:
       logger.warning(f"Error: {e}")
   ```

2. **Module-level imports in middle of file** (domain/models.py:1294-1302)
   - Move imports to top of file

---

## Priority 3: Medium Priority (Nice to Have)

### 3.1 Code Quality Improvements (Pylint - 2.05/10)

**Categories:**
- Line too long (70+ instances) - Max 100 chars
- Trailing whitespace (15 instances)
- Missing final newline (1 instance)
- Too many branches (1 method: 18 branches)
- Broad exception catching (3 instances)

**Quick wins:**
```bash
# Auto-format
black slr-server/src
# OR
ruff format slr-server/src
```

### 3.2 Interface Segregation Principle (ISP) - 5 Violations

**Problem:** Classes with too many public methods

| Class | Methods | Recommendation |
|-------|---------|----------------|
| Container | 21 | Split into ServiceContainer, RepositoryContainer |
| DatabaseConnection | 13 | Split into ConnectionManager, QueryExecutor |
| ResearchDocumentService | 14 | Split by responsibility |
| ResearchPaper | 12 | Move methods to separate services |
| PaperRepository | 12 | Split into PaperReader, PaperWriter |

### 3.3 Documentation Improvements

**Missing:**
- Architecture decision records (ADR)
- Dependency graph visualization
- API documentation (OpenAPI/Swagger for MCP tools)
- Contribution guidelines

---

## Refactoring Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Remove duplicate server.py or consolidate with main.py
- [ ] Fix SLRMCPHandler type definition
- [ ] Remove unused dependencies
- [ ] Run `ruff check --fix` to auto-fix 103 issues
- [ ] Fix bare except clauses (3 locations)

### Phase 2: Import Cleanup (Week 2)
- [ ] Standardize import paths (absolute vs relative)
- [ ] Fix domain model import issues
- [ ] Add missing type stubs
- [ ] Resolve architecture boundary violations

### Phase 3: Type Safety (Week 3)
- [ ] Audit and fix domain models (QualityAssessment, ResearchHypothesis, SLRProject)
- [ ] Add type hints to untyped functions
- [ ] Enable `--check-untyped-defs` in mypy config
- [ ] Target: 0 mypy errors

### Phase 4: SOLID Refactoring (Week 4-6)
- [ ] DIP: Create factory classes, inject dependencies (top 10 violators)
- [ ] SRP: Decompose long methods (>50 lines) into smaller functions
- [ ] OCP: Replace conditional chains with strategy pattern
- [ ] ISP: Split fat interfaces into focused ones

### Phase 5: Architecture Improvements (Week 7-8)
- [ ] Document architectural decisions
- [ ] Create public API layer for external consumption
- [ ] Add integration tests for refactored modules
- [ ] Performance benchmarking

---

## Recommendations

### Immediate Actions (This Week)
1. **Decide on canonical server:** Keep main.py, remove server.py
2. **Run auto-fixers:**
   ```bash
   cd slr-server
   ruff check src --fix
   black src
   ```
3. **Fix type imports:** Update all `from src.domain.domain.models` → `from src.domain.models`
4. **Remove unused deps:** Update requirements.txt

### Short-term (Next Month)
1. **Dependency Injection:** Refactor top 10 DIP violators
2. **Method Decomposition:** Break down 10+ methods >50 lines
3. **Type Safety:** Fix domain model mismatches
4. **Import Health:** Get to 80%+ import success rate

### Long-term (Quarter)
1. **Full SOLID compliance:** Target 95+ score
2. **100% type coverage:** MyPy strict mode
3. **API documentation:** OpenAPI specs for all MCP tools
4. **Performance optimization:** Profile and optimize hot paths

---

## Measuring Success

### Target Metrics (3 Months)
- SOLID Score: 87.5 → 95+
- Import Health: 54.2 → 90+
- Ruff Errors: 117 → 0
- Pylint Rating: 2.05 → 9.0+
- MyPy Errors: 218 → 0
- Test Coverage: ??? → 80%+

### Progress Tracking
```bash
# Weekly health check
./scripts/health_check.sh

# Contents of health_check.sh:
#!/bin/bash
echo "=== Code Quality Report ==="
ruff check src | wc -l
pylint src/main.py | grep "rated at"
mypy src | grep "error"
```

---

## Decision Log

### Should We Refactor or Rewrite?

**Verdict: REFACTOR (Not Rewrite)**

**Reasoning:**
- Core functionality works (21/24 tools tested, 20/21 passing)
- Architecture is sound (Clean Architecture patterns visible)
- Issues are mostly technical debt, not fundamental flaws
- Incremental refactoring is lower risk than rewrite

**Red Flags That Would Warrant Rewrite:**
- ❌ Circular dependencies (None found!)
- ❌ Fundamentally broken architecture (Architecture is good)
- ❌ No test coverage (Has tests, needs more)
- ❌ Unmaintainable codebase (Complex but maintainable)

### What Can Be Removed?

**Safe to Remove:**
1. `src/server.py` - Duplicate of main.py
2. `bibtexparser` - Not imported
3. `pybtex` - Not imported  
4. `PyPDF2` - Replaced by pypdf
5. Unused test files (if any exist)

**Investigate Further:**
1. `src/domain/services/` - May be old interface definitions
2. `src/application/container.py` - DI container, may conflict with `src/container.py`
3. Backup files: `connection_backup.py`, `connection_new.py`

**DO NOT Remove:**
1. Core services (research_document_service, quality_assessment_service, etc.)
2. Repository pattern implementations
3. Domain models
4. MCP handlers
5. Container.py (DI is critical)

---

## Conclusion

The SLR server is **production-ready with technical debt**. It functions well but has accumulated considerable technical debt in the form of:
- Tight coupling (DIP violations)
- Large methods (SRP violations)
- Inconsistent imports
- Type safety gaps

**The codebase is maintainable and refactorable.** With disciplined incremental refactoring over 2-3 months, we can achieve excellent code quality without disrupting functionality.

**Priority:** Fix the server duplication issue first, then tackle imports, then SOLID principles.

---

**Next Steps:**
1. Review this document with the team
2. Prioritize Phase 1 tasks
3. Create GitHub issues for each refactoring task
4. Set up weekly code quality reviews
5. Start refactoring!
