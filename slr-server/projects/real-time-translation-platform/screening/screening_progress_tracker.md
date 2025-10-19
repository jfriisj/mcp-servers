# Screening Progress Tracker
## Real-Time Speech Translation Platform SLR

**Created:** October 19, 2025  
**Status:** TEMPLATE READY - Ready for population during pilot & full screening phases

---

## Overview

This document provides tracking templates for all screening phases. These can be copied into Excel/Google Sheets for live tracking.

---

## Phase 1: Pilot Screening Tracker

### Pilot Sample Selection
**Target:** 20-30 papers for calibration  
**Strategy:** Diverse mix of clearly included, clearly excluded, and borderline cases

| Paper ID | Title (First 50 chars) | Year | Topic | Difficulty | reviewer1 | reviewer2 | Agreement | Kappa |
|----------|----------------------|------|-------|------------|-----------|-----------|-----------|-------|
| [ID] | [Title] | [Year] | [Core topic] | Easy/Hard/Borderline | Include/Exclude/Uncertain | Include/Exclude/Uncertain | Yes/No | Calculated |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

### Pilot Screening Summary

```
Pilot Screening Summary
======================

Date Conducted: [Date]
Reviewers: reviewer1, reviewer2
Papers Screened: X/25 target

DECISIONS SUMMARY:
- Both Include: X papers
- Both Exclude: X papers
- Disagreement (Include vs Exclude): X papers
- Disagreement (Include/Exclude vs Uncertain): X papers
- Both Uncertain: X papers

AGREEMENT METRICS:
- Overall Agreement: X% (X/X papers)
- Cohen's Kappa: 0.XX
  Interpretation: [Substantial/Moderate/Fair agreement]

DISAGREEMENT ANALYSIS:
Papers with disagreement:
- Paper ID [X]: reviewer1 = Include, reviewer2 = Exclude (Reason: [Criteria interpretation])
- Paper ID [Y]: reviewer1 = Exclude, reviewer2 = Uncertain (Reason: [Insufficient info])

LESSONS LEARNED:
1. Criteria interpretation: [Specific areas needing clarification]
2. Difficult cases: [Types of papers causing disagreement]
3. Training needs: [Additional guidance for reviewers]

DECISIONS MADE:
- Clarification to criteria: [Changes to IC/EC application]
- Additional training: [Topics to address]
- Updated guidance: [Specific instructions added]
- Conflict resolution: [How conflicting papers resolved]

OUTCOME:
✓ Kappa > 0.60 - PROCEED TO FULL SCREENING
OR
✓ Kappa < 0.60 - CONDUCT SECOND PILOT ROUND

Next Steps: [Next phase decision]
```

---

## Phase 2: Full Title & Abstract Screening Tracker

### Batch-Level Progress

```
FULL SCREENING PROGRESS TRACKER
===============================

Total Papers: 232
Batches: 5 (50 papers each, final batch 32 papers)

BATCH COMPLETION:

Batch 1 (Papers 1-50):
  Start Date: [Date]
  Reviewer1: [Status - Started/In Progress/Complete]
  Reviewer2: [Status - Started/In Progress/Complete]
  Completion Date: [Date]
  Include: X  |  Exclude: Y  |  Uncertain: Z
  Kappa: 0.XX  |  Avg Confidence: 0.XX
  Time: X hours
  Notes: [Any issues/lessons]

Batch 2 (Papers 51-100):
  [Same structure as Batch 1]

Batch 3 (Papers 101-150):
  [Same structure as Batch 1]

Batch 4 (Papers 151-200):
  [Same structure as Batch 1]

Batch 5 (Papers 201-232):
  [Same structure as Batch 1]

OVERALL PROGRESS:
  Papers Processed: X/232
  Percent Complete: X%
  Papers Included: X
  Papers Excluded: X
  Papers Uncertain: X
  Overall Kappa: 0.XX
  Expected Completion: [Date]
```

### Individual Paper Decisions

```
PAPER-BY-PAPER SCREENING LOG
============================

| Paper ID | Title | Authors | Year | reviewer1 Decision | reviewer1 Confidence | reviewer1 Reasoning | reviewer2 Decision | reviewer2 Confidence | reviewer2 Reasoning | Conflict? | Resolution | Final Decision |
|----------|-------|---------|------|-------------------|---------------------|-------------------|-------------------|---------------------|-------------------|-----------|------------|-----------------|
| 232 | [Title] | [Authors] | 2024 | Include | 0.95 | "Real-time S2ST platform with architecture focus" | Include | 0.90 | "Addresses RQ1 and RQ4" | No | N/A | INCLUDE |
| 233 | [Title] | [Authors] | 2018 | Exclude | 0.85 | "Statistical MT only, pre-neural" | Exclude | 0.80 | "No deep learning approach" | No | N/A | EXCLUDE (TA-02) |
| 234 | [Title] | [Authors] | 2022 | Include | 0.70 | "Mentions real-time speech translation" | Uncertain | 0.65 | "Unclear if speech-focused" | Yes | [Discussed] | UNCERTAIN → [Final] |
| | | | | | | | | | | | | |
```

---

## Phase 3: Conflict Resolution Tracker

### Disagreement Log

```
SCREENING DISAGREEMENT & RESOLUTION LOG
=======================================

Total Disagreements Identified: X (X% of X papers)

Disagreement Case 1:
  Paper ID: [X]
  Title: [Title]
  reviewer1 Decision: Include
  reviewer2 Decision: Exclude
  reviewer1 Reasoning: "Direct empirical study of platform design"
  reviewer2 Reasoning: "Text translation focus, not speech"
  
  Discussion Notes:
  - Meeting Date: [Date]
  - Discussion Points:
    * reviewer1 interpretation of abstract: [...]
    * reviewer2 interpretation of abstract: [...]
    * Criteria applied: IC2 (platform focus) vs EC2 (not speech)
  - Agreement Reached: Yes/No
  - Final Decision: [Include/Exclude/Third reviewer needed]
  - Resolved By: [Process used]
  - Date Resolved: [Date]

Disagreement Case 2:
  [Similar structure]

SUMMARY STATISTICS:
- Total Disagreements: X
- Resolved by discussion: X
- Referred to third reviewer: X
- Changed to INCLUDE: X
- Changed to EXCLUDE: X
- Changed to UNCERTAIN: X
```

---

## Phase 4: Summary & Metrics Report

### Overall Screening Report

```
TITLE & ABSTRACT SCREENING - FINAL REPORT
==========================================

Screening Period: [Start Date] to [End Date]
Total Duration: X weeks
Reviewers: reviewer1, reviewer2

PARTICIPATION & EFFORT:
- Reviewer1 Total Hours: X hours
- Reviewer2 Total Hours: X hours
- Combined Total: X hours
- Average per Paper: X minutes
- Discussion/Resolution Hours: X hours

SCREENING OUTCOMES:

Total Papers Screened: 232

                Reviewer1    Reviewer2    Initial Agreement
Include           X            X            [X%]
Exclude           X            X            [X%]
Uncertain         X            X            [X%]

After Conflict Resolution:
- Final Include: X (X% of total)
- Final Exclude: X (X% of total)
- Final Uncertain: X (X% of total)

AGREEMENT METRICS:
- Overall Cohen's Kappa: 0.XX
  Interpretation: [Substantial/Moderate/Fair]
- Observed Agreement: X%
- Expected Agreement: X%
- Papers with perfect agreement: X (X%)
- Papers requiring discussion: X (X%)

CONFIDENCE LEVELS:
- Average Reviewer Confidence (Include): 0.XX
- Average Reviewer Confidence (Exclude): 0.XX
- Papers with Confidence < 0.70: X
- Papers with Confidence > 0.90: X

EXCLUSION REASONS (Among 232 papers, X excluded):

Reason Code    | Count | Examples
TA-01 (Not S2ST) | X | Paper IDs: [list]
TA-02 (Statistical MT) | X | Paper IDs: [list]
TA-03 (Insufficient content) | X | Paper IDs: [list]
TA-04 (Duplicate) | X | Paper IDs: [list]
TA-05 (Theoretical only) | X | Paper IDs: [list]
TA-06 (Out of scope) | X | Paper IDs: [list]
TA-07 (Quality issues) | X | Paper IDs: [list]
TOTAL EXCLUDED | X |

NEXT PHASE READINESS:

Papers Advancing to Full-Text Screening: X (X% of original)
Expected Yield: X papers (20-40% typically advance from T&A to full-text)

Quality Assessment of Screening Process:
✓ Inter-rater agreement: [X/10 points]
✓ Decision consistency: [X/10 points]
✓ Documentation quality: [X/10 points]
✓ Timeline adherence: [X/10 points]

LESSONS LEARNED:
1. [Learning 1]
2. [Learning 2]
3. [Learning 3]

RECOMMENDATIONS FOR FULL-TEXT SCREENING:
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

ISSUES ENCOUNTERED:
1. [Issue 1 and resolution]
2. [Issue 2 and resolution]

PROTOCOL ADJUSTMENTS:
- Changes to criteria: [Any changes made]
- Updated definitions: [Any terms clarified]
- New guidance: [Any new instructions]

Sign-off:
Reviewer1: _________________ Date: _________
Reviewer2: _________________ Date: _________
Lead: _________________ Date: _________
```

---

## Data Quality Metrics

### Screening Quality Checklist

```
SCREENING QUALITY ASSURANCE CHECKLIST
=====================================

INDIVIDUAL REVIEWER PERFORMANCE:

Reviewer1:
☐ All 232 papers screened
☐ Decisions recorded with reasoning
☐ Confidence levels provided (0-1 scale)
☐ Exclusion codes used correctly
☐ No missing data points
☐ Reasoning substantive (not generic)
☐ Consistency check passed (spot audit)

Reviewer2:
☐ All 232 papers screened
☐ Decisions recorded with reasoning
☐ Confidence levels provided (0-1 scale)
☐ Exclusion codes used correctly
☐ No missing data points
☐ Reasoning substantive (not generic)
☐ Consistency check passed (spot audit)

INTER-RATER RELIABILITY:
☐ Cohen's Kappa calculated
☐ Kappa > 0.60 (substantial agreement)
☐ Disagreement papers identified
☐ Discussion process documented
☐ Final decisions recorded
☐ Resolution method justified

DATA INTEGRITY:
☐ No papers skipped or missing
☐ All decisions have supporting reasons
☐ All exclusion codes are valid
☐ Confidence levels within 0-1 range
☐ Paper IDs match database
☐ Date tracking complete

PROCESS ADHERENCE:
☐ Followed 2-reviewer independent process
☐ Used standardized screening tool
☐ Applied criteria consistently
☐ Documented conflict resolution
☐ Met time estimates (+/- 20%)
☐ Reported metrics as scheduled

DOCUMENTATION:
☐ Pilot screening documented
☐ All screening decisions recorded
☐ Disagreements logged with context
☐ Resolution process detailed
☐ Final report completed
☐ All supporting files archived
```

---

## Tracking Template for Spreadsheet

### Excel/Google Sheets Format

```
=== TAB 1: PILOT SCREENING ===

[Table structure as shown above]

=== TAB 2: BATCH 1 (Papers 1-50) ===

Paper ID | Title | Year | reviewer1_decision | reviewer1_conf | reviewer1_reason | reviewer2_decision | reviewer2_conf | reviewer2_reason | agreement | exclusion_code | notes
[data rows]

=== TAB 3: BATCH 2 (Papers 51-100) ===
[Same structure]

=== TAB 4: BATCH 3 (Papers 101-150) ===
[Same structure]

=== TAB 5: BATCH 4 (Papers 151-200) ===
[Same structure]

=== TAB 6: BATCH 5 (Papers 201-232) ===
[Same structure]

=== TAB 7: DISAGREEMENTS ===

Paper ID | Title | r1_decision | r2_decision | discussion_notes | final_decision | date_resolved
[conflict rows]

=== TAB 8: SUMMARY ===

[Overall metrics and statistics table]

=== TAB 9: METRICS ===

[Key performance indicators and calculations]
```

---

## Expected Tracking Outputs

After completion of each phase, the following reports should be available:

### After Pilot Screening:
- [X] Kappa calculation
- [X] Disagreement identification
- [X] Criteria clarification notes
- [X] Protocol adjustments (if needed)

### After Full Screening:
- [X] Complete screening log (all 232 papers)
- [X] Batch-level metrics (5 batches)
- [X] Inter-rater agreement statistics
- [X] Exclusion reason distribution
- [X] Confidence level analysis

### After Conflict Resolution:
- [X] Disagreement resolution log
- [X] Third-reviewer decisions (if applicable)
- [X] Final decision matrix
- [X] Agreement improvement metrics

### Final Deliverables:
- [X] T&A Screening Final Report
- [X] Papers advancing to full-text (X papers)
- [X] Detailed inclusion/exclusion summary
- [X] Quality assurance metrics
- [X] Lessons learned document

---

## Integration with SLR-server

### Recording Decisions in SLR-server

Each screening decision is recorded using:
```
mcp_slr-server_screen_paper
  project_id: 1
  paper_id: [232-233, etc]
  reviewer_id: "reviewer1" or "reviewer2"
  stage: "title_abstract"
  decision: "include" or "exclude" or "uncertain"
  exclusion_criteria: ["TA-01"] (if applicable)
  confidence_level: 0.90 (0-1)
  reason: "[Substantive explanation]"
```

### Generating Reports from SLR-server

After screening complete:
```
mcp_slr-server_get_slr_progress
  project_id: 1
  [Returns updated progress metrics]

mcp_slr-server_list_papers
  filters: status="included", stage="title_abstract"
  [Returns all papers with include decision]
```

---

## Document Maintenance

**Version:** 1.0  
**Status:** Template - Ready for implementation  
**Last Updated:** October 19, 2025  

**When to Update:**
- After pilot screening completes → Document pilot metrics
- After each batch completes → Update batch progress
- After conflict resolution → Document final decisions
- After T&A complete → Generate final summary report

---

**Next Step:** Begin pilot screening when reviewer2 is confirmed. Use these templates to track progress.
