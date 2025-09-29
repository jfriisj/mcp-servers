"""
Content Organization MCP Server implementation.
"""

from mcp.server.stdio import MCPServer
from .mcp_handler import ContentOrganizationMCPHandler

class ContentOrganizationServer(MCPServer):
    """MCP server for content organization operations."""
    
    def __init__(self):
        super().__init__(ContentOrganizationMCPHandler())

def main():
    """Run the content organization MCP server."""
    server = ContentOrganizationServer()
    server.start()

if __name__ == '__main__':
    main()