# Do## 🚀 Overview

The Documentation and Prompts MCP Server transforms how AI assistants interact with your codebase by providing:

- **📚 Smart Documentation Indexing** - Automatically indexes and searches your project's documentation with configurable root folder support
- **🎯 Intelligent Prompt Management** - Context-aware prompts that automatically incorporate relevant documentation
- **🔗 Seamless Integration** - Documentation informs prompts, prompts reference documentation
- **⚡ Real-time GUI Viewer** - Visual interface for exploring indexed content and managing prompts
- **📊 Analytics & Insights** - Usage tracking and effectiveness metrics for continuous improvementon and Prompts MCP Server

A comprehensive Model Context Protocol (MCP) server that combines intelligent documentation indexing with advanced prompt management, enabling AI assistants to understand project architecture and apply context-aware prompts for consistent, high-quality development.

## 🚀 Overview

The Documentation and Prompts MCP Server transforms how AI assistants interact with your codebase by providing:

- **📚 Smart Documentation Indexing** - Automatically indexes and searches your project's documentation
- **🎯 Intelligent Prompt Management** - Context-aware prompts that reference your specific documentation
- **🔗 Seamless Integration** - Documentation informs prompts, prompts reference documentation
- **⚡ Real-time GUI Viewer** - Visual interface for exploring indexed content and managing prompts
- **📊 Analytics & Insights** - Usage tracking and effectiveness metrics for continuous improvement

## ✨ Key Features

### **📖 Advanced Documentation Analysis**

- **Multi-format support**: Markdown, reStructuredText, YAML, JSON schemas
- **Semantic search** with keyword matching for contextual understanding
- **Architecture pattern detection** using configurable keyword analysis
- **Incremental indexing** with change detection and automatic updates
- **Cross-reference mapping** between related documents and sections
- **Metadata extraction** including file size, line counts, and structure analysis

### **🎯 Intelligent Prompt System**

- **Context-aware prompts** that automatically incorporate relevant documentation
- **Template-based prompts** with dynamic variable substitution from your docs
- **Categorized prompt library** with 8 predefined categories (code-quality, architecture, documentation, testing, refactoring, api, security, custom)
- **Usage tracking and analytics** to measure prompt effectiveness
- **Custom prompt creation** with full versioning and management
- **Smart suggestions** based on task context and documentation patterns

### **🖥️ GUI Database Viewer**

- **Real-time database exploration** of indexed documents and prompts
- **Interactive search and filtering** across all content
- **Prompt usage analytics** with charts and statistics
- **Document structure visualization** showing sections and metadata
- **Live server integration** for immediate content updates

### **🔧 Enterprise-Grade Architecture**

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

### **Prerequisites**

- Python 3.8+
- MCP-compatible client (VS Code with MCP extension, Claude Desktop, etc.)

### **1. Install Dependencies**

```bash
cd docs-prompts-server
pip install -r requirements.txt
```

### **2. Configure the Server**

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

### **3. Add to MCP Configuration**

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

### **4. Command Line Options**

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

### **5. Launch GUI Viewer (Optional)**

### **4. Launch GUI Viewer (Optional)**

```bash
cd docs-prompts-server/src
python docs_db_viewer.py --gui
```

## ⚙️ Configuration

### **Core Settings**

| Setting | Description | Default |
|---------|-------------|---------|
| `documentation_paths` | Paths to scan for documentation | `["docs/", "README.md", "*.md"]` |
| `file_patterns` | File extensions to index | `["*.md", "*.rst", "*.yaml", "*.json"]` |
| `exclude_patterns` | Paths to skip during indexing | `["node_modules/", ".git/"]` |
| `max_file_size_mb` | Maximum file size to index | `10` |
| `architecture_keywords` | Keywords for architecture detection | See config file |

### **Root Folder Configuration**

The server can be configured to index documentation from a specific root folder using either:

1. **Command line argument**: `--root-folder /path/to/project`
2. **Environment variable**: `DOCS_PROJECT_ROOT=/path/to/project`
3. **MCP server configuration**: Pass `--root-folder ${workspaceFolder}` in the args array

When no root folder is specified, the server defaults to the current working directory.

### **Performance Tuning**

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

### **Prompt Management**

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

### **📖 Documentation Tools**

#### `search_docs`

Search documentation using keywords or phrases.

**Parameters:**

```json
{
  "query": "architecture patterns",
  "doc_type": ".md",
  "limit": 10
}
```

**Example:**

```python
await call_tool("search_docs", {
    "query": "microservice architecture",
    "limit": 5
})
```

#### `get_architecture_info`

Extract architecture patterns and design information from indexed documentation.

**Returns:** Summary of architecture-related documents with content snippets.

#### `index_documentation`

Re-index all documentation files or force a complete rebuild.

**Parameters:**

```json
{
  "force": false
}
```

### **🎯 Prompt Management Tools**

#### `search_prompts`

Search prompts by name, description, category, or tags.

**Parameters:**

```json
{
  "query": "code review",
  "category": "code-quality",
  "limit": 10
}
```

#### `get_prompt`

Retrieve a specific prompt with full details and variable information.

**Parameters:**

```json
{
  "prompt_id": "code_review"
}
```

#### `suggest_prompts`

Get context-aware prompt suggestions based on task description.

**Parameters:**

```json
{
  "context": "security code review"
}
```

#### `create_prompt`

Create a new custom prompt in the library.

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

### **🔗 Integration Tools**

#### `generate_contextual_prompt`

Generate a prompt automatically from relevant documentation context.

**Parameters:**

```json
{
  "task": "API development",
  "docs_query": "rest api patterns"
}
```

#### `apply_prompt_with_context`

Apply a prompt with automatic context filling from documentation.

**Parameters:**

```json
{
  "prompt_id": "architecture_review",
  "content": "code to review",
  "auto_fill_context": true
}
```

## 🎯 Default Prompt Categories

The server includes 8 predefined prompt categories:

### **🔍 Code Quality**

- Comprehensive Code Review
- Code standards validation
- Best practices enforcement

### **🏗️ Architecture**

- Architecture Compliance Check
- Design pattern validation
- System integration verification

### **📚 Documentation**

- API Documentation Generator
- Code documentation assistance
- README and guide creation

### **🧪 Testing**

- Test Strategy and Generation
- Test coverage analysis
- Quality assurance prompts

### **🔧 Refactoring**

- Code Refactoring Recommendations
- Performance optimization
- Maintainability improvements

### **🔌 API**

- API design validation
- Endpoint documentation
- Integration guidelines

### **🔒 Security**

- Security Vulnerability Assessment
- Threat model analysis
- Compliance checking

### **⚙️ Custom**

- Project-specific prompts
- Team workflow automation
- Domain-specific guidance

## 🖥️ GUI Database Viewer

Launch the interactive GUI to explore indexed content:

```bash
cd docs-prompts-server/src
python docs_db_viewer.py --gui
```

### **Features:**

- **📊 Database Statistics** - Overview of indexed documents and prompts
- **🔍 Document Explorer** - Browse all indexed documentation with metadata
- **🎯 Prompt Library** - View and manage all available prompts
- **📈 Usage Analytics** - Charts showing prompt effectiveness and usage patterns
- **🔎 Live Search** - Real-time search across all content
- **📋 Content Preview** - Full document and prompt content viewing

## 📖 Usage Examples

### **Basic Documentation Search**

```python
# Search for architecture documentation
results = await call_tool("search_docs", {
    "query": "architecture patterns",
    "limit": 5
})
```

### **Context-Aware Code Review**

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

### **Generate Documentation**

```python
# Create API docs based on existing patterns
prompt = await call_tool("generate_contextual_prompt", {
    "task": "API documentation",
    "docs_query": "api patterns"
})
```

### **Custom Prompt Creation**

```python
# Add project-specific prompt
await call_tool("create_prompt", {
    "name": "Team Code Standards",
    "description": "Enforce team-specific coding standards",
    "template": "Review against our standards: {team_standards}\n\nCode: {code_content}",
    "category": "custom",
    "variables": ["team_standards", "code_content"]
})
```

## 🔄 Workflow Integration

### **Development Workflow**

1. **Index Documentation** - Server automatically indexes project docs on startup
2. **Context-Aware Assistance** - AI gets relevant docs for each task
3. **Consistent Quality** - Prompts enforce documented standards
4. **Continuous Learning** - Usage analytics improve prompt effectiveness

### **Team Collaboration**

- **Shared Knowledge Base** - Documentation accessible to all AI assistants
- **Standardized Practices** - Prompts ensure consistent code quality
- **Workflow Automation** - Custom prompts for team-specific processes

## 📊 Analytics & Monitoring

### **Usage Tracking**

- Prompt usage frequency and effectiveness scores
- Search query analytics and popular topics
- Document access patterns and relevance metrics

### **Performance Metrics**

- Indexing speed and document processing statistics
- Search response times and result quality
- Cache hit rates and memory usage

## 🐛 Troubleshooting

### **Common Issues**

#### **Database Not Found**

```
❌ Database not found. Tried locations: [...]
```

**Solution:** Run the server first to create the database:

```bash
python src/main.py
```

#### **No Documents Indexed**

**Check:**
- Verify `documentation_paths` in config include your docs
- Ensure files match `file_patterns`
- Check file permissions and accessibility

#### **Search Returns No Results**

**Check:**
- Try broader search terms
- Verify documents are properly indexed
- Check minimum query length (default: 2 characters)

#### **GUI Won't Launch**

**Check:**
- Tkinter installation: `pip install tk`
- Display environment for headless systems
- Database exists and is accessible

### **Performance Tuning**

#### **Large Codebases**
```yaml
indexing:
  batch_size: 50  # Reduce for memory constraints
  cache_search_results: true
  max_cache_size: 500

search:
  default_limit: 5  # Reduce default results
```

#### **Slow Searches**
- Enable `cache_search_results`
- Increase `max_cache_size`
- Use more specific search queries

## 🤝 Contributing

### **Adding Custom Prompts**
1. Use `create_prompt` tool or add directly to database
2. Follow naming conventions and include comprehensive variables
3. Test effectiveness and gather usage feedback

### **Extending Document Support**
1. Add new file patterns to configuration
2. Implement custom parsers in the server code
3. Update metadata extraction logic

### **GUI Enhancements**
1. Modify `docs_db_viewer.py` for new features
2. Maintain thread safety with server integration
3. Follow existing UI patterns and styling

## 📋 Requirements

- **Python**: 3.8+
- **Dependencies**: See `requirements.txt`
- **Database**: SQLite (automatic)
- **GUI**: Tkinter (optional, for viewer)

### **Core Dependencies**
```
mcp>=0.1.0
PyYAML>=6.0
sentence-transformers>=2.2.2
jinja2>=3.1.0
fastapi>=0.95.0
uvicorn[standard]>=0.22.0
```

### **GUI Dependencies** (Optional)
```
tkinter  # Usually included with Python
```

## 📞 Support & Resources

- **Configuration Guide**: `config/server_config.yaml`
- **API Reference**: MCP tool and resource listings
- **GUI Documentation**: Run `python docs_db_viewer.py --help`
- **Default Prompts**: See prompt categories and examples above

## 🔄 Version History

- **v1.0.0**: Initial release with core documentation indexing and prompt management
- Comprehensive MCP integration with all major clients
- GUI database viewer for content exploration
- Advanced analytics and usage tracking

---

**Transform your AI-assisted development workflow** with intelligent documentation indexing and context-aware prompt management. The Documentation and Prompts MCP Server ensures consistent, high-quality development by making your project's knowledge and standards accessible to AI assistants.