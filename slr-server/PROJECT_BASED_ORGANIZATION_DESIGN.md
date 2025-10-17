# Project-Based Organization for SLR Server

**Date**: October 17, 2025  
**Purpose**: Design document for project-based file organization in SLR server  
**Context**: Enable students to organize SLR work by project with automatic folder structure

---

## Problem Statement

### Current Issues
1. **Flat Structure**: All papers in single `papers/` folder
2. **No Project Association**: Papers not linked to specific SLR projects
3. **Manual Organization**: Students must manually organize files
4. **Scattered Documents**: Search strategies, screening notes, etc. in different locations
5. **No Project Context**: Hard to track which papers belong to which research project

### User Story
> **As a** software engineering student conducting an SLR on software design patterns,  
> **I want** to place my project description file (PDF or Markdown) in a project folder and have the system automatically create an organized structure,  
> **So that** all my papers, screening notes, and analyses are kept together in one place.

---

## Proposed Solution

### Ideal Folder Structure

```
slr-server/
├── projects/
│   ├── software-designs/              # Project root folder
│   │   ├── project.json              # Project metadata (auto-generated)
│   │   ├── software-designs.pdf      # Original project description (PDF)
│   │   ├── software-designs.md       # OR project description (Markdown)
│   │   ├── research-questions.md     # Extracted research questions
│   │   │
│   │   ├── papers/                   # All papers for this project
│   │   │   ├── screening/           # Papers being screened
│   │   │   ├── included/            # Papers included in review
│   │   │   ├── excluded/            # Papers excluded from review
│   │   │   └── bibliography/        # BibTeX and metadata files
│   │   │
│   │   ├── search-strategies/        # Database searches
│   │   │   ├── ieee-xplore.md       # IEEE search query
│   │   │   ├── acm-digital.md       # ACM search query
│   │   │   ├── search-results.csv   # Combined results
│   │   │   └── search-log.md        # Search history
│   │   │
│   │   ├── screening/                # Screening process
│   │   │   ├── inclusion-exclusion-criteria.md
│   │   │   ├── title-abstract/      # Phase 1 screening
│   │   │   │   ├── reviewer1.csv
│   │   │   │   └── reviewer2.csv
│   │   │   ├── full-text/           # Phase 2 screening
│   │   │   │   ├── reviewer1.csv
│   │   │   │   └── reviewer2.csv
│   │   │   └── conflicts.md         # Disagreements resolved
│   │   │
│   │   ├── quality-assessment/       # Quality assessment
│   │   │   ├── framework.md         # Assessment criteria
│   │   │   ├── results/             # Per-paper assessments
│   │   │   └── summary.csv
│   │   │
│   │   ├── data-extraction/          # Data extraction
│   │   │   ├── extraction-template.md
│   │   │   ├── extracted/           # Extracted data per paper
│   │   │   └── synthesis.csv        # Combined data
│   │   │
│   │   ├── analysis/                 # Data analysis
│   │   │   ├── thematic-analysis.md
│   │   │   ├── synthesis.md
│   │   │   └── visualizations/      # Charts, graphs
│   │   │
│   │   ├── deduplication/            # Duplicate detection
│   │   │   ├── duplicates-found.md  # List of duplicates
│   │   │   ├── removed.md           # Removed papers
│   │   │   └── dedup-log.csv
│   │   │
│   │   └── reports/                  # Generated reports
│   │       ├── progress-reports/    # Weekly/monthly progress
│   │       ├── interim-report.md    # Mid-project report
│   │       └── final-report.md      # Final deliverable
│   │
│   └── cloud-computing-security/     # Another project
│       └── ... (same structure)
```

### Key Principles

1. **One Project = One Folder**: All project artifacts in single location
2. **PRISMA Alignment**: Folder structure follows PRISMA methodology phases
3. **Self-Documenting**: Folder names match SLR terminology
4. **Automatic Initialization**: System creates structure from project description
5. **Paper Lifecycle**: Papers move through folders as screening progresses

---

## Database Schema Changes

### New: SLRProject Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class SLRProject:
    """Represents a systematic literature review project."""
    
    # Identity
    id: Optional[int] = None
    name: str                           # "software-designs" (slug)
    display_name: str                   # "Software Design Patterns" (human-readable)
    description: str                    # Project description
    
    # Research framework (PICO/SPIDER)
    research_questions: List[str] = None     # ["RQ1: ...", "RQ2: ..."]
    population: Optional[str] = None         # Target population
    intervention: Optional[str] = None       # Intervention being studied
    comparison: Optional[str] = None         # Comparison group
    outcome: Optional[str] = None            # Outcome measures
    
    # File system
    folder_path: str                    # "projects/software-designs"
    project_file_path: Optional[str] = None   # Path to description file (PDF or MD)
    project_file_type: Optional[str] = None   # "pdf" or "markdown"
    
    # Timestamps
    created_date: datetime = None
    updated_date: datetime = None
    
    # Status tracking
    current_phase: str = "planning"     # planning, search, screening, etc.
    status: str = "active"              # active, completed, paused, archived
    
    # Paper statistics
    total_papers: int = 0
    papers_screening: int = 0
    papers_included: int = 0
    papers_excluded: int = 0
    papers_quality_assessed: int = 0
    
    # Team management
    created_by: Optional[str] = None
    team_members: List[str] = None      # List of team member names/IDs
    
    # Settings
    settings: Optional[Dict[str, Any]] = None    # Project-specific configuration
    
    # Metadata
    tags: List[str] = None
    notes: str = ""
```

### Modified: ResearchPaper Model

```python
@dataclass
class ResearchPaper:
    # ... existing fields (id, title, authors, etc.) ...
    
    # NEW: Project association
    project_id: Optional[int] = None
    project_name: Optional[str] = None       # Denormalized for faster queries
    
    # NEW: Project-specific file management
    relative_file_path: Optional[str] = None  # "screening/paper1.pdf"
    absolute_file_path: str = None           # Full path (computed)
    
    # NEW: Screening workflow within project
    screening_status: Optional[str] = None   # "pending", "screening", "included", "excluded"
    screening_phase: Optional[str] = None    # "title-abstract", "full-text"
    screening_notes: Optional[str] = None
    screening_date: Optional[datetime] = None
    screened_by: Optional[str] = None
    
    # ... rest of existing fields ...
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Priority**: HIGH  
**Dependencies**: None

#### Tasks:
1. **Create Project Model**
   - Define `SLRProject` dataclass
   - Create database table
   - Add indexes for common queries

2. **Create Project Repository**
   - CRUD operations for projects
   - Query methods (get by name, list active, etc.)

3. **Update ResearchPaper Model**
   - Add `project_id`, `project_name` fields
   - Add screening workflow fields
   - Database migration script

4. **Create ProjectService**
   - Basic project creation
   - Folder structure initialization
   - Template file generation

#### Deliverables:
- ✅ Project model and repository
- ✅ Database migration script
- ✅ Folder initialization logic
- ✅ Unit tests for project CRUD

---

### Phase 2: Project Creation from PDF/Markdown (Week 2)

**Priority**: HIGH  
**Dependencies**: Phase 1

#### Tasks:
1. **File Parsing Service**
   - **PDF Support**: Extract title, research questions, PICO components
   - **Markdown Support**: Parse frontmatter (YAML), extract sections
   - Pattern matching for research questions (RQ1, RQ2, etc.)
   - OCR support for scanned PDFs

2. **Project Initialization**
   - `create_project_from_file(project_name, file_path)`
   - Auto-detect file type (PDF vs Markdown)
   - Automatic folder creation
   - Generate `project.json` metadata
   - Create template files

3. **MCP Tool: create_slr_project**
   - Input: project_name, file_path (PDF or MD) or manual description
   - Output: Project created with full structure
   - Error handling for duplicates
   - Support for both file formats

4. **Template System**
   - Default templates for each folder
   - Customizable templates
   - Template rendering with project metadata

#### Deliverables:
- ✅ PDF and Markdown extraction working
- ✅ Project creation from both file types functional
- ✅ MCP tool exposed and tested
- ✅ Template system implemented

---

### Phase 3: Project-Aware Paper Management (Week 3)

**Priority**: MEDIUM  
**Dependencies**: Phase 1, 2

#### Tasks:
1. **Modify upload_paper Method**
   ```python
   def upload_paper(
       self,
       file_path: str,
       project_name: Optional[str] = None,  # NEW
       # ... existing parameters ...
   ) -> ResearchPaper:
   ```

2. **New Helper Methods** (following our refactoring pattern!)
   - `_determine_storage_path(file_path, project_name)`
   - `_copy_to_project_folder(file_path, paper, project_name)`
   - `_update_project_statistics(project_id, action)`

3. **Paper Lifecycle Management**
   - Move paper between folders (screening → included/excluded)
   - Update screening status
   - Track screening history

4. **New MCP Tools**
   - `upload_paper_to_project` - Upload with project context
   - `list_project_papers` - Get papers for specific project
   - `move_paper_status` - Change screening status
   - `bulk_upload_to_project` - Batch upload

#### Deliverables:
- ✅ Project-aware paper upload
- ✅ Paper movement between folders
- ✅ MCP tools for paper management
- ✅ Integration tests

---

### Phase 4: Advanced Features (Week 4+)

**Priority**: LOW  
**Dependencies**: Phase 1-3

#### Tasks:
1. **Project Reporting**
   - Progress reports (PRISMA flow diagram)
   - Statistics dashboard
   - Export functionality (PDF, Word)

2. **Search Strategy Management**
   - Track database searches
   - Store query strings
   - Log search results

3. **Quality Assessment**
   - Framework templates (CASP, JBI, etc.)
   - Per-paper assessment storage
   - Agreement calculations

4. **Data Extraction**
   - Extraction templates
   - Structured data storage
   - Synthesis views

5. **Additional MCP Tools**
   - `get_project_structure` - Folder tree with counts
   - `generate_project_report` - Progress/final reports
   - `export_project_data` - Full project export
   - `duplicate_project` - Create project from template

#### Deliverables:
- ✅ Reporting system
- ✅ Advanced MCP tools
- ✅ Documentation updated

---

## Service Architecture

### New: ProjectService

```python
class ProjectService:
    """
    Service for managing SLR projects.
    
    Follows the orchestration pattern from Phase 3 refactoring.
    """
    
    def __init__(self, project_repository, paper_repository):
        self.project_repository = project_repository
        self.paper_repository = paper_repository
    
    def create_project_from_file(
        self,
        project_name: str,
        file_path: str,
        extract_metadata: bool = True
    ) -> SLRProject:
        """
        Create SLR project from description file (PDF or Markdown).
        
        Orchestration pattern:
        1. Validate inputs
        2. Detect file type
        3. Extract metadata
        4. Build project entity
        5. Initialize folders
        6. Create templates
        7. Persist
        """
        # 1. Validate
        self._validate_project_name(project_name)
        self._validate_file_exists(file_path)
        
        # 2. Detect file type
        file_type = self._detect_file_type(file_path)
        
        # 3. Extract metadata
        metadata = {}
        if extract_metadata:
            metadata = self._extract_project_metadata(file_path, file_type)
        
        # 4. Build entity
        project = self._build_project_entity(
            project_name, 
            file_path, 
            file_type,
            metadata
        )
        
        # 5. Initialize folders
        self._initialize_project_folders(project)
        
        # 6. Create templates
        self._create_project_templates(project)
        
        # 7. Persist
        return self.project_repository.create(project)
    
    # Helper methods (following Phase 3 pattern)
    
    def _validate_project_name(self, name: str) -> None:
        """Validate project name (slug format)."""
        # Must be lowercase, hyphens, alphanumeric
        # Must not already exist
        pass
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from extension.
        
        Returns:
            "pdf" or "markdown"
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use .pdf or .md")
    
    def _extract_project_metadata(
        self, 
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Extract title, research questions from file.
        
        For PDF:
        - Use PDF parsing library (PyPDF2, pdfplumber)
        - Pattern matching for RQ1, RQ2, etc.
        - Extract text and analyze
        
        For Markdown:
        - Parse YAML frontmatter if present
        - Extract headings and content
        - Look for research questions section
        """
        if file_type == "pdf":
            return self._extract_from_pdf(file_path)
        elif file_type == "markdown":
            return self._extract_from_markdown(file_path)
        else:
            return {}
    
    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        # Use PyPDF2 or pdfplumber
        # Pattern matching for research questions
        pass
    
    def _extract_from_markdown(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from Markdown file.
        
        Supports:
        1. YAML frontmatter:
           ---
           title: "Software Design Patterns"
           research_questions:
             - "RQ1: What are common patterns?"
             - "RQ2: How are they applied?"
           pico:
             population: "Software projects"
             intervention: "Design patterns"
           ---
        
        2. Markdown sections:
           # Title
           ## Research Questions
           - RQ1: ...
           - RQ2: ...
        """
        import re
        from pathlib import Path
        
        content = Path(file_path).read_text(encoding='utf-8')
        metadata = {}
        
        # Try YAML frontmatter first
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            import yaml
            try:
                metadata = yaml.safe_load(frontmatter_match.group(1))
            except:
                pass
        
        # Extract from markdown structure
        if not metadata.get('title'):
            # Look for # Title (first heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
        
        if not metadata.get('research_questions'):
            # Look for research questions section
            rq_section = re.search(
                r'##\s+Research Questions.*?\n(.*?)(?=\n##|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if rq_section:
                rq_text = rq_section.group(1)
                # Extract list items or RQ1, RQ2 patterns
                questions = re.findall(r'[-*]\s+(RQ\d+:?\s*.+?)(?=\n|$)', rq_text)
                if not questions:
                    questions = re.findall(r'(RQ\d+:?\s*.+?)(?=\n|$)', rq_text)
                metadata['research_questions'] = [q.strip() for q in questions]
        
        return metadata
    
    def _build_project_entity(
        self,
        name: str,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any]
    ) -> SLRProject:
        """Construct SLRProject entity from inputs."""
        pass
    
    def _initialize_project_folders(self, project: SLRProject) -> None:
        """Create standard SLR folder structure."""
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
            "reports"
        ]
        for folder in folders:
            (base_path / folder).mkdir(parents=True, exist_ok=True)
    
    def _create_project_templates(self, project: SLRProject) -> None:
        """Create template files in project folders."""
        # Copy from templates directory
        # Render with project metadata (name, RQs, etc.)
        pass
```

### Modified: ResearchDocumentService

```python
class ResearchDocumentService:
    """Modified to support project-based storage."""
    
    def __init__(self, paper_repository, project_repository=None):
        self.paper_repository = paper_repository
        self.project_repository = project_repository  # NEW
    
    def upload_paper(
        self,
        file_path: str,
        project_name: Optional[str] = None,  # NEW
        title: Optional[str] = None,
        authors: Optional[List[Author]] = None,
        # ... other existing params ...
    ) -> ResearchPaper:
        """
        Upload paper to global or project-specific location.
        
        MODIFIED orchestration:
        1. Validate file (existing)
        2. Determine storage path (NEW)
        3. Extract metadata (existing)
        4. Validate metadata (existing)
        5. Build entity with project (MODIFIED)
        6. Copy to project folder (NEW)
        7. Persist (existing)
        """
        # 1. Validate file (existing helper)
        file_ext, file_size, _ = self._validate_file_path(file_path)
        
        # 2. Determine storage (NEW helper)
        storage_info = self._determine_storage_location(file_path, project_name)
        
        # 3-4. Extract and validate (existing helpers)
        metadata = self._extract_and_merge_metadata(...)
        self._validate_paper_metadata(...)
        
        # 5. Build entity (MODIFIED helper)
        paper = self._build_research_paper_entity(
            ...,
            project_name=project_name,
            storage_info=storage_info
        )
        
        # 6. Copy to project folder (NEW)
        if project_name:
            actual_path = self._copy_to_project_folder(
                file_path, 
                paper, 
                storage_info
            )
            paper.absolute_file_path = actual_path
        
        # 7. Persist (existing)
        created = self.paper_repository.create(paper)
        
        # 8. Update project stats (NEW)
        if project_name:
            self._update_project_statistics(project_name, "paper_added")
        
        return created
    
    # NEW helper methods
    
    def _determine_storage_location(
        self,
        file_path: str,
        project_name: Optional[str]
    ) -> Dict[str, str]:
        """Determine where to store the paper."""
        if not project_name:
            # Legacy: global papers folder
            return {
                "type": "global",
                "base_path": "papers",
                "relative_path": Path(file_path).name
            }
        
        # Project-based: papers/screening folder
        project = self.project_repository.get_by_name(project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found")
        
        return {
            "type": "project",
            "project_id": project.id,
            "base_path": f"{project.folder_path}/papers/screening",
            "relative_path": f"screening/{Path(file_path).name}"
        }
    
    def _copy_to_project_folder(
        self,
        source_path: str,
        paper: ResearchPaper,
        storage_info: Dict[str, str]
    ) -> str:
        """Copy paper file to project folder."""
        import shutil
        
        dest_path = Path(storage_info["base_path"]) / Path(source_path).name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        
        return str(dest_path)
    
    def _update_project_statistics(
        self,
        project_name: str,
        action: str
    ) -> None:
        """Update project paper counts."""
        project = self.project_repository.get_by_name(project_name)
        if not project:
            return
        
        if action == "paper_added":
            project.total_papers += 1
            project.papers_screening += 1
        elif action == "paper_included":
            project.papers_screening -= 1
            project.papers_included += 1
        elif action == "paper_excluded":
            project.papers_screening -= 1
            project.papers_excluded += 1
        
        project.updated_date = datetime.now()
        self.project_repository.update(project)
```

---

## MCP Tools

### 1. create_slr_project

```python
@server.call_tool()
async def handle_create_slr_project(
    name: str,
    description: str,
    file_path: Optional[str] = None,
    research_questions: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Create new SLR project with folder structure.
    
    Args:
        name: Project name (slug format, e.g., "software-designs")
        description: Project description
        file_path: Optional path to project description file (.pdf or .md)
        research_questions: Optional list of research questions
    
    Returns:
        Success message with project details
    
    Examples:
        # From PDF
        create_slr_project(
            name="software-designs",
            description="SLR on design patterns",
            file_path="projects/software-designs/description.pdf"
        )
        
        # From Markdown
        create_slr_project(
            name="cloud-security",
            description="Cloud security analysis",
            file_path="projects/cloud-security/project.md"
        )
        
        # Manual
        create_slr_project(
            name="ai-ethics",
            description="AI ethics in healthcare",
            research_questions=["RQ1: What are ethical concerns?"]
        )
    """
```

### 2. upload_paper_to_project

```python
@server.call_tool()
async def handle_upload_paper_to_project(
    file_path: str,
    project_name: str,
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    auto_extract_metadata: bool = True
) -> List[TextContent]:
    """
    Upload paper to specific SLR project.
    
    Paper will be stored in: projects/{project_name}/papers/screening/
    """
```

### 3. list_project_papers

```python
@server.call_tool()
async def handle_list_project_papers(
    project_name: str,
    status_filter: Optional[str] = None,  # "screening", "included", "excluded"
    limit: int = 50
) -> List[TextContent]:
    """Get papers for specific project, optionally filtered by status."""
```

### 4. move_paper_status

```python
@server.call_tool()
async def handle_move_paper_status(
    paper_id: int,
    new_status: str,  # "included", "excluded", "screening"
    notes: Optional[str] = None,
    reviewer: Optional[str] = None
) -> List[TextContent]:
    """
    Change paper screening status and move to appropriate folder.
    
    Example: Move from screening to included after title/abstract screening.
    """
```

### 5. get_project_structure

```python
@server.call_tool()
async def handle_get_project_structure(
    project_name: str,
    include_counts: bool = True
) -> List[TextContent]:
    """
    Get folder structure for project with file counts.
    
    Returns tree view showing:
    - Folder hierarchy
    - File counts in each folder
    - Project statistics
    """
```

### 6. generate_project_report

```python
@server.call_tool()
async def handle_generate_project_report(
    project_name: str,
    report_type: str = "progress",  # "progress", "prisma", "final"
    output_format: str = "markdown"  # "markdown", "pdf", "html"
) -> List[TextContent]:
    """Generate project report (progress, PRISMA flow, or final)."""
```

---

## User Workflow Example

### Scenario: Software Design Patterns SLR

**Step 1: Create Project (Option A - PDF)**
```python
# Student places software-designs.pdf in projects/software-designs/
# Then calls MCP tool:

create_slr_project(
    name="software-designs",
    file_path="projects/software-designs/software-designs.pdf"
)

# System automatically:
# - Extracts title: "Software Design Patterns: A Systematic Review"
# - Extracts RQs: ["RQ1: What are the most common design patterns?", ...]
# - Creates folder structure
# - Generates project.json
# - Creates templates
```

**Step 1: Create Project (Option B - Markdown)**
```python
# Student creates software-designs.md with YAML frontmatter:
# ---
# title: "Software Design Patterns: A Systematic Review"
# research_questions:
#   - "RQ1: What are the most common design patterns?"
#   - "RQ2: How do patterns affect code quality?"
# pico:
#   population: "Software development projects"
#   intervention: "Design pattern adoption"
#   outcome: "Code quality metrics"
# ---
#
# ## Background
# Design patterns are reusable solutions...

create_slr_project(
    name="software-designs",
    file_path="projects/software-designs/software-designs.md"
)

# System automatically:
# - Parses YAML frontmatter
# - Extracts title, RQs, PICO from frontmatter
# - Falls back to markdown section parsing if no frontmatter
# - Creates folder structure
# - Generates project.json
# - Creates templates
```

**Step 2: Upload Papers**
```python
# Upload paper to project
upload_paper_to_project(
    file_path="/downloads/paper1.pdf",
    project_name="software-designs",
    auto_extract_metadata=True
)

# Paper is stored at:
# projects/software-designs/papers/screening/paper1.pdf
```

**Step 3: Screen Papers**
```python
# After reading, mark paper as included
move_paper_status(
    paper_id=1,
    new_status="included",
    notes="Relevant study on Factory pattern",
    reviewer="student123"
)

# Paper moves from screening/ to included/
```

**Step 4: Track Progress**
```python
# Check project status
get_project_structure("software-designs")

# Output:
# projects/software-designs/
# ├── papers/ (45 total)
# │   ├── screening/ (30 papers)
# │   ├── included/ (10 papers)
# │   └── excluded/ (5 papers)
# ├── search-strategies/ (3 queries)
# ├── quality-assessment/ (5 assessed)
# └── reports/ (2 progress reports)
```

**Step 5: Generate Report**
```python
# Create progress report
generate_project_report(
    project_name="software-designs",
    report_type="progress",
    output_format="markdown"
)

# Generates: projects/software-designs/reports/progress-2025-10-17.md
```

---

## Benefits

### For Students
1. **Organized Workspace**: One folder per project, all artifacts together
2. **Automatic Setup**: No manual folder creation
3. **Clear Structure**: Follows academic SLR methodology
4. **Easy Tracking**: See project progress at a glance
5. **Professional Output**: Templates and reports ready for submission

### For Developers
1. **Clean Architecture**: Builds on Phase 3 refactoring
2. **Backward Compatible**: Existing code keeps working
3. **Testable**: Helper methods are independently testable
4. **Extensible**: Easy to add new project types/templates
5. **Maintainable**: Clear separation of concerns

### For the System
1. **Better Organization**: Papers organized by context
2. **Easier Backups**: One project = one folder
3. **Multi-Project Support**: Multiple concurrent SLRs
4. **Collaboration Ready**: Clear ownership and team structure
5. **Audit Trail**: Project history tracked

---

## Migration Strategy

### For Existing Papers

**Option 1: Leave in Place**
- Keep existing papers in `papers/` folder
- New papers go to project folders
- No disruption

**Option 2: Migrate to "Default" Project**
```python
# Create default project for existing papers
create_slr_project(
    name="legacy-papers",
    description="Papers uploaded before project organization"
)

# Migrate existing papers
migrate_papers_to_project(
    project_name="legacy-papers",
    paper_ids=[1, 2, 3, ...]  # Or "all"
)
```

**Option 3: Manual Project Assignment**
- Student reviews existing papers
- Assigns to appropriate projects
- Papers moved to project folders

---

## Configuration

### Settings

```python
# config.py or environment variables

# Project organization
PROJECT_BASED_STORAGE = True  # Enable project-based organization
DEFAULT_PROJECT_NAME = "default"  # Default project for backward compatibility

# Folder structure
PROJECT_BASE_PATH = "projects"
PAPERS_BASE_PATH = "papers"  # For non-project papers

# Templates
PROJECT_TEMPLATES_PATH = "templates/projects"
CUSTOM_TEMPLATES_ENABLED = True

# File extraction
ENABLE_FILE_METADATA_EXTRACTION = True
SUPPORTED_PROJECT_FILE_TYPES = [".pdf", ".md", ".markdown"]
OCR_ENABLED = False  # For scanned PDFs
RESEARCH_QUESTION_PATTERNS = ["RQ\\d+:", "Research Question \\d+:"]

# Markdown parsing
ENABLE_YAML_FRONTMATTER = True
MARKDOWN_SECTION_EXTRACTION = True

# Limits
MAX_PROJECTS = 100
MAX_PAPERS_PER_PROJECT = 10000
```

---

## Testing Strategy

### Unit Tests
1. **ProjectService**
   - Project creation
   - Folder initialization
   - Metadata extraction
   - Template generation

2. **Modified upload_paper**
   - Project-based storage
   - Path determination
   - File copying
   - Statistics updates

3. **Paper Lifecycle**
   - Status transitions
   - File movements
   - History tracking

### Integration Tests
1. **End-to-End Project Creation**
   - Create project from PDF
   - Upload papers
   - Screen papers
   - Generate reports

2. **Multi-Project Scenarios**
   - Multiple concurrent projects
   - Paper assignment
   - Project isolation

3. **Migration**
   - Legacy paper migration
   - Backward compatibility

### MCP Tool Tests
1. Test each tool independently
2. Test tool workflows
3. Test error handling

---

## Next Steps

### Immediate (Week 1)
1. ✅ Review and approve this design document
2. ✅ Create Phase 1 implementation branch
3. ✅ Implement Project model and repository
4. ✅ Write database migration script
5. ✅ Create unit tests

### Short Term (Week 2-3)
1. ✅ Implement PDF extraction
2. ✅ Create project initialization service
3. ✅ Expose MCP tools
4. ✅ Update upload_paper for project support
5. ✅ Test with real PDF

### Long Term (Week 4+)
1. ✅ Advanced features (reporting, etc.)
2. ✅ Documentation updates
3. ✅ User guide for students
4. ✅ Video tutorials

---

## Conclusion

This project-based organization:
- ✅ Solves the student's immediate need (organized project folders)
- ✅ Follows SLR best practices (PRISMA methodology)
- ✅ Builds on Phase 3 refactoring (clean architecture)
- ✅ Maintains backward compatibility (existing code works)
- ✅ Provides clear migration path (phases 1-4)
- ✅ Enables future enhancements (collaboration, templates, etc.)

**Recommendation**: Proceed with Phase 1 implementation.

---

**Document Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: Ready for Implementation
