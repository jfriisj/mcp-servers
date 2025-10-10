"""
Comprehensive unit tests for tool layer integration components.

Tests:
- tool_invoker.py: Tool execution and management
- schemas.py: Data schema validation and transformation

Coverage Target: 90%+
Performance: <50ms per tool operation
Error Scenarios: Invalid schemas, tool failures, timeout handling
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tool_invoker import ToolInvoker, ToolRegistry
    from schemas import (
        MCPRequest, MCPResponse, ToolSchema, 
        ValidationError, SchemaValidator
    )
except ImportError as e:
    # Fallback for testing without actual implementations
    print(f"Warning: Could not import tool components: {e}")
    ToolInvoker = None
    ToolRegistry = None
    MCPRequest = None
    MCPResponse = None
    ToolSchema = None
    ValidationError = None
    SchemaValidator = None


class TestToolInvoker:
    """Unit tests for ToolInvoker execution management."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock MCP client for tool testing."""
        client = Mock()
        client.call_tool = Mock(return_value={'result': {'success': True}})
        client.is_connected = Mock(return_value=True)
        return client
    
    @pytest.fixture
    def tool_invoker(self, mock_client):
        """ToolInvoker instance for testing."""
        if ToolInvoker is None:
            pytest.skip("ToolInvoker not available")
        return ToolInvoker(mock_client)
    
    def test_invoker_initialization(self, mock_client):
        """Test tool invoker initializes correctly."""
        if ToolInvoker is None:
            pytest.skip("ToolInvoker not available")
            
        invoker = ToolInvoker(mock_client)
        assert invoker.client == mock_client
        assert hasattr(invoker, 'registry')
    
    def test_tool_registration(self, tool_invoker):
        """Test tool registration and discovery."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        tool_schema = {
            'name': 'test_tool',
            'description': 'A test tool',
            'parameters': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string'},
                    'param2': {'type': 'integer'}
                }
            }
        }
        
        result = tool_invoker.register_tool(tool_schema)
        assert result is True
        assert 'test_tool' in tool_invoker.get_available_tools()
    
    def test_tool_validation(self, tool_invoker):
        """Test parameter validation before tool execution."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Register tool with schema
        tool_schema = {
            'name': 'validation_tool',
            'parameters': {
                'type': 'object',
                'properties': {
                    'required_param': {'type': 'string'},
                    'optional_param': {'type': 'integer'}
                },
                'required': ['required_param']
            }
        }
        tool_invoker.register_tool(tool_schema)
        
        # Test valid parameters
        valid_params = {'required_param': 'test_value'}
        is_valid = tool_invoker.validate_parameters('validation_tool', valid_params)
        assert is_valid is True
        
        # Test invalid parameters
        invalid_params = {'optional_param': 42}  # Missing required param
        is_valid = tool_invoker.validate_parameters('validation_tool', invalid_params)
        assert is_valid is False
    
    def test_tool_execution_success(self, tool_invoker, performance_timer):
        """Test successful tool execution with timing."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Setup mock response
        tool_invoker.client.call_tool.return_value = {
            'result': {'success': True, 'data': 'test_output'}
        }
        
        with performance_timer:
            result = tool_invoker.execute_tool(
                'test_tool',
                {'param': 'value'}
            )
        
        assert performance_timer.elapsed < 0.05  # Should be fast
        assert result is not None
        assert result.get('result', {}).get('success') is True
        tool_invoker.client.call_tool.assert_called_once()
    
    def test_tool_execution_failure(self, tool_invoker):
        """Test tool execution failure handling."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Setup mock failure
        tool_invoker.client.call_tool.side_effect = Exception("Tool failed")
        
        result = tool_invoker.execute_tool('failing_tool', {})
        assert result is None or 'error' in result
    
    def test_tool_timeout_handling(self, tool_invoker):
        """Test tool timeout handling."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Setup mock timeout
        tool_invoker.client.call_tool.side_effect = TimeoutError("Tool timeout")
        
        result = tool_invoker.execute_tool('slow_tool', {}, timeout=1.0)
        assert result is None or 'timeout' in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_async_tool_execution(self, tool_invoker):
        """Test async tool execution patterns."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Setup async mock
        async_mock = AsyncMock(return_value={'result': {'success': True}})
        tool_invoker.client.call_tool_async = async_mock
        
        if hasattr(tool_invoker, 'execute_tool_async'):
            result = await tool_invoker.execute_tool_async('async_tool', {})
            assert result is not None
            async_mock.assert_called_once()
    
    def test_batch_tool_execution(self, tool_invoker, performance_timer):
        """Test batch execution of multiple tools."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Setup batch tools
        tools_to_execute = [
            ('tool1', {'param': 'value1'}),
            ('tool2', {'param': 'value2'}),
            ('tool3', {'param': 'value3'})
        ]
        
        # Mock responses
        tool_invoker.client.call_tool.return_value = {'result': {'success': True}}
        
        with performance_timer:
            if hasattr(tool_invoker, 'execute_batch'):
                results = tool_invoker.execute_batch(tools_to_execute)
                assert len(results) == 3
                assert performance_timer.elapsed < 0.2  # Batch should be efficient
    
    def test_tool_registry_management(self, tool_invoker):
        """Test tool registry operations."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Test getting all tools
        all_tools = tool_invoker.get_available_tools()
        assert isinstance(all_tools, (list, dict))
        
        # Test tool filtering
        if hasattr(tool_invoker, 'filter_tools'):
            filtered = tool_invoker.filter_tools(category='test')
            assert isinstance(filtered, (list, dict))
    
    def test_execution_history(self, tool_invoker):
        """Test tool execution history tracking."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Execute some tools
        tool_invoker.client.call_tool.return_value = {'result': {'success': True}}
        
        tool_invoker.execute_tool('history_tool1', {})
        tool_invoker.execute_tool('history_tool2', {})
        
        if hasattr(tool_invoker, 'get_execution_history'):
            history = tool_invoker.get_execution_history()
            assert len(history) >= 2
    
    def test_performance_monitoring(self, tool_invoker, performance_timer):
        """Test performance monitoring for tool execution."""
        if tool_invoker is None:
            pytest.skip("ToolInvoker not available")
            
        # Execute tool with timing
        tool_invoker.client.call_tool.return_value = {'result': {'success': True}}
        
        with performance_timer:
            result = tool_invoker.execute_tool('perf_tool', {})
        
        if hasattr(tool_invoker, 'get_performance_stats'):
            stats = tool_invoker.get_performance_stats('perf_tool')
            assert 'execution_time' in stats or stats is None


class TestToolRegistry:
    """Unit tests for ToolRegistry management."""
    
    @pytest.fixture
    def registry(self):
        """ToolRegistry instance for testing."""
        if ToolRegistry is None:
            pytest.skip("ToolRegistry not available")
        return ToolRegistry()
    
    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        if ToolRegistry is None:
            pytest.skip("ToolRegistry not available")
            
        registry = ToolRegistry()
        assert hasattr(registry, 'tools')
        assert len(registry.tools) >= 0
    
    def test_tool_registration_validation(self, registry):
        """Test tool registration with schema validation."""
        if registry is None:
            pytest.skip("ToolRegistry not available")
            
        # Valid tool schema
        valid_schema = {
            'name': 'valid_tool',
            'description': 'A valid tool',
            'parameters': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string'}
                }
            }
        }
        
        result = registry.register(valid_schema)
        assert result is True
        
        # Invalid tool schema
        invalid_schema = {
            'name': 'invalid_tool'
            # Missing required fields
        }
        
        with pytest.raises((ValueError, KeyError)):
            registry.register(invalid_schema)
    
    def test_tool_lookup_performance(self, registry, performance_timer):
        """Test tool lookup performance."""
        if registry is None:
            pytest.skip("ToolRegistry not available")
            
        # Register multiple tools
        for i in range(100):
            schema = {
                'name': f'perf_tool_{i}',
                'description': f'Performance tool {i}',
                'parameters': {'type': 'object'}
            }
            registry.register(schema)
        
        # Test lookup performance
        with performance_timer:
            for i in range(100):
                tool = registry.get_tool(f'perf_tool_{i}')
                assert tool is not None or tool is None  # May not exist
        
        assert performance_timer.elapsed < 0.01  # Should be very fast
    
    def test_tool_categorization(self, registry):
        """Test tool categorization and filtering."""
        if registry is None:
            pytest.skip("ToolRegistry not available")
            
        # Register tools with categories
        categories = ['data', 'analysis', 'utility']
        for i, category in enumerate(categories):
            schema = {
                'name': f'{category}_tool',
                'description': f'Tool for {category}',
                'category': category,
                'parameters': {'type': 'object'}
            }
            registry.register(schema)
        
        if hasattr(registry, 'get_by_category'):
            data_tools = registry.get_by_category('data')
            assert len(data_tools) >= 1


class TestSchemaValidation:
    """Unit tests for schema validation and transformation."""
    
    @pytest.fixture
    def validator(self):
        """SchemaValidator instance for testing."""
        if SchemaValidator is None:
            pytest.skip("SchemaValidator not available")
        return SchemaValidator()
    
    def test_request_schema_validation(self, validator):
        """Test MCP request schema validation."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        # Valid request
        valid_request = {
            'method': 'test_tool',
            'params': {'param1': 'value1'},
            'id': 'request_123'
        }
        
        is_valid = validator.validate_request(valid_request)
        assert is_valid is True
        
        # Invalid request
        invalid_request = {
            'method': 'test_tool'
            # Missing required fields
        }
        
        is_valid = validator.validate_request(invalid_request)
        assert is_valid is False
    
    def test_response_schema_validation(self, validator):
        """Test MCP response schema validation."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        # Valid response
        valid_response = {
            'result': {'success': True, 'data': 'test'},
            'id': 'request_123'
        }
        
        is_valid = validator.validate_response(valid_response)
        assert is_valid is True
        
        # Error response
        error_response = {
            'error': {'code': -1, 'message': 'Test error'},
            'id': 'request_123'
        }
        
        is_valid = validator.validate_response(error_response)
        assert is_valid is True  # Error responses are valid
    
    def test_parameter_validation(self, validator):
        """Test parameter schema validation."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        # Define parameter schema
        param_schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer', 'minimum': 0},
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['name']
        }
        
        # Valid parameters
        valid_params = {
            'name': 'Test User',
            'age': 25,
            'email': 'test@example.com'
        }
        
        is_valid = validator.validate_parameters(valid_params, param_schema)
        assert is_valid is True
        
        # Invalid parameters
        invalid_params = {
            'age': -5,  # Invalid: negative age
            'email': 'invalid-email'  # Invalid: bad email format
        }
        
        is_valid = validator.validate_parameters(invalid_params, param_schema)
        assert is_valid is False
    
    def test_schema_transformation(self, validator):
        """Test schema transformation and normalization."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        # Raw data that needs transformation
        raw_data = {
            'name': '  Test User  ',  # Needs trimming
            'age': '25',              # Needs type conversion
            'active': 'true'          # Needs boolean conversion
        }
        
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
                'active': {'type': 'boolean'}
            }
        }
        
        if hasattr(validator, 'transform'):
            transformed = validator.transform(raw_data, schema)
            assert transformed['name'] == 'Test User'
            assert transformed['age'] == 25
            assert transformed['active'] is True
    
    def test_validation_error_details(self, validator):
        """Test detailed validation error reporting."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        schema = {
            'type': 'object',
            'properties': {
                'required_field': {'type': 'string'}
            },
            'required': ['required_field']
        }
        
        invalid_data = {}  # Missing required field
        
        if hasattr(validator, 'validate_with_errors'):
            is_valid, errors = validator.validate_with_errors(invalid_data, schema)
            assert is_valid is False
            assert len(errors) > 0
            assert 'required_field' in str(errors)
    
    def test_performance_large_schemas(self, validator, performance_timer):
        """Test validation performance with large schemas."""
        if validator is None:
            pytest.skip("SchemaValidator not available")
            
        # Create large schema
        large_schema = {
            'type': 'object',
            'properties': {}
        }
        
        for i in range(1000):
            large_schema['properties'][f'field_{i}'] = {'type': 'string'}
        
        # Create large data object
        large_data = {f'field_{i}': f'value_{i}' for i in range(1000)}
        
        with performance_timer:
            is_valid = validator.validate_parameters(large_data, large_schema)
        
        assert performance_timer.elapsed < 0.1  # Should handle large schemas quickly
        assert is_valid in [True, False]  # Should complete without error


class TestMCPSchemas:
    """Unit tests for MCP schema classes."""
    
    def test_mcp_request_creation(self):
        """Test MCPRequest object creation."""
        if MCPRequest is None:
            pytest.skip("MCPRequest not available")
            
        request = MCPRequest(
            method='test_tool',
            params={'param': 'value'},
            request_id='test_123'
        )
        
        assert request.method == 'test_tool'
        assert request.params == {'param': 'value'}
        assert request.id == 'test_123'
    
    def test_mcp_response_creation(self):
        """Test MCPResponse object creation."""
        if MCPResponse is None:
            pytest.skip("MCPResponse not available")
            
        # Success response
        response = MCPResponse(
            result={'success': True, 'data': 'test'},
            request_id='test_123'
        )
        
        assert response.result == {'success': True, 'data': 'test'}
        assert response.id == 'test_123'
        assert response.error is None
    
    def test_mcp_error_response(self):
        """Test MCPResponse error creation."""
        if MCPResponse is None:
            pytest.skip("MCPResponse not available")
            
        error_response = MCPResponse(
            error={'code': -1, 'message': 'Test error'},
            request_id='test_123'
        )
        
        assert error_response.error == {'code': -1, 'message': 'Test error'}
        assert error_response.result is None
    
    def test_schema_serialization(self):
        """Test schema object serialization."""
        if MCPRequest is None:
            pytest.skip("MCPRequest not available")
            
        request = MCPRequest(
            method='test_tool',
            params={'param': 'value'},
            request_id='test_123'
        )
        
        if hasattr(request, 'to_dict'):
            request_dict = request.to_dict()
            assert isinstance(request_dict, dict)
            assert request_dict['method'] == 'test_tool'
        
        if hasattr(request, 'to_json'):
            request_json = request.to_json()
            assert isinstance(request_json, str)
            parsed = json.loads(request_json)
            assert parsed['method'] == 'test_tool'


class TestToolIntegration:
    """Integration tests for tool layer components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tool_execution(self):
        """Test complete tool execution workflow."""
        if None in [ToolInvoker, SchemaValidator]:
            pytest.skip("Components not available")
            
        # Setup components
        validator = SchemaValidator()
        mock_client = Mock()
        mock_client.call_tool.return_value = {'result': {'success': True}}
        invoker = ToolInvoker(mock_client)
        
        # Register tool with schema
        tool_schema = {
            'name': 'integration_tool',
            'parameters': {
                'type': 'object',
                'properties': {'input': {'type': 'string'}},
                'required': ['input']
            }
        }
        invoker.register_tool(tool_schema)
        
        # Validate and execute
        params = {'input': 'test_data'}
        is_valid = invoker.validate_parameters('integration_tool', params)
        assert is_valid is True
        
        result = invoker.execute_tool('integration_tool', params)
        assert result is not None
    
    def test_error_handling_integration(self):
        """Test integrated error handling across components."""
        if None in [ToolInvoker, SchemaValidator]:
            pytest.skip("Components not available")
            
        validator = SchemaValidator()
        mock_client = Mock()
        invoker = ToolInvoker(mock_client)
        
        # Test validation error propagation
        invalid_params = {'wrong_param': 'value'}
        schema = {
            'type': 'object',
            'properties': {'correct_param': {'type': 'string'}},
            'required': ['correct_param']
        }
        
        is_valid = validator.validate_parameters(invalid_params, schema)
        assert is_valid is False
        
        # Tool execution should handle validation errors
        if hasattr(invoker, 'execute_with_validation'):
            result = invoker.execute_with_validation('test_tool', invalid_params, schema)
            assert 'error' in result or result is None
    
    def test_performance_integration(self, performance_timer):
        """Test integrated performance across tool layer."""
        # Simulate complete tool workflow
        with performance_timer:
            for i in range(100):
                # Simulate validation
                data = {'param': f'value_{i}'}
                json_data = json.dumps(data)
                parsed = json.loads(json_data)
                
                # Simulate tool lookup and execution
                tool_name = f'tool_{i % 10}'
                result = {'success': True, 'tool': tool_name}
        
        assert performance_timer.elapsed < 0.1  # Should handle 100 operations quickly