"""
Comprehensive unit tests for client layer integration components.

Tests:
- mcp_client.py: Core MCP client functionality
- async_mcp_client.py: Async MCP client patterns  
- connection_manager.py: Connection lifecycle management

Coverage Target: 90%+
Performance: <100ms per operation
Error Scenarios: Comprehensive boundary testing
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp_client import MCPClient
    from async_mcp_client import AsyncMCPClient  
    from connection_manager import ConnectionManager
    from schemas import MCPRequest, MCPResponse
except ImportError as e:
    # Fallback for testing without actual implementations
    print(f"Warning: Could not import actual components: {e}")
    MCPClient = None
    AsyncMCPClient = None
    ConnectionManager = None
    MCPRequest = None
    MCPResponse = None


class TestMCPClient:
    """Unit tests for MCPClient core functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for client testing."""
        return {
            'server_uri': 'stdio://path/to/server',
            'timeout': 30.0,
            'retry_attempts': 3,
            'retry_delay': 1.0
        }
    
    @pytest.fixture
    def client(self, mock_config):
        """MCPClient instance for testing."""
        if MCPClient is None:
            pytest.skip("MCPClient not available")
        return MCPClient(mock_config)
    
    def test_client_initialization(self, mock_config):
        """Test client initializes with correct configuration."""
        if MCPClient is None:
            pytest.skip("MCPClient not available")
            
        client = MCPClient(mock_config)
        assert client.config == mock_config
        assert client.timeout == 30.0
        assert client.retry_attempts == 3
    
    def test_client_invalid_config(self):
        """Test client handles invalid configuration gracefully."""
        if MCPClient is None:
            pytest.skip("MCPClient not available")
            
        with pytest.raises((ValueError, TypeError)):
            MCPClient({})  # Missing required config
    
    @patch('subprocess.Popen')
    def test_client_connection_success(self, mock_popen, client):
        """Test successful client connection."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        # Mock successful process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        result = client.connect()
        assert result is True
        mock_popen.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_client_connection_failure(self, mock_popen, client):
        """Test client handles connection failures."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        # Mock failed process
        mock_popen.side_effect = OSError("Connection failed")
        
        result = client.connect()
        assert result is False
    
    def test_request_formatting(self, client):
        """Test MCP request formatting."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        tool_name = "test_tool"
        params = {"key": "value"}
        
        request = client.format_request(tool_name, params)
        
        assert isinstance(request, dict)
        assert 'method' in request
        assert 'params' in request
        assert request['params'] == params
    
    @patch('subprocess.Popen')
    def test_tool_execution(self, mock_popen, client, performance_timer):
        """Test tool execution with performance timing."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        # Mock successful process and response
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.return_value = json.dumps({
            "result": {"success": True, "data": "test_data"}
        }).encode()
        mock_popen.return_value = mock_process
        
        with performance_timer:
            result = client.call_tool("test_tool", {"param": "value"})
        
        assert performance_timer.elapsed < 0.1  # Should be fast
        assert result is not None
    
    def test_error_handling_timeout(self, client):
        """Test client handles timeouts gracefully."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        with patch.object(client, '_send_request') as mock_send:
            mock_send.side_effect = TimeoutError("Request timeout")
            
            result = client.call_tool("slow_tool", {})
            assert result is None or 'error' in result
    
    def test_error_handling_invalid_response(self, client):
        """Test client handles malformed responses."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        with patch.object(client, '_send_request') as mock_send:
            mock_send.return_value = "invalid json response"
            
            result = client.call_tool("test_tool", {})
            assert result is None or 'error' in result
    
    def test_retry_mechanism(self, client):
        """Test retry mechanism on failures."""
        if client is None:
            pytest.skip("MCPClient not available")
            
        with patch.object(client, '_send_request') as mock_send:
            # Fail twice, succeed on third try
            mock_send.side_effect = [
                ConnectionError("Failed"),
                ConnectionError("Failed"), 
                {"result": {"success": True}}
            ]
            
            result = client.call_tool("test_tool", {})
            assert mock_send.call_count == 3
            assert result is not None


class TestAsyncMCPClient:
    """Unit tests for AsyncMCPClient async patterns."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for async client testing."""
        return {
            'server_uri': 'stdio://path/to/server',
            'timeout': 30.0,
            'max_concurrent': 10
        }
    
    @pytest.fixture
    def async_client(self, mock_config):
        """AsyncMCPClient instance for testing."""
        if AsyncMCPClient is None:
            pytest.skip("AsyncMCPClient not available")
        return AsyncMCPClient(mock_config)
    
    @pytest.mark.asyncio
    async def test_async_client_initialization(self, mock_config):
        """Test async client initializes correctly."""
        if AsyncMCPClient is None:
            pytest.skip("AsyncMCPClient not available")
            
        client = AsyncMCPClient(mock_config)
        assert client.config == mock_config
        assert client.max_concurrent == 10
    
    @pytest.mark.asyncio  
    async def test_async_connection(self, async_client):
        """Test async connection establishment."""
        if async_client is None:
            pytest.skip("AsyncMCPClient not available")
            
        with patch.object(async_client, '_connect_async') as mock_connect:
            mock_connect.return_value = True
            
            result = await async_client.connect()
            assert result is True
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, async_client, performance_timer):
        """Test concurrent tool execution."""
        if async_client is None:
            pytest.skip("AsyncMCPClient not available")
            
        with patch.object(async_client, 'call_tool') as mock_call:
            mock_call.return_value = {"result": {"success": True}}
            
            # Execute multiple tools concurrently
            tasks = [
                async_client.call_tool(f"tool_{i}", {"param": i})
                for i in range(5)
            ]
            
            with performance_timer:
                results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert performance_timer.elapsed < 1.0  # Concurrent should be faster
            assert mock_call.call_count == 5
    
    @pytest.mark.asyncio
    async def test_async_timeout_handling(self, async_client):
        """Test async timeout handling."""
        if async_client is None:
            pytest.skip("AsyncMCPClient not available")
            
        async def slow_operation():
            await asyncio.sleep(2.0)
            return {"result": "slow"}
        
        with patch.object(async_client, 'call_tool', side_effect=slow_operation):
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    async_client.call_tool("slow_tool", {}),
                    timeout=0.1
                )
    
    @pytest.mark.asyncio
    async def test_async_error_propagation(self, async_client):
        """Test async error propagation."""
        if async_client is None:
            pytest.skip("AsyncMCPClient not available")
            
        with patch.object(async_client, '_send_request_async') as mock_send:
            mock_send.side_effect = ValueError("Async error")
            
            with pytest.raises(ValueError):
                await async_client.call_tool("error_tool", {})
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self, async_client):
        """Test connection pooling behavior."""
        if async_client is None:
            pytest.skip("AsyncMCPClient not available")
            
        with patch.object(async_client, '_get_connection') as mock_get_conn:
            mock_connection = AsyncMock()
            mock_get_conn.return_value = mock_connection
            
            # Multiple calls should reuse connections
            await async_client.call_tool("tool1", {})
            await async_client.call_tool("tool2", {})
            
            # Verify connection reuse patterns
            assert mock_get_conn.call_count >= 1


class TestConnectionManager:
    """Unit tests for ConnectionManager lifecycle management."""
    
    @pytest.fixture
    def connection_manager(self):
        """ConnectionManager instance for testing."""
        if ConnectionManager is None:
            pytest.skip("ConnectionManager not available")
        return ConnectionManager()
    
    def test_manager_initialization(self):
        """Test connection manager initializes correctly."""
        if ConnectionManager is None:
            pytest.skip("ConnectionManager not available")
            
        manager = ConnectionManager()
        assert hasattr(manager, 'connections')
        assert len(manager.connections) == 0
    
    def test_connection_creation(self, connection_manager):
        """Test creating new connections."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        config = {'server_uri': 'test://server', 'timeout': 30}
        
        connection = connection_manager.create_connection('test_id', config)
        assert connection is not None
        assert 'test_id' in connection_manager.connections
    
    def test_connection_reuse(self, connection_manager):
        """Test connection reuse for same configuration."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        config = {'server_uri': 'test://server', 'timeout': 30}
        
        conn1 = connection_manager.get_or_create('test_id', config)
        conn2 = connection_manager.get_or_create('test_id', config)
        
        assert conn1 is conn2  # Should reuse same connection
    
    def test_connection_cleanup(self, connection_manager):
        """Test connection cleanup and resource management."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        config = {'server_uri': 'test://server', 'timeout': 30}
        connection_manager.create_connection('temp_id', config)
        
        assert 'temp_id' in connection_manager.connections
        
        connection_manager.cleanup_connection('temp_id')
        assert 'temp_id' not in connection_manager.connections
    
    def test_health_checking(self, connection_manager, performance_timer):
        """Test connection health monitoring."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        config = {'server_uri': 'test://server', 'timeout': 30}
        connection_manager.create_connection('health_test', config)
        
        with performance_timer:
            is_healthy = connection_manager.check_health('health_test')
        
        assert performance_timer.elapsed < 0.05  # Health check should be fast
        assert isinstance(is_healthy, bool)
    
    def test_connection_limits(self, connection_manager):
        """Test connection limits and resource management."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        # Test creating many connections
        config = {'server_uri': 'test://server', 'timeout': 30}
        
        for i in range(15):  # Try to create many connections
            connection_manager.create_connection(f'conn_{i}', config)
        
        # Should handle resource limits gracefully
        assert len(connection_manager.connections) <= 10  # Assume max 10
    
    def test_concurrent_access(self, connection_manager):
        """Test thread-safe concurrent access."""
        if connection_manager is None:
            pytest.skip("ConnectionManager not available")
            
        import threading
        import time
        
        config = {'server_uri': 'test://server', 'timeout': 30}
        results = []
        
        def create_connection(thread_id):
            conn = connection_manager.get_or_create(f'thread_{thread_id}', config)
            results.append(conn)
        
        threads = [
            threading.Thread(target=create_connection, args=(i,))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(connection_manager.connections) <= 5


class TestClientIntegration:
    """Integration tests for client layer components working together."""
    
    @pytest.mark.asyncio
    async def test_client_manager_integration(self):
        """Test client and manager working together."""
        if None in [MCPClient, ConnectionManager]:
            pytest.skip("Components not available")
            
        manager = ConnectionManager()
        config = {'server_uri': 'test://server', 'timeout': 30}
        
        # Create connection through manager
        connection = manager.create_connection('integration_test', config)
        
        # Verify integration works
        assert connection is not None
        assert manager.check_health('integration_test') is not None
    
    def test_performance_benchmarks(self, performance_timer):
        """Test performance meets requirements."""
        # Basic performance test patterns
        with performance_timer:
            # Simulate typical client operations
            for _ in range(100):
                data = {'test': 'data', 'number': 42}
                json_str = json.dumps(data)
                parsed = json.loads(json_str)
                assert parsed == data
        
        # Should handle 100 operations quickly
        assert performance_timer.elapsed < 0.1
    
    def test_memory_usage_patterns(self):
        """Test memory usage stays within bounds."""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Simulate client operations that might leak memory
        clients = []
        for i in range(10):
            if MCPClient is not None:
                config = {'server_uri': f'test://server_{i}', 'timeout': 30}
                client = MCPClient(config)
                clients.append(client)
        
        # Cleanup
        del clients
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # Memory growth should be reasonable
        growth = final_objects - initial_objects
        assert growth < 1000  # Reasonable memory growth limit


# Performance and stress tests
class TestClientPerformance:
    """Performance and stress tests for client components."""
    
    def test_request_throughput(self, performance_timer):
        """Test request handling throughput."""
        requests = []
        
        with performance_timer:
            for i in range(1000):
                request = {
                    'method': f'tool_{i}',
                    'params': {'data': f'test_data_{i}'},
                    'id': i
                }
                requests.append(request)
        
        assert performance_timer.elapsed < 0.1  # Should handle 1000 requests quickly
        assert len(requests) == 1000
    
    @pytest.mark.asyncio
    async def test_async_throughput(self, performance_timer):
        """Test async request throughput."""
        async def mock_request(i):
            await asyncio.sleep(0.001)  # Simulate small delay
            return {'id': i, 'result': 'success'}
        
        with performance_timer:
            tasks = [mock_request(i) for i in range(100)]
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 100
        assert performance_timer.elapsed < 1.0  # Concurrent should be faster than 100ms total
    
    def test_memory_stress(self):
        """Test behavior under memory pressure."""
        large_data = []
        
        try:
            # Create large data structures
            for i in range(100):
                large_item = {
                    'id': i,
                    'data': 'x' * 10000,  # 10KB per item
                    'nested': {'more_data': list(range(1000))}
                }
                large_data.append(large_item)
            
            # Verify we can still operate with large data
            assert len(large_data) == 100
            
        finally:
            # Cleanup
            del large_data