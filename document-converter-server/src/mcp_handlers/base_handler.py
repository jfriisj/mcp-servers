"""Base handler for PDF conversion tools."""

from typing import Dict, Any
from mcp_base.mcp_handler import MCPHandler
from ..core.converter_utils import ConversionError, InvalidPDFError, FileNotFoundError
from ..core.pdf_converter import PDFConverter
from ..core.batch_processor import BatchProcessor

class PDFHandlerBase(MCPHandler):
    """Base handler class for PDF conversion tools."""
    
    def __init__(self):
        super().__init__()
        self._converter = PDFConverter()
        self._batch_processor = BatchProcessor()
    
    def _handle_conversion_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle conversion errors and return appropriate error responses.
        
        Args:
            error: The exception that occurred
        
        Returns:
            Error response dictionary
        """
        if isinstance(error, InvalidPDFError):
            return {
                'success': False,
                'error_code': 'INVALID_PDF',
                'error_message': str(error)
            }
        elif isinstance(error, FileNotFoundError):
            return {
                'success': False,
                'error_code': 'FILE_NOT_FOUND',
                'error_message': str(error)
            }
        elif isinstance(error, PermissionError):
            return {
                'success': False,
                'error_code': 'PERMISSION_DENIED',
                'error_message': str(error)
            }
        elif isinstance(error, ConversionError):
            return {
                'success': False,
                'error_code': 'CONVERSION_ERROR',
                'error_message': str(error)
            }
        else:
            return {
                'success': False,
                'error_code': 'UNKNOWN_ERROR',
                'error_message': f"An unexpected error occurred: {str(error)}"
            }