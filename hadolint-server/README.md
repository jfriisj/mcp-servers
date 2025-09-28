# Hadolint MCP Server

A Model Context Protocol (MCP) server that provides Dockerfile linting capabilities using [Hadolint](https://github.com/hadolint/hadolint).

## Features

### 🔍 Dockerfile Linting
- **Comprehensive Dockerfile analysis** - Checks for best practices and common issues
- **Multiple output formats** - tty, JSON, SARIF
- **Configurable rules** - Ignore specific rules or use custom configurations
- **Directory scanning** - Lint all Dockerfiles in a project
- **Rule explanations** - Access to hadolint's built-in help

### 🎯 Best Practice Enforcement
- **Security checks** - Identify potential security vulnerabilities
- **Performance optimization** - Suggest performance improvements
- **Maintainability** - Enforce Dockerfile best practices
- **Compatibility** - Ensure cross-platform compatibility

### 🚀 Advanced Features
- **Recursive directory scanning** - Find all Dockerfiles in subdirectories
- **Custom configuration** - Use hadolint configuration files
- **Color output control** - Enable/disable colored terminal output
- **Verbose mode** - Detailed linting information

## Architecture

This server follows SOLID design principles with a modular architecture:

### Core Modules

- **`models.py`** - Data models and configuration classes using dataclasses
- **`hadolint_runner.py`** - Command execution and subprocess management
- **`mcp_handler.py`** - MCP protocol handling and tool definitions
- **`server.py`** - Main server orchestration and resource management
- **`main.py`** - Application entry point

### Design Principles

- **Single Responsibility** - Each module has one clear purpose
- **Open/Closed** - Components can be extended without modification
- **Liskov Substitution** - Consistent interfaces across components
- **Interface Segregation** - Focused interfaces for specific needs
- **Dependency Inversion** - Loose coupling through dependency injection

## Available Tools

### `hadolint-check`

Lint a Dockerfile using hadolint.

**Parameters:**

- `dockerfile_path` (string, required): Path to the Dockerfile to lint
- `config_file` (string, optional): Path to hadolint config file
- `ignore_rules` (array, optional): List of rules to ignore (e.g., ['DL3006', 'DL3018'])
- `format` (string, optional): Output format - tty, json, sarif (default: "tty")
- `no_color` (boolean, optional): Disable colored output (default: false)
- `verbose` (boolean, optional): Enable verbose output (default: false)

**Example usage:**

```json
{
  "dockerfile_path": "Dockerfile",
  "format": "json",
  "ignore_rules": ["DL3006"]
}
```

### `hadolint-check-dir`

Lint all Dockerfiles in a directory using hadolint.

**Parameters:**

- `directory_path` (string, optional): Path to directory containing Dockerfiles (default: ".")
- `config_file` (string, optional): Path to hadolint config file
- `ignore_rules` (array, optional): List of rules to ignore (e.g., ['DL3006', 'DL3018'])
- `format` (string, optional): Output format - tty, json, sarif (default: "tty")
- `recursive` (boolean, optional): Recursively search for Dockerfiles (default: true)
- `no_color` (boolean, optional): Disable colored output (default: false)
- `verbose` (boolean, optional): Enable verbose output (default: false)

**Example usage:**

```json
{
  "directory_path": "docker/",
  "recursive": true,
  "format": "sarif"
}
```

### `hadolint-show-rules`

Show available hadolint rules and help information.

**Parameters:**

- `show_all` (boolean, optional): Show detailed information about all rules (default: false)

## Installation

### Prerequisites

- Python 3.8+
- MCP client or compatible development environment

### Install Dependencies

```bash
cd mcp-servers/hadolint-server
pip install -r requirements.txt
```

The `requirements.txt` includes `hadolint-coatl` which provides the hadolint binary via pip, eliminating the need for manual installation.

## VS Code Configuration

### Add to `.vscode/mcp.json`

```json
{
  "servers": {
    "hadolint": {
      "command": "python",
      "args": [
        "hadolint-server/src/main.py"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

## Configuration

Hadolint supports configuration through `.hadolint.yaml` files. The server will automatically detect and use configuration files in:

1. Current directory
2. Parent directories (walking up the tree)

### Example .hadolint.yaml configuration

```yaml
ignored:
  - DL3006  # Image not pinned to a specific version
  - DL3018  # Pin versions in apk add

trustedRegistries:
  - docker.io
  - gcr.io
  - registry.gitlab.com

label-schema:
  - "org.label-schema.schema-version"
  - "org.label-schema.name"
  - "org.label-schema.description"
  - "org.label-schema.vendor"
  - "org.label-schema.version"

strict-labels: false
```

## Integration with Project

This server integrates seamlessly with containerized development workflows:

- **CI/CD pipelines** - Automated Dockerfile linting
- **Development workflow** - Pre-commit hooks and IDE integration
- **Security scanning** - Identify potential security issues
- **Performance optimization** - Suggest Dockerfile improvements

## Usage Examples

### Basic Dockerfile linting

```python
# Through MCP client
await call_tool("hadolint-check", {"dockerfile_path": "Dockerfile"})
```

### Directory scanning

```python
await call_tool("hadolint-check-dir", {"directory_path": ".", "recursive": true})
```

### Custom configuration

```python
await call_tool("hadolint-check", {
  "dockerfile_path": "Dockerfile",
  "config_file": ".hadolint.yaml",
  "format": "json"
})
```

### Ignore specific rules

```python
await call_tool("hadolint-check", {
  "dockerfile_path": "Dockerfile",
  "ignore_rules": ["DL3006", "DL3018"]
})
```

## Error Handling

The server includes comprehensive error handling:

- Graceful fallback when hadolint is not installed
- Clear error messages for missing Dockerfiles
- Proper handling of configuration file issues
- Timeout protection for long-running operations

## Development

### Running the Server

```bash
python src/main.py [project_root]
```

### Testing

The server includes fallback mode for development without the MCP package, making it easy to test and develop.

## Compatibility

- **Hadolint version**: Latest stable release
- **Python version**: 3.8+
- **MCP protocol**: 2024-11-05
- **Configuration**: .hadolint.yaml (Hadolint standard)

## Performance

Hadolint is designed for fast Dockerfile analysis:

- **Quick scanning** of individual Dockerfiles
- **Efficient directory traversal** for bulk operations
- **Parallel processing** capabilities
- **Minimal resource usage** for CI/CD integration

This makes it ideal for development workflows and automated pipelines.