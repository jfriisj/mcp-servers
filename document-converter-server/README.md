# MCP Server Base Template

Base template for creating Model Context Protocol (MCP) servers that communicate via stdio.

## Directory Structure

```
base-server-template/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── mcp_handler.py     # Tool and resource handlers
│   ├── core/             # Core functionality modules
│   │   └── __init__.py
│   └── models.py         # Data models
├── tools/
│   └── tools_schemas.yaml # Tool definitions
├── config/
│   └── server_config.yaml # Server configuration
└── tests/                # Unit and integration tests
```

## Getting Started

1. Copy this template to create a new MCP server
2. Modify tools_schemas.yaml to define your tools
3. Implement tool handlers in mcp_handler.py
4. Add core functionality in src/core/
5. Configure server settings in config/server_config.yaml

## Development

Each MCP server should:
1. Use stdio communication only (no HTTP)
2. Define tools in YAML schemas
3. Handle errors consistently
4. Follow the MCP protocol specification

## Testing

```bash
cd base-server-template
python -m pytest tests/
```