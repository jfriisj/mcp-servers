"""Core functionality for converting PDF files to Markdown format."""

import os
from typing import Optional, List, Dict, Any
import logging
import fitz  # PyMuPDF
from .converter_utils import (
    validate_pdf_file,
    ensure_directory_exists,
    extract_images,
    get_default_output_path,
)

logger = logging.getLogger(__name__)

class PDFConverter:
    """Handles conversion of PDF files to Markdown format."""
    
    def __init__(self):
        self.current_doc = None
    
    def _convert_tables(self, page: fitz.Page, table_format: str = 'pipe') -> List[str]:
        """
        Convert tables in a PDF page to markdown format.
        
        Args:
            page: The PDF page containing tables
            table_format: Format for markdown tables ('grid', 'pipe', or 'simple')
        
        Returns:
            List of markdown table strings
        """
        tables = []
        
        for table in page.find_tables():
            if table_format == 'grid':
                tables.append(self._format_grid_table(table))
            elif table_format == 'simple':
                tables.append(self._format_simple_table(table))
            else:  # default to pipe format
                tables.append(self._format_pipe_table(table))
        
        return tables
    
    def _format_pipe_table(self, table) -> str:
        """Format table in pipe style (| col1 | col2 |)."""
        markdown_table = []
        
        # Header
        header = '| ' + ' | '.join(str(cell) for cell in table[0]) + ' |'
        markdown_table.append(header)
        
        # Separator
        separator = '|' + '|'.join(['---' for _ in table[0]]) + '|'
        markdown_table.append(separator)
        
        # Data rows
        for row in table[1:]:
            row_str = '| ' + ' | '.join(str(cell) for cell in row) + ' |'
            markdown_table.append(row_str)
        
        return '\n'.join(markdown_table)
    
    def _format_grid_table(self, table) -> str:
        """Format table in grid style (+---+---+)."""
        markdown_table = []
        col_widths = [max(len(str(row[i])) for row in table) for i in range(len(table[0]))]
        
        def make_separator(char='-'):
            return '+' + '+'.join(char * (width + 2) for width in col_widths) + '+'
        
        markdown_table.append(make_separator())
        
        for i, row in enumerate(table):
            cells = []
            for j, cell in enumerate(row):
                cells.append(f' {str(cell):{col_widths[j]}} ')
            markdown_table.append('|' + '|'.join(cells) + '|')
            
            if i == 0:  # After header
                markdown_table.append(make_separator('='))
            else:
                markdown_table.append(make_separator())
        
        return '\n'.join(markdown_table)
    
    def _format_simple_table(self, table) -> str:
        """Format table in simple style (no vertical bars)."""
        markdown_table = []
        
        # Header
        header = ' '.join(str(cell) for cell in table[0])
        markdown_table.append(header)
        
        # Separator
        separator = ' '.join('-' * len(str(cell)) for cell in table[0])
        markdown_table.append(separator)
        
        # Data rows
        for row in table[1:]:
            row_str = ' '.join(str(cell) for cell in row)
            markdown_table.append(row_str)
        
        return '\n'.join(markdown_table)
    
    def convert_pdf_to_markdown(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        preserve_images: bool = True,
        image_dir: str = 'images',
        table_format: str = 'pipe'
    ) -> Dict[str, Any]:
        """
        Convert a PDF file to Markdown format.
        
        Args:
            input_path: Path to the input PDF file
            output_path: Path where the markdown should be saved (optional)
            preserve_images: Whether to extract and save images
            image_dir: Directory to save extracted images
            table_format: Format for markdown tables ('grid', 'pipe', or 'simple')
        
        Returns:
            Dict containing conversion results and metadata
        
        Raises:
            FileNotFoundError: If input file doesn't exist
            InvalidPDFError: If PDF is invalid or corrupted
            PermissionError: If file access is denied
            ConversionError: If conversion fails
        """
        # Validate inputs
        validate_pdf_file(input_path)
        if not output_path:
            output_path = get_default_output_path(input_path)
        
        ensure_directory_exists(os.path.dirname(output_path))
        if preserve_images:
            image_dir = os.path.join(os.path.dirname(output_path), image_dir)
            ensure_directory_exists(image_dir)
        
        try:
            doc = fitz.open(input_path)
            self.current_doc = doc
            
            markdown_content = []
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'keywords': doc.metadata.get('keywords', ''),
                'page_count': len(doc),
                'images': []
            }
            
            # Add metadata as YAML frontmatter
            if any(metadata.values()):
                markdown_content.append('---')
                for key, value in metadata.items():
                    if value and key != 'page_count' and key != 'images':
                        markdown_content.append(f'{key}: {value}')
                markdown_content.append('---\n')
            
            for page_num, page in enumerate(doc):
                # Extract text
                text = page.get_text()
                
                # Handle images
                if preserve_images:
                    images = extract_images(page, image_dir)
                    metadata['images'].extend(images)
                    
                    # Add image references to markdown
                    for img in images:
                        relative_path = os.path.relpath(img['path'], os.path.dirname(output_path))
                        text += f"\n![Image {img['filename']}]({relative_path})\n"
                
                # Convert tables
                tables = self._convert_tables(page, table_format)
                if tables:
                    text = self._insert_tables(text, tables)
                
                markdown_content.append(text)
                
                # Add page break if not last page
                if page_num < len(doc) - 1:
                    markdown_content.append('\n---\n')
            
            # Write markdown content
            markdown_text = '\n'.join(markdown_content)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'metadata': metadata
            }
        
        except Exception as e:
            logger.error(f"Error converting PDF to markdown: {str(e)}")
            raise
        
        finally:
            if self.current_doc:
                self.current_doc.close()
                self.current_doc = None
    
    def _insert_tables(self, text: str, tables: List[str]) -> str:
        """
        Insert markdown tables into the appropriate positions in the text.
        
        Args:
            text: The page text
            tables: List of markdown table strings
        
        Returns:
            Text with tables inserted
        """
        # Simple implementation: append tables at the end of the text
        # A more sophisticated implementation would try to determine
        # the original table positions in the text
        result = text.rstrip()
        for table in tables:
            result += f"\n\n{table}\n"
        return result