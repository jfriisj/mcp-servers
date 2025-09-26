# Ruff MCP Server

A Model Context Protocol (MCP) server that provides fast Python linting and formatting capabilities using [Ruff](https://github.com/astral-sh/ruff).

## Features

### 🔍 Linting Capabilities
- **Fast Python linting** - Ruff is 10-100x faster than traditional tools
- **Multiple output formats** - Text, JSON, GitHub, GitLab, JUnit, SARIF
- **Selective rule checking** - Choose specific rule categories to check
- **Auto-fixing** - Automatically fix issues where possible
- **Show available fixes** - See what fixes are available for each issue

### 🎨 Formatting Capabilities  
- **Black-compatible formatting** - Drop-in replacement for Black
- **Check-only mode** - Verify formatting without making changes
- **Diff view** - See exactly what would be changed
- **Fast execution** - Significantly faster than Black

### 🚀 Advanced Features
- **Git integration** - Check only changed files (git diff)
- **Configuration display** - Show active Ruff settings
- **Rule explanation** - Get detailed explanations of specific rules
- **Project-aware** - Automatically finds and uses pyproject.toml configuration

## Available Tools

### `ruff-check`
Run Ruff linter to identify code issues.

**Parameters:**
- `path` (string, optional): Path to check (file or directory, default: ".")
- `fix` (boolean, optional): Automatically fix issues where possible (default: false)
- `format` (string, optional): Output format - text, json, github, gitlab, junit, sarif (default: "text")
- `select` (string, optional): Comma-separated list of rule codes to select (e.g., 'E,W,F')
- `ignore` (string, optional): Comma-separated list of rule codes to ignore
- `show_fixes` (boolean, optional): Show available fixes for issues (default: false)

**Example usage:**
```json
{
  "path": "src/",
  "fix": true,
  "format": "json",
  "select": "E,W,F"
}
```

### `ruff-format`
Format Python code using Ruff (Black-compatible).

**Parameters:**
- `path` (string, optional): Path to format (file or directory, default: ".")
- `check` (boolean, optional): Only check formatting without making changes (default: false)
- `diff` (boolean, optional): Show diff of formatting changes (default: false)

**Example usage:**
```json
{
  "path": "src/main.py",
  "diff": true
}
```

### `ruff-check-diff`
Check Ruff issues on changed files only (git diff).

**Parameters:**
- `base` (string, optional): Base commit/branch to compare against (default: "HEAD~1")
- `format` (string, optional): Output format - text, json, github (default: "text")

**Example usage:**
```json
{
  "base": "main",
  "format": "github"
}
```

### `ruff-show-settings`
Show active Ruff configuration settings.

**Parameters:**
- `path` (string, optional): Path to show settings for (default: ".")

### `ruff-explain-rule`
Explain a specific Ruff rule.

**Parameters:**
- `rule` (string, required): Rule code to explain (e.g., 'E501', 'F401')

**Example usage:**
```json
{
  "rule": "E501"
}
```

## Installation

### Prerequisites
- Python 3.8+
- Ruff (`pip install ruff`)
- MCP client or compatible development environment

### Install Dependencies
```bash
cd mcp-servers/ruff-server
pip install -r requirements.txt
```

### Install Ruff
```bash
pip install ruff
```

## Configuration

The server automatically detects and uses `pyproject.toml` configuration files. It searches for configuration in:
1. Current directory
2. Parent directories (walking up the tree)

### Example pyproject.toml configuration:
```toml
[tool.ruff]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F"]
ignore = []

# Allow autofix for all enabled rules (when `--fix`) is provided.
fixable = ["A", "B", "C", "D", "E", "F", "G", "I", "N", "Q", "S", "T", "W", "ANN", "ARG", "BLE", "COM", "DJ", "DTZ", "EM", "ERA", "EXE", "FBT", "ICN", "INP", "ISC", "NPY", "PD", "PGH", "PIE", "PL", "PT", "PTH", "PYI", "RET", "RSE", "RUF", "SIM", "SLF", "TCH", "TID", "TRY", "UP", "YTT"]
unfixable = []

# Exclude a variety of commonly ignored directories.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]

# Same as Black.
line-length = 88

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

# Assume Python 3.10.
target-version = "py310"

[tool.ruff.mccabe]
# Unlike Flake8, default to a complexity level of 10.
max-complexity = 10
```

## Integration with Project

This server is designed to integrate with the existing afhandling project structure:
- Uses the project's `pyproject.toml` configuration
- Compatible with existing development workflow
- Provides faster alternative to Black and Flake8
- Supports all standard Ruff rule categories and plugins

## Usage Examples

### Basic linting:
```python
# Through MCP client
await call_tool("ruff-check", {"path": "src/"})
```

### Format with diff:
```python
await call_tool("ruff-format", {"path": ".", "diff": True})
```

### Check only changed files:
```python
await call_tool("ruff-check-diff", {"base": "main"})
```

### Auto-fix issues:
```python
await call_tool("ruff-check", {"path": "src/", "fix": True})
```

## Error Handling

The server includes comprehensive error handling:
- Graceful fallback when Ruff is not installed
- Clear error messages for configuration issues
- Proper handling of git operations for diff mode
- Timeout protection for long-running operations

## Development

### Running the Server
```bash
python src/ruff_mcp_server.py [project_root]
```

### Testing
The server includes fallback mode for development without the MCP package, making it easy to test and develop.

## Compatibility

- **Ruff version**: 0.1.6 or later
- **Python version**: 3.8+
- **MCP protocol**: 2024-11-05
- **Configuration**: pyproject.toml (Ruff standard)

## Performance

Ruff provides significant performance improvements:
- **10-100x faster** than traditional linting tools
- **Faster formatting** than Black
- **Parallel processing** of multiple files
- **Incremental checking** for git diff mode

This makes it ideal for large codebases and continuous integration workflows.