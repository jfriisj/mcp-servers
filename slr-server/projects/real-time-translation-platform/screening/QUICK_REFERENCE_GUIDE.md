# QUICK REFERENCE GUIDE
## Bulk Screening Workflow for 232 Papers

**Created:** October 19, 2025  
**Status:** ALL DOCUMENTATION COMPLETE - Ready to Execute

---

## Current Situation

```
✅ COMPLETED:
   • 232 papers imported with abstracts
   • SLR-server tools operational
   • Project infrastructure ready
   • 4 comprehensive workflow documents created
   • Inclusion/exclusion criteria defined

❌ PENDING (CRITICAL):
   • Reviewer 2 confirmation
   • Training meeting scheduling
   • Pilot screening initiation
```

---

## What SLR-Server Can Do

### 5 Available Tools for Bulk Screening

```
TOOL 1: list_papers
├─ Get 50 papers at a time (5 batches for 232 papers)
├─ Supports filtering by year, author, tags
└─ Use: Retrieve papers ready for screening

TOOL 2: get_paper
├─ Get complete metadata for individual paper
├─ Includes: title, abstract, authors, year, keywords
└─ Use: Get full details before screening decision

TOOL 3: screen_paper ★ MAIN TOOL FOR SCREENING
├─ Record INCLUDE / EXCLUDE / UNCERTAIN decision
├─ Include: confidence level, reasoning, exclusion codes
├─ Parameters: project_id=1, reviewer_id, stage="title_abstract"
└─ Use: Record all screening decisions in database

TOOL 4: search_papers
├─ Search papers by keyword or semantic meaning
├─ Useful for finding papers matching criteria
└─ Use: Filter specific paper types

TOOL 5: get_slr_progress
├─ Get real-time project metrics
├─ Returns: papers screened, included, agreement metrics
└─ Use: Track progress and generate reports
```

---

## 5-Week Screening Timeline

```
WEEK 1: PILOT & CALIBRATION
├─ Monday: Select 25 diverse pilot papers
├─ Tue-Wed: Both reviewers screen independently
├─ Thursday: Calculate Kappa (target > 0.60)
├─ Friday: Prepare for full screening
└─ Decision: Proceed or refine criteria?

WEEKS 2-4: FULL SCREENING (3 Batches)
├─ Week 2: Batch 1-2 (Papers 1-100) → 6 hours
├─ Week 3: Batch 3-4 (Papers 101-200) → 6 hours  
├─ Week 4: Batch 5 (Papers 201-232) → 2 hours
├─ All batches: Both reviewers in parallel
└─ Expected outcome: 46-93 papers included

WEEK 5: CONFLICT RESOLUTION
├─ Monday-Tue: Identify disagreements
├─ Wednesday: Discussion meeting
├─ Thursday: Record final decisions
├─ Friday: Generate screening report
└─ Final Kappa target: > 0.70
```

---

## Screening Decision Criteria

### INCLUDE if paper has:
✓ Empirical system or evaluation (not just theory)
✓ Architecture or design focus
✓ Real-time or simultaneous translation
✓ Machine learning / deep learning approach
✓ Performance evaluation or benchmarking
✓ Peer-reviewed publication

### EXCLUDE if paper has:
✗ Statistical MT only (no neural/deep learning)
✗ Text translation only (no speech)
✗ Non-English or insufficient content
✗ Insufficient detail or quality
✗ No empirical contribution
✗ Non peer-reviewed

---

## Expected Screening Outcomes

```
INPUT:  232 papers (abstracts only)
         ↓
PROCESS: Independent review by 2 reviewers
         Kappa calibration via pilot
         Batch processing across 5 weeks
         Conflict resolution
         ↓
OUTPUT: ~46-93 papers (20-40% inclusion rate)
        Moving to Full-Text Screening
```

---

## Key Metrics to Track

| Metric | Target | How |
|--------|--------|-----|
| Papers screened | 232 | Use: list_papers |
| Inter-rater Kappa | > 0.70 | Calculate: Cohen's formula |
| Avg confidence | > 0.80 | Average of all decisions |
| Decision consistency | No bias | Spot check: 5% random |
| Papers included | 46-93 | Count: decision='include' |
| Papers excluded | 139-186 | Count: decision='exclude' |
| Papers uncertain | < 5 | Count: decision='uncertain' |

---

## Documents Created (8 Files)

```
SCREENING FOLDER: /projects/real-time-translation-platform/screening/

1. ⭐ OPTION_C_SUMMARY.md (THIS WEEK'S ANALYSIS)
   └─ Complete overview of capabilities, workflow, next steps

2. ⭐ bulk_screening_workflow.md (3,500+ words)
   └─ 3-phase workflow with detailed procedures
   └─ Quality assurance, conflict resolution, troubleshooting
   └─ Timeline, resource allocation, risk assessment

3. ⭐ bulk_screening_implementation_guide.md (2,500+ words)
   └─ Step-by-step implementation with code examples
   └─ Weekly schedules, success criteria, final checklist
   └─ Tool usage patterns, quality checkpoints

4. ⭐ screening_progress_tracker.md (2,000+ words)
   └─ Pilot tracking templates
   └─ Batch progress tracker (all 5 batches)
   └─ Disagreement log, summary reports
   └─ Spreadsheet format templates

5. screening_protocol.md (already exists - 350+ lines)
   └─ Detailed 3-stage screening procedure
   └─ Reviewer assignments, conflict resolution, forms

6. Related: SLR_SETUP_COMPLETE.md (already exists - 800+ lines)
   └─ Inclusion/exclusion criteria with full definitions
   └─ Research questions, search strategy

7. Related: prisma_framework.md (already exists - 400+ lines)
   └─ PRISMA quality assessment for later phases

8. Related: PROGRESS_REPORT.md (already exists - 600+ lines)
   └─ Overall project status and milestones
```

---

## This Week's Action Items (CRITICAL)

### MONDAY-TUESDAY:
- [ ] Send message to potential reviewer2
- [ ] Verify their availability (4-5 weeks)
- [ ] Share screening protocol overview

### WEDNESDAY:
- [ ] Confirm reviewer2 commitment
- [ ] Set training meeting date/time
- [ ] Prepare training materials

### THURSDAY:
- [ ] Hold 1-hour training meeting
  - Review PRISMA principles
  - Discuss inclusion/exclusion criteria
  - Walk through example papers
  - Explain conflict resolution
  
### FRIDAY:
- [ ] Set up tracking spreadsheet
- [ ] Verify SLR-server tool access
- [ ] Select 25-paper pilot sample
- [ ] Schedule pilot screening start

### NEXT WEEK:
- [ ] Pilot screening: Both reviewers (Tue-Wed)
- [ ] Analyze results & calculate Kappa (Thu)
- [ ] Decision: Proceed or refine (Fri)

---

## Quick Reference: Tool Usage

### Screening Decision Recording Example

```python
# For each paper, both reviewers call:

mcp_slr-server_screen_paper(
    project_id=1,
    paper_id=232,                    # Paper ID from database
    reviewer_id="reviewer1",         # Or "reviewer2"
    stage="title_abstract",
    decision="include",              # Or "exclude" or "uncertain"
    exclusion_criteria=["TA-02"],   # Only if excluding
    confidence_level=0.95,           # 0-1 scale
    reason="Empirical study of real-time S2ST platform 
            design with multilingual support and 
            performance evaluation. Addresses RQ1 and RQ4."
)
```

### Batch Retrieval Example

```python
# Get batch of papers for screening

mcp_slr-server_list_papers(
    limit=50,      # 50 papers at a time
    offset=0       # Batch 1: offset=0
               # Batch 2: offset=50
               # Batch 3: offset=100
               # Batch 4: offset=150
               # Batch 5: offset=200
)
```

---

## Success Checklist

### Before Starting:
- [ ] Reviewer 2 confirmed & available
- [ ] Training completed
- [ ] Tools tested & working
- [ ] Pilot papers identified
- [ ] Tracking spreadsheet ready

### During Screening:
- [ ] Each paper reviewed by 2 reviewers independently
- [ ] Decisions recorded with reasoning
- [ ] Confidence levels provided
- [ ] Disagreements logged
- [ ] Progress tracked weekly

### After Completion:
- [ ] All 232 papers screened
- [ ] Kappa > 0.70 achieved
- [ ] ~46-93 papers for full-text
- [ ] Report generated
- [ ] Lessons documented

---

## FAQ - Quick Answers

**Q: Can SLR-server auto-screen papers?**  
A: No - decisions require human review. SLR-server stores the decisions.

**Q: How long will this take?**  
A: 4-5 weeks total. ~10-15 hours actual screening work split between 2 reviewers.

**Q: What if reviewers disagree?**  
A: Follow 5-step conflict resolution in bulk_screening_workflow.md

**Q: What's the inclusion rate?**  
A: Typically 20-40% for systematic reviews. Target: ~60 papers.

**Q: Do we need both reviewers for every paper?**  
A: YES - Independent review by both ensures reliability.

**Q: What if Kappa < 0.60?**  
A: Normal. Run second pilot after clarifying criteria.

---

## Workflow at a Glance

```
START (This week)
   ↓
[Confirm reviewer2]
   ↓
[Training meeting]
   ↓
PILOT (Week 1)
   ├─ 25 papers
   ├─ Both reviewers
   └─ Calculate Kappa
   ↓
[Kappa > 0.60?]
   ├─ YES → Continue
   └─ NO → Clarify criteria, retry
   ↓
FULL SCREENING (Weeks 2-4)
   ├─ Batch 1-2: Papers 1-100
   ├─ Batch 3-4: Papers 101-200
   ├─ Batch 5: Papers 201-232
   └─ Both reviewers on each
   ↓
CONFLICT RESOLUTION (Week 5)
   ├─ Identify disagreements
   ├─ Discussion meeting
   ├─ Final decisions
   └─ Calculate final Kappa
   ↓
REPORT (End of Week 5)
   ├─ Screening summary
   ├─ 46-93 papers advancing
   └─ Ready for Full-Text Phase
   ↓
NEXT PHASE (Weeks 6-8)
   └─ Full-text retrieval & screening
```

---

## Resources at Your Fingertips

| Need | Document | Location |
|------|----------|----------|
| Full workflow | bulk_screening_workflow.md | screening/ |
| Step-by-step guide | bulk_screening_implementation_guide.md | screening/ |
| Progress tracking | screening_progress_tracker.md | screening/ |
| Criteria definitions | SLR_SETUP_COMPLETE.md | root |
| Project status | PROGRESS_REPORT.md | reports/ |
| Quality framework | prisma_framework.md | quality-assessment/ |
| This summary | OPTION_C_SUMMARY.md | screening/ |

---

## Next Step: CONFIRM REVIEWER 2

This is the **CRITICAL BLOCKING ITEM**.

Until reviewer2 is confirmed:
- Cannot schedule training
- Cannot start pilot screening
- Cannot meet Week 1 timeline
- Project will slip

**Action:** Contact reviewer2 TODAY with:
1. Role description (domain expert in speech translation)
2. Time commitment (4-5 weeks)
3. Meeting schedule (training + weekly syncs)
4. What's involved (2-3 minutes per paper × 232 papers)

---

## Contact & Support

| Item | Details |
|------|---------|
| **Project** | Real-Time Speech Translation Platform SLR |
| **Lead Reviewer** | reviewer1 (methodology specialist) |
| **Domain Reviewer** | reviewer2 [CONFIRM THIS WEEK] |
| **Papers Ready** | 232 with abstracts |
| **Tools** | SLR-server MCP |
| **Timeline** | 4-5 weeks to complete T&A screening |

---

## Document Versions & Maintenance

**Created:** October 19, 2025  
**Status:** READY FOR IMPLEMENTATION  
**Version:** 1.0  

**These documents are living references:**
- Update after pilot screening (lessons learned)
- Update after each batch (progress metrics)
- Update after conflict resolution (final outcomes)
- Archive final report when complete

---

## Final Status

```
✅ INFRASTRUCTURE: Ready
✅ TOOLS: Operational
✅ DOCUMENTATION: Complete (8 documents)
✅ CRITERIA: Defined & approved
✅ PAPERS: 232 imported with abstracts
✅ TIMELINE: 4-5 weeks planned

⏳ BLOCKING ITEM: Reviewer 2 confirmation

🚀 NEXT ACTION: Confirm Reviewer 2 THIS WEEK
```

---

**Prepared by:** SLR Research Team  
**Date:** October 19, 2025  
**Status:** Ready to Execute  
**Next Review:** After Reviewer2 confirmation and training completion

---

**REMEMBER:** This is a BULK screening operation with MCP tools handling decision recording. The process is efficient, trackable, and quality-assured. With both reviewers working in parallel, 232 papers can be screened in 4-5 weeks.

**Let's get reviewer2 confirmed and start the pilot screening next week!**
