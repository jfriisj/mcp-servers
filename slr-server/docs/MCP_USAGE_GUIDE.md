# SLR MCP Server - Usage Guide

## Quick Start

### 1. **Direct Python Usage**

```bash
# Navigate to the project directory
cd C:\github\mcp-servers\slr-server

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run the server directly
python -m src.main
```

### 2. **Claude Desktop Integration**

1. Copy `claude_desktop_config.json` to your Claude Desktop config location:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Restart Claude Desktop

3. You'll now have access to all SLR research tools!

### 3. **VS Code Integration**

1. Install the "MCP Tools" extension in VS Code
2. Open this project folder in VS Code
3. The `.vscode/mcp.json` file will be automatically detected
4. Access tools via the MCP panel

### 4. **Docker Usage**

```bash
# Build the Docker image
docker build -t slr-mcp-server:latest .

# Run with Docker Compose
docker-compose up -d

# Use the docker_mcp_config.json for MCP integration
```

## Available Tools

The SLR MCP Server provides 20+ specialized tools for systematic literature reviews:

### 📄 **Document Management**
- `upload-paper`: Upload and process academic papers
- `index-paper`: Create intelligent academic chunks and indexes
- `extract-paper-metadata`: Extract bibliographic information

### 🔍 **Quality Assessment**
- `assess-quality`: PRISMA/COCHRANE quality evaluation
- `calculate-inter-rater-reliability`: Multi-reviewer agreement analysis
- `generate-quality-report`: Comprehensive quality assessment reports

### ❓ **Research Question Management**
- `validate-research-question`: PICO/SPIDER framework validation
- `optimize-research-question`: AI-powered question improvement
- `generate-search-strategy`: Database search term generation

### 🧪 **Hypothesis Analysis**
- `analyze-hypothesis`: Extract and test hypotheses
- `synthesize-evidence`: GRADE framework evidence synthesis
- `perform-meta-analysis`: Statistical meta-analysis

### 🔗 **Citation Analysis**
- `analyze-citations`: Citation network mapping
- `find-related-papers`: Similarity-based paper discovery
- `track-research-trends`: Temporal analysis of research areas

### 📊 **Data Export & Reporting**
- `export-prisma-flow`: Generate PRISMA flow diagrams
- `generate-evidence-summary`: Structured evidence tables
- `export-bibtex`: Bibliography management

## Example Usage

### Research Workflow Example

```python
# 1. Upload papers
upload_result = await call_tool("upload-paper", {
    "file_path": "./papers/ml_healthcare.pdf",
    "title": "Machine Learning in Healthcare",
    "tags": ["machine-learning", "healthcare"]
})

# 2. Validate research question
question_result = await call_tool("validate-research-question", {
    "question_text": "How effective are ML algorithms in improving diagnostic accuracy?",
    "framework": "pico",
    "suggest_improvements": True
})

# 3. Assess paper quality
quality_result = await call_tool("assess-quality", {
    "paper_id": 1,
    "framework": "prisma",
    "reviewer_id": "researcher_001"
})

# 4. Perform evidence synthesis
synthesis_result = await call_tool("synthesize-evidence", {
    "research_question_id": 1,
    "paper_ids": [1, 2, 3],
    "include_meta_analysis": True
})
```

## Configuration Options

### Environment Variables

- `DATABASE_PATH`: SQLite database location (default: `./slr_database.db`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_PORT`: Server port (default: 8080)
- `MAX_PAPERS_PER_ANALYSIS`: Maximum papers per analysis (default: 100)
- `ENABLE_CACHING`: Enable result caching (true/false)

### Database Setup

The server automatically creates the SQLite database on first run. For production:

```bash
# Use PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/slr_db"

# Or use the Docker Compose setup with PostgreSQL
docker-compose -f docker-compose.yml up -d
```

## Integration Examples

### With Claude Desktop
Once configured, simply ask Claude:
- "Upload this research paper and assess its quality"
- "Validate this research question using PICO framework"
- "Perform a meta-analysis on these studies"

### With VS Code
1. Open the MCP Tools panel
2. Select the appropriate tool
3. Fill in the parameters
4. Execute and view results

### Programmatically
Use the `mcp_client_example.py` script as a starting point for custom integrations.

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure you've installed the package with `pip install -e .`

2. **Database permission errors**: Check that the `DATABASE_PATH` directory is writable

3. **Port conflicts**: Change `MCP_PORT` if 8080 is in use

4. **Memory issues with large papers**: Adjust `MAX_PAPERS_PER_ANALYSIS` for your system

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.main
```

## Academic Standards Compliance

The SLR MCP Server follows established academic standards:

- **PRISMA**: Systematic review reporting standards
- **COCHRANE**: Quality assessment methodologies  
- **GRADE**: Evidence quality evaluation
- **PICO/SPIDER**: Research question frameworks

This ensures all analyses meet academic publication standards for systematic literature reviews.