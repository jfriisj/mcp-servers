# API Reference - SLR MCP Server

Complete API documentation for the Systematic Literature Review MCP Server.

## Table of Contents

1. [MCP Tools](#mcp-tools)
2. [Service Layer APIs](#service-apis) 
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Response Formats](#response-formats)

## MCP Tools {#mcp-tools}

### upload-paper

Upload and process academic papers with automatic metadata extraction.

**Tool Name:** `upload-paper`

**Description:** Uploads a research paper (PDF or text format), extracts metadata, and creates a paper record for systematic review analysis.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `file_path` | string | Yes | Absolute or relative path to the paper file | - |
| `title` | string | No | Paper title (extracted if not provided) | Auto-extracted |
| `authors` | array[string] | No | List of author names | Auto-extracted |
| `doi` | string | No | Digital Object Identifier | Auto-extracted |
| `tags` | array[string] | No | Classification tags for organization | [] |

**Example Request:**
```json
{
  "name": "upload-paper",
  "arguments": {
    "file_path": "/papers/smith2023_ml_healthcare.pdf",
    "title": "Machine Learning Applications in Healthcare: A Systematic Review",
    "authors": ["Dr. Jane Smith", "Dr. John Doe", "Dr. Alice Johnson"],
    "doi": "10.1000/ml-healthcare-2023",
    "tags": ["machine-learning", "healthcare", "systematic-review"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paper_id": 1,
    "title": "Machine Learning Applications in Healthcare: A Systematic Review",
    "authors": ["Dr. Jane Smith", "Dr. John Doe", "Dr. Alice Johnson"],
    "doi": "10.1000/ml-healthcare-2023",
    "file_path": "/papers/smith2023_ml_healthcare.pdf",
    "file_type": "pdf",
    "metadata": {
      "publication_year": 2023,
      "journal": "Journal of Healthcare Informatics",
      "pages": "123-145",
      "abstract": "This systematic review examines..."
    },
    "processing_time_ms": 1450
  },
  "message": "Paper uploaded and processed successfully"
}
```

**Error Responses:**
- `FILE_NOT_FOUND`: Specified file path does not exist
- `UNSUPPORTED_FORMAT`: File format not supported
- `METADATA_EXTRACTION_FAILED`: Could not extract metadata from file
- `DUPLICATE_PAPER`: Paper with same DOI already exists

---

### assess-quality

Evaluate paper quality using systematic assessment frameworks.

**Tool Name:** `assess-quality`

**Description:** Performs quality assessment of research papers using established frameworks like PRISMA, CONSORT, or custom criteria.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `paper_id` | integer | Yes | ID of the paper to assess | - |
| `framework` | string | No | Assessment framework | "prisma" |
| `reviewer_id` | string | No | Identifier for the reviewer | "default" |
| `criterion_scores` | object | No | Manual scoring for specific criteria | {} |

**Available Frameworks:**
- `prisma`: PRISMA systematic review framework
- `consort`: CONSORT randomized trial reporting
- `strobe`: STROBE observational study reporting
- `quadas`: QUADAS diagnostic accuracy studies
- `custom`: User-defined criteria

**Example Request:**
```json
{
  "name": "assess-quality",
  "arguments": {
    "paper_id": 1,
    "framework": "prisma",
    "reviewer_id": "reviewer_001",
    "criterion_scores": {
      "study_design": {
        "score": 8.5,
        "notes": "Well-designed randomized controlled trial",
        "evidence": "Clear randomization procedure described"
      },
      "methodology": {
        "score": 7.8,
        "notes": "Appropriate sample size calculation",
        "evidence": "Power analysis provided"
      },
      "reporting": {
        "score": 9.0,
        "notes": "Excellent adherence to CONSORT guidelines",
        "evidence": "All required elements present"
      }
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "assessment_id": 1,
    "paper_id": 1,
    "framework": "prisma",
    "reviewer_id": "reviewer_001",
    "overall_score": 8.4,
    "risk_of_bias": "low",
    "grade_level": "high",
    "criterion_scores": {
      "study_design": 8.5,
      "methodology": 7.8,
      "reporting": 9.0,
      "data_quality": 8.2,
      "statistical_analysis": 8.1
    },
    "strengths": [
      "Rigorous study design with appropriate controls",
      "Comprehensive statistical analysis",
      "Excellent reporting transparency"
    ],
    "limitations": [
      "Limited generalizability due to single-center design",
      "Relatively short follow-up period"
    ],
    "recommendations": [
      "Consider multi-center replication",
      "Extend follow-up period in future studies"
    ],
    "assessment_date": "2023-10-14T15:30:00Z"
  },
  "message": "Quality assessment completed successfully"
}
```

---

### validate-research-question

Validate research questions using structured frameworks.

**Tool Name:** `validate-research-question`

**Description:** Validates and optimizes research questions using PICO, SPIDER, or other structured frameworks.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `question_text` | string | Yes | The research question to validate | - |
| `framework` | string | No | Validation framework | "pico" |
| `suggest_improvements` | boolean | No | Generate improvement suggestions | true |

**Available Frameworks:**
- `pico`: Population, Intervention, Comparison, Outcome
- `spider`: Sample, Phenomenon, Design, Evaluation, Research type
- `peco`: Population, Exposure, Comparison, Outcome
- `picot`: PICO with Time dimension

**Example Request:**
```json
{
  "name": "validate-research-question",
  "arguments": {
    "question_text": "How effective are machine learning algorithms in improving diagnostic accuracy in healthcare compared to traditional methods?",
    "framework": "pico",
    "suggest_improvements": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "question_id": 1,
    "original_question": "How effective are machine learning algorithms in improving diagnostic accuracy in healthcare compared to traditional methods?",
    "framework": "pico",
    "validity_score": 8.7,
    "framework_components": {
      "population": {
        "text": "Healthcare patients requiring diagnosis",
        "clarity_score": 7.5,
        "specificity_score": 6.8
      },
      "intervention": {
        "text": "Machine learning diagnostic algorithms",
        "clarity_score": 8.2,
        "specificity_score": 7.9
      },
      "comparison": {
        "text": "Traditional diagnostic methods",
        "clarity_score": 8.0,
        "specificity_score": 7.2
      },
      "outcome": {
        "text": "Diagnostic accuracy improvement",
        "clarity_score": 9.1,
        "specificity_score": 8.5
      }
    },
    "strengths": [
      "Clear intervention definition",
      "Well-defined outcome measure",
      "Appropriate comparison group"
    ],
    "weaknesses": [
      "Population could be more specific",
      "Healthcare domain too broad"
    ],
    "suggestions": [
      "Consider specifying the healthcare domain (e.g., 'radiology', 'pathology', 'emergency medicine')",
      "Define specific diagnostic accuracy metrics (e.g., 'sensitivity and specificity', 'area under ROC curve')",
      "Specify the patient population more precisely (e.g., 'adult patients with suspected COVID-19')"
    ],
    "improved_question": "In adult patients requiring radiological diagnosis, how do machine learning algorithms compare to traditional radiologist interpretation in terms of diagnostic sensitivity and specificity?",
    "validation_date": "2023-10-14T15:30:00Z"
  },
  "message": "Research question validated successfully"
}
```

---

### analyze-citations

Perform citation network analysis on research papers.

**Tool Name:** `analyze-citations`

**Description:** Analyzes citation patterns, builds citation networks, and calculates impact metrics for research papers.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `paper_id` | integer | Yes | ID of the paper to analyze | - |
| `include_network` | boolean | No | Include citation network data | false |
| `depth` | integer | No | Analysis depth (1-3 levels) | 2 |
| `analyze_influence` | boolean | No | Calculate influence metrics | true |

**Example Request:**
```json
{
  "name": "analyze-citations",
  "arguments": {
    "paper_id": 1,
    "include_network": true,
    "depth": 2,
    "analyze_influence": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paper_id": 1,
    "citation_analysis": {
      "internal_citations": 12,
      "external_citations": 45,
      "citation_network_size": 178,
      "citation_depth": 2,
      "h_index_contribution": 3.2,
      "impact_metrics": {
        "local_citation_score": 8.7,
        "global_impact_factor": 2.4,
        "field_weighted_citation_impact": 1.8,
        "relative_citation_ratio": 2.1
      }
    },
    "citation_network": {
      "nodes": [
        {
          "paper_id": 1,
          "title": "ML in Healthcare",
          "type": "target",
          "citation_count": 45
        },
        {
          "paper_id": 23,
          "title": "Deep Learning for Medical Imaging",
          "type": "citing",
          "citation_count": 78
        }
      ],
      "edges": [
        {
          "source": 23,
          "target": 1,
          "relationship": "cites",
          "context": "foundational_work"
        }
      ]
    },
    "key_citing_papers": [
      {
        "paper_id": 23,
        "title": "Deep Learning for Medical Imaging",
        "authors": ["Dr. Brown", "Dr. Wilson"],
        "citation_context": "foundational methodology",
        "influence_score": 8.9
      }
    ],
    "analysis_date": "2023-10-14T15:30:00Z"
  },
  "message": "Citation analysis completed successfully"
}
```

---

### analyze-hypothesis

Extract and analyze hypotheses with evidence synthesis.

**Tool Name:** `analyze-hypothesis`

**Description:** Extracts hypotheses from papers, classifies supporting evidence, and performs statistical analysis including meta-analysis.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `paper_ids` | array[integer] | Yes | List of paper IDs to analyze | - |
| `hypothesis_text` | string | No | Specific hypothesis to test | Auto-extracted |
| `meta_analysis` | boolean | No | Perform meta-analysis | false |
| `significance_level` | number | No | Statistical significance level | 0.05 |

**Example Request:**
```json
{
  "name": "analyze-hypothesis",
  "arguments": {
    "paper_ids": [1, 2, 3, 4],
    "hypothesis_text": "Machine learning algorithms demonstrate significantly higher diagnostic accuracy than traditional methods in healthcare applications",
    "meta_analysis": true,
    "significance_level": 0.05
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "hypothesis_id": 1,
    "hypothesis_text": "Machine learning algorithms demonstrate significantly higher diagnostic accuracy than traditional methods in healthcare applications",
    "papers_analyzed": 4,
    "evidence_classification": {
      "supporting_evidence": 12,
      "contradicting_evidence": 2,
      "neutral_evidence": 1,
      "inconclusive_evidence": 0
    },
    "statistical_analysis": {
      "effect_size": 1.25,
      "confidence_interval": [0.98, 1.52],
      "p_value": 0.003,
      "statistical_significance": true,
      "heterogeneity": {
        "i_squared": 34.2,
        "tau_squared": 0.12,
        "interpretation": "moderate"
      }
    },
    "meta_analysis": {
      "model": "random_effects",
      "pooled_effect": 1.18,
      "pooled_ci": [1.05, 1.31],
      "forest_plot_data": {
        "studies": [
          {
            "study_id": 1,
            "effect": 1.42,
            "ci_lower": 1.18,
            "ci_upper": 1.66,
            "weight": 28.5
          }
        ]
      },
      "publication_bias": {
        "egger_test_p": 0.234,
        "begg_test_p": 0.441,
        "funnel_plot_asymmetry": false
      }
    },
    "grade_assessment": {
      "overall_quality": "moderate",
      "certainty_rating": 3,
      "factors": {
        "study_design": "no_downgrade",
        "inconsistency": "no_downgrade", 
        "indirectness": "no_downgrade",
        "imprecision": "downgrade_1_level",
        "publication_bias": "no_downgrade"
      }
    },
    "analysis_date": "2023-10-14T15:30:00Z"
  },
  "message": "Hypothesis analysis completed successfully"
}
```

---

### index-paper

Create intelligent academic chunks and indexes for papers.

**Tool Name:** `index-paper`

**Description:** Processes academic papers using intelligent chunking strategies optimized for AI agent consumption and semantic search.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `paper_id` | integer | Yes | ID of the paper to index | - |
| `strategy` | string | No | Chunking strategy | "academic-section" |
| `optimize_for_agents` | boolean | No | Optimize chunks for AI processing | true |
| `chunk_size` | integer | No | Target chunk size in tokens | 512 |

**Available Strategies:**
- `academic-section`: Chunk by academic sections (Abstract, Methods, Results, Discussion)
- `citation-aware`: Preserve citation contexts and references
- `topic-based`: Semantic chunking based on topic modeling
- `hybrid`: Combination of section and semantic chunking

**Example Request:**
```json
{
  "name": "index-paper",
  "arguments": {
    "paper_id": 1,
    "strategy": "academic-section",
    "optimize_for_agents": true,
    "chunk_size": 512
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paper_id": 1,
    "indexing_strategy": "academic-section",
    "chunks_created": 8,
    "total_tokens": 4096,
    "chunks": [
      {
        "chunk_id": 1,
        "chunk_index": 0,
        "chunk_type": "abstract",
        "section_title": "Abstract",
        "content": "This systematic review examines the application of machine learning techniques...",
        "token_count": 245,
        "semantic_keywords": ["machine learning", "healthcare", "diagnostic accuracy"],
        "research_concepts": ["systematic review", "meta-analysis", "evidence synthesis"],
        "citations_referenced": ["Smith et al., 2022", "Johnson & Brown, 2023"]
      },
      {
        "chunk_id": 2,
        "chunk_index": 1,
        "chunk_type": "methods",
        "section_title": "Methodology",
        "content": "We conducted a systematic literature review following PRISMA guidelines...",
        "token_count": 512,
        "semantic_keywords": ["PRISMA", "systematic review", "literature search"],
        "research_concepts": ["methodology", "inclusion criteria", "data extraction"],
        "citations_referenced": ["PRISMA Group, 2020"]
      }
    ],
    "semantic_enhancement": {
      "indexed_for_search": true,
      "concept_extraction_completed": true,
      "citation_mapping_completed": true,
      "agent_optimization_applied": true
    },
    "processing_metrics": {
      "processing_time_ms": 2340,
      "chunk_optimization_time_ms": 450,
      "semantic_analysis_time_ms": 890
    },
    "indexing_date": "2023-10-14T15:30:00Z"
  },
  "message": "Paper indexed successfully"
}
```

---

### synthesize-evidence

Generate evidence synthesis and recommendations.

**Tool Name:** `synthesize-evidence`

**Description:** Synthesizes evidence from multiple papers to answer research questions, including meta-analysis and GRADE assessments.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `research_question_id` | integer | Yes | ID of the research question | - |
| `paper_ids` | array[integer] | Yes | Papers to include in synthesis | - |
| `include_meta_analysis` | boolean | No | Include quantitative meta-analysis | true |
| `include_grade_assessment` | boolean | No | Include GRADE evidence assessment | true |

**Example Request:**
```json
{
  "name": "synthesize-evidence",
  "arguments": {
    "research_question_id": 1,
    "paper_ids": [1, 2, 3, 4, 5],
    "include_meta_analysis": true,
    "include_grade_assessment": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "synthesis_id": 1,
    "research_question_id": 1,
    "research_question": "How effective are ML algorithms in improving diagnostic accuracy?",
    "papers_analyzed": 5,
    "evidence_summary": {
      "total_participants": 12450,
      "study_designs": {
        "randomized_controlled_trials": 3,
        "cohort_studies": 2,
        "diagnostic_accuracy_studies": 5
      },
      "outcome_measures": ["sensitivity", "specificity", "auc_roc"],
      "follow_up_range": "3-24 months"
    },
    "quantitative_synthesis": {
      "meta_analysis_performed": true,
      "pooled_results": {
        "sensitivity": {
          "pooled_estimate": 0.89,
          "confidence_interval": [0.85, 0.93],
          "heterogeneity_i2": 28.3
        },
        "specificity": {
          "pooled_estimate": 0.84,
          "confidence_interval": [0.79, 0.89],
          "heterogeneity_i2": 45.1
        }
      },
      "subgroup_analyses": [
        {
          "subgroup": "imaging_modality",
          "categories": ["CT", "MRI", "X-ray"],
          "significant_difference": true,
          "p_value": 0.023
        }
      ]
    },
    "grade_assessment": {
      "overall_certainty": "moderate",
      "recommendation_strength": "conditional",
      "evidence_profile": {
        "risk_of_bias": "no_serious_concerns",
        "inconsistency": "no_serious_concerns", 
        "indirectness": "no_serious_concerns",
        "imprecision": "serious_concerns",
        "other_factors": "none"
      }
    },
    "conclusions": {
      "primary_finding": "Machine learning algorithms show superior diagnostic accuracy compared to traditional methods",
      "clinical_significance": "The improvement in diagnostic accuracy is clinically meaningful",
      "applicability": "Findings apply to healthcare settings with adequate technical infrastructure",
      "limitations": [
        "Heterogeneity in ML algorithm types",
        "Limited long-term follow-up data",
        "Publication bias possible but not detected"
      ]
    },
    "recommendations": {
      "practice_recommendations": [
        "Consider implementing ML-assisted diagnosis in appropriate clinical contexts",
        "Ensure adequate training for healthcare providers",
        "Implement quality monitoring systems"
      ],
      "research_recommendations": [
        "Conduct longer-term outcome studies",
        "Investigate cost-effectiveness",
        "Develop implementation guidelines"
      ]
    },
    "synthesis_date": "2023-10-14T15:30:00Z"
  },
  "message": "Evidence synthesis completed successfully"
}
```

## Service Layer APIs {#service-apis}

### ResearchDocumentService

Core service for managing academic papers and documents.

#### Methods

**`upload_paper(file_path, title=None, authors=None, doi=None, tags=None)`**

Uploads and processes an academic paper.

**Parameters:**
- `file_path` (str): Path to the paper file
- `title` (str, optional): Paper title
- `authors` (List[str], optional): Author names
- `doi` (str, optional): DOI
- `tags` (List[str], optional): Classification tags

**Returns:** `ResearchPaper` object

**`get_paper(paper_id)`**

Retrieves a paper by ID.

**Parameters:**
- `paper_id` (int): Paper identifier

**Returns:** `ResearchPaper` object or None

**`search_papers(query, filters=None)`**

Searches papers by query and filters.

**Parameters:**
- `query` (str): Search query
- `filters` (dict, optional): Search filters

**Returns:** List of `ResearchPaper` objects

### QualityAssessmentService

Service for paper quality assessment and evaluation.

#### Methods

**`create_assessment(paper_id, framework, reviewer_id, criterion_scores=None)`**

Creates a quality assessment for a paper.

**Parameters:**
- `paper_id` (int): Paper to assess
- `framework` (QualityFramework): Assessment framework
- `reviewer_id` (str): Reviewer identifier
- `criterion_scores` (dict, optional): Manual scoring

**Returns:** `QualityAssessment` object

**`calculate_inter_rater_reliability(assessments)`**

Calculates inter-rater reliability metrics.

**Parameters:**
- `assessments` (List[QualityAssessment]): Assessments to compare

**Returns:** `InterRaterReliability` object

## Data Models {#data-models}

### ResearchPaper

Represents an academic research paper.

```python
@dataclass
class ResearchPaper:
    id: int
    title: str
    file_path: str
    file_type: str
    doi: Optional[str] = None
    abstract: Optional[str] = None
    publication_year: Optional[int] = None
    authors: List[Author] = field(default_factory=list)
    journal: Optional[Journal] = None
    keywords: List[str] = field(default_factory=list)
    research_areas: List[str] = field(default_factory=list)
    methodology: Optional[str] = None
    study_type: Optional[str] = None
    indexed: bool = False
    quality_assessed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
```

### QualityAssessment

Represents a quality assessment of a research paper.

```python
@dataclass  
class QualityAssessment:
    id: int
    paper_id: int
    framework: QualityFramework
    reviewer_id: str
    overall_score: float
    risk_of_bias: str
    criterion_scores: Dict[str, float]
    strengths: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    grade_level: Optional[str] = None
    assessment_date: datetime = field(default_factory=datetime.now)
```

### ResearchQuestion

Represents a validated research question.

```python
@dataclass
class ResearchQuestion:
    id: int
    question_text: str
    framework: QuestionFramework
    validation_status: ValidationLevel
    validity_score: float
    components: Dict[str, str]
    suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
```

## Error Handling {#error-handling}

### Error Types

**System Errors:**
- `DATABASE_ERROR`: Database operation failed
- `FILE_SYSTEM_ERROR`: File system operation failed  
- `NETWORK_ERROR`: Network operation failed

**Validation Errors:**
- `INVALID_PARAMETER`: Parameter validation failed
- `MISSING_REQUIRED_PARAMETER`: Required parameter missing
- `INVALID_FILE_FORMAT`: Unsupported file format

**Business Logic Errors:**
- `PAPER_NOT_FOUND`: Requested paper does not exist
- `DUPLICATE_PAPER`: Paper already exists
- `INSUFFICIENT_DATA`: Not enough data for analysis

**Example Error Response:**
```json
{
  "success": false,
  "error": "Paper with ID 999 not found",
  "error_type": "business_logic",
  "error_code": "PAPER_NOT_FOUND",
  "timestamp": "2023-10-14T15:30:00Z",
  "request_id": "req_12345"
}
```

## Response Formats {#response-formats}

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data varies by endpoint
  },
  "message": "Operation completed successfully",
  "timestamp": "2023-10-14T15:30:00Z",
  "request_id": "req_12345"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_type": "validation|business_logic|system",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2023-10-14T15:30:00Z",
  "request_id": "req_12345"
}
```

### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [
      // Array of items
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_previous": false
    }
  },
  "message": "Results retrieved successfully"
}
```

---

For additional technical support, see the [Research Guide](research-guide.md) or contact the development team through [GitHub Issues](https://github.com/your-org/mcp-servers/issues).