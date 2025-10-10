"""
Connection Lifecycle Integration Tests

Tests for MCP client connection establishment, management,
and termination with real MCP servers.

Test Coverage:
- Connection establishment and handshake
- Connection persistence and keep-alive
- Graceful disconnection and cleanup
- Connection pooling and reuse
- Timeout and error handling
- Reconnection and recovery scenarios
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from contextlib import asynccontextmanager

from . import CONNECTION_TESTS, REQUIRES_SERVER, INTEGRATION_TEST
from .conftest import IntegrationTestBase, measure_performance, temporary_server_failure


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_server
class TestConnectionLifecycle(IntegrationTestBase):
    """Test suite for connection lifecycle operations"""
    
    async def test_basic_connection_establishment(self, server_config):
        """Test basic connection to MCP server"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        
        # Test connection establishment
        start_time = time.time()
        await client.connect()
        connection_time = time.time() - start_time
        
        # Verify connection within performance requirements
        assert connection_time < 3.0, f"Connection took {connection_time}s, expected < 3s"
        assert client.is_connected(), "Client should be connected"
        
        # Test graceful disconnection
        await client.disconnect()
        assert not client.is_connected(), "Client should be disconnected"
        
    async def test_connection_with_invalid_server(self):
        """Test connection failure handling"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Configure client with invalid server
        invalid_config = {
            "host": "localhost",
            "port": 9999,  # Non-existent server
            "timeout": 2,
            "retry_attempts": 1
        }
        
        client = MCPClient(invalid_config)
        
        # Test that connection fails appropriately
        with pytest.raises(ConnectionError):
            await client.connect()
            
        assert not client.is_connected(), "Client should not be connected"
        
    @measure_performance
    async def test_multiple_connections(self, server_config, performance_config):
        """Test multiple concurrent connections"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        num_connections = performance_config["concurrent_connections"]
        clients = []
        
        # Create multiple clients
        for i in range(num_connections):
            config = server_config.copy()
            config["client_id"] = f"test_client_{i}"
            clients.append(MCPClient(config))
            
        # Connect all clients concurrently
        start_time = time.time()
        connection_tasks = [client.connect() for client in clients]
        await asyncio.gather(*connection_tasks)
        total_time = time.time() - start_time
        
        # Verify all connections established
        assert all(client.is_connected() for client in clients), "All clients should be connected"
        
        # Verify performance within requirements
        avg_time_per_connection = total_time / num_connections
        assert avg_time_per_connection < 3.0, f"Average connection time {avg_time_per_connection}s exceeds limit"
        
        # Clean up
        disconnect_tasks = [client.disconnect() for client in clients]
        await asyncio.gather(*disconnect_tasks)
        
    async def test_connection_persistence(self, mcp_client):
        """Test that connections remain stable over time"""
        # Keep connection alive for extended period
        test_duration = 10  # seconds
        check_interval = 1
        
        start_time = time.time()
        while time.time() - start_time < test_duration:
            assert mcp_client.is_connected(), "Connection should remain stable"
            
            # Send keep-alive if supported
            if hasattr(mcp_client, 'ping'):
                response = await mcp_client.ping()
                assert response["status"] == "ok", "Keep-alive should succeed"
                
            await asyncio.sleep(check_interval)
            
    async def test_reconnection_after_server_restart(self, server_config):
        """Test automatic reconnection after server restart"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        await client.connect()
        
        assert client.is_connected(), "Initial connection should succeed"
        
        # Simulate server restart using context manager
        async with temporary_server_failure(self.test_server, duration=2.0):
            # Wait for client to detect disconnection
            await asyncio.sleep(1)
            
            # Client should detect disconnection
            if hasattr(client, 'connection_status'):
                status = await client.connection_status()
                assert status in ["disconnected", "reconnecting"], "Client should detect server failure"
                
        # Give client time to reconnect
        await asyncio.sleep(3)
        
        # Verify reconnection (if auto-reconnect is implemented)
        if hasattr(client, 'auto_reconnect') and client.auto_reconnect:
            assert client.is_connected(), "Client should auto-reconnect after server restart"
        
        await client.disconnect()
        
    async def test_connection_timeout_configuration(self, server_config):
        """Test connection timeout behavior"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        # Configure short timeout
        config = server_config.copy()
        config["timeout"] = 1  # 1 second timeout
        
        client = MCPClient(config)
        
        # Mock slow server response by connecting to busy port
        config["port"] = 22  # SSH port (likely to timeout)
        
        start_time = time.time()
        with pytest.raises((ConnectionError, TimeoutError)):
            await client.connect()
            
        elapsed = time.time() - start_time
        
        # Verify timeout was respected (with small margin)
        assert elapsed < config["timeout"] + 1, f"Timeout took {elapsed}s, expected ~{config['timeout']}s"
        
    async def test_graceful_shutdown_during_operations(self, mcp_client, sample_tool_calls):
        """Test graceful shutdown while operations are in progress"""
        # Start multiple concurrent operations
        tasks = []
        for tool_call in sample_tool_calls[:3]:  # Use first 3 calls
            if hasattr(mcp_client, 'call_tool'):
                task = asyncio.create_task(
                    mcp_client.call_tool(tool_call["tool"], tool_call["args"])
                )
                tasks.append(task)
                
        # Allow operations to start
        await asyncio.sleep(0.5)
        
        # Initiate graceful shutdown
        if hasattr(mcp_client, 'graceful_shutdown'):
            await mcp_client.graceful_shutdown(timeout=5)
        else:
            await mcp_client.disconnect()
            
        # Verify operations were handled appropriately
        # (either completed or cancelled gracefully)
        for task in tasks:
            assert task.done(), "All operations should be completed or cancelled"
            
    async def test_connection_pool_management(self, server_config, performance_config):
        """Test connection pooling and reuse"""
        try:
            from gui.integration.core.connection_pool import ConnectionPool
        except ImportError:
            pytest.skip("Connection pool not yet implemented")
            
        pool_config = {
            **server_config,
            "pool_size": 5,
            "max_connections": 10,
            "connection_timeout": 30
        }
        
        pool = ConnectionPool(pool_config)
        await pool.initialize()
        
        # Test acquiring connections from pool
        connections = []
        for i in range(pool_config["pool_size"]):
            conn = await pool.acquire_connection()
            assert conn is not None, f"Should acquire connection {i}"
            connections.append(conn)
            
        # Test connection reuse
        pool.release_connection(connections[0])
        reused_conn = await pool.acquire_connection()
        assert reused_conn == connections[0], "Connection should be reused from pool"
        
        # Clean up
        for conn in connections[1:]:
            pool.release_connection(conn)
        pool.release_connection(reused_conn)
        
        await pool.shutdown()
        
    async def test_connection_error_recovery(self, server_config, error_scenarios):
        """Test recovery from various connection errors"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        client = MCPClient(server_config)
        
        for scenario in error_scenarios:
            if scenario["type"] == "server_disconnect":
                await client.connect()
                
                # Simulate server disconnect
                if hasattr(self.test_server, 'force_disconnect_client'):
                    await self.test_server.force_disconnect_client(client.client_id)
                    
                # Test error detection and recovery
                await asyncio.sleep(1)
                
                if hasattr(client, 'connection_status'):
                    status = await client.connection_status()
                    assert status != "connected", "Client should detect disconnection"
                    
                # Test manual reconnection
                if not client.is_connected():
                    await client.connect()
                    assert client.is_connected(), "Manual reconnection should succeed"
                    
                await client.disconnect()
                
    @pytest.mark.slow
    async def test_long_running_connection_stability(self, mcp_client):
        """Test connection stability over extended period"""
        # Run for longer duration to test stability
        test_duration = 60  # 1 minute for slow tests
        check_interval = 5
        operation_interval = 10
        
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < test_duration:
            # Verify connection is still active
            assert mcp_client.is_connected(), "Connection should remain stable"
            
            # Perform periodic operations to keep connection active
            if (time.time() - start_time) // operation_interval > operation_count:
                if hasattr(mcp_client, 'call_tool'):
                    result = await mcp_client.call_tool("echo", {"message": f"stability_test_{operation_count}"})
                    assert result is not None, "Operations should continue working"
                operation_count += 1
                
            await asyncio.sleep(check_interval)
            
        # Verify final state
        assert mcp_client.is_connected(), "Connection should still be active after long run"


@pytest.mark.asyncio 
@pytest.mark.integration
@pytest.mark.load
class TestConnectionPerformance(IntegrationTestBase):
    """Performance-focused connection tests"""
    
    @measure_performance
    async def test_connection_throughput(self, server_config, performance_config):
        """Test connection establishment throughput"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        target_ops = performance_config["target_ops_per_second"]
        test_duration = 10  # seconds
        
        connection_count = 0
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            client = MCPClient(server_config)
            await client.connect()
            await client.disconnect()
            connection_count += 1
            
            # Brief pause to prevent overwhelming
            await asyncio.sleep(0.01)
            
        elapsed_time = time.time() - start_time
        ops_per_second = connection_count / elapsed_time
        
        # Log performance metrics
        print(f"\nConnection Performance:")
        print(f"  Connections: {connection_count}")
        print(f"  Duration: {elapsed_time:.2f}s") 
        print(f"  Ops/sec: {ops_per_second:.2f}")
        
        # Performance validation
        assert ops_per_second >= target_ops * 0.5, f"Performance below 50% of target: {ops_per_second} < {target_ops * 0.5}"
        
    @measure_performance
    async def test_memory_usage_under_load(self, server_config, performance_config):
        """Test memory usage with multiple connections"""
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
            
        import psutil
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many connections
        clients = []
        num_connections = performance_config["concurrent_connections"] * 2
        
        for i in range(num_connections):
            client = MCPClient(server_config)
            await client.connect()
            clients.append(client)
            
            # Check memory periodically
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_per_connection = (current_memory - baseline_memory) / (i + 1)
                
                # Ensure reasonable memory usage per connection
                assert memory_per_connection < 5.0, f"Memory per connection too high: {memory_per_connection:.2f}MB"
                
        # Final memory check
        peak_memory = process.memory_info().rss / 1024 / 1024
        total_memory_used = peak_memory - baseline_memory
        
        print(f"\nMemory Usage:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Peak: {peak_memory:.2f}MB")
        print(f"  Used: {total_memory_used:.2f}MB")
        print(f"  Per connection: {total_memory_used / num_connections:.2f}MB")
        
        # Verify memory limits
        assert total_memory_used < performance_config["memory_threshold_mb"], f"Memory usage too high: {total_memory_used}MB"
        
        # Clean up
        for client in clients:
            await client.disconnect()
            
        # Verify memory cleanup
        await asyncio.sleep(1)  # Allow cleanup
        final_memory = process.memory_info().rss / 1024 / 1024
        cleanup_threshold = baseline_memory + 10  # Allow 10MB overhead
        
        assert final_memory < cleanup_threshold, f"Memory not properly cleaned up: {final_memory:.2f}MB"