# Using Enhanced get_paper in SLR Screening Workflow

## Quick Start Guide

The enhanced `get_paper` MCP tool now delivers complete paper information for screening decisions.

## Typical Usage Pattern

### Phase 1: Title-Abstract Screening

```python
# Reviewer calls get_paper to retrieve complete paper info
paper_info = await mcp_server.get_paper(paper_id=5)

# Paper information includes:
# - Title and authors (for relevance check)
# - Publication year (for recency check)
# - Abstract (for scope and methodology check)
# - Keywords (for topic alignment check)
# - Tags (showing paper source)

# Reviewer makes decision based on:
# ✅ Is the paper about speech translation? (Check title/abstract)
# ✅ Is it published peer-reviewed? (Check tags and journal)
# ✅ Does it match our focus? (Check keywords and abstract)
# ✅ Is methodology compatible? (Check abstract)

# Record decision:
await mcp_server.screen_paper(
    project_id=1,
    paper_id=5,
    reviewer_id="reviewer1",
    stage="title_abstract",
    decision="include",
    confidence_level=0.95,
    reason="Directly addresses real-time S2ST platform design with neural approaches"
)
```

### Phase 2: Full-Text Screening

```python
# For papers that passed title-abstract screening
paper_info = await mcp_server.get_paper(paper_id=5)

# Now reviewers have access to:
# - Complete abstract (verify scope)
# - Full text extracted from paper (if available)
# - Methodology and study type (assess quality)
# - All metadata (for evidence extraction)

# Reviewer assesses:
# ✅ Does methodology match inclusion criteria?
# ✅ Is data extraction feasible?
# ✅ Are results clearly reported?
# ✅ Any quality concerns?

# Record quality assessment and final decision:
await mcp_server.screen_paper(
    project_id=1,
    paper_id=5,
    reviewer_id="reviewer1",
    stage="full_text",
    decision="include",
    confidence_level=0.9,
    reason="Clear methodology, comprehensive evaluation on 3 datasets, direct relevance to platform design"
)
```

## Screening Workflow with Enhanced get_paper

### Week 1: Pilot Screening (20-25 papers)

**Day 1-2: Preparation**
```
1. Select diverse pilot sample (mix of clear include/exclude/uncertain)
2. Brief reviewers on enhanced get_paper capabilities
3. Set up tracking spreadsheet
4. Conduct first 2-3 papers as team to calibrate
```

**Day 3-4: Pilot Screening**
```
FOR EACH PILOT PAPER:
  1. Reviewer 1: Call get_paper(paper_id)
  2. Reviewer 1: Review title, abstract, keywords
  3. Reviewer 1: Make decision (include/exclude/uncertain)
  4. Reviewer 1: Record via screen_paper()
  
  5. Reviewer 2: Call get_paper(paper_id)
  6. Reviewer 2: Review same content
  7. Reviewer 2: Make independent decision
  8. Reviewer 2: Record via screen_paper()

  9. System: Calculate inter-rater agreement
  10. If disagreement: Meet to discuss and calibrate
```

**Day 5: Analysis**
```
1. Calculate Cohen's Kappa on pilot sample
2. If Kappa > 0.60: Proceed to full screening
3. If Kappa < 0.60: Discuss disagreements, refine criteria, repeat with new sample
```

### Weeks 2-3: Full Title-Abstract Screening (79-84 papers)

**Batch 1: Papers 1-35**
```
PARALLEL REVIEW (8 papers per reviewer per day):
- Reviewer 1: get_paper + decision for papers 1-35
- Reviewer 2: get_paper + decision for papers 1-35
- Both independently assess
- System tracks progress
- Expected time: 2 days
```

**Batch 2: Papers 36-70**
```
Same process for second batch
- Expected time: 2 days
- Inter-rater agreement tracked
- Any disagreements noted
```

**Batch 3: Papers 71-104**
```
Same process for final batch
- Expected time: 1.5-2 days
- Final inter-rater metrics calculated
```

### Week 4: Conflict Resolution

```
FOR PAPERS WITH DISAGREEMENTS:
  1. Identify papers where Reviewer1 decision ≠ Reviewer2 decision
  2. For each conflicted paper:
     - Reviewer1 calls get_paper() to prepare
     - Reviewer2 calls get_paper() to prepare
     - Meet to discuss reasoning
     - Review abstract + metadata together
     - If needed, brief full-text review
     - Reach consensus on final decision
     - Document resolution method
  
  3. Record final decision via screen_paper()
  4. Calculate final Cohen's Kappa
  5. Generate screening report
```

## get_paper Response Contents for Screening

### What Reviewers See

```
📄 **Paper ID:** 5
📝 **Title:** [Paper title - CHECK RELEVANCE]
✍️ **Authors:** [Authors - CHECK EXPERTISE]
📅 **Year:** [Year - CHECK RECENCY]
🔗 **DOI:** [DOI - CHECK PUBLICATION]

--- ABSTRACT ---
[FULL ABSTRACT - PRIMARY SCREENING BASIS]
[Review this for:
  - Research focus alignment
  - Methodology compatibility
  - Data requirements
  - Scope match]

--- KEYWORDS ---
[Keywords - CHECK TOPIC ALIGNMENT]
[Review this for:
  - Primary topics covered
  - Related domains
  - Study focus]

--- FULL TEXT ---
[EXTRACTED TEXT - FOR FULL-TEXT PHASE]
[Use this to:
  - Verify methodology details
  - Check data quality
  - Extract findings
  - Assess limitations]

--- METADATA ---
🏷️ **Tags:** [Tags - CHECK SOURCE]
[Review this for:
  - Import source
  - Initial categorization
  - Data lineage]
```

## Decision Criteria Integration

### Using get_paper for Inclusion/Exclusion

**Inclusion Criteria (check against abstract/metadata):**

1. **Empirical Study** ← Check abstract for "experiment", "evaluation", "dataset"
2. **Architecture/Design Focus** ← Check title and keywords for "platform", "system", "design"
3. **Real-time/Simultaneous** ← Check abstract for "real-time", "simultaneous", "low-latency"
4. **Multilingual Systems** ← Check keywords for multiple language pairs
5. **ML/Deep Learning** ← Check for "neural", "deep learning", "transformer", "LSTM"
6. **Scalability Focus** ← Check abstract for "scale", "efficiency", "deployment"
7. **Performance Evaluation** ← Check for "evaluate", "metrics", "BLEU", "benchmark"
8. **Peer-Reviewed** ← Check tags and publication venue

**Exclusion Criteria (use get_paper to verify):**

1. **Statistical MT Only** ← If abstract mentions only "statistical MT" without neural
2. **Text Translation Only** ← If no mention of speech in title/abstract
3. **Non-English/Insufficient** ← Check title/abstract language, keywords
4. **Insufficient Detail** ← If abstract is very sparse or vague
5. **Theoretical Only** ← If no "evaluate", "dataset", "experiment" mentioned
6. **Out of Scope** ← If keywords don't match SLR focus
7. **Quality Issues** ← If obvious grammar/clarity problems in abstract
8. **Gray Literature** ← Check tags for publication type

## Practical Screening Examples

### Example 1: INCLUDE Decision

```
get_paper(5) returns:
- Title: "Real-Time Speech-to-Speech Translation Platform Architecture"
- Authors: [Domain experts in speech processing]
- Year: 2024
- Abstract: "We present an end-to-end neural S2ST platform with low-latency 
            requirements. System architecture combines transformer-based ASR 
            with multilingual NMT. Evaluation on 5 language pairs shows..."
- Keywords: speech translation, neural, real-time, platform, multilingual

DECISION: INCLUDE ✅
REASON: Directly addresses platform design with neural approaches, 
        real-time focus, empirical evaluation on multiple pairs
CONFIDENCE: 0.95
```

### Example 2: EXCLUDE Decision

```
get_paper(42) returns:
- Title: "Statistical Approaches to Machine Translation"
- Authors: [MT specialists]
- Year: 2015
- Abstract: "We explore statistical phrase-based translation models..."
- Keywords: SMT, phrases, word alignment

DECISION: EXCLUDE ❌
REASON: Statistical MT only (not neural), no speech component, 
        pre-dating neural approaches
CONFIDENCE: 0.98
```

### Example 3: UNCERTAIN Decision

```
get_paper(78) returns:
- Title: "Low-Resource Language Translation via Transfer Learning"
- Authors: [NLP researchers]
- Year: 2023
- Abstract: "We propose transfer learning approaches for low-resource 
            translation. While primarily text-focused, methods may apply 
            to speech translation. We evaluate on..."
- Keywords: transfer learning, low-resource, NMT

DECISION: UNCERTAIN ?
REASON: While text-focused, transfer learning approach might be applicable
        to S2ST. Needs full-text review to determine speech relevance.
CONFIDENCE: 0.55
ACTION: Advance to full-text screening for detailed assessment
```

## Performance Tips

1. **Batch Review**: Both reviewers review same 3-5 papers first to calibrate
2. **Use Full Info**: Don't just scan title - always read abstract
3. **Note Uncertainties**: Mark papers requiring team discussion
4. **Track Time**: Monitor screening pace (target: ~5 min per paper for T&A phase)
5. **Document Reasoning**: Always record reason for decision (1-2 sentences)
6. **Confidence Levels**: 0.9-1.0 = clear decision, 0.5-0.7 = uncertain, needs team review

## Troubleshooting

### Abstract Missing
```
If get_paper returns "[No abstract available]":
- Use title and keywords for decision
- If cannot decide from title alone: UNCERTAIN
- Note in screening comments for team discussion
```

### Full Text Truncated
```
If get_paper shows "[... truncated. Total: XXXXX chars]":
- Abstract is available for T&A screening
- For full-text phase, retrieve original paper
- Note file availability in screening comments
```

### Conflicting Metadata
```
If title and abstract seem misaligned:
- Prioritize abstract over title
- Use keywords to disambiguate
- Mark for team discussion
```

## Integration Checklist

Before starting screening with enhanced get_paper:

- [ ] Both reviewers trained on workflow
- [ ] get_paper tested with sample papers
- [ ] Screen_paper tool tested and working
- [ ] Tracking spreadsheet set up
- [ ] Decision criteria reviewed and agreed
- [ ] Pilot papers selected (20-25 diverse samples)
- [ ] Training meeting scheduled
- [ ] Calibration examples reviewed
- [ ] Contact method for questions established
- [ ] Progress tracking method defined

---

**Ready to screen?** Start with the pilot sample and track results carefully!
