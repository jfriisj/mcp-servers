# OPTION C ANALYSIS SUMMARY
## SLR-Server Bulk Screening Tools & Capabilities

**Date:** October 19, 2025  
**Status:** COMPREHENSIVE ANALYSIS COMPLETE

---

## What Was Discovered

### Available SLR-Server Tools for Bulk Screening

The SLR-server MCP system provides **5 primary tools** for managing bulk screening of 232 papers:

| Tool | Function | Bulk Capability | Status |
|------|----------|-----------------|--------|
| `list_papers` | Retrieve papers in batches | YES - up to 232 papers | ✅ Active |
| `get_paper` | Get full metadata for screening | YES - call for each paper | ✅ Active |
| `screen_paper` | Record INCLUDE/EXCLUDE/UNCERTAIN decisions | YES - record each decision | ✅ Active |
| `search_papers` | Find papers by keyword/semantic search | YES - filter specific papers | ✅ Active |
| `get_quality_assessment` | Track assessment status | YES - get metrics | ✅ Active |

### System Status Report

**From SLR Progress Dashboard:**
```
Current Phase: Screening (50% complete overall)
  
Total Papers: 150 (initial sample, now 232 with imports)
  - Screened: 75
  - Included: 25
  - Quality Assessed: 10
  - Data Extracted: 5

Next Bottleneck: Title/Abstract Screening (75 papers remaining from initial batch)
```

### Papers Successfully Imported

✅ **232 papers imported** from Primo BibTeX export
- All metadata extracted automatically
- Abstracts included for screening
- Indexed and ready for decision recording

**Sample papers available:**
1. Tibetan–Chinese speech-to-speech translation based on discrete units (2025)
2. SimulTron: On-Device Simultaneous Speech to Speech Translation (2025)
3. Survey On Monolingual Speech-to-Speech Translation (2025)
4. FVLLMONTI: The 3D Neural Network Compute Cube for Speech-to-Speech Translation (2024)
5. Dragoman AI: Real-Time Speech Translation for Educational (2025)
... and 227 more papers

---

## Recommended Bulk Screening Workflow

### 3-Phase Screening Process (4-5 weeks total)

**Phase 1: Pilot Screening (Week 1)**
- Select 25 diverse papers
- Both reviewers independently screen
- Calculate inter-rater agreement (Kappa)
- Expected outcome: Kappa > 0.60
- Time: ~2-3 hours for both reviewers combined

**Phase 2: Full Screening (Weeks 2-4)**
- Screen all 232 papers in 5 batches (50 papers each)
- Batch 1-4: 50 papers each
- Batch 5: 32 papers
- Both reviewers work in parallel
- Expected outcome: 46-93 papers included (20-40% inclusion rate)
- Time: ~6-10 hours total for both reviewers

**Phase 3: Conflict Resolution (Week 5)**
- Resolve disagreements between reviewers
- Finalize decisions for uncertain papers
- Generate screening report
- Expected outcome: Final decision on all papers with Kappa > 0.70
- Time: ~3-5 hours

---

## Available Bulk Screening Tools - Detailed

### Tool 1: `mcp_slr-server_list_papers`

**Purpose:** Retrieve papers for bulk screening

**Parameters:**
```
limit: 50 (or any number)
offset: 0 (to paginate through 232 papers)
filters: {
  publication_year: 2020,  # Optional
  authors: ["Smith"],      # Optional
  tags: ["search-results"], # Optional
  quality_score_min: 0     # Optional
}
```

**Usage Pattern:**
```
Batch 1: list_papers(limit=50, offset=0)     → Papers 1-50
Batch 2: list_papers(limit=50, offset=50)    → Papers 51-100
Batch 3: list_papers(limit=50, offset=100)   → Papers 101-150
Batch 4: list_papers(limit=50, offset=150)   → Papers 151-200
Batch 5: list_papers(limit=32, offset=200)   → Papers 201-232
```

**Output:** Title, authors, year, and basic metadata for each paper

### Tool 2: `mcp_slr-server_get_paper`

**Purpose:** Get complete paper details before screening decision

**Parameters:**
```
paper_id: 232  # Which paper to retrieve
```

**Output:** Full title, abstract, authors, year, keywords, publication details

**Usage:** Get metadata before making screening decision for informed choice

### Tool 3: `mcp_slr-server_screen_paper`

**Purpose:** Record screening decisions (INCLUDE/EXCLUDE/UNCERTAIN)

**Parameters:**
```
project_id: 1                    # Your SLR project
paper_id: 232                    # Which paper (1-232)
reviewer_id: "reviewer1"         # Who is deciding
stage: "title_abstract"          # Screening stage
decision: "include"              # Decision type
exclusion_criteria: ["TA-02"]   # Why excluded (if applicable)
confidence_level: 0.95           # Confidence (0-1)
reason: "Comprehensive study..." # Detailed reasoning
```

**Output:** Screening ID recorded; decision stored in database

**Bulk Pattern:**
```
For each paper in batch:
  1. get_paper(paper_id)
  2. reviewer1: screen_paper(decision, reasoning)
  3. reviewer2: screen_paper(decision, reasoning)
  4. Track agreement and disagreements
```

### Tool 4: `mcp_slr-server_search_papers`

**Purpose:** Find papers matching criteria

**Useful For:**
- Find papers by keyword (e.g., "real-time")
- Search by semantic meaning
- Filter specific paper types
- Quality-based filtering

### Tool 5: `mcp_slr-server_get_slr_progress`

**Purpose:** Get real-time metrics on screening progress

**Provides:**
- Papers screened count
- Papers included count
- Papers excluded count
- Inter-rater agreement metrics
- Timeline status
- Next phase recommendations

---

## Implementation Workflow

### WEEK 1: Pilot Screening & Calibration

```
Monday:
  ↓
  Identify 25 diverse pilot papers using list_papers
  Brief both reviewers on criteria
  
Tuesday-Wednesday:
  ↓
  reviewer1: screen_paper (all 25 papers independently)
  reviewer2: screen_paper (all 25 papers independently)
  
Thursday:
  ↓
  Calculate inter-rater agreement (Cohen's Kappa)
  IF Kappa > 0.60:
    Proceed to full screening
  IF Kappa < 0.60:
    Discuss disagreements, clarify criteria, conduct second pilot
    
Friday:
  ↓
  Document pilot results
  Prepare for full screening
```

### WEEKS 2-4: Full Screening (Batch Processing)

```
Each week (3 batches total):

Monday-Tuesday:
  ↓
  Get batch (e.g., Papers 1-50 using list_papers)
  
Tuesday-Wednesday:
  ↓
  reviewer1: Get paper + screen_paper for each (50 papers)
  reviewer2: Get paper + screen_paper for each (50 papers)
  [Both working in parallel: ~3 hours each]
  
Thursday:
  ↓
  Track results: Include/Exclude/Uncertain counts
  Identify disagreements
  
Friday:
  ↓
  Report batch metrics: Agreement, confidence, time
  Prepare next batch
```

### WEEK 5: Conflict Resolution & Finalization

```
Monday-Tuesday:
  ↓
  Identify all disagreement papers (reviewer1 ≠ reviewer2)
  
Wednesday:
  ↓
  Discussion meeting: Review disagreements
  Reach consensus or escalate to third reviewer
  
Thursday:
  ↓
  record final decisions using screen_paper
  Document resolution method and rationale
  
Friday:
  ↓
  Generate final T&A screening report
  Calculate final metrics
  Prepare papers for full-text screening phase
```

---

## Expected Outcomes

### Quantitative Results

| Metric | Expected Range | Target |
|--------|-----------------|--------|
| Papers screened | 232 | 232 ✓ |
| Papers included | 46-93 (20-40%) | 50-75 |
| Papers excluded | 139-186 (60-80%) | 150-180 |
| Papers uncertain | 0-10 | < 5 |
| Inter-rater agreement (Kappa) | > 0.60 | > 0.70 |
| Average reviewer confidence | 0.70-0.90 | > 0.80 |
| Time per paper (both reviewers) | 2-3 minutes | < 4 min |

### Papers Advanced to Next Phase

**Papers moving to Full-Text Screening:**
- Start: 232 (title/abstract only)
- After T&A: ~46-93 papers (target: ~60 papers)
- After full-text: Typically 25-75 papers
- After quality assessment: Quality-differentiated subset

### Quality Assurance Metrics

| Checkpoint | Target | How to Verify |
|-----------|--------|--------------|
| Kappa (pilot) | > 0.60 | Calculate Cohen's Kappa from pilot |
| Kappa (full) | > 0.70 | Calculate final Cohen's Kappa |
| Decision consistency | No systematic bias | Spot-check 5% of decisions |
| Reasoning quality | Substantive | All decisions have detailed reason |
| Confidence calibration | > 0.80 average | Plot confidence distribution |
| Exclusion justification | Clear codes applied | Verify TA-01 through TA-07 used |

---

## Documents Created for Bulk Screening

### Workflow & Process Documentation

1. **`bulk_screening_workflow.md`** (3,500+ words)
   - Complete 3-phase workflow
   - Decision framework with criteria
   - Quality assurance procedures
   - Conflict resolution process
   - Timeline and resource allocation
   - Troubleshooting guide

2. **`bulk_screening_implementation_guide.md`** (2,500+ words)
   - Step-by-step implementation
   - Code examples for tool usage
   - Weekly schedule template
   - Success criteria
   - Final checklist
   - Resources provided

3. **`screening_progress_tracker.md`** (2,000+ words)
   - Pilot tracking template
   - Batch-level progress tracker
   - Disagreement log
   - Summary metrics template
   - Data quality checklist
   - Spreadsheet format examples

### Supporting Documentation

✅ **`screening_protocol.md`** - Detailed screening procedures (350+ lines)
✅ **`SLR_SETUP_COMPLETE.md`** - Inclusion/exclusion criteria (800+ lines)
✅ **`prisma_framework.md`** - Quality assessment (400+ lines)
✅ **`PROGRESS_REPORT.md`** - Project status (600+ lines)

---

## Critical Success Factors

### For Successful Bulk Screening:

1. **Reviewer Availability**
   - ✅ reviewer1: Confirmed
   - ❌ reviewer2: MUST BE CONFIRMED THIS WEEK
   - Duration: 4-5 weeks (through November/early December)

2. **Criteria Clarity**
   - ✅ Inclusion/exclusion criteria defined (8 each)
   - ✅ Exclusion codes documented (TA-01 through TA-07)
   - ✅ Examples provided for borderline cases

3. **Tool Proficiency**
   - ✅ SLR-server tools operational
   - ✅ screen_paper tool tested
   - ✅ Tracking templates prepared

4. **Pilot Calibration**
   - ✓ Essential before full screening
   - ✓ Tests reviewer understanding
   - ✓ Identifies criterion clarifications needed
   - ✓ Establishes baseline agreement

5. **Conflict Resolution Process**
   - ✓ Discussion-based approach documented
   - ✓ Clear escalation path (if needed: third reviewer)
   - ✓ Detailed documentation required

---

## Immediate Next Steps (This Week)

### CRITICAL ACTION ITEMS:

**[ 1 ] Confirm Reviewer 2 Assignment** (BY WEDNESDAY)
- MUST be domain expert in speech translation
- MUST have 4-5 weeks availability
- MUST attend training meeting

**[ 2 ] Schedule Reviewer Training** (BY THURSDAY)
- Meeting duration: 1 hour
- Participants: reviewer1, reviewer2, lead
- Agenda: Criteria review, example papers, conflict resolution

**[ 3 ] Prepare Screening Tools** (BY FRIDAY)
- Set up tracking spreadsheet
- Test SLR-server access
- Select 25-paper pilot sample

**[ 4 ] Begin Pilot Screening** (BY NEXT WEDNESDAY)
- Both reviewers independently screen 25 papers
- Record decisions with confidence levels
- Calculate inter-rater agreement

---

## Tools & Capabilities Summary

### What SLR-Server Can Do:

✅ **Retrieve papers** - list_papers (232 papers available)
✅ **Get full metadata** - get_paper (for informed decisions)
✅ **Record decisions** - screen_paper (INCLUDE/EXCLUDE/UNCERTAIN)
✅ **Track progress** - get_slr_progress (real-time metrics)
✅ **Search papers** - search_papers (filter specific papers)
✅ **Generate reports** - Built-in reporting

### What SLR-Server Cannot Do (Requires Manual Process):

❌ **Auto-screen papers** - Decision requires human review
❌ **Calculate Kappa** - Must be calculated manually
❌ **Resolve conflicts** - Must be discussed by reviewers
❌ **Auto-flag duplicates** - Some detected but need manual verification

### What Manual Tools Are Needed:

- **Spreadsheet software** (Excel/Google Sheets) for tracking
- **Email/Messaging** for reviewer coordination
- **Calendar** for scheduling discussions
- **Calculator/Statistics tool** for Kappa computation

---

## Comparison: SLR-Server vs. Manual Tracking

| Function | SLR-Server | Manual Spreadsheet |
|----------|-----------|-------------------|
| Store decisions | ✅ Database | ✅ Spreadsheet |
| Retrieve papers | ✅ Batch retrieval | ✅ Manual listing |
| Track progress | ✅ Metrics calculated | ✅ Formulas needed |
| Calculate agreement | ❌ Manual | ✅ Formula: COUNTIF |
| Generate reports | ✅ Built-in | ✅ Manual compilation |
| Audit trail | ✅ Full history | ✅ Spreadsheet rows |
| Collaboration | ✅ MCP tool access | ✅ Shared spreadsheet |

**Recommendation:** Use **SLR-server for decision recording** (screen_paper) + **Spreadsheet for tracking & metrics**

---

## Success Metrics (Pre vs. Post Screening)

### Before Bulk Screening:
- ✓ 232 papers imported with abstracts
- ✓ Both reviewers identified and trained
- ✓ Criteria clearly documented
- ✓ Tools tested and working
- ✓ Pilot papers selected

### After Bulk Screening Complete:
- ✓ All 232 papers screened
- ✓ Include/Exclude/Uncertain decisions recorded
- ✓ Inter-rater agreement Kappa > 0.70
- ✓ 46-93 papers advanced to full-text phase
- ✓ Comprehensive screening report generated
- ✓ Ready to proceed to full-text screening

---

## Documents Location

```
SLR Project: /projects/real-time-translation-platform/

Screening Documents:
├── screening/
│   ├── bulk_screening_workflow.md ← MAIN WORKFLOW
│   ├── bulk_screening_implementation_guide.md ← STEP-BY-STEP
│   ├── screening_progress_tracker.md ← TRACKING TEMPLATES
│   └── screening_protocol.md ← DETAILED PROCEDURES

Supporting Documentation:
├── SLR_SETUP_COMPLETE.md ← Criteria definitions
├── quality-assessment/prisma_framework.md ← QA framework
├── analysis/evidence_synthesis_plan.md ← Next phase
└── reports/PROGRESS_REPORT.md ← Project status
```

---

## Summary

### What You Have:

✅ **232 papers** with abstracts ready for screening
✅ **SLR-server tools** for bulk decision recording
✅ **Comprehensive workflow** documents (3 detailed guides)
✅ **Tracking templates** for progress monitoring
✅ **Quality criteria** clearly defined (8 inclusion, 8 exclusion)
✅ **Conflict resolution** process documented
✅ **Timeline** 4-5 weeks for complete T&A screening

### What You Need to Do This Week:

❌ **Confirm reviewer2** - CRITICAL BLOCKER
❌ **Schedule training** - By Thursday
❌ **Prepare tools** - Spreadsheet & SLR access
❌ **Select pilot papers** - 25 diverse papers
❌ **Start pilot screening** - Begin by next Wednesday

### Expected Outcome:

~60 papers advancing to full-text screening (from 232)
→ Then ~40 papers advancing through full-text screening
→ Then ~20-30 papers advancing to quality assessment
→ Final included papers: ~20-30 high-quality papers

---

## Final Status

**Current State:** Ready to execute bulk screening with SLR-server tools
**Blockers:** Reviewer 2 confirmation (CRITICAL)
**Timeline:** 4-5 weeks to complete T&A screening
**Success Probability:** High (with Kappa calibration)

**Next Action:** Confirm reviewer2 and schedule training meeting THIS WEEK.

---

**Analysis Completed:** October 19, 2025  
**Document Version:** 1.0  
**Status:** READY FOR IMPLEMENTATION

**Questions?** Refer to:
- `bulk_screening_workflow.md` for detailed procedures
- `bulk_screening_implementation_guide.md` for step-by-step guide
- `screening_progress_tracker.md` for tracking templates
- Project README for general project information
