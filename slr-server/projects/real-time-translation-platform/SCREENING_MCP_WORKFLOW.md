# SLR Screening Workflow - MCP Integration Guide

## Architecture Overview

The workflow integrates MCP tools with automatic documentation generation to ensure every screening decision is recorded and documented in real-time.

```
MCP Tools (Input)          Processing         Documentation Output
┌──────────────────┐       ┌──────────┐       ┌────────────────────┐
│ list_papers()    │──────▶│ Reviewer │──────▶│ screening_log.json │
│ get_paper()      │       │ Decision │       │ screening_track.md │
│ screen_paper()   │       │ Process  │       │ results_summary.md │
│ get_slr_progress()       └──────────┘       │ decision_matrix.md │
└──────────────────┘                         └────────────────────┘
                                                       │
                                                       ▼
                                            Folder Structure:
                                            title-abstract/
                                              ├── logs/
                                              ├── decisions/
                                              ├── reports/
                                              └── summaries/
```

---

## Folder Structure & Documentation Strategy

### Project Root Structure
```
projects/real-time-translation-platform/
├── README.md                          # Project overview
├── screening/                         # Phase 1: Title-Abstract
│   ├── title-abstract/               # CURRENT PHASE
│   │   ├── logs/                     # Decision logs (JSON/CSV)
│   │   ├── decisions/                # Individual decision records
│   │   ├── reports/                  # Generated reports
│   │   ├── summaries/                # Summary documents
│   │   ├── screening_decisions.md    # Main results document
│   │   ├── screening_log.json        # Machine-readable log
│   │   └── screening_progress.csv    # Progress tracking
│   │
│   ├── full-text/                    # Phase 2: Full-Text Screening (future)
│   ├── final-selection/              # Phase 3: Final Selection (future)
│   └── screening_protocol.md         # Methodology & criteria
│
├── data-extraction/                  # Phase 3: Data Extraction
├── analysis/                         # Phase 4: Analysis & Synthesis
├── quality-assessment/               # Cross-cutting: Quality metrics
└── reports/                          # Final SLR reports
```

---

## Real-Time Documentation Workflow

### Step 1: Reviewer Gets Paper
```
COMMAND: mcp_slr-server_get_paper(paper_id=232)

OUTPUT LOGGED TO:
├── logs/paper_232_retrieved.json     # Timestamp, metadata
├── logs/retrieval_log.csv             # Append entry
└── summaries/papers_reviewed.md       # Update progress tracker
```

### Step 2: Reviewer Makes Decision
```
COMMAND: mcp_slr-server_screen_paper(
  paper_id=232,
  reviewer_id="reviewer1",
  decision="include",
  confidence_level=0.85,
  reason="..."
)

OUTPUT LOGGED TO:
├── logs/screening_232_reviewer1.json       # Full decision record
├── decisions/232_decision_record.md        # Human-readable format
├── screening_log.json                      # Append to master log
├── screening_progress.csv                  # Update progress row
├── screening_decisions.md                  # Update summary table
└── summaries/screening_stats.json          # Update statistics
```

### Step 3: Track Progress
```
COMMAND: mcp_slr-server_get_slr_progress(project_id=1)

OUTPUT LOGGED TO:
├── reports/progress_checkpoint_OCT19.md    # Timestamped checkpoint
├── screening_progress.csv                   # Update metrics row
└── summaries/current_metrics.json           # Update statistics
```

---

## File Format Specifications

### 1. Screening Log (screening_log.json)
Master machine-readable record of all screening decisions:

```json
{
  "project_id": 1,
  "project_name": "real-time-translation-platform",
  "screening_phase": "title_abstract",
  "log_generated": "2025-10-19T14:30:00Z",
  "total_papers_screened": 3,
  "decisions": [
    {
      "screening_id": "screening_1_232_1760854621",
      "paper_id": 232,
      "title": "Adapting Translation Models for Transcript Disfluency Detection",
      "year": 2019,
      "reviewer_id": "reviewer1",
      "stage": "title_abstract",
      "decision": "INCLUDE",
      "confidence_level": 0.85,
      "reason": "Directly addresses real-time speech translation with neural approaches...",
      "timestamp": "2025-10-19T14:20:00Z",
      "inclusions_met": ["IC1_EMPIRICAL", "IC2_ARCHITECTURE", "IC5_NEURAL"],
      "exclusions_triggered": []
    },
    {
      "screening_id": "screening_1_232_1760854627",
      "paper_id": 232,
      "reviewer_id": "reviewer2",
      "stage": "title_abstract",
      "decision": "INCLUDE",
      "confidence_level": 0.90,
      "reason": "Clear empirical study with transformer-based approach...",
      "timestamp": "2025-10-19T14:25:00Z",
      "agreement": true,
      "kappa_contribution": 1.0
    }
  ],
  "summary": {
    "total_decisions": 3,
    "include_count": 2,
    "exclude_count": 1,
    "uncertain_count": 0,
    "average_confidence": 0.90,
    "inter_rater_agreement": "PERFECT (2/2 pairs agree)"
  }
}
```

### 2. Individual Decision Record (decisions/{paper_id}_decision_record.md)
Human-readable record for each paper:

```markdown
# Paper Screening Decision Record

**Paper ID:** 232  
**Title:** Adapting Translation Models for Transcript Disfluency Detection  
**Year:** 2019  
**Authors:** Dong, Qianqian; Wang, Feng; Yang, Zhen; Chen, Wei; Xu, Shuang; Xu, Bo

---

## Reviewer 1 Decision

- **Reviewer:** reviewer1
- **Stage:** Title-Abstract Screening
- **Decision:** ✅ INCLUDE
- **Confidence:** 0.85
- **Timestamp:** 2025-10-19 14:20:00

### Reasoning
Directly addresses real-time speech translation with neural approaches and comprehensive evaluation.

### Criteria Assessment
- ✅ IC1_EMPIRICAL: Empirical evaluation with datasets
- ✅ IC2_ARCHITECTURE: Real-time S2ST platform design focus
- ✅ IC5_NEURAL: Transformer-based approach mentioned
- ✅ IC7_EVALUATION: Comprehensive multi-dataset evaluation

---

## Reviewer 2 Decision

- **Reviewer:** reviewer2
- **Stage:** Title-Abstract Screening
- **Decision:** ✅ INCLUDE
- **Confidence:** 0.90
- **Timestamp:** 2025-10-19 14:25:00

### Reasoning
Clear empirical study with transformer-based approach and multi-dataset evaluation. Strong fit for platform design focus.

### Agreement Status
✅ **AGREEMENT**: Both reviewers agree → INCLUDE

---

## Next Steps
- Advance to full-text screening phase
- Prepare for quality assessment
```

### 3. Screening Progress Tracker (screening_progress.csv)
Tab-delimited progress tracking:

```csv
paper_id,title,year,reviewer1_decision,reviewer1_conf,reviewer2_decision,reviewer2_conf,agreement,final_decision,status,timestamp
232,"Adapting Translation Models...",2019,INCLUDE,0.85,INCLUDE,0.90,TRUE,INCLUDE,SCREENED,2025-10-19T14:25:00Z
233,"Open Source Toolkit...",2018,EXCLUDE,0.95,PENDING,N/A,FALSE,PENDING,IN_PROGRESS,2025-10-19T14:30:00Z
231,"Breaking the Data Barrier...",2019,UNCERTAIN,0.55,PENDING,N/A,FALSE,PENDING,WAITING,2025-10-19T14:35:00Z
```

### 4. Screening Statistics (summaries/screening_stats.json)
Real-time metrics:

```json
{
  "phase": "title_abstract",
  "timestamp": "2025-10-19T14:35:00Z",
  "papers_total": 104,
  "papers_screened": 3,
  "papers_pending": 101,
  "decisions": {
    "include": 2,
    "exclude": 1,
    "uncertain": 0
  },
  "percentages": {
    "include_pct": 66.7,
    "exclude_pct": 33.3,
    "uncertain_pct": 0.0
  },
  "quality_metrics": {
    "average_confidence": 0.90,
    "pairs_screened": 2,
    "pairs_agreeing": 2,
    "kappa": 1.0
  },
  "progress": {
    "completion_pct": 2.9,
    "estimated_remaining_hours": 8.5,
    "papers_per_hour": 3.5
  }
}
```

### 5. Main Summary Report (screening_decisions.md)
High-level summary with tables (already generated):

```markdown
# Title-Abstract Screening Results

**Date:** October 19, 2025  
**Total Screened:** 104 papers  
**Status:** In Progress

## Summary
- ✅ INCLUDE: 64 papers (61.5%)
- ❌ EXCLUDE: 12 papers (11.5%)
- ❓ UNCERTAIN: 28 papers (26.9%)

[Full tables and details...]
```

---

## Implementation Strategy

### Phase 1: During Screening (Real-Time)

For each paper screened:

```
1. Reviewer calls: get_paper(paper_id)
   └─► Log: logs/paper_{id}_retrieved.json

2. Reviewer makes decision via: screen_paper(...)
   └─► Log: logs/screening_{id}_reviewer{#}.json
   └─► Create: decisions/{paper_id}_decision_record.md (after all reviewers)
   └─► Append: screening_log.json
   └─► Update: screening_progress.csv
   └─► Update: screening_stats.json

3. Periodically call: get_slr_progress()
   └─► Log: reports/progress_checkpoint_{timestamp}.md
   └─► Update: summaries/current_metrics.json
```

### Phase 2: Batch Processing (End of Each Day)

Generate daily summary:

```
generate_daily_report():
  ├─ Compile all decisions from logs/
  ├─ Generate: reports/daily_summary_{DATE}.md
  ├─ Update: screening_decisions.md (main report)
  ├─ Calculate: inter-rater agreement (Cohen's Kappa)
  └─ Generate: alerts for disagreements
```

### Phase 3: Conflict Resolution (Weekly)

```
resolve_conflicts():
  ├─ Identify: Papers where reviewer1 ≠ reviewer2
  ├─ Log: decisions/{paper_id}_conflict_discussion.md
  ├─ Record: Final decision (with resolution method)
  └─ Update: screening_log.json (final_decision field)
```

---

## MCP Command Workflow Template

### For Reviewer Using CLI/API

```bash
# Start screening session
PROJECT_ID=1
REVIEWER_ID="reviewer1"

# Loop through papers
for paper_id in {232,233,231,...}; do
  # 1. Retrieve paper
  mcp_slr-server_get_paper(paper_id=$paper_id)
  
  # 2. Make decision (via reviewer input)
  mcp_slr-server_screen_paper(
    project_id=$PROJECT_ID,
    paper_id=$paper_id,
    reviewer_id=$REVIEWER_ID,
    stage="title_abstract",
    decision="include",  # or "exclude", "uncertain"
    confidence_level=0.85,
    reason="..."
  )
  
  # 3. Log automatically saved to:
  #    - logs/screening_{paper_id}_{reviewer_id}.json
  #    - decisions/{paper_id}_decision_record.md (after both reviewers)
  #    - screening_log.json (appended)
  #    - screening_progress.csv (row updated)
  #    - screening_stats.json (metrics updated)
done

# Periodically check progress
mcp_slr-server_get_slr_progress(project_id=$PROJECT_ID)
```

---

## Documentation Auto-Generation Features

### 1. Decision Record Generator
After both reviewers screen same paper:
- ✅ Auto-generates `decisions/{paper_id}_decision_record.md`
- ✅ Compares reviewer decisions
- ✅ Calculates agreement/disagreement
- ✅ Flags conflicts for team discussion

### 2. Progress Report Generator
On demand or daily:
- ✅ Compiles `screening_decisions.md` from logs
- ✅ Generates tables (INCLUDE/EXCLUDE/UNCERTAIN)
- ✅ Calculates statistics
- ✅ Estimates timeline

### 3. Metrics Tracker
Real-time updates:
- ✅ Papers screened vs. total
- ✅ Average confidence levels
- ✅ Inter-rater agreement (Cohen's Kappa)
- ✅ Screening velocity (papers/hour)
- ✅ Estimated completion time

### 4. Conflict Resolution Logger
When reviewers disagree:
- ✅ Auto-logs conflict to `decisions/{paper_id}_conflict_discussion.md`
- ✅ Tracks resolution method
- ✅ Records final consensus decision
- ✅ Updates kappa calculations

---

## Integration with SLR Server

### Recommended Implementation

Add to `mcp_handler.py`:

```python
class ScreeningDocumentationHandler:
    """Auto-generates documentation during screening."""
    
    async def handle_screen_paper_with_docs(self, arguments):
        """Record decision AND auto-generate documentation."""
        
        # 1. Record decision via MCP
        result = await self.handle_screen_paper(arguments)
        
        # 2. Auto-generate docs
        paper_id = arguments["paper_id"]
        reviewer_id = arguments["reviewer_id"]
        
        # Log to JSON
        self.log_decision_json(arguments, result)
        
        # Check if both reviewers done
        if self.both_reviewers_screened(paper_id):
            # Generate human-readable record
            self.generate_decision_record(paper_id)
            
            # Check for agreement
            if self.reviewers_agree(paper_id):
                self.update_progress_tracker(paper_id, "COMPLETED")
            else:
                self.flag_conflict(paper_id)
        
        # Update statistics
        self.update_screening_stats()
        
        return result
```

---

## Recommended Folder Structure After Screening

```
projects/real-time-translation-platform/screening/title-abstract/
├── logs/                           # Machine-readable records
│   ├── paper_232_retrieved.json
│   ├── screening_232_reviewer1.json
│   ├── screening_232_reviewer2.json
│   ├── screening_233_reviewer1.json
│   ├── retrieval_log.csv
│   └── ...
│
├── decisions/                      # Individual paper decision records
│   ├── 232_decision_record.md
│   ├── 233_decision_record.md
│   ├── 231_conflict_discussion.md
│   └── ...
│
├── reports/                        # Generated reports
│   ├── daily_summary_OCT19.md
│   ├── daily_summary_OCT20.md
│   ├── progress_checkpoint_1400.md
│   └── ...
│
├── summaries/                      # Key summaries
│   ├── screening_stats.json
│   ├── current_metrics.json
│   ├── papers_reviewed.md
│   └── papers_pending.md
│
├── screening_log.json              # Master log (all decisions)
├── screening_progress.csv          # Progress tracker
├── screening_decisions.md           # Main results document (updated daily)
└── README.md                        # Documentation of this folder
```

---

## Usage Instructions

### For SLR Coordinator

**Daily Workflow:**

1. **Morning**: Check progress
   ```bash
   cat screening_progress.csv | tail -10     # See latest entries
   cat summaries/current_metrics.json        # Check stats
   ```

2. **Afternoon**: Compile daily report
   ```bash
   generate_daily_report()                   # Auto-generates summary
   cat reports/daily_summary_{DATE}.md       # Review results
   ```

3. **End of week**: Resolve conflicts
   ```bash
   find decisions -name "*conflict*" -type f # Find disagreements
   # Schedule team meeting to discuss
   ```

### For Reviewers

**During Screening:**

1. Get paper info
2. Review in abstract
3. Use `screen_paper()` to record decision
4. Documentation auto-saves to:
   - `logs/screening_{id}.json`
   - `screening_log.json` (appended)
   - `screening_progress.csv` (row updated)
   - `screening_stats.json` (metrics updated)

**No additional documentation steps needed** - everything is automatic!

---

## Quality Assurance Checklist

- ✅ Every decision logged to JSON (machine-readable)
- ✅ Every decision logged to CSV (progress tracking)
- ✅ Every paper's decisions in decision record (human-readable)
- ✅ Statistics updated in real-time
- ✅ Conflicts flagged for team review
- ✅ Agreement calculated (Cohen's Kappa)
- ✅ Progress estimates updated
- ✅ All logs timestamped and traceable

---

## Benefits of This Approach

1. **Transparent**: Every decision documented and traceable
2. **Auditable**: Full history of screening process
3. **Efficient**: Auto-documentation saves time
4. **Professional**: Meets SLR standards and PRISMA guidelines
5. **Reproducible**: Complete record of methodology
6. **Collaborative**: Clear tracking of inter-rater agreement
7. **Adaptive**: Easy to adjust criteria based on early results

---

**Status**: ✅ Ready for Implementation  
**Created**: October 19, 2025  
**Integration**: MCP Server auto-documentation workflow
