# SLR MCP Server

A production-ready Model Context Protocol (MCP) server for systematic literature review operations. This server provides comprehensive tools for managing academic research papers, quality assessments, and systematic review workflows.

## Features

- **Academic Paper Management**: Upload, parse, and manage research papers (PDF, DOCX, LaTeX, BibTeX)
- **Quality Assessment**: PRISMA-compliant quality assessment with multiple frameworks
- **Citation Analysis**: Extract and analyze citation networks and patterns
- **Research Questions**: PICO/SPIDER framework support for research question validation
- **Hypothesis Testing**: Statistical hypothesis analysis and evidence synthesis
- **Full-Text Search**: FTS5-powered semantic search across papers and content
- **Systematic Reviews**: Complete SLR workflow support with progress tracking

## Quick Start

1. **Start the Server**:
   ```bash
   python start_server.py
   ```

2. **List Available Tools**:
   ```bash
   python list_slr_tools.py
   ```

3. **Run Complete Workflow**:
   ```bash
   python slr_workflow.py
   ```

## Production Ready

- **No Demo Code**: All placeholder implementations removed
- **Single Implementation**: One robust implementation per component  
- **Production Database**: Comprehensive schema with proper indexes
- **Error Handling**: Complete exception handling and validation
- **Performance**: Optimized queries and FTS5 search indexes

**Systematic Literature Review MCP Server** - A comprehensive MCP server for academic researchers conducting systematic literature reviews with AI assistance.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://github.com/anthropic/mcp-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The SLR MCP Server provides AI-powered tools for conducting systematic literature reviews following established academic standards including PRISMA, PICO/SPIDER frameworks, and GRADE evidence assessment. It integrates seamlessly with Claude and VS Code through the Model Context Protocol (MCP).

## Features

- **Research Document Management**: Upload, process, and manage academic papers with metadata extraction
- **Quality Assessment**: Evaluate papers using systematic frameworks (PRISMA, STROBE, CONSORT, QUADAS)
- **Research Question Validation**: Validate research questions using PICO/SPIDER frameworks
- **Citation Analysis**: Perform citation network analysis and impact assessment
- **Hypothesis Testing**: Test research hypotheses against evidence with statistical analysis
- **Academic Indexing**: Create intelligent chunks and indexes for research papers
- **Evidence Synthesis**: Synthesize evidence from multiple papers with meta-analysis support

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/slr-team/slr-mcp-server.git
cd slr-mcp-server
```

2. Install the package:
```bash
pip install -e .
```

### Development Installation

For development work, install with development dependencies:
```bash
pip install -e ".[dev]"
```

## Usage

### Running the Server

The server can be run in several ways:

1. **As a module**:
```bash
python -m slr_server
```

2. **Using the CLI script** (after installation):
```bash
slr-mcp-server
```

3. **Direct execution**:
```bash
python src/server.py
```

### MCP Client Integration

Add the server to your MCP client configuration. For example, with Claude Desktop:

```json
{
  "mcpServers": {
    "slr-server": {
      "command": "python",
      "args": ["-m", "slr_server"],
      "cwd": "/path/to/slr-mcp-server"
    }
  }
}
```

## Available Tools

### upload-paper
Upload and process research papers with automatic metadata extraction.

**Parameters:**
- `file_path` (required): Path to the paper file (PDF or text)
- `title` (optional): Paper title
- `authors` (optional): List of author names
- `doi` (optional): Digital Object Identifier
- `tags` (optional): Classification tags

### assess-quality
Assess paper quality using systematic evaluation frameworks.

**Parameters:**
- `paper_id` (required): ID of the paper to assess
- `framework` (optional): Assessment framework (prisma, strobe, consort, quadas)
- `reviewer_id` (optional): Reviewer identifier
- `criterion_scores` (optional): Manual criterion scores override

### validate-research-question
Validate research questions using structured frameworks.

**Parameters:**
- `question_text` (required): The research question to validate
- `framework` (optional): Validation framework (pico, spider)

### analyze-citations
Perform citation network analysis on research papers.

**Parameters:**
- `paper_id` (required): ID of the paper to analyze

### test-hypothesis
Test research hypotheses against evidence from papers.

**Parameters:**
- `hypothesis_text` (required): The research hypothesis to test
- `paper_ids` (required): List of paper IDs containing evidence
- `significance_level` (optional): Statistical significance level (default: 0.05)

### index-paper
Create intelligent academic chunks and indexes for papers.

**Parameters:**
- `paper_id` (required): ID of the paper to index
- `strategy` (optional): Chunking strategy (section, semantic, hybrid)
- `optimization_level` (optional): Optimization level (basic, intermediate, advanced)

### synthesize-evidence
Synthesize evidence from multiple papers for research questions.

**Parameters:**
- `research_question` (required): The research question to investigate
- `paper_ids` (required): List of paper IDs to analyze
- `include_meta_analysis` (optional): Whether to include meta-analysis

## Architecture

The server follows Clean Architecture principles with clear separation of concerns:

- **Layer 1 (MCP Protocol)**: MCP server and protocol handlers
- **Layer 2 (Business Logic)**: Services implementing domain logic
- **Layer 3 (Data Access)**: Repositories and database operations
- **Layer 4 (Infrastructure)**: External dependencies and I/O

### Key Components

- **Server**: MCP protocol server and tool definitions
- **MCP Handler**: Protocol translation and parameter validation
- **Services**: Business logic implementation
  - ResearchDocumentService
  - QualityAssessmentService
  - ResearchQuestionService
  - HypothesisAnalysisService
  - AcademicChunkingService
- **Repositories**: Data access and persistence
- **Models**: Domain entities and data structures

## Development

### Code Quality

Run code quality checks:
```bash
# Linting
flake8 src/

# Type checking
mypy src/

# Code formatting
black src/
isort src/
```

### Testing

Run the test suite:
```bash
pytest
```

For coverage reports:
```bash
pytest --cov=slr_server --cov-report=html
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:

- GitHub Issues: [https://github.com/slr-team/slr-mcp-server/issues](https://github.com/slr-team/slr-mcp-server/issues)
- Documentation: [https://slr-mcp-server.readthedocs.io](https://slr-mcp-server.readthedocs.io)

## Acknowledgments

This server implements systematic literature review best practices based on:

- PRISMA guidelines for systematic reviews
- Cochrane Handbook for systematic reviews
- PICO and SPIDER frameworks for research questions
- GRADE framework for evidence assessment