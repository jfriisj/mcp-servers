"""Document Converter Server for MCP."""

import logging.config
import os
import asyncio
from src.core import BatchProcessor, PDFConverter
from src.mcp_handlers import PDFToMarkdownHandler, BatchConvertHandler, QuickConvertHandler

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'server.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

logger = logging.getLogger(__name__)

class DocumentConverterServer(MCPServer):
    """MCP server for document conversion operations."""
    
    def __init__(self):
        """Initialize the document converter server."""
        super().__init__()
        
        # Register tool handlers
        self.register_tool('pdf_to_markdown', PDFToMarkdownHandler())
        self.register_tool('batch_convert', BatchConvertHandler())
        self.register_tool('quick_convert', QuickConvertHandler())
        
        # Load tool schemas
        schema_path = os.path.join(os.path.dirname(__file__), 'tools_schemas.yaml')
        self.load_tool_schemas(schema_path)
        
        logger.info("Document Converter Server initialized successfully")

if __name__ == '__main__':
    try:
        server = DocumentConverterServer()
        asyncio.run(server.serve())
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise
