"""
Integration Testing Suite for Study Buddy Integration Layer

This module provides comprehensive integration testing capabilities
that validate the integration layer with real MCP servers.

Test Categories:
- Connection lifecycle testing
- Tool invocation workflow testing
- Error recovery and resilience testing  
- Performance validation under load
- End-to-end workflow validation

All tests use real MCP server communication to ensure
production-level reliability and correctness.
"""

# Test Categories
CONNECTION_TESTS = "connection"
TOOL_TESTS = "tools"
WORKFLOW_TESTS = "workflows"
ERROR_TESTS = "errors"
PERFORMANCE_TESTS = "performance"
RESILIENCE_TESTS = "resilience"

# Test Markers
SLOW_TEST = "slow"
REQUIRES_SERVER = "requires_server"
INTEGRATION_TEST = "integration"
LOAD_TEST = "load"

__version__ = "1.0.0"
__all__ = [
    "CONNECTION_TESTS",
    "TOOL_TESTS", 
    "WORKFLOW_TESTS",
    "ERROR_TESTS",
    "PERFORMANCE_TESTS",
    "RESILIENCE_TESTS",
    "SLOW_TEST",
    "REQUIRES_SERVER",
    "INTEGRATION_TEST", 
    "LOAD_TEST"
]