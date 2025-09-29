"""Handler for batch PDF conversion tool."""

from typing import Dict, Any
import logging
from .base_handler import PDFHandlerBase

logger = logging.getLogger(__name__)

class BatchConvertHandler(PDFHandlerBase):
    """Handler for batch converting multiple PDF files to markdown format."""
    
async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a batch PDF conversion request.
        
        Args:
            data: Dictionary containing input parameters:
                - input_dir: Directory containing PDF files
                - output_dir: Directory to save markdown files
                - recursive: Whether to process subdirectories (optional)
                - file_pattern: Pattern to match PDF files (optional)
                - preserve_images: Whether to extract images (optional)
                - parallel: Whether to use parallel processing (optional)
                - max_workers: Maximum number of worker threads (optional)
        
        Returns:
            Dictionary containing conversion results or error information
        """
        try:
            # Extract parameters
            input_dir = arguments['input_dir']
            output_dir = arguments['output_dir']
            recursive = arguments.get('recursive', False)
            file_pattern = arguments.get('file_pattern', '*.pdf')
            preserve_images = arguments.get('preserve_images', True)
            parallel = arguments.get('parallel', True)
            max_workers = arguments.get('max_workers', None)
            
            # Perform batch conversion
            result = self._batch_processor.convert_directory(
                input_dir=input_dir,
                output_dir=output_dir,
                recursive=recursive,
                file_pattern=file_pattern,
                preserve_images=preserve_images,
                parallel=parallel,
                max_workers=max_workers
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