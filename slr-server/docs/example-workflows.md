# Example Workflows - SLR MCP Server

Practical examples of systematic literature review workflows using the SLR MCP Server.

## Table of Contents

1. [Basic Systematic Review](#basic-systematic-review)
2. [Meta-Analysis Workflow](#meta-analysis-workflow)
3. [Qualitative Evidence Synthesis](#qualitative-evidence-synthesis)
4. [Living Systematic Review](#living-systematic-review)
5. [Quality Assessment Only](#quality-assessment-only)
6. [Citation Network Analysis](#citation-network-analysis)

## Basic Systematic Review {#basic-systematic-review}

**Scenario:** Conducting a systematic review on "Machine Learning in Healthcare Diagnostics"

### Step-by-Step Workflow

#### 1. Research Question Development

```bash
# Develop and validate the research question
mcp call validate-research-question \
  --question "How effective are machine learning algorithms in improving diagnostic accuracy in healthcare compared to traditional diagnostic methods?" \
  --framework "pico" \
  --suggest-improvements true
```

**Expected Response:**
- Validity score: 8.7/10
- PICO components identified
- Suggestions for improvement
- Refined question provided

#### 2. Protocol Development

```bash
# Document the research protocol
mcp call create-protocol \
  --title "ML in Healthcare Diagnostics: Systematic Review" \
  --research-question-id 1 \
  --search-strategy "Comprehensive search across PubMed, IEEE, ACM Digital Library" \
  --inclusion-criteria "RCTs, cohort studies, diagnostic accuracy studies from 2018-2023" \
  --exclusion-criteria "Case reports, editorials, non-English papers"
```

#### 3. Literature Search and Upload

```bash
# Upload papers from literature search
papers=(
    "smith2023_ml_radiology.pdf"
    "jones2023_ai_pathology.pdf" 
    "brown2022_dl_diagnostics.pdf"
    "wilson2023_ml_emergency.pdf"
    "garcia2022_ai_cardiology.pdf"
)

for paper in "${papers[@]}"; do
    mcp call upload-paper \
      --file-path "/literature_search/$paper" \
      --tags ["machine-learning", "healthcare", "diagnostics"]
done
```

#### 4. Study Selection

```bash
# Screen papers based on inclusion criteria
for paper_id in {1..5}; do
    mcp call screen-paper \
      --paper-id $paper_id \
      --criteria-set "inclusion_criteria_v1" \
      --screener-id "researcher_001"
done

# Second-level screening for included papers
mcp call screen-papers-batch \
  --paper-ids [1,2,3,4,5] \
  --screening-level "full_text" \
  --screener-id "researcher_002"
```

#### 5. Quality Assessment

```bash
# Quality assessment using QUADAS for diagnostic studies
for paper_id in {1..5}; do
    # Primary reviewer
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "quadas" \
      --reviewer-id "quality_reviewer_1"
    
    # Secondary reviewer  
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "quadas" \
      --reviewer-id "quality_reviewer_2"
done

# Calculate inter-rater reliability
mcp call calculate-interrater-reliability \
  --assessment-type "quality" \
  --paper-ids [1,2,3,4,5] \
  --agreement-metric "kappa"
```

#### 6. Data Extraction

```bash
# Extract key data from included studies
for paper_id in {1..5}; do
    mcp call extract-data \
      --paper-id $paper_id \
      --extraction-form "diagnostic_accuracy_form" \
      --extractor-id "data_extractor_001" \
      --fields [
        "study_design",
        "population",
        "sample_size", 
        "intervention_details",
        "outcome_measures",
        "sensitivity",
        "specificity",
        "auc_roc"
      ]
done
```

#### 7. Evidence Synthesis

```bash
# Synthesize evidence from all included studies
mcp call synthesize-evidence \
  --research-question-id 1 \
  --paper-ids [1,2,3,4,5] \
  --include-meta-analysis true \
  --include-grade-assessment true \
  --synthesis-approach "quantitative_narrative"
```

#### 8. Report Generation

```bash
# Generate PRISMA-compliant report
mcp call generate-report \
  --synthesis-id 1 \
  --report-type "prisma_systematic_review" \
  --include-flow-diagram true \
  --include-risk-of-bias-summary true \
  --output-format "markdown"
```

**Timeline:** 2-3 months for 5-10 studies

## Meta-Analysis Workflow {#meta-analysis-workflow}

**Scenario:** Meta-analysis of diagnostic accuracy studies

### Prerequisites
- Quantitative studies with comparable outcome measures
- Sufficient statistical data for pooling

```bash
# 1. Upload studies with effect size data
rct_papers=(
    "rct_ml_radiology_2023.pdf"
    "rct_ai_pathology_2022.pdf"
    "rct_dl_cardiology_2023.pdf"
)

for paper in "${rct_papers[@]}"; do
    mcp call upload-paper \
      --file-path "/meta_analysis/$paper" \
      --study-type "randomized_controlled_trial"
done

# 2. Extract effect sizes and confidence intervals
for paper_id in {1..3}; do
    mcp call extract-effect-sizes \
      --paper-id $paper_id \
      --outcome-type "diagnostic_accuracy" \
      --effect-measures ["sensitivity", "specificity", "dor"] \
      --include-confidence-intervals true
done

# 3. Assess risk of bias using Cochrane ROB2
for paper_id in {1..3}; do
    mcp call assess-bias \
      --paper-id $paper_id \
      --tool "cochrane_rob2" \
      --domains ["randomization", "deviations", "missing_outcome", "measurement", "selection"]
done

# 4. Perform meta-analysis
mcp call perform-meta-analysis \
  --paper-ids [1,2,3] \
  --outcome "diagnostic_accuracy" \
  --analysis-model "random_effects" \
  --heterogeneity-tests ["i_squared", "tau_squared", "q_test"] \
  --publication-bias-tests ["funnel_plot", "egger_test", "begg_test"]

# 5. Subgroup analysis
mcp call subgroup-analysis \
  --meta-analysis-id 1 \
  --subgroup-variable "imaging_modality" \
  --categories ["CT", "MRI", "Ultrasound"] \
  --test-for-differences true

# 6. Sensitivity analysis
mcp call sensitivity-analysis \
  --meta-analysis-id 1 \
  --exclusion-criteria ["high_risk_of_bias", "small_sample_size"] \
  --recompute-pooled-estimates true
```

**Key Outputs:**
- Forest plot with pooled estimates
- Funnel plot for publication bias
- GRADE evidence profile
- Heterogeneity analysis results

## Qualitative Evidence Synthesis {#qualitative-evidence-synthesis}

**Scenario:** Thematic synthesis of healthcare professionals' experiences with AI

```bash
# 1. Validate qualitative research question using SPIDER
mcp call validate-research-question \
  --question "What are healthcare professionals' experiences and perceptions of using AI-powered diagnostic tools in clinical practice?" \
  --framework "spider"

# 2. Upload qualitative studies
qual_papers=(
    "interview_study_physicians_ai.pdf"
    "focus_group_nurses_ml.pdf" 
    "ethnography_radiologists_ai.pdf"
    "phenomenology_pathologists_ai.pdf"
)

for paper in "${qual_papers[@]}"; do
    mcp call upload-paper \
      --file-path "/qualitative_synthesis/$paper" \
      --study-type "qualitative"
done

# 3. Quality appraisal using CASP
for paper_id in {1..4}; do
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "casp_qualitative" \
      --reviewer-id "qual_reviewer_001"
done

# 4. Extract findings and themes
for paper_id in {1..4}; do
    mcp call extract-qualitative-findings \
      --paper-id $paper_id \
      --extraction-approach "interpretive" \
      --coding-framework "inductive" \
      --extract-participant-quotes true
done

# 5. Thematic synthesis
mcp call perform-thematic-synthesis \
  --paper-ids [1,2,3,4] \
  --synthesis-approach "meta_ethnography" \
  --coding-method "line_by_line" \
  --theme-development "constant_comparative"

# 6. Develop conceptual model
mcp call develop-conceptual-model \
  --synthesis-id 1 \
  --model-type "framework_synthesis" \
  --include-participant-voice true \
  --confidence-assessment "grade_cerqual"
```

## Living Systematic Review {#living-systematic-review}

**Scenario:** Continuously updated review on COVID-19 diagnostics

```bash
# 1. Set up automated search monitoring
mcp call setup-living-review \
  --review-title "COVID-19 Diagnostic Technologies: Living Systematic Review" \
  --research-question-id 1 \
  --search-frequency "weekly" \
  --databases ["pubmed", "embase", "medrxiv"] \
  --search-alert-threshold 5

# 2. Configure automated screening
mcp call configure-auto-screening \
  --living-review-id 1 \
  --screening-algorithm "ml_classifier" \
  --training-set "covid_diagnostics_training" \
  --confidence-threshold 0.85

# 3. Set up continuous monitoring
mcp call monitor-evidence-base \
  --living-review-id 1 \
  --monitoring-frequency "daily" \
  --update-triggers ["new_rct", "contradictory_evidence", "safety_concerns"]

# 4. Automated quality assessment for new studies
mcp call setup-auto-quality-assessment \
  --living-review-id 1 \
  --assessment-framework "cochrane_rob2" \
  --quality-threshold 7.0 \
  --require-human-validation true

# 5. Schedule periodic updates
mcp call schedule-review-updates \
  --living-review-id 1 \
  --update-schedule "monthly" \
  --meta-analysis-trigger 3 \
  --notification-recipients ["team@research.org"]
```

## Quality Assessment Only {#quality-assessment-only}

**Scenario:** Quality assessment of existing systematic reviews

```bash
# 1. Upload systematic reviews for assessment
sr_papers=(
    "cochrane_review_diabetes_2023.pdf"
    "bmj_review_hypertension_2022.pdf"
    "nejm_review_cancer_screening_2023.pdf"
)

for paper in "${sr_papers[@]}"; do
    mcp call upload-paper \
      --file-path "/quality_assessment/$paper" \
      --paper-type "systematic_review"
done

# 2. Quality assessment using AMSTAR-2
for paper_id in {1..3}; do
    # Primary reviewer
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "amstar2" \
      --reviewer-id "sr_expert_001" \
      --detailed-rationale true
    
    # Secondary reviewer
    mcp call assess-quality \
      --paper-id $paper_id \
      --framework "amstar2" \
      --reviewer-id "sr_expert_002" \
      --detailed-rationale true
done

# 3. Resolve disagreements
mcp call resolve-assessment-conflicts \
  --paper-ids [1,2,3] \
  --resolution-method "consensus_discussion" \
  --moderator-id "senior_reviewer"

# 4. Generate quality summary
mcp call generate-quality-summary \
  --paper-ids [1,2,3] \
  --framework "amstar2" \
  --include-recommendations true \
  --output-format "summary_table"
```

## Citation Network Analysis {#citation-network-analysis}

**Scenario:** Mapping the evolution of machine learning in healthcare

```bash
# 1. Upload seminal papers in the field
seminal_papers=(
    "lecun2015_deep_learning.pdf"
    "rajkomar2018_scalable_ml_healthcare.pdf"
    "topol2019_high_performance_medicine.pdf"
)

for paper in "${seminal_papers[@]}"; do
    mcp call upload-paper \
      --file-path "/citation_analysis/$paper" \
      --paper-type "foundational"
done

# 2. Build comprehensive citation network
for paper_id in {1..3}; do
    mcp call analyze-citations \
      --paper-id $paper_id \
      --include-forward-citations true \
      --include-backward-citations true \
      --depth 3 \
      --minimum-citation-threshold 10
done

# 3. Identify key citing clusters
mcp call identify-citation-clusters \
  --network-id 1 \
  --clustering-algorithm "modularity" \
  --minimum-cluster-size 5 \
  --include-temporal-analysis true

# 4. Analyze research evolution
mcp call analyze-research-evolution \
  --citation-network-id 1 \
  --time-period "2015-2023" \
  --evolution-metrics ["growth_rate", "impact_trajectory", "field_emergence"]

# 5. Generate network visualization
mcp call generate-network-visualization \
  --network-id 1 \
  --layout-algorithm "force_directed" \
  --node-size-by "citation_count" \
  --edge-weight-by "co_citation_strength" \
  --output-format "interactive_html"
```

## Troubleshooting Common Issues

### Issue: Low Inter-rater Agreement

```bash
# Diagnose disagreement patterns
mcp call analyze-disagreement-patterns \
  --assessment-type "quality" \
  --paper-ids [1,2,3,4,5] \
  --reviewers ["reviewer_001", "reviewer_002"] \
  --identify-systematic-bias true

# Provide additional reviewer training
mcp call generate-training-materials \
  --disagreement-analysis-id 1 \
  --training-focus ["unclear_criteria", "borderline_cases"] \
  --include-practice-examples true

# Third reviewer for disputed cases
mcp call assign-third-reviewer \
  --disputed-assessments [1,3,7,12] \
  --senior-reviewer-id "expert_reviewer"
```

### Issue: High Heterogeneity in Meta-Analysis

```bash
# Investigate sources of heterogeneity
mcp call investigate-heterogeneity \
  --meta-analysis-id 1 \
  --explore-sources ["population", "intervention", "outcome_measurement", "study_design"] \
  --statistical-tests ["galbraith_plot", "baujat_plot"]

# Perform meta-regression
mcp call meta-regression \
  --meta-analysis-id 1 \
  --covariates ["publication_year", "sample_size", "risk_of_bias_score"] \
  --regression-method "mixed_effects"

# Consider narrative synthesis
mcp call convert-to-narrative-synthesis \
  --meta-analysis-id 1 \
  --synthesis-method "vote_counting" \
  --include-harvest-plots true
```

### Issue: Publication Bias Detected

```bash
# Quantify publication bias
mcp call assess-publication-bias \
  --meta-analysis-id 1 \
  --tests ["egger", "begg", "peters", "ruchert"] \
  --create-funnel-plots true

# Adjust for publication bias
mcp call adjust-for-publication-bias \
  --meta-analysis-id 1 \
  --adjustment-methods ["trim_and_fill", "selection_models"] \
  --report-adjusted-estimates true

# Search for unpublished studies
mcp call search-grey-literature \
  --research-question-id 1 \
  --sources ["clinical_trials_registries", "conference_abstracts", "thesis_databases"]
```

## Performance Optimization Tips

### For Large Reviews (>100 papers)

```bash
# Enable batch processing
mcp call configure-batch-processing \
  --batch-size 20 \
  --parallel-workers 4 \
  --memory-limit "8GB"

# Use database indexing
mcp call optimize-database \
  --create-indexes ["paper_title", "authors", "doi", "publication_year"] \
  --enable-full-text-search true

# Cache expensive operations
mcp call enable-caching \
  --cache-types ["quality_assessments", "citation_analysis", "meta_analysis"] \
  --cache-duration "7_days"
```

### For Real-time Collaboration

```bash
# Set up collaborative workspace
mcp call setup-collaboration \
  --workspace-id "covid_review_2023" \
  --team-members ["researcher1", "researcher2", "statistician1"] \
  --permissions-model "role_based"

# Enable real-time conflict resolution
mcp call enable-real-time-sync \
  --workspace-id "covid_review_2023" \
  --conflict-resolution "last_writer_wins" \
  --audit-trail true
```

---

These examples demonstrate the flexibility and power of the SLR MCP Server for various systematic review scenarios. For additional examples or custom workflows, see the [API Reference](api-reference.md) or contact the development team.