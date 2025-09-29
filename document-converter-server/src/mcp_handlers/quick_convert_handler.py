"""Handler for quick PDF conversion tool."""

from typing import Dict, Any
import logging
from .base_handler import PDFHandlerBase

logger = logging.getLogger(__name__)

class QuickConvertHandler(PDFHandlerBase):
    """Handler for quick one-shot PDF conversion to markdown."""
    
async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a quick PDF conversion request.
        
        Args:
            data: Dictionary containing input parameters:
                - input_path: Path to input PDF file
                - output_path: Path for output markdown file (optional)
                - extract_images: Whether to extract images (optional)
        
        Returns:
            Dictionary containing conversion results or error information
        """
        try:
            # Extract parameters
            input_path = arguments['input_path']
            output_path = arguments.get('output_path')
            extract_images = arguments.get('extract_images', False)
            
            # Perform quick conversion
            result = self._batch_processor.quick_convert(
                input_path=input_path,
                output_path=output_path,
                extract_images=extract_images
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