"""Test suite for PDF conversion tools."""

import os
import pytest
from typing import Dict, Any
import shutil
import tempfile
from mcp_handlers.pdf_to_markdown_handler import PDFToMarkdownHandler
from mcp_handlers.batch_convert_handler import BatchConvertHandler
from mcp_handlers.quick_convert_handler import QuickConvertHandler
from core.converter_utils import ConversionError, InvalidPDFError, FileNotFoundError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_data_dir():
    """Get the path to test data directory."""
    return os.path.join(os.path.dirname(__file__), 'data')

@pytest.fixture
def sample_pdf(test_data_dir):
    """Get the path to sample PDF file."""
    return os.path.join(test_data_dir, 'sample.pdf')

def test_pdf_to_markdown_basic(sample_pdf, temp_dir):
    """Test basic PDF to markdown conversion."""
    handler = PDFToMarkdownHandler()
    output_path = os.path.join(temp_dir, 'output.md')
    
    result = handler.handle_request({
        'input_path': sample_pdf,
        'output_path': output_path
    })
    
    assert result['success']
    assert os.path.exists(output_path)
    assert result['metadata']['page_count'] > 0

def test_pdf_to_markdown_with_images(sample_pdf, temp_dir):
    """Test PDF conversion with image extraction."""
    handler = PDFToMarkdownHandler()
    output_path = os.path.join(temp_dir, 'output.md')
    image_dir = os.path.join(temp_dir, 'images')
    
    result = handler.handle_request({
        'input_path': sample_pdf,
        'output_path': output_path,
        'preserve_images': True,
        'image_dir': 'images'
    })
    
    assert result['success']
    assert os.path.exists(output_path)
    if result['metadata']['images']:
        assert os.path.exists(image_dir)

def test_pdf_to_markdown_missing_file(temp_dir):
    """Test handling of missing input file."""
    handler = PDFToMarkdownHandler()
    output_path = os.path.join(temp_dir, 'output.md')
    
    result = handler.handle_request({
        'input_path': 'nonexistent.pdf',
        'output_path': output_path
    })
    
    assert not result['success']
    assert result['error_code'] == 'FILE_NOT_FOUND'

def test_batch_convert_basic(test_data_dir, temp_dir):
    """Test basic batch conversion."""
    handler = BatchConvertHandler()
    
    result = handler.handle_request({
        'input_dir': test_data_dir,
        'output_dir': temp_dir
    })
    
    assert result['success']
    assert result['files_processed'] > 0
    assert len(os.listdir(temp_dir)) > 0

def test_batch_convert_recursive(test_data_dir, temp_dir):
    """Test recursive batch conversion."""
    handler = BatchConvertHandler()
    
    result = handler.handle_request({
        'input_dir': test_data_dir,
        'output_dir': temp_dir,
        'recursive': True
    })
    
    assert result['success']
    assert result['files_processed'] > 0

def test_batch_convert_missing_dir():
    """Test handling of missing input directory."""
    handler = BatchConvertHandler()
    
    result = handler.handle_request({
        'input_dir': 'nonexistent_dir',
        'output_dir': 'output_dir'
    })
    
    assert not result['success']
    assert result['error_code'] == 'FILE_NOT_FOUND'

def test_quick_convert_basic(sample_pdf, temp_dir):
    """Test basic quick conversion."""
    handler = QuickConvertHandler()
    output_path = os.path.join(temp_dir, 'output.md')
    
    result = handler.handle_request({
        'input_path': sample_pdf,
        'output_path': output_path
    })
    
    assert result['success']
    assert os.path.exists(output_path)

def test_quick_convert_auto_output(sample_pdf, temp_dir):
    """Test quick conversion with automatic output path."""
    handler = QuickConvertHandler()
    
    result = handler.handle_request({
        'input_path': sample_pdf
    })
    
    assert result['success']
    assert os.path.exists(result['output_path'])
    assert result['output_path'].endswith('.md')

def test_quick_convert_missing_file(temp_dir):
    """Test quick conversion with missing file."""
    handler = QuickConvertHandler()
    
    result = handler.handle_request({
        'input_path': 'nonexistent.pdf'
    })
    
    assert not result['success']
    assert result['error_code'] == 'FILE_NOT_FOUND'

def test_invalid_table_format(sample_pdf, temp_dir):
    """Test handling of invalid table format."""
    handler = PDFToMarkdownHandler()
    output_path = os.path.join(temp_dir, 'output.md')
    
    result = handler.handle_request({
        'input_path': sample_pdf,
        'output_path': output_path,
        'table_format': 'invalid'
    })
    
    assert not result['success']
    assert result['error_code'] == 'INVALID_PARAMETER'

def test_missing_required_params():
    """Test handling of missing required parameters."""
    handlers = [
        PDFToMarkdownHandler(),
        BatchConvertHandler(),
        QuickConvertHandler()
    ]
    
    for handler in handlers:
        result = handler.handle_request({})
        assert not result['success']
        assert result['error_code'] == 'MISSING_PARAMETER'