"""Tests for server stdio communication."""

import os
import json
import pytest
import asyncio
from io import StringIO
from typing import Dict, Any, AsyncGenerator, Tuple
from src.server import ContentOrganizationServer

async def mock_stdio() -> AsyncGenerator[Tuple[asyncio.StreamReader, asyncio.StreamWriter], None]:
    """Mock stdio streams for testing."""
    reader = asyncio.StreamReader()
    writer = asyncio.StreamWriter(StringIO(), None, None, None)
    yield reader, writer

@pytest.mark.asyncio
async def test_server_stdio_initialization():
    """Test server initialization via stdio."""
    server = ContentOrganizationServer()
    
    # Mock initialization request
    init_request = {
        'jsonrpc': '2.0',
        'method': 'initialize',
        'id': 1,
        'params': {}
    }
    
    async with mock_stdio() as (reader, writer):
        # Send initialization request
        reader.feed_data(json.dumps(init_request).encode() + b'\n')
        reader.feed_eof()
        
        # Start server
        await server.serve()
        
        # Check response
        response = writer.buffer.getvalue()
        assert response
        response_data = json.loads(response.decode())
        assert response_data['id'] == 1
        assert 'result' in response_data

@pytest.mark.asyncio
async def test_server_stdio_tool_call():
    """Test tool execution via stdio."""
    server = ContentOrganizationServer()
    
    # Mock tool call request
    tool_request = {
        'jsonrpc': '2.0',
        'method': 'call_tool',
        'id': 2,
        'params': {
            'name': 'organize_course_content',
            'arguments': {
                'content_dir': '/path/to/content',
                'output_dir': '/path/to/output'
            }
        }
    }
    
    async with mock_stdio() as (reader, writer):
        # Send tool request
        reader.feed_data(json.dumps(tool_request).encode() + b'\n')
        reader.feed_eof()
        
        # Start server
        await server.serve()
        
        # Check response
        response = writer.buffer.getvalue()
        assert response
        response_data = json.loads(response.decode())
        assert response_data['id'] == 2
        assert 'result' in response_data

@pytest.mark.asyncio
async def test_server_stdio_error_handling():
    """Test error handling in stdio communication."""
    server = ContentOrganizationServer()
    
    # Mock invalid request
    invalid_request = {
        'jsonrpc': '2.0',
        'method': 'invalid_method',
        'id': 3,
        'params': {}
    }
    
    async with mock_stdio() as (reader, writer):
        # Send invalid request
        reader.feed_data(json.dumps(invalid_request).encode() + b'\n')
        reader.feed_eof()
        
        # Start server
        await server.serve()
        
        # Check error response
        response = writer.buffer.getvalue()
        assert response
        response_data = json.loads(response.decode())
        assert response_data['id'] == 3
        assert 'error' in response_data