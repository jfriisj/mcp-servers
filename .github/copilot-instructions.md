# MCP Servers - AI Coding Guidelines

## Architecture Overview

This repository contains three specialized MCP (Model Context Protocol) servers providing Python development tooling:

- **Coverage Server** (`coverage-server/`) - Test coverage analysis using pytest-cov
- **Docs-Prompts Server** (`docs-prompts-server/`) - Documentation indexing and intelligent prompt management  
- **Ruff Server** (`ruff-server/`) - Fast Python linting and formatting using Ruff

Each server follows a consistent architecture:
- `src/main.py` - Entry point with asyncio server setup
- `src/server.py` - Main MCP server class with resource/tool handlers
- `src/mcp_handler.py` - Tool definitions and MCP protocol handling
- `src/models.py` - Data structures using Python dataclasses
- `requirements.txt` - Server-specific dependencies

## Key Patterns & Conventions

### MCP Server Structure
```python
# Server initialization pattern (from coverage-server/src/server.py)
class CoverageMCPServer:
    def __init__(self, project_root: Optional[Path] = None):
        self.server = Server("coverage-mcp-server")
        # Initialize components...
        
    async def serve(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools():
            return self.mcp_handler.get_tools()
```

### Tool Definition Pattern
```python
# Tool schema definition (from coverage-server/src/mcp_handler.py)
Tool(
    name="run-tests-with-coverage",
    description="Run tests with coverage measurement using pytest-cov",
    inputSchema={
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "default": "tests/"},
            "min_coverage": {"type": "number", "default": 80.0},
        }
    }
)
```

### Error Handling & Response Format
```python
# Consistent error handling with emoji prefixes
try:
    # tool implementation
    return [TextContent(type="text", text="✅ Success message")]
except Exception as e:
    return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
```

### Configuration Integration
- VS Code: Configure servers in `.vscode/mcp.json`
- Claude Desktop: Add to `claude_desktop_config.json`
- Each server supports `--root-folder` parameter for workspace root

## Development Workflows

### Adding a New Server
1. Create `{server-name}-server/` directory
2. Implement standard file structure (`src/main.py`, `server.py`, etc.)
3. Add `requirements.txt` with dependencies
4. Update main `README.md` and `.vscode/mcp.json`
5. Include fallback mode for development without MCP package

### Testing Servers
Each server supports fallback mode for testing:
```bash
cd {server-name}-server/src
python main.py --test  # If supported
```

### Running Individual Servers
```bash
# From project root
python {server-name}-server/src/main.py
```

## Integration Points

### External Tool Dependencies
- **pytest + pytest-cov** - Test execution and coverage (coverage-server)
- **ruff** - Fast linting/formatting (ruff-server)  
- **sentence-transformers** - Semantic search (docs-prompts-server)
- **gitpython** - Git operations for diff analysis

### CI/CD Integration
- GitHub Actions examples in main README
- Pre-commit hooks for linting
- Coverage reporting to external services

## Code Quality Standards

### Import Organization
- Standard library imports first
- Third-party imports second  
- Local imports last
- Use absolute imports within server packages

### Async/Await Patterns
- All MCP handlers are async
- Use `asyncio.create_subprocess_exec` for external commands
- Proper error handling in async contexts

### Configuration Management
- Use `pyproject.toml` for tool configuration (ruff, coverage)
- YAML config files for server-specific settings
- Environment variable support where needed

## Common Gotchas

- **MCP Package Availability**: Servers include fallback implementations for development
- **Path Handling**: Use absolute paths for cross-platform compatibility
- **Process Execution**: Always handle stdout/stderr from subprocess calls
- **Configuration Discovery**: Servers auto-discover config files (pyproject.toml, etc.)

## Key Files to Reference

- `.vscode/mcp.json` - Server configuration for VS Code
- `coverage-server/src/mcp_handler.py` - Tool definition patterns
- `ruff-server/src/ruff_mcp_server.py` - Single-file server example  
- `docs-prompts-server/config/server_config.yaml` - Configuration structure