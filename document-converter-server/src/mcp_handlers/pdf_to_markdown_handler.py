"""Handler for PDF to Markdown conversion tool."""

from typing import Dict, Any
import logging
from .base_handler import PDFHandlerBase

logger = logging.getLogger(__name__)

class PDFToMarkdownHandler(PDFHandlerBase):
    """Handler for converting PDF files to markdown format."""
    
async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a PDF to markdown conversion request.
        
        Args:
            data: Dictionary containing input parameters:
                - input_path: Path to input PDF file
                - output_path: Path for output markdown file
                - preserve_images: Whether to extract images (optional)
                - image_dir: Directory for extracted images (optional)
                - table_format: Format for tables (optional)
        
        Returns:
            Dictionary containing conversion results or error information
        """
        try:
            # Extract parameters
            input_path = arguments['input_path']
            output_path = arguments['output_path']
            preserve_images = arguments.get('preserve_images', True)
            image_dir = arguments.get('image_dir', 'images')
            table_format = arguments.get('table_format', 'pipe')
            
            # Validate table format
            if table_format not in ['grid', 'pipe', 'simple']:
                return {
                    'success': False,
                    'error_code': 'INVALID_PARAMETER',
                    'error_message': f"Invalid table format: {table_format}"
                }
            
            # Perform conversion
            result = self._converter.convert_pdf_to_markdown(
                input_path=input_path,
                output_path=output_path,
                preserve_images=preserve_images,
                image_dir=image_dir,
                table_format=table_format
            )
            
            return result
            
        except KeyError as e:
            return {
                'success': False,
                'error_code': 'MISSING_PARAMETER',
                'error_message': f"Missing required parameter: {str(e)}"
            }
        except Exception as e:
            return self._handle_conversion_error(e)