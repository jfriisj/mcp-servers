"""
Test Configuration and Utilities for Integration Layer Unit Tests.

This module provides shared test configuration, fixtures, and utilities
for comprehensive unit testing of the Study Buddy integration layer components.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing Infrastructure  
SOLID Compliance: Full compliance with dependency inversion and interface segregation
Purpose: Enable comprehensive isolated testing of all integration components
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator, Callable
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import json
import logging
import time
from datetime import datetime, timedelta

# Add integration layer to path for testing
integration_path = Path(__file__).parent.parent
sys.path.insert(0, str(integration_path))

# Test configuration
TEST_CONFIG = {
    "timeout_seconds": 5.0,
    "max_test_duration": 30.0,
    "mock_latency_ms": 10.0,
    "performance_threshold_ms": 100.0,
    "coverage_target_percent": 90.0,
    "async_test_timeout": 10.0
}


# ============================================================================
# PYTEST CONFIGURATION AND FIXTURES
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Configure asyncio for testing
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_file(temp_dir):
    """Create temporary configuration file for testing."""
    config_data = {
        "mcp_server": {
            "host": "localhost",
            "port": 8000,
            "timeout": 30.0
        },
        "performance": {
            "cache_size_mb": 50,
            "max_connections": 5
        },
        "security": {
            "validation_enabled": True,
            "sanitize_errors": True
        },
        "logging": {
            "level": "DEBUG",
            "structured": True
        }
    }
    
    config_file = temp_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return config_file


@pytest.fixture
def mock_logger():
    """Create mock logger for testing."""
    logger = Mock(spec=logging.Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def mock_async_context():
    """Create mock async context manager."""
    context = AsyncMock()
    context.__aenter__ = AsyncMock(return_value=context)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


# ============================================================================
# MOCK CLIENT AND CONNECTION FIXTURES
# ============================================================================

@pytest.fixture
async def mock_mcp_connection():
    """Create mock MCP connection for testing."""
    connection = AsyncMock()
    connection.is_connected = True
    connection.connect = AsyncMock(return_value=True)
    connection.disconnect = AsyncMock()
    connection.send = AsyncMock()
    connection.receive = AsyncMock()
    connection.health_check = AsyncMock(return_value={"status": "healthy"})
    return connection


@pytest.fixture
def mock_connection_factory():
    """Create mock connection factory."""
    factory = Mock()
    factory.create_connection = AsyncMock()
    return factory


@pytest.fixture
async def mock_tool_response():
    """Create mock tool response data."""
    return {
        "success": True,
        "data": {
            "document_id": 123,
            "title": "Test Document",
            "message": "Operation completed successfully"
        },
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def mock_tool_list():
    """Create mock tool list for testing."""
    return [
        {
            "name": "upload_document",
            "description": "Upload a document for processing",
            "parameters": {
                "file_path": {"type": "string", "required": True},
                "title": {"type": "string", "required": False}
            }
        },
        {
            "name": "list_documents", 
            "description": "List all documents",
            "parameters": {
                "filters": {"type": "object", "required": False}
            }
        },
        {
            "name": "search_documents",
            "description": "Search documents by query",
            "parameters": {
                "query": {"type": "string", "required": True},
                "limit": {"type": "integer", "required": False}
            }
        }
    ]


# ============================================================================
# ERROR SIMULATION FIXTURES
# ============================================================================

@pytest.fixture
def connection_error():
    """Create connection error for testing."""
    return ConnectionError("Mock connection failed")


@pytest.fixture 
def timeout_error():
    """Create timeout error for testing."""
    return asyncio.TimeoutError("Mock operation timed out")


@pytest.fixture
def validation_error():
    """Create validation error for testing."""
    return ValueError("Mock validation failed")


@pytest.fixture
def server_error():
    """Create server error for testing."""
    return RuntimeError("Mock server error")


# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================

class PerformanceTimer:
    """Utility for measuring performance in tests."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
    
    def start(self) -> None:
        """Start timing."""
        self.start_time = time.perf_counter()
    
    def stop(self) -> float:
        """Stop timing and return duration in milliseconds."""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        return self.duration_ms
    
    def assert_within_threshold(self, threshold_ms: float) -> None:
        """Assert that duration is within threshold."""
        if self.duration_ms is None:
            raise RuntimeError("Timer not stopped")
        
        assert self.duration_ms <= threshold_ms, (
            f"Operation took {self.duration_ms:.1f}ms, "
            f"expected <= {threshold_ms}ms"
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds (for compatibility)."""
        if self.duration_ms is None:
            return 0.0
        return self.duration_ms / 1000.0


@pytest.fixture
def performance_timer():
    """Create performance timer for tests."""
    return PerformanceTimer()


@pytest.fixture
def performance_threshold():
    """Get performance threshold from config."""
    return TEST_CONFIG["performance_threshold_ms"]


# ============================================================================
# ASYNC TESTING UTILITIES
# ============================================================================

async def wait_for_condition(
    condition_func: Callable[[], bool], 
    timeout_seconds: float = 1.0,
    check_interval: float = 0.01
) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if condition_func():
            return True
        await asyncio.sleep(check_interval)
    
    return False


async def assert_async_raises(exception_class, async_func, *args, **kwargs):
    """Assert that async function raises specific exception."""
    try:
        await async_func(*args, **kwargs)
        pytest.fail(f"Expected {exception_class.__name__} to be raised")
    except exception_class:
        pass  # Expected
    except Exception as e:
        pytest.fail(f"Expected {exception_class.__name__}, got {type(e).__name__}: {e}")


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_test_document_data() -> Dict[str, Any]:
    """Generate test document data."""
    return {
        "id": 123,
        "title": "Test Document",
        "file_path": "/test/document.pdf",
        "file_type": "pdf",
        "upload_date": datetime.now().isoformat(),
        "total_pages": 10,
        "total_words": 1500,
        "tags": ["test", "example"],
        "indexed": False,
        "summarized": False
    }


def generate_test_chunk_data() -> Dict[str, Any]:
    """Generate test chunk data."""
    return {
        "id": 456,
        "document_id": 123,
        "chunk_index": 0,
        "chunk_type": "chapter",
        "title": "Chapter 1: Introduction",
        "content": "This is test content for the chunk.",
        "word_count": 150,
        "metadata": {
            "chapter_number": 1,
            "start_page": 1,
            "end_page": 5
        }
    }


def generate_test_summary_data() -> Dict[str, Any]:
    """Generate test summary data."""
    return {
        "id": 789,
        "chunk_id": 456,
        "summary_type": "standard",
        "summary_content": "This is a test summary of the chunk content.",
        "created_at": datetime.now().isoformat(),
        "word_count": 50
    }


# ============================================================================
# MOCKING UTILITIES
# ============================================================================

class MockContainer:
    """Container for commonly used mocks."""
    
    def __init__(self):
        self.logger = Mock(spec=logging.Logger)
        self.connection = AsyncMock()
        self.config = {}
        self.responses = {}
    
    def setup_connection_mock(self, success: bool = True):
        """Setup connection mock behavior."""
        if success:
            self.connection.connect = AsyncMock(return_value=True)
            self.connection.is_connected = True
        else:
            self.connection.connect = AsyncMock(side_effect=ConnectionError("Mock error"))
            self.connection.is_connected = False
    
    def setup_response_mock(self, tool_name: str, response_data: Dict[str, Any]):
        """Setup response mock for specific tool."""
        self.responses[tool_name] = response_data
    
    def get_mock_response(self, tool_name: str) -> Dict[str, Any]:
        """Get mock response for tool."""
        return self.responses.get(tool_name, {"success": True, "data": {}})


@pytest.fixture
def mock_container():
    """Create mock container for tests."""
    return MockContainer()


# ============================================================================
# TEST MARKERS AND CATEGORIES
# ============================================================================

# Pytest markers for test categorization
pytest_markers = [
    "unit: Unit tests with mocked dependencies",
    "async: Async function tests",
    "performance: Performance and timing tests", 
    "error: Error handling and edge case tests",
    "config: Configuration and validation tests",
    "security: Security validation tests"
]


def is_async_test(item):
    """Check if test is async."""
    return asyncio.iscoroutinefunction(item.function)


# ============================================================================
# TEST UTILITIES
# ============================================================================

def assert_mock_called_with_timeout(mock_func, timeout_seconds: float = 1.0):
    """Assert mock was called within timeout."""
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if mock_func.called:
            return True
        time.sleep(0.01)
    
    pytest.fail(f"Mock {mock_func} was not called within {timeout_seconds} seconds")


def validate_test_coverage():
    """Validate test coverage meets requirements."""
    # This would integrate with coverage.py in real implementation
    target = TEST_CONFIG["coverage_target_percent"]
    print(f"Target coverage: {target}%")
    return True


# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup any lingering async tasks
    try:
        pending_tasks = [
            task for task in asyncio.all_tasks() 
            if not task.done()
        ]
        for task in pending_tasks:
            task.cancel()
    except RuntimeError:
        pass  # No event loop running


# ============================================================================
# EXAMPLE TEST FUNCTION
# ============================================================================

def _test_configuration():
    """Test that configuration is working."""
    print("🧪 Testing configuration...")
    
    # Test basic configuration
    assert TEST_CONFIG["timeout_seconds"] == 5.0
    assert TEST_CONFIG["coverage_target_percent"] == 90.0
    
    # Test temp directory creation
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
    
    print("✅ Configuration tests passed!")


if __name__ == "__main__":
    _test_configuration()