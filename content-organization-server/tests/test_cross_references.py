"""Tests for cross-reference generation functionality."""

import os
import json
import pytest
import networkx as nx
from src.core.cross_referencer import CrossReferencer
from src.mcp_handlers.cross_reference_handler import CrossReferenceHandler

@pytest.mark.asyncio
async def test_cross_reference_basic(cross_references_dir, temp_dir):
    """Test basic cross-reference generation."""
    handler = CrossReferenceHandler()
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': cross_references_dir,
            'reference_types': ['links', 'concepts'],
            'formats': ['md']
        }
    )
    
    assert result['success']
    assert result['references_found'] > 0
    assert 'graph_stats' in result

@pytest.mark.asyncio
async def test_cross_reference_export(cross_references_dir, temp_dir):
    """Test cross-reference export functionality."""
    handler = CrossReferenceHandler()
    output_file = os.path.join(temp_dir, 'references.json')
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': cross_references_dir,
            'output_file': output_file,
            'reference_types': ['links', 'concepts', 'dependencies'],
            'formats': ['md'],
            'generate_graph': True,
            'graph_format': 'json'
        }
    )
    
    assert result['success']
    assert os.path.exists(output_file)
    
    with open(output_file, 'r') as f:
        data = json.load(f)
        assert 'nodes' in data
        assert 'edges' in data

@pytest.mark.asyncio
async def test_cross_reference_documentation(cross_references_dir, temp_dir):
    """Test cross-reference documentation generation."""
    handler = CrossReferenceHandler()
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': cross_references_dir,
            'reference_types': ['links', 'concepts'],
            'generate_graph': True
        }
    )
    
    assert result['success']
    assert 'documentation' in result
    assert result['documentation']['success']
    assert os.path.exists(os.path.join('references', 'index.md'))

@pytest.mark.asyncio
async def test_cross_reference_cycles(cross_references_dir, temp_dir):
    """Test cycle detection in references."""
    handler = CrossReferenceHandler()
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': cross_references_dir,
            'reference_types': ['concepts'],
            'depth': 3
        }
    )
    
    assert result['success']
    assert 'cycles_detected' in result

@pytest.mark.asyncio
async def test_cross_reference_invalid_dir(temp_dir):
    """Test handling of invalid directory."""
    handler = CrossReferenceHandler()
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': os.path.join(temp_dir, 'nonexistent')
        }
    )
    
    assert not result['success']
    assert result['error_code'] == 'FS_ERROR'

@pytest.mark.asyncio
async def test_cross_reference_statistics(cross_references_dir, temp_dir):
    """Test cross-reference statistics generation."""
    handler = CrossReferenceHandler()
    
    result = await handler.handle_tool(
        'generate_cross_references',
        {
            'content_dir': cross_references_dir,
            'reference_types': ['links', 'concepts', 'dependencies', 'citations']
        }
    )
    
    assert result['success']
    assert 'statistics' in result
    stats = result['statistics']
    assert 'total_references' in stats
    assert 'reference_types' in stats
    assert 'graph_stats' in stats