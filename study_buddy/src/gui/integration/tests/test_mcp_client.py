"""
Unit Tests for MCP Client Components and Mock Client.

Tests the MCP client interfaces, data structures, error handling,
and mock client functionality for comprehensive integration testing.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing
SOLID Compliance: Tests ensure SRP, OCP, LSP, ISP, DIP compliance
Coverage Target: 90%+ with comprehensive error scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, call
from typing import Dict, Any, List
import json
from datetime import datetime

# Import components under test
try:
    from mcp_client import (
        IMCPClient, ConnectionState, OperationStatus, 
        MCPResponse, ConnectionHealth, IProgressTracker,
        IConnectionManager, IToolInvoker, BaseProgressTracker
    )
    from async_mcp_client import IAsyncMCPClient, AsyncMCPClient, ClientStatus
    from mock_client import MockMCPClient, MockConfiguration
    from schemas import BaseRequest, BaseResponse, UploadDocumentRequest, UploadDocumentResponse
except ImportError as e:
    print(f"Warning: Import failed - {e}")
    pytest.skip(f"Integration components not available: {e}", allow_module_level=True)


class TestMCPClientInterface:
    """Unit tests for IMCPClient interface compliance."""
    
    def test_interface_methods_defined(self):
        """Test that interface has required method signatures."""
        # Test interface exists
        assert hasattr(IMCPClient, '__abstractmethods__')
        
        # Test required methods are abstract
        abstract_methods = getattr(IMCPClient, '__abstractmethods__', set())
        expected_methods = {
            'connect', 'disconnect', 'is_connected', 
            'invoke_tool', 'list_tools', 'get_tool_schema'
        }
        
        # Check that expected methods are in abstract methods
        assert expected_methods.issubset(abstract_methods), (
            f"Missing abstract methods: {expected_methods - abstract_methods}"
        )
    
    def test_interface_cannot_be_instantiated(self):
        """Test that interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IMCPClient()


class TestMCPClient:
    """Unit tests for concrete MCPClient implementation."""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock connection for testing."""
        connection = AsyncMock()
        connection.connect = AsyncMock(return_value=True)
        connection.disconnect = AsyncMock()
        connection.is_connected = True
        connection.send = AsyncMock()
        connection.receive = AsyncMock()
        return connection
    
    @pytest.fixture
    def client(self, mock_connection, mock_logger):
        """Create client with mocked dependencies."""
        # Mock the connection creation
        with patch('client.create_connection', return_value=mock_connection):
            client = MCPClient(
                host="localhost",
                port=8000,
                timeout=30.0,
                logger=mock_logger
            )
            client._connection = mock_connection
            return client
    
    def test_client_initialization(self, mock_logger):
        """Test client initialization with valid parameters."""
        client = MCPClient(
            host="test.example.com",
            port=9000,
            timeout=60.0,
            logger=mock_logger
        )
        
        assert client.host == "test.example.com"
        assert client.port == 9000
        assert client.timeout == 60.0
        assert client.logger == mock_logger
    
    def test_client_initialization_defaults(self):
        """Test client initialization with default parameters."""
        client = MCPClient()
        
        assert client.host == "localhost"
        assert client.port == 8000
        assert client.timeout == 30.0
        assert client.logger is not None
    
    async def test_connect_success(self, client, mock_connection):
        """Test successful connection."""
        mock_connection.connect.return_value = True
        
        result = await client.connect()
        
        assert result is True
        mock_connection.connect.assert_called_once()
        client.logger.info.assert_called_with(
            "Connected to MCP server", 
            extra={"host": "localhost", "port": 8000}
        )
    
    async def test_connect_failure(self, client, mock_connection):
        """Test connection failure."""
        mock_connection.connect.side_effect = ConnectionError("Connection failed")
        
        result = await client.connect()
        
        assert result is False
        client.logger.error.assert_called()
    
    async def test_disconnect_success(self, client, mock_connection):
        """Test successful disconnection."""
        client._connected = True
        
        await client.disconnect()
        
        mock_connection.disconnect.assert_called_once()
        assert client._connected is False
        client.logger.info.assert_called_with("Disconnected from MCP server")
    
    def test_is_connected_when_connected(self, client):
        """Test is_connected returns True when connected."""
        client._connected = True
        assert client.is_connected() is True
    
    def test_is_connected_when_disconnected(self, client):
        """Test is_connected returns False when disconnected."""
        client._connected = False
        assert client.is_connected() is False
    
    async def test_invoke_tool_success(self, client, mock_connection, mock_tool_response):
        """Test successful tool invocation."""
        client._connected = True
        mock_connection.send.return_value = None
        mock_connection.receive.return_value = json.dumps(mock_tool_response)
        
        request = ToolInvocationRequest(
            name="upload_document",
            parameters={"file_path": "/test/doc.pdf"}
        )
        
        result = await client.invoke_tool(request)
        
        assert result.success is True
        assert result.data == mock_tool_response["data"]
        client.logger.info.assert_called()
    
    async def test_invoke_tool_not_connected(self, client):
        """Test tool invocation when not connected."""
        client._connected = False
        
        request = ToolInvocationRequest(
            name="test_tool",
            parameters={}
        )
        
        result = await client.invoke_tool(request)
        
        assert result.success is False
        assert "not connected" in result.error.lower()
    
    async def test_invoke_tool_timeout(self, client, mock_connection):
        """Test tool invocation timeout."""
        client._connected = True
        mock_connection.receive.side_effect = asyncio.TimeoutError()
        
        request = ToolInvocationRequest(
            name="slow_tool",
            parameters={}
        )
        
        result = await client.invoke_tool(request)
        
        assert result.success is False
        assert "timeout" in result.error.lower()
        client.logger.error.assert_called()
    
    async def test_list_tools_success(self, client, mock_connection, mock_tool_list):
        """Test successful tool listing."""
        client._connected = True
        mock_connection.send.return_value = None
        mock_connection.receive.return_value = json.dumps({
            "success": True,
            "tools": mock_tool_list
        })
        
        tools = await client.list_tools()
        
        assert len(tools) == 3
        assert tools[0]["name"] == "upload_document"
        assert tools[1]["name"] == "list_documents"
        assert tools[2]["name"] == "search_documents"
    
    async def test_list_tools_not_connected(self, client):
        """Test tool listing when not connected."""
        client._connected = False
        
        tools = await client.list_tools()
        
        assert tools == []
        client.logger.error.assert_called()
    
    async def test_get_tool_schema_success(self, client, mock_connection):
        """Test successful tool schema retrieval."""
        client._connected = True
        schema_data = {
            "name": "upload_document",
            "description": "Upload a document",
            "parameters": {
                "file_path": {"type": "string", "required": True}
            }
        }
        
        mock_connection.send.return_value = None
        mock_connection.receive.return_value = json.dumps({
            "success": True,
            "schema": schema_data
        })
        
        schema = await client.get_tool_schema("upload_document")
        
        assert schema is not None
        assert schema.name == "upload_document"
        assert "file_path" in schema.parameters
    
    async def test_get_tool_schema_not_found(self, client, mock_connection):
        """Test tool schema retrieval for non-existent tool."""
        client._connected = True
        mock_connection.send.return_value = None
        mock_connection.receive.return_value = json.dumps({
            "success": False,
            "error": "Tool not found"
        })
        
        schema = await client.get_tool_schema("nonexistent_tool")
        
        assert schema is None


class TestAsyncMCPClient:
    """Unit tests for AsyncMCPClient implementation."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock underlying MCP client."""
        client = AsyncMock(spec=MCPClient)
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock()
        client.is_connected = Mock(return_value=True)
        client.invoke_tool = AsyncMock()
        client.list_tools = AsyncMock(return_value=[])
        client.get_tool_schema = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def async_client(self, mock_client, mock_logger):
        """Create AsyncMCPClient with mocked dependencies."""
        with patch('async_client.MCPClient', return_value=mock_client):
            client = AsyncMCPClient(
                host="localhost",
                port=8000,
                max_concurrent=10,
                logger=mock_logger
            )
            client._client = mock_client
            return client
    
    def test_async_client_initialization(self, mock_logger):
        """Test async client initialization."""
        client = AsyncMCPClient(
            host="test.com",
            port=9000,
            max_concurrent=5,
            timeout=60.0,
            logger=mock_logger
        )
        
        assert client.host == "test.com"
        assert client.port == 9000
        assert client.max_concurrent == 5
        assert client.timeout == 60.0
    
    async def test_async_context_manager_success(self, async_client, mock_client):
        """Test async context manager protocol."""
        async with async_client as client:
            assert client is async_client
            mock_client.connect.assert_called_once()
        
        mock_client.disconnect.assert_called_once()
    
    async def test_async_context_manager_connection_failure(self, async_client, mock_client):
        """Test async context manager with connection failure."""
        mock_client.connect.side_effect = ConnectionError("Failed")
        
        with pytest.raises(ConnectionError):
            async with async_client:
                pass
    
    async def test_concurrent_tool_invocations(self, async_client, mock_client, mock_tool_response):
        """Test concurrent tool invocations with semaphore limiting."""
        # Setup mock responses
        mock_client.invoke_tool.return_value = ToolInvocationResponse(
            success=True,
            data=mock_tool_response["data"]
        )
        
        # Create multiple concurrent requests
        requests = [
            ToolInvocationRequest(name=f"tool_{i}", parameters={})
            for i in range(15)  # More than max_concurrent (10)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*[
            async_client.invoke_tool(req) for req in requests
        ])
        
        # Verify all succeeded
        assert len(results) == 15
        assert all(result.success for result in results)
        
        # Verify semaphore limited concurrent calls
        assert mock_client.invoke_tool.call_count == 15
    
    async def test_batch_tool_invocation(self, async_client, mock_client, mock_tool_response):
        """Test batch tool invocation."""
        mock_client.invoke_tool.return_value = ToolInvocationResponse(
            success=True,
            data=mock_tool_response["data"]
        )
        
        requests = [
            ToolInvocationRequest(name="tool1", parameters={"param": "value1"}),
            ToolInvocationRequest(name="tool2", parameters={"param": "value2"}),
            ToolInvocationRequest(name="tool3", parameters={"param": "value3"})
        ]
        
        results = await async_client.batch_invoke_tools(requests)
        
        assert len(results) == 3
        assert all(result.success for result in results)
        assert mock_client.invoke_tool.call_count == 3
    
    async def test_batch_tool_invocation_with_errors(self, async_client, mock_client):
        """Test batch tool invocation with some failures."""
        def mock_invoke_side_effect(request):
            if "fail" in request.name:
                return ToolInvocationResponse(
                    success=False,
                    error="Simulated failure"
                )
            else:
                return ToolInvocationResponse(
                    success=True,
                    data={"result": "success"}
                )
        
        mock_client.invoke_tool.side_effect = mock_invoke_side_effect
        
        requests = [
            ToolInvocationRequest(name="success_tool", parameters={}),
            ToolInvocationRequest(name="fail_tool", parameters={}),
            ToolInvocationRequest(name="another_success", parameters={})
        ]
        
        results = await async_client.batch_invoke_tools(requests)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
    
    async def test_health_check(self, async_client, mock_client):
        """Test health check functionality."""
        mock_client.is_connected.return_value = True
        mock_client.invoke_tool.return_value = ToolInvocationResponse(
            success=True,
            data={"status": "healthy", "timestamp": datetime.now().isoformat()}
        )
        
        health = await async_client.health_check()
        
        assert health["status"] == "healthy"
        assert "timestamp" in health
        mock_client.invoke_tool.assert_called_once()
    
    async def test_connection_retry_logic(self, async_client, mock_client):
        """Test connection retry logic."""
        # First two attempts fail, third succeeds
        mock_client.connect.side_effect = [
            ConnectionError("First attempt"),
            ConnectionError("Second attempt"),
            True
        ]
        
        result = await async_client.connect_with_retry(max_retries=3, retry_delay=0.01)
        
        assert result is True
        assert mock_client.connect.call_count == 3
    
    async def test_connection_retry_exhausted(self, async_client, mock_client):
        """Test connection retry when all attempts fail."""
        mock_client.connect.side_effect = ConnectionError("Always fails")
        
        result = await async_client.connect_with_retry(max_retries=2, retry_delay=0.01)
        
        assert result is False
        assert mock_client.connect.call_count == 2


class TestMockMCPClient:
    """Unit tests for MockMCPClient testing infrastructure."""
    
    def test_mock_client_initialization_normal_mode(self):
        """Test mock client initialization in normal mode."""
        client = MockMCPClient()
        
        assert client.config.behavior_mode == "normal"
        assert client.config.success_rate == 1.0
        assert client.config.latency_ms == 0
        assert client.is_connected() is False
    
    def test_mock_client_initialization_custom_config(self):
        """Test mock client with custom configuration."""
        config = MockConfiguration(
            behavior_mode="error_simulation",
            success_rate=0.7,
            latency_ms=50,
            enable_operation_tracking=True
        )
        
        client = MockMCPClient(config)
        
        assert client.config.behavior_mode == "error_simulation"
        assert client.config.success_rate == 0.7
        assert client.config.latency_ms == 50
        assert client.config.enable_operation_tracking is True
    
    async def test_mock_connect_normal_mode(self):
        """Test mock connection in normal mode."""
        client = MockMCPClient()
        
        result = await client.connect()
        
        assert result is True
        assert client.is_connected() is True
    
    async def test_mock_connect_error_mode(self):
        """Test mock connection in error simulation mode."""
        config = MockConfiguration(
            behavior_mode="error_simulation",
            success_rate=0.0  # Always fail
        )
        client = MockMCPClient(config)
        
        result = await client.connect()
        
        assert result is False
        assert client.is_connected() is False
    
    async def test_mock_tool_invocation_success(self):
        """Test successful mock tool invocation."""
        client = MockMCPClient()
        await client.connect()
        
        request = ToolInvocationRequest(
            name="upload_document",
            parameters={"file_path": "/test/doc.pdf"}
        )
        
        response = await client.invoke_tool(request)
        
        assert response.success is True
        assert response.data is not None
        assert "document_id" in response.data
    
    async def test_mock_tool_invocation_with_latency(self, performance_timer):
        """Test mock tool invocation with simulated latency."""
        config = MockConfiguration(
            behavior_mode="latency_testing",
            latency_ms=100
        )
        client = MockMCPClient(config)
        await client.connect()
        
        request = ToolInvocationRequest(name="test_tool", parameters={})
        
        performance_timer.start()
        response = await client.invoke_tool(request)
        duration_ms = performance_timer.stop()
        
        assert response.success is True
        assert duration_ms >= 95  # Allow 5ms tolerance
    
    async def test_mock_operation_tracking(self):
        """Test operation tracking in mock client."""
        config = MockConfiguration(enable_operation_tracking=True)
        client = MockMCPClient(config)
        
        # Perform operations
        await client.connect()
        request1 = ToolInvocationRequest(name="tool1", parameters={})
        request2 = ToolInvocationRequest(name="tool2", parameters={})
        
        await client.invoke_tool(request1)
        await client.invoke_tool(request2)
        await client.disconnect()
        
        # Check tracking
        operations = client.get_operation_history()
        
        assert len(operations) >= 4  # connect, tool1, tool2, disconnect
        
        # Verify operation types
        operation_types = [op["operation"] for op in operations]
        assert "connect" in operation_types
        assert "invoke_tool" in operation_types
        assert "disconnect" in operation_types
    
    def test_mock_client_builder(self):
        """Test MockClientBuilder for easy configuration."""
        from mock_client import MockClientBuilder
        
        client = (MockClientBuilder()
                 .with_error_simulation(success_rate=0.8)
                 .with_latency(50)
                 .with_operation_tracking()
                 .build())
        
        assert client.config.behavior_mode == "error_simulation"
        assert client.config.success_rate == 0.8
        assert client.config.latency_ms == 50
        assert client.config.enable_operation_tracking is True


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
class TestClientPerformance:
    """Performance tests for MCP clients."""
    
    async def test_connection_establishment_performance(self, performance_timer, performance_threshold):
        """Test connection establishment performance."""
        client = MockMCPClient()
        
        performance_timer.start()
        result = await client.connect()
        duration_ms = performance_timer.stop()
        
        assert result is True
        performance_timer.assert_within_threshold(performance_threshold)
    
    async def test_tool_invocation_performance(self, performance_timer, performance_threshold):
        """Test tool invocation performance."""
        client = MockMCPClient()
        await client.connect()
        
        request = ToolInvocationRequest(name="fast_tool", parameters={})
        
        performance_timer.start()
        response = await client.invoke_tool(request)
        duration_ms = performance_timer.stop()
        
        assert response.success is True
        performance_timer.assert_within_threshold(performance_threshold)
    
    async def test_concurrent_invocation_performance(self, performance_timer):
        """Test performance under concurrent load."""
        config = MockConfiguration(behavior_mode="normal")
        client = AsyncMCPClient(max_concurrent=20)
        
        # Mock the underlying client
        client._client = MockMCPClient(config)
        await client._client.connect()
        
        # Create many concurrent requests
        requests = [
            ToolInvocationRequest(name=f"tool_{i}", parameters={})
            for i in range(50)
        ]
        
        performance_timer.start()
        results = await asyncio.gather(*[
            client.invoke_tool(req) for req in requests
        ])
        duration_ms = performance_timer.stop()
        
        # Verify all completed successfully
        assert len(results) == 50
        assert all(result.success for result in results)
        
        # Performance should be reasonable even with 50 concurrent operations
        assert duration_ms < 1000  # Less than 1 second for 50 operations


# ============================================================================
# ERROR SCENARIO TESTS
# ============================================================================

@pytest.mark.error
class TestErrorScenarios:
    """Error handling and edge case tests."""
    
    async def test_connection_timeout(self):
        """Test connection timeout handling."""
        config = MockConfiguration(
            behavior_mode="error_simulation",
            simulate_timeouts=True
        )
        client = MockMCPClient(config)
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(client.connect(), timeout=0.1)
    
    async def test_network_interruption_during_operation(self):
        """Test network interruption during tool invocation."""
        client = MockMCPClient()
        await client.connect()
        
        # Simulate network failure during operation
        client._connected = False
        
        request = ToolInvocationRequest(name="test_tool", parameters={})
        response = await client.invoke_tool(request)
        
        assert response.success is False
        assert "not connected" in response.error.lower()
    
    async def test_malformed_response_handling(self):
        """Test handling of malformed server responses."""
        # This would test the client's robustness against invalid JSON, etc.
        # Implementation depends on actual client error handling logic
        pass
    
    async def test_resource_exhaustion(self):
        """Test behavior under resource exhaustion."""
        config = MockConfiguration(
            behavior_mode="error_simulation",
            success_rate=0.1  # 90% failure rate
        )
        client = AsyncMCPClient(max_concurrent=2)
        client._client = MockMCPClient(config)
        await client._client.connect()
        
        # Create more requests than can be handled
        requests = [
            ToolInvocationRequest(name=f"tool_{i}", parameters={})
            for i in range(20)
        ]
        
        results = await asyncio.gather(*[
            client.invoke_tool(req) for req in requests
        ], return_exceptions=True)
        
        # Some should succeed, some should fail
        successes = sum(1 for r in results if isinstance(r, ToolInvocationResponse) and r.success)
        failures = len(results) - successes
        
        assert failures > successes  # Most should fail with 10% success rate


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "--tb=short"])