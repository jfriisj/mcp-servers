# Import Conventions Guide

## Clean Architecture Import Strategy

This project follows Clean Architecture with proper layer separation. Here are the import conventions to maintain code quality and prevent circular dependencies.

---

## Layer Structure

```
src/
├── domain/          # Layer 1: Business Logic (no dependencies)
├── application/     # Layer 2: Use Cases (depends on domain)
├── infrastructure/  # Layer 3: External Services (depends on domain)
├── services/        # Layer 2: Application Services
├── repositories/    # Layer 3: Data Access
├── database/        # Layer 4: Database Infrastructure
└── handlers/        # Layer 2: MCP Protocol Handlers
```

---

## Import Rules

### ✅ Rule 1: Use Relative Imports Within Package

**Within the same layer, use relative imports:**

```python
# ✅ GOOD - Relative import within domain layer
from ...domain import ResearchPaper, AcademicChunk
from ...domain.services.chunking_service import IChunkingService

# ❌ BAD - Absolute import without src prefix
from domain.models import ResearchPaper  # Won't resolve!

# ❌ BAD - Deep relative import when __init__.py exports exist
from ...domain.models.research_paper import ResearchPaper
```

### ✅ Rule 2: Use `__init__.py` to Expose Public API

**Each layer exposes its public API through `__init__.py`:**

```python
# src/domain/__init__.py
from .models import ResearchPaper, AcademicChunk, QualityAssessment

__all__ = ["ResearchPaper", "AcademicChunk", "QualityAssessment"]
```

**Then import from the layer level, not deep paths:**

```python
# ✅ GOOD - Import from layer __init__.py
from ...domain import ResearchPaper, AcademicChunk

# ❌ BAD - Deep import bypassing __init__.py
from ...domain.models.research_paper import ResearchPaper
```

### ✅ Rule 3: Layer Dependency Direction

**Dependencies flow inward (towards domain):**

```
Infrastructure → Application → Domain
   (Layer 3)   →  (Layer 2)  → (Layer 1)
```

```python
# ✅ GOOD - Infrastructure depends on domain
# In src/infrastructure/services/content_extraction_service.py
from ...domain import ResearchPaper
from ...domain.services.chunking_service import IContentExtractionService

# ❌ BAD - Domain depending on infrastructure
# In src/domain/models/research_paper.py
from ...infrastructure.services import SomeService  # NEVER!
```

### ✅ Rule 4: Import Grouping

**Group imports in this order:**

```python
"""Module docstring"""

# 1. Standard library imports
import os
import logging
from pathlib import Path
from typing import List, Optional

# 2. Third-party imports
import numpy as np
from mcp.types import TextContent

# 3. Local relative imports (same layer)
from . import helper_module

# 4. Cross-layer imports (other layers)
from ...domain import ResearchPaper
from ...domain.services import IChunkingService
from ..services import ResearchDocumentService

logger = logging.getLogger(__name__)
```

---

## Common Patterns

### Pattern 1: Domain Models

```python
# In any file needing domain models
from ...domain import ResearchPaper, AcademicChunk, QualityAssessment
```

### Pattern 2: Services

```python
# In handlers needing services
from ..services import (
    ResearchDocumentService,
    QualityAssessmentService,
    AcademicChunkingService
)
```

### Pattern 3: Repositories

```python
# In services needing repositories
from ..repositories import PaperRepository, ChunkRepository
```

### Pattern 4: Database

```python
# In files needing database
from ..database import DatabaseConnection, SchemaManager
```

---

## Relative Import Navigation

**Understand the `..` notation:**

```
Current file:  src/infrastructure/services/content_extraction.py

.              → src/infrastructure/services/
..             → src/infrastructure/
...            → src/
....           → (parent of src - usually not needed)
```

**Examples:**

```python
# From: src/infrastructure/services/content_extraction.py
from ...domain import ResearchPaper              # ✅ src/domain/__init__.py
from ...services import ResearchDocumentService  # ✅ src/services/__init__.py
from ..services.chunking import ChunkService     # ✅ src/infrastructure/services/chunking.py
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Importing from `domain` Without Prefix

```python
# ❌ BAD - Python can't resolve 'domain' as top-level package
from domain.models import ResearchPaper
from application.container import Container

# ✅ GOOD - Use relative imports
from ...domain import ResearchPaper
from .. import Container
```

### ❌ Anti-Pattern 2: Circular Imports

```python
# ❌ BAD - Circular dependency
# In domain/models/paper.py
from ...services import PaperService  # Domain depends on application!

# ✅ GOOD - Use dependency injection
class PaperService:
    def __init__(self, paper_repository: IPaperRepository):
        self.paper_repo = paper_repository  # Depend on interface
```

### ❌ Anti-Pattern 3: Deep Imports

```python
# ❌ BAD - Bypasses __init__.py abstraction
from ...domain.models.research_paper import ResearchPaper
from ...domain.models.academic_chunk import AcademicChunk

# ✅ GOOD - Import from layer level
from ...domain import ResearchPaper, AcademicChunk
```

### ❌ Anti-Pattern 4: Wildcard Imports

```python
# ❌ BAD - Unclear what's imported, namespace pollution
from ...domain import *

# ✅ GOOD - Explicit imports
from ...domain import ResearchPaper, AcademicChunk
```

---

## Layer-Specific Examples

### Domain Layer (src/domain/)

```python
# domain/__init__.py - Expose domain models
from .models import ResearchPaper, AcademicChunk, QualityAssessment

__all__ = ["ResearchPaper", "AcademicChunk", "QualityAssessment"]
```

### Application Layer (src/application/)

```python
# application/handlers/solid_mcp_handler.py
from ...domain import ResearchPaper  # Import from domain
from ...domain.repositories.paper_repository import IPaperRepository
from .. import IDependencyContainer   # Import from application
```

### Infrastructure Layer (src/infrastructure/)

```python
# infrastructure/services/content_extraction.py
from ...domain import ResearchPaper  # Import domain models
from ...domain.services.chunking_service import IContentExtractionService
```

### Services Layer (src/services/)

```python
# services/research_document_service.py
from ..domain import ResearchPaper    # Import domain models
from ..repositories import PaperRepository
from ..database import DatabaseConnection
```

---

## Testing Imports

**In tests, import from `src` prefix:**

```python
# tests/test_research_service.py
from src.domain import ResearchPaper
from src.services import ResearchDocumentService
from src.repositories import PaperRepository
```

**Or use relative imports if tests are in `src/` directory:**

```python
# src/tests/test_research_service.py
from ..domain import ResearchPaper
from ..services import ResearchDocumentService
```

---

## Quick Reference

| Import Type | Example | Use When |
|------------|---------|----------|
| Same package | `from . import module` | Importing sibling module |
| Parent package | `from .. import module` | One level up |
| Grandparent | `from ... import module` | Two levels up |
| Layer API | `from ...domain import Model` | Importing from layer `__init__.py` |
| Deep import | `from ...domain.models.paper import Paper` | **Avoid - use layer API** |

---

## Checklist for New Files

When creating a new file, ensure:

- [ ] ✅ Imports use relative notation (`..`, `...`)
- [ ] ✅ Import from layer `__init__.py` when possible
- [ ] ✅ Imports grouped: stdlib → third-party → local → cross-layer
- [ ] ✅ No circular dependencies
- [ ] ✅ Dependencies flow inward (toward domain)
- [ ] ✅ No `from domain.` or `from application.` (missing `src.`)
- [ ] ✅ Explicit imports (no `import *`)

---

## Troubleshooting

### Issue: "Import could not be resolved"

**Problem:** Python can't find the module

**Solutions:**
1. Check relative import depth (`..`, `...`)
2. Ensure `__init__.py` exists in each directory
3. Verify module name matches filename
4. Check if you're using `from domain.` instead of `from ...domain`

### Issue: "Circular import detected"

**Problem:** Module A imports B, B imports A

**Solutions:**
1. Move shared code to a separate module
2. Use dependency injection (pass instances)
3. Import inside function instead of module level
4. Refactor to break the cycle

### Issue: "Module not found in __all__"

**Problem:** Trying to import something not exposed

**Solutions:**
1. Check `__init__.py` `__all__` list
2. Import directly from the module file
3. Add the export to `__init__.py` if it should be public

---

## Migration Guide

**Converting old imports to new convention:**

```python
# OLD (broken)
from domain.models import ResearchPaper
from application.container import Container

# NEW (working)
from ...domain import ResearchPaper
from .. import Container
```

**Bulk find and replace:**

```bash
# Find files with old pattern
grep -r "from domain\." src/
grep -r "from application\." src/

# Fix manually or with sed (be careful!)
sed -i 's/from domain\./from ...domain./g' src/**/*.py
sed -i 's/from application\./from ...application./g' src/**/*.py
```

---

**Last Updated:** October 16, 2025  
**Status:** ✅ Actively enforced  
**Violations:** See [REFACTORING_PLAN.md](REFACTORING_PLAN.md) for current issues
