"""
Document Conversion MCP Server implementation.
"""

from mcp.server.stdio import MCPServer
from .mcp_handler import DocumentConversionMCPHandler

class DocumentConversionServer(MCPServer):
    """MCP server for document conversion operations."""
    
    def __init__(self):
        super().__init__(DocumentConversionMCPHandler())

def main():
    """Run the document conversion MCP server."""
    server = DocumentConversionServer()
    server.start()

if __name__ == '__main__':
    main()