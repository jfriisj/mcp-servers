# Research Guide for SLR MCP Server

A comprehensive guide for academic researchers using the Systematic Literature Review MCP Server.

## Table of Contents

1. [Introduction to Systematic Literature Reviews](#introduction)
2. [Academic Standards and Frameworks](#standards)
3. [Getting Started](#getting-started)
4. [Complete Workflow Examples](#workflows)
5. [Advanced Research Techniques](#advanced)
6. [Quality Assurance Best Practices](#quality)
7. [Troubleshooting Common Issues](#troubleshooting)

## Introduction to Systematic Literature Reviews {#introduction}

A systematic literature review is a rigorous and transparent method for identifying, evaluating, and synthesizing research evidence on a specific topic. Unlike traditional narrative reviews, systematic reviews follow structured protocols to minimize bias and ensure reproducibility.

### Key Components of a Systematic Review

1. **Protocol Development**: Define research questions, search strategy, and inclusion/exclusion criteria
2. **Literature Search**: Comprehensive search across multiple databases
3. **Study Selection**: Screen and select relevant studies based on predefined criteria
4. **Quality Assessment**: Evaluate the methodological quality of included studies
5. **Data Extraction**: Extract relevant data from included studies
6. **Data Synthesis**: Analyze and synthesize findings, potentially through meta-analysis
7. **Reporting**: Present findings following established guidelines (PRISMA)

## Academic Standards and Frameworks {#standards}

The SLR MCP Server implements several established academic frameworks:

### PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses)

PRISMA provides a checklist of 27 items that should be included in systematic reviews:

- **Title and Abstract**: Clear identification as a systematic review
- **Introduction**: Rationale and objectives
- **Methods**: Protocol registration, eligibility criteria, search strategy
- **Results**: Study selection, characteristics, risk of bias
- **Discussion**: Summary of evidence, limitations, conclusions

**Usage in SLR Server:**
```bash
# Assess papers using PRISMA framework
mcp call assess-quality --paper-id 1 --framework "prisma" --reviewer-id "researcher_001"
```

### PICO Framework (Population, Intervention, Comparison, Outcome)

PICO helps structure clinical research questions:

- **Population**: Who are the participants?
- **Intervention**: What intervention is being studied?
- **Comparison**: What is it compared to?
- **Outcome**: What are the measured outcomes?

**Example PICO Question:**
"In adults with Type 2 diabetes (P), does metformin therapy (I) compared to lifestyle modification alone (C) reduce HbA1c levels (O)?"

**Usage in SLR Server:**
```bash
# Validate research question using PICO
mcp call validate-research-question \
  --question "In adults with Type 2 diabetes, does metformin therapy compared to lifestyle modification alone reduce HbA1c levels?" \
  --framework "pico"
```

### SPIDER Framework (Sample, Phenomenon of Interest, Design, Evaluation, Research type)

SPIDER is used for qualitative and mixed-methods research questions:

- **Sample**: Who are the participants?
- **Phenomenon of Interest**: What is being studied?
- **Design**: What study design is required?
- **Evaluation**: What outcomes are measured?
- **Research type**: What research methodology is appropriate?

### GRADE Framework (Grading of Recommendations Assessment, Development and Evaluation)

GRADE provides a systematic approach to rating the quality of evidence:

**Quality Ratings:**
- **High**: Very confident in the effect estimate
- **Moderate**: Moderately confident in the effect estimate
- **Low**: Limited confidence in the effect estimate
- **Very Low**: Very little confidence in the effect estimate

**Factors affecting evidence quality:**
- Study design limitations
- Inconsistency of results
- Indirectness of evidence
- Imprecision
- Publication bias

## Getting Started {#getting-started}

### 1. Define Your Research Question

Start by clearly defining your research question using appropriate frameworks:

```bash
# Validate your research question
mcp call validate-research-question \
  --question "How effective are machine learning algorithms in improving diagnostic accuracy in healthcare compared to traditional methods?" \
  --framework "pico" \
  --suggest-improvements true
```

**Response example:**
```json
{
  "success": true,
  "data": {
    "validity_score": 8.7,
    "framework_components": {
      "population": "Healthcare patients requiring diagnosis",
      "intervention": "Machine learning diagnostic algorithms",
      "comparison": "Traditional diagnostic methods",
      "outcome": "Diagnostic accuracy improvement"
    },
    "suggestions": [
      "Consider specifying the healthcare domain (e.g., radiology, pathology)",
      "Define specific accuracy metrics (sensitivity, specificity, AUC)"
    ]
  }
}
```

### 2. Upload and Process Papers

Upload your research papers for analysis:

```bash
# Upload individual papers
mcp call upload-paper \
  --file-path "/papers/smith2023_ml_diagnostics.pdf" \
  --title "Machine Learning in Medical Diagnostics: A Systematic Review" \
  --doi "10.1000/ml-diagnostics-2023" \
  --tags ["machine-learning", "diagnostics", "healthcare"]

# Batch upload multiple papers
for paper in /papers/ml_healthcare/*.pdf; do
    mcp call upload-paper --file-path "$paper"
done
```

### 3. Assess Paper Quality

Conduct systematic quality assessment:

```bash
# PRISMA-compliant assessment
mcp call assess-quality \
  --paper-id 1 \
  --framework "prisma" \
  --reviewer-id "reviewer_001" \
  --criterion-scores '{
    "study_design": {"score": 8.5, "notes": "Well-designed RCT"},
    "methodology": {"score": 7.8, "notes": "Appropriate sample size"},
    "reporting": {"score": 9.0, "notes": "Excellent reporting quality"}
  }'
```

## Complete Workflow Examples {#workflows}

### Workflow 1: Clinical Effectiveness Review

**Research Question:** "Are telehealth interventions effective for managing chronic diseases compared to in-person care?"

```bash
# Step 1: Validate research question
mcp call validate-research-question \
  --question "Are telehealth interventions effective for managing chronic diseases compared to in-person care?" \
  --framework "pico"

# Step 2: Upload relevant papers
papers=("telehealth_diabetes_2023.pdf" "remote_monitoring_heart_disease.pdf" "virtual_care_effectiveness.pdf")
for paper in "${papers[@]}"; do
    mcp call upload-paper --file-path "/papers/$paper"
done

# Step 3: Quality assessment with multiple reviewers
for paper_id in {1..3}; do
    # Primary reviewer
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "prisma" \
      --reviewer-id "clinical_reviewer_1"
    
    # Secondary reviewer
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "prisma" \
      --reviewer-id "clinical_reviewer_2"
done

# Step 4: Calculate inter-rater reliability
mcp call calculate-interrater-reliability --paper-ids [1,2,3]

# Step 5: Citation network analysis
for paper_id in {1..3}; do
    mcp call analyze-citations \
      --paper-id $paper_id \
      --include-network true \
      --depth 2
done

# Step 6: Index papers for analysis
for paper_id in {1..3}; do
    mcp call index-paper \
      --paper-id $paper_id \
      --strategy "academic-section" \
      --optimize-for-agents true
done

# Step 7: Hypothesis testing
mcp call analyze-hypothesis \
  --paper-ids [1,2,3] \
  --hypothesis "Telehealth interventions are as effective as in-person care for chronic disease management" \
  --meta-analysis true

# Step 8: Evidence synthesis
mcp call synthesize-evidence \
  --research-question-id 1 \
  --paper-ids [1,2,3] \
  --include-grade-assessment true
```

### Workflow 2: Technology Adoption Review

**Research Question:** "What factors influence healthcare professionals' adoption of AI-powered diagnostic tools?"

```bash
# Step 1: Validate qualitative research question
mcp call validate-research-question \
  --question "What factors influence healthcare professionals' adoption of AI-powered diagnostic tools?" \
  --framework "spider"

# Response includes SPIDER components:
# - Sample: Healthcare professionals
# - Phenomenon: AI adoption factors
# - Design: Qualitative/mixed methods
# - Evaluation: Adoption barriers and facilitators
# - Research type: Qualitative synthesis

# Step 2: Upload qualitative and mixed-methods studies
qualitative_papers=("ai_adoption_barriers.pdf" "physician_attitudes_ai.pdf" "implementation_challenges.pdf")
for paper in "${qualitative_papers[@]}"; do
    mcp call upload-paper --file-path "/papers/qualitative/$paper"
done

# Step 3: Quality assessment using appropriate framework
for paper_id in {4..6}; do
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "casp_qualitative" \
      --reviewer-id "qualitative_reviewer"
done

# Step 4: Thematic analysis
mcp call analyze-themes \
  --paper-ids [4,5,6] \
  --analysis-type "thematic_synthesis" \
  --coding-framework "inductive"
```

### Workflow 3: Meta-Analysis

**Research Question:** "What is the pooled effect size of machine learning interventions on diagnostic accuracy?"

```bash
# Step 1: Upload quantitative studies with effect sizes
quantitative_papers=("rct_ml_radiology.pdf" "diagnostic_accuracy_study.pdf" "ml_pathology_trial.pdf")
for paper in "${quantitative_papers[@]}"; do
    mcp call upload-paper --file-path "/papers/quantitative/$paper"
done

# Step 2: Extract effect sizes and confidence intervals
for paper_id in {7..9}; do
    mcp call extract-effect-sizes \
      --paper-id $paper_id \
      --outcome-type "diagnostic_accuracy" \
      --effect-measure "sensitivity_specificity"
done

# Step 3: Assess risk of bias
for paper_id in {7..9}; do
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "robins_i" \
      --reviewer-id "meta_analysis_reviewer"
done

# Step 4: Perform meta-analysis
mcp call perform-meta-analysis \
  --paper-ids [7,8,9] \
  --effect-measure "sensitivity" \
  --analysis-model "random_effects" \
  --heterogeneity-test true \
  --publication-bias-test "funnel_plot"
```

## Advanced Research Techniques {#advanced}

### Network Meta-Analysis

For comparing multiple interventions:

```bash
# Network meta-analysis comparing multiple AI approaches
mcp call network-meta-analysis \
  --paper-ids [1,2,3,4,5,6,7,8,9] \
  --interventions ["deep_learning", "random_forest", "svm", "traditional_methods"] \
  --outcome "diagnostic_accuracy" \
  --network-geometry "star" \
  --ranking-method "sucra"
```

### Individual Patient Data (IPD) Meta-Analysis

When raw data is available:

```bash
# IPD meta-analysis
mcp call ipd-meta-analysis \
  --data-files ["/data/study1.csv", "/data/study2.csv", "/data/study3.csv"] \
  --outcome-variable "diagnostic_accuracy" \
  --covariates ["age", "gender", "disease_severity"] \
  --analysis-level "patient"
```

### Living Systematic Reviews

For continuously updated reviews:

```bash
# Set up automated search monitoring
mcp call setup-living-review \
  --search-strategy "automated_monthly" \
  --databases ["pubmed", "embase", "cochrane"] \
  --alert-threshold "new_rct" \
  --auto-screening true
```

## Quality Assurance Best Practices {#quality}

### 1. Multiple Reviewer Assessment

Always use multiple reviewers for quality assessment:

```bash
# Primary and secondary reviewer workflow
reviewers=("reviewer_001" "reviewer_002")
for paper_id in {1..10}; do
    for reviewer in "${reviewers[@]}"; do
        mcp call assess-quality \
          --paper-id $paper_id \
          --framework "prisma" \
          --reviewer-id $reviewer
    done
done

# Calculate agreement
mcp call calculate-inter-rater-reliability \
  --paper-ids [1,2,3,4,5,6,7,8,9,10] \
  --agreement-measure "kappa"
```

### 2. Protocol Registration

Register your protocol before beginning:

```bash
# Document your protocol
mcp call register-protocol \
  --title "Machine Learning in Healthcare Diagnostics: A Systematic Review" \
  --research-question "PICO-formatted question" \
  --search-strategy "detailed search terms and databases" \
  --inclusion-criteria "clearly defined criteria" \
  --exclusion-criteria "clearly defined criteria" \
  --registry "prospero"
```

### 3. Search Strategy Documentation

Document comprehensive search strategies:

```bash
# Document search performed
mcp call document-search \
  --database "pubmed" \
  --search-terms '("machine learning" OR "artificial intelligence") AND ("diagnostic accuracy" OR "diagnosis") AND ("healthcare" OR "medical")' \
  --filters "human studies, English, 2010-2023" \
  --results-count 1247 \
  --search-date "2023-10-14"
```

### 4. Risk of Bias Assessment

Implement systematic bias assessment:

```bash
# Cochrane Risk of Bias tool
mcp call assess-bias \
  --paper-id 1 \
  --tool "rob2" \
  --domains ["randomization", "deviations", "missing_outcome", "measurement", "selection"] \
  --assessor "bias_reviewer_001"
```

## Troubleshooting Common Issues {#troubleshooting}

### Issue 1: Low Inter-Rater Agreement

**Symptoms:** Kappa coefficient < 0.6

**Solutions:**
```bash
# Check reviewer training
mcp call analyze-disagreements \
  --paper-ids [1,2,3] \
  --reviewers ["reviewer_001", "reviewer_002"] \
  --identify-patterns true

# Consensus meeting
mcp call conduct-consensus-meeting \
  --disagreements-list "generated from analysis" \
  --resolution-method "discussion"

# Additional reviewer
mcp call add-third-reviewer \
  --paper-ids [disputed_papers] \
  --reviewer-id "senior_reviewer"
```

### Issue 2: High Heterogeneity in Meta-Analysis

**Symptoms:** I² > 75%

**Solutions:**
```bash
# Investigate sources of heterogeneity
mcp call investigate-heterogeneity \
  --meta-analysis-id 1 \
  --subgroup-analyses ["study_design", "population", "intervention_type"] \
  --meta-regression-variables ["sample_size", "study_quality", "publication_year"]

# Consider random effects model
mcp call update-meta-analysis \
  --analysis-id 1 \
  --model "random_effects" \
  --prediction-interval true
```

### Issue 3: Publication Bias Detected

**Symptoms:** Asymmetric funnel plot

**Solutions:**
```bash
# Publication bias testing
mcp call test-publication-bias \
  --meta-analysis-id 1 \
  --tests ["egger", "begg", "peters"] \
  --funnel-plot true

# Adjust for publication bias
mcp call adjust-publication-bias \
  --meta-analysis-id 1 \
  --method "trim_and_fill" \
  --impute-missing true
```

### Issue 4: Insufficient Data for Meta-Analysis

**Symptoms:** < 3 studies with comparable data

**Solutions:**
```bash
# Narrative synthesis
mcp call narrative-synthesis \
  --paper-ids [1,2,3,4,5] \
  --synthesis-method "vote_counting" \
  --harvest-plots true \
  --textual-description true

# Contact authors for additional data
mcp call generate-author-contact-requests \
  --paper-ids [1,2,3] \
  --requested-data ["means", "standard_deviations", "sample_sizes"] \
  --template "standard_request"
```

## Best Practice Checklists

### Pre-Review Checklist

- [ ] Research question clearly defined using PICO/SPIDER
- [ ] Protocol registered in appropriate registry
- [ ] Search strategy developed and documented
- [ ] Inclusion/exclusion criteria clearly defined
- [ ] Data extraction form prepared
- [ ] Quality assessment tools selected
- [ ] Review team assembled with appropriate expertise

### During Review Checklist

- [ ] Comprehensive search across multiple databases
- [ ] Duplicate removal documented
- [ ] Screening process documented (PRISMA flow diagram)
- [ ] Quality assessment completed by multiple reviewers
- [ ] Inter-rater reliability calculated and reported
- [ ] Data extraction completed systematically
- [ ] Risk of bias assessment completed

### Post-Review Checklist

- [ ] Results synthesized appropriately
- [ ] Heterogeneity assessed and reported
- [ ] Publication bias evaluated
- [ ] GRADE assessment completed
- [ ] Limitations clearly stated
- [ ] PRISMA checklist completed
- [ ] Protocol deviations documented

## Additional Resources

### Academic Guidelines
- [PRISMA Statement](http://www.prisma-statement.org/)
- [Cochrane Handbook](https://training.cochrane.org/handbook)
- [GRADE Guidelines](https://www.gradeworkinggroup.org/)
- [PROSPERO Registry](https://www.crd.york.ac.uk/prospero/)

### Quality Assessment Tools
- [Cochrane Risk of Bias Tools](https://www.cochrane.org/bias)
- [CASP Checklists](https://casp-uk.net/casp-tools-checklists/)
- [JBI Critical Appraisal Tools](https://jbi.global/critical-appraisal-tools)

### Statistical Resources
- [Meta-Analysis Guidelines](https://www.bmj.com/content/374/bmj.n1864)
- [Network Meta-Analysis](https://www.nature.com/articles/s41591-021-01480-3)
- [Publication Bias Detection](https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.MR000007.pub3/full)

---

For additional support, consult the [API Documentation](api-reference.md) or visit our [GitHub Issues](https://github.com/your-org/mcp-servers/issues) page.