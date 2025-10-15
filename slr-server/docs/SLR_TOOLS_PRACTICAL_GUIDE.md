# SLR Tools Practical Usage Guide

## Overview

This guide provides practical examples and troubleshooting for using the SLR MCP Server tools effectively. Based on real testing and common issues encountered during implementation.

## 🚀 Quick Start: Your First SLR Project

### Step 1: Verify Server Setup

```bash
# Test the server is running
python start_server.py

# In another terminal, verify tools are available
python list_slr_tools.py
```

### Step 2: Create Your First Project

**Using MCP Client:**
```python
# Create a systematic literature review project
await session.call_tool("create_slr_project", {
    "title": "AI in Healthcare Diagnosis - Systematic Review",
    "research_domain": "Artificial Intelligence",  
    "description": "Investigating AI applications in medical diagnosis",
    "team_lead": "Dr. Research Leader",
    "team_members": ["Reviewer A", "Reviewer B"],
    "research_question": "How effective are AI systems in medical diagnosis?",
    "estimated_timeline_weeks": 12
})
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "title": "AI in Healthcare Diagnosis - Systematic Review",
    "status": "planning",
    "current_phase": "planning",
    "progress_percentage": 5.0
  }
}
```

### Step 3: Upload Your First Paper

**Prerequisites:**
- Have a PDF file ready (e.g., `research_paper.pdf`)
- Ensure file path is accessible to the server

```python
# Upload a research paper
await session.call_tool("upload_paper", {
    "file_path": "/path/to/research_paper.pdf",
    "title": "Machine Learning in Medical Diagnosis",
    "authors": ["Dr. Smith", "Dr. Johnson"],
    "publication_year": 2023,
    "tags": ["machine-learning", "healthcare", "diagnosis"]
})
```

**Common Issues & Solutions:**

❌ **Error: File not found**
```json
{"success": false, "error": "File not found: /path/to/research_paper.pdf"}
```
✅ **Solution:** Use absolute paths and verify file exists:
```bash
# Check if file exists
ls -la "/full/path/to/research_paper.pdf"
# Or on Windows
dir "C:\full\path\to\research_paper.pdf"
```

❌ **Error: Authors position constraint**
```json
{"success": false, "error": "CHECK constraint failed: author_position > 0"}
```
✅ **Solution:** This is fixed in the latest version. If you encounter this, ensure you're running the updated code.

## 🔧 Tool-by-Tool Usage Guide

### Document Management Tools

#### `upload_paper` - Upload Academic Papers

**Purpose:** Upload and process research papers with metadata extraction

**Best Practices:**
- Use descriptive titles and author names
- Include publication year for better categorization
- Add relevant tags for searchability

**Example:**
```python
result = await session.call_tool("upload_paper", {
    "file_path": "/papers/smith_2023_ai_diagnosis.pdf",
    "title": "AI-Assisted Diagnosis in Emergency Medicine",
    "authors": ["Dr. Sarah Smith", "Dr. Michael Chen", "Dr. Emily Rodriguez"],
    "doi": "10.1000/example-doi-2023",
    "publication_year": 2023,
    "tags": ["artificial-intelligence", "emergency-medicine", "diagnosis", "healthcare"]
})
```

**Troubleshooting:**
- **Large files:** Break down very large PDFs or increase processing timeout
- **Unsupported formats:** Convert to PDF format first
- **Encoding issues:** Ensure PDF text is extractable (not scanned images)

#### `list_papers` - Browse Available Papers

**Purpose:** List all papers with optional filtering

**Example:**
```python
# List all papers
all_papers = await session.call_tool("list_papers", {})

# List papers with filters
filtered_papers = await session.call_tool("list_papers", {
    "filters": {
        "tags": ["artificial-intelligence"],
        "publication_year": 2023,
        "quality_score_min": 7.0
    },
    "limit": 10
})
```

#### `get_paper` - Get Paper Details

**Purpose:** Retrieve detailed information about a specific paper

**Example:**
```python
paper_details = await session.call_tool("get_paper", {
    "paper_id": 1
})
```

#### `search_papers` - Search Paper Content

**Purpose:** Full-text search across papers and metadata

**Search Types:**
- `semantic`: AI-powered semantic search (default)
- `keyword`: Traditional keyword matching
- `citation`: Search by citation patterns

**Example:**
```python
# Semantic search
results = await session.call_tool("search_papers", {
    "query": "machine learning diagnostic accuracy",
    "search_type": "semantic",
    "limit": 5
})

# Keyword search with filters
results = await session.call_tool("search_papers", {
    "query": "artificial intelligence AND healthcare",
    "search_type": "keyword",
    "filters": {
        "publication_year": 2023
    }
})
```

**Troubleshooting:**
- **No results:** Check if papers are properly indexed
- **Slow searches:** Use more specific queries
- **Encoding issues:** Ensure query text is properly formatted

### Quality Assessment Tools

#### `assess_quality` - Evaluate Paper Quality

**Purpose:** Systematic quality assessment using established frameworks

**Available Frameworks:**
- `PRISMA`: Systematic reviews and meta-analyses
- `CASP`: Critical Appraisal Skills Programme
- `JBI`: Joanna Briggs Institute

**Example:**
```python
# Basic quality assessment
assessment = await session.call_tool("assess_quality", {
    "paper_id": 1,
    "assessment_framework": "PRISMA",
    "reviewer_id": "reviewer_001"
})

# Assessment with custom criteria
assessment = await session.call_tool("assess_quality", {
    "paper_id": 1,
    "assessment_framework": "PRISMA",
    "reviewer_id": "reviewer_001",
    "criteria": {
        "study_design": {"weight": 0.3, "min_score": 7.0},
        "methodology": {"weight": 0.4, "min_score": 8.0},
        "reporting": {"weight": 0.3, "min_score": 6.0}
    }
})
```

**Best Practices:**
- Use consistent reviewer IDs for tracking
- Document assessment criteria clearly
- Perform inter-rater reliability checks

#### `calculate_inter_rater_reliability` - Reviewer Agreement

**Purpose:** Measure agreement between multiple reviewers

**Example:**
```python
reliability = await session.call_tool("calculate_inter_rater_reliability", {
    "paper_ids": [1, 2, 3, 4, 5],
    "reviewer_ids": ["reviewer_001", "reviewer_002", "reviewer_003"]
})
```

### Research Question Tools

#### `validate_research_question` - PICO/SPIDER Validation

**Purpose:** Validate and improve research questions using structured frameworks

**Frameworks:**
- `PICO`: Population, Intervention, Comparison, Outcome
- `SPIDER`: Sample, Phenomenon, Design, Evaluation, Research type

**Example:**
```python
# PICO validation
validation = await session.call_tool("validate_research_question", {
    "research_question": "In adult patients with diabetes (P), how does AI-assisted glucose monitoring (I) compared to traditional monitoring (C) affect glycemic control (O)?",
    "framework": "PICO",
    "domain": "healthcare"
})

# SPIDER validation for qualitative research
validation = await session.call_tool("validate_research_question", {
    "research_question": "What are healthcare professionals' experiences with AI diagnostic tools?",
    "framework": "SPIDER",
    "domain": "healthcare"
})
```

**Best Practice Tips:**
- Be specific about population characteristics
- Clearly define interventions and comparisons
- Use measurable outcomes
- Consider timeframes where relevant

### Workflow Management Tools

#### `create_slr_project` - Initialize SLR Project

**Purpose:** Set up a structured systematic literature review project

**Example:**
```python
project = await session.call_tool("create_slr_project", {
    "title": "Effectiveness of Telemedicine in Rural Healthcare",
    "research_domain": "Healthcare Technology",
    "description": "Systematic review of telemedicine applications in rural healthcare settings, focusing on patient outcomes and accessibility",
    "team_lead": "Dr. Rural Health",
    "team_members": [
        "Research Assistant 1",
        "Medical Librarian",
        "Statistics Consultant"
    ],
    "research_question": "How effective is telemedicine in improving healthcare outcomes for rural populations?",
    "estimated_timeline_weeks": 16
})
```

#### `get_slr_progress` - Track Project Progress

**Purpose:** Comprehensive progress dashboard

**Example:**
```python
progress = await session.call_tool("get_slr_progress", {
    "project_id": 1
})
```

**Expected Response:**
```json
{
  "project_id": 1,
  "current_phase": "screening",
  "progress_percentage": 45.2,
  "papers_uploaded": 25,
  "papers_screened": 18,
  "papers_included": 12,
  "quality_assessments_completed": 8,
  "bottlenecks": ["Quality assessment backlog"],
  "next_milestones": [
    {"task": "Complete quality assessments", "due_date": "2024-01-15"},
    {"task": "Begin data extraction", "due_date": "2024-01-22"}
  ]
}
```

#### `get_next_steps` - AI-Powered Recommendations

**Purpose:** Get intelligent recommendations for next actions

**Example:**
```python
recommendations = await session.call_tool("get_next_steps", {
    "project_id": 1,
    "current_phase": "screening"
})
```

#### `create_screening_workflow` - Multi-Stage Screening

**Purpose:** Set up systematic study selection process

**Example:**
```python
workflow = await session.call_tool("create_screening_workflow", {
    "project_id": 1,
    "inclusion_criteria": [
        "Randomized controlled trials",
        "Telemedicine interventions",
        "Rural healthcare settings",
        "Adult patients (18+ years)",
        "English language publications"
    ],
    "exclusion_criteria": [
        "Conference abstracts only",
        "Pilot studies with <50 participants",
        "Non-peer reviewed publications",
        "Publications before 2010"
    ],
    "reviewers": ["reviewer_001", "reviewer_002"],
    "screening_stages": ["title_abstract", "full_text", "final_selection"]
})
```

#### `screen_paper` - Record Screening Decisions

**Purpose:** Document study selection decisions with rationale

**Example:**
```python
# Include a paper
screening = await session.call_tool("screen_paper", {
    "project_id": 1,
    "paper_id": 5,
    "reviewer_id": "reviewer_001",
    "stage": "title_abstract",
    "decision": "include",
    "reason": "RCT of telemedicine in rural setting, meets all inclusion criteria",
    "confidence_level": 0.9
})

# Exclude a paper
screening = await session.call_tool("screen_paper", {
    "project_id": 1,
    "paper_id": 8,
    "reviewer_id": "reviewer_001", 
    "stage": "full_text",
    "decision": "exclude",
    "reason": "Study conducted in urban setting, does not meet rural healthcare criterion",
    "exclusion_criteria": ["Non-rural setting"],
    "confidence_level": 0.95
})
```

### Analysis Tools

#### `analyze_citations` - Citation Network Analysis

**Purpose:** Analyze citation patterns and research impact

**Example:**
```python
# Basic citation analysis
citations = await session.call_tool("analyze_citations", {
    "paper_id": 1,
    "analysis_type": "network",
    "depth": 2
})

# Forward citation analysis
forward_citations = await session.call_tool("analyze_citations", {
    "paper_id": 1,
    "analysis_type": "forward",
    "depth": 1
})
```

#### `analyze_hypotheses` - Hypothesis Extraction

**Purpose:** Extract and analyze research hypotheses from papers

**Example:**
```python
hypotheses = await session.call_tool("analyze_hypotheses", {
    "paper_id": 1,
    "hypothesis_type": "explicit"  # or "implicit" or "all"
})
```

#### `synthesize_evidence` - Evidence Synthesis

**Purpose:** Combine evidence from multiple studies

**Example:**
```python
synthesis = await session.call_tool("synthesize_evidence", {
    "paper_ids": [1, 2, 3, 4, 5],
    "synthesis_method": "meta-analysis",  # or "narrative" or "meta-synthesis"
    "outcome_measures": ["patient_satisfaction", "clinical_outcomes", "cost_effectiveness"]
})
```

### Reporting Tools

#### `generate_slr_report` - Comprehensive Reports

**Purpose:** Generate systematic literature review reports

**Example:**
```python
report = await session.call_tool("generate_slr_report", {
    "paper_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    "output_path": "/reports/telemedicine_slr_report.md",
    "report_format": "markdown",  # or "latex" or "docx"
    "include_quality_assessment": True,
    "include_citation_analysis": True
})
```

**Report Formats:**
- `markdown`: Easy to read and version control
- `latex`: Academic publication ready
- `docx`: Microsoft Word format for collaboration

#### `export_citation_network` - Network Visualization

**Purpose:** Export citation data for visualization tools

**Example:**
```python
network_export = await session.call_tool("export_citation_network", {
    "paper_ids": [1, 2, 3, 4, 5],
    "output_path": "/exports/citation_network.json",
    "format": "json"  # or "gephi" or "cytoscape"
})
```

### Guidance Tools

#### `get_slr_guide` - Interactive Methodology Guidance

**Purpose:** Get context-specific guidance and best practices

**Example:**
```python
# Beginner guidance for planning phase
guidance = await session.call_tool("get_slr_guide", {
    "topic": "research question formulation",
    "current_phase": "planning",
    "experience_level": "beginner"
})

# Advanced guidance for analysis
guidance = await session.call_tool("get_slr_guide", {
    "topic": "meta-analysis techniques",
    "current_phase": "analysis", 
    "experience_level": "advanced"
})
```

## 🔍 Common Workflows

### Complete SLR Workflow

```python
# 1. Create project
project = await session.call_tool("create_slr_project", {...})
project_id = project["data"]["project_id"]

# 2. Upload papers
for paper_file in paper_files:
    await session.call_tool("upload_paper", {"file_path": paper_file, ...})

# 3. Set up screening
await session.call_tool("create_screening_workflow", {
    "project_id": project_id, ...
})

# 4. Screen papers
for paper_id in paper_ids:
    await session.call_tool("screen_paper", {
        "project_id": project_id,
        "paper_id": paper_id, ...
    })

# 5. Quality assessment
for paper_id in included_papers:
    await session.call_tool("assess_quality", {
        "paper_id": paper_id, ...
    })

# 6. Generate report
await session.call_tool("generate_slr_report", {
    "paper_ids": included_papers, ...
})
```

### Quality Assessment Workflow

```python
# 1. Assess papers with multiple reviewers
for paper_id in papers:
    for reviewer in reviewers:
        await session.call_tool("assess_quality", {
            "paper_id": paper_id,
            "reviewer_id": reviewer, ...
        })

# 2. Calculate inter-rater reliability
reliability = await session.call_tool("calculate_inter_rater_reliability", {
    "paper_ids": papers,
    "reviewer_ids": reviewers
})

# 3. Resolve conflicts if reliability is low
if reliability["data"]["kappa"] < 0.6:
    # Discuss discrepancies and reassess
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### Tool Not Found Error
```
Error: Tool 'tool_name' not found
```
**Solution:** 
1. Check if server is running properly
2. Verify tool name spelling
3. Ensure latest version is installed

#### Database Connection Issues
```
Error: Database connection failed
```
**Solution:**
1. Check database file permissions
2. Ensure SQLite is properly installed
3. Check disk space availability

#### File Path Issues
```
Error: File not found or access denied
```
**Solution:**
1. Use absolute file paths
2. Check file permissions
3. Ensure file exists and is readable

#### Memory Issues with Large Files
```
Error: Memory allocation failed
```
**Solution:**
1. Process files in smaller batches
2. Increase system memory if possible
3. Use file streaming for very large documents

#### Async/Event Loop Issues
```
Error: Event loop is already running
```
**Solution:**
1. Use Docker deployment for better isolation
2. Ensure proper async context management
3. Consider using synchronous wrapper functions

### Performance Optimization

#### Large Document Collections
- **Batch Processing:** Process papers in groups of 10-20
- **Indexing:** Run indexing operations during off-peak hours
- **Database:** Consider PostgreSQL for large datasets

#### Search Performance
- **Query Optimization:** Use specific keywords rather than broad terms
- **Result Limiting:** Set appropriate limits on search results
- **Caching:** Enable caching for frequently accessed data

## 📊 Best Practices

### Project Organization
1. **Consistent Naming:** Use descriptive, consistent naming for projects and papers
2. **Tagging Strategy:** Develop a comprehensive tagging taxonomy
3. **Version Control:** Track changes and decisions throughout the process

### Quality Assurance
1. **Multiple Reviewers:** Use at least 2 independent reviewers for screening
2. **Calibration:** Conduct calibration exercises before full screening
3. **Documentation:** Document all decisions and rationale

### Data Management
1. **Backup Strategy:** Regular backups of database and files
2. **File Organization:** Consistent file naming and folder structure
3. **Access Control:** Proper permissions for team collaboration

### Reporting
1. **PRISMA Compliance:** Follow PRISMA guidelines for systematic reviews
2. **Transparency:** Include all screening and assessment data
3. **Reproducibility:** Document all search strategies and criteria

## 🆘 Getting Help

### Support Resources
- **Documentation:** Check the comprehensive API reference
- **Examples:** Review practical examples in this guide
- **Community:** GitHub discussions and issues

### Debug Mode
Enable detailed logging for troubleshooting:
```bash
export LOG_LEVEL=DEBUG
python start_server.py
```

### Contact Information
- **GitHub Issues:** Report bugs and feature requests
- **Documentation:** Contribute improvements to guides
- **Community:** Share experiences and best practices

---

This practical guide should help you effectively use all SLR MCP Server tools. For additional technical details, see the API Reference documentation.