"""Tests for file reorganization functionality."""

import os
import pytest
import yaml
from src.core.file_reorganizer import FileReorganizer
from src.mcp_handlers.file_reorganization_handler import FileReorganizationHandler

@pytest.mark.asyncio
async def test_file_reorganization_basic(file_organization_dir, temp_dir):
    """Test basic file reorganization."""
    handler = FileReorganizationHandler()
    rules_path = os.path.join(file_organization_dir, 'rules.yaml')
    
    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)
    
    result = await handler.handle_tool(
        'reorganize_files',
        {
            'source_dir': file_organization_dir,
            'target_dir': temp_dir,
            'organization_rules': rules,
            'recursive': True
        }
    )
    
    assert result['success']
    assert os.path.exists(os.path.join(temp_dir, 'content'))
    assert os.path.exists(os.path.join(temp_dir, 'code'))

@pytest.mark.asyncio
async def test_file_reorganization_dry_run(file_organization_dir, temp_dir):
    """Test dry run mode."""
    handler = FileReorganizationHandler()
    rules_path = os.path.join(file_organization_dir, 'rules.yaml')
    
    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)
    
    result = await handler.handle_tool(
        'reorganize_files',
        {
            'source_dir': file_organization_dir,
            'target_dir': temp_dir,
            'organization_rules': rules,
            'dry_run': True
        }
    )
    
    assert result['success']
    assert result['dry_run']
    assert not os.path.exists(os.path.join(temp_dir, 'content'))

@pytest.mark.asyncio
async def test_file_reorganization_invalid_rules(file_organization_dir, temp_dir):
    """Test handling of invalid rules."""
    handler = FileReorganizationHandler()
    
    result = await handler.handle_tool(
        'reorganize_files',
        {
            'source_dir': file_organization_dir,
            'target_dir': temp_dir,
            'organization_rules': [
                {
                    'pattern': '*.txt'
                    # Missing required 'action' field
                }
            ]
        }
    )
    
    assert not result['success']
    assert result['error_code'] == 'VALIDATION_ERROR'

@pytest.mark.asyncio
async def test_file_reorganization_conflicts(file_organization_dir, temp_dir):
    """Test handling of file conflicts."""
    handler = FileReorganizationHandler()
    
    # Create rules that would cause conflicts
    conflicting_rules = [
        {
            'pattern': '*.md',
            'action': 'move',
            'target_subdir': 'docs'
        },
        {
            'pattern': '*.*',
            'action': 'move',
            'target_subdir': 'docs'
        }
    ]
    
    result = await handler.handle_tool(
        'reorganize_files',
        {
            'source_dir': file_organization_dir,
            'target_dir': temp_dir,
            'organization_rules': conflicting_rules
        }
    )
    
    assert not result['success']
    assert result['error_code'] == 'FILE_CONFLICT'

@pytest.mark.asyncio
async def test_file_reorganization_categorize(file_organization_dir, temp_dir):
    """Test categorize action."""
    handler = FileReorganizationHandler()
    
    rules = [
        {
            'pattern': '*.*',
            'action': 'categorize',
            'target_subdir': 'sorted'
        }
    ]
    
    result = await handler.handle_tool(
        'reorganize_files',
        {
            'source_dir': file_organization_dir,
            'target_dir': temp_dir,
            'organization_rules': rules
        }
    )
    
    assert result['success']
    assert os.path.exists(os.path.join(temp_dir, 'sorted', 'yaml'))