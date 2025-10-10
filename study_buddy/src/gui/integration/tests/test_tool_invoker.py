"""
Unit tests for GUI Tool Invoker with Schema Validation

Tests the ToolInvoker implementation with mocked dependencies to ensure
proper validation, progress tracking, error handling, and MCP integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import Dict, Any

from gui.integration.tool_invoker import (
    GUIToolInvoker, 
    UploadDocumentParams,
    ValidationResult,
    ToolExecutionError,
    create_tool_invoker
)
from gui.integration.mcp_client import (
    IMCPClient, MCPResponse, OperationProgress, ProgressPhase,
    ValidationError, ConnectionHealth, ConnectionState
)


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    client = Mock(spec=IMCPClient)
    
    # Mock health status
    health_status = ConnectionHealth(
        is_connected=True,
        connection_state=ConnectionState.CONNECTED,
        round_trip_time_ms=50.0,
        active_operations=0,
        total_operations=0,
        error_count=0
    )
    client.get_health_status = AsyncMock(return_value=health_status)
    
    # Mock upload document
    upload_response = MCPResponse(
        success=True,
        operation_id="test_op",
        operation_name="upload_document",
        data={"document_id": 123, "title": "Test Document", "file_type": "pdf"}
    )
    client.upload_document = AsyncMock(return_value=upload_response)
    
    # Mock search documents
    search_response = MCPResponse(
        success=True,
        operation_id="test_op",
        operation_name="search_documents",
        data={"total_results": 1, "results": [{"document_id": 123}]}
    )
    client.search_documents = AsyncMock(return_value=search_response)
    
    return client


@pytest.fixture
def tool_invoker(mock_mcp_client):
    """Create a GUIToolInvoker instance for testing."""
    return GUIToolInvoker(mcp_client=mock_mcp_client, enable_validation=True)


class TestGUIToolInvoker:
    """Test suite for GUIToolInvoker."""
    
    def test_initialization(self, mock_mcp_client):
        """Test proper initialization of tool invoker."""
        invoker = GUIToolInvoker(mcp_client=mock_mcp_client, enable_validation=True)
        
        assert invoker.mcp_client is mock_mcp_client
        assert invoker.enable_validation is True
        assert len(invoker.tool_schemas) > 0
        assert "upload_document" in invoker.tool_schemas
        assert invoker.stats['total_operations'] == 0
    
    def test_parameter_validation_success(self, tool_invoker):
        """Test successful parameter validation."""
        parameters = {
            'file_path': '/absolute/path/to/document.pdf',
            'title': 'Test Document',
            'tags': ['test', 'document']
        }
        
        result = tool_invoker.validate_parameters('upload_document', parameters)
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.validated_params['file_path'] == parameters['file_path']
    
    def test_parameter_validation_failure(self, tool_invoker):
        """Test parameter validation failure."""
        parameters = {
            'file_path': '',  # Invalid empty path
            'title': 'Test Document'
        }
        
        result = tool_invoker.validate_parameters('upload_document', parameters)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validation_disabled(self, mock_mcp_client):
        """Test behavior when validation is disabled."""
        invoker = GUIToolInvoker(mcp_client=mock_mcp_client, enable_validation=False)
        
        parameters = {'invalid': 'parameters'}
        result = invoker.validate_parameters('upload_document', parameters)
        
        assert result.is_valid is True
        assert result.validated_params == parameters
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, tool_invoker):
        """Test successful document upload."""
        file_path = '/path/to/document.pdf'
        
        response = await tool_invoker.upload_document(
            file_path=file_path,
            title="Test Document",
            tags=["test"]
        )
        
        assert response.success is True
        assert response.data['document_id'] == 123
        assert tool_invoker.stats['successful_operations'] == 1
        assert tool_invoker.stats['total_operations'] == 1
    
    @pytest.mark.asyncio
    async def test_search_documents_success(self, tool_invoker):
        """Test successful document search."""
        query = "test query"
        
        response = await tool_invoker.search_documents(
            query=query,
            limit=10
        )
        
        assert response.success is True
        assert response.data['total_results'] == 1
        assert tool_invoker.stats['successful_operations'] == 1
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, tool_invoker):
        """Test handling of validation errors."""
        # Empty file path should trigger validation error
        with pytest.raises(ValidationError):
            await tool_invoker.upload_document(file_path="")
        
        assert tool_invoker.stats['failed_operations'] == 1
        assert tool_invoker.stats['validation_errors'] == 1
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, tool_invoker):
        """Test progress callback functionality."""
        progress_updates = []
        
        def progress_callback(progress: OperationProgress):
            progress_updates.append(progress)
        
        await tool_invoker.upload_document(
            file_path='/path/to/document.pdf',
            progress_callback=progress_callback
        )
        
        # Should have at least one progress update (completion)
        assert len(progress_updates) >= 1
        final_progress = progress_updates[-1]
        assert final_progress.progress_percent == 100.0
        assert final_progress.current_step == "Completed"
    
    @pytest.mark.asyncio
    async def test_health_check(self, tool_invoker):
        """Test health check functionality."""
        health = await tool_invoker.health_check()
        
        assert health['status'] == 'healthy'
        assert 'tool_invoker' in health
        assert 'mcp_client' in health
        assert health['tool_invoker']['validation_enabled'] is True
    
    def test_get_supported_tools(self, tool_invoker):
        """Test getting list of supported tools."""
        tools = tool_invoker.get_supported_tools()
        
        assert isinstance(tools, list)
        assert 'upload_document' in tools
        assert len(tools) > 0
    
    def test_get_statistics(self, tool_invoker):
        """Test getting performance statistics."""
        stats = tool_invoker.get_statistics()
        
        assert 'total_operations' in stats
        assert 'successful_operations' in stats
        assert 'failed_operations' in stats
        assert 'validation_errors' in stats
        assert stats['total_operations'] == 0  # No operations run yet
    
    def test_get_active_operations(self, tool_invoker):
        """Test getting active operations list."""
        operations = tool_invoker.get_active_operations()
        
        assert isinstance(operations, list)
        assert len(operations) == 0  # No active operations initially
    
    def test_factory_function(self, mock_mcp_client):
        """Test the factory function for creating tool invoker."""
        invoker = create_tool_invoker(mcp_client=mock_mcp_client, enable_validation=True)
        
        assert isinstance(invoker, GUIToolInvoker)
        assert invoker.mcp_client is mock_mcp_client
        assert invoker.enable_validation is True
    
    @pytest.mark.asyncio
    async def test_shutdown(self, tool_invoker):
        """Test proper shutdown of tool invoker."""
        await tool_invoker.shutdown()
        
        # Should clear active operations
        assert len(tool_invoker.active_operations) == 0


class TestParameterSchemas:
    """Test the Pydantic parameter schemas."""
    
    def test_upload_document_params_valid(self):
        """Test valid upload document parameters."""
        params = UploadDocumentParams(
            file_path='/absolute/path/to/document.pdf',
            title='Test Document',
            tags=['test', 'document'],
            notes='Test notes'
        )
        
        assert params.file_path == '/absolute/path/to/document.pdf'
        assert params.title == 'Test Document'
        assert params.tags == ['test', 'document']
    
    def test_upload_document_params_minimal(self):
        """Test upload document parameters with only required fields."""
        params = UploadDocumentParams(file_path='/path/to/doc.pdf')
        
        assert params.file_path == '/path/to/doc.pdf'
        assert params.title is None
        assert params.tags is None
        assert params.notes is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])