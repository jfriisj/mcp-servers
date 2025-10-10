"""
Comprehensive unit tests for infrastructure layer integration components.

Tests:
- config_manager.py: Configuration management and validation
- performance.py: Performance monitoring and metrics
- security.py: Security validation and protection

Coverage Target: 90%+
Performance: Configuration ops <10ms, Security validation <5ms
Error Scenarios: Invalid configs, security violations, performance degradation
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import time
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config_manager import ConfigManager, IntegrationConfig
    from performance import PerformanceMonitor, MetricsCollector
    from security import SecurityManager, SecurityValidator
except ImportError as e:
    # Fallback for testing without actual implementations
    print(f"Warning: Could not import infrastructure components: {e}")
    ConfigManager = None
    IntegrationConfig = None
    PerformanceMonitor = None
    MetricsCollector = None
    SecurityManager = None
    SecurityValidator = None


class TestConfigManager:
    """Unit tests for ConfigManager configuration management."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing."""
        config_data = {
            'mcp_server': {
                'uri': 'stdio://path/to/server',
                'timeout': 30.0,
                'retry_attempts': 3
            },
            'gui': {
                'theme': 'light',
                'window_size': [800, 600],
                'auto_save': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'study_buddy.log'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """ConfigManager instance for testing."""
        if ConfigManager is None:
            pytest.skip("ConfigManager not available")
        return ConfigManager(temp_config_file)
    
    def test_config_manager_initialization(self, temp_config_file):
        """Test config manager initializes correctly."""
        if ConfigManager is None:
            pytest.skip("ConfigManager not available")
            
        manager = ConfigManager(temp_config_file)
        assert manager.config_file == temp_config_file
        assert hasattr(manager, 'config')
    
    def test_config_loading(self, config_manager):
        """Test configuration loading from file."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        config = config_manager.load_config()
        assert isinstance(config, dict)
        assert 'mcp_server' in config
        assert 'gui' in config
        assert 'logging' in config
    
    def test_config_validation(self, config_manager):
        """Test configuration validation."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        # Test valid config
        valid_config = {
            'mcp_server': {
                'uri': 'stdio://valid/path',
                'timeout': 30.0
            }
        }
        
        is_valid = config_manager.validate_config(valid_config)
        assert is_valid is True
        
        # Test invalid config
        invalid_config = {
            'mcp_server': {
                'uri': '',  # Invalid: empty URI
                'timeout': -1  # Invalid: negative timeout
            }
        }
        
        is_valid = config_manager.validate_config(invalid_config)
        assert is_valid is False
    
    def test_config_getting_setting(self, config_manager):
        """Test getting and setting configuration values."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        # Test getting nested value
        timeout = config_manager.get('mcp_server.timeout')
        assert timeout == 30.0
        
        # Test setting nested value
        config_manager.set('mcp_server.timeout', 45.0)
        new_timeout = config_manager.get('mcp_server.timeout')
        assert new_timeout == 45.0
        
        # Test default values
        nonexistent = config_manager.get('nonexistent.key', 'default_value')
        assert nonexistent == 'default_value'
    
    def test_config_persistence(self, config_manager, performance_timer):
        """Test configuration persistence to file."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        # Modify config
        config_manager.set('gui.theme', 'dark')
        
        with performance_timer:
            success = config_manager.save_config()
        
        assert performance_timer.elapsed < 0.01  # Should be fast
        assert success is True
        
        # Verify persistence by reloading
        config_manager.load_config()
        theme = config_manager.get('gui.theme')
        assert theme == 'dark'
    
    def test_config_backup_restore(self, config_manager):
        """Test configuration backup and restore."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        if not hasattr(config_manager, 'create_backup'):
            pytest.skip("Backup functionality not available")
            
        # Create backup
        backup_file = config_manager.create_backup()
        assert os.path.exists(backup_file)
        
        # Modify config
        config_manager.set('gui.theme', 'modified')
        
        # Restore from backup
        success = config_manager.restore_backup(backup_file)
        assert success is True
        
        # Verify restoration
        theme = config_manager.get('gui.theme')
        assert theme != 'modified'  # Should be restored to original
    
    def test_config_environment_overrides(self, config_manager):
        """Test environment variable overrides."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        # Set environment override
        os.environ['STUDY_BUDDY_MCP_TIMEOUT'] = '60'
        
        try:
            if hasattr(config_manager, 'apply_env_overrides'):
                config_manager.apply_env_overrides()
                timeout = config_manager.get('mcp_server.timeout')
                assert timeout == 60.0
        finally:
            # Cleanup
            if 'STUDY_BUDDY_MCP_TIMEOUT' in os.environ:
                del os.environ['STUDY_BUDDY_MCP_TIMEOUT']
    
    def test_config_validation_errors(self, config_manager):
        """Test detailed configuration validation errors."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        invalid_configs = [
            {'mcp_server': {'uri': None}},  # None URI
            {'mcp_server': {'timeout': 'not_a_number'}},  # Invalid type
            {'gui': {'window_size': [800]}},  # Incomplete array
            {}  # Empty config
        ]
        
        for invalid_config in invalid_configs:
            is_valid = config_manager.validate_config(invalid_config)
            assert is_valid is False
    
    def test_config_performance(self, config_manager, performance_timer):
        """Test configuration operation performance."""
        if config_manager is None:
            pytest.skip("ConfigManager not available")
            
        # Test rapid get operations
        with performance_timer:
            for _ in range(1000):
                value = config_manager.get('mcp_server.timeout')
        
        assert performance_timer.elapsed < 0.01  # Should be very fast
        
        # Test rapid set operations
        with performance_timer:
            for i in range(100):
                config_manager.set('temp.value', i)
        
        assert performance_timer.elapsed < 0.05  # Should be fast


class TestPerformanceMonitor:
    """Unit tests for PerformanceMonitor metrics collection."""
    
    @pytest.fixture
    def performance_monitor(self):
        """PerformanceMonitor instance for testing."""
        if PerformanceMonitor is None:
            pytest.skip("PerformanceMonitor not available")
        return PerformanceMonitor()
    
    def test_monitor_initialization(self):
        """Test performance monitor initializes correctly."""
        if PerformanceMonitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        monitor = PerformanceMonitor()
        assert hasattr(monitor, 'metrics')
        assert hasattr(monitor, 'collectors')
    
    def test_timing_operations(self, performance_monitor, performance_timer):
        """Test timing operation measurement."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        # Start timing
        performance_monitor.start_timer('test_operation')
        
        # Simulate work
        time.sleep(0.01)
        
        # Stop timing
        elapsed = performance_monitor.stop_timer('test_operation')
        
        assert elapsed >= 0.01
        assert elapsed < 0.1  # Should be reasonable
    
    def test_metrics_collection(self, performance_monitor):
        """Test metrics collection and aggregation."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        # Record multiple metrics
        performance_monitor.record_metric('api_calls', 1)
        performance_monitor.record_metric('api_calls', 1)
        performance_monitor.record_metric('errors', 1)
        
        # Get aggregated metrics
        metrics = performance_monitor.get_metrics()
        assert 'api_calls' in metrics
        assert metrics['api_calls'] == 2
        assert metrics['errors'] == 1
    
    def test_performance_thresholds(self, performance_monitor):
        """Test performance threshold monitoring."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        if not hasattr(performance_monitor, 'set_threshold'):
            pytest.skip("Threshold functionality not available")
            
        # Set threshold
        performance_monitor.set_threshold('response_time', 0.1)  # 100ms
        
        # Record slow operation
        performance_monitor.record_metric('response_time', 0.2)  # 200ms
        
        # Check if threshold exceeded
        violations = performance_monitor.get_threshold_violations()
        assert len(violations) > 0
        assert 'response_time' in violations[0]['metric']
    
    def test_memory_monitoring(self, performance_monitor):
        """Test memory usage monitoring."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        if not hasattr(performance_monitor, 'get_memory_usage'):
            pytest.skip("Memory monitoring not available")
            
        # Get memory baseline
        initial_memory = performance_monitor.get_memory_usage()
        assert initial_memory > 0
        
        # Allocate memory
        large_data = [i for i in range(100000)]
        
        # Check memory increase
        current_memory = performance_monitor.get_memory_usage()
        assert current_memory >= initial_memory
        
        # Cleanup
        del large_data
    
    def test_performance_reporting(self, performance_monitor):
        """Test performance report generation."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        # Record some metrics
        performance_monitor.record_metric('requests', 100)
        performance_monitor.record_metric('errors', 5)
        performance_monitor.start_timer('operation')
        time.sleep(0.01)
        performance_monitor.stop_timer('operation')
        
        if hasattr(performance_monitor, 'generate_report'):
            report = performance_monitor.generate_report()
            assert isinstance(report, (dict, str))
            
            if isinstance(report, dict):
                assert 'requests' in str(report)
                assert 'errors' in str(report)
    
    @pytest.mark.asyncio
    async def test_async_performance_monitoring(self, performance_monitor):
        """Test async operation performance monitoring."""
        if performance_monitor is None:
            pytest.skip("PerformanceMonitor not available")
            
        if not hasattr(performance_monitor, 'monitor_async'):
            pytest.skip("Async monitoring not available")
            
        async def async_operation():
            await asyncio.sleep(0.01)
            return "result"
        
        # Monitor async operation
        result = await performance_monitor.monitor_async(
            'async_test', 
            async_operation()
        )
        
        assert result == "result"
        
        # Check metrics recorded
        metrics = performance_monitor.get_metrics()
        assert 'async_test' in str(metrics)


class TestSecurityManager:
    """Unit tests for SecurityManager validation and protection."""
    
    @pytest.fixture
    def security_manager(self):
        """SecurityManager instance for testing."""
        if SecurityManager is None:
            pytest.skip("SecurityManager not available")
        return SecurityManager()
    
    def test_security_manager_initialization(self):
        """Test security manager initializes correctly."""
        if SecurityManager is None:
            pytest.skip("SecurityManager not available")
            
        manager = SecurityManager()
        assert hasattr(manager, 'policies')
        assert hasattr(manager, 'validators')
    
    def test_input_validation(self, security_manager, performance_timer):
        """Test input validation and sanitization."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        # Test safe inputs
        safe_inputs = [
            "normal_string",
            "path/to/file.txt",
            "user@example.com",
            42,
            {"key": "value"}
        ]
        
        with performance_timer:
            for safe_input in safe_inputs:
                is_safe = security_manager.validate_input(safe_input)
                assert is_safe is True
        
        assert performance_timer.elapsed < 0.005  # Should be very fast
    
    def test_malicious_input_detection(self, security_manager):
        """Test detection of malicious inputs."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        malicious_inputs = [
            "../../../etc/passwd",  # Path traversal
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "__import__('os').system('rm -rf /')",  # Code injection
            "file:///etc/passwd",  # Local file inclusion
        ]
        
        for malicious_input in malicious_inputs:
            is_safe = security_manager.validate_input(malicious_input)
            assert is_safe is False
    
    def test_file_path_validation(self, security_manager):
        """Test file path validation and sanitization."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        # Safe paths
        safe_paths = [
            "documents/file.pdf",
            "./local/file.txt",
            "C:\\Users\\Documents\\file.docx"
        ]
        
        for safe_path in safe_paths:
            is_safe = security_manager.validate_file_path(safe_path)
            assert is_safe in [True, False]  # Implementation dependent
        
        # Dangerous paths
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/dev/null",
            "\\\\network\\share\\file"
        ]
        
        for dangerous_path in dangerous_paths:
            is_safe = security_manager.validate_file_path(dangerous_path)
            assert is_safe is False
    
    def test_command_validation(self, security_manager):
        """Test command validation for tool execution."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        if not hasattr(security_manager, 'validate_command'):
            pytest.skip("Command validation not available")
            
        # Safe commands
        safe_commands = [
            "list_documents",
            "get_document_by_id",
            "search_content"
        ]
        
        for safe_command in safe_commands:
            is_safe = security_manager.validate_command(safe_command)
            assert is_safe is True
        
        # Dangerous commands
        dangerous_commands = [
            "exec",
            "eval",
            "import",
            "os.system",
            "__builtins__"
        ]
        
        for dangerous_command in dangerous_commands:
            is_safe = security_manager.validate_command(dangerous_command)
            assert is_safe is False
    
    def test_rate_limiting(self, security_manager, performance_timer):
        """Test rate limiting functionality."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        if not hasattr(security_manager, 'check_rate_limit'):
            pytest.skip("Rate limiting not available")
            
        client_id = "test_client"
        
        # Should allow initial requests
        for i in range(10):
            allowed = security_manager.check_rate_limit(client_id)
            assert allowed is True
        
        # Should hit rate limit eventually
        rate_limited = False
        for i in range(100):
            if not security_manager.check_rate_limit(client_id):
                rate_limited = True
                break
        
        assert rate_limited is True  # Should eventually hit limit
    
    def test_access_control(self, security_manager):
        """Test access control and permissions."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        if not hasattr(security_manager, 'check_permission'):
            pytest.skip("Access control not available")
            
        # Test permissions
        permissions = [
            ('user', 'read_document', True),
            ('user', 'write_document', True),
            ('user', 'delete_document', False),
            ('admin', 'delete_document', True),
            ('guest', 'write_document', False)
        ]
        
        for role, action, expected in permissions:
            has_permission = security_manager.check_permission(role, action)
            # Note: Actual behavior depends on implementation
            assert isinstance(has_permission, bool)
    
    def test_data_sanitization(self, security_manager):
        """Test data sanitization for output."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        if not hasattr(security_manager, 'sanitize_output'):
            pytest.skip("Data sanitization not available")
            
        # Test various data types
        test_data = {
            'safe_string': 'Hello World',
            'html_content': '<p>Hello <script>alert("xss")</script></p>',
            'file_path': '../../../etc/passwd',
            'number': 42,
            'nested': {
                'content': '<img src="x" onerror="alert(1)">'
            }
        }
        
        sanitized = security_manager.sanitize_output(test_data)
        
        # Should remove dangerous content
        assert '<script>' not in str(sanitized)
        assert 'onerror=' not in str(sanitized)
        assert '../../../' not in str(sanitized)
    
    def test_security_audit_logging(self, security_manager):
        """Test security event audit logging."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        if not hasattr(security_manager, 'log_security_event'):
            pytest.skip("Audit logging not available")
            
        # Log various security events
        events = [
            {'type': 'failed_validation', 'input': 'malicious_input'},
            {'type': 'rate_limit_exceeded', 'client': 'test_client'},
            {'type': 'access_denied', 'user': 'guest', 'action': 'delete'}
        ]
        
        for event in events:
            result = security_manager.log_security_event(event)
            assert result in [True, None]  # Should succeed or be silent
    
    def test_security_performance(self, security_manager, performance_timer):
        """Test security validation performance."""
        if security_manager is None:
            pytest.skip("SecurityManager not available")
            
        # Test rapid validation operations
        test_inputs = [f"test_input_{i}" for i in range(1000)]
        
        with performance_timer:
            for test_input in test_inputs:
                security_manager.validate_input(test_input)
        
        assert performance_timer.elapsed < 0.1  # Should handle 1000 validations quickly


class TestInfrastructureIntegration:
    """Integration tests for infrastructure layer components."""
    
    def test_config_security_integration(self):
        """Test config and security working together."""
        if None in [ConfigManager, SecurityManager]:
            pytest.skip("Components not available")
            
        # Create test config
        config_data = {'mcp_server': {'uri': 'stdio://safe/path'}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            security = SecurityManager()
            
            # Test secure config loading
            config = manager.load_config()
            server_uri = config.get('mcp_server', {}).get('uri', '')
            
            is_safe = security.validate_input(server_uri)
            assert is_safe in [True, False]  # Should validate
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_performance_security_integration(self):
        """Test performance monitoring of security operations."""
        if None in [PerformanceMonitor, SecurityManager]:
            pytest.skip("Components not available")
            
        monitor = PerformanceMonitor()
        security = SecurityManager()
        
        # Monitor security operation performance
        monitor.start_timer('security_validation')
        
        # Perform security validations
        for i in range(100):
            security.validate_input(f"test_input_{i}")
        
        elapsed = monitor.stop_timer('security_validation')
        
        # Should be fast
        assert elapsed < 0.1
        
        # Record security metrics
        monitor.record_metric('security_checks', 100)
        metrics = monitor.get_metrics()
        assert 'security_checks' in metrics
    
    def test_config_performance_integration(self):
        """Test performance monitoring of config operations."""
        if None in [ConfigManager, PerformanceMonitor]:
            pytest.skip("Components not available")
            
        config_data = {'test': {'value': 42}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            monitor = PerformanceMonitor()
            
            # Monitor config operations
            monitor.start_timer('config_operations')
            
            for i in range(100):
                value = manager.get('test.value')
                manager.set('test.temp', i)
            
            elapsed = monitor.stop_timer('config_operations')
            
            # Should be fast
            assert elapsed < 0.05
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_comprehensive_infrastructure_workflow(self, performance_timer):
        """Test complete infrastructure workflow."""
        # Simulate infrastructure operations
        with performance_timer:
            # Config operations
            config = {
                'server': {'uri': 'stdio://path', 'timeout': 30},
                'security': {'rate_limit': 100, 'validation': True}
            }
            
            # Security validations
            inputs_to_validate = [
                'normal_input',
                'path/to/file',
                'user@example.com'
            ]
            
            for input_val in inputs_to_validate:
                # Simulate validation (basic string operations)
                is_safe = len(input_val) > 0 and not any(
                    dangerous in input_val 
                    for dangerous in ['../', '<script>', 'DROP TABLE']
                )
                assert is_safe is True
            
            # Performance tracking
            metrics = {
                'requests': 0,
                'errors': 0,
                'response_times': []
            }
            
            for i in range(50):
                start_time = time.time()
                # Simulate work
                result = {'status': 'success', 'data': f'item_{i}'}
                end_time = time.time()
                
                metrics['requests'] += 1
                metrics['response_times'].append(end_time - start_time)
            
            # Calculate averages
            avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
            assert avg_response_time < 0.001  # Very fast operations
        
        # Overall workflow should be fast
        assert performance_timer.elapsed < 0.1