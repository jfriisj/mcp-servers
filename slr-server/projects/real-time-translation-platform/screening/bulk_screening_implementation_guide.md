# Bulk Screening Implementation Guide
## SLR-Server Capabilities for 232 Papers

**Created:** October 19, 2025  
**Status:** READY TO EXECUTE  
**Papers Ready for Screening:** 232 (from Primo BibTeX import)

---

## Summary of Available Tools & Workflow

You now have **232 papers with abstracts** ready for screening, and the SLR-server provides tools for bulk screening. Here's what's available:

---

## SLR-Server Bulk Screening Capabilities

### ✅ Tool 1: List Papers (`mcp_slr-server_list_papers`)

**Purpose:** Retrieve papers in batches for screening

**Capability:**
- Get up to 232 papers with metadata
- Filter by year, author, tags, quality score
- Retrieve in manageable batches

**Example Usage:**
```
mcp_slr-server_list_papers
  limit: 50        # Get 50 papers at a time
  offset: 0        # Start from beginning
```

**Current Data:**
```
Total papers available: 232
Sample papers retrieved:
- Adapting Translation Models for Transcript Disfluency Detection (2019)
- Open Source Toolkit for Speech to Text Translation (2018)
- Breaking the Data Barrier: Towards Robust Speech Translation (2019)
- Jointly Trained Transformers models for Spoken Language Translation (2020)
- [... 228 more papers]
```

### ✅ Tool 2: Get Paper (`mcp_slr-server_get_paper`)

**Purpose:** Get full metadata for a paper before screening

**Capability:**
- Retrieve title, abstract, authors, year, keywords
- Complete information for informed decision

**Example Usage:**
```
mcp_slr-server_get_paper
  paper_id: 232  # Get specific paper details
```

### ✅ Tool 3: Screen Paper (`mcp_slr-server_screen_paper`)

**Purpose:** Record screening decisions in database

**Capability:**
- Record INCLUDE/EXCLUDE/UNCERTAIN decisions
- Document reasoning and confidence
- Apply exclusion reason codes
- Build screening decision history

**Required Information:**
```
project_id: 1                           # Your SLR project
paper_id: 232                           # Which paper (1-232)
reviewer_id: "reviewer1" or "reviewer2" # Who decided
stage: "title_abstract"                 # T&A stage
decision: "include"                     # The decision
exclusion_criteria: ["TA-02"]          # Why excluded (if applicable)
confidence_level: 0.90                  # Confidence (0-1 scale)
reason: "Detailed explanation..."       # Substantive reasoning
```

**Current Status:**
- Papers available: 232
- Papers with metadata extracted: 232 ✓
- Ready for screening: YES ✓

---

## Recommended Bulk Screening Workflow

### Phase 1: Pilot Screening (This Week)

**Objective:** Test criteria with both reviewers using 20-30 papers

**Steps:**
1. Use `mcp_slr-server_list_papers` to select diverse pilot sample
2. Both reviewers independently use `mcp_slr-server_get_paper` to review each paper
3. Both reviewers use `mcp_slr-server_screen_paper` to record decisions
4. Calculate inter-rater agreement (Kappa)
5. If Kappa > 0.6: Proceed to full screening

**Tools Used:** list_papers → get_paper → screen_paper

### Phase 2: Full Screening (Weeks 2-4)

**Objective:** Screen all 232 papers with both reviewers

**Batch Processing:**
- **Batch 1:** Papers 1-50 → `list_papers` (offset=0, limit=50)
- **Batch 2:** Papers 51-100 → `list_papers` (offset=50, limit=50)
- **Batch 3:** Papers 101-150 → `list_papers` (offset=100, limit=50)
- **Batch 4:** Papers 151-200 → `list_papers` (offset=150, limit=50)
- **Batch 5:** Papers 201-232 → `list_papers` (offset=200, limit=32)

**Per Batch Process:**
```
For each batch:
  1. mcp_slr-server_list_papers (get 50 papers)
  2. For each paper in batch:
     - mcp_slr-server_get_paper (get full metadata)
     - reviewer1: mcp_slr-server_screen_paper (record decision)
     - reviewer2: mcp_slr-server_screen_paper (record decision)
  3. Track completion, metrics, disagreements
```

### Phase 3: Conflict Resolution (Week 5)

**Objective:** Resolve disagreements between reviewers

**Tools Used:** 
- Use `mcp_slr-server_screen_paper` to record final decisions after discussion

### Phase 4: Reporting & Next Steps

**Objective:** Prepare for full-text screening

**Metrics Available from SLR-server:**
- Total papers screened
- Papers included vs. excluded
- Inter-rater agreement
- Papers advancing to full-text

---

## Time Estimates

| Activity | Per Paper | Batch (50) | All (232) |
|----------|-----------|-----------|----------|
| Get metadata | 10 sec | 8 min | 39 min |
| Review abstract | 1-2 min | 50-100 min | 232-464 min |
| Record decision | 30 sec | 25 min | 116 min |
| **Total per reviewer** | **2-3 min** | **83-150 min** | **387-619 min** |
| **Both reviewers parallel** | - | **2-3 hrs** | **6.5-10 hrs** |

**Timeline:** 
- Pilot screening: 1 week
- Full screening: 2-3 weeks (with parallel reviewers)
- Conflict resolution: 3-5 days
- **Total: 4-5 weeks for all 232 papers**

---

## Expected Outcomes

### After Title & Abstract Screening

| Metric | Expected Range | Your Case |
|--------|-----------------|-----------|
| Papers screened | 232 | 232 ✓ |
| Inclusion rate (T&A) | 20-40% | ~46-93 papers |
| Exclusion rate | 60-80% | ~139-186 papers |
| Inter-rater agreement | Kappa > 0.60 | Target > 0.70 |
| Papers for full-text | 50-100 | Typical yield |

### Papers Advancing

Expected papers for **Full-Text Screening Stage:**
- Start with: 232 papers with abstracts
- After T&A: 46-93 papers included
- After full-text: Typically 25-75 papers final include
- After quality assessment: Quality-differentiated subset

---

## Step-by-Step Implementation Guide

### Week 1: Pilot Screening

**Monday - Setup:**
```bash
# Step 1: Get pilot sample (25 papers)
mcp_slr-server_list_papers
  limit: 25
  offset: 0

# Returns: Papers 1-25 with titles, years, authors
```

**Tuesday-Wednesday - Pilot Screening:**
```bash
# Step 2: For each paper in pilot sample
# Reviewer 1:
mcp_slr-server_get_paper paper_id=1
  # Review title and abstract
  
mcp_slr-server_screen_paper
  project_id: 1
  paper_id: 1
  reviewer_id: "reviewer1"
  stage: "title_abstract"
  decision: "include"
  confidence_level: 0.95
  reason: "Empirical study of real-time S2ST platform design..."

# Same process for reviewer 2
mcp_slr-server_screen_paper
  project_id: 1
  paper_id: 1
  reviewer_id: "reviewer2"
  stage: "title_abstract"
  decision: "include"
  confidence_level: 0.90
  reason: "Addresses multiple RQs with architecture focus..."

# Repeat for all 25 pilot papers
```

**Thursday - Agreement Analysis:**
```
Calculate inter-rater agreement (Kappa statistic)
- If Kappa > 0.6: Proceed to full screening
- If Kappa < 0.6: Discuss criteria, conduct second pilot
```

**Friday - Prepare for Full Screening:**
- Document pilot results
- Finalize criteria clarifications
- Brief reviewers on full screening schedule

---

### Weeks 2-4: Full Screening (Batch Processing)

**Batch 1 (Papers 1-50):**
```bash
# Get batch 1
mcp_slr-server_list_papers
  limit: 50
  offset: 0

# For each paper 1-50:
#   - mcp_slr-server_get_paper
#   - reviewer1: mcp_slr-server_screen_paper
#   - reviewer2: mcp_slr-server_screen_paper
# Time: 2-3 hours for both reviewers
```

**Batch 2 (Papers 51-100):**
```bash
mcp_slr-server_list_papers
  limit: 50
  offset: 50
# [Same process as Batch 1]
```

**Batch 3 (Papers 101-150):**
```bash
mcp_slr-server_list_papers
  limit: 50
  offset: 100
# [Same process]
```

**Batch 4 (Papers 151-200):**
```bash
mcp_slr-server_list_papers
  limit: 50
  offset: 150
# [Same process]
```

**Batch 5 (Papers 201-232):**
```bash
mcp_slr-server_list_papers
  limit: 32
  offset: 200
# [Same process]
```

---

### Week 5: Conflict Resolution

```bash
# After full screening, identify disagreements
# For each disagreement:

# Paper with conflict example:
Paper 123: reviewer1=Include, reviewer2=Exclude

# Discussion → Final decision
mcp_slr-server_screen_paper
  project_id: 1
  paper_id: 123
  reviewer_id: "reviewer1"  # OR lead reviewer
  stage: "title_abstract"
  decision: "include"       # Final decision after discussion
  confidence_level: 0.75    # Lower confidence due to discussion
  reason: "After discussion with reviewer2, team consensus: 
           paper addresses RQ1 despite initial ambiguity. 
           Classified as INCLUDE."
```

---

## Document Resources Created

### Workflow Documents
✅ `bulk_screening_workflow.md` - Complete workflow guide  
✅ `screening_progress_tracker.md` - Tracking templates  
✅ `evidence_synthesis_plan.md` - Analysis phase planning  

### Reference Documents
✅ `screening_protocol.md` - Detailed screening procedures  
✅ `SLR_SETUP_COMPLETE.md` - Complete SLR protocol  
✅ `prisma_framework.md` - Quality assessment framework  

### Supporting Materials
✅ `search_strings.txt` - All search strings (used to create these 232 papers)  
✅ `PROGRESS_REPORT.md` - Project status tracking  

---

## Quality Assurance Checkpoints

### Before Starting Screening:
- [ ] Both reviewers trained on criteria
- [ ] Pilot papers selected (25 diverse papers)
- [ ] SLR-server tools tested and accessible
- [ ] Tracking spreadsheet prepared

### During Screening:
- [ ] Each reviewer independently screens
- [ ] Decisions recorded with reasoning
- [ ] Confidence levels provided (0-1)
- [ ] Time tracking per batch

### After Each Batch:
- [ ] Calculate batch-level Kappa
- [ ] Spot-check 5% of decisions
- [ ] Document any disagreements
- [ ] Track time estimates vs actual

### At Conclusion:
- [ ] Final inter-rater agreement > 0.60
- [ ] All disagreements resolved
- [ ] Metrics documented
- [ ] Papers ready for full-text screening

---

## Troubleshooting Common Issues

### Issue: Reviewers can't agree (Kappa < 0.60)
**Solution:** Follow conflict resolution in `screening_protocol.md`
1. Identify disagreement patterns
2. Discuss specific criteria interpretations
3. Re-screen disagreement papers
4. Document resolution method

### Issue: Pilot screening not representative
**Solution:** Ensure pilot includes:
- Papers clearly meeting all criteria (easy includes)
- Papers clearly not meeting criteria (easy excludes)
- Borderline/ambiguous papers
- Mix of years and topics

### Issue: Insufficient abstract information
**Solution:** Mark as UNCERTAIN and plan for full-text review
- Record reason: "Insufficient information in abstract"
- Note for full-text stage: "Requires detailed review"

### Issue: Duplicate papers
**Solution:** Mark both papers with code TA-04
- Document which is primary, which is duplicate
- Exclude duplicate
- Note this relationship in reasoning

### Issue: Screening taking longer than estimated
**Solution:** 
- Normal variation is ±20%
- Check for bottlenecks (specific paper types taking longer)
- Consider rotating batches between reviewers for efficiency

---

## Next Steps - THIS WEEK

### Action Items:

**[ ] 1. Confirm Reviewer 2 Assignment** (CRITICAL)
- Must be domain expert in speech translation
- Confirm 4-5 week availability
- Availability for training meeting

**[ ] 2. Schedule Reviewer Training** (Within 3 days)
- Meeting: Both reviewers + lead
- Duration: 1 hour
- Agenda: 
  - Review PRISMA principles
  - Discuss inclusion/exclusion criteria with examples
  - Walk through 2-3 sample papers
  - Discuss conflict resolution process

**[ ] 3. Prepare Screening Tools** (Within 3 days)
- Set up tracking spreadsheet (Excel/Google Sheets)
- Verify SLR-server access for both reviewers
- Test `mcp_slr-server_screen_paper` tool
- Prepare 25-paper pilot sample

**[ ] 4. Begin Pilot Screening** (By end of week)
- Both reviewers independently screen 25 papers
- Record all decisions with reasoning
- Calculate agreement metrics

**[ ] 5. Document Pilot Results** (Week 1 Friday)
- Calculate Cohen's Kappa
- Identify disagreement patterns
- Document criteria clarifications needed
- Decide: Proceed to full screening or conduct second pilot?

---

## Success Criteria for T&A Screening

### Minimum Acceptable:
- ✓ All 232 papers screened
- ✓ Both reviewers participate
- ✓ Inter-rater Kappa ≥ 0.60
- ✓ All disagreements resolved
- ✓ 46-93 papers advanced to full-text

### Excellent Outcomes:
- ✓ Inter-rater Kappa ≥ 0.70
- ✓ < 5% of papers requiring discussion
- ✓ High reviewer confidence (avg > 0.80)
- ✓ Completed within 4-5 weeks
- ✓ Comprehensive reasoning documented

---

## Resources Provided

| Resource | Location | Purpose |
|----------|----------|---------|
| Bulk Screening Workflow | `screening/bulk_screening_workflow.md` | Complete workflow guide |
| Progress Tracker Template | `screening/screening_progress_tracker.md` | Track decisions |
| Screening Protocol | `screening/screening_protocol.md` | Detailed procedures |
| Inclusion/Exclusion Criteria | `SLR_SETUP_COMPLETE.md` | Decision guidance |
| Quality Framework | `quality-assessment/prisma_framework.md` | PRISMA standards |
| Analysis Plan | `analysis/evidence_synthesis_plan.md` | Post-screening phase |

---

## Final Checklist Before Starting

- [ ] 232 papers imported and metadata extracted ✓
- [ ] SLR-server tools operational ✓
- [ ] Reviewer 1 confirmed ✓
- [ ] Reviewer 2 [CONFIRM THIS WEEK]
- [ ] Screening criteria reviewed and approved ✓
- [ ] Tracking templates prepared [CREATE THIS WEEK]
- [ ] Training session scheduled [SCHEDULE THIS WEEK]
- [ ] Pilot papers identified [DO THIS WEEK]
- [ ] Tools tested and working [TEST THIS WEEK]
- [ ] Team ready to begin [BY END OF WEEK]

---

**Status:** 232 papers ready for screening. SLR-server tools operational. Ready to execute bulk screening workflow upon confirmation of reviewer2 and completion of training meeting.

**Next Action:** Contact reviewer2 for confirmation and schedule training meeting for this week.

---

**Document Version:** 1.0  
**Status:** READY FOR IMPLEMENTATION  
**Last Updated:** October 19, 2025  

**Prepared for:** SLR Project on Real-Time Speech Translation Platforms  
**Contact:** [reviewer1 / Project Lead]
