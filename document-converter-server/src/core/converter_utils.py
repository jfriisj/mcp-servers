"""Utility functions for PDF conversion operations."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass

class InvalidPDFError(ConversionError):
    """Exception raised when the PDF file is invalid or corrupted."""
    pass

class FileNotFoundError(ConversionError):
    """Exception raised when a file or directory is not found."""
    pass

def ensure_directory_exists(path: str) -> None:
    """
    Ensure that the directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory to check/create
    
    Raises:
        PermissionError: If directory cannot be created due to permissions
    """
    os.makedirs(path, exist_ok=True)

def validate_pdf_file(file_path: str) -> None:
    """
    Validate that a PDF file exists and is readable.
    
    Args:
        file_path: Path to the PDF file
    
    Raises:
        FileNotFoundError: If the file does not exist
        InvalidPDFError: If the file is not a valid PDF
        PermissionError: If the file cannot be read due to permissions
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    try:
        doc = fitz.open(file_path)
        doc.close()
    except fitz.FileDataError:
        raise InvalidPDFError(f"Invalid or corrupted PDF file: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading PDF file: {file_path}")

def extract_images(page: fitz.Page, output_dir: str) -> List[Dict[str, Any]]:
    """
    Extract images from a PDF page and save them to the output directory.
    
    Args:
        page: The PDF page to extract images from
        output_dir: Directory to save extracted images
    
    Returns:
        List of dictionaries containing image metadata
    """
    ensure_directory_exists(output_dir)
    images = []
    
    for img_index, img in enumerate(page.get_images()):
        xref = img[0]
        base_image = page.parent.extract_image(xref)
        
        if base_image:
            image_data = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"image_{page.number + 1}_{img_index + 1}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            
            images.append({
                "filename": image_filename,
                "path": image_path,
                "ext": image_ext,
                "size": len(image_data)
            })
    
    return images

def find_pdf_files(directory: str, recursive: bool = False, pattern: str = "*.pdf") -> List[str]:
    """
    Find PDF files in a directory.
    
    Args:
        directory: Directory to search for PDF files
        recursive: Whether to search recursively in subdirectories
        pattern: File pattern to match (e.g., "*.pdf")
    
    Returns:
        List of PDF file paths
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    pdf_files = []
    base_path = Path(directory)
    
    if recursive:
        for path in base_path.rglob(pattern):
            if path.is_file():
                pdf_files.append(str(path))
    else:
        for path in base_path.glob(pattern):
            if path.is_file():
                pdf_files.append(str(path))
    
    return sorted(pdf_files)

def get_default_output_path(input_path: str) -> str:
    """
    Generate default output path by replacing the extension with .md
    
    Args:
        input_path: Path to the input PDF file
    
    Returns:
        Path to the output markdown file
    """
    return str(Path(input_path).with_suffix('.md'))

def process_with_threadpool(
    items: List[Any],
    process_func: callable,
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Process items in parallel using a thread pool.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        max_workers: Maximum number of worker threads
    
    Returns:
        List of processed results
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_func, items))
    return results