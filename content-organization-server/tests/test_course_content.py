"""Tests for course content organization functionality."""

import os
import pytest
import yaml
import json
from src.core.content_organizer import ContentOrganizer
from src.mcp_handlers.course_content_handler import CourseContentHandler

@pytest.mark.asyncio
async def test_content_organization_basic(course_content_dir, temp_dir):
    """Test basic content organization without templates."""
    handler = CourseContentHandler()
    
    result = await handler.handle_tool(
        'organize_course_content',
        {
            'content_dir': course_content_dir,
            'output_dir': temp_dir,
            'content_types': ['markdown'],
            'preserve_original': True,
            'generate_index': True
        }
    )
    
    assert result['success']
    assert result['files_processed'] > 0
    assert os.path.exists(os.path.join(temp_dir, 'index.md'))

@pytest.mark.asyncio
async def test_content_organization_with_template(course_content_dir, temp_dir):
    """Test content organization with structure template."""
    handler = CourseContentHandler()
    structure_path = os.path.join(course_content_dir, 'structure.yaml')
    
    result = await handler.handle_tool(
        'organize_course_content',
        {
            'content_dir': course_content_dir,
            'output_dir': temp_dir,
            'structure_template': structure_path,
            'content_types': ['markdown'],
            'preserve_original': True,
            'generate_index': True
        }
    )
    
    assert result['success']
    assert os.path.exists(os.path.join(temp_dir, 'basics'))
    assert os.path.exists(os.path.join(temp_dir, 'concepts'))

@pytest.mark.asyncio
async def test_content_organization_with_metadata_schema(course_content_dir, temp_dir):
    """Test content organization with metadata schema validation."""
    handler = CourseContentHandler()
    schema_path = os.path.join(course_content_dir, 'metadata_schema.json')
    
    result = await handler.handle_tool(
        'organize_course_content',
        {
            'content_dir': course_content_dir,
            'output_dir': temp_dir,
            'metadata_schema': schema_path,
            'content_types': ['markdown']
        }
    )
    
    assert result['success']

@pytest.mark.asyncio
async def test_content_organization_invalid_dir(temp_dir):
    """Test handling of invalid directory."""
    handler = CourseContentHandler()
    
    result = await handler.handle_tool(
        'organize_course_content',
        {
            'content_dir': os.path.join(temp_dir, 'nonexistent'),
            'output_dir': temp_dir
        }
    )
    
    assert not result['success']
    assert result['error_code'] == 'FS_ERROR'

@pytest.mark.asyncio
async def test_content_organization_index_generation(course_content_dir, temp_dir):
    """Test index file generation."""
    handler = CourseContentHandler()
    
    result = await handler.handle_tool(
        'organize_course_content',
        {
            'content_dir': course_content_dir,
            'output_dir': temp_dir,
            'generate_index': True
        }
    )
    
    assert result['success']
    index_path = os.path.join(temp_dir, 'index.md')
    assert os.path.exists(index_path)
    
    with open(index_path, 'r') as f:
        content = f.read()
        assert 'Introduction to Algorithms' in content