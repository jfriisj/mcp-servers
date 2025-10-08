# Import Test MCP Server - Docker Usage

This document explains how to use the Import Test MCP Server via Docker.

> **Note**: Replace `import-test-server` with `ghcr.io/jfriisj/import-test-mcp-server:latest` if using a published image from the registry. For local development, build the image first with `docker build -t import-test-server .`

## 🚀 Quick Start

### 1. Basic Analysis (Test Mode)

```bash
# Test the server on your Python project
docker run --rm -v /path/to/your/python/project:/workspace \
  import-test-server --test
```

### 2. MCP Server Mode

```bash
# Run as MCP server (for integration with MCP clients)
docker run -i -v /path/to/your/python/project:/workspace \
  import-test-server
```

### 3. Generate Report

```bash
# Generate comprehensive report to output directory
docker run --rm \
  -v /path/to/your/python/project:/workspace \
  -v /path/to/output:/output \
  import-test-server --generate-report
```

### 4. Quick Check

```bash
# Run quick import validation
docker run --rm -v /path/to/your/python/project:/workspace \
  ghcr.io/jfriisj/import-test-mcp-server --quick-check
```

## 🛠️ Usage Examples

### Analyze the Solid Server

```bash
# Clone the repo and test the solid-server
git clone https://github.com/jfriisj/mcp-servers.git
cd mcp-servers

# Analyze solid-server with import-test
docker run --rm -v $(pwd)/solid-server:/workspace \
  ghcr.io/jfriisj/import-test-mcp-server --test
```

### Analyze Your Own Project

```bash
# Replace /path/to/your/project with actual path
docker run --rm -v /path/to/your/project:/workspace \
  ghcr.io/jfriisj/import-test-mcp-server --test
```

### Generate Reports with Custom Settings

```bash
# Generate report with custom settings
docker run --rm \
  -v /path/to/your/project:/workspace \
  -v /path/to/output:/output \
  -e IMPORT_TEST_MAX_FILES=200 \
  -e IMPORT_TEST_INCLUDE_TESTS=false \
  ghcr.io/jfriisj/import-test-mcp-server --generate-report
```

## 📊 Docker Compose Usage

### Using the Included docker-compose.yml

```bash
# Copy your project to test-project directory
cp -r /path/to/your/python/project ./test-project

# Run default analysis
docker-compose up import-test-server

# Run quick check
docker-compose --profile quick up import-test-quick

# Generate report
docker-compose --profile report up import-test-report
```

### Custom docker-compose.yml

```yaml
version: '3.8'
services:
  import-test:
    image: ghcr.io/jfriisj/import-test-mcp-server
    volumes:
      - ./my-python-project:/workspace:ro
      - ./reports:/output
    environment:
      - IMPORT_TEST_MAX_FILES=100
    command: ["--test"]
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMPORT_TEST_PROJECT_ROOT` | `/workspace` | Root directory to analyze |
| `IMPORT_TEST_OUTPUT_DIR` | `/output` | Output directory for reports |
| `IMPORT_TEST_MAX_FILES` | `100` | Maximum files to analyze |
| `IMPORT_TEST_INCLUDE_TESTS` | `true` | Include test files in analysis |

### Volume Mounts

| Path | Purpose | Required |
|------|---------|----------|
| `/workspace` | Your Python project to analyze | Yes |
| `/output` | Generated reports and summaries | Optional |

## 📋 Command Line Options

| Option | Description |
|--------|-------------|
| `--test` | Run in test mode with sample analysis |
| `--generate-report` | Generate comprehensive report and exit |
| `--quick-check` | Run quick validation and exit |
| `--project-root PATH` | Set project root (default: /workspace) |
| `--help` | Show usage information |

## 🐳 Integration with MCP Clients

### VS Code Integration

Add to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "import-test-docker": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "${workspaceFolder}:/workspace",
        "ghcr.io/jfriisj/import-test-mcp-server"
      ]
    }
  }
}
```

### Claude Desktop Integration

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "import-test-docker": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/your/project:/workspace",
        "ghcr.io/jfriisj/import-test-mcp-server"
      ]
    }
  }
}
```

## 🔍 Available Analysis Tools

When running as MCP server, these tools are available:

| Tool | Description |
|------|-------------|
| `import-test-analyze-file` | Analyze imports in single Python file |
| `import-test-analyze-project` | Analyze entire project imports |
| `import-test-circular-imports` | Detect circular import dependencies |
| `import-test-validate-dependencies` | Check missing/unused packages |
| `import-test-unused-imports` | Find unused imports |
| `import-test-get-stats` | Get comprehensive statistics |

## 🏗️ Building Locally

```bash
# Clone repository
git clone https://github.com/jfriisj/mcp-servers.git
cd mcp-servers/import-test-server

# Build Docker image
docker build -t import-test-mcp-server .

# Test local build
docker run --rm -v $(pwd):/workspace import-test-mcp-server --test
```

## 🐛 Troubleshooting

### Common Issues

1. **No Python files found**
   ```bash
   # Make sure you're mounting the right directory
   docker run --rm -v $(pwd):/workspace import-test-mcp-server --test
   ```

2. **Permission denied**
   ```bash
   # Ensure the mounted directory is readable
   chmod -R +r /path/to/your/project
   ```

3. **Container exits immediately**
   ```bash
   # Check if directory exists and has Python files
   ls -la /path/to/your/project/*.py
   ```

### Debug Mode

```bash
# Run with interactive shell for debugging
docker run -it --rm -v /path/to/your/project:/workspace \
  ghcr.io/jfriisj/import-test-mcp-server bash

# Inside container, run manually
python src/main.py --test --project-root /workspace
```

## 📈 Performance Notes

- The container analyzes up to 100 files by default (configurable)
- Analysis typically takes 1-10 seconds depending on project size
- Memory usage scales with project complexity
- Use `IMPORT_TEST_MAX_FILES` to limit analysis scope for large projects

## 🔐 Security

- Runs as non-root user (`importuser`)
- Read-only access to source code (recommended)
- No network access required for basic analysis
- Isolated container environment