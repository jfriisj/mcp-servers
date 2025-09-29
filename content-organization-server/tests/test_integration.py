"""Integration tests for content organization server."""

import os
import pytest
import json
from src.server import ContentOrganizationServer
from src.core import (
    ContentOrganizer,
    FileReorganizer,
    CrossReferencer
)

@pytest.mark.asyncio
async def test_content_organization_workflow(
    course_content_dir,
    file_organization_dir,
    cross_references_dir,
    temp_dir
):
    """Test complete content organization workflow."""
    # Initialize server
    server = ContentOrganizationServer()
    
    # Step 1: Organize course content
    result1 = await server.call_tool(
        'organize_course_content',
        {
            'content_dir': course_content_dir,
            'output_dir': os.path.join(temp_dir, 'organized'),
            'structure_template': os.path.join(course_content_dir, 'structure.yaml'),
            'metadata_schema': os.path.join(course_content_dir, 'metadata_schema.json'),
            'generate_index': True
        }
    )
    
    assert result1['success']
    organized_dir = os.path.join(temp_dir, 'organized')
    assert os.path.exists(organized_dir)
    assert os.path.exists(os.path.join(organized_dir, 'index.md'))
    
    # Step 2: Reorganize files
    with open(os.path.join(file_organization_dir, 'rules.yaml'), 'r') as f:
        rules = json.load(f)
    
    result2 = await server.call_tool(
        'reorganize_files',
        {
            'source_dir': organized_dir,
            'target_dir': os.path.join(temp_dir, 'reorganized'),
            'organization_rules': rules
        }
    )
    
    assert result2['success']
    reorganized_dir = os.path.join(temp_dir, 'reorganized')
    assert os.path.exists(reorganized_dir)
    
    # Step 3: Generate cross-references
    result3 = await server.call_tool(
        'generate_cross_references',
        {
            'content_dir': reorganized_dir,
            'output_file': os.path.join(temp_dir, 'references.json'),
            'generate_graph': True
        }
    )
    
    assert result3['success']
    assert os.path.exists(os.path.join(temp_dir, 'references.json'))
    assert 'documentation' in result3

@pytest.mark.asyncio
async def test_server_initialization():
    """Test server initialization and tool registration."""
    server = ContentOrganizationServer()
    
    # Check tool availability
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    
    assert 'organize_course_content' in tool_names
    assert 'reorganize_files' in tool_names
    assert 'generate_cross_references' in tool_names
    
    # Check schema loading
    for tool in tools:
        assert tool.input_schema is not None

@pytest.mark.asyncio
async def test_error_propagation(temp_dir):
    """Test error handling and propagation across components."""
    server = ContentOrganizationServer()
    
    # Test validation error
    result1 = await server.call_tool(
        'organize_course_content',
        {
            'content_dir': os.path.join(temp_dir, 'nonexistent'),
            'output_dir': temp_dir
        }
    )
    assert not result1['success']
    assert result1['error_code'] == 'FS_ERROR'
    
    # Test conflict error
    result2 = await server.call_tool(
        'reorganize_files',
        {
            'source_dir': temp_dir,
            'target_dir': temp_dir,
            'organization_rules': [
                {
                    'pattern': '*',
                    'action': 'move',
                    'target_subdir': 'same'
                }
            ]
        }
    )
    assert not result2['success']
    assert result2['error_code'] == 'FILE_CONFLICT'
    
    # Test invalid tool
    with pytest.raises(ValueError):
        await server.call_tool('nonexistent_tool', {})