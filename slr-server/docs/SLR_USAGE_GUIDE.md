# SLR MCP Server Usage Guide with test.pdf

## Overview

You now have a fully functional **Systematic Literature Review (SLR) MCP Server** with comprehensive workflow guidance tools. Here's how to use it with your test.pdf file.

## ✅ What's Available

### 🔬 **23 MCP Tools Ready to Use**
- **5 Workflow Guidance Tools**: Project management, progress tracking, methodology guidance
- **18 Document Management Tools**: Paper processing, quality assessment, search, analysis

### 📊 **Key Capabilities**
- **Project Management**: Create and track SLR projects through all phases
- **Document Processing**: Upload, parse, and analyze research papers (including your test.pdf)
- **Quality Assessment**: PRISMA-compliant systematic quality evaluation
- **Screening Workflows**: Multi-stage study selection with reviewer management
- **Progress Tracking**: Real-time dashboards and bottleneck identification
- **Methodology Guidance**: AI-powered recommendations and best practices
- **Citation Analysis**: Network analysis and reference pattern detection
- **Report Generation**: Comprehensive SLR reports in multiple formats

## 🚀 How to Use the Server

### Option 1: Run Server Directly

```powershell
# Start the SLR MCP Server
python start_slr_server.py
```

Then connect with any MCP client or use our test clients.

### Option 2: Use Docker Container (Recommended)

```powershell
# Run with Docker for better isolation
python test_docker_slr.py
```

This mounts your current directory (with test.pdf) into the container.

### Option 3: Test Individual Tools

```powershell
# Test specific MCP tools
python test_slr_tools.py
```

Choose option 1 to test tools via MCP protocol, or option 2 for quick server test.

## 📋 Complete SLR Workflow Example

Here's how to conduct a systematic literature review using your test.pdf:

### Step 1: Create SLR Project
```python
# Via MCP client
project_result = await session.call_tool(
    "create_slr_project",
    {
        "title": "AI in Medical Diagnosis - Systematic Review",
        "research_domain": "Artificial Intelligence & Healthcare",
        "description": "Comprehensive review of AI applications in medical diagnostics",
        "team_lead": "Your Name",
        "team_members": ["Reviewer 1", "Reviewer 2"],
        "research_question": "How effective are AI systems in medical diagnosis compared to traditional methods?",
        "estimated_timeline_weeks": 16
    }
)
```

### Step 2: Validate Research Question
```python
question_result = await session.call_tool(
    "validate_research_question",
    {
        "question_text": "In patients with cardiovascular disease (P), how does AI-assisted diagnosis (I) compared to traditional clinical assessment (C) affect diagnostic accuracy (O)?",
        "framework": "pico"
    }
)
```

### Step 3: Upload Your test.pdf
```python
upload_result = await session.call_tool(
    "upload_paper",
    {
        "file_path": "/path/to/test.pdf",
        "title": "Your Paper Title",
        "authors": ["Author 1", "Author 2"],
        "publication_year": 2023,
        "tags": ["ai", "healthcare", "diagnosis"]
    }
)
```

### Step 4: Set Up Screening Workflow
```python
screening_result = await session.call_tool(
    "create_screening_workflow",
    {
        "project_id": 1,
        "inclusion_criteria": [
            "AI/ML in medical diagnosis",
            "Peer-reviewed studies",
            "Quantitative outcomes"
        ],
        "exclusion_criteria": [
            "Non-English publications",
            "Conference abstracts only"
        ],
        "reviewers": ["reviewer_1", "reviewer_2"],
        "screening_stages": ["title_abstract", "full_text"]
    }
)
```

### Step 5: Screen Papers
```python
screen_result = await session.call_tool(
    "screen_paper",
    {
        "project_id": 1,
        "paper_id": 1,
        "reviewer_id": "reviewer_1",
        "stage": "title_abstract",
        "decision": "include",
        "reason": "Directly relevant to AI in medical diagnosis",
        "confidence_level": 0.9
    }
)
```

### Step 6: Quality Assessment
```python
quality_result = await session.call_tool(
    "assess_quality",
    {
        "paper_id": 1,
        "assessment_framework": "PRISMA",
        "reviewer_id": "quality_reviewer"
    }
)
```

### Step 7: Get Progress Dashboard
```python
progress_result = await session.call_tool(
    "get_slr_progress",
    {
        "project_id": 1
    }
)
```

### Step 8: Get Next Steps Guidance
```python
next_steps_result = await session.call_tool(
    "get_next_steps",
    {
        "project_id": 1,
        "current_phase": "screening"
    }
)
```

### Step 9: Generate Final Report
```python
report_result = await session.call_tool(
    "generate_slr_report",
    {
        "project_id": 1,
        "paper_ids": [1, 2, 3],  # Include relevant papers
        "include_methodology": True,
        "include_results": True,
        "format": "markdown"
    }
)
```

## 🔧 Testing Your Setup

### Quick Server Test
```powershell
# Test server initialization
echo "2" | python test_slr_tools.py
```

### Full Workflow Test
```powershell
# Test complete MCP protocol workflow
python mcp_slr_client.py
```

### Docker Test (Recommended)
```powershell
# Test with Docker isolation
python test_docker_slr.py
```

## 📊 Available MCP Tools

### Workflow Management
- `create_slr_project` - Initialize new SLR project
- `get_slr_progress` - Comprehensive progress dashboard
- `get_next_steps` - AI-powered workflow recommendations
- `create_screening_workflow` - Multi-stage screening setup
- `screen_paper` - Record screening decisions
- `get_slr_guide` - Interactive methodology guidance

### Document Management
- `upload_paper` - Upload and process research papers
- `get_paper` - Retrieve paper information
- `list_papers` - List papers with filters
- `search_papers` - Semantic and keyword search
- `assess_quality` - PRISMA quality assessment
- `analyze_citations` - Citation network analysis
- `validate_research_question` - PICO/SPIDER validation
- `generate_slr_report` - Comprehensive reports

### Advanced Features
- `synthesize_evidence` - Meta-analysis and evidence synthesis
- `index_paper` - Intelligent academic chunking
- `analyze_hypotheses` - Hypothesis extraction and analysis
- `calculate_inter_rater_reliability` - Reviewer agreement metrics
- `export_citation_network` - Network visualization data

## 🎯 Key Benefits

### For Researchers
- **Guided Workflow**: Step-by-step guidance through all SLR phases
- **Quality Assurance**: Built-in PRISMA compliance and best practices
- **Progress Tracking**: Real-time dashboards and bottleneck identification
- **AI-Powered Insights**: Intelligent recommendations and analysis

### For Teams
- **Collaboration**: Multi-reviewer workflows with conflict resolution
- **Standardization**: Consistent methodology across team members
- **Efficiency**: Automated tasks and intelligent prioritization
- **Transparency**: Complete audit trail and decision documentation

## 🔄 Next Steps

1. **Start Simple**: Test with your test.pdf using the provided scripts
2. **Expand**: Add more papers to build a comprehensive corpus
3. **Collaborate**: Set up multi-reviewer workflows
4. **Analyze**: Use advanced tools for meta-analysis and synthesis
5. **Report**: Generate PRISMA-compliant systematic review reports

## 💡 Tips for Success

- **Use Docker**: For better isolation and fewer dependency issues
- **Start Small**: Begin with a few papers before scaling up
- **Follow PRISMA**: Use the built-in guidance for methodology compliance
- **Track Progress**: Regular dashboard checks to identify bottlenecks
- **Document Everything**: Use the built-in recording features for transparency

## 🆘 Troubleshooting

- **Async Issues**: Use Docker version for better event loop handling
- **Tool Errors**: Check input validation requirements in error messages  
- **File Access**: Ensure proper path mounting for Docker containers
- **Database Issues**: Server creates SQLite database automatically

Your SLR MCP Server is now ready for professional systematic literature review work!