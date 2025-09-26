# Documentation and Prompts MCP Server

A comprehensive Model Context Protocol (MCP) server that combines intelligent documentation indexing with advanced prompt management, enabling AI assistants to understand project architecture and apply context-aware prompts for consistent, high-quality development.

## 🚀 Overview

The Documentation and Prompts MCP Server transforms how AI assistants interact with your codebase by providing:

- **📚 Smart Documentation Indexing** - Automatically indexes and searches your project's documentation with configurable root folder support
- **🎯 Intelligent Prompt Management** - Context-aware prompts that automatically incorporate relevant documentation
- **🔗 Seamless Integration** - Documentation informs prompts, prompts reference documentation
- **⚡ Real-time GUI Viewer** - Visual interface for exploring indexed content and managing prompts
- **📊 Analytics & Insights** - Usage tracking and effectiveness metrics for continuous improvement

## ✨ Key Features

### 🐍 Python Code Analysis

- **Shared utility indexing** - Automatically indexes Python files from service utils directories
- **Class and function extraction** - Parses Python source code to extract classes, functions, and methods
- **Docstring preservation** - Maintains and indexes Python docstrings for context
- **Import relationship mapping** - Tracks module dependencies and imports
- **Cross-service code reuse** - Enables easy discovery of shared functionality across services

### 🎯 Intelligent Prompt System

- **Context-aware prompts** that automatically incorporate relevant documentation
- **Template-based prompts** with dynamic variable substitution from your docs
- **Categorized prompt library** with 8 predefined categories (code-quality, architecture, documentation, testing, refactoring, api, security, custom)
- **Usage tracking and analytics** to measure prompt effectiveness
- **Custom prompt creation** with full versioning and management
- **Smart suggestions** based on task context and documentation patterns

### 🖥️ GUI Database Viewer

- **Real-time database exploration** of indexed documents and prompts
- **Interactive search and filtering** across all content
- **Prompt usage analytics** with charts and statistics
- **Document structure visualization** showing sections and metadata
- **Live server integration** for immediate content updates

### 🔧 Enterprise-Grade Architecture

- **SQLite-based storage** with optimized indexing for fast searches
- **Configurable performance settings** for large codebases
- **Comprehensive error handling** with graceful fallbacks
- **Thread-safe operations** with proper concurrency management
- **Extensible plugin architecture** for custom document parsers

## 📁 Project Structure

```
docs-prompts-server/
├── src/
│   ├── main.py                        # Main MCP server entry point
│   ├── server.py                       # Core server facade
│   ├── config.py                       # Configuration management
│   ├── database.py                     # Database operations
│   ├── document_indexer.py             # Document indexing logic
│   ├── document_processor.py           # Document processing utilities
│   ├── prompt_manager.py               # Prompt management system
│   ├── mcp_handler.py                  # MCP protocol handling
│   ├── gui_manager.py                  # GUI management
│   ├── models.py                       # Data models
│   └── docs_db_viewer.py               # GUI database viewer
├── config/
│   └── server_config.yaml             # Server configuration
├── prompts/
│   └── categories.yaml                # Prompt category definitions
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- MCP-compatible client (VS Code with MCP extension, Claude Desktop, etc.)

### 1. Install Dependencies

```bash
cd docs-prompts-server
pip install -r requirements.txt
```

### 2. Configure the Server

The server uses `config/server_config.yaml` for configuration. Key settings include:

```yaml
# Documentation paths to scan
documentation_paths:
  - "docs/"
  - "README.md"
  - "*.md"

# File patterns and exclusions
file_patterns: ["*.md", "*.rst", "*.yaml", "*.json"]
exclude_patterns: ["node_modules/", ".git/", "__pycache__/"]

# Architecture keywords for detection
architecture_keywords:
  - "architecture"
  - "design"
  - "pattern"
  - "api"
  - "service"
```

### 3. Add to MCP Configuration

#### VS Code (.vscode/mcp.json)

```json
{
  "servers": {
    "docs": {
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": [
        "mcp-servers/docs-prompts-server/src/main.py",
        "--root-folder",
        "${workspaceFolder}"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

#### Claude Desktop (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": [
        "/path/to/docs-prompts-server/src/main.py",
        "--root-folder",
        "/path/to/your/project"
      ]
    }
  }
}
```

### 4. Command Line Options

The server supports the following command line arguments:

- `--root-folder PATH`: Specify the root folder for documentation indexing (defaults to current directory or `DOCS_PROJECT_ROOT` environment variable)
- `--help`: Show help message and exit

**Example usage:**

```bash
# Use specific project root
python src/main.py --root-folder /path/to/project

# Use environment variable
export DOCS_PROJECT_ROOT=/path/to/project
python src/main.py
```

### 5. Launch GUI Viewer (Optional)

```bash
cd docs-prompts-server/src
python docs_db_viewer.py --gui
```

## ⚙️ Configuration

### Core Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `documentation_paths` | Paths to scan for documentation | `["docs/", "README.md", "*.md"]` |
| `file_patterns` | File extensions to index | `["*.md", "*.rst", "*.yaml", "*.json"]` |
| `exclude_patterns` | Paths to skip during indexing | `["node_modules/", ".git/"]` |
| `max_file_size_mb` | Maximum file size to index | `10` |
| `architecture_keywords` | Keywords for architecture detection | See config file |

### Root Folder Configuration

The server can be configured to index documentation from a specific root folder using either:

1. **Command line argument**: `--root-folder /path/to/project`
2. **Environment variable**: `DOCS_PROJECT_ROOT=/path/to/project`
3. **MCP server configuration**: Pass `--root-folder ${workspaceFolder}` in the args array

When no root folder is specified, the server defaults to the current working directory.

### Performance Tuning

```yaml
indexing:
  auto_index_on_startup: true
  watch_for_changes: true
  batch_size: 100
  cache_search_results: true
  max_cache_size: 1000

search:
  default_limit: 10
  max_limit: 50
  fuzzy_matching: true
```

### Prompt Management

```yaml
prompts:
  auto_load_on_startup: true
  enable_usage_tracking: true
  enable_version_control: true
  template_engine: "jinja2"
```

## 📚 Resources

The server exposes several MCP resources for programmatic access:

- `docs://index` - Complete documentation index with metadata
- `docs://architecture` - Architecture-related documentation summary
- `docs://statistics` - Indexing statistics and metrics
- `prompts://library` - Complete prompt library
- `prompts://categories` - Available prompt categories
- `prompts://usage-stats` - Usage analytics and effectiveness metrics

## 🔧 Available Tools

### 🔍 Code Reuse Tools (USE FIRST)

#### `find_code_reuse`

**ALWAYS USE THIS TOOL FIRST** when looking for existing code patterns, utilities, or implementations across services. This tool prioritizes Python code search to enable code reuse and maintain consistency.

**Parameters:**

```json
{
  "functionality": "logging",
  "service_context": "translation-service",
  "limit": 5
}
```

**Example:**

```python
# Always search for reusable code first
await call_tool("find_code_reuse", {
    "functionality": "circuit_breaker",
    "service_context": "api-gateway"
})
```

**Why use this first:**

- ✅ Finds existing implementations across services
- ✅ Provides reuse suggestions and import guidance
- ✅ Maintains architectural consistency
- ✅ Reduces code duplication
- ✅ Discovers proven patterns

### 📖 Documentation Tools

#### `find_documents`

Find relevant documentation and guides (optimized for document discovery). This tool focuses specifically on documentation files and excludes code files for targeted document searches.

**Parameters:**

```json
{
  "topic": "architecture patterns",
  "doc_type": ".md",
  "limit": 10
}
```

**Example:**

```python
await call_tool("find_documents", {
    "topic": "microservice architecture",
    "limit": 5
})
```

**Use cases:**
- Finding design documents and guides
- Locating API documentation
- Discovering architectural patterns
- Researching implementation guides

#### `search_docs`

General documentation search with flexible querying. Searches across all indexed content including both documentation and code files.

**Parameters:**

```json
{
  "query": "circuit breaker pattern",
  "doc_type": ".md",
  "limit": 10
}
```

**Example:**

```python
await call_tool("search_docs", {
    "query": "error handling",
    "limit": 5
})
```

**Use cases:**
- Broad searches across all content types
- When you need both docs and code results
- Complex queries with multiple terms

### 🏗️ Architecture Tools

#### `get_architecture_info`

Extract architecture patterns and design information from indexed documentation.

**Returns:** Summary of architecture-related documents with content snippets.

### 🔄 Management Tools

#### `index_documentation`

Re-index all documentation files or force a complete rebuild.

**Parameters:**

```json
{
  "force": false
}
```

### 🎯 Prompt Management Tools

#### `search_prompts`

Search prompts by keyword, category, or tags.

**Parameters:**

```json
{
  "query": "code review",
  "category": "code-quality",
  "limit": 10
}
```

#### `get_prompt`

Retrieve a specific prompt with full details.

**Parameters:**

```json
{
  "prompt_id": "code_review"
}
```

#### `suggest_prompts`

Get context-aware prompt suggestions.

**Parameters:**

```json
{
  "context": "security code review"
}
```

#### `create_prompt`

Create a new custom prompt.

**Parameters:**

```json
{
  "name": "Custom Security Review",
  "description": "Project-specific security analysis",
  "template": "Analyze this code for security issues...",
  "category": "security",
  "variables": ["code_content", "security_guidelines"],
  "tags": ["security", "review"]
}
```

### 🔗 Integration Tools

#### `generate_contextual_prompt`

Generate a prompt from documentation context.

**Parameters:**

```json
{
  "task": "API development",
  "docs_query": "rest api patterns"
}
```

#### `apply_prompt_with_context`

Apply a prompt with automatic context filling.

**Parameters:**

```json
{
  "prompt_id": "architecture_review",
  "content": "code to review",
  "auto_fill_context": true
}
```

## 🎯 Tool Usage Guidelines

### When to Use Each Tool

| Tool | Purpose | Best For |
|------|---------|----------|
| `find_code_reuse` | **ALWAYS FIRST** - Find reusable code patterns | Code reuse, shared utilities, implementation discovery |
| `find_documents` | Documentation-focused search | Design docs, guides, architectural patterns |
| `search_docs` | General content search | Broad queries, mixed content types |
| `get_architecture_info` | Architecture overview | System design, architectural patterns |
| `search_prompts` | Find existing prompts | Code review, testing, documentation tasks |

### Recommended Workflow

1. **🔍 Code Reuse First**: Always start with `find_code_reuse` to discover existing implementations
2. **📚 Documentation Search**: Use `find_documents` for design documents and guides
3. **🔧 Implementation**: Use `search_docs` for broader technical searches
4. **🎯 Apply Context**: Use prompt tools with documentation context

## 🖥️ GUI Database Viewer

Launch the interactive GUI to explore indexed content:

```bash
cd docs-prompts-server/src
python docs_db_viewer.py --gui
```

### Features:

- **📊 Database Statistics** - Overview of indexed documents and prompts
- **🔍 Document Explorer** - Browse all indexed documentation with metadata
- **🎯 Prompt Library** - View and manage all available prompts
- **📈 Usage Analytics** - Charts showing prompt effectiveness and usage patterns
- **🔎 Live Search** - Real-time search across all content
- **📋 Content Preview** - Full document and prompt content viewing

## 📖 Usage Examples

### Code Reuse Discovery

```python
# Always check for existing implementations first
results = await call_tool("find_code_reuse", {
    "functionality": "logging",
    "service_context": "translation-service"
})
```

### Documentation Search

```python
# Find architectural documentation
docs = await call_tool("find_documents", {
    "topic": "microservice architecture",
    "limit": 5
})

# General search across all content
all_results = await call_tool("search_docs", {
    "query": "error handling patterns"
})
```

### Context-Aware Code Review

```python
# Get architecture context
arch_info = await call_tool("get_architecture_info")

# Apply context-aware prompt
result = await call_tool("apply_prompt_with_context", {
    "prompt_id": "code_review",
    "content": "your_code_here",
    "auto_fill_context": true
})
```

## 🔄 Workflow Integration

### Development Workflow

1. **Index Documentation** - Server automatically indexes project docs on startup
2. **Context-Aware Assistance** - AI gets relevant docs for each task
3. **Consistent Quality** - Prompts enforce documented standards
4. **Continuous Learning** - Usage analytics improve prompt effectiveness

### Team Collaboration

- **Shared Knowledge Base** - Documentation accessible to all AI assistants
- **Standardized Practices** - Prompts ensure consistent code quality
- **Workflow Automation** - Custom prompts for team-specific processes

## 📊 Analytics & Monitoring

### Usage Tracking

- Prompt usage frequency and effectiveness scores
- Search query analytics and popular topics
- Document access patterns and relevance metrics

### Performance Metrics

- Indexing speed and document processing statistics
- Search response times and result quality
- Cache hit rates and memory usage

## 🐛 Troubleshooting

### Common Issues

#### Database Not Found

```
❌ Database not found. Tried locations: [...]
```

**Solution:** Run the server first to create the database:

```bash
python src/main.py
```

#### No Documents Indexed

**Check:**

- Verify `documentation_paths` in config include your docs
- Ensure files match `file_patterns`
- Check file permissions and accessibility

#### Search Returns No Results

**Check:**

- Try broader search terms
- Verify documents are properly indexed
- Check minimum query length (default: 2 characters)

#### GUI Won't Launch

**Check:**

- Tkinter installation: `pip install tk`
- Display environment for headless systems
- Database exists and is accessible

## 🤝 Contributing

### Adding Custom Prompts

1. Use `create_prompt` tool or add directly to database
2. Follow naming conventions and include comprehensive variables
3. Test effectiveness and gather usage feedback

### Extending Document Support

1. Add new file patterns to configuration
2. Implement custom parsers in the server code
3. Update metadata extraction logic

### GUI Enhancements

1. Modify `docs_db_viewer.py` for new features
2. Maintain thread safety with server integration
3. Follow existing UI patterns and styling

## 📋 Requirements

- **Python**: 3.8+
- **Dependencies**: See `requirements.txt`
- **Database**: SQLite (automatic)
- **GUI**: Tkinter (optional, for viewer)

### Core Dependencies

```
mcp>=0.1.0
PyYAML>=6.0
sentence-transformers>=2.2.2
jinja2>=3.1.0
fastapi>=0.95.0
uvicorn[standard]>=0.22.0
```

### GUI Dependencies (Optional)

```
tkinter  # Usually included with Python
```

## 📞 Support & Resources

- **Configuration Guide**: `config/server_config.yaml`
- **API Reference**: MCP tool and resource listings
- **GUI Documentation**: Run `python docs_db_viewer.py --help`
- **Default Prompts**: See prompt categories and examples above

## 🔄 Version History

- **v1.1.0**: Added Python source code indexing for shared utilities across services
  - Indexes Python files from service utils directories
  - Extracts classes, functions, and docstrings
  - Enables cross-service code reuse discovery
  - Enhanced search capabilities for shared functionality
  - Added `find_documents` tool for documentation-focused searches
- **v1.0.0**: Initial release with core documentation indexing and prompt management
- Comprehensive MCP integration with all major clients
- GUI database viewer for content exploration
- Advanced analytics and usage tracking

---

**Transform your AI-assisted development workflow** with intelligent documentation indexing and context-aware prompt management. The Documentation and Prompts MCP Server ensures consistent, high-quality development by making your project's knowledge and standards accessible to AI assistants.