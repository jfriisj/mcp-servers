# Screening Documentation
## Real-Time Speech Translation Platform SLR

**Project:** real-time-translation-platform  
**Date Created:** October 19, 2025

---

## Screening Workflow Setup

### Stage 1: Title & Abstract Screening
- **Objective:** Identify papers potentially relevant to research questions
- **Criteria:** Does title/abstract suggest relevance to RQ1-RQ4?
- **Decision Options:** INCLUDE, EXCLUDE, UNCERTAIN
- **Reviewers:** 2 independent reviewers (reviewer1, reviewer2)
- **Target Inter-rater Agreement (Kappa):** > 0.6
- **Average Time per Paper:** 2-3 minutes

#### Inclusion Criteria for T&A Screening:
1. Mentions speech translation OR simultaneous interpretation
2. References platform, architecture, system, or framework
3. Discusses real-time, streaming, or low-latency aspects
4. Appears to be peer-reviewed research

#### Exclusion Criteria for T&A Screening:
1. Clearly text-only translation (no speech component)
2. General translation theory without system implementation
3. Opinion pieces or editorials
4. Non-English publications
5. Obvious false positives

---

### Stage 2: Full-Text Screening
- **Objective:** Verify full-text compliance with inclusion/exclusion criteria
- **Criteria:** Does full paper meet ALL inclusion criteria and NONE of exclusion criteria?
- **Decision Options:** INCLUDE with rationale, EXCLUDE with reason code
- **Reviewers:** 2 independent reviewers
- **Target Inter-rater Agreement (Kappa):** > 0.6
- **Average Time per Paper:** 15-30 minutes

#### Full Inclusion Criteria:
IC1: Studies addressing real-time speech translation systems
IC2: Papers on platform architecture and design patterns
IC3: Research on multilingual translation systems
IC4: Studies discussing system performance and latency
IC5: Papers on machine learning models for speech translation
IC6: Research on scalability and deployment strategies
IC7: Studies with empirical evaluation or case studies
IC8: Published in peer-reviewed venues

#### Full Exclusion Criteria:
EC1: Papers focused solely on statistical machine translation without speech
EC2: Studies on text-only translation systems
EC3: Non-English or non-scholarly publications
EC4: Papers with less than 3 pages substantive content
EC5: Studies on specific language pairs only (not generalizable)
EC6: Opinion papers without empirical evidence
EC7: Papers older than 2010 without historical relevance
EC8: Duplicate or substantially overlapping publications
EC9: Severe methodological limitations
EC10: Non-peer-reviewed online content

---

### Stage 3: Final Selection & Data Extraction
- **Objective:** Confirmed eligibility and data extraction readiness
- **Activities:** Full data extraction, quality assessment
- **Reviewer:** Lead reviewer (reviewer1) with quality check

---

## Reviewer Assignment

| Reviewer | Role | Expertise | Status |
|----------|------|-----------|--------|
| reviewer1 | Lead Reviewer | Systematic review methodology, screening coordination | Active |
| reviewer2 | Domain Expert | Speech translation, NLP systems | To be assigned |

---

## Screening Progress Tracking

### Current Status (as of 2025-10-19)

**Title & Abstract Screening:**
- Total papers to screen: 150 (initial sample)
- Papers screened: 75
- Papers marked for full-text: ~50
- Papers excluded at T&A: ~25
- Agreement rate (pilot): Pending

**Full-Text Screening:**
- Papers to screen: TBD
- Papers screened: 0
- Papers included: 0
- Papers excluded: 0

**Quality Assessment:**
- Papers assessed: 1 (initial paper)
- High quality: 1
- Moderate quality: 0
- Low quality: 0

---

## Conflict Resolution Protocol

### If Reviewers Disagree at T&A Stage:

1. **Step 1 - Discussion Round (30 minutes)**
   - Reviewers discuss reasoning for different decisions
   - Focus on understanding different interpretation of criteria
   - Attempt to reach consensus

2. **Step 2 - Criteria Clarification (30 minutes)**
   - Review inclusion/exclusion criteria together
   - Discuss ambiguous cases
   - Document clarifications for consistency

3. **Step 3 - Re-evaluation with Clarified Criteria**
   - Each reviewer independently re-evaluates paper
   - Record new decisions

4. **Step 4 - Mediation (if still disagreement)**
   - Lead reviewer (reviewer1) makes final decision
   - Document decision rationale
   - Record as "consensus after discussion"

5. **Step 5 - Documentation**
   - Record original decisions
   - Note reason for disagreement
   - Document final decision and rationale

### If Reviewers Disagree at Full-Text Stage:

Same protocol as above, with extended discussion time (60 minutes) given higher stakes.

---

## Screening Decision Form Template

```
Screening ID: [Auto-generated]
Paper ID: [Internal ID]
Title: [Paper title]
Authors: [Author names]
Year: [Publication year]

TITLE & ABSTRACT SCREENING
Reviewer ID: [reviewer1 or reviewer2]
Decision: [INCLUDE / EXCLUDE / UNCERTAIN]
Reason Code: [See codes below]
Confidence: [1-5 scale, 5=very confident]
Time Spent: [minutes]

FULL-TEXT SCREENING (when applicable)
Reviewer ID: [reviewer1 or reviewer2]
Decision: [INCLUDE / EXCLUDE]

If INCLUDE:
  - Quality Score: [0-12]
  - Ready for Data Extraction: [Yes/No]

If EXCLUDE:
  - Exclusion Code: [EC1-EC10]
  - Detailed Reason: [Free text]

Notes: [Any additional comments]
```

---

## Exclusion Reason Codes

### Title & Abstract Screening:
- TA-01: Not about speech translation
- TA-02: Not about systems/platforms/architecture
- TA-03: Appears to be non-peer-reviewed
- TA-04: Obviously non-English
- TA-05: Unclear/uncertain relevance - defer to full-text
- TA-06: Text-only translation, no speech component
- TA-07: Opinion piece, no empirical content

### Full-Text Screening:
- EC1: Statistical MT without speech component
- EC2: Text-only translation system
- EC3: Non-English or non-scholarly
- EC4: Insufficient content (< 3 pages)
- EC5: Language pair specific only
- EC6: Opinion paper without evidence
- EC7: Pre-2010 without historical significance
- EC8: Duplicate publication
- EC9: Severe methodological flaws
- EC10: Non-peer-reviewed

---

## Pilot Screening Results

**Target:** 50-100 papers
**Purpose:** Calibrate reviewers and test inclusion/exclusion criteria
**Status:** Pending (to be conducted Week 2)

### Expected Outcomes:
- [ ] Calculate inter-rater reliability (target Kappa > 0.6)
- [ ] Identify ambiguous inclusion/exclusion cases
- [ ] Refine criteria if needed
- [ ] Document lessons learned
- [ ] Proceed to full screening if agreement adequate

---

## Documentation Standards

### For Every Screening Decision:
- [ ] Decision clearly documented
- [ ] Reason code/classification applied
- [ ] Reviewer identity recorded
- [ ] Date of decision recorded
- [ ] Rationale available (especially for exclusions)
- [ ] Any conflicts with co-reviewer noted

### Screening Log Maintenance:
- [ ] Log updated daily during screening
- [ ] Running totals maintained
- [ ] Problems/issues flagged immediately
- [ ] Communication between reviewers recorded
- [ ] Decisions linked to papers in database

---

## Quality Checks

### Weekly Reviews:
- [ ] Percentage agreement calculated
- [ ] Exclusion reasons analyzed for patterns
- [ ] Any systematic disagreements identified
- [ ] Criteria clarification needed?

### Monthly Reviews:
- [ ] Overall screening progress vs. target
- [ ] Time estimates updated
- [ ] Any scope creep identified
- [ ] Reviewer workload balanced

---

## Next Steps

1. **Immediate (This Week):**
   - [ ] Finalize reviewer2 assignment
   - [ ] Conduct reviewer training session
   - [ ] Prepare screening materials
   - [ ] Set up screening database/spreadsheet

2. **Short-term (Week 2):**
   - [ ] Execute pilot screening (50-100 papers)
   - [ ] Calculate inter-rater agreement
   - [ ] Refine criteria if Kappa < 0.6
   - [ ] Document pilot results

3. **Medium-term (Weeks 3-5):**
   - [ ] Complete title & abstract screening (all papers)
   - [ ] Retrieve full texts for included papers
   - [ ] Begin full-text screening

4. **Ongoing:**
   - [ ] Maintain regular communication between reviewers
   - [ ] Document any protocol deviations
   - [ ] Update progress tracking

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Next Review:** After pilot screening completion
