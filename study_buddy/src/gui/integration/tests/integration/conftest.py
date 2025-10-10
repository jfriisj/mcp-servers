"""
Integration Test Configuration and Fixtures

Provides shared configuration, fixtures, and utilities
for integration testing with real MCP servers.
"""

import pytest
import asyncio
import subprocess
import time
import psutil
import tempfile
import shutil
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Integration test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_server
]

class TestMCPServer:
    """Test MCP Server management for integration tests"""
    
    def __init__(self, port: int = 3000, debug: bool = False):
        self.port = port
        self.debug = debug
        self.process: Optional[subprocess.Popen] = None
        self.temp_dir: Optional[str] = None
        
    async def start(self) -> None:
        """Start test MCP server instance"""
        # Create temporary directory for server data
        self.temp_dir = tempfile.mkdtemp(prefix="test_mcp_")
        
        # Create minimal server configuration
        config = {
            "server": {
                "port": self.port,
                "host": "localhost",
                "debug": self.debug
            },
            "tools": {
                "echo": {"enabled": True},
                "add": {"enabled": True},
                "error": {"enabled": True},
                "slow": {"enabled": True}
            },
            "data_dir": self.temp_dir
        }
        
        config_file = os.path.join(self.temp_dir, "config.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
            
        # Start server process
        server_script = self._create_test_server_script()
        self.process = subprocess.Popen([
            "python", server_script,
            "--config", config_file,
            "--port", str(self.port)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to be ready
        await self._wait_for_server()
        
    async def stop(self) -> None:
        """Stop test MCP server instance"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
    def _create_test_server_script(self) -> str:
        """Create minimal test MCP server script"""
        script_content = '''
import asyncio
import json
import sys
from pathlib import Path

class TestMCPServer:
    """Minimal MCP server for integration testing"""
    
    def __init__(self, port: int):
        self.port = port
        
    async def handle_echo(self, message: str) -> Dict[str, Any]:
        """Echo tool for testing"""
        return {"result": message, "tool": "echo"}
        
    async def handle_add(self, a: int, b: int) -> Dict[str, Any]:
        """Add tool for testing"""  
        return {"result": a + b, "tool": "add"}
        
    async def handle_error(self) -> Dict[str, Any]:
        """Error tool for testing error handling"""
        raise Exception("Test error from server")
        
    async def handle_slow(self, delay: float = 2.0) -> Dict[str, Any]:
        """Slow tool for timeout testing"""
        await asyncio.sleep(delay)
        return {"result": f"Completed after {delay}s", "tool": "slow"}
        
    async def run(self):
        """Run test server"""
        print(f"Test MCP Server running on port {self.port}")
        # Simple server implementation
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--config", type=str)
    args = parser.parse_args()
    
    server = TestMCPServer(args.port)
    asyncio.run(server.run())
'''
        
        if self.temp_dir:
            script_path = os.path.join(self.temp_dir, "test_server.py")
            with open(script_path, "w") as f:
                f.write(script_content)
                
            return script_path
        else:
            raise RuntimeError("Temporary directory not initialized")
        
    async def _wait_for_server(self, timeout: int = 10) -> None:
        """Wait for server to become ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to connect to server
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', self.port))
                sock.close()
                if result == 0:
                    return
            except:
                pass
            await asyncio.sleep(0.1)
            
        raise TimeoutError(f"Test MCP server did not start within {timeout}s")


class IntegrationTestBase:
    """Base class for integration tests"""
    
    @pytest.fixture(autouse=True) 
    async def setup_integration_test(self):
        """Setup for each integration test"""
        self.test_server = TestMCPServer()
        await self.test_server.start()
        yield
        await self.test_server.stop()
        
    @pytest.fixture
    def server_config(self) -> Dict[str, Any]:
        """Test server configuration"""
        return {
            "host": "localhost",
            "port": 3000,
            "timeout": 5,
            "retry_attempts": 3,
            "retry_delay": 1
        }
        
    @pytest.fixture  
    async def mcp_client(self, server_config):
        """MCP client instance for testing"""
        # Import will be available when integration layer is implemented
        try:
            from gui.integration.core.mcp_client import MCPClient
        except ImportError:
            pytest.skip("MCP client not yet implemented")
        
        client = MCPClient(server_config)
        await client.connect()
        yield client
        await client.disconnect()


@pytest.fixture(scope="session")
async def test_servers():
    """Session-scoped test servers for performance testing"""
    servers = []
    try:
        # Start multiple servers for load testing
        for i in range(3):
            server = TestMCPServer(port=3000 + i)
            await server.start()
            servers.append(server)
        yield servers
    finally:
        for server in servers:
            await server.stop()


@pytest.fixture
def performance_config() -> Dict[str, Any]:
    """Configuration for performance testing"""
    return {
        "concurrent_connections": 10,
        "operations_per_connection": 50,
        "timeout_threshold": 3.0,
        "memory_threshold_mb": 50,
        "target_ops_per_second": 100
    }


@pytest.fixture
def resilience_config() -> Dict[str, Any]:
    """Configuration for resilience testing"""
    return {
        "failure_scenarios": [
            "server_restart",
            "network_timeout", 
            "invalid_response",
            "server_overload",
            "connection_drop"
        ],
        "recovery_timeout": 10,
        "max_retry_attempts": 5,
        "backoff_factor": 1.5
    }


@asynccontextmanager
async def temporary_server_failure(server: TestMCPServer, duration: float = 2.0):
    """Context manager to simulate temporary server failures"""
    try:
        # Stop server
        await server.stop()
        yield
        await asyncio.sleep(duration)
    finally:
        # Restart server
        await server.start()


def measure_performance(func):
    """Decorator to measure test performance metrics"""
    import functools
    import time
    import psutil
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Capture initial metrics
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = await func(*args, **kwargs)
            
            # Capture final metrics
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Store metrics for validation
            metrics = {
                "duration": end_time - start_time,
                "memory_used": end_memory - start_memory,
                "peak_memory": end_memory
            }
            
            # Attach metrics to result if possible
            if hasattr(result, '__dict__'):
                result._test_metrics = metrics
                
            return result
            
        except Exception as e:
            # Include partial metrics in exception (if supported)
            try:
                e.test_duration = time.time() - start_time  # type: ignore
            except AttributeError:
                pass  # Not all exceptions support dynamic attributes
            raise
            
    return wrapper


# Test data fixtures
@pytest.fixture
def sample_tool_calls() -> List[Dict[str, Any]]:
    """Sample tool calls for testing"""
    return [
        {"tool": "echo", "args": {"message": "Hello World"}},
        {"tool": "add", "args": {"a": 5, "b": 3}}, 
        {"tool": "echo", "args": {"message": "Test message"}},
        {"tool": "add", "args": {"a": 10, "b": 20}},
        {"tool": "slow", "args": {"delay": 0.5}}
    ]


@pytest.fixture
def error_scenarios() -> List[Dict[str, Any]]:
    """Error scenarios for resilience testing"""
    return [
        {"type": "tool_error", "tool": "error", "args": {}},
        {"type": "timeout", "tool": "slow", "args": {"delay": 10}},
        {"type": "invalid_tool", "tool": "nonexistent", "args": {}},
        {"type": "invalid_args", "tool": "add", "args": {"a": "not_a_number"}},
        {"type": "server_disconnect", "tool": "echo", "disconnect_before": True}
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for integration tests"""
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "requires_server: Requires test server")
    config.addinivalue_line("markers", "slow: Slow running test")
    config.addinivalue_line("markers", "load: Load/performance test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection for integration tests"""
    for item in items:
        # Add integration marker to all tests in this directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Add slow marker to performance tests
        if "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)