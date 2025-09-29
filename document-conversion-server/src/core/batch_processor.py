"""
Batch processing functionality for PDF conversions.

This module provides functionality for processing multiple PDF files,
with support for parallel processing and directory structure preservation.
"""

import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .pdf_converter import PDFConverter, ConversionOptions, ConversionResult


@dataclass
class BatchOptions:
    """Options for batch processing."""
    file_pattern: str = "*.pdf"
    recursive: bool = False
    preserve_structure: bool = True
    parallel: bool = True
    max_workers: int = 4
    preserve_images: bool = True


@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    total_files: int
    successful: int
    failed: int
    failed_files: List[str]
    conversion_times: Dict[str, float]
    error_messages: Dict[str, str]


class BatchProcessor:
    """Handles batch processing of PDF files."""

    def __init__(self):
        """Initialize the batch processor."""
        self.converter = PDFConverter()

    def process_batch(
        self,
        input_dir: str,
        output_dir: str,
        options: Optional[BatchOptions] = None
    ) -> BatchResult:
        """
        Process multiple PDF files in a directory.

        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory for output Markdown files
            options: Batch processing options (optional)

        Returns:
            BatchResult with processing statistics
        """
        if not os.path.exists(input_dir):
            return BatchResult(
                total_files=0,
                successful=0,
                failed=0,
                failed_files=[],
                conversion_times={},
                error_messages={"input_dir": f"Directory not found: {input_dir}"}
            )

        if options is None:
            options = BatchOptions()

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Find all PDF files
        pattern = os.path.join(input_dir, "**" if options.recursive else "", options.file_pattern)
        pdf_files = glob.glob(pattern, recursive=options.recursive)

        if not pdf_files:
            return BatchResult(
                total_files=0,
                successful=0,
                failed=0,
                failed_files=[],
                conversion_times={},
                error_messages={"files": "No PDF files found"}
            )

        conversion_results: List[ConversionResult] = []
        conversion_times: Dict[str, float] = {}
        
        if options.parallel and len(pdf_files) > 1:
            conversion_results = self._process_parallel(
                pdf_files,
                input_dir,
                output_dir,
                options
            )
        else:
            conversion_results = self._process_sequential(
                pdf_files,
                input_dir,
                output_dir,
                options
            )

        # Collect results
        successful = sum(1 for r in conversion_results if r.success)
        failed = len(pdf_files) - successful
        failed_files = [
            r.output_path for r in conversion_results 
            if not r.success
        ]
        error_messages = {
            r.output_path: r.error_message
            for r in conversion_results
            if not r.success and r.error_message
        }

        # Extract conversion times from stats
        for result in conversion_results:
            if result.success and result.stats:
                conversion_times[result.output_path] = result.stats.get(
                    "conversion_time", 0
                )

        return BatchResult(
            total_files=len(pdf_files),
            successful=successful,
            failed=failed,
            failed_files=failed_files,
            conversion_times=conversion_times,
            error_messages=error_messages
        )

    def _process_parallel(
        self,
        pdf_files: List[str],
        input_dir: str,
        output_dir: str,
        options: BatchOptions
    ) -> List[ConversionResult]:
        """Process files in parallel using a thread pool."""
        results: List[ConversionResult] = []
        
        with ThreadPoolExecutor(max_workers=options.max_workers) as executor:
            future_to_file = {
                executor.submit(
                    self._convert_single_file,
                    pdf_file,
                    input_dir,
                    output_dir,
                    options
                ): pdf_file
                for pdf_file in pdf_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    results.append(future.result())
                except Exception as e:
                    pdf_file = future_to_file[future]
                    results.append(ConversionResult(
                        success=False,
                        output_path=pdf_file,
                        error_message=f"Processing error: {str(e)}"
                    ))
                    
        return results

    def _process_sequential(
        self,
        pdf_files: List[str],
        input_dir: str,
        output_dir: str,
        options: BatchOptions
    ) -> List[ConversionResult]:
        """Process files sequentially."""
        return [
            self._convert_single_file(
                pdf_file,
                input_dir,
                output_dir,
                options
            )
            for pdf_file in pdf_files
        ]

    def _convert_single_file(
        self,
        pdf_file: str,
        input_dir: str,
        output_dir: str,
        options: BatchOptions
    ) -> ConversionResult:
        """Convert a single PDF file, preserving directory structure if needed."""
        rel_path = os.path.relpath(pdf_file, input_dir)
        
        if options.preserve_structure:
            # Maintain directory structure
            output_path = os.path.join(
                output_dir,
                os.path.splitext(rel_path)[0] + '.md'
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            # Flatten structure
            output_path = os.path.join(
                output_dir,
                os.path.splitext(os.path.basename(pdf_file))[0] + '.md'
            )

        conversion_options = ConversionOptions(
            preserve_images=options.preserve_images,
            image_dir=os.path.join(
                os.path.dirname(output_path),
                "images",
                os.path.splitext(os.path.basename(pdf_file))[0]
            )
        )

        return self.converter.convert_to_markdown(
            pdf_file,
            output_path,
            conversion_options
        )