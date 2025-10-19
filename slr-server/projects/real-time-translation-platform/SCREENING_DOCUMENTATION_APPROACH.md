# SLR Screening Documentation - Correct Approach

## Project Structure Overview

```
projects/real-time-translation-platform/
├── papers/                    ← Individual papers organized by status
│   ├── included/              ← Papers passing screening
│   ├── excluded/              ← Papers not meeting criteria
│   └── uncertain/             ← Papers needing discussion
│
├── screening/                 ← Screening process & decisions
│   ├── title-abstract/        ← T&A screening phase
│   │   ├── decisions/         ← Individual decision records
│   │   ├── screening_decisions.md    ← Master T&A report
│   │   └── RESULTS_SUMMARY.md        ← Quick summary
│   │
│   ├── full-text/             ← Full-text screening phase
│   │   ├── decisions/         ← Individual decision records
│   │   ├── screening_decisions.md    ← Master full-text report
│   │   └── agreements.md             ← Reviewer agreement tracking
│   │
│   ├── screening_protocol.md          ← Procedures
│   ├── screening_progress_tracker.md  ← Progress tracking
│   └── bulk_screening_workflow.md     ← Workflow documentation
│
├── quality-assessment/        ← Quality evaluation
│   ├── decisions/             ← Individual assessments
│   └── report.md              ← Summary report
│
├── data-extraction/           ← Data synthesis
│   ├── extracted_data/        ← Extracted information
│   └── synthesis.md           ← Analysis results
│
└── reports/                   ← Final reports
    └── SLR_Report_v1.md       ← Final report
```

---

## Correct Approach for Saving Screening Decisions

### Phase 1: Title-Abstract Screening

#### Document Strategy

**Step 1: Individual Decision Record**
- **Location**: `screening/title-abstract/decisions/paper_{id}_reviewer_{reviewer_id}.json`
- **Format**: Structured JSON with all decision data
- **Purpose**: Audit trail and individual reviewer record

**Step 2: Master Screening Report**
- **Location**: `screening/title-abstract/screening_decisions.md`
- **Format**: Markdown table with all decisions
- **Purpose**: Overview of all T&A screening decisions

**Step 3: Summary Statistics**
- **Location**: `screening/title-abstract/RESULTS_SUMMARY.md`
- **Format**: Summary statistics and advancement rates
- **Purpose**: Quick reference for progress

#### File Structure for Individual Decisions

**Filename Pattern**: `paper_{paper_id}_reviewer_{reviewer_id}.json`

**Content Format**:
```json
{
  "paper_id": 232,
  "title": "Adapting Translation Models for Transcript Disfluency Detection",
  "reviewer_id": "reviewer1",
  "stage": "title_abstract",
  "decision": "include|exclude|uncertain",
  "confidence_level": 0.85,
  "reason": "Clear reasoning for decision",
  "inclusion_criteria_met": ["IC1_EMPIRICAL", "IC2_ARCHITECTURE", "IC5_NEURAL"],
  "exclusion_criteria_met": [],
  "exclusion_reason": null,
  "timestamp": "2025-10-19T10:30:00Z",
  "notes": "Any additional notes"
}
```

### Phase 2: Full-Text Screening

**Same Structure** as Title-Abstract but in `screening/full-text/decisions/`

Additional fields:
```json
{
  "quality_score": 8.5,
  "methodology_appropriate": true,
  "data_quality": "high",
  "results_clearly_reported": true,
  "limitations_acknowledged": true
}
```

---

## MCP Tool Integration for Saving Decisions

### Using `screen_paper` MCP Tool

The `screen_paper` MCP tool automatically saves decisions to the database. To also save to files:

#### Approach 1: Manual File Saving (Recommended for Complete Audit Trail)

After calling `screen_paper` MCP tool:

```bash
# Step 1: Get paper via get_paper MCP tool
get_paper(paper_id=232)

# Step 2: Record decision via screen_paper MCP tool
screen_paper(
  project_id=1,
  paper_id=232,
  reviewer_id="reviewer1",
  stage="title_abstract",
  decision="include",
  confidence_level=0.85,
  reason="..."
)

# Step 3: Save structured record to file
# File: screening/title-abstract/decisions/paper_232_reviewer_reviewer1.json
{
  "paper_id": 232,
  "reviewer_id": "reviewer1",
  "decision": "include",
  "confidence_level": 0.85,
  "timestamp": "2025-10-19T10:30:00Z",
  "reason": "..."
}
```

#### Approach 2: Generate Report from Database

Use `get_slr_progress` MCP tool to fetch all decisions and generate comprehensive report:

```bash
# Get progress and all decisions
get_slr_progress(project_id=1)

# Generate markdown report from database results
# Output: screening/title-abstract/screening_decisions.md
```

---

## Recommended File Organization

### For Each Screening Phase

**Create Subdirectory**: `decisions/`

```
screening/title-abstract/
├── decisions/
│   ├── paper_232_reviewer_reviewer1.json
│   ├── paper_232_reviewer_reviewer2.json
│   ├── paper_233_reviewer_reviewer1.json
│   └── ...
├── screening_decisions.md (Master report)
└── RESULTS_SUMMARY.md (Quick reference)
```

### JSON Decision Record Template

Create `screening/title-abstract/decisions/TEMPLATE.json`:

```json
{
  "screening_id": "screening_1_232_1760854621",
  "project_id": 1,
  "paper_id": 232,
  "title": "Paper Title",
  "authors": ["Author1", "Author2"],
  "publication_year": 2019,
  "reviewer_id": "reviewer1",
  "review_stage": "title_abstract",
  "decision": "include",
  "confidence_level": 0.85,
  "reason": "Reasoning for decision",
  "inclusion_criteria_met": {
    "IC1_EMPIRICAL": true,
    "IC2_ARCHITECTURE": true,
    "IC3_REALTIME": false,
    "IC4_MULTILINGUAL": false,
    "IC5_NEURAL": true,
    "IC6_SCALABILITY": false,
    "IC7_EVALUATION": true,
    "IC8_PEERREVIEWED": true
  },
  "exclusion_criteria_met": {
    "EC1_STATISTICAL": false,
    "EC2_TEXTONLY": false,
    "EC3_INSUFFICIENT": false,
    "EC4_QUALITY": false,
    "EC5_THEORETICAL": false,
    "EC6_OUTOFSCOPE": false,
    "EC7_GRAYLITERATURE": false,
    "EC8_NOACCESS": false
  },
  "exclusion_reason": null,
  "timestamp": "2025-10-19T10:30:00Z",
  "updated_at": "2025-10-19T10:30:00Z",
  "notes": "Any additional notes or observations"
}
```

---

## Master Report Format

### Location
`screening/title-abstract/screening_decisions.md`

### Structure

```markdown
# Title-Abstract Screening Results

**Date**: October 19, 2025
**Phase**: Title-Abstract Screening (Stage 1 of 3)
**Total Papers Reviewed**: 104

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|-----------|
| INCLUDE | 64 | 61.5% |
| EXCLUDE | 12 | 11.5% |
| UNCERTAIN | 28 | 26.9% |
| TOTAL | 104 | 100% |

## Reviewer Decisions

| Paper ID | Title | Reviewer1 | Reviewer2 | Agreement | Final Decision |
|----------|-------|-----------|-----------|-----------|------------------|
| 232 | Adapting Translation Models... | INCLUDE (0.85) | INCLUDE (0.90) | ✅ Yes | INCLUDE |
| 233 | Open Source Toolkit... | EXCLUDE (0.95) | PENDING | ⏳ Awaiting | PENDING |
| 231 | Breaking the Data Barrier... | UNCERTAIN (0.55) | PENDING | ⏳ Awaiting | PENDING |

## Included Papers (64)

[Detailed list of included papers with reasoning]

## Excluded Papers (12)

[Detailed list with exclusion reasons]

## Uncertain Papers (28)

[Papers requiring team discussion]

## Inter-Rater Agreement

- Cohen's Kappa: [calculated value]
- Agreement Rate: [percentage]
- Conflicts to Resolve: [number]

## Next Steps

1. Obtain second reviewer decisions
2. Resolve disagreements
3. Advance included papers to full-text screening
```

---

## Complete Workflow with MCP Tools

### Step-by-Step Process

#### 1. **Get Paper Information**
```
Tool: mcp_slr-server_get_paper
Input: paper_id=232
Output: Complete paper metadata, abstract, full text
File: No file created (data in response)
```

#### 2. **Record Screening Decision**
```
Tool: mcp_slr-server_screen_paper
Input: 
  - paper_id=232
  - reviewer_id="reviewer1"
  - decision="include"
  - confidence_level=0.85
Output: Confirmation that decision saved to database
File Created: screening/title-abstract/decisions/paper_232_reviewer_reviewer1.json
```

#### 3. **Generate Summary Report**
```
Tool: mcp_slr-server_get_slr_progress
Input: project_id=1
Output: Progress dashboard with all decisions
File Updated: screening/title-abstract/screening_decisions.md
```

#### 4. **Check Agreement**
```
Tool: mcp_slr-server_calculate_inter_rater_reliability
Input: paper_ids=[232, 233, 231], reviewer_ids=["reviewer1", "reviewer2"]
Output: Cohen's Kappa and agreement statistics
File: screening/title-abstract/AGREEMENT_ANALYSIS.md
```

---

## File Saving Strategy

### Automated (Via MCP Tools)

1. **Database Storage** ← Primary storage via `screen_paper` tool
2. **Progress Dashboard** ← Updated via `get_slr_progress` tool
3. **Master Report** ← Generated from database

### Manual (For Audit Trail)

1. **Individual Decisions** ← Save JSON to `decisions/` folder
2. **Markdown Reports** ← Generate summaries
3. **Statistics** ← Save metrics and analysis

### Recommended Hybrid Approach

```
📊 Database (MCP Tools)
    ├── Primary storage
    ├── Real-time updates
    └── Query-based reporting

📁 File System
    ├── Audit trail (JSON decisions)
    ├── Markdown reports
    ├── Analysis artifacts
    └── Version history
```

---

## Implementation Example

### Complete Workflow

**Goal**: Screen 3 papers and save decisions correctly

```bash
# 1. List papers
mcp_slr-server_list_papers(limit=3, offset=0)
   → Papers: 232, 233, 231

# 2. Get paper 232
mcp_slr-server_get_paper(paper_id=232)
   → Response: Full paper info

# 3. Screen paper 232 (Reviewer 1)
mcp_slr-server_screen_paper(
  project_id=1,
  paper_id=232,
  reviewer_id="reviewer1",
  stage="title_abstract",
  decision="include",
  confidence_level=0.85,
  reason="Clear empirical study on S2ST with neural approaches"
)
   → ✅ Decision saved to database
   → Create: screening/title-abstract/decisions/paper_232_reviewer_reviewer1.json

# 4. Screen paper 232 (Reviewer 2)
mcp_slr-server_screen_paper(
  project_id=1,
  paper_id=232,
  reviewer_id="reviewer2",
  stage="title_abstract",
  decision="include",
  confidence_level=0.90,
  reason="Strong match for platform design focus"
)
   → ✅ Decision saved to database
   → Create: screening/title-abstract/decisions/paper_232_reviewer_reviewer2.json

# 5. Check agreement
mcp_slr-server_calculate_inter_rater_reliability(
  paper_ids=[232],
  reviewer_ids=["reviewer1", "reviewer2"]
)
   → Kappa = 1.0 (perfect agreement on inclusion)

# 6. Get progress
mcp_slr-server_get_slr_progress(project_id=1)
   → Update: screening/title-abstract/screening_decisions.md
   → Update: screening/title-abstract/RESULTS_SUMMARY.md

# 7. Generate final report
mcp_slr-server_generate_slr_report(
  paper_ids=[232, 233, 231],
  output_path="screening/title-abstract/FINAL_REPORT.md"
)
   → Create: screening/title-abstract/FINAL_REPORT.md
```

---

## Folder Structure Creation

```bash
# Create decision folders
mkdir -p screening/title-abstract/decisions
mkdir -p screening/full-text/decisions
mkdir -p quality-assessment/decisions
mkdir -p data-extraction/extracted_data

# Create tracking files
touch screening/title-abstract/AGREEMENT_ANALYSIS.md
touch screening/title-abstract/CONFLICT_LOG.md
touch quality-assessment/assessment_summary.md
```

---

## Summary: Best Practice Approach

### ✅ DO

- ✅ Use `screen_paper` MCP tool as primary decision recorder
- ✅ Save individual JSON decisions for audit trail
- ✅ Generate markdown reports from database data
- ✅ Use consistent naming: `paper_{id}_reviewer_{reviewer_id}.json`
- ✅ Create `decisions/` subdirectory for each phase
- ✅ Update master reports after each batch
- ✅ Track inter-rater agreement metrics
- ✅ Document conflicting decisions clearly

### ❌ DON'T

- ❌ Only save to files without database
- ❌ Duplicate decision data in multiple formats
- ❌ Manually create reports without using tools
- ❌ Skip agreement calculations
- ❌ Mix different decision formats
- ❌ Lose audit trail of individual decisions
- ❌ Save decisions without timestamps

---

## Location Reference

**Project Root**: `C:\github\mcp-servers\slr-server\projects\real-time-translation-platform\`

**Screening Folder**: `screening/`

**T&A Phase**:
- Decisions: `screening/title-abstract/decisions/`
- Master Report: `screening/title-abstract/screening_decisions.md`
- Summary: `screening/title-abstract/RESULTS_SUMMARY.md`

**Full-Text Phase**:
- Decisions: `screening/full-text/decisions/`
- Master Report: `screening/full-text/screening_decisions.md`

**Quality Phase**:
- Decisions: `quality-assessment/decisions/`
- Report: `quality-assessment/assessment_summary.md`

---

**Approach**: Hybrid (Database + File System)  
**Primary Storage**: MCP Database  
**Audit Trail**: JSON Files  
**Reports**: Markdown Generated from Database
