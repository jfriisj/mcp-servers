"""Batch processing functionality for PDF conversions."""

import os
from typing import List, Dict, Any, Optional
import logging
from .converter_utils import (
    find_pdf_files,
    process_with_threadpool,
    get_default_output_path,
)
from .pdf_converter import PDFConverter

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing of multiple PDF files."""
    
    def __init__(self):
        self.converter = PDFConverter()
    
    def convert_directory(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = False,
        file_pattern: str = "*.pdf",
        preserve_images: bool = True,
        parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convert all PDF files in a directory to markdown.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save markdown files
            recursive: Whether to process subdirectories
            file_pattern: Pattern to match PDF files
            preserve_images: Whether to extract images
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker threads
        
        Returns:
            Dictionary containing conversion results
        
        Raises:
            FileNotFoundError: If input directory doesn't exist
        """
        # Find all PDF files
        pdf_files = find_pdf_files(input_dir, recursive, file_pattern)
        if not pdf_files:
            return {
                'success': True,
                'files_processed': 0,
                'results': []
            }
        
        # Prepare conversion parameters
        conversion_results = []
        
        def process_file(pdf_path: str) -> Dict[str, Any]:
            try:
                # Generate output path
                rel_path = os.path.relpath(pdf_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                output_path = get_default_output_path(output_path)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Convert the file
                result = self.converter.convert_pdf_to_markdown(
                    pdf_path,
                    output_path,
                    preserve_images=preserve_images
                )
                result['rel_path'] = rel_path
                return result
            
            except Exception as e:
                logger.error(f"Error processing file {pdf_path}: {str(e)}")
                return {
                    'success': False,
                    'input_path': pdf_path,
                    'error': str(e)
                }
        
        # Process files
        if parallel and len(pdf_files) > 1:
            conversion_results = process_with_threadpool(
                pdf_files,
                process_file,
                max_workers
            )
        else:
            conversion_results = [process_file(f) for f in pdf_files]
        
        # Summarize results
        successful = [r for r in conversion_results if r.get('success', False)]
        failed = [r for r in conversion_results if not r.get('success', False)]
        
        return {
            'success': len(failed) == 0,
            'files_processed': len(conversion_results),
            'successful_conversions': len(successful),
            'failed_conversions': len(failed),
            'results': conversion_results
        }
    
    def quick_convert(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        extract_images: bool = False
    ) -> Dict[str, Any]:
        """
        Quick conversion of a single PDF file with minimal configuration.
        
        Args:
            input_path: Path to the input PDF file
            output_path: Path for the output markdown file (optional)
            extract_images: Whether to extract images
        
        Returns:
            Dictionary containing conversion results
        """
        try:
            return self.converter.convert_pdf_to_markdown(
                input_path,
                output_path,
                preserve_images=extract_images
            )
        except Exception as e:
            logger.error(f"Error in quick convert: {str(e)}")
            return {
                'success': False,
                'input_path': input_path,
                'error': str(e)
            }