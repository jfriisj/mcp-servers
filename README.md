# MCP Servers

A collection of Model Context Protocol (MCP) servers providing specialized development tools through standardized AI assistant integration with unified Docker deployment and CI/CD workflows.

## 🚀 Overview

This repository contains multiple specialized MCP servers designed for comprehensive software development workflows:

### 🏗️ Core MCP Servers
- **🎯 SOLID Server** - SOLID principles analysis and code quality assessment for Python
- **🎤 Whisper Server** - Audio transcription using local Hugging Face Whisper Large V3 model  
- **🔍 Import Analysis Server** - Python import validation, dependency analysis, and circular import detection
- **� Study Buddy Server** - Document processing, intelligent chunking, and AI-powered study assistance
- **�🔧 Multi-Lint Servers** - Comprehensive linting for Python, Infrastructure as Code, and Docker

### 🚀 Unified Deployment Strategy
- **GitHub Container Registry** - Lightweight servers optimized for size and performance
- **Docker Hub** - Full-featured servers with GPU support and large dependencies
- **Automated CI/CD** - Trigger-based builds using commit message patterns (`@server-name`)
- **Multi-platform Support** - AMD64 and ARM64 architectures where applicable

These servers enable AI assistants to perform comprehensive code analysis, audio transcription, and development workflow automation through the standardized MCP protocol.

## 📦 Servers

### ⚖️ SOLID Server

**Location:** `solid-server/`

Provides comprehensive SOLID principles analysis for Python code, helping developers write more maintainable, testable, and flexible software.

**Features:**
- **Complete SOLID Analysis** - Checks all five principles: SRP, OCP, LSP, ISP, DIP
- **AST-based Analysis** - Uses Python's Abstract Syntax Tree for accurate parsing
- **Severity Classification** - High, medium, and low priority violations
- **Educational Content** - Detailed explanations with examples and best practices
- **Batch Processing** - Analyze entire directories and generate reports
- **Multiple Output Formats** - Text, JSON, and Markdown reports
- **Code Quality Scoring** - 0-100 compliance scores with improvement tracking

**Key Tools:**
- `solid-check-file` - Analyze single Python file for SOLID violations
- `solid-check-directory` - Batch analyze directory of Python files  
- `solid-generate-report` - Create comprehensive SOLID compliance reports
- `solid-explain-principle` - Get detailed explanations of SOLID principles
- `solid-check-score` - Get compliance scores for files or directories
- `solid-list-violations` - List violations with filtering options

### 🎙️ Whisper Server

**Location:** `whisper-server/`

Provides audio transcription capabilities using the local Hugging Face Whisper Large V3 model for converting speech to text.

**Features:**

- **Local Whisper Large V3 Model**: Run transcription locally without API calls
- **High-accuracy transcription** using OpenAI's Whisper Large V3 model
- **Multiple audio formats** support (MP3, WAV, M4A, FLAC, etc.)
- **Timestamp extraction** with detailed segment information
- **Language detection** and multi-language support
- **Batch processing** for multiple audio files
- **GPU acceleration** support (optional)
- **Configurable output formats** (text, JSON, SRT, VTT)

**Key Tools:**

- `whisper-transcribe` - Transcribe audio file to text
- `whisper-transcribe-timestamps` - Transcribe with timestamps
- `whisper-detect-language` - Detect audio language
- `whisper-batch-transcribe` - Batch transcribe multiple files

### 🔍 Import Analysis Server

**Location:** `import-analysis-server/`

Comprehensive Python import validation, dependency analysis, and architectural assessment to ensure code correctness and maintainability.

**Features:**
- **Import Validation** - Check if all imports can be resolved and are accessible
- **Circular Import Detection** - Find and analyze circular dependency chains
- **Unused Import Detection** - Identify imports that aren't referenced in code
- **Dependency Analysis** - Validate project dependencies and detect missing packages
- **Dependency Tree Visualization** - Generate visual tree diagrams and dependency maps
- **Architecture Analysis** - Assess adherence to architectural patterns (clean, layered, hexagonal)
- **Health Scoring** - Calculate comprehensive import health metrics (0-100)
- **Service Dependencies** - Analyze cross-service dependencies and usage patterns
- **Multiple Analysis Levels** - Single file, directory, or entire project analysis
- **Issue Classification** - Categorize issues by type, severity, and architectural impact

**Key Tools:**
- `import-analysis-analyze-file` - Analyze imports in a single Python file
- `import-analysis-analyze-project` - Comprehensive project-wide import analysis
- `import-analysis-circular-imports` - Detect and map circular import dependencies
- `import-analysis-validate-dependencies` - Check missing/unused dependencies
- `import-analysis-unused-imports` - Find unused imports across files
- `import-analysis-get-stats` - Get comprehensive import statistics and metrics
- `import-analysis-dependency-tree` - Generate visual dependency tree diagrams
- `import-analysis-architecture-analysis` - Analyze architectural patterns and violations
- `import-analysis-service-dependencies` - Analyze cross-service dependency patterns

### � Study Buddy Server

**Location:** `study_buddy/`

Comprehensive document processing and AI-powered study assistance platform for managing and analyzing academic and professional documents.

**Features:**
- **Document Processing** - Upload and parse PDF, DOCX, PPTX, and Markdown files
- **Intelligent Chunking** - Smart content segmentation using chapter, section, heading, or slide-based strategies
- **AI-Powered Summaries** - Generate brief, standard, or detailed summaries with rich metadata
- **Export Capabilities** - Create markdown files with YAML frontmatter for external tools
- **Full-Text Search** - Advanced search across documents and chunks with filtering
- **Study Workflows** - Native MCP prompts for document analysis, comparison, and concept extraction
- **Progress Tracking** - Monitor reading progress and study sessions
- **Bookmark Management** - Save and organize important document sections

**Key Tools:**
- `upload_document` - Process and store documents with metadata extraction
- `index_document` - Create intelligent chunks using configurable strategies
- `save_summary` - Generate AI summaries with export-ready metadata
- `search_documents` - Full-text search with advanced filtering options
- `create_markdown_file` - Export content to standalone markdown files
- `get_document_structure` - Retrieve organized document table of contents
- `export_summary_to_file` - Export summaries with rich metadata for external use

**Native MCP Prompts:**
- `analyze_document` - Comprehensive document analysis with focus areas
- `create_study_plan` - Structured study planning with timeline management
- `summarize_chapter` - Focused chapter summarization with style options
- `compare_documents` - Comparative analysis across multiple documents
- `extract_key_concepts` - Concept extraction and definition generation
- `research_questions` - Generate study questions at different complexity levels

### �🔧 Multi-Lint Servers

**Docker Images Available:**
- `ghcr.io/jfriisj/multi-lint-python` - Comprehensive Python linting (ruff, black, mypy, pylint, etc.)
- `ghcr.io/jfriisj/multi-lint-infrastructure` - Infrastructure as Code linting (terraform, ansible, kubernetes)
- `ghcr.io/jfriisj/multi-lint-docker` - Docker and containerization linting (hadolint, dive, etc.)

**Features:**
- **Multi-Tool Integration** - Run multiple linters in a single command
- **Standardized Output** - Unified reporting across different linting tools
- **Configuration Management** - Centralized configuration for all linting tools
- **Performance Optimization** - Parallel execution and intelligent caching
- **CI/CD Ready** - Designed for automated pipeline integration

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MCP-compatible client (VS Code with MCP extension, Claude Desktop, etc.)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jfriisj/mcp-servers.git
   cd mcp-servers
   ```

2. **Install individual servers:**

   ```bash
   # SOLID Server
   cd solid-server
   pip install -r requirements.txt

   # Whisper Server
   cd ../whisper-server
   pip install -r requirements.txt
   # Set HUGGINGFACE_TOKEN environment variable or update .env file
   
   # Import Test Server
   cd ../import-test-server
   pip install -r requirements.txt
   ```

3. **Configure MCP client** (example for VS Code `.vscode/mcp.json`):

   ```json
   {
     "servers": {
       "solid": {
         "command": "python",
         "args": ["solid-server/src/main.py", "--project-root", "${workspaceFolder}"],
         "cwd": "${workspaceFolder}/mcp-servers"
       },
       "whisper": {
         "command": "python",
         "args": ["src/main.py"],
         "cwd": "${workspaceFolder}/mcp-servers/whisper-server",
         "env": {
           "HUGGINGFACE_TOKEN": "${HUGGINGFACE_TOKEN}",
           "USE_GPU": "true"
         }
       },
       "import-analysis": {
         "command": "python",
         "args": ["import-analysis-server/src/main.py", "--project-root", "${workspaceFolder}"],
         "cwd": "${workspaceFolder}/mcp-servers"
       }
     }
   }
   ```

## 🐳 Docker Deployment

### Quick Start with Docker

**Pull and run servers directly from registries:**

```bash
# SOLID Server (GitHub Container Registry)
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/solid-mcp-server:latest

# Import Analysis Server (GitHub Container Registry)  
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/import-analysis-mcp-server:latest

# Whisper CPU Server (GitHub Container Registry)
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/whisper-mcp-server-cpu:latest

# Whisper GPU Server (Docker Hub - requires GPU support)
docker run --rm -i --gpus all -v "${PWD}:/workspace" \
  jfriisj/whisper-mcp-server-gpu:latest

# Study Buddy Server (GitHub Container Registry)
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/study-buddy-mcp-server:latest

# Multi-Lint Python
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/multi-lint-python:latest

# Multi-Lint Infrastructure
docker run --rm -i -v "${PWD}:/workspace" \
  ghcr.io/jfriisj/multi-lint-infrastructure:latest
```

### Docker MCP Configuration

Add Docker-based servers to your MCP configuration:

```json
{
  "servers": {
    "solid-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "ghcr.io/jfriisj/solid-mcp-server:latest"
      ]
    },
    "whisper-docker-cpu": {
      "command": "docker", 
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace", 
        "-e", "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}",
        "ghcr.io/jfriisj/whisper-mcp-server-cpu:latest"
      ]
    },
    "import-analysis-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "ghcr.io/jfriisj/import-analysis-mcp-server:latest" 
      ]
    }
  }
}
```

## ⚙️ Configuration

### SOLID Server

The SOLID server analyzes Python code using AST parsing. No additional configuration is required, but you can customize analysis by filtering principles or severity levels when calling tools.

### Whisper Server

Requires Hugging Face authentication token set as environment variable:

```bash
export HUGGINGFACE_TOKEN="your-huggingface-token-here"
```

Or create a `.env` file in the whisper-server directory:

```bash
HUGGINGFACE_TOKEN=your_actual_huggingface_token_here
USE_GPU=true  # Optional: enable GPU acceleration
```

Supported audio formats: MP3, WAV, M4A, FLAC, OGG, WEBM
Maximum file size: 100MB (local processing allows larger files than API limits)

## 📖 Usage Examples

### Analyzing Python Code for SOLID Principles

```python
# Analyze a single file
await call_tool("solid-check-file", {
    "file_path": "src/main.py",
    "principles": ["SRP", "DIP"]
})

# Analyze entire directory
await call_tool("solid-check-directory", {
    "directory_path": "src/",
    "max_files": 50
})

# Generate comprehensive report
await call_tool("solid-generate-report", {
    "directory_path": "src/",
    "output_format": "markdown",
    "include_suggestions": True
})

# Get principle explanation
await call_tool("solid-explain-principle", {
    "principle": "SRP"
})
```

### Audio Transcription

```python
# Transcribe audio file
await call_tool("whisper-transcribe", {
    "audio_file": "recording.mp3",
    "language": "en",
    "response_format": "json"
})

# Transcribe with timestamps
await call_tool("whisper-transcribe-timestamps", {
    "audio_file": "interview.wav"
})

# Detect language
await call_tool("whisper-detect-language", {
    "audio_file": "unknown_language.mp3"
})

# Batch transcribe
await call_tool("whisper-batch-transcribe", {
    "audio_files": ["file1.mp3", "file2.wav", "file3.m4a"]
})
```

## 🔗 Integration

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "solid": {
      "command": "python",
      "args": [
        "solid-server/src/main.py",
        "--project-root",
        "${workspaceFolder}"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    "whisper": {
      "command": "python",
      "args": [
        "whisper-server/src/main.py"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solid": {
      "command": "python",
      "args": ["path/to/solid-server/src/main.py", "--project-root", "path/to/project"]
    },
    "whisper": {
      "command": "python",
      "args": ["path/to/whisper-server/src/main.py"],
      "env": {
        "HUGGINGFACE_TOKEN": "your-huggingface-token-here"
      }
    }
  }
}
```

## 🏗️ Development

### Running Individual Servers

```bash
# SOLID Server
cd solid-server/src
python main.py --project-root /path/to/project

# SOLID Server (test mode)
python main.py --test

# Whisper Server
cd whisper-server/src
python main.py
```

### Testing

Each server includes test mode for development:

```bash
# Test SOLID server
python solid-server/src/main.py --test

# Test MCP protocol
python test_solid_mcp_protocol.py

# Test Whisper server
python whisper-server/tests/test_whisper.py

# Test Import Test server
python import-test-server/src/main.py --test
```

## � Unified CI/CD Workflow

### Automated Building with Commit Triggers

The repository uses a unified GitHub Actions workflow that builds and publishes Docker images based on commit message patterns:

#### Single Server Builds
```bash
# Build SOLID server
git commit -m "feat: Updated SOLID analysis @solid"

# Build Import Analysis server  
git commit -m "fix: Import resolution bug @import-analysis"

# Build Whisper CPU server
git commit -m "feat: Audio optimization @whisper"
# or
git commit -m "feat: Audio optimization @whisper-cpu"

# Build Whisper GPU server (Docker Hub)
git commit -m "feat: CUDA acceleration @whisper-gpu"
```

#### Batch Builds
```bash
# Build all compatible servers (excludes GPU due to size limits)
git commit -m "feat: Major updates across all servers @all"
```

### Registry Strategy

| Server | Registry | Size | Trigger | Platforms |
|--------|----------|------|---------|-----------|
| SOLID MCP | GitHub Container Registry | ~500MB | `@solid` | linux/amd64, linux/arm64 |
| Import Analysis MCP | GitHub Container Registry | ~300MB | `@import-analysis` | linux/amd64, linux/arm64 |
| Whisper CPU MCP | GitHub Container Registry | ~3GB | `@whisper` or `@whisper-cpu` | linux/amd64, linux/arm64 |
| Whisper GPU MCP | Docker Hub | ~16GB | `@whisper-gpu` | linux/amd64 |

### Manual Workflow Triggers

You can also trigger builds manually from the GitHub Actions tab using the "Run workflow" button.

## 🎯 Registry Commands

### GitHub Container Registry (Public)
```bash
# Pull latest versions
docker pull ghcr.io/jfriisj/solid-mcp-server:latest
docker pull ghcr.io/jfriisj/import-analysis-mcp-server:latest  
docker pull ghcr.io/jfriisj/whisper-mcp-server-cpu:latest
docker pull ghcr.io/jfriisj/multi-lint-python:latest
docker pull ghcr.io/jfriisj/multi-lint-infrastructure:latest
docker pull ghcr.io/jfriisj/multi-lint-docker:latest
```

### Docker Hub (Public) 
```bash
# GPU-enabled servers (large images)
docker pull jfriisj/whisper-mcp-server-gpu:latest
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following existing patterns
4. **Test locally** using both direct Python execution and Docker
5. **Update documentation** including README and tool descriptions
6. **Commit with appropriate trigger** to test CI/CD pipeline
7. **Submit a pull request**

### Adding New Servers

1. **Create server directory** following existing structure:
   ```
   new-server/
   ├── src/
   │   ├── main.py
   │   ├── server.py
   │   └── mcp_handler.py
   ├── Dockerfile
   ├── requirements.txt
   └── README.md
   ```

2. **Update unified workflow** in `.github/workflows/mcp-servers.yml`:
   - Add new build job
   - Configure appropriate registry (GitHub vs Docker Hub)
   - Set trigger pattern (e.g., `@new-server`)

3. **Update MCP configuration** in `.vscode/mcp.json`

4. **Test deployment** using trigger commit:
   ```bash
   git commit -m "feat: Add new server @new-server"
   ```

### Development Guidelines

- **Follow MCP Protocol** - Implement standardized tool and resource interfaces
- **Container-First Design** - Ensure servers work in containerized environments  
- **Multi-Platform Support** - Test on both AMD64 and ARM64 when possible
- **Size Optimization** - Keep Docker images under 2GB for GitHub Container Registry
- **Comprehensive Documentation** - Include usage examples and configuration options
- **Automated Testing** - Add health checks and validation scripts
- **Registry Strategy** - Use GitHub Container Registry for smaller images, Docker Hub for larger ones

### Testing Changes

```bash
# Test locally with Python
cd server-name/src
python main.py --test

# Test with Docker build
docker build -t test-server .
docker run --rm test-server --help

# Test CI/CD trigger
git commit -m "test: Validate changes @server-name"
```

## 📋 Requirements

### SOLID Server Dependencies

- Python 3.8+
- mcp>=0.1.0
- pydantic>=2.0.0

### Whisper Server Dependencies

- Python 3.8+
- mcp>=0.1.0
- transformers>=4.35.0
- torch>=2.0.0
- torchaudio>=2.0.0
- datasets>=2.14.0
- accelerate>=0.24.0
- python-dotenv>=1.0.0

### Import Analysis Server Dependencies

- Python 3.8+
- mcp>=0.1.0
- ast (built-in)
- typing-extensions>=4.8.0
- pathlib (built-in)

### Multi-Lint Server Dependencies

Multi-lint servers are containerized and include all necessary dependencies:
- **Python**: ruff, black, mypy, pylint, bandit, isort, autoflake, safety, vulture
- **Infrastructure**: terraform (tflint, tfsec), ansible-lint, kubeval, kube-score, yamllint  
- **Docker**: hadolint, dive, trivy, docker-bench-security, container-structure-test

## 📄 License

This project is open source. See individual server directories for specific licensing information.

## � Project Health

**Import Analysis Results** (via `import-analysis-docker`):
- **Files Analyzed**: 75 Python files across all servers
- **Import Success Rate**: 83.7% (364/435 imports resolved)
- **Health Score**: 28.5/100 (room for improvement in inter-server dependencies)
- **Circular Imports**: 0 (excellent architectural isolation)

*Note: Lower health score reflects the multi-server architecture with independent dependencies rather than code quality issues.*

## 🏷️ Version History

- **v2.0.0** - Unified workflow system with automated Docker deployment
- **v1.5.0** - Added Import Analysis Server and Multi-Lint integration
- **v1.0.0** - Initial release with SOLID and Whisper servers

## �🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized AI assistant integration
- [GitHub Actions](https://github.com/features/actions) for the unified CI/CD workflow system
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) and [Docker Hub](https://hub.docker.com/) for container hosting
- [Ruff](https://github.com/astral-sh/ruff) for inspiring fast, modern Python tooling
- [OpenAI Whisper](https://github.com/openai/whisper) for the Whisper model architecture
- [Hugging Face](https://huggingface.co/) for the Transformers library and model hosting
- [Docker](https://www.docker.com/) for containerization and multi-platform support

---

**Note:** These servers are designed to work with MCP-compatible clients such as VS Code with MCP extension, Claude Desktop, or any other MCP-compliant AI assistant. Ensure your development environment supports the Model Context Protocol for full functionality.

**Registry Status**: All servers are publicly available and ready for production use. No authentication required for pulling Docker images.
