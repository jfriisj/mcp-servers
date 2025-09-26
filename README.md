# MCP Servers

A comprehensive collection of Model Context Protocol (MCP) servers providing essential Python development tooling through standardized AI assistant integration.

## 🚀 Overview

This repository contains three specialized MCP servers that work together to provide a complete Python development toolchain:

- **Coverage Server** - Test coverage analysis and reporting
- **Docs-Prompts Server** - Documentation indexing and intelligent prompt management
- **Ruff Server** - Fast Python linting and code formatting

Together, these servers enable AI assistants to perform comprehensive code quality analysis, testing, documentation management, and code improvement tasks through the MCP protocol.

## 📦 Servers

### 🧪 Coverage Server

**Location:** `coverage-server/`

Provides comprehensive Python test coverage analysis using pytest-cov and coverage.py. Features include:

- **Integrated test execution** with coverage measurement
- **Multiple report formats** (HTML, XML, JSON, terminal)
- **Coverage threshold checking** and validation
- **Missing coverage identification** with specific line numbers
- **Branch coverage analysis** and parallel test execution
- **CI/CD integration** support for Jenkins, GitLab, and GitHub Actions

**Key Tools:**
- `run-tests-with-coverage` - Execute tests with coverage
- `generate-coverage-report` - Create coverage reports
- `check-coverage-threshold` - Validate coverage requirements
- `find-missing-coverage` - Identify uncovered code
- `coverage-summary` - Quick coverage overview

### 📚 Docs-Prompts Server

**Location:** `docs-prompts-server/`

Combines intelligent documentation indexing with advanced prompt management for context-aware development assistance.

**Features:**
- **Multi-format documentation indexing** (Markdown, reStructuredText, YAML, JSON)
- **Semantic search** across project documentation
- **Context-aware prompt system** with variable substitution
- **Architecture pattern detection** and analysis
- **Custom prompt creation** and management
- **Usage analytics** and prompt effectiveness tracking
- **GUI interface** for prompt and documentation management

**Key Tools:**
- `search_docs` - Search documentation with keywords
- `get_architecture_info` - Extract architecture patterns
- `search_prompts` - Find relevant prompts
- `get_prompt` - Retrieve specific prompts
- `create_prompt` - Add custom prompts
- `apply_prompt_with_context` - Use prompts with documentation context

### 🔍 Ruff Server

**Location:** `ruff-server/`

Provides fast Python linting and formatting capabilities using Ruff, the modern Python linter and formatter.

**Features:**
- **10-100x faster** than traditional linting tools
- **Black-compatible formatting** with check-only mode
- **Multiple output formats** (text, JSON, GitHub, GitLab, JUnit, SARIF)
- **Selective rule checking** and auto-fixing
- **Git integration** for checking only changed files
- **Rule explanations** and configuration display

**Key Tools:**
- `ruff-check` - Lint Python code
- `ruff-format` - Format Python code
- `ruff-check-diff` - Check only changed files
- `ruff-show-settings` - Display current configuration
- `ruff-explain-rule` - Explain specific linting rules

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
   # Coverage Server
   cd coverage-server
   pip install -r requirements.txt
   pip install pytest pytest-cov coverage pytest-xdist

   # Docs-Prompts Server
   cd ../docs-prompts-server
   pip install -r requirements.txt

   # Ruff Server
   cd ../ruff-server
   pip install -r requirements.txt
   pip install ruff
   ```

3. **Configure MCP client** (example for VS Code `.vscode/mcp.json`):

   ```json
   {
     "mcpServers": {
       "coverage": {
         "command": "python",
         "args": ["${workspaceFolder}/mcp-servers/coverage-server/src/coverage_mcp_server.py"],
         "cwd": "${workspaceFolder}"
       },
       "docs-prompts": {
         "command": "python",
         "args": ["${workspaceFolder}/mcp-servers/docs-prompts-server/src/docs_prompts_mcp_server.py"],
         "cwd": "${workspaceFolder}"
       },
       "ruff": {
         "command": "python",
         "args": ["${workspaceFolder}/mcp-servers/ruff-server/src/ruff_mcp_server.py"],
         "cwd": "${workspaceFolder}"
       }
     }
   }
   ```

## ⚙️ Configuration

### Coverage Server

Uses `pyproject.toml`, `pytest.ini`, or `setup.cfg` configuration. Example:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 80.0
```

### Docs-Prompts Server

Configuration in `docs-prompts-server/config/server_config.yaml`:

```yaml
documentation_paths:
  - "docs/"
  - "README.md"
  - "*.md"

file_patterns:
  - "*.md"
  - "*.rst"
  - "*.yaml"

architecture_keywords:
  - "architecture"
  - "design"
  - "pattern"
  - "api"
  - "service"
```

### Ruff Server

Uses `pyproject.toml` configuration:

```toml
[tool.ruff]
select = ["E", "F", "W"]
ignore = []
line-length = 88

[tool.ruff.isort]
known-first-party = ["my_package"]
```

## 📖 Usage Examples

### Running Tests with Coverage

```python
# Through MCP client
await call_tool("run-tests-with-coverage", {
    "test_path": "tests/",
    "source": "src/",
    "min_coverage": 85.0,
    "parallel": true
})
```

### Searching Documentation

```python
await call_tool("search_docs", {
    "query": "architecture patterns",
    "limit": 5
})
```

### Linting Code

```python
await call_tool("ruff-check", {
    "path": "src/",
    "fix": true,
    "format": "json"
})
```

### Getting Context-Aware Prompts

```python
await call_tool("suggest_prompts", {
    "context": "code review for security"
})
```

## 🔗 Integration

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "python-dev-tools": {
      "command": "python",
      "args": ["path/to/mcp-servers/coverage-server/src/coverage_mcp_server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "coverage": {
      "command": "python",
      "args": ["path/to/coverage_mcp_server.py"]
    }
  }
}
```

### CI/CD Integration

#### GitHub Actions
```yaml
- name: Run tests with coverage
  run: |
    python mcp-servers/coverage-server/src/coverage_mcp_server.py
    # Use MCP tools via CI integration

- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: test-reports/coverage.xml
```

#### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: Ruff Check
        entry: python mcp-servers/ruff-server/src/ruff_mcp_server.py --check
        language: system
        files: \.py$
```

## 🏗️ Development

### Running Individual Servers

```bash
# Coverage Server
cd coverage-server/src
python coverage_mcp_server.py

# Docs-Prompts Server
cd docs-prompts-server/src
python docs_prompts_mcp_server.py

# Ruff Server
cd ruff-server/src
python ruff_mcp_server.py
```

### Testing

Each server includes fallback mode for development without MCP:

```bash
# Test coverage server
python coverage-server/src/coverage_mcp_server.py --test

# Test docs-prompts server
python docs-prompts-server/src/docs_prompts_mcp_server.py --test
```

### Adding New Servers

1. Create new directory under project root
2. Implement MCP server following the pattern of existing servers
3. Add comprehensive README.md
4. Update main project README
5. Add to CI/CD configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Development Guidelines

- Follow existing code patterns and structure
- Include comprehensive documentation
- Add unit tests for new functionality
- Update README files for any changes
- Test with multiple MCP clients

## 📋 Requirements

### Coverage Server Dependencies

- pytest>=7.0.0
- pytest-cov>=4.0.0
- coverage>=7.0.0
- pytest-xdist>=3.0.0 (optional)

### Docs-Prompts Server Dependencies

- mcp>=0.1.0
- PyYAML>=6.0
- sentence-transformers>=2.2.2
- jinja2>=3.1.0
- fastapi>=0.95.0
- uvicorn>=0.22.0

### Ruff Server Dependencies

- ruff>=0.1.6

## 📄 License

This project is open source. See individual server directories for specific licensing information.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized AI assistant integration
- [pytest](https://pytest.org/) and [coverage.py](https://coverage.readthedocs.io/) for testing infrastructure
- [Ruff](https://github.com/astral-sh/ruff) for fast Python linting and formatting
- [Sentence Transformers](https://www.sbert.net/) for semantic search capabilities

---

**Note:** These servers are designed to work with MCP-compatible clients. Ensure your development environment supports the Model Context Protocol for full functionality.
