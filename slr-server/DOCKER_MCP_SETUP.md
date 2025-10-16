# Docker Compose Setup for SLR MCP Server with PostgreSQL

This guide shows you how to use the Docker Compose setup with PostgreSQL and the SLR server as MCP tools.

## 🏗️ Architecture Overview

The setup includes:
- **PostgreSQL 15 Alpine** - Database for storing research papers, citations, and analysis data
- **SLR MCP Server** - 23 specialized tools for systematic literature review workflows
- **Docker Bridge Network** - Internal communication between services
- **Persistent Volumes** - Data persistence for database and logs

## 🚀 Quick Start

### 1. Start the Services

```bash
cd c:/github/mcp-servers/slr-server/deployment
docker compose up -d
```

This will:
- ✅ Start PostgreSQL database with automatic schema creation
- ✅ Launch SLR MCP server on port 8080
- ✅ Create internal Docker network for service communication
- ✅ Set up persistent volumes for data storage

### 2. Verify Services are Running

```bash
# Check service status
docker compose ps

# View logs
docker compose logs slr-server --tail=30
docker compose logs postgres --tail=20
```

Expected output should show:
```
✅ PostgreSQL tables and indexes created successfully
✅ Container initialized successfully  
✅ MCP server listening on port 8080
```

### 3. Stop Services

```bash
docker compose down
```

## 🛠️ Available MCP Tools (23 Tools)

The SLR server provides comprehensive tools for systematic literature review:

### 📚 Document Management
- `upload_paper` - Upload and parse academic papers (PDF, DOCX)
- `get_paper` - Retrieve paper information by ID
- `list_papers` - List papers with filters
- `search_papers` - Full-text semantic/keyword search
- `index_paper` - Create intelligent academic chunks
- `get_paper_structure` - Get paper sections and structure
- `get_chunk_content` - Retrieve specific text chunks

### 🔍 Quality Assessment
- `assess_quality` - PRISMA/CASP quality assessment
- `get_quality_assessment` - Retrieve quality scores
- `calculate_inter_rater_reliability` - Inter-rater agreement analysis

### 📊 Citation Analysis
- `analyze_citations` - Citation network analysis
- `detect_citation_patterns` - Find citation trends
- `export_citation_network` - Export for visualization

### 🧪 Research Validation
- `validate_research_question` - PICO/SPIDER framework validation
- `analyze_hypotheses` - Extract and analyze hypotheses
- `synthesize_evidence` - Meta-analysis and evidence synthesis

### 📋 Project Management
- `create_slr_project` - Initialize SLR project with workflow
- `get_slr_progress` - Progress dashboard
- `get_next_steps` - AI-powered workflow recommendations
- `create_screening_workflow` - Multi-stage screening setup
- `screen_paper` - Record screening decisions
- `get_slr_guide` - Interactive methodology guidance

### 📈 Reporting & Export
- `generate_slr_report` - Comprehensive SLR reports (Markdown/LaTeX/DOCX)

## 🔧 Configuration Options

### Environment Variables

The Docker Compose setup uses these key environment variables:

```yaml
environment:
  - DATABASE_TYPE=postgresql          # Use PostgreSQL instead of SQLite
  - POSTGRES_HOST=postgres           # Docker service name
  - POSTGRES_PORT=5432               # PostgreSQL port
  - POSTGRES_DB=slr_database         # Database name
  - POSTGRES_USER=slr_user           # Database user
  - POSTGRES_PASSWORD=slr_password   # Database password
  - LOG_LEVEL=INFO                   # Logging level
  - MCP_PORT=8080                    # MCP server port
  - MAX_PAPERS_PER_ANALYSIS=100      # Performance limit
```

### Customizing the Setup

1. **Change Database Credentials**: Edit the `docker-compose.yml` file
2. **Add Volume Mounts**: Map additional directories for papers/outputs
3. **Port Configuration**: Change external ports if needed
4. **Resource Limits**: Add memory/CPU limits for production

## 🔌 Using as MCP Tools

### Option 1: Direct MCP Connection

Connect directly to the containerized MCP server:

```json
{
  "mcpServers": {
    "slr-server-docker": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--network", "deployment_slr-network",
        "-e", "DATABASE_TYPE=postgresql",
        "-e", "POSTGRES_HOST=slr-postgres", 
        "-e", "POSTGRES_PORT=5432",
        "-e", "POSTGRES_DB=slr_database",
        "-e", "POSTGRES_USER=slr_user",
        "-e", "POSTGRES_PASSWORD=slr_password",
        "slr-mcp-server:latest",
        "python", "-m", "src.main"
      ]
    }
  }
}
```

### Option 2: Via HTTP API (if implemented)

Connect to the running container via HTTP:

```json
{
  "mcpServers": {
    "slr-server-http": {
      "command": "curl",
      "args": ["-X", "POST", "http://localhost:8080/mcp", "-H", "Content-Type: application/json"]
    }
  }
}
```

## 📁 Data Persistence

### Database Data
- **Location**: `postgres_data` Docker volume
- **Contents**: All research papers, citations, quality assessments
- **Backup**: Use `pg_dump` for database backups

### Logs
- **Location**: `slr_logs` Docker volume  
- **Contents**: Application logs, error traces
- **Access**: `docker compose logs slr-server`

### Paper Files
- **Location**: `./papers` directory (mounted read-only)
- **Usage**: Place PDF/DOCX files here for upload_paper tool

## 🔍 Example Workflow

### 1. Upload Research Papers
```bash
# Place papers in ./papers/ directory
cp "research-paper.pdf" ./papers/

# Use upload_paper tool via MCP client
```

### 2. Create SLR Project
```bash
# Use create_slr_project tool with:
{
  "title": "Machine Learning in Healthcare",
  "research_domain": "Computer Science",
  "description": "Systematic review of ML applications in healthcare",
  "team_lead": "Research Lead"
}
```

### 3. Conduct Analysis
```bash
# Screen papers, assess quality, analyze citations
# All data persists in PostgreSQL database
```

### 4. Generate Reports
```bash
# Use generate_slr_report tool to create final reports
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker compose logs postgres

# Verify internal network
docker network ls | grep slr-network
```

### Service Communication
```bash  
# Test internal connectivity
docker compose exec slr-server ping postgres
```

### Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep :5432
netstat -an | grep :8080
```

### Reset Everything
```bash
# Complete cleanup and restart
docker compose down -v  # Removes volumes too
docker compose up -d
```

## 📚 Next Steps

1. **Configure your MCP client** to connect to the containerized server
2. **Upload research papers** using the papers volume mount
3. **Create an SLR project** to get started with structured workflows
4. **Use the 23 specialized tools** for comprehensive literature review
5. **Generate reports** in your preferred format (Markdown/LaTeX/DOCX)

The system provides a complete containerized solution for systematic literature reviews with PostgreSQL persistence and professional-grade tools for academic research workflows.