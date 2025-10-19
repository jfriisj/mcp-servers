# Bulk Screening Workflow & Tools
## Real-Time Speech Translation Platform SLR

**Created:** October 19, 2025  
**Status:** READY FOR IMPLEMENTATION  
**Total Papers to Screen:** 232 papers with abstracts

---

## Overview

With 232 papers successfully imported from Primo BibTeX export, we now move into the **Title & Abstract (T&A) Screening phase**. This document outlines:

1. Available SLR-server tools for bulk screening
2. Recommended screening workflow
3. Decision tracking process
4. Quality assurance procedures

---

## Current System Capabilities

### SLR-Server Bulk Screening Tools

The SLR-server MCP provides the following screening tools:

#### 1. **List Papers Tool** (`mcp_slr-server_list_papers`)
- **Purpose:** Retrieve papers for screening review
- **Capability:** Batch retrieval with filters (year, author, tags, quality score)
- **Use Case:** Get papers ready for screening in batches
- **Current Data:** 232 papers available for screening

#### 2. **Screen Paper Tool** (`mcp_slr-server_screen_paper`)
- **Purpose:** Record screening decisions for individual papers
- **Key Parameters:**
  - `project_id`: Project identifier (ID: 1)
  - `paper_id`: Paper to screen (232 papers available)
  - `reviewer_id`: Reviewer making decision
  - `stage`: Screening stage ("title_abstract" for T&A phase)
  - `decision`: INCLUDE / EXCLUDE / UNCERTAIN
  - `exclusion_criteria`: Applicable exclusion codes
  - `confidence_level`: 0-1 scale (0=low, 1=high)
  - `reason`: Detailed explanation of decision
- **Output:** Screening ID recorded in database

#### 3. **Search Papers Tool** (`mcp_slr-server_search_papers`)
- **Purpose:** Find papers by keyword/semantic search
- **Useful For:** Finding papers matching specific criteria
- **Use Case:** Search by topic for focused screening batches

#### 4. **Get Paper Tool** (`mcp_slr-server_get_paper`)
- **Purpose:** Retrieve full paper metadata and details
- **Key Data:** Title, abstract, year, authors, keywords
- **Use Case:** Review full abstract before screening decision

---

## Recommended Bulk Screening Workflow

### Phase 1: Pilot Screening (Week 1)
**Objective:** Calibrate screening criteria with both reviewers

**Steps:**

1. **Select Pilot Sample**
   - Retrieve 20-30 papers for pilot screening
   - Ensure diverse representation (different years, types)
   - Mix easy/obvious decisions with borderline cases

2. **Independent Review**
   - reviewer1 screens all pilot papers independently
   - reviewer2 screens all pilot papers independently
   - Each records decisions using `mcp_slr-server_screen_paper` tool
   - Target: 2-3 minutes per paper

3. **Agreement Analysis**
   - Calculate inter-rater agreement (Kappa statistic)
   - Identify papers with disagreement
   - Analyze disagreement patterns

4. **Criteria Refinement**
   - If Kappa < 0.6: Discuss criteria, clarify definitions, adjust
   - If Kappa > 0.6: Proceed to full screening
   - Document any criteria adjustments

5. **Progress Recording**
   - Update screening log with pilot results
   - Document lessons learned
   - Record any protocol adjustments

### Phase 2: Full Title & Abstract Screening (Weeks 2-4)
**Objective:** Screen all 232 papers using calibrated criteria

**Batch Processing Strategy:**

1. **Batch Size:** Screen in groups of 50 papers
   - Batch 1: Papers 1-50
   - Batch 2: Papers 51-100
   - Batch 3: Papers 101-150
   - Batch 4: Papers 151-200
   - Batch 5: Papers 201-232

2. **Per Batch Process:**
   - **Step 1:** Retrieve batch using `mcp_slr-server_list_papers`
   - **Step 2:** For each paper in batch:
     - Get full metadata using `mcp_slr-server_get_paper`
     - Review title and abstract
     - Record decision using `mcp_slr-server_screen_paper`
   - **Step 3:** Calculate batch agreement metrics
   - **Step 4:** Log batch completion

3. **Time Estimates:**
   - 2-3 minutes per paper
   - ~100-150 minutes per 50-paper batch
   - ~2-3 hours per batch with breaks
   - Estimated 10-15 hours total for all 232 papers

### Phase 3: Conflict Resolution & Finalization (Week 4-5)
**Objective:** Resolve disagreements and finalize T&A decisions

**Conflict Resolution Process:**

1. **Identify Conflicts**
   - Papers with INCLUDE vs EXCLUDE decisions
   - Papers with UNCERTAIN decisions
   - Papers with low confidence scores

2. **Discussion Round**
   - Bring conflicting papers to reviewer meeting
   - Present both perspectives
   - Discuss criteria application
   - Aim for consensus

3. **Recording Decisions**
   - Use `mcp_slr-server_screen_paper` to record final decisions
   - Include conflict resolution notes in reason field
   - Mark confidence level accordingly

4. **Final Metrics**
   - Calculate final inter-rater agreement
   - Document % of papers requiring discussion
   - Prepare T&A screening summary

---

## Screening Decision Framework

### Inclusion/Exclusion Criteria (from SLR_SETUP_COMPLETE.md)

**INCLUDE if paper addresses:**
- IC1: Empirical system or evaluation (not purely theoretical)
- IC2: Architecture, design, or platform focus (not just single component)
- IC3: Real-time or simultaneous translation capability
- IC4: Multilingual systems or multiple language pairs (preferred)
- IC5: Uses machine learning/deep learning approaches
- IC6: Addresses scalability or performance characteristics
- IC7: Includes performance evaluation or benchmarking
- IC8: Published in peer-reviewed venue

**EXCLUDE if:**
- EC1: Statistical machine translation only (pre-neural, no deep learning)
- EC2: Text-only translation (no speech component)
- EC3: Non-English or insufficient English content
- EC4: Insufficient detail (< 500 words in abstract)
- EC5: Other language-pair systems (not speech)
- EC6: Opinion/review without empirical contribution
- EC7: Published before 2015 (outdated technology)
- EC8: Duplicate of already identified paper
- EC9: Major methodological flaws
- EC10: Gray literature (not peer-reviewed)

### Exclusion Reason Codes (T&A Stage)

Use these codes when excluding papers at title/abstract stage:

| Code | Reason | Example |
|------|--------|---------|
| TA-01 | Not speech translation | "Text translation only" |
| TA-02 | Statistical MT only | "SMT approach, pre-neural" |
| TA-03 | Insufficient content | "Too brief abstract" |
| TA-04 | Duplicate | "Same paper as ID #X" |
| TA-05 | Theoretical only | "No empirical evaluation" |
| TA-06 | Out of scope | "Not platform-focused" |
| TA-07 | Quality issues | "Poor publication venue" |

---

## Screening Decision Recording

### Using mcp_slr-server_screen_paper Tool

**Required Fields for Each Decision:**

```
Tool: mcp_slr-server_screen_paper

Parameters:
- project_id: 1 (real-time-translation-platform)
- paper_id: [232-233, etc.] (from imported bibliography)
- reviewer_id: "reviewer1" or "reviewer2"
- stage: "title_abstract"
- decision: "include" OR "exclude" OR "uncertain"
- exclusion_criteria: ["TA-01"] (if excluding)
- confidence_level: 0.9 (scale 0-1)
- reason: "Comprehensive study of real-time speech translation platform design..."
```

**Example Screening Decisions:**

**Decision 1: INCLUDE**
```
paper_id: 232
reviewer_id: reviewer1
stage: title_abstract
decision: include
confidence_level: 0.95
reason: "Direct empirical study of real-time S2ST systems with architecture focus, 
         multilingual capability, and performance evaluation. Meets IC1-IC7 criteria."
```

**Decision 2: EXCLUDE**
```
paper_id: 233
reviewer_id: reviewer1
stage: title_abstract
decision: exclude
exclusion_criteria: ["TA-02"]
confidence_level: 0.85
reason: "Paper focuses on statistical machine translation approaches (pre-neural era), 
         does not address neural/deep learning for speech translation. Falls under EC1."
```

**Decision 3: UNCERTAIN**
```
paper_id: 234
reviewer_id: reviewer1
stage: title_abstract
decision: uncertain
confidence_level: 0.55
reason: "Abstract mentions real-time translation but unclear if speech-focused. 
         May be text-based. Requires full-text review for confirmation."
```

---

## Quality Assurance Procedures

### During Screening

**Reviewer Checklist:**
- [ ] Have I read the complete abstract carefully?
- [ ] Have I applied the criteria consistently?
- [ ] Have I recorded my confidence level honestly?
- [ ] Have I provided detailed reasoning?
- [ ] Have I used correct exclusion codes?

**Batch Monitoring:**
- [ ] Batch completed within time estimate?
- [ ] Confidence levels within expected range (0.7-1.0)?
- [ ] Exclusion reasons substantive and specific?
- [ ] Any unusual patterns in decisions?

### After Each Batch

**Batch QA Checklist:**
- [ ] Calculate inter-rater agreement for batch
- [ ] Identify high-disagreement papers (Kappa < 0.4 for pair)
- [ ] Review any papers with confidence < 0.6
- [ ] Spot-check 5% of excluded papers for accuracy
- [ ] Document any criteria clarifications needed

### Final Screening QA

**Overall Metrics to Calculate:**
- Total papers: 232
- Papers included: X
- Papers excluded: Y
- Papers uncertain: Z
- Inclusion rate: X/232
- Overall inter-rater agreement (Kappa)
- Cohen's kappa interpretation:
  - 0.81-1.00 = Almost perfect agreement
  - 0.61-0.80 = Substantial agreement ✓ TARGET
  - 0.41-0.60 = Moderate agreement
  - 0.01-0.40 = Fair agreement

---

## Workflow Timeline

### Week 1: Pilot & Preparation
| Day | Activity | Owner | Output |
|-----|----------|-------|--------|
| Mon | Select pilot sample (20-30 papers) | reviewer1 | Pilot paper list |
| Tue-Wed | Pilot screening by both reviewers | reviewer1, reviewer2 | 40-60 screening decisions |
| Thu | Agreement analysis & discussion | Both | Kappa score, criteria notes |
| Fri | Finalize criteria; prepare for full screening | reviewer1 | Updated screening guidance |

### Weeks 2-4: Full Screening
| Week | Batch | Papers | Time | Owner |
|------|-------|--------|------|-------|
| 2 | 1-2 | 1-100 | 4-6 hrs | Both reviewers |
| 3 | 3-4 | 101-200 | 4-6 hrs | Both reviewers |
| 4 | 5 | 201-232 | 1-2 hrs | Both reviewers |

### Week 5: Conflict Resolution & Finalization
| Activity | Time | Output |
|----------|------|--------|
| Resolve disagreements | 2-4 hrs | Final decisions for conflicts |
| Calculate final metrics | 1 hr | Screening report |
| Document results | 2 hrs | T&A Screening Summary Report |

---

## Expected Outcomes

### Screening Results Projections

Based on typical SLR T&A screening rates:

| Metric | Estimate | Range |
|--------|----------|-------|
| Papers screened | 232 | 232 |
| Papers included | 46-93 | 20-40% inclusion rate |
| Papers excluded | 139-186 | 60-80% exclusion rate |
| Papers uncertain | 0-10 | To be resolved |
| Inclusion rate | 25-30% | Common for S2ST field |

### Quality Targets

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| Inter-rater agreement (Kappa) | > 0.70 | 0.60-1.00 |
| Reviewer confidence (avg) | > 0.80 | 0.70-1.00 |
| Papers with Kappa conflict | < 5% | 0-10% |
| Time per paper (avg) | 2-3 min | 1-5 min |

---

## Next Phase Preparation

### After Title & Abstract Screening Complete

1. **Full-Text Retrieval** (Week 5-6)
   - Attempt to retrieve full texts for all included papers
   - Document retrieval success rate
   - Prepare for full-text screening

2. **Full-Text Screening** (Weeks 6-8)
   - Apply same 2-reviewer process
   - Target Kappa > 0.60
   - Expected to advance 50-150 papers (50-75% of T&A included)

3. **Quality Assessment** (Weeks 8-10)
   - Apply PRISMA quality framework
   - Use 0-12 point scale + 6-domain risk of bias
   - Categorize by quality level

4. **Data Extraction** (Weeks 10-12)
   - Extract data using 14-section framework
   - Populate evidence table
   - Prepare for synthesis

---

## Resources & Tools

### Available SLR-server Tools
✓ `mcp_slr-server_list_papers` - Retrieve papers for screening  
✓ `mcp_slr-server_get_paper` - Get full paper metadata  
✓ `mcp_slr-server_screen_paper` - Record screening decisions  
✓ `mcp_slr-server_search_papers` - Find papers by criteria  
✓ `mcp_slr-server_get_quality_assessment` - Track assessment status  

### External Tools Needed
- Spreadsheet software (Excel/Google Sheets) for tracking
- Reference management (Zotero/Mendeley) for organization
- Email for reviewer coordination
- Calendar for scheduling discussions

### Documentation Provided
✓ Screening protocol (screening_protocol.md)  
✓ Inclusion/exclusion criteria (SLR_SETUP_COMPLETE.md)  
✓ PRISMA framework (prisma_framework.md)  
✓ Quality assessment guide (prisma_framework.md)  
✓ This workflow document (bulk_screening_workflow.md)  

---

## Key Contacts & Responsibilities

| Role | Person | Contact | Responsibility |
|------|--------|---------|-----------------|
| Project Lead | reviewer1 | [contact] | Overall coordination |
| Lead Reviewer | reviewer1 | [contact] | T&A screening, QA |
| Domain Reviewer | reviewer2 | [contact] | T&A screening |
| Coordinator | [TBD] | [contact] | Progress tracking |

---

## Troubleshooting & FAQ

### Q: What if reviewers can't reach agreement (Kappa < 0.6)?

**A:** This is common. Follow the conflict resolution process:
1. Identify papers with disagreement
2. Discuss reasoning for each decision
3. Clarify criteria application
4. Re-screen disagreement papers
5. If still disagreement, third reviewer adjudicates
6. Document decision in detail

### Q: What if a paper's abstract is insufficient?

**A:** Mark as UNCERTAIN and plan for full-text review. Record reason as "Insufficient information in abstract for confident decision."

### Q: How do I handle duplicate papers?

**A:** Use exclusion code TA-04. The SLR system has detected some duplicates already (see list_papers output showing duplicates). Document both paper IDs.

### Q: Should I screen papers multiple times?

**A:** No. Both reviewers independently screen each paper ONCE. Then you compare and resolve disagreements. This ensures true independent assessment.

### Q: How much time will this take?

**A:** Estimated 10-15 hours of active screening time spread over 4-5 weeks. With two reviewers working in parallel, wall-clock time is 2-3 weeks.

---

## Getting Started

### This Week's Actions

1. **Identify reviewer2** (if not already done)
   - Domain expert in speech translation
   - Available for 4-week screening period
   - Willing to attend training session

2. **Schedule pilot screening meeting**
   - Both reviewers + lead
   - Review criteria together
   - Discuss 2-3 example papers
   - Plan pilot execution

3. **Prepare screening tools**
   - Set up spreadsheet for progress tracking
   - Configure SLR-server access for both reviewers
   - Test `mcp_slr-server_screen_paper` tool

4. **Conduct pilot screening**
   - Select 20-30 diverse papers
   - Both reviewers screen independently
   - Calculate agreement

---

## Document Maintenance

**Version:** 1.0  
**Status:** Ready for implementation  
**Last Updated:** October 19, 2025  
**Next Review:** After pilot screening completion

**To Update This Document:**
- Add lessons learned from pilot screening
- Refine time estimates based on actual experience
- Document any criteria clarifications made
- Record final screening metrics

---

**Ready to begin pilot screening? Contact reviewer1 and reviewer2 to schedule the planning meeting.**
