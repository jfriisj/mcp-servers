"""
Handlers package for Study Buddy MCP Server.

This package contains the external interface layer (Layer 1) of Clean Architecture,
providing protocol-specific handlers that translate external requests to service calls.

Clean Architecture Layer 1: External Interface
- MCP protocol handlers
- Request/response translation
- Error formatting and protocol compliance
- Parameter validation and sanitization
"""

from .mcp_handler import MCPHandler

__all__ = [
    "MCPHandler",
]
