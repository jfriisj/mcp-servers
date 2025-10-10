"""
Unit Tests for Mock MCP Client - Critical Testing Infrastructure.

Tests the MockMCPClient which is essential for testing all other integration 
components. This mock client must behave identically to real MCP clients
for comprehensive testing scenarios.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing
SOLID Compliance: Tests ensure SRP, OCP, LSP, ISP, DIP compliance
Coverage Target: 90%+ with comprehensive error scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
from datetime import datetime

# Import components under test
try:
    from mock_client import (
        MockMCPClient, MockConfiguration, MockClientBuilder,
        BehaviorMode, OperationTracker, OperationRecord
    )
    from schemas import ToolInvocationRequest, ToolInvocationResponse
    from mcp_client import ConnectionState, OperationStatus
except ImportError as e:
    pytest.skip(f"Mock client components not available: {e}", allow_module_level=True)


class TestMockConfiguration:
    """Test MockConfiguration data structure."""
    
    def test_mock_configuration_default(self):
        """Test MockConfiguration with default values."""
        config = MockConfiguration()
        
        assert config.behavior_mode == BehaviorMode.NORMAL
        assert config.success_rate == 1.0
        assert config.latency_ms == 0
        assert config.error_types == []
        assert config.response_overrides == {}
        assert config.enable_operation_tracking is False
        assert config.simulate_timeouts is False
        assert config.connection_failure_rate == 0.0
    
    def test_mock_configuration_custom(self):
        """Test MockConfiguration with custom values."""
        config = MockConfiguration(
            behavior_mode=BehaviorMode.ERROR_SIMULATION,
            success_rate=0.8,
            latency_ms=100,
            error_types=["TimeoutError", "ConnectionError"],
            enable_operation_tracking=True,
            simulate_timeouts=True,
            connection_failure_rate=0.2
        )
        
        assert config.behavior_mode == BehaviorMode.ERROR_SIMULATION
        assert config.success_rate == 0.8
        assert config.latency_ms == 100
        assert "TimeoutError" in config.error_types
        assert "ConnectionError" in config.error_types
        assert config.enable_operation_tracking is True
        assert config.simulate_timeouts is True
        assert config.connection_failure_rate == 0.2
    
    def test_mock_configuration_validation(self):
        """Test MockConfiguration parameter validation."""
        # Valid range tests
        config = MockConfiguration(success_rate=0.0)
        assert config.success_rate == 0.0
        
        config = MockConfiguration(success_rate=1.0)
        assert config.success_rate == 1.0
        
        # Test boundary values
        config = MockConfiguration(latency_ms=0)
        assert config.latency_ms == 0
        
        config = MockConfiguration(connection_failure_rate=0.0)
        assert config.connection_failure_rate == 0.0
        
        config = MockConfiguration(connection_failure_rate=1.0)
        assert config.connection_failure_rate == 1.0


class TestBehaviorMode:
    """Test BehaviorMode enumeration."""
    
    def test_behavior_mode_values(self):
        """Test BehaviorMode enum values."""
        assert BehaviorMode.NORMAL == "normal"
        assert BehaviorMode.ERROR_SIMULATION == "error_simulation"
        assert BehaviorMode.LATENCY_TESTING == "latency_testing"
        assert BehaviorMode.OFFLINE_MODE == "offline_mode"


class TestOperationTracker:
    """Test OperationTracker functionality."""
    
    @pytest.fixture
    def tracker(self):
        """Create OperationTracker instance."""
        return OperationTracker()
    
    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert len(tracker.get_operation_history()) == 0
        assert tracker.get_operation_count() == 0
    
    def test_record_operation(self, tracker):
        """Test recording operations."""
        tracker.record_operation(
            operation="connect",
            success=True,
            duration_ms=50.0,
            parameters={"host": "localhost"}
        )
        
        history = tracker.get_operation_history()
        assert len(history) == 1
        
        record = history[0]
        assert record.operation == "connect"
        assert record.success is True
        assert record.duration_ms == 50.0
        assert record.parameters["host"] == "localhost"
        assert isinstance(record.timestamp, datetime)
    
    def test_record_multiple_operations(self, tracker):
        """Test recording multiple operations."""
        operations = [
            {"operation": "connect", "success": True, "duration_ms": 50.0},
            {"operation": "invoke_tool", "success": True, "duration_ms": 25.0},
            {"operation": "invoke_tool", "success": False, "duration_ms": 15.0},
            {"operation": "disconnect", "success": True, "duration_ms": 10.0}
        ]
        
        for op in operations:
            tracker.record_operation(**op)
        
        history = tracker.get_operation_history()
        assert len(history) == 4
        assert tracker.get_operation_count() == 4
        
        # Verify operations are in order
        assert history[0].operation == "connect"
        assert history[1].operation == "invoke_tool"
        assert history[2].operation == "invoke_tool"
        assert history[3].operation == "disconnect"
    
    def test_get_operations_by_type(self, tracker):
        """Test filtering operations by type."""
        # Record mixed operations
        tracker.record_operation("connect", True, 50.0)
        tracker.record_operation("invoke_tool", True, 25.0)
        tracker.record_operation("invoke_tool", False, 15.0)
        tracker.record_operation("disconnect", True, 10.0)
        
        # Get specific operation types
        tool_operations = tracker.get_operations_by_type("invoke_tool")
        assert len(tool_operations) == 2
        
        connect_operations = tracker.get_operations_by_type("connect")
        assert len(connect_operations) == 1
        
        nonexistent_operations = tracker.get_operations_by_type("nonexistent")
        assert len(nonexistent_operations) == 0
    
    def test_get_success_rate(self, tracker):
        """Test success rate calculation."""
        # Initially no operations
        assert tracker.get_success_rate() == 0.0
        
        # Add successful operations
        tracker.record_operation("test1", True, 10.0)
        tracker.record_operation("test2", True, 10.0)
        assert tracker.get_success_rate() == 1.0
        
        # Add failed operation
        tracker.record_operation("test3", False, 10.0)
        assert tracker.get_success_rate() == 2/3  # 2 out of 3 successful
        
        # Add more operations
        tracker.record_operation("test4", False, 10.0)
        tracker.record_operation("test5", True, 10.0)
        assert tracker.get_success_rate() == 3/5  # 3 out of 5 successful
    
    def test_clear_history(self, tracker):
        """Test clearing operation history."""
        # Add some operations
        tracker.record_operation("test1", True, 10.0)
        tracker.record_operation("test2", False, 15.0)
        
        assert len(tracker.get_operation_history()) == 2
        assert tracker.get_operation_count() == 2
        
        # Clear history
        tracker.clear_history()
        
        assert len(tracker.get_operation_history()) == 0
        assert tracker.get_operation_count() == 0
        assert tracker.get_success_rate() == 0.0


class TestMockMCPClient:
    """Test MockMCPClient functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create MockMCPClient with default configuration."""
        return MockMCPClient()
    
    @pytest.fixture
    def error_client(self):
        """Create MockMCPClient configured for error simulation."""
        config = MockConfiguration(
            behavior_mode=BehaviorMode.ERROR_SIMULATION,
            success_rate=0.2,  # 80% failure rate
            error_types=["ConnectionError", "TimeoutError"]
        )
        return MockMCPClient(config)
    
    @pytest.fixture
    def latency_client(self):
        """Create MockMCPClient configured for latency testing."""
        config = MockConfiguration(
            behavior_mode=BehaviorMode.LATENCY_TESTING,
            latency_ms=100,
            enable_operation_tracking=True
        )
        return MockMCPClient(config)
    
    def test_client_initialization(self, mock_client):
        """Test mock client initialization."""
        assert mock_client is not None
        assert mock_client.is_connected() is False
        assert mock_client.config.behavior_mode == BehaviorMode.NORMAL
    
    async def test_connect_normal_mode(self, mock_client):
        """Test connection in normal mode."""
        result = await mock_client.connect()
        
        assert result is True
        assert mock_client.is_connected() is True
    
    async def test_connect_error_simulation(self, error_client):
        """Test connection with error simulation."""
        # With 20% success rate, connection might fail
        results = []
        for _ in range(10):
            result = await error_client.connect()
            results.append(result)
            error_client._connected = False  # Reset for next attempt
        
        # Should have mix of successes and failures
        successes = sum(1 for r in results if r)
        failures = len(results) - successes
        
        # With 20% success rate, expect some failures
        assert failures > 0
    
    async def test_disconnect(self, mock_client):
        """Test disconnection."""
        # Connect first
        await mock_client.connect()
        assert mock_client.is_connected() is True
        
        # Disconnect
        await mock_client.disconnect()
        assert mock_client.is_connected() is False
    
    async def test_tool_invocation_normal_mode(self, mock_client):
        """Test tool invocation in normal mode."""
        await mock_client.connect()
        
        request = ToolInvocationRequest(
            name="upload_document",
            parameters={"file_path": "/test/document.pdf"}
        )
        
        response = await mock_client.invoke_tool(request)
        
        assert response.success is True
        assert response.data is not None
        assert response.error is None
    
    async def test_tool_invocation_not_connected(self, mock_client):
        """Test tool invocation when not connected."""
        request = ToolInvocationRequest(
            name="test_tool",
            parameters={}
        )
        
        response = await mock_client.invoke_tool(request)
        
        assert response.success is False
        assert response.error is not None
        assert "not connected" in response.error.lower()
    
    async def test_tool_invocation_with_latency(self, latency_client, performance_timer):
        """Test tool invocation with simulated latency."""
        await latency_client.connect()
        
        request = ToolInvocationRequest(
            name="test_tool", 
            parameters={}
        )
        
        performance_timer.start()
        response = await latency_client.invoke_tool(request)
        duration_ms = performance_timer.stop()
        
        assert response.success is True
        # Should take at least the configured latency (allowing some tolerance)
        assert duration_ms >= 80  # 100ms configured - 20ms tolerance
    
    async def test_tool_invocation_error_simulation(self, error_client):
        """Test tool invocation with error simulation."""
        await error_client.connect()
        
        request = ToolInvocationRequest(
            name="test_tool",
            parameters={}
        )
        
        # Try multiple invocations to test error rate
        results = []
        for _ in range(20):
            response = await error_client.invoke_tool(request)
            results.append(response.success)
        
        successes = sum(1 for r in results if r)
        failures = len(results) - successes
        
        # With 20% success rate, should have more failures than successes
        assert failures > successes
    
    async def test_list_tools(self, mock_client):
        """Test tool listing functionality."""
        await mock_client.connect()
        
        tools = await mock_client.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check structure of tool entries
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
    
    async def test_get_tool_schema(self, mock_client):
        """Test tool schema retrieval."""
        await mock_client.connect()
        
        schema = await mock_client.get_tool_schema("upload_document")
        
        assert schema is not None
        assert schema.name == "upload_document"
        assert schema.parameters is not None
    
    async def test_operation_tracking(self):
        """Test operation tracking functionality."""
        config = MockConfiguration(enable_operation_tracking=True)
        client = MockMCPClient(config)
        
        # Perform operations
        await client.connect()
        
        request = ToolInvocationRequest(name="test_tool", parameters={})
        await client.invoke_tool(request)
        await client.invoke_tool(request)
        
        await client.disconnect()
        
        # Check tracking
        history = client.get_operation_history()
        assert len(history) >= 4  # connect, invoke_tool x2, disconnect
        
        # Verify operation types
        operations = [record.operation for record in history]
        assert "connect" in operations
        assert "invoke_tool" in operations
        assert "disconnect" in operations
    
    async def test_response_overrides(self):
        """Test custom response overrides."""
        custom_response = {
            "success": True,
            "data": {"custom": "response", "id": 12345},
            "message": "Custom test response"
        }
        
        config = MockConfiguration(
            response_overrides={"test_tool": custom_response}
        )
        client = MockMCPClient(config)
        await client.connect()
        
        request = ToolInvocationRequest(name="test_tool", parameters={})
        response = await client.invoke_tool(request)
        
        assert response.success is True
        assert response.data["custom"] == "response"
        assert response.data["id"] == 12345
    
    async def test_offline_mode(self):
        """Test offline mode behavior."""
        config = MockConfiguration(behavior_mode=BehaviorMode.OFFLINE_MODE)
        client = MockMCPClient(config)
        
        # Connection should fail in offline mode
        result = await client.connect()
        assert result is False
        assert client.is_connected() is False
        
        # Tool invocation should fail
        request = ToolInvocationRequest(name="test_tool", parameters={})
        response = await client.invoke_tool(request)
        
        assert response.success is False
        assert "offline" in response.error.lower() or "not connected" in response.error.lower()


class TestMockClientBuilder:
    """Test MockClientBuilder pattern."""
    
    def test_builder_default(self):
        """Test builder with default configuration."""
        client = MockClientBuilder().build()
        
        assert client is not None
        assert client.config.behavior_mode == BehaviorMode.NORMAL
        assert client.config.success_rate == 1.0
        assert client.config.latency_ms == 0
    
    def test_builder_with_error_simulation(self):
        """Test builder with error simulation configuration."""
        client = (MockClientBuilder()
                 .with_error_simulation(success_rate=0.7)
                 .build())
        
        assert client.config.behavior_mode == BehaviorMode.ERROR_SIMULATION
        assert client.config.success_rate == 0.7
    
    def test_builder_with_latency(self):
        """Test builder with latency configuration."""
        client = (MockClientBuilder()
                 .with_latency(latency_ms=50)
                 .build())
        
        assert client.config.behavior_mode == BehaviorMode.LATENCY_TESTING
        assert client.config.latency_ms == 50
    
    def test_builder_with_operation_tracking(self):
        """Test builder with operation tracking."""
        client = (MockClientBuilder()
                 .with_operation_tracking()
                 .build())
        
        assert client.config.enable_operation_tracking is True
    
    def test_builder_with_offline_mode(self):
        """Test builder with offline mode."""
        client = (MockClientBuilder()
                 .with_offline_mode()
                 .build())
        
        assert client.config.behavior_mode == BehaviorMode.OFFLINE_MODE
    
    def test_builder_with_custom_responses(self):
        """Test builder with custom response overrides."""
        custom_responses = {
            "tool1": {"success": True, "data": {"custom": "response1"}},
            "tool2": {"success": False, "error": "Custom error"}
        }
        
        client = (MockClientBuilder()
                 .with_custom_responses(custom_responses)
                 .build())
        
        assert client.config.response_overrides == custom_responses
    
    def test_builder_chaining(self):
        """Test builder method chaining."""
        client = (MockClientBuilder()
                 .with_error_simulation(success_rate=0.8)
                 .with_latency(latency_ms=25)
                 .with_operation_tracking()
                 .build())
        
        # Should combine all configurations
        assert client.config.behavior_mode == BehaviorMode.ERROR_SIMULATION  # Last behavior wins
        assert client.config.success_rate == 0.8
        assert client.config.latency_ms == 25
        assert client.config.enable_operation_tracking is True


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
class TestMockClientPerformance:
    """Performance tests for MockMCPClient."""
    
    async def test_connection_performance(self, performance_timer, performance_threshold):
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
    
    async def test_concurrent_operations_performance(self, performance_timer):
        """Test performance under concurrent operations."""
        client = MockMCPClient()
        await client.connect()
        
        # Create many concurrent requests
        requests = [
            ToolInvocationRequest(name=f"tool_{i}", parameters={})
            for i in range(100)
        ]
        
        performance_timer.start()
        
        # Execute concurrently
        results = await asyncio.gather(*[
            client.invoke_tool(req) for req in requests
        ])
        
        duration_ms = performance_timer.stop()
        
        # All should succeed
        assert len(results) == 100
        assert all(r.success for r in results)
        
        # Should handle 100 concurrent operations reasonably fast
        assert duration_ms < 1000  # Less than 1 second


# ============================================================================
# ERROR SCENARIO TESTS
# ============================================================================

@pytest.mark.error
class TestMockClientErrorScenarios:
    """Error handling and edge case tests."""
    
    async def test_multiple_connections(self):
        """Test behavior with multiple connection attempts."""
        client = MockMCPClient()
        
        # First connection should succeed
        result1 = await client.connect()
        assert result1 is True
        assert client.is_connected() is True
        
        # Second connection attempt should handle gracefully
        result2 = await client.connect()
        assert result2 is True  # Should remain connected
        assert client.is_connected() is True
    
    async def test_disconnect_when_not_connected(self):
        """Test disconnection when not connected."""
        client = MockMCPClient()
        
        # Should handle gracefully
        await client.disconnect()
        assert client.is_connected() is False
    
    async def test_invalid_tool_invocation(self):
        """Test invocation of non-existent tools."""
        client = MockMCPClient()
        await client.connect()
        
        request = ToolInvocationRequest(
            name="nonexistent_tool",
            parameters={}
        )
        
        response = await client.invoke_tool(request)
        
        # Should handle gracefully - either success with mock data or clear error
        assert response.success in [True, False]
        if not response.success:
            assert response.error is not None
    
    async def test_malformed_parameters(self):
        """Test tool invocation with malformed parameters."""
        client = MockMCPClient()
        await client.connect()
        
        # Test with various malformed parameter sets
        malformed_params = [
            None,
            {"invalid": None},
            {"nested": {"deeply": {"nested": None}}}
        ]
        
        for params in malformed_params:
            request = ToolInvocationRequest(
                name="test_tool",
                parameters=params
            )
            
            response = await client.invoke_tool(request)
            
            # Should handle gracefully
            assert response is not None
            assert hasattr(response, 'success')
    
    async def test_extreme_configuration_values(self):
        """Test with extreme configuration values."""
        extreme_configs = [
            MockConfiguration(success_rate=0.0),  # Always fail
            MockConfiguration(success_rate=1.0),  # Always succeed
            MockConfiguration(latency_ms=0),      # No latency
            MockConfiguration(latency_ms=1000),   # High latency
        ]
        
        for config in extreme_configs:
            client = MockMCPClient(config)
            
            # Should create client without errors
            assert client is not None
            
            # Basic operations should work
            result = await client.connect()
            if config.success_rate > 0:
                # Might succeed
                pass
            else:
                # Should fail consistently
                assert result is False


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "--tb=short"])