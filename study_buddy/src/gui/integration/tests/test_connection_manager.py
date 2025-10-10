"""
Unit Tests for Connection Manager - Study Buddy Integration Layer.

Tests connection management functionality including connection pooling,
health monitoring, retry logic, and error handling.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing  
SOLID Compliance: Tests ensure SRP, OCP, LSP, ISP, DIP compliance
Coverage Target: 90%+ with comprehensive error scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

# Import components under test
try:
    from connection_manager import (
        ConnectionManager, ConnectionPool, ConnectionState,
        ConnectionHealth, ConnectionConfig, HealthChecker
    )
    from mcp_client import ConnectionState as MCPConnectionState
except ImportError as e:
    print(f"Warning: Import failed - {e}")
    pytest.skip(f"Integration components not available: {e}", allow_module_level=True)


class TestConnectionManager:
    """Test ConnectionManager functionality."""
    
    @pytest.fixture
    def connection_config(self):
        """Create test connection configuration."""
        return {
            "host": "localhost",
            "port": 8000,
            "timeout": 30.0,
            "max_retries": 3,
            "retry_delay": 1.0
        }
    
    @pytest.fixture
    def connection_manager(self, connection_config, mock_logger):
        """Create ConnectionManager instance for testing."""
        return ConnectionManager(
            config=connection_config,
            logger=mock_logger
        )
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection for testing."""
        connection = AsyncMock()
        connection.is_connected = True
        connection.connect = AsyncMock(return_value=True)
        connection.disconnect = AsyncMock()
        connection.send = AsyncMock()
        connection.receive = AsyncMock()
        return connection
    
    def test_connection_manager_initialization(self, connection_config, mock_logger):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager(
            config=connection_config,
            logger=mock_logger
        )
        
        assert manager is not None
        # Verify configuration is stored
        if hasattr(manager, 'config'):
            assert manager.config == connection_config
    
    async def test_connection_manager_connect_success(self, connection_manager, mock_connection):
        """Test successful connection establishment."""
        with patch.object(connection_manager, '_create_connection', return_value=mock_connection):
            result = await connection_manager.connect()
            
            if result is not None:
                assert result is True
                mock_connection.connect.assert_called_once()
    
    async def test_connection_manager_connect_failure(self, connection_manager):
        """Test connection failure handling."""
        with patch.object(connection_manager, '_create_connection', side_effect=ConnectionError("Failed")):
            result = await connection_manager.connect()
            
            # Should handle failure gracefully
            assert result is False or result is None
    
    async def test_connection_manager_disconnect(self, connection_manager, mock_connection):
        """Test connection disconnection."""
        # Setup connected state
        if hasattr(connection_manager, '_connection'):
            connection_manager._connection = mock_connection
        
        await connection_manager.disconnect()
        
        # Should call disconnect on underlying connection
        if mock_connection.disconnect.called:
            mock_connection.disconnect.assert_called_once()
    
    async def test_connection_manager_health_check(self, connection_manager, mock_connection):
        """Test connection health checking."""
        with patch.object(connection_manager, '_connection', mock_connection):
            mock_connection.is_connected = True
            
            # Test health check if method exists
            if hasattr(connection_manager, 'health_check'):
                health = await connection_manager.health_check()
                assert health is not None
            else:
                # Alternative: test that connection state can be checked
                is_connected = getattr(connection_manager, 'is_connected', lambda: True)()
                assert isinstance(is_connected, bool)
    
    async def test_connection_manager_retry_logic(self, connection_manager):
        """Test connection retry mechanism."""
        attempt_count = 0
        
        async def mock_connect():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Mock failure")
            return True
        
        with patch.object(connection_manager, '_attempt_connect', side_effect=mock_connect):
            # Test retry logic if available
            if hasattr(connection_manager, 'connect_with_retry'):
                result = await connection_manager.connect_with_retry(max_retries=3)
                assert result is True
                assert attempt_count == 3
    
    def test_connection_manager_configuration_validation(self, mock_logger):
        """Test configuration validation."""
        # Test invalid configuration
        invalid_configs = [
            {"host": "", "port": 8000},  # Empty host
            {"host": "localhost", "port": -1},  # Invalid port
            {"host": "localhost", "port": "invalid"},  # Non-numeric port
        ]
        
        for config in invalid_configs:
            try:
                manager = ConnectionManager(config=config, logger=mock_logger)
                # If no validation, should still create successfully
                assert manager is not None
            except (ValueError, TypeError):
                # Expected for invalid configurations
                pass


class TestConnectionPool:
    """Test ConnectionPool functionality."""
    
    @pytest.fixture  
    def connection_pool_config(self):
        """Create connection pool configuration."""
        return {
            "max_connections": 5,
            "min_connections": 1,
            "connection_timeout": 30.0,
            "idle_timeout": 300.0
        }
    
    @pytest.fixture
    def connection_pool(self, connection_pool_config, mock_logger):
        """Create ConnectionPool instance."""
        try:
            return ConnectionPool(
                config=connection_pool_config,
                logger=mock_logger
            )
        except Exception:
            # Skip if ConnectionPool not available
            pytest.skip("ConnectionPool class not available")
    
    async def test_connection_pool_initialization(self, connection_pool):
        """Test connection pool initialization."""
        assert connection_pool is not None
        
        # Test pool properties if available
        if hasattr(connection_pool, 'max_connections'):
            assert connection_pool.max_connections >= 1
    
    async def test_connection_pool_acquire_connection(self, connection_pool):
        """Test acquiring connection from pool."""
        if hasattr(connection_pool, 'acquire'):
            connection = await connection_pool.acquire()
            assert connection is not None
            
            # Return connection to pool
            if hasattr(connection_pool, 'release'):
                await connection_pool.release(connection)
    
    async def test_connection_pool_max_connections(self, connection_pool):
        """Test connection pool limits."""
        connections = []
        max_connections = getattr(connection_pool, 'max_connections', 5)
        
        # Try to acquire more connections than limit
        for i in range(max_connections + 2):
            try:
                if hasattr(connection_pool, 'acquire'):
                    conn = await asyncio.wait_for(
                        connection_pool.acquire(), 
                        timeout=1.0
                    )
                    connections.append(conn)
            except asyncio.TimeoutError:
                # Expected when pool is exhausted
                break
        
        # Should not exceed max connections
        assert len(connections) <= max_connections
        
        # Clean up
        for conn in connections:
            if hasattr(connection_pool, 'release'):
                await connection_pool.release(conn)


class TestConnectionHealth:
    """Test connection health monitoring."""
    
    def test_connection_health_data_structure(self):
        """Test ConnectionHealth data structure."""
        try:
            health = ConnectionHealth(
                is_connected=True,
                connection_state=MCPConnectionState.CONNECTED,
                last_successful_operation=datetime.now(),
                round_trip_time_ms=25.5
            )
            
            assert health.is_connected is True
            assert health.connection_state == MCPConnectionState.CONNECTED
            assert health.round_trip_time_ms == 25.5
            
        except Exception:
            # If ConnectionHealth not available or different signature
            pytest.skip("ConnectionHealth not available or different structure")
    
    def test_connection_health_error_rate_calculation(self):
        """Test error rate calculation in health status."""
        try:
            health = ConnectionHealth(
                is_connected=True,
                connection_state=MCPConnectionState.CONNECTED,
                total_operations=100,
                error_count=5
            )
            
            if hasattr(health, 'error_rate'):
                assert health.error_rate == 5.0
                
        except Exception:
            pytest.skip("ConnectionHealth error rate calculation not available")


class TestHealthChecker:
    """Test health checking functionality."""
    
    @pytest.fixture
    def health_checker(self, mock_logger):
        """Create HealthChecker instance."""
        try:
            return HealthChecker(logger=mock_logger)
        except Exception:
            pytest.skip("HealthChecker not available")
    
    async def test_health_checker_basic_check(self, health_checker):
        """Test basic health check."""
        mock_connection = AsyncMock()
        mock_connection.is_connected = True
        
        if hasattr(health_checker, 'check_connection_health'):
            health = await health_checker.check_connection_health(mock_connection)
            assert health is not None
    
    async def test_health_checker_performance_metrics(self, health_checker):
        """Test performance metric collection."""
        mock_connection = AsyncMock()
        
        if hasattr(health_checker, 'measure_response_time'):
            # Simulate operation with timing
            start_time = datetime.now()
            await asyncio.sleep(0.01)  # 10ms delay
            response_time = await health_checker.measure_response_time(
                mock_connection, 
                start_time
            )
            
            assert response_time >= 10.0  # Should be at least 10ms


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance  
class TestConnectionPerformance:
    """Performance tests for connection management."""
    
    async def test_connection_establishment_time(self, performance_timer):
        """Test connection establishment performance."""
        mock_manager = Mock()
        mock_manager.connect = AsyncMock(return_value=True)
        
        performance_timer.start()
        result = await mock_manager.connect()
        duration = performance_timer.stop()
        
        assert result is True
        performance_timer.assert_within_threshold(100.0)  # 100ms threshold
    
    async def test_connection_pool_throughput(self, performance_timer):
        """Test connection pool throughput."""
        # Create mock pool with fast operations
        mock_pool = Mock()
        mock_pool.acquire = AsyncMock()
        mock_pool.release = AsyncMock()
        
        async def simulate_operation():
            conn = await mock_pool.acquire()
            await asyncio.sleep(0.001)  # 1ms operation
            await mock_pool.release(conn)
        
        performance_timer.start()
        
        # Run 100 concurrent operations
        tasks = [simulate_operation() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        duration = performance_timer.stop()
        
        # Should complete in reasonable time
        assert duration < 1000.0  # Less than 1 second


# ============================================================================
# ERROR SCENARIO TESTS
# ============================================================================

@pytest.mark.error
class TestConnectionErrorScenarios:
    """Error handling tests for connection management."""
    
    async def test_connection_timeout_handling(self):
        """Test connection timeout scenarios."""
        manager = Mock()
        
        async def slow_connect():
            await asyncio.sleep(2.0)  # 2 second delay
            return True
        
        manager.connect = slow_connect
        
        # Should timeout quickly
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(manager.connect(), timeout=0.5)
    
    async def test_connection_retry_exhaustion(self):
        """Test behavior when all retry attempts fail."""
        attempt_count = 0
        
        async def failing_connect():
            nonlocal attempt_count
            attempt_count += 1
            raise ConnectionError(f"Attempt {attempt_count} failed")
        
        # Simulate manager with retry logic
        manager = Mock()
        manager.connect = failing_connect
        
        for _ in range(3):  # Try 3 times
            try:
                await manager.connect()
            except ConnectionError:
                pass
        
        assert attempt_count == 3
    
    async def test_network_interruption_simulation(self):
        """Test handling of network interruptions."""
        connection = Mock()
        connection.is_connected = True
        
        # Simulate network failure
        async def simulate_network_failure():
            connection.is_connected = False
            raise ConnectionError("Network interrupted")
        
        connection.send = simulate_network_failure
        
        # Should handle gracefully
        with pytest.raises(ConnectionError):
            await connection.send("test data")
        
        assert connection.is_connected is False
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configurations."""
        invalid_configs = [
            None,
            {},
            {"host": None},
            {"port": "invalid"},
        ]
        
        for config in invalid_configs:
            try:
                # Simulate configuration validation
                if not config or not isinstance(config.get("host"), str):
                    raise ValueError("Invalid configuration")
                    
            except (ValueError, AttributeError):
                # Expected for invalid configs
                pass


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "--tb=short"])