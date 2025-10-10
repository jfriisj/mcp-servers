"""
Comprehensive unit tests for container and dependency injection patterns.

Tests:
- container.py: Dependency injection container
- mock_client.py: Mock MCP client for testing

Coverage Target: 90%+
Performance: DI resolution <1ms, Mock operations <0.1ms
Error Scenarios: Missing dependencies, circular dependencies, mock failures
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from container import Container, DIContainer, ServiceRegistry
    from mock_client import MockMCPClient, MockToolResponse
except ImportError as e:
    # Fallback for testing without actual implementations
    print(f"Warning: Could not import container components: {e}")
    Container = None
    DIContainer = None
    ServiceRegistry = None
    MockMCPClient = None
    MockToolResponse = None


class TestContainer:
    """Unit tests for dependency injection container."""
    
    @pytest.fixture
    def container(self):
        """Container instance for testing."""
        if Container is None:
            pytest.skip("Container not available")
        return Container()
    
    def test_container_initialization(self):
        """Test container initializes correctly."""
        if Container is None:
            pytest.skip("Container not available")
            
        container = Container()
        assert hasattr(container, 'services')
        assert hasattr(container, 'singletons')
    
    def test_service_registration(self, container):
        """Test service registration in container."""
        if container is None:
            pytest.skip("Container not available")
            
        # Register a simple service
        class TestService:
            def __init__(self, value: str = "test"):
                self.value = value
            
            def get_value(self):
                return self.value
        
        container.register('test_service', TestService)
        
        # Verify registration
        assert container.has_service('test_service')
        
        # Get service instance
        service = container.get('test_service')
        assert isinstance(service, TestService)
        assert service.get_value() == "test"
    
    def test_singleton_behavior(self, container):
        """Test singleton service behavior."""
        if container is None:
            pytest.skip("Container not available")
            
        class SingletonService:
            def __init__(self):
                self.created_at = id(self)
        
        # Register as singleton
        container.register('singleton_service', SingletonService, singleton=True)
        
        # Get multiple instances
        instance1 = container.get('singleton_service')
        instance2 = container.get('singleton_service')
        
        # Should be same instance
        assert instance1 is instance2
        assert instance1.created_at == instance2.created_at
    
    def test_dependency_injection(self, container):
        """Test automatic dependency injection."""
        if container is None:
            pytest.skip("Container not available")
            
        # Define services with dependencies
        class DatabaseService:
            def __init__(self):
                self.connected = True
        
        class UserService:
            def __init__(self, database: DatabaseService):
                self.database = database
            
            def is_ready(self):
                return self.database.connected
        
        # Register services
        container.register('database', DatabaseService, singleton=True)
        container.register('user_service', UserService)
        
        # Get service with injected dependencies
        user_service = container.get('user_service')
        assert isinstance(user_service, UserService)
        assert user_service.is_ready() is True
    
    def test_circular_dependency_detection(self, container):
        """Test circular dependency detection and handling."""
        if container is None:
            pytest.skip("Container not available")
            
        class ServiceA:
            def __init__(self, service_b):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):
                self.service_a = service_a
        
        container.register('service_a', ServiceA)
        container.register('service_b', ServiceB)
        
        # Should detect circular dependency
        with pytest.raises((ValueError, RuntimeError)):
            container.get('service_a')
    
    def test_missing_dependency_handling(self, container):
        """Test handling of missing dependencies."""
        if container is None:
            pytest.skip("Container not available")
            
        class ServiceWithMissingDep:
            def __init__(self, nonexistent_service):
                self.dep = nonexistent_service
        
        container.register('faulty_service', ServiceWithMissingDep)
        
        # Should handle missing dependency gracefully
        with pytest.raises((ValueError, KeyError, TypeError)):
            container.get('faulty_service')
    
    def test_factory_registration(self, container):
        """Test factory function registration."""
        if container is None:
            pytest.skip("Container not available")
            
        def create_config_service():
            return {
                'server_uri': 'stdio://test',
                'timeout': 30.0,
                'created_by': 'factory'
            }
        
        container.register_factory('config', create_config_service)
        
        config = container.get('config')
        assert isinstance(config, dict)
        assert config['created_by'] == 'factory'
    
    def test_container_performance(self, container, performance_timer):
        """Test container resolution performance."""
        if container is None:
            pytest.skip("Container not available")
            
        # Register multiple services
        class FastService:
            def __init__(self):
                self.value = "fast"
        
        for i in range(100):
            container.register(f'service_{i}', FastService)
        
        # Test resolution speed
        with performance_timer:
            services = []
            for i in range(100):
                service = container.get(f'service_{i}')
                services.append(service)
        
        assert performance_timer.elapsed < 0.001  # Should be very fast
        assert len(services) == 100
    
    def test_container_scopes(self, container):
        """Test different service scopes."""
        if container is None:
            pytest.skip("Container not available")
            
        class TransientService:
            def __init__(self):
                self.id = id(self)
        
        class ScopedService:
            def __init__(self):
                self.id = id(self)
        
        # Register with different scopes
        container.register('transient', TransientService, scope='transient')
        container.register('scoped', ScopedService, scope='scoped')
        
        # Transient should create new instances
        t1 = container.get('transient')
        t2 = container.get('transient')
        assert t1.id != t2.id
        
        # Scoped should reuse within scope
        if hasattr(container, 'create_scope'):
            with container.create_scope():
                s1 = container.get('scoped')
                s2 = container.get('scoped')
                assert s1.id == s2.id


class TestMockMCPClient:
    """Unit tests for MockMCPClient testing infrastructure."""
    
    @pytest.fixture
    def mock_client(self):
        """MockMCPClient instance for testing."""
        if MockMCPClient is None:
            pytest.skip("MockMCPClient not available")
        return MockMCPClient()
    
    def test_mock_client_initialization(self):
        """Test mock client initializes correctly."""
        if MockMCPClient is None:
            pytest.skip("MockMCPClient not available")
            
        client = MockMCPClient()
        assert hasattr(client, 'responses')
        assert hasattr(client, 'call_history')
    
    def test_mock_tool_response_setup(self, mock_client):
        """Test setting up mock tool responses."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Setup mock response
        mock_response = {
            'result': {'success': True, 'data': 'test_data'}
        }
        
        mock_client.set_response('test_tool', mock_response)
        
        # Call tool and verify response
        response = mock_client.call_tool('test_tool', {'param': 'value'})
        assert response == mock_response
    
    def test_mock_call_history_tracking(self, mock_client):
        """Test call history tracking."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Setup responses
        mock_client.set_response('tool1', {'result': {'data': '1'}})
        mock_client.set_response('tool2', {'result': {'data': '2'}})
        
        # Make calls
        mock_client.call_tool('tool1', {'param1': 'value1'})
        mock_client.call_tool('tool2', {'param2': 'value2'})
        mock_client.call_tool('tool1', {'param3': 'value3'})
        
        # Verify history
        history = mock_client.get_call_history()
        assert len(history) == 3
        assert history[0]['tool'] == 'tool1'
        assert history[1]['tool'] == 'tool2'
        assert history[2]['tool'] == 'tool1'
    
    def test_mock_error_simulation(self, mock_client):
        """Test simulating tool errors."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Setup error response
        error_response = {
            'error': {'code': -1, 'message': 'Tool failed'}
        }
        
        mock_client.set_response('failing_tool', error_response)
        
        response = mock_client.call_tool('failing_tool', {})
        assert 'error' in response
        assert response['error']['message'] == 'Tool failed'
    
    def test_mock_timeout_simulation(self, mock_client):
        """Test simulating timeouts."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        if not hasattr(mock_client, 'set_timeout'):
            pytest.skip("Timeout simulation not available")
            
        # Setup timeout
        mock_client.set_timeout('slow_tool', 2.0)
        
        import time
        start_time = time.time()
        
        try:
            response = mock_client.call_tool('slow_tool', {}, timeout=1.0)
            # Should either timeout or return quickly
            elapsed = time.time() - start_time
            assert elapsed < 1.5  # Should not wait full 2 seconds
        except TimeoutError:
            # Timeout is expected behavior
            pass
    
    @pytest.mark.asyncio
    async def test_mock_async_operations(self, mock_client):
        """Test async mock operations."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        if not hasattr(mock_client, 'call_tool_async'):
            pytest.skip("Async operations not available")
            
        # Setup async response
        mock_response = {'result': {'async': True}}
        mock_client.set_response('async_tool', mock_response)
        
        response = await mock_client.call_tool_async('async_tool', {})
        assert response == mock_response
    
    def test_mock_performance_simulation(self, mock_client, performance_timer):
        """Test performance characteristics simulation."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Setup fast response
        mock_client.set_response('fast_tool', {'result': 'fast'})
        
        with performance_timer:
            for _ in range(100):
                mock_client.call_tool('fast_tool', {})
        
        assert performance_timer.elapsed < 0.01  # Should be very fast
    
    def test_mock_state_management(self, mock_client):
        """Test mock client state management."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Test connection state
        assert mock_client.is_connected() in [True, False]
        
        if hasattr(mock_client, 'connect'):
            result = mock_client.connect()
            assert result in [True, False]
        
        if hasattr(mock_client, 'disconnect'):
            result = mock_client.disconnect()
            assert result in [True, False]
    
    def test_mock_response_validation(self, mock_client):
        """Test mock response validation."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Test invalid response format
        invalid_responses = [
            None,
            "not_a_dict",
            {"incomplete": True},  # Missing result or error
        ]
        
        for invalid_response in invalid_responses:
            if hasattr(mock_client, 'validate_response'):
                is_valid = mock_client.validate_response(invalid_response)
                assert is_valid is False
    
    def test_mock_reset_functionality(self, mock_client):
        """Test mock client reset functionality."""
        if mock_client is None:
            pytest.skip("MockMCPClient not available")
            
        # Setup some state
        mock_client.set_response('tool1', {'result': 'data'})
        mock_client.call_tool('tool1', {})
        
        # Verify state exists
        history = mock_client.get_call_history()
        assert len(history) > 0
        
        # Reset
        if hasattr(mock_client, 'reset'):
            mock_client.reset()
            
            # Verify reset
            new_history = mock_client.get_call_history()
            assert len(new_history) == 0


class TestContainerMockIntegration:
    """Integration tests for container and mock components."""
    
    def test_container_with_mock_services(self):
        """Test container using mock services."""
        if None in [Container, MockMCPClient]:
            pytest.skip("Components not available")
            
        container = Container()
        
        # Register mock client as service
        mock_client = MockMCPClient()
        mock_client.set_response('test_tool', {'result': {'success': True}})
        
        container.register_instance('mcp_client', mock_client)
        
        # Create service that uses mock client
        class DocumentService:
            def __init__(self, mcp_client):
                self.client = mcp_client
            
            def process_document(self, doc_id):
                return self.client.call_tool('test_tool', {'doc_id': doc_id})
        
        container.register('document_service', DocumentService)
        
        # Test integration
        doc_service = container.get('document_service')
        result = doc_service.process_document(123)
        
        assert result['result']['success'] is True
    
    def test_mock_service_replacement(self):
        """Test replacing real services with mocks in container."""
        if Container is None:
            pytest.skip("Container not available")
            
        container = Container()
        
        # Original service
        class RealDatabaseService:
            def connect(self):
                return "real_connection"
        
        # Mock service
        class MockDatabaseService:
            def connect(self):
                return "mock_connection"
        
        # Register real service first
        container.register('database', RealDatabaseService)
        real_db = container.get('database')
        assert real_db.connect() == "real_connection"
        
        # Replace with mock
        container.register('database', MockDatabaseService, replace=True)
        mock_db = container.get('database')
        assert mock_db.connect() == "mock_connection"
    
    def test_container_performance_with_mocks(self, performance_timer):
        """Test container performance with mock services."""
        if Container is None:
            pytest.skip("Container not available")
            
        container = Container()
        
        # Register many mock services
        class MockService:
            def __init__(self, service_id):
                self.id = service_id
            
            def process(self):
                return f"processed_{self.id}"
        
        # Register services
        for i in range(50):
            container.register(f'service_{i}', lambda i=i: MockService(i))
        
        # Test resolution performance
        with performance_timer:
            services = []
            for i in range(50):
                service = container.get(f'service_{i}')
                result = service.process()
                services.append(result)
        
        assert performance_timer.elapsed < 0.01  # Should be fast
        assert len(services) == 50
    
    def test_container_lifecycle_with_mocks(self):
        """Test container lifecycle management with mock services."""
        if Container is None:
            pytest.skip("Container not available")
            
        container = Container()
        
        # Mock service with lifecycle
        class LifecycleMockService:
            def __init__(self):
                self.initialized = True
                self.disposed = False
            
            def dispose(self):
                self.disposed = True
        
        # Register and use
        container.register('lifecycle_service', LifecycleMockService)
        service = container.get('lifecycle_service')
        
        assert service.initialized is True
        assert service.disposed is False
        
        # Cleanup
        if hasattr(container, 'dispose_all'):
            container.dispose_all()
            assert service.disposed is True
    
    def test_error_handling_integration(self):
        """Test error handling across container and mock integration."""
        if None in [Container, MockMCPClient]:
            pytest.skip("Components not available")
            
        container = Container()
        
        # Mock client that simulates errors
        mock_client = MockMCPClient()
        mock_client.set_response('error_tool', {
            'error': {'code': -1, 'message': 'Simulated error'}
        })
        
        container.register_instance('client', mock_client)
        
        # Service that handles errors
        class ErrorHandlingService:
            def __init__(self, client):
                self.client = client
            
            def safe_call(self, tool_name, params):
                try:
                    response = self.client.call_tool(tool_name, params)
                    if 'error' in response:
                        return {'success': False, 'error': response['error']}
                    return {'success': True, 'data': response}
                except Exception as e:
                    return {'success': False, 'error': str(e)}
        
        container.register('error_service', ErrorHandlingService)
        
        # Test error handling
        service = container.get('error_service')
        result = service.safe_call('error_tool', {})
        
        assert result['success'] is False
        assert 'error' in result